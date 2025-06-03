from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from .models import HorarioEmpleado, Asistencia
from django.db.models import Q


def evaluar_asistencia(empleado, fecha, entrada_real, salida_real):
    # Buscar horario asignado vigente
    horario_empleado = (
        HorarioEmpleado.objects.filter(empleado=empleado, fecha_inicio__lte=fecha)
        .filter(Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha))
        .first()
    )

    if not horario_empleado:
        estado = "fuera de horario"
        minutos_atraso = 0
        minutos_salida_anticipada = 0
        horas_trabajadas = calcular_horas(entrada_real, salida_real)
    else:
        # Obtener el horario del grupo para el día
        dia_semana = fecha.strftime("%A")  # Ej: "Monday"
        horario = horario_empleado.grupo_horario.horarios.filter(
            dia_semana=dia_semana
        ).first()

        if not horario:
            estado = "fuera de horario"
            minutos_atraso = 0
            minutos_salida_anticipada = 0
            horas_trabajadas = calcular_horas(entrada_real, salida_real)
        else:
            # Comparar horas
            atraso = diferencia_minutos(entrada_real, horario.hora_entrada)
            salida_anticipada = diferencia_minutos(horario.hora_salida, salida_real)
            horas_trabajadas = calcular_horas(entrada_real, salida_real)

            minutos_atraso = max(atraso, 0)
            minutos_salida_anticipada = max(salida_anticipada, 0)

            # Determinar estado
            if minutos_atraso > 0 and minutos_salida_anticipada > 0:
                estado = "atraso y salida anticipada"
            elif minutos_atraso > 0:
                estado = "atraso"
            elif minutos_salida_anticipada > 0:
                estado = "salida anticipada"
            else:
                estado = "presente completo"

    # Crear o actualizar asistencia
    asistencia, _ = Asistencia.objects.update_or_create(
        empleado=empleado,
        fecha=fecha,
        defaults={
            "hora_entrada_real": entrada_real,
            "hora_salida_real": salida_real,
            "minutos_atraso": minutos_atraso,
            "minutos_salida_anticipada": minutos_salida_anticipada,
            "horas_trabajadas": horas_trabajadas,
            "estado": estado,
        },
    )
    return asistencia


# Función auxiliar para calcular diferencia en minutos
def diferencia_minutos(t1, t2):
    dt1 = datetime.combine(datetime.today(), t1)
    dt2 = datetime.combine(datetime.today(), t2)
    return int((dt1 - dt2).total_seconds() // 60)


# Función auxiliar para calcular horas trabajadas
def calcular_horas(t1, t2):
    dt1 = datetime.combine(datetime.today(), t1)
    dt2 = datetime.combine(datetime.today(), t2)
    return round((dt2 - dt1).total_seconds() / 3600, 2)
