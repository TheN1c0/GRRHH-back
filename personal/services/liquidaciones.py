# services/liquidaciones.py
from datetime import date
from django.db.models import Sum
from personal.models import RegistroAsistencia, Liquidacion  # Ajusta "app" con el nombre real de tu app

def calcular_liquidacion(contrato, mes, año, ingresos_no_imponibles=0, descuentos_extra=[]):
    datos_prev = contrato.empleado.datosprevisionales
    sueldo_base = contrato.sueldo_base

    valor_dia = sueldo_base / 30
    valor_hora = valor_dia / 8

    asistencias = RegistroAsistencia.objects.filter(
        empleado=contrato.empleado,
        fecha__month=mes,
        fecha__year=año
    )

    dias_trabajados = asistencias.filter(presente=True).count()
    dias_inasistencia = 30 - dias_trabajados
    descuento_inasistencia = dias_inasistencia * valor_dia

    total_horas_extras = asistencias.aggregate(
        total=Sum('horas_extras')
    )['total'] or 0

    monto_horas_extras = total_horas_extras * valor_hora * 1.5

    sueldo_imponible = sueldo_base + monto_horas_extras - descuento_inasistencia
    sueldo_bruto = sueldo_imponible + ingresos_no_imponibles

    descuento_afp = sueldo_imponible * datos_prev.afp.porcentaje_cotizacion / 100
    descuento_salud = sueldo_imponible * datos_prev.salud.porcentaje_cotizacion / 100
    descuento_cesantia = sueldo_imponible * datos_prev.seguro_cesantia.porcentaje_trabajador / 100
    monto_otros_descuentos = sum(descuentos_extra)

    total_descuentos = (
        descuento_afp + descuento_salud + descuento_cesantia +
        descuento_inasistencia + monto_otros_descuentos
    )

    sueldo_liquido = sueldo_bruto - total_descuentos

    return Liquidacion.objects.create(
        contrato=contrato,
        fecha_pago=date(año, mes, 30),
        sueldo_bruto=sueldo_bruto,
        ingresos_no_imponibles=ingresos_no_imponibles,
        sueldo_imponible=sueldo_imponible,
        descuento_afp=descuento_afp,
        descuento_salud=descuento_salud,
        descuento_cesantia=descuento_cesantia,
        descuento_inasistencias=descuento_inasistencia,
        monto_horas_extras=monto_horas_extras,
        otros_descuentos=monto_otros_descuentos,
        total_descuentos=total_descuentos,
        sueldo_liquido=sueldo_liquido
    )
