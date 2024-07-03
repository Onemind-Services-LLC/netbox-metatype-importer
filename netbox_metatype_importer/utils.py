from collections import OrderedDict

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from netbox_metatype_importer.graphql.gql import GitHubGqlAPI, GQLError

from dcim import forms
from .models import MetaType

__all__ = ['load_data', 'related_object_forms']


def load_data(type_choice):
    loaded = created = updated = 0
    plugin_settings = settings.PLUGINS_CONFIG.get('netbox_metatype_importer', {})
    token = plugin_settings.get('github_token')
    repo = plugin_settings.get('repo')
    branch = plugin_settings.get('branch')
    owner = plugin_settings.get('repo_owner')
    gh_api_instance = GitHubGqlAPI(token=token, owner=owner, repo=repo, branch=branch, path=type_choice)

    try:
        models = gh_api_instance.get_tree()
    except GQLError as e:
        return Exception(f'GraphQL API Error: {e.message}')

    for vendor, models_data in models.items():
        for model, model_data in models_data.items():
            loaded += 1
            try:
                meta_type = MetaType.objects.get(vendor=vendor, name=model, type=type_choice)
                if meta_type.sha != model_data['sha']:
                    meta_type.is_new = True
                    meta_type.save()
                    updated += 1
                else:
                    meta_type.is_new = False
                    meta_type.save()
                continue
            except ObjectDoesNotExist:
                MetaType.objects.create(vendor=vendor, name=model, sha=model_data['sha'], type=type_choice)
                created += 1

    return loaded, created, updated


def related_object_forms():
    return OrderedDict(
        (
            ('console-ports', forms.ConsolePortTemplateImportForm),
            ('console-server-ports', forms.ConsoleServerPortTemplateImportForm),
            ('power-ports', forms.PowerPortTemplateImportForm),
            ('power-outlets', forms.PowerOutletTemplateImportForm),
            ('interfaces', forms.InterfaceTemplateImportForm),
            ('rear-ports', forms.RearPortTemplateImportForm),
            ('front-ports', forms.FrontPortTemplateImportForm),
            ('device-bays', forms.DeviceBayTemplateImportForm),
            ('inventory-items', forms.InventoryItemTemplateImportForm),
            ('module-bays', forms.ModuleBayTemplateImportForm),
            ('device-bays', forms.DeviceBayTemplateImportForm),
        )
    )
