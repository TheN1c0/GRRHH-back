from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class TestModel(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# models.py


class HistorialAcceso(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    ip = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.fecha}"


class Nota(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nota de {self.usuario.username} - {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}"

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    
    telefono = models.CharField(max_length=20, blank=True)
    telefono_verificado = models.BooleanField(default=False)
    nuevo_telefono = models.CharField(max_length=20, blank=True, null=True)

    email_verificado = models.BooleanField(default=False)
    nuevo_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f'Perfil de {self.user.username}'