from unittest import mock

from dcim import forms
from django.test import SimpleTestCase, TestCase

from netbox_metatype_importer.choices import TypeChoices
from netbox_metatype_importer.utils import load_data, related_object_forms


class RelatedObjectFormsTest(SimpleTestCase):
    def test_netbox_46_port_mappings_are_imported(self):
        self.assertIs(
            related_object_forms()['port-mappings'],
            forms.PortTemplateMappingImportForm,
        )


class LoadDataLoggingTestCase(TestCase):
    @mock.patch("netbox_metatype_importer.utils.GitHubGqlAPI")
    def test_logs_successful_batch(self, mock_api_class):
        mock_api = mock_api_class.return_value
        mock_api.iter_tree_batches.return_value = [[("Cisco", "switch.yaml", "sha123")]]

        logger = mock.Mock()

        loaded, created, updated = load_data(
            TypeChoices.TYPE_DEVICE,
            job_logger=logger,
        )

        self.assertEqual((loaded, created, updated), (1, 1, 0))
        self.assertGreaterEqual(logger.info.call_count, 3)
