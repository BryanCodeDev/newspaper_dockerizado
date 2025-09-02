from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Article, Comment

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Configuración del admin para Article"""
    
    list_display = [
        'title', 
        'author', 
        'date', 
        'is_published',
        'views_count',
        'comments_count_display',
        'has_image_display',
        'reading_time'
    ]
    
    list_filter = [
        'is_published',
        'date',
        'author',
        'updated'
    ]
    
    search_fields = [
        'title',
        'body',
        'author__username',
        'author__first_name',
        'author__last_name'
    ]
    
    readonly_fields = [
        'date',
        'updated',
        'views_count',
        'reading_time',
        'comments_count_display'
    ]
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('title', 'body', 'author')
        }),
        ('Multimedia', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('SEO y Metadatos', {
            'fields': ('meta_description', 'is_published'),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('views_count', 'comments_count_display', 'date', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 20
    date_hierarchy = 'date'
    
    def has_image_display(self, obj):
        """Muestra si el artículo tiene imagen"""
        if obj.has_image:
            return format_html(
                '<span style="color: green;">✓ Sí</span>'
            )
        return format_html(
            '<span style="color: red;">✗ No</span>'
        )
    has_image_display.short_description = 'Imagen'
    has_image_display.admin_order_field = 'image'
    
    def comments_count_display(self, obj):
        """Muestra el número de comentarios"""
        count = obj.total_comments
        if count > 0:
            return format_html(
                '<span style="color: blue;">{} comentario{}</span>',
                count,
                's' if count != 1 else ''
            )
        return format_html('<span style="color: gray;">Sin comentarios</span>')
    comments_count_display.short_description = 'Comentarios'
    
    def get_queryset(self, request):
        """Optimiza las consultas del admin"""
        return super().get_queryset(request).select_related('author').prefetch_related('comments')
    
    actions = ['make_published', 'make_unpublished']
    
    def make_published(self, request, queryset):
        """Acción para publicar artículos seleccionados"""
        updated = queryset.update(is_published=True)
        self.message_user(
            request,
            f'{updated} artículo(s) publicado(s) exitosamente.'
        )
    make_published.short_description = 'Publicar artículos seleccionados'
    
    def make_unpublished(self, request, queryset):
        """Acción para despublicar artículos seleccionados"""
        updated = queryset.update(is_published=False)
        self.message_user(
            request,
            f'{updated} artículo(s) despublicado(s) exitosamente.'
        )
    make_unpublished.short_description = 'Despublicar artículos seleccionados'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Configuración del admin para Comment"""
    
    list_display = [
        'content_preview_display',
        'author',
        'article_title',
        'parent_comment_display',
        'created_at',
        'is_edited',
        'replies_count_display'
    ]
    
    list_filter = [
        'created_at',
        'is_edited',
        'article',
        'author',
        ('parent', admin.EmptyFieldListFilter)  # Filtrar por comentarios principales vs respuestas
    ]
    
    search_fields = [
        'content',
        'author__username',
        'author__first_name',
        'author__last_name',
        'article__title'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'replies_count_display',
        'comment_depth_display'
    ]
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('article', 'author', 'content')
        }),
        ('Jerarquía', {
            'fields': ('parent', 'comment_depth_display'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at', 'is_edited', 'replies_count_display'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def content_preview_display(self, obj):
        """Muestra un preview del contenido"""
        preview = obj.content_preview
        if obj.is_reply:
            return format_html(
                '<span style="color: #007bff;">↳ {}</span>',
                preview
            )
        return preview
    content_preview_display.short_description = 'Contenido'
    
    def article_title(self, obj):
        """Muestra el título del artículo con enlace"""
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.article.get_absolute_url(),
            obj.article.title[:50] + ('...' if len(obj.article.title) > 50 else '')
        )
    article_title.short_description = 'Artículo'
    article_title.admin_order_field = 'article__title'
    
    def parent_comment_display(self, obj):
        """Muestra información del comentario padre si existe"""
        if obj.parent:
            return format_html(
                'Respuesta a: <strong>{}</strong>',
                obj.parent.author.username
            )
        return format_html('<span style="color: green;">Comentario principal</span>')
    parent_comment_display.short_description = 'Tipo'
    parent_comment_display.admin_order_field = 'parent'
    
    def replies_count_display(self, obj):
        """Muestra el número de respuestas"""
        count = obj.replies_count
        if count > 0:
            return format_html(
                '<span style="color: blue;">{} respuesta{}</span>',
                count,
                's' if count != 1 else ''
            )
        return format_html('<span style="color: gray;">Sin respuestas</span>')
    replies_count_display.short_description = 'Respuestas'
    
    def comment_depth_display(self, obj):
        """Muestra la profundidad de anidación"""
        depth = obj.get_reply_depth()
        if depth == 0:
            return "Comentario principal"
        return f"Nivel {depth}"
    comment_depth_display.short_description = 'Profundidad'
    
    def get_queryset(self, request):
        """Optimiza las consultas del admin"""
        return super().get_queryset(request).select_related(
            'author', 'article', 'parent__author'
        ).prefetch_related('replies')
    
    actions = ['mark_as_edited', 'mark_as_not_edited']
    
    def mark_as_edited(self, request, queryset):
        """Acción para marcar comentarios como editados"""
        updated = queryset.update(is_edited=True)
        self.message_user(
            request,
            f'{updated} comentario(s) marcado(s) como editado(s).'
        )
    mark_as_edited.short_description = 'Marcar como editados'
    
    def mark_as_not_edited(self, request, queryset):
        """Acción para desmarcar comentarios como editados"""
        updated = queryset.update(is_edited=False)
        self.message_user(
            request,
            f'{updated} comentario(s) desmarcado(s) como editado(s).'
        )
    mark_as_not_edited.short_description = 'Desmarcar como editados'
    
    def get_form(self, request, obj=None, **kwargs):
        """Personaliza el formulario del admin"""
        form = super().get_form(request, obj, **kwargs)
        
        # Si es una respuesta, limitar los comentarios padre disponibles
        if obj and obj.article:
            form.base_fields['parent'].queryset = Comment.objects.filter(
                article=obj.article,
                parent=None  # Solo permitir responder a comentarios principales
            )
        
        return form


# Configuración adicional del admin
admin.site.site_header = "Drift Blog - Panel de Administración"
admin.site.site_title = "Drift Blog Admin"
admin.site.index_title = "Gestión de Contenido"