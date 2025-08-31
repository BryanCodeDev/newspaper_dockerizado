from django.urls import path
from .views import (
    ArticleListView,
    ArticleUpdateView,
    ArticleDetailView,  
    ArticleDeleteView,
    ArticleCreateView,
    AuthorArticlesView,
    search_articles_ajax,
)

app_name = 'articles'

urlpatterns = [
    # Artículos principales
    path('', ArticleListView.as_view(), name='article_list'),
    path('nuevo/', ArticleCreateView.as_view(), name='article_new'),
    path('<int:pk>/', ArticleDetailView.as_view(), name='article_detail'),
    path('<int:pk>/editar/', ArticleUpdateView.as_view(), name='article_edit'),
    path('<int:pk>/eliminar/', ArticleDeleteView.as_view(), name='article_delete'),
    
    # Artículos por autor
    path('autor/<str:username>/', AuthorArticlesView.as_view(), name='author_articles'),
    
    # AJAX endpoints
    path('buscar/', search_articles_ajax, name='search_ajax'),
]