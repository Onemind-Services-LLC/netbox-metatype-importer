from django.test import TestCase, override_settings

from netbox_metatype_importer.graphql.gql import GitHubGqlAPI


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
