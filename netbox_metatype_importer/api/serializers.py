from rest_framework import serializers

from netbox.api.serializers import NetBoxModelSerializer
from ..models import MetaType

__all__ = [
    'MetaTypeSerializer',
]


class MetaTypeSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedRelatedField(
        view_name='metatype-detail',
        lookup_field='name',
        read_only=True
    )

    class Meta:
        model = MetaType
        fields = '__all__'
