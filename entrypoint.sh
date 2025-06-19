#!/bin/sh

echo "🚀 Iniciando aplicación Django..."

# Crear directorio de datos si no existe
mkdir -p /app/data

# Esperar un momento para asegurar que todo esté listo
sleep 2

# Ejecutar migraciones
echo "📝 Aplicando migraciones..."
python manage.py makemigrations
python manage.py migrate

# Recolectar archivos estáticos
echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear || echo "⚠️  Advertencia: No se pudieron recolectar archivos estáticos"

# Crear superusuario automáticamente si no existe (opcional)
echo "👤 Verificando superusuario..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('No hay superusuario, puedes crear uno con: docker-compose exec web python manage.py createsuperuser')
else:
    print('✅ Superusuario ya existe')
" 2>/dev/null || echo "ℹ️  Para crear un superusuario: docker-compose exec web python manage.py createsuperuser"

# Iniciar el servidor de desarrollo de Django
echo "🌐 Iniciando servidor Django en 0.0.0.0:8000..."
echo "🔗 Accede a: http://localhost:8000"
python manage.py runserver 0.0.0.0:8000