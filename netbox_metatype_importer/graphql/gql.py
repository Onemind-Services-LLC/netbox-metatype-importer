import logging
import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class GQLError(Exception):
    default_message = None

    def __init__(self, message=None):
        if message is None:
            self.message = self.default_message
        else:
            self.message = message
        super().__init__(message)


class GitHubGqlAPI:
    # Keep GraphQL request batching separate from the database batch size used
    # by iter_tree_batches(). Twenty vendor trees are requested per HTTP call.
    DEFAULT_VENDOR_BATCH_SIZE = 20
    # Keep file-query batching independent from vendor and database batching.
    DEFAULT_FILE_BATCH_SIZE = 50

    VENDOR_QUERY = """
    query GetVendorDirectory(
        $owner: String!,
        $repo: String!,
        $path: String!
    ) {
        repository(owner: $owner, name: $repo) {
            object(expression: $path) {
                ... on Tree {
                    entries {
                        name
                        type
                    }
                }
            }
        }
    }
    """

    def __init__(
        self,
        url="https://api.github.com/graphql",
        token=None,
        owner=None,
        repo=None,
        branch=None,
        path=None,
    ):
        self.session = requests.session()
        # Honor environment proxies and NetBox's HTTP_PROXIES setting if provided.
        self.session.trust_env = True
        http_proxies = getattr(settings, "HTTP_PROXIES", None)
        if http_proxies:
            self.session.proxies.update(http_proxies)

        self.session.headers.update({"Authorization": f"token {token}"})
        self.path = path
        self.url = url
        self.token = token
        self.owner = owner
        self.repo = repo
        self.branch = branch

    def get_query(self, query, variables=None):
        payload = {"query": query}
        if variables is not None:
            payload["variables"] = variables

        response = self.session.post(url=self.url, json=payload)

        if response.status_code == 401:
            raise GQLError("GitHub token invalid or expired (401 Unauthorized)")

        try:
            result = response.json()
        except requests.exceptions.JSONDecodeError as exc:
            raise GQLError(f"Cannot parse response from GitHub: {response.text}") from exc

        if not isinstance(result, dict):
            raise GQLError("GitHub returned an unexpected GraphQL response.")

        # GitHub may return GraphQL errors with HTTP 200, so inspect errors
        # before relying on the HTTP status code.
        errors = result.get("errors") or []
        if errors:
            first_error = errors[0] or {}
            first_message = first_error.get("message", "")
            message_lower = first_message.lower() if isinstance(first_message, str) else ""
            if any(phrase in message_lower for phrase in ("bad credentials", "expired", "unauthorized")):
                raise GQLError("GitHub token invalid or expired")
            raise GQLError(first_message or "Unknown GraphQL error from GitHub")

        if response.ok:
            return result

        raise GQLError(result.get("message") or f"GitHub API request failed: {response.status_code}")

    @staticmethod
    def _chunks(items, chunk_size):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        items = list(items)
        for start in range(0, len(items), chunk_size):
            yield items[start : start + chunk_size]

    def get_tree_entries(self, data):
        if not data:
            raise GQLError("GitHub returned an empty response.")

        errors = data.get("errors")
        if errors:
            raise GQLError(f"GitHub GraphQL error: {errors}")

        repository = (data.get("data") or {}).get("repository")
        if repository is None:
            raise GQLError(
                "Repository not found or inaccessible. Check the repository owner, name, and token permissions."
            )

        tree = repository.get("object")
        if tree is None:
            raise GQLError("GitHub could not find the configured branch or path. Check the branch and path settings.")

        return tree.get("entries") or []

    def _get_vendor_trees(self, vendors, batch_size=DEFAULT_VENDOR_BATCH_SIZE):
        # Preserve the input order while avoiding duplicate vendor requests.
        vendors = list(dict.fromkeys(vendors or []))
        if not vendors:
            return {}

        result = {}

        for vendor_batch in self._chunks(vendors, batch_size):
            variable_definitions = ["$owner: String!", "$repo: String!"]
            variables = {
                "owner": self.owner,
                "repo": self.repo,
            }
            selections = []
            aliases = []

            for index, vendor_name in enumerate(vendor_batch):
                variable_name = f"vendor_path_{index}"
                alias = f"vendor_{index}"

                variable_definitions.append(f"${variable_name}: String!")
                variables[variable_name] = f"{self.branch}:{self.path}/{vendor_name}"
                selections.append(
                    f"""
                    {alias}: object(expression: ${variable_name}) {{
                        ... on Tree {{
                            entries {{
                                name
                                type
                                oid
                            }}
                        }}
                    }}
                    """
                )
                aliases.append((alias, vendor_name))

            query = f"""
            query GetVendorTrees(
                {", ".join(variable_definitions)}
            ) {{
                repository(owner: $owner, name: $repo) {{
                    {" ".join(selections)}
                }}
            }}
            """

            data = self.get_query(query, variables)
            repository = (data.get("data") or {}).get("repository")
            if repository is None:
                raise GQLError(
                    "Repository not found or inaccessible. Check the repository owner, name, and token permissions."
                )

            for alias, vendor_name in aliases:
                tree = repository.get(alias)
                # A vendor directory can disappear between discovery and this
                # request. Preserve other results in the same batch.
                if tree is None:
                    continue

                entries = tree.get("entries") or []
                result[vendor_name] = {
                    entry["name"]: {"sha": entry["oid"]}
                    for entry in entries
                    if entry.get("type") == "blob" and entry.get("name") and entry.get("oid")
                }

        return result

    def get_tree(self, vendors, batch_size=DEFAULT_VENDOR_BATCH_SIZE):
        return self._get_vendor_trees(vendors, batch_size=batch_size)

    def iter_tree_batches(self, batch_size=300):
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")

        variables = {
            "owner": self.owner,
            "repo": self.repo,
            "path": f"{self.branch}:{self.path}",
        }
        data = self.get_query(self.VENDOR_QUERY, variables)
        entries = self.get_tree_entries(data)
        vendors = [entry["name"] for entry in entries if entry.get("type") == "tree" and entry.get("name")]

        batch = []
        for vendor_batch in self._chunks(vendors, self.DEFAULT_VENDOR_BATCH_SIZE):
            vendor_trees = self._get_vendor_trees(
                vendor_batch,
                batch_size=self.DEFAULT_VENDOR_BATCH_SIZE,
            )

            for vendor_name in vendor_batch:
                for model_name, model_data in vendor_trees.get(vendor_name, {}).items():
                    batch.append((vendor_name, model_name, model_data["sha"]))

                    if len(batch) >= batch_size:
                        yield batch
                        batch = []

        if batch:
            yield batch

    def get_files(self, query_data, batch_size=DEFAULT_FILE_BATCH_SIZE):
        if not query_data:
            return {}

        result = {}

        for file_batch in self._chunks(query_data.items(), batch_size):
            variable_definitions = ["$owner: String!", "$repo: String!"]
            variables = {
                "owner": self.owner,
                "repo": self.repo,
            }
            selections = []
            aliases = []

            for index, (sha, path) in enumerate(file_batch):
                variable_name = f"file_path_{index}"
                alias = f"file_{index}"

                variable_definitions.append(f"${variable_name}: String!")
                variables[variable_name] = f"{self.branch}:{self.path}/{path}"
                selections.append(
                    f"""
                    {alias}: object(expression: ${variable_name}) {{
                        ... on Blob {{
                            text
                        }}
                    }}
                    """
                )
                aliases.append((alias, sha, path))

            query = f"""
            query GetFiles(
                {", ".join(variable_definitions)}
            ) {{
                repository(owner: $owner, name: $repo) {{
                    {" ".join(selections)}
                }}
            }}
            """

            data = self.get_query(query, variables)
            repository = (data.get("data") or {}).get("repository")
            if repository is None:
                raise GQLError(
                    "Repository not found or inaccessible. Check the repository owner, name, and token permissions."
                )

            for alias, sha, path in aliases:
                blob = repository.get(alias)
                content = blob.get("text") if isinstance(blob, dict) else None

                if not isinstance(content, str) or not content.strip():
                    logger.warning(
                        "Skipping GitHub file with missing or empty content: path=%s sha=%s",
                        path,
                        sha,
                    )
                    continue

                result[sha] = content

        return result
