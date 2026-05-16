from django.test import SimpleTestCase

from netbox_metatype_importer import config


class PluginConfigTest(SimpleTestCase):
    def test_netbox_46_compatibility_window(self):
        self.assertEqual(config.min_version, '4.6.0')
        self.assertEqual(config.max_version, '4.6.99')
