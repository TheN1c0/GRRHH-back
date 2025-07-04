# Generated by Django 5.1.7 on 2025-06-03 05:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personal', '0014_postulante_fecha_nacimiento'),
    ]

    operations = [
        migrations.CreateModel(
            name='Horario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dia_semana', models.CharField(choices=[('Lunes', 'Lunes'), ('Martes', 'Martes'), ('Miércoles', 'Miércoles'), ('Jueves', 'Jueves'), ('Viernes', 'Viernes'), ('Sábado', 'Sábado'), ('Domingo', 'Domingo')], max_length=10)),
                ('hora_entrada', models.TimeField()),
                ('hora_salida', models.TimeField()),
            ],
        ),
        migrations.RemoveField(
            model_name='registroasistencia',
            name='empleado',
        ),
        migrations.CreateModel(
            name='Asistencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('hora_entrada_real', models.TimeField(blank=True, null=True)),
                ('hora_salida_real', models.TimeField(blank=True, null=True)),
                ('minutos_atraso', models.PositiveIntegerField(default=0)),
                ('minutos_salida_anticipada', models.PositiveIntegerField(default=0)),
                ('horas_trabajadas', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('estado', models.CharField(choices=[('presente', 'Presente'), ('presente completo', 'Presente (completo)'), ('atraso', 'Atraso'), ('salida anticipada', 'Salida anticipada'), ('ausente', 'Ausente'), ('justificado', 'Justificado'), ('fuera de horario', 'Fuera de horario')], default='presente', max_length=50)),
                ('observaciones', models.TextField(blank=True, null=True)),
                ('empleado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='personal.empleado')),
            ],
            options={
                'unique_together': {('empleado', 'fecha')},
            },
        ),
        migrations.CreateModel(
            name='ExcepcionHorario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('hora_entrada', models.TimeField()),
                ('hora_salida', models.TimeField()),
                ('motivo', models.CharField(blank=True, max_length=255, null=True)),
                ('empleado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='personal.empleado')),
            ],
            options={
                'unique_together': {('empleado', 'fecha')},
            },
        ),
        migrations.CreateModel(
            name='GrupoHorario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('horarios', models.ManyToManyField(related_name='grupos', to='personal.horario')),
            ],
        ),
        migrations.CreateModel(
            name='HorarioEmpleado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField(blank=True, null=True)),
                ('empleado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='personal.empleado')),
                ('grupo_horario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='personal.grupohorario')),
            ],
        ),
        migrations.DeleteModel(
            name='PermisoAusencia',
        ),
        migrations.DeleteModel(
            name='RegistroAsistencia',
        ),
    ]
