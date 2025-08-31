from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone
from PIL import Image
import os

def article_image_path(instance, filename):
    """Función para generar la ruta de la imagen del artículo"""
    # Obtener la extensión del archivo
    ext = filename.split('.')[-1].lower()
    # Generar nombre único usando timestamp y título
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    title_slug = "".join(c for c in instance.title[:30] if c.isalnum() or c in '-_').lower()
    filename = f"article_{timestamp}_{title_slug}.{ext}"
    return os.path.join('articles/', filename)

class ArticleQuerySet(models.QuerySet):
    """QuerySet personalizado para Article"""
    
    def published(self):
        """Retorna solo artículos publicados"""
        return self.filter(is_published=True)
    
    def by_author(self, author):
        """Filtra artículos por autor"""
        return self.filter(author=author)
    
    def search(self, query):
        """Búsqueda en título y contenido"""
        return self.filter(
            models.Q(title__icontains=query) | 
            models.Q(body__icontains=query)
        )

class ArticleManager(models.Manager):
    """Manager personalizado para Article"""
    
    def get_queryset(self):
        return ArticleQuerySet(self.model, using=self._db)
    
    def published(self):
        return self.get_queryset().published()
    
    def recent(self, limit=5):
        return self.get_queryset().published().order_by('-date')[:limit]

class Article(models.Model):
    """Modelo para artículos del blog de drift"""
    
    # Campos principales
    title = models.CharField(
        max_length=255,
        verbose_name="Título",
        help_text="Título del artículo (máximo 255 caracteres)"
    )
    body = models.TextField(
        verbose_name="Contenido",
        help_text="Contenido principal del artículo"
    )
    image = models.ImageField(
        upload_to=article_image_path,
        blank=True,
        null=True,
        verbose_name="Imagen Principal",
        help_text="Imagen principal del artículo (opcional, máximo 5MB)"
    )
    
    # Metadatos
    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        verbose_name="Autor",
        related_name="articles"
    )
    
    # Control de publicación
    is_published = models.BooleanField(
        default=True,
        verbose_name="Publicado",
        help_text="Determina si el artículo es visible públicamente"
    )
    
    # SEO y metadatos adicionales
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        verbose_name="Meta Descripción",
        help_text="Descripción para SEO (máximo 160 caracteres)"
    )
    
    # Estadísticas
    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Visualizaciones"
    )
    
    # Manager personalizado
    objects = ArticleManager()
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Artículo"
        verbose_name_plural = "Artículos"
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['author']),
            models.Index(fields=['is_published']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('article_detail', args=[str(self.pk)])
    
    @property
    def has_image(self):
        """Verifica si el artículo tiene una imagen"""
        return bool(self.image and hasattr(self.image, 'url'))
    
    @property
    def reading_time(self):
        """Calcula el tiempo estimado de lectura (asumiendo 200 palabras por minuto)"""
        word_count = len(self.body.split())
        reading_time = max(1, round(word_count / 200))
        return f"{reading_time} min de lectura"
    
    @property
    def excerpt(self):
        """Retorna un extracto del artículo"""
        if self.meta_description:
            return self.meta_description
        words = self.body.split()[:30]
        return ' '.join(words) + ('...' if len(self.body.split()) > 30 else '')
    
    def save(self, *args, **kwargs):
        """Override del método save para optimizar imágenes"""
        super().save(*args, **kwargs)
        
        # Optimizar imagen si existe
        if self.image:
            img_path = self.image.path
            if os.path.exists(img_path):
                with Image.open(img_path) as img:
                    # Redimensionar si es muy grande (máximo 1200px de ancho)
                    if img.width > 1200:
                        ratio = 1200 / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((1200, new_height), Image.Resampling.LANCZOS)
                        img.save(img_path, optimize=True, quality=85)
    
    def increment_views(self):
        """Incrementa el contador de visualizaciones"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def can_edit(self, user):
        """Verifica si un usuario puede editar este artículo"""
        return user.is_authenticated and (user == self.author or user.is_staff)
    
    def can_delete(self, user):
        """Verifica si un usuario puede eliminar este artículo"""
        return user.is_authenticated and (user == self.author or user.is_staff)


class Category(models.Model):
    """Modelo para categorías de artículos (opcional - para futuras mejoras)"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descripción"
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="Slug"
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category_detail', args=[str(self.slug)])

# Si quieres agregar categorías al modelo Article en el futuro:
"""
# Agregar este campo al modelo Article:
category = models.ForeignKey(
    Category,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    verbose_name="Categoría",
    related_name="articles"
)
"""