from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmpleadoViewSet, CargoViewSet, GenerarLiquidacionView, ListaContratosView, ReporteMensualView, PostulanteViewSet


router = DefaultRouter()
router.register(r'empleados', EmpleadoViewSet)
router.register(r'cargos', CargoViewSet)
router.register(r'postulantes', PostulanteViewSet)
urlpatterns = [
    path('api/', include(router.urls)),
     path('api/liquidaciones/generar/', GenerarLiquidacionView.as_view(), name='generar-liquidacion'),
     path('api/contratos/', ListaContratosView.as_view(), name='lista-contratos'),
     path('api/reporte-mensual/', ReporteMensualView.as_view(), name='reporte-mensual'),
]
