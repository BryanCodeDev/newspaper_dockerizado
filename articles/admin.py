from django.contrib import admin
from django.utils.html import format_html
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'date', 'has_image_display')
    list_filter = ('date', 'author')
    search_fields = ('title', 'body')
    readonly_fields = ('date', 'image_preview')
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('title', 'author', 'body')
        }),
        ('Imagen', {
            'fields': ('image', 'image_preview'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('date',),
            'classes': ('collapse',)
        }),
    )
    
    def has_image_display(self, obj):
        """Muestra si el artículo tiene imagen"""
        if obj.has_image:
            return format_html(
                '<span style="color: green;">✓ Sí</span>'
            )
        return format_html(
            '<span style="color: red;">✗ No</span>'
        )
    has_image_display.short_description = 'Tiene Imagen'
    
    def image_preview(self, obj):
        """Muestra una vista previa de la imagen en el admin"""
        if obj.has_image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 200px; border-radius: 8px;" />',
                obj.image.url
            )
        return "No hay imagen"
    image_preview.short_description = 'Vista Previa'