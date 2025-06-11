from personal.models import HistorialCambio
from django.utils.timezone import now


class HistorialMixin:
    def registrar_accion(self, request, accion, detalle):
        HistorialCambio.objects.create(
            usuario=request.user, accion=accion, detalle=detalle, fecha=now()
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        self.registrar_accion(
            self.request, "Crear", f"{instance.__class__.__name__} creado: {instance}"
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        self.registrar_accion(
            self.request, "Editar", f"{instance.__class__.__name__} editado: {instance}"
        )

    def perform_destroy(self, instance):
        self.registrar_accion(
            self.request,
            "Eliminar",
            f"{instance.__class__.__name__} eliminado: {instance}",
        )
        instance.delete()
