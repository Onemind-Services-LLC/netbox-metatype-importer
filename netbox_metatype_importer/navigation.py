from django.conf import settings
from extras.plugins import PluginMenuItem, PluginMenu

plugins_settings = settings.PLUGINS_CONFIG.get('netbox_metatype_importer')

menu_buttons = (
    PluginMenuItem(
        link='plugins:netbox_metatype_importer:metadevicetype_list',
        link_text='DeviceType Import',
        permissions=['netbox_metatype_importer.view_metadevicetype'],
    ),
    PluginMenuItem(
        link='plugins:netbox_metatype_importer:metamoduletype_list',
        link_text='ModuleType Import',
        permissions=['netbox_metatype_importer.view_metadevicetype'],
    ),
)
if plugins_settings.get('top_level_menu'):
    menu = PluginMenu(
        label='Metatype Importer',
        groups=(('Metatype Importer', menu_buttons),),
        icon_class='mdi mdi-account-settings',
    )
else:
    menu_items = menu_buttons
