from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from PyPDF2 import PdfReader
import nltk
from nltk.tokenize import word_tokenize
import re

from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from analisiscv.services.analisis_ia import analizar_curriculum_con_ia, generar_etiquetas_para_cargo


class HistorialCambio(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    accion = models.CharField(
        max_length=100
    )  # 'Crear empleado', 'Eliminar contrato', etc.
    detalle = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.usuario} - {self.accion} ({self.fecha.strftime('%Y-%m-%d %H:%M')})"
        )


class Departamento(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Cargo(models.Model):
    nombre = models.CharField(max_length=100)
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    superior = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL
    )
    palabras_clave = models.ManyToManyField('PalabraClave', blank=True)
    def __str__(self):
        if self.superior:
            return f"{self.nombre} ({self.departamento.nombre}) → Jefe: {self.superior.nombre}"
        return f"{self.nombre} ({self.departamento.nombre})"

    def clean(self):
        # ❌ No puede ser su propio superior
        if self.superior and self.superior == self:
            raise ValidationError("Un cargo no puede ser su propio superior.")

        # ❌ Validar jerarquía circular
        superior = self.superior
        while superior:
            if superior == self:
                raise ValidationError(
                    "Asignación inválida: se genera un ciclo jerárquico."
                )
            superior = superior.superior

    def save(self, *args, **kwargs):
        self.full_clean()  # Ejecuta las validaciones de clean()
        super().save(*args, **kwargs)
    def inicializar_etiquetas_con_ia(self):
        try:
            resultado = generar_etiquetas_para_cargo(self.nombre)

            for nombre in resultado.get("habilidades", []):
                if nombre:
                    palabra, _ = PalabraClave.objects.get_or_create(
                        nombre=nombre.strip().lower(),
                        defaults={"categoria": "habilidad"}
                    )
                    self.palabras_clave.add(palabra)

            for nombre in resultado.get("certificaciones", []):
                if nombre:
                    palabra, _ = PalabraClave.objects.get_or_create(
                        nombre=nombre.strip().lower(),
                        defaults={"categoria": "certificacion"}
                    )
                    self.palabras_clave.add(palabra)

            for nombre in resultado.get("areas", []):
                if nombre:
                    palabra, _ = PalabraClave.objects.get_or_create(
                        nombre=nombre.strip().lower(),
                        defaults={"categoria": "area"}
                    )
                    self.palabras_clave.add(palabra)

            self.save()

        except Exception as e:
            print(f"Error al generar etiquetas para cargo {self.nombre}: {e}")




class Empleado(models.Model):
    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True
    )
    primer_nombre = models.CharField(max_length=50, null=True, blank=True)
    otros_nombres = models.CharField(max_length=100, blank=True, null=True)  # opcional
    apellido_paterno = models.CharField(max_length=50, null=True, blank=True)
    apellido_materno = models.CharField(max_length=50, null=True, blank=True)
    rut = models.CharField(max_length=12, unique=True)
    fecha_nacimiento = models.DateField()
    direccion = models.TextField()
    telefono = models.CharField(max_length=20)
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True)
    empleador = models.ForeignKey("Empleador", on_delete=models.SET_NULL, null=True)
    ESTADOS = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
    ]
    estado = models.CharField(max_length=10, choices=ESTADOS, default="activo")
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="empleados_creados",
    )

    def __str__(self):
        return f"{self.rut} - {self.cargo.nombre if self.cargo else 'Sin cargo'}"


class ReglasContrato(models.Model):
    nombre = models.CharField(max_length=100)
    requiere_cotizaciones = models.BooleanField(default=True)
    controla_asistencia = models.BooleanField(default=True)
    requiere_liquidacion = models.BooleanField(default=True)
    genera_vacaciones = models.BooleanField(default=True)
    afecta_antiguedad = models.BooleanField(default=True)
    requiere_firma_digital = models.BooleanField(default=False)
    aplica_seguro_invalidez = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class TipoContrato(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    reglas = models.OneToOneField(
        ReglasContrato, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.nombre


class Contrato(models.Model):
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE)
    tipo_contrato = models.ForeignKey(
        "TipoContrato", on_delete=models.SET_NULL, null=True, blank=True
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        nombre = (
            self.empleado.usuario.get_full_name()
            if self.empleado and self.empleado.usuario
            else f"{self.empleado.rut}"
        )
        return f"Contrato de {nombre}"


from django.db import models


class Liquidacion(models.Model):
    contrato = models.ForeignKey("Contrato", on_delete=models.CASCADE)

    # Campos congelados del empleado (para historial)
    rut_empleado = models.CharField(max_length=12, null=True, blank=True)
    nombre_empleado = models.CharField(max_length=200, null=True, blank=True)
    cargo_empleado = models.CharField(max_length=100, default="Sin cargo")
    tipo_contrato = models.CharField(max_length=50, null=True, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)

    # Datos previsionales congelados
    nombre_afp = models.CharField(max_length=100, null=True)
    porcentaje_afp = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    comision_afp = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    nombre_salud = models.CharField(max_length=100, null=True)
    tipo_salud = models.CharField(max_length=10, null=True)
    porcentaje_salud = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    nombre_seguro_cesantia = models.CharField(max_length=100, null=True)
    porcentaje_cesantia_trabajador = models.DecimalField(
        max_digits=5, decimal_places=2, null=True
    )
    porcentaje_cesantia_empleador = models.DecimalField(
        max_digits=5, decimal_places=2, null=True
    )

    # Datos congelados del empleador
    razon_social_empleador = models.CharField(max_length=255, null=True)
    rut_empleador = models.CharField(max_length=12, null=True)
    direccion_empleador = models.CharField(max_length=255, null=True)

    # Periodo trabajado
    periodo_inicio = models.DateField(null=True, blank=True)
    periodo_termino = models.DateField(null=True, blank=True)

    # Totales
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    sueldo_bruto = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    gratificacion = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    total_haberes = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    total_descuentos = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    sueldo_liquido = models.DecimalField(max_digits=12, decimal_places=2, null=True)

    documento = models.FileField(upload_to="liquidaciones/", blank=True, null=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_en = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Liquidación  {self.contrato.empleado.rut}"


# models.py (añadiendo a lo anterior)


class AFP(models.Model):
    nombre = models.CharField(max_length=100)
    porcentaje_cotizacion = models.DecimalField(
        max_digits=5, decimal_places=2
    )  # ejemplo: 10.00 (%)

    def __str__(self):
        return self.nombre


class Salud(models.Model):
    TIPO_CHOICES = (
        ("FONASA", "Fonasa"),
        ("ISAPRE", "Isapre"),
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    nombre = models.CharField(max_length=100, null=True, blank=True)  # Solo para Isapre
    porcentaje_cotizacion = models.DecimalField(
        max_digits=5, decimal_places=2, default=7.00
    )
    def save(self, *args, **kwargs):
        if self.tipo == 'FONASA':
            self.nombre = 'FONASA'  
        super().save(*args, **kwargs)
    def __str__(self):
        if self.tipo == "FONASA":
            return "Fonasa"
        return f"Isapre: {self.nombre}"


class SeguroCesantia(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    porcentaje_trabajador = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.60
    )
    porcentaje_empleador = models.DecimalField(
        max_digits=5, decimal_places=2, default=2.40
    )

    def __str__(self):
        return self.nombre


class DatosPrevisionales(models.Model):
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE)
    afp = models.ForeignKey(AFP, on_delete=models.SET_NULL, null=True)
    salud = models.ForeignKey(Salud, on_delete=models.SET_NULL, null=True)
    seguro_cesantia = models.ForeignKey(
        SeguroCesantia, on_delete=models.SET_NULL, null=True
    )

    def __str__(self):
        return f"Previsión de {self.empleado.usuario.get_full_name()}"


class TipoDescuento(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class OtroDescuento(models.Model):
    liquidacion = models.ForeignKey(
        Liquidacion, on_delete=models.CASCADE, related_name="detalles_descuento"
    )
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
        ("imponible", "Imponible"),
        ("no_imponible", "No Imponible"),
    ]

    liquidacion = models.ForeignKey(
        "Liquidacion", on_delete=models.CASCADE, related_name="haberes"
    )
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
    categoria = models.CharField(
        max_length=50,
        choices=[
            ("habilidad", "Habilidad"),
            ("certificacion", "Certificación"),
            ("area", "Área"),
        ],
    )
    sinonimos = models.TextField(blank=True, help_text="Separados por coma")
    def __str__(self):
        return f"{self.nombre} ({self.categoria})"


try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")



class Postulante(models.Model):
    ESTADOS = [
        ("postulado", "Postulado"),
        ("entrevista", "Entrevista"),
        ("evaluacion", "Evaluación"),
        ("seleccionado", "Seleccionado"),
        ("descartado", "Descartado"),
    ]
    rut = models.CharField(max_length=12, blank=True, null=True, unique=True)
    primer_nombre = models.CharField(max_length=50)
    otros_nombres = models.CharField(max_length=100, blank=True, null=True)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion = models.TextField(blank=True, null=True)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)
    cargo_postulado = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True)
    curriculum = models.FileField(upload_to="postulantes/cv/", null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="postulado")
    fecha_postulacion = models.DateTimeField(default=timezone.now)
    etiquetas = models.ManyToManyField(Etiqueta, blank=True)
    prioridad = models.DecimalField(max_digits=4, decimal_places=3, default=0.0)
    texto_extraido = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{self.primer_nombre} {self.apellido_paterno} - {self.cargo_postulado}"

    def procesar_curriculum(self):
        try:
            if not self.curriculum:
                return

            pdf = PdfReader(self.curriculum)
            texto = "".join([page.extract_text().lower() for page in pdf.pages])
            self.texto_extraido = texto
            self.save()

            palabras_clave = PalabraClave.objects.all()
            palabras_cv = set(re.findall(r"\b\w+\b", texto))

            # Registrar palabras desconocidas si pasan filtros y aparecen 3+ veces
            palabras_no_reconocidas = set()
            conocidas = set()
            for pc in palabras_clave:
                conocidas.update([pc.nombre] + [s.strip() for s in (pc.sinonimos or "").split(",")])

            for palabra in palabras_cv:
                if palabra not in conocidas and len(palabra) > 3 and not palabra.isdigit():
                    try:
                        obj, created = PalabraDesconocida.objects.get_or_create(palabra=palabra)
                        if not created:
                            obj.veces_detectada += 1
                            obj.save()
                        if obj.veces_detectada >= 3:
                            palabras_no_reconocidas.add(palabra)
                    except Exception as err:
                        print(f"Error registrando palabra desconocida '{palabra}': {err}")

            # Detectar etiquetas por coincidencia o sinónimos
            etiquetas_detectadas = set()
            for pc in palabras_clave:
                variantes = [pc.nombre] + [s.strip() for s in (pc.sinonimos or "").split(",")]
                if any(v in palabras_cv for v in variantes):
                    etiquetas_detectadas.add(pc.nombre)

            for nombre in etiquetas_detectadas:
                etiqueta, _ = Etiqueta.objects.get_or_create(nombre=nombre)
                self.etiquetas.add(etiqueta)

            # 🧠 Generar etiquetas para el cargo si no tiene
            if not self.cargo_postulado.palabras_clave.exists():
                self.cargo_postulado.inicializar_etiquetas_con_ia()

            # Recalcular con posibles nuevas etiquetas IA
            etiquetas_ia = analizar_curriculum_con_ia(self.texto_extraido)
            for nombre in etiquetas_ia:
                etiqueta, _ = Etiqueta.objects.get_or_create(nombre=nombre)
                self.etiquetas.add(etiqueta)

            # 🧠 Vectorización y prioridad
            cargo_vector = {pc.nombre: 1 for pc in self.cargo_postulado.palabras_clave.all()}
            postulante_vector = {e.nombre: 1 for e in self.etiquetas.all()}

            if not cargo_vector or not postulante_vector:
                self.prioridad = 0.0
            else:
                dv = DictVectorizer()
                X = dv.fit_transform([postulante_vector, cargo_vector])
                similitud = cosine_similarity(X[0], X[1])[0][0]
                self.prioridad = round(similitud, 3)

            self.save()

        except Exception as e:
            print(f"Error en extracción y análisis del CV: {e}")



class PalabraDesconocida(models.Model):
    palabra = models.CharField(max_length=100, unique=True)
    fecha_detectada = models.DateTimeField(auto_now_add=True)
    veces_detectada = models.PositiveIntegerField(default=1)
    revisada = models.BooleanField(default=False)

    def __str__(self):
        return self.palabra


class Horario(models.Model):
    DIAS_SEMANA = [
        ("Lunes", "Lunes"),
        ("Martes", "Martes"),
        ("Miércoles", "Miércoles"),
        ("Jueves", "Jueves"),
        ("Viernes", "Viernes"),
        ("Sábado", "Sábado"),
        ("Domingo", "Domingo"),
    ]
    dia_semana = models.CharField(max_length=20, choices=DIAS_SEMANA)
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()

    def __str__(self):
        return f"{self.dia} {self.hora_inicio} - {self.hora_fin}"


class GrupoHorario(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    horarios = models.ManyToManyField(Horario, related_name="grupos")

    def __str__(self):
        return self.nombre


# Asignación de grupo a empleado
class HorarioEmpleado(models.Model):
    empleado = models.ForeignKey("Empleado", on_delete=models.CASCADE)
    grupo_horario = models.ForeignKey(GrupoHorario, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    es_personalizado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.empleado} - {self.grupo_horario}"


class Asistencia(models.Model):
    empleado = models.ForeignKey("Empleado", on_delete=models.CASCADE)
    fecha = models.DateField()

    hora_entrada_real = models.TimeField(blank=True, null=True)
    hora_salida_real = models.TimeField(blank=True, null=True)

    minutos_atraso = models.PositiveIntegerField(default=0)
    minutos_salida_anticipada = models.PositiveIntegerField(default=0)
    horas_trabajadas = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    estado = models.CharField(
        max_length=50,
        choices=[
            ("presente", "Presente"),
            ("presente completo", "Presente (completo)"),
            ("atraso", "Atraso"),
            ("salida anticipada", "Salida anticipada"),
            ("ausente", "Ausente"),
            ("justificado", "Justificado"),
            ("fuera de horario", "Fuera de horario"),
        ],
        default="presente",
    )

    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("empleado", "fecha")

    def __str__(self):
        return f"{self.fecha} - {self.empleado} ({self.estado})"


class ExcepcionHorario(models.Model):
    empleado = models.ForeignKey("Empleado", on_delete=models.CASCADE)
    fecha = models.DateField()
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()
    motivo = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ("empleado", "fecha")

    def __str__(self):
        return f"{self.fecha} - {self.empleado} (excepción)"
