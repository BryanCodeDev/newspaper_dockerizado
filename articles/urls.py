from django.urls import path
from .views import (
    ArticleListView,
    ArticleUpdateView,
    ArticleDetailView,  
    ArticleDeleteView,
    ArticleCreateView,
    AuthorArticlesView,
    search_articles_ajax,
    # Vistas de comentarios
    add_comment,
    add_reply,
    edit_comment,
    delete_comment,
    toggle_comment_form,
    CommentListView,
    comment_moderation,
)

app_name = 'articles'

urlpatterns = [
    # Listado principal
    path('', ArticleListView.as_view(), name='article_list'),

    # CRUD de artículos
    path('nuevo/', ArticleCreateView.as_view(), name='article_new'),
    path('<int:pk>/', ArticleDetailView.as_view(), name='article_detail'),
    path('<int:pk>/editar/', ArticleUpdateView.as_view(), name='article_edit'),
    path('<int:pk>/eliminar/', ArticleDeleteView.as_view(), name='article_delete'),

    # Artículos por autor
    path('autor/<str:username>/', AuthorArticlesView.as_view(), name='author_articles'),

    # AJAX
    path('buscar/', search_articles_ajax, name='search_ajax'),
    
    # ================================================
    # URLS DE COMENTARIOS
    # ================================================
    
    # Crear comentario principal
    path('<int:article_pk>/comentar/', add_comment, name='add_comment'),
    
    # Responder a comentario
    path('<int:article_pk>/responder/<int:comment_pk>/', add_reply, name='add_reply'),
    
    # Editar comentario
    path('<int:article_pk>/comentario/<int:comment_pk>/editar/', edit_comment, name='edit_comment'),
    
    # Eliminar comentario
    path('<int:article_pk>/comentario/<int:comment_pk>/eliminar/', delete_comment, name='delete_comment'),
    
    # AJAX para formularios dinámicos
    path('<int:article_pk>/comentario/formulario/', toggle_comment_form, name='toggle_comment_form'),
    path('<int:article_pk>/comentario/<int:comment_pk>/formulario/', toggle_comment_form, name='toggle_reply_form'),
    
    # Gestión de comentarios del usuario
    path('mis-comentarios/', CommentListView.as_view(), name='my_comments'),
    
    # Moderación de comentarios (para autores de artículos)
    path('moderar-comentarios/', comment_moderation, name='comment_moderation'),
]