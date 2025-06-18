from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmpleadoViewSet,
    CargoViewSet,
    GenerarLiquidacionView,
    ListaContratosView,
    ReporteMensualView,
    PostulanteViewSet,
    contratar_postulante,
    AFPViewSet,
    SaludViewSet,
    CesantiaViewSet,
    ReglasContratoViewSet,
    DepartamentoViewSet,
    TipoContratoViewSet,
    GrupoHorarioViewSet,
    HorarioViewSet,
    HorarioEmpleadoViewSet,
    actualizar_horarios_empleados,
    crear_multiples_horarios_empleado,
    eliminar_varios_horarios_empleado,
    HistorialCambioViewSet,
    desvincular_empleado,
    cambiar_estado_empleado,
    empleados_sin_contrato,
    ContratoViewSet,
)

router = DefaultRouter()
router.register(r"empleados", EmpleadoViewSet)
router.register(r"cargos", CargoViewSet)
router.register(r"postulantes", PostulanteViewSet)
router.register(r"afp", AFPViewSet)
router.register(r"salud", SaludViewSet)
router.register(r"cesantia", CesantiaViewSet)
router.register(r"reglas-contrato", ReglasContratoViewSet)
router.register(r"tipo-contrato", TipoContratoViewSet, basename="tipo-contrato")
router.register(r'contratos', ContratoViewSet)

router.register(r"departamentos", DepartamentoViewSet, basename="departamentos")
router.register(r"grupo-horarios", GrupoHorarioViewSet)
router.register(r"horarios", HorarioViewSet)
router.register(r"horario-empleado", HorarioEmpleadoViewSet)
router.register(
    r"historial-cambios", HistorialCambioViewSet, basename="historial-cambios"
)
urlpatterns = [
    path("api/", include(router.urls)),
    path(
        "api/liquidaciones/generar/",
        GenerarLiquidacionView.as_view(),
        name="generar-liquidacion",
    ),
    path("api/contratos/", ListaContratosView.as_view(), name="lista-contratos"),
    path("api/reporte-mensual/", ReporteMensualView.as_view(), name="reporte-mensual"),
    path("api/contratar/", contratar_postulante, name="contratar_postulante"),
    path(
        "api/desvincular_empleado/", desvincular_empleado, name="desvincular_empleado"
    ),
    path(
        "api/cambiar_estado_empleado/",
        cambiar_estado_empleado,
        name="cambiar_estado_empleado",
    ),
    path(
        "api/horario-empleado/editar-multiples/",
        actualizar_horarios_empleados,
        name="editar_horarios_empleados",
    ),
    path(
        "api/asignacion-horaria-masiva/",
        crear_multiples_horarios_empleado,
        name="crear_multiples_horarios_empleado",
    ),
    path("api/horario-empleado-eliminar-multiples/", eliminar_varios_horarios_empleado),
    path('empleados-sin-contrato/', empleados_sin_contrato),
]
