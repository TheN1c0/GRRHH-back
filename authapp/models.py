from django.db import models

# Create your models here.
class TestModel(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
# models.py

from django.db import models
from django.contrib.auth.models import User

class Departamento(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Cargo(models.Model):
    nombre = models.CharField(max_length=100)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} ({self.departamento.nombre})"

class Empleado(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    rut = models.CharField(max_length=12, unique=True)
    fecha_nacimiento = models.DateField()
    direccion = models.TextField()
    telefono = models.CharField(max_length=20)
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.cargo.nombre}"

class Contrato(models.Model):
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Contrato de {self.empleado.usuario.get_full_name()}"

class Liquidacion(models.Model):
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE)
    fecha_pago = models.DateField()
    sueldo_bruto = models.DecimalField(max_digits=12, decimal_places=2)
    descuentos = models.DecimalField(max_digits=12, decimal_places=2)
    sueldo_liquido = models.DecimalField(max_digits=12, decimal_places=2)
    documento = models.FileField(upload_to='liquidaciones/')

    def __str__(self):
        return f"Liquidación {self.fecha_pago} - {self.contrato.empleado.usuario.username}"

class RegistroAsistencia(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha = models.DateField()
    presente = models.BooleanField(default=True)
    horas_trabajadas = models.DecimalField(max_digits=4, decimal_places=2, default=8)  # Normalmente 8 horas
    horas_extras = models.DecimalField(max_digits=4, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.empleado.usuario.username} - {self.fecha}"


class PermisoAusencia(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    motivo = models.CharField(max_length=255)
    aprobado = models.BooleanField(default=False)

# models.py (añadiendo a lo anterior)

class AFP(models.Model):
    nombre = models.CharField(max_length=100)
    porcentaje_cotizacion = models.DecimalField(max_digits=5, decimal_places=2)  # ejemplo: 10.00 (%)

    def __str__(self):
        return self.nombre

class Salud(models.Model):
    TIPO_CHOICES = (
        ('FONASA', 'Fonasa'),
        ('ISAPRE', 'Isapre'),
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    nombre = models.CharField(max_length=100, null=True, blank=True)  # Solo para Isapre
    porcentaje_cotizacion = models.DecimalField(max_digits=5, decimal_places=2, default=7.00)

    def __str__(self):
        if self.tipo == 'FONASA':
            return 'Fonasa'
        return f"Isapre: {self.nombre}"

class SeguroCesantia(models.Model):
    porcentaje_trabajador = models.DecimalField(max_digits=5, decimal_places=2, default=0.60)
    porcentaje_empleador = models.DecimalField(max_digits=5, decimal_places=2, default=2.40)

    def __str__(self):
        return "Seguro de Cesantía (AFC)"

class DatosPrevisionales(models.Model):
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE)
    afp = models.ForeignKey(AFP, on_delete=models.SET_NULL, null=True)
    salud = models.ForeignKey(Salud, on_delete=models.SET_NULL, null=True)
    seguro_cesantia = models.ForeignKey(SeguroCesantia, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Previsión de {self.empleado.usuario.get_full_name()}"

class TipoDescuento(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class OtroDescuento(models.Model):
    liquidacion = models.ForeignKey(Liquidacion, on_delete=models.CASCADE, related_name='otros_descuentos')
    tipo = models.ForeignKey(TipoDescuento, on_delete=models.SET_NULL, null=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.tipo.nombre}: {self.monto} - {self.liquidacion}"

from django.db import models
from datetime import date
from django.db.models import Sum

class Liquidacion(models.Model):
    contrato = models.ForeignKey('Contrato', on_delete=models.CASCADE)
    fecha_pago = models.DateField()
    
    sueldo_bruto = models.DecimalField(max_digits=12, decimal_places=2)
    sueldo_imponible = models.DecimalField(max_digits=12, decimal_places=2)
    ingresos_no_imponibles = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    descuento_afp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento_salud = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento_cesantia = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento_inasistencias = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monto_horas_extras = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    otros_descuentos = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    total_descuentos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sueldo_liquido = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    documento = models.FileField(upload_to='liquidaciones/', null=True, blank=True)

    def __str__(self):
        return f"Liquidación {self.fecha_pago} - {self.contrato.empleado.usuario.username}"

    @classmethod
    def calcular_y_crear(cls, contrato, mes, año, ingresos_no_imponibles=0, descuentos_extra=[]):
        from .models import RegistroAsistencia  # Import interno para evitar errores de dependencia circular

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

        # Se crea y retorna la liquidación
        return cls.objects.create(
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
