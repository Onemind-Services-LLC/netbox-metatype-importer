from django.test import TestCase

from ..filters import *
from ..models import *


class MetatypeImporterTests(TestCase):
    queryset = MetaType.objects.all()
    filterset = MetaTypeFilterSet

    @classmethod
    def setUpTestData(cls):
        meta_types = (
            MetaType(
                name='Test Metatype 1',
                vendor='Test Vendor 1',
                type=TypeChoices.TYPE_DEVICE,
                sha='sha256',
                download_url='https://www.testurl1.com/',
                is_new=False,
                imported_dt=1,
                is_imported=True,
            ),
            MetaType(
                name='Test Metatype 2',
                vendor='Test Vendor 2',
                type=TypeChoices.TYPE_DEVICE,
                sha='sha256',
                download_url='https://www.testurl2.com/',
                is_new=False,
                imported_dt=2,
                is_imported=True,
            ),
        )
        MetaType.objects.bulk_create(meta_types)

    def test_meta_types(self):
        meta_types = MetaType.objects.all()[:2]
        params = {"name": 'Test Metatype 1'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {"vendor": meta_types[0].vendor}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
