import os
import logging
from collections import OrderedDict
from urllib.request import urlopen

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db import transaction

from dcim import forms
from netbox_metatype_importer.graphql.gql import GQLError, GitHubGqlAPI
from .models import MetaType

logger = logging.getLogger(__name__)

__all__ = ['load_data', 'related_object_forms', 'save_image_from_url']


def save_image_from_url(instance, image_url, field_name):
    """
    Downloads an image from the URL and saves it to the specified ImageField.
    """
    try:
        response = urlopen(image_url)
        file_name = os.path.basename(image_url.split('?')[0])  # handle GitHub blob/raw URLs
        content = ContentFile(response.read())

        getattr(instance, field_name).save(file_name, content)
    except Exception as e:
        return e


def load_data(type_choice, job_logger=None, job=None):
    loaded = created = updated = 0
    plugin_settings = settings.PLUGINS_CONFIG.get('netbox_metatype_importer', {})
    token = plugin_settings.get('github_token')
    repo = plugin_settings.get('repo')
    branch = plugin_settings.get('branch')
    owner = plugin_settings.get('repo_owner')

    if job_logger:
        job_logger.info(f"Starting data load for Type: {type_choice}, Repo: {repo}, Branch: {branch}, Owner: {owner}")

    gh_api_instance = GitHubGqlAPI(
        token=token,
        owner=owner,
        repo=repo,
        branch=branch,
        path=type_choice,
    )

    try:
        batches = gh_api_instance.iter_tree_batches(batch_size=300)

        for batch in batches:
            batch_created = 0
            batch_updated = 0

            # Commit each batch independently so the records become
            # visible to other database connections immediately.
            with transaction.atomic():
                for vendor, model, sha in batch:
                    loaded += 1

                    try:
                        meta_type = MetaType.objects.get(
                            vendor=vendor,
                            name=model,
                            type=type_choice,
                        )

                        if meta_type.sha != sha:
                            meta_type.is_new = True
                            meta_type.save()
                            updated += 1
                            batch_updated += 1
                        else:
                            meta_type.is_new = False
                            meta_type.save()

                    except ObjectDoesNotExist:
                        MetaType.objects.create(
                            vendor=vendor,
                            name=model,
                            sha=sha,
                            type=type_choice,
                        )
                        created += 1
                        batch_created += 1

            if job_logger:
                job_logger.info(f"Batch saved: loaded={len(batch)}, created={batch_created}, updated={batch_updated}")
            if job:
                job.save(update_fields=["log_entries"])

    except GQLError as e:
        raise GQLError(f'GraphQL API Error: {e.message}')

    if job_logger:
        job_logger.info(f"Batch saved successfully. Processed: {loaded}")

    return loaded, created, updated


def related_object_forms():
    return OrderedDict(
        (
            ('console-ports', forms.ConsolePortTemplateImportForm),
            ('console-server-ports', forms.ConsoleServerPortTemplateImportForm),
            ('cooling-intakes', forms.CoolingIntakeTemplateImportForm),
            ('cooling-outflows', forms.CoolingOutflowTemplateImportForm),
            ('power-ports', forms.PowerPortTemplateImportForm),
            ('power-outlets', forms.PowerOutletTemplateImportForm),
            ('interfaces', forms.InterfaceTemplateImportForm),
            ('rear-ports', forms.RearPortTemplateImportForm),
            ('front-ports', forms.FrontPortTemplateImportForm),
            ('port-mappings', forms.PortTemplateMappingImportForm),
            ('device-bays', forms.DeviceBayTemplateImportForm),
            ('inventory-items', forms.InventoryItemTemplateImportForm),
            ('module-bays', forms.ModuleBayTemplateImportForm),
        )
    )
