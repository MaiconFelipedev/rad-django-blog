from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView

from .forms import BuscaForm, PostForm
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


class PermissaoComLoginMixin(LoginRequiredMixin, PermissionRequiredMixin):
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()


class PostCreateView(
    PermissaoComLoginMixin,
    SuccessMessageMixin,
    CreateView,
):
    model = Post
    form_class = PostForm
    permission_required = "artigos.add_post"
    template_name = "artigos/form_post.html"
    success_message = "Post criado com sucesso."
    extra_context = {
        "titulo_pagina": "Criar post",
        "texto_botao": "Criar post",
    }

    def form_valid(self, form):
        form.instance.autor = self.request.user
        return super().form_valid(form)


@login_required
@permission_required("artigos.change_post", raise_exception=True)
def editar(request, slug):
    post = get_object_or_404(Post, slug=slug, autor=request.user)
    form = PostForm(request.POST or None, instance=post)

    if request.method == "POST" and form.is_valid():
        post = form.save()
        messages.success(request, "Post atualizado com sucesso.")
        return redirect(post)

    contexto = {
        "form": form,
        "post": post,
        "titulo_pagina": "Editar post",
        "texto_botao": "Salvar alterações",
    }
    return render(request, "artigos/form_post.html", contexto)


class PostDeleteView(PermissaoComLoginMixin, DeleteView):
    model = Post
    permission_required = "artigos.delete_post"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "artigos/confirmar_exclusao.html"
    success_url = reverse_lazy("artigos:lista")

    def get_queryset(self):
        return Post.objects.filter(autor=self.request.user)

    def form_valid(self, form):
        messages.success(
            self.request,
            f'O post "{self.object.titulo}" foi excluído com sucesso.',
        )
        return super().form_valid(form)


def busca(request):
    form = BuscaForm(request.GET or None)
    posts = Post.objects.none()
    pesquisou = False

    if form.is_bound and form.is_valid():
        pesquisou = True
        termo = form.cleaned_data["termo"]
        posts = (
            Post.objects.filter(situacao=Post.Situacao.PUBLICADO)
            .filter(Q(titulo__icontains=termo) | Q(conteudo__icontains=termo))
            .select_related("categoria")
            .prefetch_related("tags")
        )

    contexto = {"form": form, "posts": posts, "pesquisou": pesquisou}
    return render(request, "artigos/busca.html", contexto)


@login_required
def meus_posts(request):
    queryset = (
        Post.objects.filter(autor=request.user)
        .select_related("categoria", "autor")
        .prefetch_related("tags")
    )
    posts = _paginar(request, queryset)
    contexto = {"posts": posts, "meus_posts": True}
    return render(request, "artigos/lista.html", contexto)


class CadastroView(CreateView):
    form_class = UserCreationForm
    template_name = "registration/cadastro.html"
    success_url = reverse_lazy("artigos:lista")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("artigos:lista")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        resposta = super().form_valid(form)
        login(self.request, self.object)
        messages.success(
            self.request,
            "Cadastro realizado. Você já está conectado.",
        )
        return resposta

# Create your views here.
