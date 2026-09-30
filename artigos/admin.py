from django.contrib import admin

from .models import Categoria, Post, Tag


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "total_de_posts")
    search_fields = ("nome",)
    prepopulated_fields = {"slug": ("nome",)}

    @admin.display(description="Posts")
    def total_de_posts(self, obj):
        return obj.posts.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug")
    search_fields = ("nome",)
    prepopulated_fields = {"slug": ("nome",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "categoria",
        "situacao",
        "publicado_em",
        "total_de_tags",
    )
    list_filter = ("situacao", "categoria", "tags")
    search_fields = ("titulo", "conteudo")
    date_hierarchy = "publicado_em"
    list_editable = ("situacao",)
    prepopulated_fields = {"slug": ("titulo",)}
    filter_horizontal = ("tags",)
    readonly_fields = ("atualizado_em",)
    fieldsets = (
        (
            "Conteúdo",
            {"fields": ("titulo", "slug", "resumo", "capa", "conteudo")},
        ),
        (
            "Classificação",
            {"fields": ("categoria", "tags")},
        ),
        (
            "Publicação",
            {"fields": ("situacao", "publicado_em", "atualizado_em")},
        ),
    )

    @admin.display(description="Tags")
    def total_de_tags(self, obj):
        return obj.tags.count()


admin.site.site_header = "Blog IFPB — Administração"
admin.site.site_title = "Blog IFPB"
admin.site.index_title = "Publicação de conteúdo"

# Register your models here.
