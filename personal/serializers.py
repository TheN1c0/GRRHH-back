from rest_framework import serializers
from .models import Empleado

class EmpleadoSerializer(serializers.ModelSerializer):
    nombre_usuario = serializers.SerializerMethodField()
    nombre_cargo = serializers.CharField(source='cargo.nombre', read_only=True)
    nombre_departamento = serializers.CharField(source='cargo.departamento.nombre', read_only=True)

    class Meta:
        model = Empleado
        fields = [
            'id',
            'rut',
            'fecha_nacimiento',
            'direccion',
            'telefono',
            'nombre_usuario',
            'nombre_cargo',
            'nombre_departamento',
        ]

    def get_nombre_usuario(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name()
        return "Sin usuario asignado"
