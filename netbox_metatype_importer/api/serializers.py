from rest_framework import serializers

from netbox_metatype_importer.models import MetaType


class MetaTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaType
        fields = "__all__"
        brief_fields = ("id", "name", "vendor")
