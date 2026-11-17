from unittest import mock

from dcim import forms
from django.test import SimpleTestCase, TestCase

from netbox_metatype_importer.choices import TypeChoices
from netbox_metatype_importer.graphql.gql import GQLError
from netbox_metatype_importer.jobs.load_devicetype import LoadData
from netbox_metatype_importer.models import MetaType
from netbox_metatype_importer.utils import load_data, related_object_forms


class RelatedObjectFormsTest(SimpleTestCase):
    def test_netbox_47_port_mappings_are_imported(self):
        self.assertIs(
            related_object_forms()['port-mappings'],
            forms.PortTemplateMappingImportForm,
        )


class LoadDataLoggingTestCase(TestCase):
    @mock.patch('netbox_metatype_importer.utils.GitHubGqlAPI')
    def test_logs_successful_batch(self, mock_api_class):
        mock_api = mock_api_class.return_value
        mock_api.iter_tree_batches.return_value = [[('Cisco', 'switch.yaml', 'sha123')]]

        logger = mock.Mock()

        loaded, created, updated = load_data(
            TypeChoices.TYPE_DEVICE,
            job_logger=logger,
        )

        self.assertEqual((loaded, created, updated), (1, 1, 0))
        self.assertGreaterEqual(logger.info.call_count, 3)
        mock_api.iter_tree_batches.assert_called_once_with(batch_size=300)
        self.assertTrue(
            MetaType.objects.filter(
                vendor='Cisco',
                name='switch.yaml',
                sha='sha123',
                type=TypeChoices.TYPE_DEVICE,
            ).exists()
        )

    @mock.patch('netbox_metatype_importer.utils.GitHubGqlAPI')
    def test_wraps_graphql_error_with_context(self, mock_api_class):
        mock_api_class.return_value.iter_tree_batches.side_effect = GQLError('GitHub unavailable')

        with self.assertRaisesRegex(GQLError, 'GraphQL API Error: GitHub unavailable'):
            load_data(TypeChoices.TYPE_DEVICE)


class LoadDataJobRunTestCase(SimpleTestCase):
    def setUp(self):
        # JobRunner receives the associated Job object at initialization.
        # The run() method does not require the Job to be persisted here.
        self.job = mock.Mock()
        self.runner = LoadData(self.job)
        self.runner.logger = mock.Mock()

    @mock.patch('netbox_metatype_importer.jobs.load_devicetype.load_data')
    def test_run_logs_successful_load(self, mock_load_data):
        mock_load_data.return_value = (12, 10, 2)

        self.runner.run(path=TypeChoices.TYPE_DEVICE)

        mock_load_data.assert_called_once_with(
            TypeChoices.TYPE_DEVICE,
            job_logger=self.runner.logger,
            job=self.job,
        )
        self.runner.logger.info.assert_any_call(f'Loading completed: loaded=12, created=10, updated=2')
        self.runner.logger.exception.assert_not_called()

    @mock.patch('netbox_metatype_importer.jobs.load_devicetype.load_data')
    def test_run_logs_and_reraises_load_error(self, mock_load_data):
        error = RuntimeError('GitHub connection failed')
        mock_load_data.side_effect = error

        with self.assertRaises(RuntimeError) as raised:
            self.runner.run(path=TypeChoices.TYPE_DEVICE)

        self.assertIs(raised.exception, error)
        self.runner.logger.exception.assert_called_once_with(
            f'Failed to load device types from GitHub: {TypeChoices.TYPE_DEVICE}'
        )
