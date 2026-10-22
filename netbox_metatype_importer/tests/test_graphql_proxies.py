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
