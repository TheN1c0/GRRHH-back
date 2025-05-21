from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from PyPDF2 import PdfReader
from nltk.tokenize import word_tokenize
import re

# Create your models here.

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
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    primer_nombre = models.CharField(max_length=50, null=True, blank=True)
    otros_nombres = models.CharField(max_length=100, blank=True, null=True)  # opcional
    apellido_paterno = models.CharField(max_length=50, null=True, blank=True)
    apellido_materno = models.CharField(max_length=50, null=True, blank=True)
    rut = models.CharField(max_length=12, unique=True)
    fecha_nacimiento = models.DateField()
    direccion = models.TextField()
    telefono = models.CharField(max_length=20)
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True)
    empleador = models.ForeignKey('Empleador', on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return f"{self.rut} - {self.cargo.nombre if self.cargo else 'Sin cargo'}"

class Contrato(models.Model):
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE)
    tipo_contrato = models.CharField(max_length=50, null=True, blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        nombre = self.empleado.usuario.get_full_name() if self.empleado and self.empleado.usuario else f"{self.empleado.rut}"
        return f"Contrato de {nombre}"
from django.db import models

class Liquidacion(models.Model):
    contrato = models.ForeignKey('Contrato', on_delete=models.CASCADE)

    # Campos congelados del empleado (para historial)
    rut_empleado = models.CharField(max_length=12, null=True, blank=True)
    nombre_empleado = models.CharField(max_length=200, null=True, blank=True)
    cargo_empleado = models.CharField(max_length=100, default="Sin cargo")
    tipo_contrato = models.CharField(max_length=50, null=True, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)

    # Datos previsionales congelados
    nombre_afp = models.CharField(max_length=100,null=True)
    porcentaje_afp = models.DecimalField(max_digits=5, decimal_places=2,null=True)
    comision_afp = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    nombre_salud = models.CharField(max_length=100,null=True)
    tipo_salud = models.CharField(max_length=10,null=True)
    porcentaje_salud = models.DecimalField(max_digits=5, decimal_places=2,null=True)

    nombre_seguro_cesantia = models.CharField(max_length=100,null=True)
    porcentaje_cesantia_trabajador = models.DecimalField(max_digits=5, decimal_places=2,null=True)
    porcentaje_cesantia_empleador = models.DecimalField(max_digits=5, decimal_places=2,null=True)

    # Datos congelados del empleador
    razon_social_empleador = models.CharField(max_length=255,null=True)
    rut_empleador = models.CharField(max_length=12,null=True)
    direccion_empleador = models.CharField(max_length=255,null=True)

    # Periodo trabajado
    periodo_inicio = models.DateField(null=True, blank=True)
    periodo_termino = models.DateField( null=True, blank=True)

    # Totales
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=2,null=True)
    sueldo_bruto = models.DecimalField(max_digits=12, decimal_places=2,null=True)
    gratificacion = models.DecimalField(max_digits=12, decimal_places=2,null=True)
    total_haberes = models.DecimalField(max_digits=12, decimal_places=2,null=True)
    total_descuentos = models.DecimalField(max_digits=12, decimal_places=2,null=True)
    sueldo_liquido = models.DecimalField(max_digits=12, decimal_places=2,null=True)

    documento = models.FileField(upload_to='liquidaciones/', blank=True, null=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_en = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Liquidación  {self.contrato.empleado.rut}"


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
    nombre = models.CharField(max_length=100, unique=True)
    porcentaje_trabajador = models.DecimalField(max_digits=5, decimal_places=2, default=0.60)
    porcentaje_empleador = models.DecimalField(max_digits=5, decimal_places=2, default=2.40)

    def __str__(self):
        return self.nombre

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
    liquidacion = models.ForeignKey(Liquidacion, on_delete=models.CASCADE, related_name='detalles_descuento')
    tipo = models.ForeignKey(TipoDescuento, on_delete=models.SET_NULL, null=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.tipo.nombre}: {self.monto} - {self.liquidacion}"

class Empleador(models.Model):
    nombre = models.CharField(max_length=255)
    rut = models.CharField(max_length=12)
    direccion = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre} ({self.rut})"

class ParametroSistema(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    valor_decimal = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_vigencia = models.DateField()

    def __str__(self):
        return f"{self.nombre}: {self.valor_decimal} desde {self.fecha_vigencia}"

class Haber(models.Model):
    TIPO_CHOICES = [
        ('imponible', 'Imponible'),
        ('no_imponible', 'No Imponible'),
    ]

    liquidacion = models.ForeignKey('Liquidacion', on_delete=models.CASCADE, related_name='haberes')
    nombre = models.CharField(max_length=100)  # Ej: "Bono Producción"
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nombre} ({self.tipo}) - ${self.monto}"




class Etiqueta(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre
class PalabraClave(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    categoria = models.CharField(max_length=50, choices=[
        ('habilidad', 'Habilidad'),
        ('certificacion', 'Certificación'),
        ('area', 'Área'),
    ])

    def __str__(self):
        return f"{self.nombre} ({self.categoria})"

class Postulante(models.Model):
    ESTADOS = [
        ('postulado', 'Postulado'),
        ('entrevista', 'Entrevista'),
        ('evaluacion', 'Evaluación'),
        ('seleccionado', 'Seleccionado'),
        ('descartado', 'Descartado'),
    ]

    primer_nombre = models.CharField(max_length=50)
    otros_nombres = models.CharField(max_length=100, blank=True, null=True)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50)
    direccion = models.TextField(blank=True, null=True)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)
    cargo_postulado = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True)
    curriculum = models.FileField(upload_to='postulantes/cv/', null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='postulado')
    fecha_postulacion = models.DateTimeField(default=timezone.now)
    etiquetas = models.ManyToManyField(Etiqueta, blank=True)

    def __str__(self):
        return f"{self.primer_nombre} {self.apellido_paterno} - {self.cargo_postulado}"

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
def procesar_curriculum(self):
    if not self.curriculum:
        return

    etiquetas_detectadas = set()
    palabras_no_reconocidas = set()

    try:
        pdf = PdfReader(self.curriculum)
        texto = ""
        for page in pdf.pages:
            texto += page.extract_text().lower()

        palabras_clave = PalabraClave.objects.values_list('nombre', flat=True)
        palabras_cv = set(re.findall(r'\b\w+\b', texto))

        for palabra in palabras_cv:
            if palabra in palabras_clave:
                etiquetas_detectadas.add(palabra)
            elif len(palabra) > 3:
                palabras_no_reconocidas.add(palabra)

        for palabra in etiquetas_detectadas:
            etiqueta_obj, _ = Etiqueta.objects.get_or_create(nombre=palabra)
            self.etiquetas.add(etiqueta_obj)

        # Aquí puedes registrar o guardar las palabras no reconocidas para revisión manual
        for palabra in sorted(palabras_no_reconocidas):
            obj, created = PalabraDesconocida.objects.get_or_create(palabra=palabra)
            if not created:
                obj.veces_detectada += 1
                obj.save()

    except Exception as e:
        print(f"Error procesando CV: {e}")

class PalabraDesconocida(models.Model):
    palabra = models.CharField(max_length=100, unique=True)
    fecha_detectada = models.DateTimeField(auto_now_add=True)
    veces_detectada = models.PositiveIntegerField(default=1)
    revisada = models.BooleanField(default=False)

    def __str__(self):
        return self.palabra

