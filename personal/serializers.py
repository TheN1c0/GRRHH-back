from rest_framework import serializers
from .models import (
    Empleado,
    Cargo,
    Contrato,
    Postulante,
    Etiqueta,
    Cargo,
    AFP,
    Salud,
    SeguroCesantia,
    ReglasContrato,
    Departamento,
    TipoContrato,
    GrupoHorario,
    Horario,
    HorarioEmpleado,
    HistorialCambio,
    PalabraClave,
    DatosPrevisionales,
)


class EmpleadoSerializer(serializers.ModelSerializer):
    nombre_cargo = serializers.CharField(source="cargo.nombre", read_only=True)
    nombre_departamento = serializers.CharField(
        source="cargo.departamento.nombre", read_only=True
    )
    nombre_usuario = serializers.SerializerMethodField()

    grupo_nombre = serializers.SerializerMethodField()
    grupo_id = serializers.SerializerMethodField()
    es_personalizado = serializers.SerializerMethodField()
    fecha_inicio = serializers.SerializerMethodField()
    fecha_fin = serializers.SerializerMethodField()
    horario_empleado_id = serializers.SerializerMethodField()
    contrato = serializers.SerializerMethodField()
    afp = serializers.SerializerMethodField()
    salud = serializers.SerializerMethodField()
    cesantia = serializers.SerializerMethodField()
    class Meta:
        model = Empleado
        fields = [
            "id",
            "usuario",
            "primer_nombre",
            "otros_nombres",
            "apellido_paterno",
            "apellido_materno",
            "rut",
            "fecha_nacimiento",
            "direccion",
            "telefono",
            "cargo",
            "nombre_cargo",
            "nombre_departamento",
            "nombre_usuario",
            "grupo_nombre",
            "grupo_id",
            "es_personalizado",
            "fecha_inicio",
            "fecha_fin",
            "horario_empleado_id",
            "estado",
            "contrato", 
            "afp",
            "salud", 
            "cesantia"
        ]

    def get_nombre_usuario(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name()
        return "Sin usuario asignado"

    def _get_ultimo_horario(self, obj):
        return obj.horarioempleado_set.order_by("-fecha_inicio").first()

    def get_grupo_nombre(self, obj):
        horario = self._get_ultimo_horario(obj)
        return horario.grupo_horario.nombre if horario else None

    def get_grupo_id(self, obj):
        horario = self._get_ultimo_horario(obj)
        return horario.grupo_horario.id if horario else None

    def get_es_personalizado(self, obj):
        horario = self._get_ultimo_horario(obj)
        return (
            getattr(horario.grupo_horario, "es_personalizado", False)
            if horario
            else None
        )

    def get_fecha_inicio(self, obj):
        horario = self._get_ultimo_horario(obj)
        return horario.fecha_inicio if horario else None

    def get_fecha_fin(self, obj):
        horario = self._get_ultimo_horario(obj)
        return horario.fecha_fin if horario else None

    def get_horario_empleado_id(self, obj):
        horario = obj.horarioempleado_set.order_by("-fecha_inicio").first()
        return horario.id if horario else None

    def get_contrato(self, obj):
        contrato = getattr(obj, 'contrato', None)
        if contrato and contrato.tipo_contrato:
            return contrato.tipo_contrato.nombre
        return "No tiene contrato asignado"

    def get_afp(self, obj):
        previsional = getattr(obj, 'datosprevisionales', None)
        if previsional and previsional.afp:
            return previsional.afp.nombre
        return "No asignado aún"

    def get_salud(self, obj):
        previsional = getattr(obj, 'datosprevisionales', None)
        if previsional and previsional.salud:
            return previsional.salud.nombre
        return "No asignado aún"

    def get_cesantia(self, obj):
        previsional = getattr(obj, 'datosprevisionales', None)
        if previsional and previsional.seguro_cesantia:
            return previsional.seguro_cesantia.nombre
        return "No asignado aún"

class CargoSerializer(serializers.ModelSerializer):
    departamento_nombre = serializers.CharField(source="departamento.nombre", read_only=True)
    superior_nombre = serializers.CharField(source="superior.nombre", read_only=True)

    generar_etiquetas_ia = serializers.BooleanField(write_only=True, required=False)

    palabras_clave = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=PalabraClave.objects.all(),
        required=False
    )

    # ✅ Campo de solo lectura para mostrar etiquetas completas
    palabras_clave_detalle = serializers.SerializerMethodField()

    class Meta:
        model = Cargo
        fields = [
            "id",
            "nombre",
            "departamento",
            "superior",
            "departamento_nombre",
            "superior_nombre",
            "generar_etiquetas_ia",
            "palabras_clave",
            "palabras_clave_detalle"  # importante agregar aquí también
        ]

    def get_palabras_clave_detalle(self, obj):
        return [
            {
                "id": pk.id,
                "nombre": pk.nombre,
                "categoria": pk.categoria
            }
            for pk in obj.palabras_clave.all()
        ]
    def create(self, validated_data):
        validated_data.pop('generar_etiquetas_ia', None)
        return super().create(validated_data)



class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = ["id", "nombre"]


from rest_framework import serializers


class HaberInputSerializer(serializers.Serializer):
    nombre = serializers.CharField()
    tipo = serializers.ChoiceField(
        choices=[("imponible", "Imponible"), ("no_imponible", "No Imponible")]
    )
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)


class DescuentoInputSerializer(serializers.Serializer):
    tipo = serializers.CharField()  # nombre del tipo
    monto = serializers.DecimalField(max_digits=12, decimal_places=2)
    descripcion = serializers.CharField(allow_blank=True, required=False)


class LiquidacionInputSerializer(serializers.Serializer):
    contrato_id = serializers.IntegerField()
    periodo_inicio = serializers.DateField()
    periodo_termino = serializers.DateField()
    gratificacion_tipo = serializers.ChoiceField(
        choices=[("legal", "Legal"), ("pactada", "Pactada")]
    )
    haberes = HaberInputSerializer(many=True)
    descuentos = DescuentoInputSerializer(many=True)


class ContratoEmpleadoSerializer(serializers.ModelSerializer):
    nombre_empleado = serializers.SerializerMethodField()
    cargo = serializers.CharField(source="empleado.cargo.nombre", default="Sin cargo")

    class Meta:
        model = Contrato
        fields = ["id", "nombre_empleado", "cargo"]

    def get_nombre_empleado(self, obj):
        emp = obj.empleado
        return f"{emp.primer_nombre} {emp.otros_nombres or ''} {emp.apellido_paterno} {emp.apellido_materno}".strip()


class EtiquetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Etiqueta
        fields = ["id", "nombre"]


class PostulanteSerializer(serializers.ModelSerializer):
    etiquetas = EtiquetaSerializer(many=True, read_only=True)
    cargo_postulado = serializers.PrimaryKeyRelatedField(queryset=Cargo.objects.all())
    cargo_postulado_nombre = serializers.CharField(
    source="cargo_postulado.nombre", read_only=True
)

    class Meta:
        model = Postulante
        fields = [
            "id",
            "rut",
            "primer_nombre",
            "otros_nombres",
            "apellido_paterno",
            "apellido_materno",
            "direccion",
            "fecha_nacimiento",
            "correo",
            "telefono",
            "cargo_postulado",
            "cargo_postulado_nombre", 
            "curriculum",
            "estado",
            "fecha_postulacion",
            "etiquetas",
        ]
        read_only_fields = ["estado", "fecha_postulacion", "etiquetas"]


class AFPSerializer(serializers.ModelSerializer):
    class Meta:
        model = AFP
        fields = "__all__"


class SaludSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salud
        fields = "__all__"


class CesantiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeguroCesantia
        fields = "__all__"


class ReglasContratoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReglasContrato
        fields = "__all__"


class TipoContratoSerializer(serializers.ModelSerializer):
    reglas_nombre = serializers.CharField(source="reglas.nombre", read_only=True)

    class Meta:
        model = TipoContrato
        fields = ["id", "nombre", "reglas", "reglas_nombre"]


class HorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Horario
        fields = "__all__"


class GrupoHorarioSerializer(serializers.ModelSerializer):
    horarios = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Horario.objects.all()
    )

    class Meta:
        model = GrupoHorario
        fields = "__all__"


class HorarioEmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorarioEmpleado
        fields = "__all__"


class HistorialCambioSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField()

    class Meta:
        model = HistorialCambio
        fields = "__all__"
        
class ContratoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contrato
        fields = '__all__'
        
class PalabraClaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = PalabraClave
        fields = ['id', 'nombre', 'categoria']

class DatosPrevisionalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatosPrevisionales
        fields = ['empleado', 'afp', 'salud', 'seguro_cesantia']
