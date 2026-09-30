from django.contrib import admin
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from .admin import PostAdmin
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

    def test_detalhe_de_rascunho_retorna_404(self):
        resposta = self.client.get(self.rascunho.get_absolute_url())
        self.assertEqual(resposta.status_code, 404)

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
