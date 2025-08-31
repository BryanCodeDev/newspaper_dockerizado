from django.contrib import admin
from django.utils.html import format_html
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Configuración del admin para Article"""
    
    list_display = [
        'title', 
        'author', 
        'date', 
        'is_published',
        'views_count',
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
        'reading_time'
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
            'fields': ('views_count', 'date', 'updated'),
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
    
    def get_queryset(self, request):
        """Optimiza las consultas del admin"""
        return super().get_queryset(request).select_related('author')
    
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