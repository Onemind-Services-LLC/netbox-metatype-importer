import time
from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.shortcuts import reverse
from django.utils.text import slugify
from netbox_metatype_importer.filters import MetaTypeFilterSet
from netbox_metatype_importer.forms import MetaTypeFilterForm
from netbox_metatype_importer.graphql.gql import GQLError, GitHubGqlAPI
from rest_framework import mixins as drf_mixins, status
from rest_framework.response import Response
from rest_framework.routers import APIRootView

from dcim import forms
from dcim.models import DeviceType, Manufacturer, ModuleType
from netbox.api.viewsets import BaseViewSet
from utilities.exceptions import AbortTransaction, PermissionsViolation
from utilities.forms.bulk_import import BulkImportForm
from . import serializers
from ..choices import TypeChoices
from ..models import MetaType
from ..utils import *


class MetaTypeRootView(APIRootView):
    """
    MetaType API root view
    """

    def get_view_name(self):
        return 'MetaType'


class DeviceTypeListViewSet(drf_mixins.ListModelMixin, BaseViewSet):
    serializer_class = serializers.MetaTypeSerializer
    queryset = MetaType.objects.filter(type=TypeChoices.TYPE_DEVICE)
    filterset_class = MetaTypeFilterSet


class ModuleTypeListViewSet(drf_mixins.ListModelMixin, BaseViewSet):
    serializer_class = serializers.MetaTypeSerializer
    queryset = MetaType.objects.filter(type=TypeChoices.TYPE_MODULE)
    filterset_class = MetaTypeFilterSet


class MetaTypeLoadViewSetBase(BaseViewSet):
    serializer_class = serializers.MetaTypeSerializer
    queryset = MetaType.objects.all()
    type_choice = None

    def create(self, request, *args, **kwargs):
        if not request.user.has_perm('netbox_metatype_importer.add_metatype'):
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            loaded, created, updated = load_data(self.type_choice)

            response_data = {'loaded': loaded, 'created': created, 'updated': updated}
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MetaDeviceTypeLoadViewSet(MetaTypeLoadViewSetBase):
    type_choice = TypeChoices.TYPE_DEVICE


class MetaModuleTypeLoadViewSet(MetaTypeLoadViewSetBase):
    type_choice = TypeChoices.TYPE_MODULE


class MetaTypeImportViewSetBase(BaseViewSet):
    serializer_class = serializers.MetaTypeSerializer
    queryset = MetaType.objects.all()
    filterset = MetaTypeFilterSet
    filterset_form = MetaTypeFilterForm
    type = None
    type_model = None
    model_form = None
    related_object = None

    def create(self, request, *args, **kwargs):
        if not request.user.has_perm('netbox_metatype_importer.add_metatype'):
            return Response(status=status.HTTP_403_FORBIDDEN)

        vendor_count = 0
        errored = 0
        imported_dt = []
        model = self.queryset.model

        if name := request.data.get("name"):
            instance = MetaType.objects.filter(
                Q(name__in=[f"{name}.yaml", f"{name}.yml", name]), type=self.type
            ).values_list("pk", flat=True)
            pk_list = list(instance)
        else:
            return Response({"error": "Name field is required"}, status=status.HTTP_400_BAD_REQUEST)

        plugin_settings = settings.PLUGINS_CONFIG.get('netbox_metatype_importer', {})
        token = plugin_settings.get('github_token')
        repo = plugin_settings.get('repo')
        branch = plugin_settings.get('branch')
        owner = plugin_settings.get('repo_owner')

        gh_api = GitHubGqlAPI(token=token, owner=owner, repo=repo, branch=branch, path=self.type)

        query_data = {}
        # check already imported mdt
        already_imported_mdt = model.objects.filter(pk__in=pk_list, is_imported=True, type=self.type)
        if already_imported_mdt.exists():
            for _mdt in already_imported_mdt:
                if self.type_model.objects.filter(pk=_mdt.imported_dt).exists() is False:
                    _mdt.imported_dt = None
                    _mdt.is_imported = False
                    _mdt.save()
        vendors_for_cre = set(model.objects.filter(pk__in=pk_list).values_list('vendor', flat=True).distinct())
        for vendor, name, sha in model.objects.filter(pk__in=pk_list, is_imported=False).values_list(
            'vendor', 'name', 'sha'
        ):
            query_data[sha] = f'{vendor}/{name}'
        if not query_data:
            return Response({'message': 'Nothing to import'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            dt_files = gh_api.get_files(query_data)
        except GQLError as e:
            return Response({'error': f'GraphQL API Error: {e.message}'}, status=status.HTTP_400_BAD_REQUEST)

        # create manufacturer
        for vendor in vendors_for_cre:
            manufacturer, created = Manufacturer.objects.get_or_create(name=vendor, slug=slugify(vendor))
            if created:
                vendor_count += 1

        for sha, yaml_text in dt_files.items():
            form = BulkImportForm(data={'data': yaml_text, 'format': 'yaml'})
            if form.is_valid():
                data = form.cleaned_data['data']

                if isinstance(data, list):
                    data = data[0]

                model_form = self.model_form(data)

                for field_name, field in model_form.fields.items():
                    if field_name not in data and hasattr(field, 'initial'):
                        model_form.data[field_name] = field.initial

                # Initialize the "_init_time" field with the current timestamp to ensure it's present in the form data
                model_form.data["_init_time"] = time.time()

                if model_form.is_valid():
                    try:
                        with transaction.atomic():
                            obj = model_form.save()

                            for field_name, related_object_form in related_object_forms().items():
                                related_obj_pks = []
                                for i, rel_obj_data in enumerate(data.get(field_name, list())):
                                    rel_obj_data.update({self.related_object: obj})
                                    f = related_object_form(rel_obj_data)
                                    for subfield_name, field in f.fields.items():
                                        if subfield_name not in rel_obj_data and hasattr(field, 'initial'):
                                            f.data[subfield_name] = field.initial
                                    if f.is_valid():
                                        related_obj = f.save()
                                        related_obj_pks.append(related_obj.pk)
                                    else:
                                        for subfield_name, errors in f.errors.items():
                                            for err in errors:
                                                err_msg = "{}[{}] {}: {}".format(field_name, i, subfield_name, err)
                                                model_form.add_error(None, err_msg)
                                        raise AbortTransaction()
                    except AbortTransaction:
                        # log ths
                        pass
                    except PermissionsViolation:
                        errored += 1
                        continue
                if model_form.errors:
                    errored += 1
                else:
                    imported_dt.append(obj.pk)
                    metadt = MetaType.objects.get(sha=sha)
                    metadt.imported_dt = obj.pk
                    metadt.save()
            else:
                errored += 1

        if imported_dt:
            if errored:
                return Response(
                    {'message': f'Imported: {len(imported_dt)}, Failed: {errored}'},
                    status=status.HTTP_206_PARTIAL_CONTENT,
                )
            else:
                qparams = urlencode({'id': imported_dt}, doseq=True)
                url = reverse(f'dcim:{str(self.type).replace("-", "").rstrip("s")}_list') + '?' + qparams
                return Response(
                    {'message': f'Imported: {len(imported_dt)}', 'url': url}, status=status.HTTP_201_CREATED
                )
        else:
            return Response({'error': f'Can not import {self.type}'}, status=status.HTTP_400_BAD_REQUEST)


class MetaDeviceTypeImportViewSet(MetaTypeImportViewSetBase):
    type = TypeChoices.TYPE_DEVICE
    type_model = DeviceType
    model_form = forms.DeviceTypeImportForm
    related_object = 'device_type'


class MetaModuleTypeImportViewSet(MetaTypeImportViewSetBase):
    type = TypeChoices.TYPE_MODULE
    type_model = ModuleType
    model_form = forms.ModuleTypeImportForm
    related_object = 'module_type'
