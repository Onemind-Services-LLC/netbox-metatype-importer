from netbox_metatype_importer.models import MetaType
from rest_framework import serializers
from rest_framework.serializers import HyperlinkedIdentityField


class MetaTypeSerializer(serializers.ModelSerializer):
    url = HyperlinkedIdentityField(view_name="plugins-api:netbox_metatype_importer-api:metatype-detail")

    class Meta:
        model = MetaType
        fields = "__all__"
        brief_fields = ("id", "url", "display", "name", "description")
