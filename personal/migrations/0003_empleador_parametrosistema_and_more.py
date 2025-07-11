# Generated by Django 5.1.7 on 2025-05-15 04:46

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('personal', '0002_empleado_apellido_materno_empleado_apellido_paterno_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Empleador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('rut', models.CharField(max_length=12)),
                ('direccion', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='ParametroSistema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('valor_decimal', models.DecimalField(decimal_places=2, max_digits=12)),
                ('fecha_vigencia', models.DateField()),
            ],
        ),
        migrations.RemoveField(
            model_name='liquidacion',
            name='descuento_afp',
        ),
        migrations.RemoveField(
            model_name='liquidacion',
            name='descuento_cesantia',
        ),
        migrations.RemoveField(
            model_name='liquidacion',
            name='descuento_inasistencias',
        ),
        migrations.RemoveField(
            model_name='liquidacion',
            name='descuento_salud',
        ),
        migrations.RemoveField(
            model_name='liquidacion',
            name='fecha_pago',
        ),
        migrations.RemoveField(
            model_name='liquidacion',
            name='ingresos_no_imponibles',
        ),
        migrations.RemoveField(
            model_name='liquidacion',
            name='monto_horas_extras',
        ),
        migrations.RemoveField(
            model_name='liquidacion',
            name='otros_descuentos',
        ),
        migrations.RemoveField(
            model_name='liquidacion',
            name='sueldo_imponible',
        ),
        migrations.AddField(
            model_name='contrato',
            name='tipo_contrato',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='actualizado_en',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='cargo_empleado',
            field=models.CharField(default='Sin cargo', max_length=100),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='comision_afp',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='creado_en',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='direccion_empleador',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='fecha_ingreso',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='gratificacion',
            field=models.DecimalField(decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='nombre_afp',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='nombre_empleado',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='nombre_salud',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='nombre_seguro_cesantia',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='periodo_inicio',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='periodo_termino',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='porcentaje_afp',
            field=models.DecimalField(decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='porcentaje_cesantia_empleador',
            field=models.DecimalField(decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='porcentaje_cesantia_trabajador',
            field=models.DecimalField(decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='porcentaje_salud',
            field=models.DecimalField(decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='razon_social_empleador',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='rut_empleado',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='rut_empleador',
            field=models.CharField(max_length=12, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='sueldo_base',
            field=models.DecimalField(decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='tipo_contrato',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='tipo_salud',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='total_haberes',
            field=models.DecimalField(decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='segurocesantia',
            name='nombre',
            field=models.CharField(default='Sin nombre', max_length=100, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='liquidacion',
            name='sueldo_bruto',
            field=models.DecimalField(decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='liquidacion',
            name='sueldo_liquido',
            field=models.DecimalField(decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='liquidacion',
            name='total_descuentos',
            field=models.DecimalField(decimal_places=2, max_digits=12, null=True),
        ),
        migrations.CreateModel(
            name='Haber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('tipo', models.CharField(choices=[('imponible', 'Imponible'), ('no_imponible', 'No Imponible')], max_length=20)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=10)),
                ('liquidacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='haberes', to='personal.liquidacion')),
            ],
        ),
    ]
