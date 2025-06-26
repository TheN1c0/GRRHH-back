from rest_framework.permissions import BasePermission
from .models import PermisosRRHH

class PuedeCrear(BasePermission):
    def has_permission(self, request, view):
        try:
            return PermisosRRHH.objects.get(user=request.user).puede_crear
        except PermisosRRHH.DoesNotExist:
            return False

class PuedeEditar(BasePermission):
    def has_permission(self, request, view):
        try:
            return PermisosRRHH.objects.get(user=request.user).puede_editar
        except PermisosRRHH.DoesNotExist:
            return False

class PuedeEliminar(BasePermission):
    def has_permission(self, request, view):
        try:
            return PermisosRRHH.objects.get(user=request.user).puede_eliminar
        except PermisosRRHH.DoesNotExist:
            return False
