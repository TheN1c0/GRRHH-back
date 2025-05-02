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
