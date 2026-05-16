from dcim import forms
from django.test import SimpleTestCase

from netbox_metatype_importer.utils import related_object_forms


class RelatedObjectFormsTest(SimpleTestCase):
    def test_netbox_46_port_mappings_are_imported(self):
        self.assertIs(related_object_forms()['port-mappings'], forms.PortTemplateMappingImportForm)
