#!/bin/sh

echo "¿Deseas instalar requirements.txt antes de iniciar el servidor? (s/n)"
read instalar

if [ "$instalar" = "s" ]; then
    echo "Instalando dependencias..."
    pip install -r requirements.txt
fi

echo "¿Deseas aplicar migraciones? (s/n)"
read migrar

if [ "$migrar" = "s" ]; then
    echo "Ejecutando migraciones..."
    python manage.py migrate
fi

echo "¿Deseas iniciar el servidor Django? (s/n)"
read iniciar

if [ "$iniciar" = "s" ]; then
    echo "Iniciando servidor..."
    python manage.py runserver 0.0.0.0:8000
else
    echo "Servidor no iniciado. El contenedor sigue activo."
    tail -f /dev/null  # mantiene el contenedor vivo sin cerrar
fi
