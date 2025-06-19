# Newspaper Dockerizado 📰

Proyecto Django dockerizado para fácil desarrollo y despliegue de una aplicación de periódico.

## Características ✨

- 🐍 Django 5.2.1
- 🐳 Docker y Docker Compose
- 📱 Servidor de desarrollo incluido
- 🗃️ SQLite (base de datos ligera)
- 🎨 Bootstrap 5 con Crispy Forms
- 👥 Sistema de usuarios personalizado
- 📝 Sistema de artículos

## Requisitos 📋

- Docker Desktop
- Git

## Instalación y Uso 🚀

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/BryanMunoz1/newspaper_dockerizado.git
   cd newspaper_dockerizado
   ```

2. **Construir y levantar el contenedor:**
   ```bash
   docker-compose up --build
   ```

3. **Acceder a la aplicación:**
   - Abrir navegador en: http://localhost:8000

## Comandos Útiles 🛠️

### Desarrollo básico
```bash
# Levantar la aplicación
docker-compose up

# Levantar en background
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f

# Parar la aplicación
docker-compose down
```

### Gestión de la aplicación
```bash
# Crear superusuario (admin)
docker-compose exec web python manage.py createsuperuser

# Ejecutar migraciones manualmente
docker-compose exec web python manage.py migrate

# Ejecutar comandos de Django
docker-compose exec web python manage.py <comando>

# Acceder al shell de Django
docker-compose exec web python manage.py shell

# Acceder al contenedor
docker-compose exec web bash
```

### Limpieza
```bash
# Parar y eliminar contenedores
docker-compose down

# Eliminar también los volúmenes (¡cuidado! se perderán los datos)
docker-compose down -v

# Limpiar imágenes no utilizadas
docker system prune
```

## Estructura del Proyecto 📁

```
newspaper_dockerizado/
├── docker-compose.yml          # Configuración de Docker Compose
├── Dockerfile                  # Configuración del contenedor
├── entrypoint.sh              # Script de inicialización
├── .dockerignore              # Archivos ignorados por Docker
├── requirements.txt           # Dependencias de Python
├── manage.py                  # Comando de gestión de Django
├── accounts/                  # App de usuarios
├── articles/                  # App de artículos
├── pages/                     # App de páginas
├── templates/                 # Plantillas HTML
├── static/                    # Archivos estáticos
└── app_newspaper/             # Configuración principal
    ├── settings.py
    ├── urls.py
    └── wsgi.py
```

## Desarrollo 💻

### Cambios en el código
Los cambios en el código se reflejan automáticamente gracias al volumen montado en docker-compose.yml. No necesitas reconstruir el contenedor.

### Base de datos
- Se usa SQLite por simplicidad
- La base de datos se guarda en un volumen persistente (`db_volume`)
- Los datos persisten entre reinicios del contenedor

### Archivos estáticos
- Bootstrap 5 incluido
- Los archivos estáticos se manejan automáticamente
- Se recolectan al iniciar el contenedor

## Aplicaciones Incluidas 📱

- **accounts**: Gestión de usuarios personalizada
- **articles**: Sistema de artículos/noticias
- **pages**: Páginas estáticas (home, about, etc.)

## Acceso de Administrador 👨‍💼

1. Crear superusuario:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

2. Acceder al admin en: http://localhost:8000/admin

## Troubleshooting 🔧

### El contenedor no inicia
- Verificar que Docker Desktop esté ejecutándose
- Comprobar que el puerto 8000 no esté en uso
- Revisar los logs: `docker-compose logs`

### Problemas con migraciones
```bash
# Resetear migraciones (¡cuidado! se perderán datos)
docker-compose exec web python manage.py migrate --fake-initial
```

### Problemas con permisos
```bash
# En Linux/Mac, asegurar permisos del script
chmod +x entrypoint.sh
```

## URLs Principales 🌐

- Home: http://localhost:8000
- Admin: http://localhost:8000/admin
- Artículos: http://localhost:8000/articles/
- Cuentas: http://localhost:8000/accounts/

## Contribuir 🤝

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Notas Técnicas 📝

- Django configurado para desarrollo
- DEBUG=True por defecto
- Email backend configurado para consola
- Timezone: America/Bogota
- Idioma: Español (Colombia)