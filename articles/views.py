from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Article
from .forms import ArticleForm, ArticleSearchForm

class ArticleListView(ListView):
    """Vista para listar todos los artículos con búsqueda y paginación"""
    model = Article
    template_name = 'article_list.html'
    context_object_name = 'articles'
    paginate_by = 6
    ordering = ['-date']
    
    def get_queryset(self):
        queryset = Article.objects.published().select_related('author')
        
        # Búsqueda
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(body__icontains=search_query) |
                Q(author__username__icontains=search_query)
            )
        
        # Filtro por autor
        author_filter = self.request.GET.get('author')
        if author_filter:
            queryset = queryset.filter(author__username=author_filter)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ArticleSearchForm(self.request.GET)
        context['current_search'] = self.request.GET.get('search', '')
        context['current_author'] = self.request.GET.get('author', '')
        
        # Estadísticas para la página
        context['total_articles'] = Article.objects.published().count()
        context['total_authors'] = Article.objects.published().values('author').distinct().count()
        
        return context

class ArticleDetailView(DetailView):
    """Vista detallada de un artículo con contador de visualizaciones"""
    model = Article
    template_name = 'article_detail.html'
    context_object_name = 'article'
    
    def get_queryset(self):
        return Article.objects.published().select_related('author')
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # Incrementar contador de visualizaciones solo si no es el autor
        if self.request.user != obj.author:
            obj.increment_views()
            
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Artículos relacionados del mismo autor (excluir el actual)
        context['related_articles'] = Article.objects.published().filter(
            author=self.object.author
        ).exclude(pk=self.object.pk)[:3]
        
        return context

class ArticleCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear nuevos artículos"""
    model = Article
    form_class = ArticleForm
    template_name = 'article_new.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        
        # Auto-generar meta_description si no se proporciona
        if not form.instance.meta_description:
            words = form.instance.body.split()[:25]
            form.instance.meta_description = ' '.join(words) + '...'
        
        messages.success(
            self.request, 
            f'¡Artículo "{form.instance.title}" creado exitosamente!'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request, 
            'Hay errores en el formulario. Por favor, revisa los campos marcados.'
        )
        return super().form_invalid(form)

class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Vista para editar artículos existentes"""
    model = Article
    form_class = ArticleForm
    template_name = 'article_edit.html'
    context_object_name = 'article'

    def test_func(self):
        obj = self.get_object()
        return obj.can_edit(self.request.user)
    
    def handle_no_permission(self):
        messages.error(
            self.request, 
            'No tienes permisos para editar este artículo.'
        )
        return super().handle_no_permission()

    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Artículo "{form.instance.title}" actualizado correctamente.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request, 
            'Hay errores en el formulario. Por favor, revisa los campos marcados.'
        )
        return super().form_invalid(form)

class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Vista para eliminar artículos"""
    model = Article
    template_name = 'article_delete.html'
    success_url = reverse_lazy('article_list')
    context_object_name = 'article'

    def test_func(self):
        obj = self.get_object()
        return obj.can_delete(self.request.user)
    
    def handle_no_permission(self):
        messages.error(
            self.request, 
            'No tienes permisos para eliminar este artículo.'
        )
        return super().handle_no_permission()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        title = self.object.title
        
        # Eliminar imagen asociada si existe
        if self.object.image:
            try:
                if os.path.exists(self.object.image.path):
                    os.remove(self.object.image.path)
            except:
                pass  # Continuar aunque no se pueda eliminar la imagen
        
        messages.success(
            request, 
            f'Artículo "{title}" eliminado correctamente.'
        )
        return super().delete(request, *args, **kwargs)

class AuthorArticlesView(ListView):
    """Vista para mostrar artículos de un autor específico"""
    model = Article
    template_name = 'author_articles.html'
    context_object_name = 'articles'
    paginate_by = 6
    
    def get_queryset(self):
        self.author = get_object_or_404(get_user_model(), username=self.kwargs['username'])
        return Article.objects.published().filter(author=self.author).order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = self.author
        context['total_articles'] = self.get_queryset().count()
        return context

# Vista basada en función para búsqueda AJAX (opcional)
def search_articles_ajax(request):
    """Vista AJAX para búsqueda en tiempo real"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('q', '')
        if query:
            articles = Article.objects.published().filter(
                Q(title__icontains=query) | Q(body__icontains=query)
            )[:5]
            
            results = []
            for article in articles:
                results.append({
                    'id': article.pk,
                    'title': article.title,
                    'url': article.get_absolute_url(),
                    'author': article.author.username,
                    'date': article.date.strftime('%d %b %Y')
                })
            
            return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})