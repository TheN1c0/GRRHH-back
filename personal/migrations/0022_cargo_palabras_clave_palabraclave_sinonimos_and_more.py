# Generated by Django 5.2.1 on 2025-06-24 19:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personal', '0021_empleado_estado'),
    ]

    operations = [
        migrations.AddField(
            model_name='cargo',
            name='palabras_clave',
            field=models.ManyToManyField(blank=True, to='personal.palabraclave'),
        ),
        migrations.AddField(
            model_name='palabraclave',
            name='sinonimos',
            field=models.TextField(blank=True, help_text='Separados por coma'),
        ),
        migrations.AddField(
            model_name='postulante',
            name='texto_extraido',
            field=models.TextField(blank=True, null=True),
        ),
    ]
