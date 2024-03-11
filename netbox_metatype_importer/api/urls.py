from netbox.api.routers import NetBoxRouter

from . import views

router = NetBoxRouter()
router.APIRootView = views.MetaTypeRootView

router.register('device-types', views.DeviceTypeListViewSet, basename='device-types')
router.register('module-types', views.ModuleTypeListViewSet, basename="module-types")

router.register('device-type-load', views.MetaDeviceTypeLoadViewSet, basename='device-type-load')
router.register('module-type-load', views.MetaModuleTypeLoadViewSet, basename="module-type-load")

router.register('device-type-import', views.MetaDeviceTypeImportViewSet, basename='device-type-import')
router.register('module-type-import', views.MetaModuleTypeImportViewSet, basename="module-type-import")

urlpatterns = router.urls
