from extras.plugins import PluginConfig
from .version import __version__


class NetBoxMetatypeImporterConfig(PluginConfig):
    name = 'netbox_metatype_importer'
    verbose_name = 'MetaType Importer'
    description = 'Import MetaType from github repo'
    version = __version__
    author = 'Nikolay Yuzefovich'
    author_email = 'mgk.kolek@gmail.com'
    required_settings = []
    min_version = '3.3.99'
    max_version = '3.4.99'
    default_settings = {
        'repo_owner': 'netbox-community',
        'repo': 'metatype-library',
        'branch': 'master',
        'github_token': '',
        'use_gql': True,
    }


config = NetBoxMetatypeImporterConfig
