# Dockerfile
# Backend con Django y PostgreSQL

FROM python:3.11

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de requerimientos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto (incluido start.sh si no usas volumen)
COPY . .

# Dar permisos de ejecución al script
RUN chmod +x start.sh

# Exponer el puerto de Django
EXPOSE 8000

# Usar start.sh como comando por defecto
CMD ["sh", "start.sh"]
