from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (EmpleadoViewSet,
                    CargoViewSet, 
                    GenerarLiquidacionView,
                    ListaContratosView, 
                    ReporteMensualView, 
                    PostulanteViewSet,
                    contratar_postulante,
                    AFPViewSet, 
                    SaludViewSet, 
                    CesantiaViewSet,
                    ReglasContratoViewSet
)

router = DefaultRouter()
router.register(r'empleados', EmpleadoViewSet)
router.register(r'cargos', CargoViewSet)
router.register(r'postulantes', PostulanteViewSet)
router.register(r'afp', AFPViewSet)
router.register(r'salud', SaludViewSet)
router.register(r'cesantia', CesantiaViewSet)
router.register(r'reglas-contrato', ReglasContratoViewSet)
urlpatterns = [
    path('api/', include(router.urls)),
     path('api/liquidaciones/generar/', GenerarLiquidacionView.as_view(), name='generar-liquidacion'),
     path('api/contratos/', ListaContratosView.as_view(), name='lista-contratos'),
     path('api/reporte-mensual/', ReporteMensualView.as_view(), name='reporte-mensual'),
     path('api/contratar/', contratar_postulante, name='contratar_postulante'),
]
