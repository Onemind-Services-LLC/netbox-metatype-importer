from rest_framework import serializers

from netbox.api.serializers import WritableNestedSerializer
from ..models import MetaType

__all__ = [
    'NestedMetaTypeSerializer',
]


class NestedMetaTypeSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedRelatedField(
        view_name='metatype-detail',
        lookup_field='name',
        read_only=True
    )

    class Meta:
        model = MetaType
        fields = ('display', 'id', 'name', 'url')
