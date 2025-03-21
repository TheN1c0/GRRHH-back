# Dockerfile
# Backend con Django y PostgreSQL

FROM python:3.11

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de requerimientos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto 8000
EXPOSE 8000

# Comando por defecto para el contenedor
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]