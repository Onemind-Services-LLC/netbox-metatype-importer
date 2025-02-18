from django.test import TestCase

from ..models import *


class TestMetaTypeImporter(TestCase):
    def test_metatype_creation(self):
        metatype = MetaType.objects.create(
            name='GS5104-1471-EC.yaml',
            vendor='Test Vendor',
            type=TypeChoices.TYPE_DEVICE,
            sha='sha256',
            download_url='https://www.testurl.com/',
            is_new=False,
            imported_dt=1,
            is_imported=True,
        )

        self.assertEqual(metatype.__str__(), 'GS5104-1471-EC')
        self.assertEqual(metatype.name, 'GS5104-1471-EC.yaml')
        self.assertEqual(metatype.vendor, 'Test Vendor')
        self.assertEqual(metatype.type, TypeChoices.TYPE_DEVICE)
        self.assertEqual(metatype.sha, 'sha256')
        self.assertEqual(metatype.download_url, 'https://www.testurl.com/')
        self.assertEqual(metatype.is_new, False)
        self.assertEqual(metatype.imported_dt, 1)
        self.assertEqual(metatype.is_imported, True)
