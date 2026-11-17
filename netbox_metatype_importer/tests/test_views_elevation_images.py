from django.test import TestCase, RequestFactory

from unittest import mock

from netbox_metatype_importer.choices import TypeChoices
from netbox_metatype_importer.models import MetaType
from netbox_metatype_importer.views import MetaDeviceTypeImportView


class ElevationImageImportViewTestCase(TestCase):
    def setUp(self):
        self.meta_type = MetaType.objects.create(
            name='test-device.yaml',
            vendor='Test Vendor',
            type=TypeChoices.TYPE_DEVICE,
            sha='test-device-sha',
            is_new=True,
            is_imported=False,
        )

    def test_import_fetches_elevation_tree_when_yaml_references_images(self):
        parsed_yaml = {
            'manufacturer': 'Test Vendor',
            'model': 'Test Device',
            'slug': 'test-device',
            'u_height': 1,
            'is_full_depth': True,
            'front_image': True,
        }
        device_type = mock.Mock(pk=123)
        import_form = mock.Mock()
        import_form.is_valid.return_value = True
        import_form.errors = {}
        import_form.save.return_value = device_type

        with (
            mock.patch('netbox_metatype_importer.views.GitHubGqlAPI') as mock_api_class,
            mock.patch('netbox_metatype_importer.views.BulkImportForm') as mock_bulk_form_class,
            mock.patch(
                'netbox_metatype_importer.views.Manufacturer.objects.get_or_create', return_value=(mock.Mock(), True)
            ),
            mock.patch('netbox_metatype_importer.views.related_object_forms', return_value={}),
            mock.patch('netbox_metatype_importer.views.save_image_from_url') as mock_save_image,
            mock.patch('netbox_metatype_importer.views.messages.success'),
            mock.patch('netbox_metatype_importer.views.reverse', return_value='/dcim/device-types/'),
            mock.patch('netbox_metatype_importer.views.redirect', return_value='/dcim/device-types/'),
        ):
            api = mock_api_class.return_value
            api.get_files.return_value = {'test-device-sha': 'manufacturer: Test Vendor'}
            api.get_tree.return_value = {
                'Test Vendor': {
                    'test-device-front.png': {'sha': 'image-sha'},
                }
            }

            bulk_form = mock.Mock()
            bulk_form.is_valid.return_value = True
            bulk_form.cleaned_data = {'data': parsed_yaml}
            mock_bulk_form_class.return_value = bulk_form

            view = MetaDeviceTypeImportView()
            view.get_return_url = mock.Mock(return_value='/meta-device-types/')
            view.model_form = mock.Mock(return_value=import_form)

            request = RequestFactory().post(
                '/meta-device-types/import/',
                {'pk': [str(self.meta_type.pk)]},
            )
            response = view.post(request)

        self.assertEqual(response, '/dcim/device-types/')
        api.get_tree.assert_called_once_with({'Test Vendor'})
        self.assertEqual(api.path, 'elevation-images')
        mock_save_image.assert_called_once_with(
            device_type,
            'https://raw.githubusercontent.com/netbox-community/devicetype-library/master/elevation-images/Test Vendor/test-device-front.png',
            'front_image',
        )

        self.meta_type.refresh_from_db()
        self.assertTrue(self.meta_type.is_imported)
        self.assertEqual(self.meta_type.imported_dt, device_type.pk)
