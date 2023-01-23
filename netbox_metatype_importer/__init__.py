from extras.plugins import PluginConfig

from importlib.metadata import metadata

metadata = metadata('netbox_metatype_importer')


class NetBoxMetatypeImporterConfig(PluginConfig):
    name = metadata.get('Name').replace('-', '_')
    verbose_name = metadata.get('Summary')
    description = metadata.get('Long-Description')
    version = metadata.get('Version')
    author = metadata.get('Author')
    author_email = metadata.get('Author-email')
    min_version = '3.4.0'
    max_version = '3.4.99'
    default_settings = {
        'repo_owner': 'netbox-community',
        'repo': 'devicetype-library',
        'branch': 'master',
        'github_token': ''
    }
    required_settings = ['github_token']


config = NetBoxMetatypeImporterConfig
