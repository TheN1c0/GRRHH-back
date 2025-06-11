from django.contrib import admin
from .models import HorarioEmpleado

# Register your models here.
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered

app_models = apps.get_app_config("personal").get_models()

for model in app_models:
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass


class HorarioEmpleadoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "empleado",
        "grupo_horario",
        "fecha_inicio",
        "fecha_fin",
        "es_personalizado",
    )
