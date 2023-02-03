from netbox.api.routers import NetBoxRouter
from . import views

app_name = 'netbox_metatype_importer'

router = NetBoxRouter()
router.register('device-type', views.DeviceTypeViewSet, basename='device-type')
router.register('module-type', views.ModuleTypeViewSet)

urlpatterns = router.urls
