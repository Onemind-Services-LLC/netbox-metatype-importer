from rest_framework.routers import APIRootView

from netbox.api.viewsets import NetBoxModelViewSet
from .serializers import MetaTypeSerializer
from ..choices import TypeChoices
from ..filters import MetaTypeFilterSet
from ..models import MetaType


class MetaTypeImporterAPIRootView(APIRootView):
    """
    Meta Type Importer API Root
    """

    def get_view_name(self):
        return 'Meta Type Importer API'


class DeviceTypeViewSet(NetBoxModelViewSet):
    queryset = MetaType.objects.filter(type=TypeChoices.TYPE_DEVICE)
    serializer_class = MetaTypeSerializer
    filterset_class = MetaTypeFilterSet


class ModuleTypeViewSet(NetBoxModelViewSet):
    queryset = MetaType.objects.filter(type=TypeChoices.TYPE_MODULE)
    serializer_class = MetaTypeSerializer
    filterset_class = MetaTypeFilterSet
