import requests
from django.conf import settings

from jinja2 import Template


class GQLError(Exception):
    default_message = None

    def __init__(self, message=None):
        if message is None:
            self.message = self.default_message
        else:
            self.message = message
        super().__init__(message)


class GitHubGqlAPI:
    tree_query = """
{
  repository(owner: "{{ owner }}", name: "{{ repo }}") {
    object(expression: "{{ branch }}:{{ path }}") {
      ... on Tree {
        entries {
          name
          type
          object {
            ... on Tree {
              entries {
                name
                type
                oid
              }
            }
          }
        }
      }
    }
  }
}
"""
    files_query = """
{
    repository(owner: "{{ owner }}", name: "{{ repo }}") {
        {% for sha, path in data.items() %}
        sha_{{ sha }}: object(expression: "{{ branch }}:{{ root_path }}/{{ path }}") {
            ... on Blob {
                text
            }
        }
        {% endfor %}
    }
}
"""

    def __init__(self, url='https://api.github.com/graphql', token=None, owner=None, repo=None, branch=None, path=None):
        self.session = requests.session()

        # Honor environment proxies and NetBox's HTTP_PROXIES setting if provided
        # - trust_env ensures requests respects http_proxy/https_proxy env vars
        # - settings.HTTP_PROXIES (if set) mirrors NetBox's outbound HTTP config
        self.session.trust_env = True
        http_proxies = getattr(settings, 'HTTP_PROXIES', None)
        if http_proxies:
            # Merge rather than replace to preserve any existing adapter defaults
            self.session.proxies.update(http_proxies)

        self.session.headers.update({'Authorization': f'token {token}'})
        self.path = path
        self.url = url
        self.token = token
        self.owner = owner
        self.repo = repo
        self.branch = branch

    def get_query(self, query):
        response = self.session.post(url=self.url, json={'query': query})

        # Handle explicit HTTP auth failures from GitHub
        if response.status_code == 401:
            raise GQLError('GitHub token invalid or expired (401 Unauthorized)')

        try:
            result = response.json()
        except requests.exceptions.JSONDecodeError:
            raise GQLError(f'Cannot parse response from GitHub: {response.text}')

        # GraphQL often returns 200 with an 'errors' array when credentials are bad
        errors = result.get('errors') or []
        if errors:
            # Prefer a friendly message on auth-related errors
            first_msg = (errors[0] or {}).get('message', '')
            msg_l = first_msg.lower() if isinstance(first_msg, str) else ''
            if 'bad credentials' in msg_l or 'expired' in msg_l or 'unauthorized' in msg_l:
                raise GQLError('GitHub token invalid or expired')
            # Fallback to the original message
            raise GQLError(message=first_msg or 'Unknown GraphQL error from GitHub')

        if response.ok:
            return result
        else:
            # Non-JSON or non-standard error payloads
            raise GQLError(result.get('message') or f'GitHub API request failed: {response.status_code}')

    def get_tree(self):
        result = {}
        template = Template(self.tree_query)
        query = template.render(owner=self.owner, repo=self.repo, branch=self.branch, path=self.path)
        data = self.get_query(query)
        if not data:
            return result

        try:
            data['data']['repository']['object']['entries']
        except TypeError:
            return None

        for vendor in data['data']['repository']['object']['entries']:
            result[vendor['name']] = {}
            for model in vendor['object'].get('entries', []):
                result[vendor['name']].update({model['name']: {'sha': model['oid']}})
        return result

    def get_files(self, query_data):
        """
        data = {'sha': 'vendor/model'}
        result = {'sha': 'yaml_text'}
        """
        result = {}
        if not query_data:
            return result
        template = Template(self.files_query)
        query = template.render(
            owner=self.owner, repo=self.repo, branch=self.branch, data=query_data, root_path=self.path
        )
        data = self.get_query(query)
        for k, v in data['data']['repository'].items():
            result[k.replace('sha_', '')] = v['text']
        return result
