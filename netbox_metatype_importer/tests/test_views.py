import yaml
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from dcim.models import (
    DeviceType,
    FrontPortTemplate,
    Manufacturer,
    PortTemplateMapping,
    RearPortTemplate,
)
from unittest.mock import patch

from ..choices import TypeChoices
from ..models import MetaType
from ..graphql.gql import GitHubGqlAPI


class TestMetaDeviceTypeImportView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username="test-importer",
            email="test@example.com",
            password="test-password",
        )
        cls.metatype = MetaType.objects.create(
            name="test-device.yaml",
            vendor="Test Vendor",
            type=TypeChoices.TYPE_DEVICE,
            sha="test-sha",
            download_url="https://example.com/test-device.yaml",
            is_new=False,
            is_imported=False,
        )

    @patch.object(GitHubGqlAPI, "get_tree", return_value={})
    @patch.object(GitHubGqlAPI, "get_files")
    def test_import_device_type_with_front_and_rear_ports(self, mock_get_files, mock_get_tree):
        device_type_data = {
            "manufacturer": "Test Vendor",
            "model": "Test Device",
            "slug": "test-device",
            "u_height": 1,
            "is_full_depth": True,
            "front-ports": [
                {
                    "name": "Front Port 1",
                    "type": "8p8c",
                    "positions": 1,
                },
            ],
            "rear-ports": [
                {
                    "name": "Rear Port 1",
                    "type": "8p8c",
                    "positions": 1,
                },
            ],
            "port-mappings": [
                {
                    "front_port": "Front Port 1",
                    "front_port_position": 1,
                    "rear_port": "Rear Port 1",
                    "rear_port_position": 1,
                },
            ],
        }
        mock_get_files.return_value = {
            "test-sha": yaml.safe_dump(device_type_data),
        }

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("plugins:netbox_metatype_importer:metadevicetype_import"),
            {"pk": [self.metatype.pk]},
        )

        self.assertEqual(response.status_code, 302)

        manufacturer = Manufacturer.objects.get(slug="test-vendor")
        device_type = DeviceType.objects.get(
            manufacturer=manufacturer,
            model="Test Device",
        )

        front_port = FrontPortTemplate.objects.get(
            device_type=device_type,
            name="Front Port 1",
        )
        rear_port = RearPortTemplate.objects.get(
            device_type=device_type,
            name="Rear Port 1",
        )

        self.assertEqual(
            FrontPortTemplate.objects.filter(device_type=device_type).count(),
            1,
        )
        self.assertEqual(
            RearPortTemplate.objects.filter(device_type=device_type).count(),
            1,
        )
        self.assertTrue(
            PortTemplateMapping.objects.filter(
                front_port=front_port,
                front_port_position=1,
                rear_port=rear_port,
                rear_port_position=1,
            ).exists()
        )

        self.metatype.refresh_from_db()
        self.assertTrue(self.metatype.is_imported)
        self.assertEqual(self.metatype.imported_dt, device_type.pk)
