from django import forms
from .models import Article

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ('title', 'body', 'image')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del artículo sobre drift...',
                'maxlength': 255
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Comparte tu conocimiento sobre drift, técnicas, configuraciones, experiencias...',
                'rows': 12,
                'style': 'min-height: 300px;'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png,image/gif,image/webp',
                'id': 'id_image'
            })
        }
        labels = {
            'title': 'Título del Artículo',
            'body': 'Contenido',
            'image': 'Imagen Principal'
        }
        help_texts = {
            'title': 'Un título atractivo y descriptivo (máximo 255 caracteres)',
            'body': 'Detalla tu experiencia, técnicas, configuraciones o cualquier información valiosa sobre drift',
            'image': 'Imagen opcional para acompañar tu artículo (JPG, PNG, GIF, WEBP - máx. 5MB)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar validaciones client-side
        self.fields['title'].widget.attrs.update({
            'required': True,
            'minlength': 5
        })
        
        self.fields['body'].widget.attrs.update({
            'required': True,
            'minlength': 50
        })

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title:
            if len(title.strip()) < 5:
                raise forms.ValidationError('El título debe tener al menos 5 caracteres.')
            if Article.objects.filter(title__iexact=title).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('Ya existe un artículo con este título.')
        return title.strip()

    def clean_body(self):
        body = self.cleaned_data.get('body')
        if body:
            if len(body.strip()) < 50:
                raise forms.ValidationError('El contenido debe tener al menos 50 caracteres.')
        return body.strip()

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Validar tamaño (5MB máximo)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('La imagen no puede ser mayor a 5MB.')
            
            # Validar tipo de archivo
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise forms.ValidationError('Formato de imagen no válido. Usa JPG, PNG, GIF o WEBP.')
                
        return image


class ArticleSearchForm(forms.Form):
    """Formulario para búsqueda de artículos"""
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar artículos...',
            'aria-label': 'Buscar artículos'
        })
    )
    
    def clean_search(self):
        search = self.cleaned_data.get('search')
        if search:
            return search.strip()
        return search