from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Categoria, Post, Tag


ITENS_POR_PAGINA = 3


def _paginar(request, queryset):
    return Paginator(queryset, ITENS_POR_PAGINA).get_page(
        request.GET.get("pagina")
    )


def lista(request):
    queryset = (
        Post.objects.filter(situacao=Post.Situacao.PUBLICADO)
        .select_related("categoria")
        .prefetch_related("tags")
    )
    posts = _paginar(request, queryset)
    return render(request, "artigos/lista.html", {"posts": posts})


def detalhe(request, slug):
    post = get_object_or_404(
        Post.objects.select_related("categoria").prefetch_related("tags"),
        slug=slug,
        situacao=Post.Situacao.PUBLICADO,
    )
    relacionados = (
        Post.objects.filter(
            categoria=post.categoria,
            situacao=Post.Situacao.PUBLICADO,
        )
        .exclude(pk=post.pk)
        .select_related("categoria")
        .prefetch_related("tags")[:3]
    )
    return render(
        request,
        "artigos/detalhe.html",
        {"post": post, "relacionados": relacionados},
    )


def por_categoria(request, slug):
    categoria = get_object_or_404(Categoria, slug=slug)
    queryset = (
        categoria.posts.filter(situacao=Post.Situacao.PUBLICADO)
        .select_related("categoria")
        .prefetch_related("tags")
    )
    posts = _paginar(request, queryset)
    contexto = {"posts": posts, "categoria": categoria}
    return render(request, "artigos/lista.html", contexto)


def por_tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    queryset = (
        tag.posts.filter(situacao=Post.Situacao.PUBLICADO)
        .select_related("categoria")
        .prefetch_related("tags")
    )
    posts = _paginar(request, queryset)
    contexto = {"posts": posts, "tag": tag}
    return render(request, "artigos/lista.html", contexto)

# Create your views here.
