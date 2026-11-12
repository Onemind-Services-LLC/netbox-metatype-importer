from unittest import mock
from django.test import TestCase, override_settings

from netbox_metatype_importer.graphql.gql import GitHubGqlAPI, GQLError


class GraphQLProxyTests(TestCase):
    @override_settings(
        HTTP_PROXIES={
            'http': 'http://proxy.example.com:8080',
            'https': 'http://proxy.example.com:8080',
        }
    )
    def test_github_gql_api_honors_http_proxies_setting(self):
        api = GitHubGqlAPI(token='x', owner='o', repo='r', branch='b', path='p')
        # session.proxies should include the configured proxies
        self.assertIn('http', api.session.proxies)
        self.assertIn('https', api.session.proxies)
        self.assertEqual(api.session.proxies['http'], 'http://proxy.example.com:8080')
        self.assertEqual(api.session.proxies['https'], 'http://proxy.example.com:8080')

    def test_github_gql_api_trusts_env_proxies(self):
        # Without overriding settings, ensure trust_env is enabled so env proxies are honored
        api = GitHubGqlAPI(token='x', owner='o', repo='r', branch='b', path='p')
        self.assertTrue(api.session.trust_env)


class GetTreeEntriesTestCase(TestCase):
    def setUp(self):
        self.api = GitHubGqlAPI()

    def test_empty_response(self):
        for data in (None, {}):
            with self.subTest(data=data):
                with self.assertRaisesRegex(GQLError, "empty response"):
                    self.api.get_tree_entries(data)

    def test_missing_data(self):
        with self.assertRaisesRegex(GQLError, "Repository not found"):
            self.api.get_tree_entries({"extensions": {}})

    def test_null_data(self):
        with self.assertRaisesRegex(GQLError, "Repository not found"):
            self.api.get_tree_entries({"data": None})

    def test_missing_repository(self):
        with self.assertRaisesRegex(GQLError, "Repository not found"):
            self.api.get_tree_entries({"data": {}})

    def test_missing_object(self):
        with self.assertRaisesRegex(GQLError, "configured branch or path"):
            self.api.get_tree_entries({"data": {"repository": {"object": None}}})

    def test_graphql_errors(self):
        with self.assertRaisesRegex(GQLError, "GraphQL error"):
            self.api.get_tree_entries({"errors": [{"message": "Something went wrong"}]})

    def test_returns_tree_entries(self):
        entries = [{"name": "Cisco", "type": "tree"}]
        data = {"data": {"repository": {"object": {"entries": entries}}}}

        self.assertEqual(self.api.get_tree_entries(data), entries)

    def test_missing_entries_returns_empty_list(self):
        data = {"data": {"repository": {"object": {}}}}

        self.assertEqual(self.api.get_tree_entries(data), [])


class GetTreeTestCase(TestCase):
    def setUp(self):
        self.api = GitHubGqlAPI(
            token='token',
            owner='netbox-community',
            repo='devicetype-library',
            branch='master',
            path='elevation-images',
        )

    @mock.patch.object(GitHubGqlAPI, 'get_query')
    def test_get_tree_batches_vendors_and_skips_missing_vendor_directories(self, mock_get_query):
        # A quoted manufacturer name must be carried in GraphQL variables, not
        # interpolated into the query text. The missing Juniper folder should
        # not prevent results for the other vendors from being returned.
        vendors = ['Cisco "Systems', 'Juniper', 'Dell']
        mock_get_query.side_effect = [
            {
                'data': {
                    'repository': {
                        'vendor_0': {
                            'entries': [
                                {'name': 'c9300-front.png', 'type': 'blob', 'oid': 'sha-cisco'},
                                {'name': 'nested', 'type': 'tree', 'oid': 'tree-cisco'},
                            ]
                        },
                        'vendor_1': None,
                    }
                }
            },
            {
                'data': {
                    'repository': {
                        'vendor_0': {
                            'entries': [
                                {'name': 'poweredge-front.png', 'type': 'blob', 'oid': 'sha-dell'},
                            ]
                        }
                    }
                }
            },
        ]

        result = self.api.get_tree(vendors, batch_size=2)

        self.assertEqual(
            result,
            {
                'Cisco "Systems': {
                    'c9300-front.png': {'sha': 'sha-cisco'},
                },
                'Dell': {
                    'poweredge-front.png': {'sha': 'sha-dell'},
                },
            },
        )
        self.assertEqual(mock_get_query.call_count, 2)

        first_query, first_variables = mock_get_query.call_args_list[0].args
        self.assertIn('$vendor_path_0', first_query)
        self.assertNotIn('Cisco "Systems', first_query)
        self.assertEqual(
            first_variables['vendor_path_0'],
            'master:elevation-images/Cisco "Systems',
        )
        self.assertEqual(
            first_variables['vendor_path_1'],
            'master:elevation-images/Juniper',
        )

    @mock.patch.object(GitHubGqlAPI, 'get_query')
    def test_get_tree_returns_empty_dict_without_request_for_empty_vendors(self, mock_get_query):
        self.assertEqual(self.api.get_tree([]), {})
        mock_get_query.assert_not_called()


class IterTreeBatchesTestCase(TestCase):
    def setUp(self):
        self.api = GitHubGqlAPI(
            token='token',
            owner='netbox-community',
            repo='devicetype-library',
            branch='master',
            path='device-types',
        )
        # Keep the test small while verifying more than one GitHub vendor batch.
        self.api.DEFAULT_VENDOR_BATCH_SIZE = 2

    @mock.patch.object(GitHubGqlAPI, 'get_query')
    def test_iter_tree_batches_batches_vendors_and_skips_non_tree_entries(self, mock_get_query):
        mock_get_query.side_effect = [
            # Root directory: README is a blob and must not be treated as vendor.
            {
                'data': {
                    'repository': {
                        'object': {
                            'entries': [
                                {'name': 'Cisco', 'type': 'tree'},
                                {'name': 'README.md', 'type': 'blob'},
                                {'name': 'Juniper', 'type': 'tree'},
                                {'name': 'Dell', 'type': 'tree'},
                            ]
                        }
                    }
                }
            },
            # First GraphQL vendor batch: Cisco and Juniper.
            {
                'data': {
                    'repository': {
                        'vendor_0': {
                            'entries': [
                                {'name': 'c9300.yaml', 'type': 'blob', 'oid': 'sha-cisco'},
                                {'name': 'subdirectory', 'type': 'tree', 'oid': 'tree-cisco'},
                            ]
                        },
                        'vendor_1': {
                            'entries': [
                                {'name': 'ex4300.yaml', 'type': 'blob', 'oid': 'sha-juniper'},
                            ]
                        },
                    }
                }
            },
            # Second GraphQL vendor batch: Dell.
            {
                'data': {
                    'repository': {
                        'vendor_0': {
                            'entries': [
                                {'name': 'r740.yaml', 'type': 'blob', 'oid': 'sha-dell'},
                                {'name': 'nested', 'type': 'tree', 'oid': 'tree-dell'},
                            ]
                        }
                    }
                }
            },
        ]

        batches = list(self.api.iter_tree_batches(batch_size=2))

        self.assertEqual(
            batches,
            [
                [
                    ('Cisco', 'c9300.yaml', 'sha-cisco'),
                    ('Juniper', 'ex4300.yaml', 'sha-juniper'),
                ],
                [('Dell', 'r740.yaml', 'sha-dell')],
            ],
        )
        # One root request plus two vendor-tree requests (2 vendors per request).
        self.assertEqual(mock_get_query.call_count, 3)

        first_vendor_query, first_vendor_variables = mock_get_query.call_args_list[1].args
        self.assertIn('vendor_0: object', first_vendor_query)
        self.assertIn('vendor_1: object', first_vendor_query)
        self.assertEqual(
            first_vendor_variables['vendor_path_0'],
            'master:device-types/Cisco',
        )
        self.assertEqual(
            first_vendor_variables['vendor_path_1'],
            'master:device-types/Juniper',
        )
        self.assertNotIn('README.md', first_vendor_variables.values())

    def test_iter_tree_batches_rejects_non_positive_batch_size(self):
        for batch_size in (0, -1):
            with self.subTest(batch_size=batch_size):
                with self.assertRaisesRegex(ValueError, 'batch_size must be greater than zero'):
                    list(self.api.iter_tree_batches(batch_size=batch_size))


class GetFilesTestCase(TestCase):
    def setUp(self):
        self.api = GitHubGqlAPI(
            token='token',
            owner='netbox-community',
            repo='devicetype-library',
            branch='master',
            path='device-types',
        )

    @mock.patch.object(GitHubGqlAPI, 'get_query')
    def test_get_files_batches_requests_and_merges_results(self, mock_get_query):
        mock_get_query.side_effect = [
            {
                'data': {
                    'repository': {
                        'file_0': {'text': ''},
                        'file_1': {'text': 'model: Cisco-2'},
                    }
                }
            },
            {
                'data': {
                    'repository': {
                        'file_0': None,
                        'file_1': {'text': 'model: Cisco-4'},
                    }
                }
            },
            {
                'data': {
                    'repository': {
                        'file_0': {'text': 'model: Cisco-5'},
                    }
                }
            },
        ]
        query_data = {
            'sha-1': 'Cisco/model-1.yaml',
            'sha-2': 'Cisco/model-2.yaml',
            'sha-3': 'Cisco/model-3.yaml',
            'sha-4': 'Cisco/model-4.yaml',
            'sha-5': 'Cisco/model-5.yaml',
        }

        with self.assertLogs('netbox_metatype_importer.graphql.gql', level='WARNING') as logs:
            result = self.api.get_files(query_data, batch_size=2)

        self.assertEqual(
            result,
            {
                'sha-2': 'model: Cisco-2',
                'sha-4': 'model: Cisco-4',
                'sha-5': 'model: Cisco-5',
            },
        )
        self.assertEqual(mock_get_query.call_count, 3)
        self.assertEqual(len(logs.records), 2)

        expected_batch_sizes = [2, 2, 1]
        expected_paths = [
            ['master:device-types/Cisco/model-1.yaml', 'master:device-types/Cisco/model-2.yaml'],
            ['master:device-types/Cisco/model-3.yaml', 'master:device-types/Cisco/model-4.yaml'],
            ['master:device-types/Cisco/model-5.yaml'],
        ]

        for call, expected_size, paths in zip(
            mock_get_query.call_args_list,
            expected_batch_sizes,
            expected_paths,
        ):
            query, variables = call.args
            file_variables = {key: value for key, value in variables.items() if key.startswith('file_path_')}

            self.assertEqual(len(file_variables), expected_size)
            self.assertEqual(
                [file_variables[f'file_path_{index}'] for index in range(expected_size)],
                paths,
            )
            self.assertIn('file_0: object', query)
            if expected_size > 1:
                self.assertIn('file_1: object', query)

    @mock.patch.object(GitHubGqlAPI, 'get_query')
    def test_get_files_uses_default_batch_size_of_fifty(self, mock_get_query):
        def build_response(query, variables):
            repository = {}
            for key in variables:
                if key.startswith('file_path_'):
                    index = key.rsplit('_', 1)[1]
                    repository[f'file_{index}'] = {'text': f'model: {variables[key]}'}
            return {'data': {'repository': repository}}

        mock_get_query.side_effect = build_response
        query_data = {f'sha-{index}': f'Cisco/model-{index}.yaml' for index in range(51)}

        result = self.api.get_files(query_data)

        self.assertEqual(len(result), 51)
        self.assertEqual(mock_get_query.call_count, 2)
        request_sizes = [
            sum(key.startswith('file_path_') for key in call.args[1]) for call in mock_get_query.call_args_list
        ]
        self.assertEqual(request_sizes, [50, 1])

    @mock.patch.object(GitHubGqlAPI, 'get_query')
    def test_get_files_returns_empty_dict_without_request_for_empty_input(self, mock_get_query):
        self.assertEqual(self.api.get_files({}), {})
        mock_get_query.assert_not_called()

    def test_get_files_rejects_non_positive_batch_size(self):
        query_data = {'sha-1': 'Cisco/model-1.yaml'}

        for batch_size in (0, -1):
            with self.subTest(batch_size=batch_size):
                with self.assertRaisesRegex(ValueError, 'chunk_size must be greater than zero'):
                    self.api.get_files(query_data, batch_size=batch_size)
