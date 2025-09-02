from django import forms
from .models import Article, Comment

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


class CommentForm(forms.ModelForm):
    """Formulario para crear y editar comentarios"""
    
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Escribe tu comentario aquí...',
                'rows': 4,
                'maxlength': 1000,
                'style': 'resize: vertical; min-height: 100px;'
            })
        }
        labels = {
            'content': 'Comentario'
        }
        help_texts = {
            'content': 'Comparte tu opinión, experiencia o pregunta (máximo 1000 caracteres)'
        }
    
    def __init__(self, *args, **kwargs):
        # Extraer parámetros personalizados
        self.is_reply = kwargs.pop('is_reply', False)
        self.parent_comment = kwargs.pop('parent_comment', None)
        super().__init__(*args, **kwargs)
        
        # Personalizar placeholder para respuestas
        if self.is_reply and self.parent_comment:
            self.fields['content'].widget.attrs['placeholder'] = f'Responder a {self.parent_comment.author.username}...'
            self.fields['content'].widget.attrs['rows'] = 3
        
        # Agregar validaciones client-side
        self.fields['content'].widget.attrs.update({
            'required': True,
            'minlength': 5
        })
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if content:
            content = content.strip()
            
            # Validación de longitud mínima
            if len(content) < 5:
                raise forms.ValidationError('El comentario debe tener al menos 5 caracteres.')
            
            # Validación de longitud máxima
            if len(content) > 1000:
                raise forms.ValidationError('El comentario no puede exceder 1000 caracteres.')
            
            # Validación básica de spam (palabras repetidas)
            words = content.lower().split()
            if len(words) > 5:
                # Verificar si más del 50% de las palabras son la misma
                word_count = {}
                for word in words:
                    if len(word) > 2:  # Solo palabras de más de 2 caracteres
                        word_count[word] = word_count.get(word, 0) + 1
                
                most_common_count = max(word_count.values()) if word_count else 0
                if most_common_count > len(words) * 0.5:
                    raise forms.ValidationError('El comentario parece ser spam. Por favor, escribe un comentario más variado.')
        
        return content


class CommentReplyForm(CommentForm):
    """Formulario específico para respuestas a comentarios"""
    
    def __init__(self, *args, **kwargs):
        kwargs['is_reply'] = True
        super().__init__(*args, **kwargs)
        
        # Estilo más compacto para respuestas
        self.fields['content'].widget.attrs.update({
            'rows': 3,
            'placeholder': 'Escribe tu respuesta...',
            'style': 'resize: vertical; min-height: 80px;'
        })
        self.fields['content'].help_text = 'Responde de manera constructiva (máximo 1000 caracteres)'


class CommentEditForm(CommentForm):
    """Formulario específico para editar comentarios"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar para edición
        self.fields['content'].widget.attrs.update({
            'placeholder': 'Edita tu comentario...',
        })
        self.fields['content'].help_text = 'Edita tu comentario (máximo 1000 caracteres)'
    
    def save(self, commit=True):
        """Marcar como editado al guardar"""
        comment = super().save(commit=False)
        if commit:
            # Usar skip_edited_flag=False para marcar como editado
            comment.save()
        return comment


class CommentSearchForm(forms.Form):
    """Formulario para buscar comentarios (opcional)"""
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar en comentarios...',
            'aria-label': 'Buscar comentarios'
        })
    )
    
    def clean_search(self):
        search = self.cleaned_data.get('search')
        if search:
            return search.strip()
        return search