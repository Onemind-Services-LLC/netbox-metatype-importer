from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, reverse
from django.utils.text import slugify
from django.views.generic import View
from netbox_metatype_importer.graphql.gql import GQLError, GitHubGqlAPI

from dcim import forms
from dcim.models import DeviceType, Manufacturer, ModuleType
from netbox.views import generic
from utilities.exceptions import AbortTransaction, PermissionsViolation
from utilities.forms.bulk_import import BulkImportForm
from utilities.views import ContentTypePermissionRequiredMixin, GetReturnURLMixin
from .choices import TypeChoices
from .filters import MetaTypeFilterSet
from .forms import MetaTypeFilterForm
from .models import MetaType
from .tables import MetaTypeTable
from .utils import *


class MetaDeviceTypeListView(generic.ObjectListView):
    queryset = MetaType.objects.filter(type=TypeChoices.TYPE_DEVICE)
    filterset = MetaTypeFilterSet
    filterset_form = MetaTypeFilterForm
    table = MetaTypeTable
    actions = ()
    template_name = 'netbox_metatype_importer/metadevicetype_list.html'


class MetaModuleTypeListView(generic.ObjectListView):
    queryset = MetaType.objects.filter(type=TypeChoices.TYPE_MODULE)
    filterset = MetaTypeFilterSet
    filterset_form = MetaTypeFilterForm
    table = MetaTypeTable
    actions = ()
    template_name = 'netbox_metatype_importer/metamoduletype_list.html'


class GenericTypeLoadView(ContentTypePermissionRequiredMixin, GetReturnURLMixin, View):
    path = None

    def get_required_permission(self):
        return 'netbox_metatype_importer.add_metatype'

    def post(self, request):
        return_url = self.get_return_url(request)

        if not request.user.has_perm('netbox_metatype_importer.add_metatype'):
            return HttpResponseForbidden()
        created, updated, loaded = load_data(self.path)
        messages.success(request, f'Loaded: {loaded}, Created: {created}, Updated: {updated}')
        return redirect(return_url)


class MetaDeviceTypeLoadView(GenericTypeLoadView):
    path = TypeChoices.TYPE_DEVICE


class MetaModuleTypeLoadView(GenericTypeLoadView):
    path = TypeChoices.TYPE_MODULE


class GenericTypeImportView(ContentTypePermissionRequiredMixin, GetReturnURLMixin, View):
    filterset = MetaTypeFilterSet
    filterset_form = MetaTypeFilterForm
    type = None
    type_model = None
    model_form = None
    related_object = None

    def get_required_permission(self):
        return 'netbox_metatype_importer.add_metatype'

    def post(self, request):
        return_url = self.get_return_url(request)

        vendor_count = 0
        errored = 0
        imported_dt = []
        model = self.queryset.model

        if request.POST.get('_all'):
            if self.filterset is not None:
                pk_list = [obj.pk for obj in self.filterset(request.GET, model.objects.only('pk')).qs]
            else:
                pk_list = model.objects.values_list('pk', flat=True)
        else:
            pk_list = [int(pk) for pk in request.POST.getlist('pk')]

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
            messages.warning(request, message='Nothing to import')
            return redirect(return_url)
        try:
            dt_files = gh_api.get_files(query_data)
        except GQLError as e:
            messages.error(request, message=f'GraphQL API Error: {e.message}')
            return redirect(return_url)

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
        # msg
        if imported_dt:
            messages.success(request, f'Imported: {imported_dt.__len__()}')
            if errored:
                messages.error(request, f'Failed: {errored}')
            qparams = urlencode({'id': imported_dt}, doseq=True)
            # Black magic to get the url path from the type
            return redirect(reverse(f'dcim:{self.type_model._meta.model_name}_list') + '?' + qparams)
        else:
            messages.error(request, f'Can not import {self.type_model.__name__}')
            return redirect(return_url)


class MetaDeviceTypeImportView(GenericTypeImportView):
    queryset = MetaType.objects.filter(type=TypeChoices.TYPE_DEVICE)
    type = TypeChoices.TYPE_DEVICE
    type_model = DeviceType
    model_form = forms.DeviceTypeImportForm
    related_object = 'device_type'


class MetaModuleTypeImportView(GenericTypeImportView):
    queryset = MetaType.objects.filter(type=TypeChoices.TYPE_MODULE)
    type = TypeChoices.TYPE_MODULE
    type_model = ModuleType
    model_form = forms.ModuleTypeImportForm
    related_object = 'module_type'


class MetaDeviceTypeBulkDeleteView(generic.BulkDeleteView):
    queryset = MetaType.objects.filter(type=TypeChoices.TYPE_DEVICE)
    table = MetaTypeTable


class MetaModuleTypeBulkDeleteView(generic.BulkDeleteView):
    queryset = MetaType.objects.filter(type=TypeChoices.TYPE_MODULE)
    table = MetaTypeTable
