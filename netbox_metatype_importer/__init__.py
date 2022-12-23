from extras.plugins import PluginConfig
from .version import __version__


class NetBoxMetatypeImporterConfig(PluginConfig):
    name = 'netbox_metatype_importer'
    verbose_name = 'MetaType Importer'
    description = 'Import MetaType from github repo'
    version = __version__
    author = 'Abhimanyu Saharan'
    author_email = 'asaharan@onemindservices.com'
    required_settings = []
    min_version = '3.4.1'
    max_version = '3.4.99'
    default_settings = {
        'repo_owner': 'netbox-community',
        'repo': 'devicetype-library',
        'branch': 'master',
        'github_token': '',
        'use_gql': True,
    }


config = NetBoxMetatypeImporterConfig
