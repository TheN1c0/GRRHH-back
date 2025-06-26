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
    PalabraClave
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
from rest_framework.decorators import api_view, permission_classes, action

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

from analisiscv.services.analisis_ia import generar_etiquetas_para_cargo

from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from .pagination import EmpleadoPagination
from authapp.permissions import PuedeCrear, PuedeEditar, PuedeEliminar


class EmpleadoViewSet(HistorialMixin, viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]

    search_fields = ["rut", "primer_nombre", "apellido_paterno", "apellido_materno"]

    filterset_fields = ["cargo", "empleador", "cargo__departamento", "estado"]
    pagination_class = EmpleadoPagination
    def get_permissions(self):
        if self.action == 'create':
            return [PuedeCrear()]
        elif self.action in ['update', 'partial_update']:
            return [PuedeEditar()]
        elif self.action == 'destroy':
            return [PuedeEliminar()]
        return [IsAuthenticated()]

class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [IsAuthenticated]
    def perform_create(self, serializer):
        generar = self.request.data.get("generar_etiquetas_ia") in ["true", "True", True, "1", 1]
        cargo = serializer.save()
        if generar:
            cargo.inicializar_etiquetas_con_ia()
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

            # Calcular gratificación (IMM puede obtenerse de ParametroSistema si está disponible)
            try:
                param_imm = ParametroSistema.objects.filter(nombre__iexact="IMM").order_by("-fecha_vigencia").first()
                IMM = param_imm.valor_decimal if param_imm else Decimal("500000")
            except Exception:
                IMM = Decimal("500000")
            if data["gratificacion_tipo"] == "legal":
                tope = (IMM * Decimal("4.75")) / Decimal("12")
                gratificacion = min(contrato.sueldo_base * Decimal("0.25"), tope)
            else:
                gratificacion = contrato.sueldo_base / Decimal("12")
            
            empleador = empleado.empleador
            if empleador:
                razon_social_empleador = empleador.nombre
                rut_empleador = empleador.rut
                direccion_empleador = empleador.direccion
            else:
                razon_social_empleador = "No Aplica"
                rut_empleador = "No Aplica"
                direccion_empleador = "No Aplica"

            # Preparar datos previsionales congelados (usar "No Aplica" si no hay datos)
            if previsionales.afp:
                nombre_afp = previsionales.afp.nombre
                porcentaje_afp = previsionales.afp.porcentaje_cotizacion
                comision_afp = Decimal("1.44")  # Comisión fija de ejemplo; idealmente obtener de AFP o ParametroSistema
            else:
                nombre_afp = "No Aplica"
                porcentaje_afp = None
                comision_afp = Decimal("0.00")
            if previsionales.salud:
                nombre_salud = previsionales.salud.nombre or previsionales.salud.tipo
                tipo_salud = previsionales.salud.tipo
                porcentaje_salud = previsionales.salud.porcentaje_cotizacion
            else:
                nombre_salud = "No Aplica"
                tipo_salud = None
                porcentaje_salud = None
            if previsionales.seguro_cesantia:
                nombre_seguro = previsionales.seguro_cesantia.nombre
                porc_cesantia_trabajador = previsionales.seguro_cesantia.porcentaje_trabajador
                porc_cesantia_empleador = previsionales.seguro_cesantia.porcentaje_empleador
            else:
                nombre_seguro = "No Aplica"
                porc_cesantia_trabajador = None
                porc_cesantia_empleador = None

            # Crear Liquidación con campos congelados
            liquidacion = Liquidacion.objects.create(
                contrato=contrato,
                periodo_inicio=data["periodo_inicio"],
                periodo_termino=data["periodo_termino"],
                sueldo_base=contrato.sueldo_base,
                gratificacion=gratificacion,
                sueldo_bruto=contrato.sueldo_base + gratificacion,  # se actualizará más abajo si hay haberes imponibles
                rut_empleado=empleado.rut,
                nombre_empleado=f"{empleado.primer_nombre} {empleado.otros_nombres or ''} {empleado.apellido_paterno} {empleado.apellido_materno}".strip(),
                cargo_empleado=empleado.cargo.nombre if empleado.cargo else "Sin cargo",
                tipo_contrato=str(contrato.tipo_contrato),  # Convertir a string si es ForeignKey/objeto
                fecha_ingreso=contrato.fecha_inicio,
                nombre_afp=nombre_afp,
                porcentaje_afp=porcentaje_afp,
                comision_afp=comision_afp,
                nombre_salud=nombre_salud,
                tipo_salud=tipo_salud,
                porcentaje_salud=porcentaje_salud,
                nombre_seguro_cesantia=nombre_seguro,
                porcentaje_cesantia_trabajador=porc_cesantia_trabajador,
                porcentaje_cesantia_empleador=porc_cesantia_empleador,
                razon_social_empleador=razon_social_empleador,
                rut_empleador=rut_empleador,
                direccion_empleador=direccion_empleador,
            )

            # Calcular totales de haberes e imponibles
            total_haberes = contrato.sueldo_base + gratificacion
            sueldo_imponible = contrato.sueldo_base + gratificacion
            for h in data["haberes"]:
                Haber.objects.create(liquidacion=liquidacion, **h)
                total_haberes += h["monto"]
                if h["tipo"] == "imponible":
                    sueldo_imponible += h["monto"]

            # Calcular y registrar descuentos proporcionados en la solicitud
            total_descuentos = Decimal("0")
            for d in data["descuentos"]:
                tipo_desc, _ = TipoDescuento.objects.get_or_create(nombre=d["tipo"])
                OtroDescuento.objects.create(
                    liquidacion=liquidacion,
                    tipo=tipo_desc,
                    monto=d["monto"],
                    descripcion=d.get("descripcion", "")
                )
                total_descuentos += d["monto"]

            # Incluir descuentos legales (AFP, Salud, Seguro de Cesantía) si corresponden
            # Descuento AFP (incluye comisión) 
            if previsionales.afp:
                afp_percent = previsionales.afp.porcentaje_cotizacion or Decimal("0")
                afp_commission = comision_afp  # ya definido arriba
                total_afp_percent = afp_percent + afp_commission
                descuento_afp = (sueldo_imponible * total_afp_percent) / Decimal("100")
                descuento_afp = descuento_afp.quantize(Decimal("0.01"))  # Redondear a 2 decimales
                if descuento_afp > 0:
                    tipo_desc, _ = TipoDescuento.objects.get_or_create(nombre="Cotización AFP")
                    OtroDescuento.objects.create(
                        liquidacion=liquidacion,
                        tipo=tipo_desc,
                        monto=descuento_afp,
                        descripcion=f"{nombre_afp} ({afp_percent}% + {afp_commission}% comisión)"
                    )
                    total_descuentos += descuento_afp

            # Descuento Salud (Fonasa/Isapre)
            if previsionales.salud:
                salud_percent = previsionales.salud.porcentaje_cotizacion or Decimal("0")
                descuento_salud = (sueldo_imponible * salud_percent) / Decimal("100")
                descuento_salud = descuento_salud.quantize(Decimal("0.01"))
                if descuento_salud > 0:
                    tipo_desc, _ = TipoDescuento.objects.get_or_create(nombre="Cotización Salud")
                    OtroDescuento.objects.create(
                        liquidacion=liquidacion,
                        tipo=tipo_desc,
                        monto=descuento_salud,
                        descripcion=f"{nombre_salud} ({salud_percent}%)"
                    )
                    total_descuentos += descuento_salud

            # Descuento Seguro de Cesantía (solo trabajador, el empleador no afecta sueldo líquido)
            if previsionales.seguro_cesantia:
                sc_percent = previsionales.seguro_cesantia.porcentaje_trabajador or Decimal("0")
                descuento_cesantia = (sueldo_imponible * sc_percent) / Decimal("100")
                descuento_cesantia = descuento_cesantia.quantize(Decimal("0.01"))
                if descuento_cesantia > 0:
                    tipo_desc, _ = TipoDescuento.objects.get_or_create(nombre="Seguro Cesantía")
                    OtroDescuento.objects.create(
                        liquidacion=liquidacion,
                        tipo=tipo_desc,
                        monto=descuento_cesantia,
                        descripcion=f"{nombre_seguro} ({sc_percent}%)"
                    )
                    total_descuentos += descuento_cesantia

            # Actualizar campos totales en Liquidacion
            sueldo_liquido = total_haberes - total_descuentos
            liquidacion.sueldo_bruto = sueldo_imponible  # sueldo imponible total (sueldo bruto actualizado)
            liquidacion.total_haberes = total_haberes
            liquidacion.total_descuentos = total_descuentos
            liquidacion.sueldo_liquido = sueldo_liquido
            liquidacion.save()

            # Generar PDF de la liquidación
            pdf_data = generar_pdf_liquidacion(
                    liquidacion,
                    contexto_extra={
                        "informe_imm": IMM,
                        "tipo_gratificacion": data["gratificacion_tipo"],
                        "gratificacion_25pct": contrato.sueldo_base * Decimal("0.25"),
                        "gratificacion_tope": tope
                    }
                )
            
            if pdf_data:
                response = HttpResponse(pdf_data, content_type="application/pdf")
                response["Content-Disposition"] = f'attachment; filename="liquidacion_{liquidacion.id}.pdf"'
                return response
            else:
                return Response({"error": "Error al generar el PDF"}, status=500)
        # Si el serializer no es válido, retornar errores de validación
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def generar_pdf_liquidacion(liquidacion, contexto_extra=None):
    template_path = "pdf/liquidacion.html"
    haberes_qs = liquidacion.haberes.all()
    descuentos_qs = liquidacion.detalles_descuento.all()

    context = {
        "liquidacion": liquidacion,
        "haberes_imponibles": haberes_qs.filter(tipo="imponible"),
        "haberes_no_imponibles": haberes_qs.filter(tipo="no_imponible"),
        "descuentos": descuentos_qs,
        "descuentos_legales": descuentos_qs.filter(tipo__nombre__in=[
            "Cotización AFP", "Cotización Salud", "Seguro Cesantía"
        ]),
    }

    if contexto_extra:
        context.update(contexto_extra)

    html = render_to_string(template_path, context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    return result.getvalue() if not pdf.err else None

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
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def empleados_sin_contrato(request):
    empleados_contrato = Contrato.objects.values_list('empleado_id', flat=True)
    empleados = Empleado.objects.exclude(id__in=empleados_contrato)
    serializer = EmpleadoSerializer(empleados, many=True)
    return Response(serializer.data)
class ContratoViewSet(viewsets.ModelViewSet):
    queryset = Contrato.objects.all()
    serializer_class = ContratoSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='lista-empleados', permission_classes=[AllowAny])
    def lista_empleados(self, request):
        contratos = Contrato.objects.select_related("empleado", "empleado__cargo").all()
        serializer = ContratoEmpleadoSerializer(contratos, many=True)
        return Response(serializer.data)
    
class PalabraClaveViewSet(viewsets.ModelViewSet):
    queryset = PalabraClave.objects.all()
    serializer_class = PalabraClaveSerializer
    permission_classes = [IsAuthenticated]

class DatosPrevisionalesViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = DatosPrevisionalesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'mensaje': 'Datos previsionales creados'}, status=201)
        return Response(serializer.errors, status=400)

    def update(self, request, pk=None):
        try:
            datos = DatosPrevisionales.objects.get(empleado_id=pk)
        except DatosPrevisionales.DoesNotExist:
            return Response({'error': 'No existen datos previsionales para ese empleado'}, status=404)

        serializer = DatosPrevisionalesSerializer(datos, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'mensaje': 'Datos previsionales actualizados'})
        return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_permisos_usuario_actual(request):
    user = request.user
    permisos = getattr(user, 'permisos_rrhh', None)

    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_superuser": user.is_superuser,
        "permisos": {
            "puede_crear": getattr(permisos, 'puede_crear', False),
            "puede_editar": getattr(permisos, 'puede_editar', False),
            "puede_eliminar": getattr(permisos, 'puede_eliminar', False),
        }
    })