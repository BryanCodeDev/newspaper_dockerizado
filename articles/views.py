from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import get_user_model
import os
from .models import Article, Comment
from .forms import ArticleForm, ArticleSearchForm, CommentForm, CommentReplyForm, CommentEditForm

class ArticleListView(ListView):
    """Vista para listar todos los artículos con búsqueda y paginación"""
    model = Article
    template_name = 'article_list.html'
    context_object_name = 'articles'
    paginate_by = 6
    ordering = ['-date']
    
    def get_queryset(self):
        queryset = Article.objects.published().select_related('author').annotate(
            comments_count=Count('comments')
        )
        
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
    """Vista detallada de un artículo con comentarios"""
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
        
        # Comentarios con respuestas anidadas optimizadas
        root_comments = Comment.objects.filter(
            article=self.object,
            parent=None
        ).select_related('author').prefetch_related(
            Prefetch(
                'replies',
                queryset=Comment.objects.select_related('author').order_by('created_at')
            )
        ).order_by('-created_at')
        
        context['comments'] = root_comments
        context['comments_count'] = self.object.total_comments
        
        # Formularios para comentarios
        context['comment_form'] = CommentForm()
        
        # Para manejar formularios de respuesta (se crearán dinámicamente con AJAX)
        if self.request.user.is_authenticated:
            context['reply_form'] = CommentReplyForm()
        
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

# ================================================
# VISTAS PARA COMENTARIOS
# ================================================

@login_required
@csrf_protect
@require_http_methods(["POST"])
def add_comment(request, article_pk):
    """Vista para agregar un comentario a un artículo"""
    article = get_object_or_404(Article, pk=article_pk, is_published=True)
    
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.article = article
        comment.author = request.user
        comment.save(skip_edited_flag=True)  # Primera creación, no marcar como editado
        
        messages.success(request, '¡Comentario agregado exitosamente!')
        return redirect('articles:article_detail', pk=article.pk)
    else:
        # Manejar errores del formulario
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'Error en comentario: {error}')
        return redirect('articles:article_detail', pk=article.pk)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def add_reply(request, article_pk, comment_pk):
    """Vista para agregar una respuesta a un comentario"""
    article = get_object_or_404(Article, pk=article_pk, is_published=True)
    parent_comment = get_object_or_404(Comment, pk=comment_pk, article=article)
    
    # Verificar profundidad máxima de anidación (3 niveles)
    if parent_comment.get_reply_depth() >= 2:
        messages.error(request, 'No se pueden agregar más niveles de respuestas.')
        return redirect('articles:article_detail', pk=article.pk)
    
    form = CommentReplyForm(request.POST, parent_comment=parent_comment)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.article = article
        reply.author = request.user
        reply.parent = parent_comment
        reply.save(skip_edited_flag=True)  # Primera creación, no marcar como editado
        
        messages.success(request, f'¡Respuesta agregada a {parent_comment.author.username}!')
        return redirect('articles:article_detail', pk=article.pk)
    else:
        # Manejar errores del formulario
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'Error en respuesta: {error}')
        return redirect('articles:article_detail', pk=article.pk)


@login_required
def edit_comment(request, article_pk, comment_pk):
    """Vista para editar un comentario"""
    article = get_object_or_404(Article, pk=article_pk, is_published=True)
    comment = get_object_or_404(Comment, pk=comment_pk, article=article)
    
    # Verificar permisos
    if not comment.can_edit(request.user):
        messages.error(request, 'No tienes permisos para editar este comentario.')
        return redirect('articles:article_detail', pk=article.pk)
    
    if request.method == 'POST':
        form = CommentEditForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Comentario actualizado exitosamente.')
            return redirect('articles:article_detail', pk=article.pk)
        else:
            # Manejar errores del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error: {error}')
    else:
        form = CommentEditForm(instance=comment)
    
    context = {
        'article': article,
        'comment': comment,
        'form': form,
        'is_editing': True
    }
    
    return render(request, 'comment_edit.html', context)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def delete_comment(request, article_pk, comment_pk):
    """Vista para eliminar un comentario"""
    article = get_object_or_404(Article, pk=article_pk, is_published=True)
    comment = get_object_or_404(Comment, pk=comment_pk, article=article)
    
    # Verificar permisos
    if not comment.can_delete(request.user):
        messages.error(request, 'No tienes permisos para eliminar este comentario.')
        return redirect('articles:article_detail', pk=article.pk)
    
    # Guardar información antes de eliminar
    comment_author = comment.author.username
    has_replies = comment.replies.exists()
    
    if has_replies:
        # Si tiene respuestas, marcar como eliminado en lugar de borrar
        comment.content = '[Comentario eliminado por el usuario]'
        comment.author = None  # Opcional: mantener el autor o no
        comment.save(skip_edited_flag=True)
        messages.success(request, 'Comentario marcado como eliminado.')
    else:
        # Si no tiene respuestas, eliminar completamente
        comment.delete()
        messages.success(request, 'Comentario eliminado exitosamente.')
    
    return redirect('articles:article_detail', pk=article.pk)


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


@login_required
def toggle_comment_form(request, article_pk, comment_pk=None):
    """Vista AJAX para mostrar/ocultar formularios de comentario"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        article = get_object_or_404(Article, pk=article_pk, is_published=True)
        
        if comment_pk:
            # Formulario de respuesta
            parent_comment = get_object_or_404(Comment, pk=comment_pk, article=article)
            form = CommentReplyForm(parent_comment=parent_comment)
            form_type = 'reply'
        else:
            # Formulario de comentario principal
            form = CommentForm()
            form_type = 'comment'
        
        context = {
            'form': form,
            'article': article,
            'form_type': form_type,
            'parent_comment': parent_comment if comment_pk else None
        }
        
        html = render(request, 'partials/comment_form.html', context).content.decode()
        return JsonResponse({'html': html})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ================================================
# VISTAS ADICIONALES PARA GESTIÓN DE COMENTARIOS
# ================================================

class CommentListView(LoginRequiredMixin, ListView):
    """Vista para listar comentarios del usuario autenticado"""
    model = Comment
    template_name = 'comment_list.html'
    context_object_name = 'comments'
    paginate_by = 10
    
    def get_queryset(self):
        return Comment.objects.filter(
            author=self.request.user
        ).select_related('article', 'parent__author').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_comments'] = self.get_queryset().count()
        context['total_replies'] = self.get_queryset().exclude(parent=None).count()
        return context


@login_required
def comment_moderation(request):
    """Vista para que los autores de artículos moderen comentarios en sus artículos"""
    if request.method == 'POST' and request.user.is_staff:
        comment_id = request.POST.get('comment_id')
        action = request.POST.get('action')
        
        comment = get_object_or_404(Comment, pk=comment_id)
        
        # Solo el autor del artículo o staff pueden moderar
        if comment.article.author != request.user and not request.user.is_staff:
            return HttpResponseForbidden()
        
        if action == 'delete':
            if comment.replies.exists():
                comment.content = '[Comentario eliminado por moderación]'
                comment.save(skip_edited_flag=True)
            else:
                comment.delete()
            messages.success(request, 'Comentario moderado exitosamente.')
        
        return redirect('articles:article_detail', pk=comment.article.pk)
    
    # Mostrar comentarios para moderar
    user_articles = Article.objects.filter(author=request.user)
    comments_to_moderate = Comment.objects.filter(
        article__in=user_articles
    ).exclude(author=request.user).select_related(
        'author', 'article'
    ).order_by('-created_at')[:20]
    
    context = {
        'comments_to_moderate': comments_to_moderate,
        'total_pending': comments_to_moderate.count()
    }
    
    return render(request, 'comment_moderation.html', context)