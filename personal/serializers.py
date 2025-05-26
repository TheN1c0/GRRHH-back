from rest_framework import serializers
from .models import (Empleado,
                     Cargo, 
                     Contrato, 
                     Postulante, 
                     Etiqueta, 
                     Cargo, 
                     AFP, 
                     Salud, 
                     SeguroCesantia)


class EmpleadoSerializer(serializers.ModelSerializer):
    nombre_cargo = serializers.CharField(source='cargo.nombre', read_only=True)
    nombre_departamento = serializers.CharField(source='cargo.departamento.nombre', read_only=True)
    nombre_usuario = serializers.SerializerMethodField()

    class Meta:
        model = Empleado
        fields = [
            'id',
            'usuario',
            'primer_nombre',
            'otros_nombres',
            'apellido_paterno',
            'apellido_materno',
            'rut',
            'fecha_nacimiento',
            'direccion',
            'telefono',
            'cargo',
            'nombre_cargo',
            'nombre_departamento',
            'nombre_usuario'
        ]

    def get_nombre_usuario(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name()
        return "Sin usuario asignado"

class CargoSerializer(serializers.ModelSerializer):
    nombre_departamento = serializers.CharField(source='departamento.nombre', read_only=True)

    class Meta:
        model = Cargo
        fields = ['id', 'nombre', 'nombre_departamento']



from rest_framework import serializers

class HaberInputSerializer(serializers.Serializer):
    nombre = serializers.CharField()
    tipo = serializers.ChoiceField(choices=[('imponible', 'Imponible'), ('no_imponible', 'No Imponible')])
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)

class DescuentoInputSerializer(serializers.Serializer):
    tipo = serializers.CharField()  # nombre del tipo
    monto = serializers.DecimalField(max_digits=12, decimal_places=2)
    descripcion = serializers.CharField(allow_blank=True, required=False)

class LiquidacionInputSerializer(serializers.Serializer):
    contrato_id = serializers.IntegerField()
    periodo_inicio = serializers.DateField()
    periodo_termino = serializers.DateField()
    gratificacion_tipo = serializers.ChoiceField(choices=[('legal', 'Legal'), ('pactada', 'Pactada')])
    haberes = HaberInputSerializer(many=True)
    descuentos = DescuentoInputSerializer(many=True)
class ContratoEmpleadoSerializer(serializers.ModelSerializer):
    nombre_empleado = serializers.SerializerMethodField()
    cargo = serializers.CharField(source='empleado.cargo.nombre', default='Sin cargo')

    class Meta:
        model = Contrato
        fields = ['id', 'nombre_empleado', 'cargo']

    def get_nombre_empleado(self, obj):
        emp = obj.empleado
        return f"{emp.primer_nombre} {emp.otros_nombres or ''} {emp.apellido_paterno} {emp.apellido_materno}".strip()

class EtiquetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Etiqueta
        fields = ['id', 'nombre']
    
class PostulanteSerializer(serializers.ModelSerializer):
    etiquetas = EtiquetaSerializer(many=True, read_only=True)
    cargo_postulado = serializers.PrimaryKeyRelatedField(queryset=Cargo.objects.all())

    class Meta:
        model = Postulante
        fields = [
            'id',
            'primer_nombre',
            'otros_nombres',
            'apellido_paterno',
            'apellido_materno',
            'direccion',
            'correo',
            'telefono',
            'cargo_postulado',
            'curriculum',
            'estado',
            'fecha_postulacion',
            'etiquetas',
        ]
        read_only_fields = ['estado', 'fecha_postulacion', 'etiquetas']
        
class AFPSerializer(serializers.ModelSerializer):
    class Meta:
        model = AFP
        fields = '__all__'

class SaludSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salud
        fields = '__all__'

class CesantiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeguroCesantia
        fields = '__all__'