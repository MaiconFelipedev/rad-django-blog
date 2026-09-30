from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Categoria(models.Model):
    nome = models.CharField(max_length=60, unique=True, verbose_name="Nome")
    slug = models.SlugField(
        max_length=60,
        unique=True,
        help_text="Identificador usado na URL, sem espaços",
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nome


class Tag(models.Model):
    nome = models.CharField(max_length=40, unique=True, verbose_name="Nome")
    slug = models.SlugField(max_length=40, unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.nome


class Post(models.Model):
    class Situacao(models.TextChoices):
        RASCUNHO = "RA", "Rascunho"
        PUBLICADO = "PU", "Publicado"

    titulo = models.CharField(max_length=200, verbose_name="Título")
    slug = models.SlugField(max_length=200, unique=True)
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="posts",
        verbose_name="Autor",
    )
    resumo = models.CharField(
        max_length=300,
        blank=True,
        help_text="Aparece na listagem. Se vazio, usamos o início do texto.",
    )
    capa = models.ImageField(
        upload_to="capas/",
        blank=True,
        verbose_name="Imagem de capa",
    )
    conteudo = models.TextField(verbose_name="Conteúdo")
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="posts",
        verbose_name="Categoria",
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="posts",
        blank=True,
        verbose_name="Tags",
    )
    situacao = models.CharField(
        max_length=2,
        choices=Situacao.choices,
        default=Situacao.RASCUNHO,
        verbose_name="Situação",
    )
    publicado_em = models.DateTimeField(
        default=timezone.now,
        verbose_name="Publicado em",
    )
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-publicado_em"]
        verbose_name = "Post"
        verbose_name_plural = "Posts"

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("artigos:detalhe", args=[self.slug])

    def esta_publicado(self):
        return self.situacao == self.Situacao.PUBLICADO

# Create your models here.
