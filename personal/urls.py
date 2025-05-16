from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmpleadoViewSet, CargoViewSet, GenerarLiquidacionView, ListaContratosView

router = DefaultRouter()
router.register(r'empleados', EmpleadoViewSet)
router.register(r'cargos', CargoViewSet)
urlpatterns = [
    path('api/', include(router.urls)),
     path('api/liquidaciones/generar/', GenerarLiquidacionView.as_view(), name='generar-liquidacion'),
     path('api/contratos/', ListaContratosView.as_view(), name='lista-contratos'),
]
