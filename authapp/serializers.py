from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Nota, PerfilUsuario


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class NotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nota
        fields = ["id", "contenido", "fecha_creacion"]


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilUsuario
        fields = ['telefono', 'telefono_verificado', 'nuevo_telefono', 'email_verificado', 'nuevo_email']


class MiCuentaSerializer(serializers.ModelSerializer):
    telefono = serializers.CharField(
    source='perfil.telefono',
    required=False,
    allow_blank=True
)
    telefono_verificado = serializers.BooleanField(source='perfil.telefono_verificado', read_only=True)
    nuevo_telefono = serializers.CharField(
    source='perfil.nuevo_telefono',
    required=False,
    allow_blank=True
)

    email_verificado = serializers.BooleanField(source='perfil.email_verificado', read_only=True)
    nuevo_email = serializers.EmailField(
    source='perfil.nuevo_email',
    required=False,
    allow_blank=True
)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username',
                  'telefono', 'telefono_verificado', 'nuevo_telefono',
                  'email_verificado', 'nuevo_email']

    def update(self, instance, validated_data):
        perfil_data = validated_data.pop('perfil', {})

        # Actualizar datos del usuario
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Actualizar perfil
        perfil = instance.perfil
        for attr, value in perfil_data.items():
            setattr(perfil, attr, value)
        perfil.save()

        return instance
