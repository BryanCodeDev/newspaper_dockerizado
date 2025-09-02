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
    
    @property
    def total_comments(self):
        """Cuenta total de comentarios (incluye respuestas)"""
        return self.comments.count()
    
    @property
    def root_comments_count(self):
        """Cuenta solo comentarios principales (sin respuestas)"""
        return self.comments.filter(parent=None).count()
    
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


class CommentQuerySet(models.QuerySet):
    """QuerySet personalizado para Comment"""
    
    def root_comments(self):
        """Solo comentarios principales (sin respuestas)"""
        return self.filter(parent=None)
    
    def replies(self):
        """Solo respuestas a comentarios"""
        return self.exclude(parent=None)
    
    def for_article(self, article):
        """Comentarios para un artículo específico"""
        return self.filter(article=article)
    
    def by_author(self, author):
        """Comentarios de un autor específico"""
        return self.filter(author=author)


class CommentManager(models.Manager):
    """Manager personalizado para Comment"""
    
    def get_queryset(self):
        return CommentQuerySet(self.model, using=self._db)
    
    def root_comments(self):
        return self.get_queryset().root_comments()
    
    def for_article(self, article):
        return self.get_queryset().for_article(article)


class Comment(models.Model):
    """Modelo para comentarios de artículos con sistema de respuestas anidadas"""
    
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Artículo"
    )
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Autor"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name="Comentario Padre"
    )
    
    content = models.TextField(
        max_length=1000,
        verbose_name="Contenido"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )
    
    is_edited = models.BooleanField(
        default=False,
        verbose_name="Editado"
    )
    
    objects = CommentManager()
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"
        indexes = [
            models.Index(fields=['article', 'created_at']),
            models.Index(fields=['author']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self):
        return f'Comentario de {self.author.username} en "{self.article.title}"'
    
    def get_absolute_url(self):
        return reverse('articles:article_detail', args=[str(self.article.pk)]) + f'#comment-{self.pk}'
    
    @property
    def is_reply(self):
        """Verifica si es una respuesta a otro comentario"""
        return self.parent is not None
    
    @property
    def replies_count(self):
        """Cuenta las respuestas directas a este comentario"""
        return self.replies.count()
    
    @property
    def content_preview(self):
        """Preview del contenido para admin/listados"""
        words = self.content.split()[:15]
        preview = ' '.join(words)
        return preview + ('...' if len(self.content.split()) > 15 else '')
    
    def can_edit(self, user):
        """Verifica si el usuario puede editar el comentario"""
        return user.is_authenticated and (user == self.author or user.is_staff)
    
    def can_delete(self, user):
        """Verifica si el usuario puede eliminar el comentario"""
        return user.is_authenticated and (user == self.author or user.is_staff)
    
    def can_reply(self, user):
        """Verifica si el usuario puede responder al comentario"""
        return user.is_authenticated
    
    def get_reply_depth(self):
        """Calcula la profundidad de anidación (máximo 3 niveles)"""
        depth = 0
        current = self.parent
        while current and depth < 3:
            depth += 1
            current = current.parent
        return depth
    
    def save(self, *args, **kwargs):
        # Extraer el parámetro personalizado antes de llamar a super()
        skip_edited_flag = kwargs.pop('skip_edited_flag', False)
        
        # Marcar como editado si no es la primera vez que se guarda
        if self.pk and not skip_edited_flag:
            self.is_edited = True
            
        super().save(*args, **kwargs)


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