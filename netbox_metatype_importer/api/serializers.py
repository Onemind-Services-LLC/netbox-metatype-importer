from rest_framework import serializers

from ..models import MetaType


class MetaTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaType
        fields = "__all__"
