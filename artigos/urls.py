from django.urls import path

from . import views

app_name = "artigos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("cadastro/", views.CadastroView.as_view(), name="cadastro"),
    path("meus-posts/", views.meus_posts, name="meus_posts"),
    path("novo/", views.PostCreateView.as_view(), name="criar"),
    path("busca/", views.busca, name="busca"),
    path("categoria/<slug:slug>/", views.por_categoria, name="por_categoria"),
    path("tag/<slug:slug>/", views.por_tag, name="por_tag"),
    path("post/<slug:slug>/editar/", views.editar, name="editar"),
    path(
        "post/<slug:slug>/excluir/",
        views.PostDeleteView.as_view(),
        name="excluir",
    ),
    path("post/<slug:slug>/", views.detalhe, name="detalhe"),
]
