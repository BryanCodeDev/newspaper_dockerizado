from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
import os

def article_image_path(instance, filename):
    """Función para generar la ruta de la imagen del artículo"""
    # Obtener la extensión del archivo
    ext = filename.split('.')[-1]
    # Generar nombre único basado en el título del artículo
    filename = f"article_{instance.id}_{instance.title[:50]}.{ext}"
    # Limpiar caracteres especiales
    filename = "".join(c for c in filename if c.isalnum() or c in '._-')
    return os.path.join('articles/', filename)

class Article(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    image = models.ImageField(
        upload_to=article_image_path,
        blank=True,
        null=True,
        help_text="Imagen principal del artículo (opcional)"
    )
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('article_detail', args=[str(self.id)])
    
    @property
    def has_image(self):
        """Verifica si el artículo tiene una imagen"""
        return bool(self.image and hasattr(self.image, 'url'))