from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmpleadoViewSet, CargoViewSet

router = DefaultRouter()
router.register(r'empleados', EmpleadoViewSet)
router.register(r'cargos', CargoViewSet)
urlpatterns = [
    path('api/', include(router.urls)),
]
