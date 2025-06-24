from django.db import models
from django.contrib.auth.models import User
import random
from django.utils import timezone
from datetime import timedelta
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

    # NUEVOS CAMPOS PARA VERIFICACIÓN SMS
    sms_code = models.CharField(max_length=6, blank=True, null=True)
    sms_code_created = models.DateTimeField(blank=True, null=True)

    def generate_sms_code(self) -> str:
        """Genera y guarda un código de verificación de 6 dígitos."""
        self.sms_code = f"{random.randint(100000, 999999)}"
        self.sms_code_created = timezone.now()
        self.save()
        return self.sms_code

    def verify_sms_code(self, code: str) -> bool:
        """Verifica si el código coincide y está dentro del tiempo válido (10 min)."""
        if not self.sms_code or not self.sms_code_created:
            return False

        expirado = timezone.now() - self.sms_code_created > timedelta(minutes=10)
        if self.sms_code == code and not expirado:
            self.telefono = self.nuevo_telefono
            self.telefono_verificado = True
            self.nuevo_telefono = ''
            self.sms_code = None
            self.sms_code_created = None
            self.save()
            return True
        return False
class PermisosRRHH(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='permisos_rrhh')
    solo_lectura = models.BooleanField(default=False)
    puede_eliminar = models.BooleanField(default=False)

    def __str__(self):
        return f"Permisos de {self.user.username}"
