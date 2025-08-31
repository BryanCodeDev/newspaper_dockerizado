from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone
from PIL import Image
import os

def article_image_path(instance, filename):
    """Función para generar la ruta de la imagen del artículo"""
    ext = filename.split('.')[-1].lower()
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    title_slug = "".join(c for c in instance.title[:30] if c.isalnum() or c in '-_').lower()
    filename = f"article_{timestamp}_{title_slug}.{ext}"
    return os.path.join('articles/', filename)

class ArticleQuerySet(models.QuerySet):
    """QuerySet personalizado para Article"""
    
    def published(self):
        return self.filter(is_published=True)
    
    def by_author(self, author):
        return self.filter(author=author)
    
    def search(self, query):
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
    
    title = models.CharField(max_length=255, verbose_name="Título")
    body = models.TextField(verbose_name="Contenido")
    image = models.ImageField(
        upload_to=article_image_path,
        blank=True,
        null=True,
        verbose_name="Imagen Principal"
    )
    
    date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name="Autor"
    )
    
    is_published = models.BooleanField(default=True, verbose_name="Publicado")
    meta_description = models.CharField(max_length=160, blank=True, verbose_name="Meta Descripción")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Visualizaciones")
    
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
        # 👈 CORREGIDO: ahora usa el namespace "articles"
        return reverse('articles:article_detail', args=[str(self.pk)])
    
    @property
    def has_image(self):
        return bool(self.image and hasattr(self.image, 'url'))
    
    @property
    def reading_time(self):
        word_count = len(self.body.split())
        reading_time = max(1, round(word_count / 200))
        return f"{reading_time} min de lectura"
    
    @property
    def excerpt(self):
        if self.meta_description:
            return self.meta_description
        words = self.body.split()[:30]
        return ' '.join(words) + ('...' if len(self.body.split()) > 30 else '')
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            img_path = self.image.path
            if os.path.exists(img_path):
                with Image.open(img_path) as img:
                    if img.width > 1200:
                        ratio = 1200 / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((1200, new_height), Image.Resampling.LANCZOS)
                        img.save(img_path, optimize=True, quality=85)
    
    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def can_edit(self, user):
        return user.is_authenticated and (user == self.author or user.is_staff)
    
    def can_delete(self, user):
        return user.is_authenticated and (user == self.author or user.is_staff)


class Category(models.Model):
    """Modelo para categorías de artículos"""
    
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    
    class Meta:
        ordering = ['name']
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('articles:category_detail', args=[str(self.slug)])
