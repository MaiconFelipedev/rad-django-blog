from django.contrib import admin
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase
from django.urls import reverse

from .admin import PostAdmin
from .forms import PostForm
from .models import Categoria, Post, Tag


class BlogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.python = Categoria.objects.create(nome="Python", slug="python")
        cls.django = Categoria.objects.create(nome="Django", slug="django")
        cls.sem_posts = Categoria.objects.create(
            nome="Sem posts", slug="sem-posts"
        )
        cls.orm = Tag.objects.create(nome="ORM", slug="orm")

        cls.publicado = Post.objects.create(
            titulo="Consultas eficientes com o ORM",
            slug="consultas-eficientes-com-o-orm",
            resumo="Como construir consultas legíveis e eficientes.",
            conteudo="O ORM permite consultar dados com uma API Python expressiva.",
            categoria=cls.python,
            situacao=Post.Situacao.PUBLICADO,
        )
        cls.publicado.tags.add(cls.orm)
        cls.outro_publicado = Post.objects.create(
            titulo="Templates reutilizáveis",
            slug="templates-reutilizaveis",
            conteudo="A herança de templates reduz repetições no HTML.",
            categoria=cls.django,
            situacao=Post.Situacao.PUBLICADO,
        )
        cls.rascunho = Post.objects.create(
            titulo="Conteúdo ainda em revisão",
            slug="conteudo-em-revisao",
            conteudo="Este texto não pode aparecer no site público.",
            categoria=cls.python,
            situacao=Post.Situacao.RASCUNHO,
        )
        cls.rascunho.tags.add(cls.orm)

    def test_lista_exibe_apenas_posts_publicados(self):
        resposta = self.client.get(reverse("artigos:lista"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, self.publicado.titulo)
        self.assertContains(resposta, self.outro_publicado.titulo)
        self.assertNotContains(resposta, self.rascunho.titulo)

    def test_lista_exibe_mensagem_quando_nao_ha_publicacoes(self):
        Post.objects.update(situacao=Post.Situacao.RASCUNHO)
        resposta = self.client.get(reverse("artigos:lista"))
        self.assertContains(resposta, "Nenhum post publicado ainda.")

    def test_detalhe_de_post_publicado(self):
        resposta = self.client.get(self.publicado.get_absolute_url())
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, self.publicado.conteudo)
        self.assertContains(resposta, self.orm.nome)

    def test_detalhe_identifica_post_em_rascunho(self):
        resposta = self.client.get(self.rascunho.get_absolute_url())
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Rascunho")

    def test_slug_inexistente_retorna_404(self):
        resposta = self.client.get(
            reverse("artigos:detalhe", args=["nao-existe"])
        )
        self.assertEqual(resposta.status_code, 404)

    def test_categoria_exibe_somente_seus_posts_publicados(self):
        resposta = self.client.get(
            reverse("artigos:por_categoria", args=[self.python.slug])
        )
        self.assertContains(resposta, self.publicado.titulo)
        self.assertNotContains(resposta, self.outro_publicado.titulo)
        self.assertNotContains(resposta, self.rascunho.titulo)

    def test_categoria_inexistente_retorna_404(self):
        resposta = self.client.get(
            reverse("artigos:por_categoria", args=["nao-existe"])
        )
        self.assertEqual(resposta.status_code, 404)

    def test_categoria_com_posts_nao_pode_ser_excluida(self):
        with self.assertRaises(ProtectedError):
            self.python.delete()

    def test_post_informa_se_esta_publicado(self):
        self.assertTrue(self.publicado.esta_publicado())
        self.assertFalse(self.rascunho.esta_publicado())

    def test_relacionamentos_reversos(self):
        self.assertIn(self.publicado, self.python.posts.all())
        self.assertIn(self.publicado, self.orm.posts.all())

    def test_listagem_por_tag_exibe_somente_publicados(self):
        resposta = self.client.get(
            reverse("artigos:por_tag", args=[self.orm.slug])
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, self.publicado.titulo)
        self.assertNotContains(resposta, self.rascunho.titulo)
        self.assertContains(resposta, "Tag: ORM")

    def test_tag_inexistente_retorna_404(self):
        resposta = self.client.get(
            reverse("artigos:por_tag", args=["nao-existe"])
        )
        self.assertEqual(resposta.status_code, 404)

    def test_rodape_exibe_todas_as_categorias(self):
        resposta = self.client.get(reverse("artigos:lista"))
        self.assertContains(resposta, self.python.nome)
        self.assertContains(resposta, self.django.nome)
        self.assertContains(resposta, self.sem_posts.nome)

    def test_detalhe_exibe_tres_posts_relacionados_sem_o_atual(self):
        for indice in range(4):
            Post.objects.create(
                titulo=f"Relacionado {indice}",
                slug=f"relacionado-{indice}",
                conteudo="Conteúdo relacionado.",
                categoria=self.python,
                situacao=Post.Situacao.PUBLICADO,
            )

        resposta = self.client.get(self.publicado.get_absolute_url())
        relacionados = list(resposta.context["relacionados"])
        self.assertEqual(len(relacionados), 3)
        self.assertNotIn(self.publicado, relacionados)

    def test_imagem_de_capa_aparece_no_cartao(self):
        self.publicado.capa = "capas/capa-teste.png"
        self.publicado.save(update_fields=["capa"])
        resposta = self.client.get(reverse("artigos:lista"))
        self.assertContains(resposta, "/media/capas/capa-teste.png")
        self.assertContains(
            resposta,
            f"Capa de {self.publicado.titulo}",
        )

    def test_parcial_de_tags_e_usado_na_lista_e_no_detalhe(self):
        url_tag = reverse("artigos:por_tag", args=[self.orm.slug])
        resposta_lista = self.client.get(reverse("artigos:lista"))
        resposta_detalhe = self.client.get(self.publicado.get_absolute_url())
        self.assertContains(resposta_lista, url_tag)
        self.assertContains(resposta_detalhe, url_tag)

    def test_admin_exibe_quantidade_de_tags(self):
        post_admin = PostAdmin(Post, admin.site)
        self.assertEqual(post_admin.total_de_tags(self.publicado), 1)
        self.assertIn("total_de_tags", post_admin.list_display)

    def test_lista_e_paginada_em_tres_posts(self):
        for indice in range(2):
            Post.objects.create(
                titulo=f"Publicação paginada {indice}",
                slug=f"publicacao-paginada-{indice}",
                conteudo="Conteúdo de teste.",
                categoria=self.python,
                situacao=Post.Situacao.PUBLICADO,
            )

        primeira = self.client.get(reverse("artigos:lista"))
        segunda = self.client.get(reverse("artigos:lista"), {"pagina": 2})
        self.assertEqual(len(primeira.context["posts"]), 3)
        self.assertEqual(len(segunda.context["posts"]), 1)
        self.assertContains(primeira, "Próxima")
        self.assertContains(segunda, "Anterior")


class FormularioPostTests(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(
            nome="Django",
            slug="django",
        )
        self.tag = Tag.objects.create(nome="Formulários", slug="formularios")

    def dados_validos(self, **alteracoes):
        dados = {
            "titulo": "Formulários seguros no Django",
            "resumo": "Como validar e salvar formulários com segurança.",
            "conteudo": "Conteúdo completo sobre os formulários do Django.",
            "categoria": self.categoria.pk,
            "tags": [self.tag.pk],
            "situacao": Post.Situacao.PUBLICADO,
        }
        dados.update(alteracoes)
        return dados

    def criar_post(self, **alteracoes):
        dados = self.dados_validos(**alteracoes)
        tags = dados.pop("tags")
        dados.pop("categoria")
        post = Post.objects.create(
            slug="post-de-teste",
            categoria=self.categoria,
            **dados,
        )
        post.tags.set(tags)
        return post

    def test_formulario_declara_campos_exigidos_explicitamente(self):
        self.assertEqual(
            PostForm.Meta.fields,
            (
                "titulo",
                "resumo",
                "conteudo",
                "categoria",
                "tags",
                "situacao",
            ),
        )
        self.assertNotIn("slug", PostForm.Meta.fields)
        self.assertEqual(PostForm.Meta.widgets["conteudo"].attrs["rows"], 12)

    def test_criacao_vazia_exibe_erros_e_nao_grava(self):
        resposta = self.client.post(reverse("artigos:criar"), {})
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context["form"].errors)
        self.assertEqual(Post.objects.count(), 0)

    def test_titulo_com_menos_de_dez_caracteres_e_recusado(self):
        resposta = self.client.post(
            reverse("artigos:criar"),
            self.dados_validos(titulo="Curto"),
        )
        self.assertFormError(
            resposta.context["form"],
            "titulo",
            "O título precisa ter pelo menos 10 caracteres.",
        )
        self.assertEqual(Post.objects.count(), 0)

    def test_publicado_sem_resumo_exibe_erro_geral(self):
        resposta = self.client.post(
            reverse("artigos:criar"),
            self.dados_validos(resumo=""),
        )
        self.assertFormError(
            resposta.context["form"],
            None,
            "Um post publicado precisa ter um resumo.",
        )

    def test_campos_permanecem_preenchidos_apos_erro(self):
        resposta = self.client.post(
            reverse("artigos:criar"),
            self.dados_validos(titulo="Curto"),
        )
        self.assertContains(
            resposta,
            "Conteúdo completo sobre os formulários do Django.",
        )
        self.assertEqual(resposta.context["form"]["titulo"].value(), "Curto")

    def test_criacao_valida_redireciona_gera_slug_tags_e_mensagem(self):
        resposta = self.client.post(
            reverse("artigos:criar"),
            self.dados_validos(),
            follow=True,
        )
        post = Post.objects.get()
        self.assertRedirects(resposta, post.get_absolute_url())
        self.assertEqual(post.slug, "formularios-seguros-no-django")
        self.assertEqual(list(post.tags.all()), [self.tag])
        self.assertContains(resposta, "Post criado com sucesso.")
        quantidade = Post.objects.count()
        self.client.get(post.get_absolute_url())
        self.assertEqual(Post.objects.count(), quantidade)

    def test_slug_recebe_sufixo_quando_ja_existe(self):
        self.criar_post()
        primeiro = Post.objects.get()
        primeiro.slug = "formularios-seguros-no-django"
        primeiro.save(update_fields=["slug"])

        self.client.post(reverse("artigos:criar"), self.dados_validos())
        segundo = Post.objects.exclude(pk=primeiro.pk).get()
        self.assertEqual(segundo.slug, "formularios-seguros-no-django-2")

    def test_edicao_usa_mesmo_template_e_traz_dados_preenchidos(self):
        post = self.criar_post()
        resposta_criar = self.client.get(reverse("artigos:criar"))
        resposta_editar = self.client.get(
            reverse("artigos:editar", args=[post.slug])
        )
        self.assertTemplateUsed(resposta_criar, "artigos/form_post.html")
        self.assertTemplateUsed(resposta_editar, "artigos/form_post.html")
        self.assertEqual(
            resposta_editar.context["form"]["titulo"].value(),
            post.titulo,
        )

    def test_edicao_altera_o_post_sem_criar_outro(self):
        post = self.criar_post()
        resposta = self.client.post(
            reverse("artigos:editar", args=[post.slug]),
            self.dados_validos(titulo="Formulário de edição atualizado"),
        )
        post.refresh_from_db()
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(post.titulo, "Formulário de edição atualizado")
        self.assertEqual(post.slug, "formulario-de-edicao-atualizado")
        self.assertRedirects(resposta, post.get_absolute_url())

    def test_exclusao_por_get_apenas_exibe_confirmacao(self):
        post = self.criar_post()
        resposta = self.client.get(
            reverse("artigos:excluir", args=[post.slug])
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Confirmar exclusão")
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

    def test_exclusao_por_post_apaga_redireciona_e_exibe_mensagem(self):
        post = self.criar_post()
        resposta = self.client.post(
            reverse("artigos:excluir", args=[post.slug]),
            follow=True,
        )
        self.assertRedirects(resposta, reverse("artigos:lista"))
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())
        self.assertContains(resposta, "foi excluído com sucesso")

    def test_rascunho_pode_ser_criado_mas_nao_aparece_na_lista(self):
        resposta = self.client.post(
            reverse("artigos:criar"),
            self.dados_validos(
                titulo="Rascunho ainda sem resumo",
                resumo="",
                situacao=Post.Situacao.RASCUNHO,
            ),
        )
        post = Post.objects.get()
        self.assertRedirects(resposta, post.get_absolute_url())
        lista = self.client.get(reverse("artigos:lista"))
        self.assertNotContains(lista, post.titulo)

    def test_busca_por_get_lista_apenas_posts_publicados(self):
        publicado = self.criar_post(
            titulo="Consultas com formulários Django",
            conteudo="Um termo especial aparece neste conteúdo.",
        )
        rascunho = Post.objects.create(
            titulo="Termo especial em rascunho",
            slug="termo-especial-em-rascunho",
            conteudo="Não pode aparecer na busca.",
            categoria=self.categoria,
            situacao=Post.Situacao.RASCUNHO,
        )
        resposta = self.client.get(
            reverse("artigos:busca"),
            {"termo": "especial"},
        )
        self.assertContains(resposta, publicado.titulo)
        self.assertNotContains(resposta, rascunho.titulo)

    def test_busca_sem_resultado_exibe_mensagem(self):
        resposta = self.client.get(
            reverse("artigos:busca"),
            {"termo": "inexistente"},
        )
        self.assertContains(
            resposta,
            "Nenhum post publicado foi encontrado.",
        )

    def test_post_sem_token_csrf_retorna_403(self):
        cliente = Client(enforce_csrf_checks=True)
        resposta = cliente.post(
            reverse("artigos:criar"),
            self.dados_validos(),
        )
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(Post.objects.count(), 0)
