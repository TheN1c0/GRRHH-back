from rest_framework import serializers
from .models import Empleado, Cargo

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
