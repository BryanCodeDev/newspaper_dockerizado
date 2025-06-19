# Usar una imagen base de Python
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto
COPY . /app/

# Crear directorio para la base de datos
RUN mkdir -p /app/data

# Hacer ejecutable el script de entrada
RUN chmod +x /app/entrypoint.sh

# Exponer el puerto
EXPOSE 8000

# Comando por defecto (se sobrescribe con entrypoint.sh)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]