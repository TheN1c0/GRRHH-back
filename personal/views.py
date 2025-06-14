from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import (
    AFP,
    Cargo,
    Contrato,
    DatosPrevisionales,
    Empleado,
    Empleador,
    Haber,
    Liquidacion,
    OtroDescuento,
    ParametroSistema,
    Salud,
    SeguroCesantia,
    TipoDescuento,
    GrupoHorario,
    Horario,
    HorarioEmpleado,
    HistorialCambio,
    Asistencia,
)
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils.timezone import datetime, now
from django.db import models
from rest_framework.decorators import api_view, permission_classes
from .models import (
    Empleado,
    Contrato,
    DatosPrevisionales,
    AFP,
    Salud,
    SeguroCesantia,
    Cargo,
    Empleador,
)
from personal.utils.mixins import HistorialMixin


from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from .pagination import EmpleadoPagination


class EmpleadoViewSet(HistorialMixin, viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]

    search_fields = ["rut", "primer_nombre", "apellido_paterno", "apellido_materno"]

    filterset_fields = ["cargo", "empleador", "cargo__departamento", "estado"]
    pagination_class = EmpleadoPagination


class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if Empleado.objects.filter(cargo=instance).exists():
            return Response(
                {
                    "detail": "No se puede eliminar este cargo porque tiene empleados asignados."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class GenerarLiquidacionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LiquidacionInputSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            contrato = Contrato.objects.get(id=data["contrato_id"])
            empleado = contrato.empleado
            previsionales = DatosPrevisionales.objects.get(empleado=empleado)

            # Calcular gratificación
            IMM = Decimal("500000")  # o traer desde ParametroSistema
            if data["gratificacion_tipo"] == "legal":
                tope = (IMM * Decimal("4.75")) / 12
                gratificacion = min(contrato.sueldo_base * Decimal("0.25"), tope)
            else:
                gratificacion = contrato.sueldo_base / Decimal("12")
            empleador = empleado.empleador

            # Crear Liquidación con campos congelados
            liquidacion = Liquidacion.objects.create(
                contrato=contrato,
                periodo_inicio=data["periodo_inicio"],
                periodo_termino=data["periodo_termino"],
                sueldo_base=contrato.sueldo_base,
                gratificacion=gratificacion,
                sueldo_bruto=contrato.sueldo_base + gratificacion,
                rut_empleado=empleado.rut,
                nombre_empleado=f"{empleado.primer_nombre} {empleado.otros_nombres or ''} {empleado.apellido_paterno} {empleado.apellido_materno}",
                cargo_empleado=empleado.cargo.nombre,
                tipo_contrato=contrato.tipo_contrato,
                fecha_ingreso=contrato.fecha_inicio,
                nombre_afp=previsionales.afp.nombre,
                porcentaje_afp=previsionales.afp.porcentaje_cotizacion,
                comision_afp=Decimal("1.44"),  # ejemplo fijo
                nombre_salud=previsionales.salud.nombre or previsionales.salud.tipo,
                tipo_salud=previsionales.salud.tipo,
                porcentaje_salud=previsionales.salud.porcentaje_cotizacion,
                nombre_seguro_cesantia=previsionales.seguro_cesantia.nombre,
                porcentaje_cesantia_trabajador=previsionales.seguro_cesantia.porcentaje_trabajador,
                porcentaje_cesantia_empleador=previsionales.seguro_cesantia.porcentaje_empleador,
                razon_social_empleador=empleador.nombre,
                rut_empleador=empleador.rut,
                direccion_empleador=empleador.direccion,
            )

            total_haberes = contrato.sueldo_base + gratificacion

            for h in data["haberes"]:
                Haber.objects.create(liquidacion=liquidacion, **h)
                total_haberes += h["monto"]

            total_descuentos = Decimal("0")
            for d in data["descuentos"]:
                tipo, _ = TipoDescuento.objects.get_or_create(nombre=d["tipo"])
                OtroDescuento.objects.create(
                    liquidacion=liquidacion,
                    tipo=tipo,
                    monto=d["monto"],
                    descripcion=d.get("descripcion", ""),
                )
                total_descuentos += d["monto"]

            # Puedes incluir descuentos legales acá también

            sueldo_liquido = total_haberes - total_descuentos
            liquidacion.total_haberes = total_haberes
            liquidacion.total_descuentos = total_descuentos
            liquidacion.sueldo_liquido = sueldo_liquido
            liquidacion.save()

            pdf_data = generar_pdf_liquidacion(liquidacion)
            if pdf_data:
                response = HttpResponse(pdf_data, content_type="application/pdf")
                response["Content-Disposition"] = (
                    f'attachment; filename="liquidacion_{liquidacion.id}.pdf"'
                )
                return response
            else:
                return Response({"error": "Error al generar el PDF"}, status=500)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def generar_pdf_liquidacion(liquidacion):
    template_path = "pdf/liquidacion.html"
    context = {"liquidacion": liquidacion}
    html = render_to_string(template_path, context)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)

    if not pdf.err:
        return result.getvalue()
    return None


class ListaContratosView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        contratos = Contrato.objects.select_related("empleado", "empleado__cargo").all()
        serializer = ContratoEmpleadoSerializer(contratos, many=True)
        return Response(serializer.data)


class ReporteMensualView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mes = int(request.GET.get("mes"))
        anio = int(request.GET.get("anio"))

        # Liquidaciones
        liquidaciones = Liquidacion.objects.filter(
            periodo_inicio__month=mes, periodo_inicio__year=anio
        )

        empleados_pagados = (
            liquidaciones.values("contrato__empleado").distinct().count()
        )
        sueldo_bruto_total = sum(l.sueldo_bruto or 0 for l in liquidaciones)
        total_descuentos = sum(l.total_descuentos or 0 for l in liquidaciones)
        sueldo_liquido_total = sum(l.sueldo_liquido or 0 for l in liquidaciones)

        # Contratos activos durante el mes
        contratos = Contrato.objects.filter(
            fecha_inicio__lte=datetime(anio, mes, 28),
        ).filter(
            models.Q(fecha_fin__isnull=True)
            | models.Q(fecha_fin__gte=datetime(anio, mes, 1))
        )
        total_empleados_contrato = contratos.count()

        porcentaje_pagado = (
            (empleados_pagados / total_empleados_contrato) * 100
            if total_empleados_contrato > 0
            else 0
        )

        # Ausentismo laboral
        dias_mes = 30  # puedes reemplazar con calendar.monthrange(anio, mes)[1]
        total_posibles = total_empleados_contrato * dias_mes

        asistencias = Asistencia.objects.filter(fecha__month=mes, fecha__year=anio)

        asistencias_presentes = (
            asistencias.exclude(estado="ausente").exclude(estado="justificado").count()
        )
        dias_justificados = asistencias.filter(estado="justificado").count()

        dias_ausentes = total_posibles - asistencias_presentes - dias_justificados
        ausentismo_laboral = (
            (dias_ausentes / total_posibles) * 100 if total_posibles > 0 else 0
        )

        return Response(
            {
                "mes": mes,
                "anio": anio,
                "empleados_pagados": empleados_pagados,
                "sueldo_bruto_total": sueldo_bruto_total,
                "total_descuentos": total_descuentos,
                "sueldo_liquido_total": sueldo_liquido_total,
                "porcentaje_pagado": round(porcentaje_pagado, 2),
                "ausentismo_laboral": round(ausentismo_laboral, 2),
            }
        )


class PostulanteViewSet(viewsets.ModelViewSet):

    queryset = Postulante.objects.all().order_by("-fecha_postulacion")
    serializer_class = PostulanteSerializer

    def perform_create(self, serializer):
        postulante = serializer.save()
        postulante.procesar_curriculum()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def contratar_postulante(request):
    data = request.data
    emp_data = data.get("empleado")
    if not emp_data:
        return Response({"error": "Faltan los datos del empleado"}, status=400)

    # Validar existencia de cargo
    try:
        cargo = Cargo.objects.get(pk=emp_data["cargo"])
    except Cargo.DoesNotExist:
        return Response({"error": "El cargo seleccionado no existe"}, status=400)

    # Validar existencia de empleador
    try:
        empleador = Empleador.objects.get(pk=emp_data["empleador"])
    except Empleador.DoesNotExist:
        return Response({"error": "El empleador indicado no existe"}, status=400)

    if not emp_data.get("fecha_nacimiento"):
        return Response({"error": "La fecha de nacimiento es obligatoria"}, status=400)

    try:
        fecha_nac = datetime.strptime(emp_data["fecha_nacimiento"], "%Y-%m-%d").date()
    except ValueError:
        return Response(
            {"error": "Formato de fecha de nacimiento inválido. Usa YYYY-MM-DD"},
            status=400,
        )

    try:
        # 1. Crear Empleado

        cargo = Cargo.objects.get(pk=emp_data["cargo"])
        empleador = Empleador.objects.get(pk=emp_data["empleador"])

        empleado = Empleado.objects.create(
            rut=emp_data["rut"],
            primer_nombre=emp_data["primer_nombre"],
            otros_nombres=emp_data.get("otros_nombres", ""),
            apellido_paterno=emp_data["apellido_paterno"],
            apellido_materno=emp_data["apellido_materno"],
            fecha_nacimiento=fecha_nac,
            direccion=emp_data["direccion"],
            telefono=emp_data["telefono"],
            cargo=cargo,
            empleador=empleador,
            creado_por=request.user,
        )

        # 2. Crear Contrato
        contrato_data = data["contrato"]
        tipo_contrato_obj = TipoContrato.objects.get(pk=contrato_data["tipo_contrato"])
        contrato_data = data["contrato"]
        Contrato.objects.create(
            empleado=empleado,
            tipo_contrato=tipo_contrato_obj,
            fecha_inicio=contrato_data["fecha_inicio"],
            fecha_fin=contrato_data.get("fecha_fin"),
            sueldo_base=contrato_data["sueldo_base"],
        )

        # 3. Crear Datos Previsionales
        previsionales = data["prevision"]
        DatosPrevisionales.objects.create(
            empleado=empleado,
            afp=AFP.objects.get(pk=previsionales["afp"]),
            salud=Salud.objects.get(pk=previsionales["salud"]),
            seguro_cesantia=SeguroCesantia.objects.get(
                pk=previsionales["seguro_cesantia"]
            ),
        )

        return Response(
            {"mensaje": "Empleado contratado con éxito"}, status=status.HTTP_201_CREATED
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AFPViewSet(viewsets.ModelViewSet):
    queryset = AFP.objects.all()
    serializer_class = AFPSerializer
    permission_classes = [IsAuthenticated]


class SaludViewSet(viewsets.ModelViewSet):
    queryset = Salud.objects.all()
    serializer_class = SaludSerializer
    permission_classes = [IsAuthenticated]


class CesantiaViewSet(viewsets.ModelViewSet):
    queryset = SeguroCesantia.objects.all()
    serializer_class = CesantiaSerializer
    permission_classes = [IsAuthenticated]


class ReglasContratoViewSet(viewsets.ModelViewSet):
    queryset = ReglasContrato.objects.all()
    serializer_class = ReglasContratoSerializer
    permission_classes = [IsAuthenticated]


class DepartamentoViewSet(viewsets.ModelViewSet):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if Cargo.objects.filter(departamento=instance).exists():
            return Response(
                {
                    "detail": "No se puede eliminar este departamento porque tiene cargos asociados."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class TipoContratoViewSet(viewsets.ModelViewSet):
    queryset = TipoContrato.objects.all()
    serializer_class = TipoContratoSerializer
    permission_classes = [IsAuthenticated]


class GrupoHorarioViewSet(viewsets.ModelViewSet):
    queryset = GrupoHorario.objects.all()
    serializer_class = GrupoHorarioSerializer
    permission_classes = [IsAuthenticated]


class HorarioViewSet(viewsets.ModelViewSet):
    queryset = Horario.objects.all()
    serializer_class = HorarioSerializer
    permission_classes = [IsAuthenticated]


class HorarioEmpleadoViewSet(viewsets.ModelViewSet):
    queryset = HorarioEmpleado.objects.all()
    serializer_class = HorarioEmpleadoSerializer
    permission_classes = [IsAuthenticated]


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def actualizar_horarios_empleados(request):
    actualizaciones = request.data

    if not isinstance(actualizaciones, list):
        return Response(
            {"error": "Se espera una lista de objetos."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    errores = []
    actualizados = []

    for item in actualizaciones:
        try:
            instancia = HorarioEmpleado.objects.get(pk=item["id"])
            serializer = HorarioEmpleadoSerializer(instancia, data=item, partial=True)
            if serializer.is_valid():
                serializer.save()
                actualizados.append(serializer.data)
            else:
                errores.append({"id": item["id"], "errores": serializer.errors})
        except HorarioEmpleado.DoesNotExist:
            errores.append({"id": item["id"], "error": "No encontrado"})

    return Response(
        {"actualizados": actualizados, "errores": errores}, status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def crear_multiples_horarios_empleado(request):
    datos = request.data

    if not isinstance(datos, list):
        return Response(
            {"error": "Se espera una lista de asignaciones"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    errores = []
    creados = []

    for item in datos:
        serializer = HorarioEmpleadoSerializer(data=item)
        if serializer.is_valid():
            serializer.save()
            creados.append(serializer.data)
        else:
            errores.append({"data": item, "errores": serializer.errors})

    return Response(
        {"creados": creados, "errores": errores},
        status=status.HTTP_201_CREATED if creados else status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def eliminar_varios_horarios_empleado(request):
    empleados = request.data.get("empleados", [])

    if not isinstance(empleados, list) or not all(
        isinstance(id, int) for id in empleados
    ):
        return Response({"error": "Formato inválido"}, status=400)

    eliminados = HorarioEmpleado.objects.filter(empleado_id__in=empleados).delete()

    return Response({"mensaje": f"{eliminados[0]} asignaciones eliminadas"})


class HistorialCambioViewSet(viewsets.ReadOnlyModelViewSet):  # solo lectura
    queryset = HistorialCambio.objects.all().order_by("-fecha")
    serializer_class = HistorialCambioSerializer
    permission_classes = [IsAuthenticated]


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def desvincular_empleado(request):
    empleado_id = request.data.get("id")
    if not empleado_id:
        return Response({"error": "ID de empleado requerido."}, status=400)

    try:
        empleado = Empleado.objects.get(pk=empleado_id)
        empleado.estado = "inactivo"
        empleado.save()
        return Response({"mensaje": "Empleado desvinculado correctamente."}, status=200)
    except Empleado.DoesNotExist:
        return Response({"error": "Empleado no encontrado."}, status=404)


""" Reactivar empleado """


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cambiar_estado_empleado(request):
    empleado_id = request.data.get("id")
    if not empleado_id:
        return Response({"error": "ID de empleado requerido."}, status=400)

    try:
        empleado = Empleado.objects.get(pk=empleado_id)
        nuevo_estado = "inactivo" if empleado.estado == "activo" else "activo"
        empleado.estado = nuevo_estado
        empleado.save()
        return Response(
            {"mensaje": f"Empleado marcado como {nuevo_estado}."}, status=200
        )
    except Empleado.DoesNotExist:
        return Response({"error": "Empleado no encontrado."}, status=404)
