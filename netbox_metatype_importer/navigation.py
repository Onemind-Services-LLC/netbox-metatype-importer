from netbox.plugins import PluginMenuItem

menu_items = (
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
