from netbox.api.routers import NetBoxRouter

from .views import (
    DeviceTypeListViewSet,
    ModuleTypeListViewSet,
    MetaDeviceTypeLoadViewSet,
    MetaModuleTypeLoadViewSet,
    MetaDeviceTypeImportViewSet,
    MetaModuleTypeImportViewSet,
    MetaTypeRootView,
)

router = NetBoxRouter()
router.APIRootView = MetaTypeRootView

router.register('device-types', DeviceTypeListViewSet, basename='device-types')
router.register('module-types', ModuleTypeListViewSet, basename="module-types")

router.register('device-type-load', MetaDeviceTypeLoadViewSet, basename='device-type-load')
router.register('module-type-load', MetaModuleTypeLoadViewSet, basename="module-type-load")

router.register('device-type-import', MetaDeviceTypeImportViewSet, basename='device-type-import')
router.register('module-type-import', MetaModuleTypeImportViewSet, basename="module-type-import")

urlpatterns = router.urls
