from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Empleado, Cargo, Contrato, DatosPrevisionales, Liquidacion, Haber, OtroDescuento, Empleador, TipoDescuento
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import render_to_string
from django.http import HttpResponse
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