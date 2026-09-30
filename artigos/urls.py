from django.urls import path

from . import views

app_name = "artigos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("categoria/<slug:slug>/", views.por_categoria, name="por_categoria"),
    path("tag/<slug:slug>/", views.por_tag, name="por_tag"),
    path("post/<slug:slug>/", views.detalhe, name="detalhe"),
]
