from rest_framework import serializers

from netbox.api.serializers import WritableNestedSerializer
from ..models import MetaType

__all__ = [
    'NestedMetaTypeSerializer',
]


class NestedMetaTypeSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_metatype_importer-api:metatype-detail'
    )

    class Meta:
        model = MetaType
        fields = '__all__'
