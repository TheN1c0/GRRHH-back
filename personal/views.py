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
    PermisoAusencia,
    RegistroAsistencia,
    Salud,
    SeguroCesantia,
    TipoDescuento,
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
from django.utils.timezone import datetime
from django.db import models
from rest_framework.decorators import api_view, permission_classes
from .models import Empleado, Contrato, DatosPrevisionales, AFP, Salud, SeguroCesantia, Cargo, Empleador

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

class CargoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [IsAuthenticated]  # o AllowAny para que cualquiera pueda ver
    

class GenerarLiquidacionView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LiquidacionInputSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            contrato = Contrato.objects.get(id=data['contrato_id'])
            empleado = contrato.empleado
            previsionales = DatosPrevisionales.objects.get(empleado=empleado)

            # Calcular gratificación
            IMM = Decimal('500000')  # o traer desde ParametroSistema
            if data['gratificacion_tipo'] == 'legal':
                tope = (IMM * Decimal('4.75')) / 12
                gratificacion = min(contrato.sueldo_base * Decimal('0.25'), tope)
            else:
                gratificacion = contrato.sueldo_base / Decimal('12')
            empleador = empleado.empleador

            # Crear Liquidación con campos congelados
            liquidacion = Liquidacion.objects.create(
                contrato=contrato,
                periodo_inicio=data['periodo_inicio'],
                periodo_termino=data['periodo_termino'],
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

            for h in data['haberes']:
                Haber.objects.create(liquidacion=liquidacion, **h)
                total_haberes += h['monto']

            total_descuentos = Decimal("0")
            for d in data['descuentos']:
                tipo, _ = TipoDescuento.objects.get_or_create(nombre=d['tipo'])
                OtroDescuento.objects.create(
                    liquidacion=liquidacion,
                    tipo=tipo,
                    monto=d['monto'],
                    descripcion=d.get('descripcion', '')
                )
                total_descuentos += d['monto']

            # Puedes incluir descuentos legales acá también

            sueldo_liquido = total_haberes - total_descuentos
            liquidacion.total_haberes = total_haberes
            liquidacion.total_descuentos = total_descuentos
            liquidacion.sueldo_liquido = sueldo_liquido
            liquidacion.save()

            pdf_data = generar_pdf_liquidacion(liquidacion)
            if pdf_data:
                response = HttpResponse(pdf_data, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="liquidacion_{liquidacion.id}.pdf"'
                return response
            else:
                return Response({'error': 'Error al generar el PDF'}, status=500)

        
        
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def generar_pdf_liquidacion(liquidacion):
    template_path = 'pdf/liquidacion.html'
    context = {'liquidacion': liquidacion}
    html = render_to_string(template_path, context)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('utf-8')), result)

    if not pdf.err:
        return result.getvalue()
    return None

class ListaContratosView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        contratos = Contrato.objects.select_related('empleado', 'empleado__cargo').all()
        serializer = ContratoEmpleadoSerializer(contratos, many=True)
        return Response(serializer.data)
    





class ReporteMensualView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mes = int(request.GET.get('mes'))
        anio = int(request.GET.get('anio'))

        # Filtrar liquidaciones del mes
        liquidaciones = Liquidacion.objects.filter(
            periodo_inicio__month=mes,
            periodo_inicio__year=anio
        )

        empleados_pagados = liquidaciones.values('contrato__empleado').distinct().count()
        sueldo_bruto_total = sum(l.sueldo_bruto or 0 for l in liquidaciones)
        total_descuentos = sum(l.total_descuentos or 0 for l in liquidaciones)
        sueldo_liquido_total = sum(l.sueldo_liquido or 0 for l in liquidaciones)

        # Contratos activos durante el mes
        contratos = Contrato.objects.filter(
            fecha_inicio__lte=datetime(anio, mes, 28),
        ).filter(
            models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gte=datetime(anio, mes, 1))
        )
        total_empleados_contrato = contratos.count()
        porcentaje_pagado = (empleados_pagados / total_empleados_contrato) * 100 if total_empleados_contrato > 0 else 0

        # Ausentismo laboral
        dias_mes = 30  # para simplificar, luego se puede usar calendar.monthrange
        total_posibles = total_empleados_contrato * dias_mes
        asistencias = RegistroAsistencia.objects.filter(fecha__month=mes, fecha__year=anio)
        asistencias_presentes = asistencias.filter(presente=True).count()

        permisos = PermisoAusencia.objects.filter(
            fecha_inicio__lte=datetime(anio, mes, 28),
            fecha_fin__gte=datetime(anio, mes, 1),
            aprobado=True
        )

        dias_permiso = 0
        for permiso in permisos:
            inicio = max(permiso.fecha_inicio, datetime(anio, mes, 1).date())
            fin = min(permiso.fecha_fin, datetime(anio, mes, 28).date())
            dias_permiso += (fin - inicio).days + 1

        dias_ausentes = total_posibles - asistencias_presentes - dias_permiso
        ausentismo_laboral = (dias_ausentes / total_posibles) * 100 if total_posibles > 0 else 0

        return Response({
            "mes": mes,
            "anio": anio,
            "empleados_pagados": empleados_pagados,
            "sueldo_bruto_total": sueldo_bruto_total,
            "total_descuentos": total_descuentos,
            "sueldo_liquido_total": sueldo_liquido_total,
            "porcentaje_pagado": round(porcentaje_pagado, 2),
            "ausentismo_laboral": round(ausentismo_laboral, 2)
        })
        
   
class PostulanteViewSet(viewsets.ModelViewSet):
   
    queryset = Postulante.objects.all().order_by('-fecha_postulacion')
    serializer_class = PostulanteSerializer

    def perform_create(self, serializer):
        postulante = serializer.save()
        postulante.procesar_curriculum()     


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def contratar_postulante(request):
    data = request.data

    try:
        # 1. Crear Empleado
        emp_data = data['empleado']
        cargo = Cargo.objects.get(pk=emp_data['cargo'])
        empleador = Empleador.objects.get(pk=emp_data['empleador'])

        empleado = Empleado.objects.create(
            rut=emp_data['rut'],
            primer_nombre=emp_data['primer_nombre'],
            otros_nombres=emp_data.get('otros_nombres', ''),
            apellido_paterno=emp_data['apellido_paterno'],
            apellido_materno=emp_data['apellido_materno'],
            direccion=emp_data['direccion'],
            telefono=emp_data['telefono'],
            cargo=cargo,
            empleador=empleador,
            creado_por=request.user
        )

        # 2. Crear Contrato
        contrato_data = data['contrato']
        Contrato.objects.create(
            empleado=empleado,
            tipo_contrato=contrato_data['tipo_contrato'],
            fecha_inicio=contrato_data['fecha_inicio'],
            fecha_fin=contrato_data.get('fecha_fin'),
            sueldo_base=contrato_data['sueldo_base']
        )

        # 3. Crear Datos Previsionales
        previsionales = data['prevision']
        DatosPrevisionales.objects.create(
            empleado=empleado,
            afp=AFP.objects.get(pk=previsionales['afp']),
            salud=Salud.objects.get(pk=previsionales['salud']),
            seguro_cesantia=SeguroCesantia.objects.get(pk=previsionales['seguro_cesantia']),
        )

        return Response({'mensaje': 'Empleado contratado con éxito'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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