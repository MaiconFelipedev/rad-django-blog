from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase
from django.urls import reverse

from .admin import PostAdmin
from .forms import PostForm
from .models import Categoria, Post, Tag


class BlogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.autor = get_user_model().objects.create_user(
            username="autor_blog",
            password="SenhaForte@2026",
        )
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
            autor=cls.autor,
            categoria=cls.python,
            situacao=Post.Situacao.PUBLICADO,
        )
        cls.publicado.tags.add(cls.orm)
        cls.outro_publicado = Post.objects.create(
            titulo="Templates reutilizáveis",
            slug="templates-reutilizaveis",
            conteudo="A herança de templates reduz repetições no HTML.",
            autor=cls.autor,
            categoria=cls.django,
            situacao=Post.Situacao.PUBLICADO,
        )
        cls.rascunho = Post.objects.create(
            titulo="Conteúdo ainda em revisão",
            slug="conteudo-em-revisao",
            conteudo="Este texto não pode aparecer no site público.",
            autor=cls.autor,
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
                autor=self.autor,
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
                autor=self.autor,
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
        self.usuario = get_user_model().objects.create_user(
            username="autor_formulario",
            password="SenhaForte@2026",
        )
        permissoes = Permission.objects.filter(
            content_type__app_label="artigos",
            codename__in=("add_post", "change_post", "delete_post"),
        )
        self.usuario.user_permissions.add(*permissoes)
        self.client.force_login(self.usuario)
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
            autor=self.usuario,
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
            autor=self.usuario,
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
        cliente.force_login(self.usuario)
        resposta = cliente.post(
            reverse("artigos:criar"),
            self.dados_validos(),
        )
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(Post.objects.count(), 0)


class AutenticacaoAutorizacaoTests(TestCase):
    def setUp(self):
        self.senha = "SenhaForte@2026"
        Usuario = get_user_model()
        self.redator2 = Usuario.objects.create_user(
            username="redator2",
            password=self.senha,
        )
        self.redator3 = Usuario.objects.create_user(
            username="redator3",
            password=self.senha,
        )
        self.editor4 = Usuario.objects.create_user(
            username="editor4",
            password=self.senha,
        )

        permissoes = {
            permissao.codename: permissao
            for permissao in Permission.objects.filter(
                content_type__app_label="artigos",
                codename__in=("add_post", "change_post", "delete_post"),
            )
        }
        self.redatores = Group.objects.create(name="Redatores")
        self.redatores.permissions.set(
            [permissoes["add_post"], permissoes["change_post"]]
        )
        self.editores = Group.objects.create(name="Editores")
        self.editores.permissions.set(permissoes.values())
        self.redator2.groups.add(self.redatores)
        self.redator3.groups.add(self.redatores)
        self.editor4.groups.add(self.editores)

        self.categoria = Categoria.objects.create(
            nome="Segurança",
            slug="seguranca",
        )
        self.post_redator3 = Post.objects.create(
            titulo="Post publicado pelo redator três",
            slug="post-redator-tres",
            resumo="Post usado nos testes de propriedade.",
            conteudo="Somente o autor pode alterar este conteúdo.",
            autor=self.redator3,
            categoria=self.categoria,
            situacao=Post.Situacao.PUBLICADO,
        )
        self.rascunho_redator2 = Post.objects.create(
            titulo="Rascunho privado do redator dois",
            slug="rascunho-redator-dois",
            conteudo="Área de trabalho do redator dois.",
            autor=self.redator2,
            categoria=self.categoria,
            situacao=Post.Situacao.RASCUNHO,
        )

    def dados_post(self, **alteracoes):
        dados = {
            "titulo": "Novo post do usuário redator",
            "resumo": "Resumo válido do novo post.",
            "conteudo": "Conteúdo criado por um usuário autenticado.",
            "categoria": self.categoria.pk,
            "tags": [],
            "situacao": Post.Situacao.PUBLICADO,
        }
        dados.update(alteracoes)
        return dados

    def test_anonimo_ao_criar_e_redirecionado_para_login_com_next(self):
        url = reverse("artigos:criar")
        resposta = self.client.get(url)
        self.assertRedirects(resposta, f"{reverse('login')}?next={url}")

    def test_login_respeita_o_parametro_next(self):
        url = reverse("artigos:criar")
        resposta = self.client.post(
            reverse("login"),
            {
                "username": self.redator2.username,
                "password": self.senha,
                "next": url,
            },
        )
        self.assertRedirects(resposta, url)

    def test_cadastro_publico_e_exibido(self):
        resposta = self.client.get(reverse("artigos:cadastro"))
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "registration/cadastro.html")

    def test_cadastro_recusa_senhas_diferentes(self):
        resposta = self.client.post(
            reverse("artigos:cadastro"),
            {
                "username": "visitante_diferente",
                "password1": "SenhaForte@2026",
                "password2": "OutraSenha@2026",
            },
        )
        self.assertIn("password2", resposta.context["form"].errors)
        self.assertFalse(
            get_user_model().objects.filter(
                username="visitante_diferente"
            ).exists()
        )

    def test_cadastro_recusa_senha_de_quatro_digitos(self):
        resposta = self.client.post(
            reverse("artigos:cadastro"),
            {
                "username": "visitante_fraco",
                "password1": "1234",
                "password2": "1234",
            },
        )
        self.assertIn("password2", resposta.context["form"].errors)

    def test_cadastro_valido_faz_login_sem_conceder_poderes(self):
        resposta = self.client.post(
            reverse("artigos:cadastro"),
            {
                "username": "visitante5",
                "password1": "VisitanteSeguro@2026",
                "password2": "VisitanteSeguro@2026",
            },
            follow=True,
        )
        usuario = get_user_model().objects.get(username="visitante5")
        self.assertRedirects(resposta, reverse("artigos:lista"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), usuario.pk)
        self.assertFalse(usuario.groups.exists())
        self.assertFalse(usuario.user_permissions.exists())
        self.assertFalse(usuario.has_perm("artigos.add_post"))

    def test_usuario_recem_cadastrado_recebe_403_ao_criar(self):
        self.client.post(
            reverse("artigos:cadastro"),
            {
                "username": "visitante_sem_permissao",
                "password1": "VisitanteSeguro@2026",
                "password2": "VisitanteSeguro@2026",
            },
        )
        resposta = self.client.get(reverse("artigos:criar"))
        self.assertEqual(resposta.status_code, 403)

    def test_redator_cria_post_com_autor_preenchido_pela_view(self):
        self.client.force_login(self.redator2)
        resposta = self.client.post(
            reverse("artigos:criar"),
            self.dados_post(),
        )
        post = Post.objects.get(titulo="Novo post do usuário redator")
        self.assertEqual(post.autor, self.redator2)
        self.assertRedirects(resposta, post.get_absolute_url())

    def test_formulario_de_post_nao_expoe_autor(self):
        self.client.force_login(self.redator2)
        resposta = self.client.get(reverse("artigos:criar"))
        self.assertNotIn("autor", resposta.context["form"].fields)

    def test_redator_nao_edita_post_de_outro_autor(self):
        self.client.force_login(self.redator2)
        resposta = self.client.get(
            reverse("artigos:editar", args=[self.post_redator3.slug])
        )
        self.assertEqual(resposta.status_code, 404)

    def test_redator_sem_delete_recebe_403_sem_ir_ao_login(self):
        self.client.force_login(self.redator2)
        resposta = self.client.get(
            reverse("artigos:excluir", args=[self.rascunho_redator2.slug])
        )
        self.assertEqual(resposta.status_code, 403)
        self.assertFalse(resposta.has_header("Location"))

    def test_editor_exclui_apenas_o_proprio_post(self):
        post = Post.objects.create(
            titulo="Post próprio do editor quatro",
            slug="post-editor-quatro",
            conteudo="Conteúdo que será excluído.",
            autor=self.editor4,
            categoria=self.categoria,
            situacao=Post.Situacao.RASCUNHO,
        )
        self.client.force_login(self.editor4)
        resposta = self.client.post(
            reverse("artigos:excluir", args=[post.slug])
        )
        self.assertRedirects(resposta, reverse("artigos:lista"))
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_editor_nao_exclui_post_de_outro_autor(self):
        self.client.force_login(self.editor4)
        resposta = self.client.post(
            reverse("artigos:excluir", args=[self.post_redator3.slug])
        )
        self.assertEqual(resposta.status_code, 404)
        self.assertTrue(
            Post.objects.filter(pk=self.post_redator3.pk).exists()
        )

    def test_logout_exige_post_e_encerra_a_sessao(self):
        self.client.force_login(self.redator2)
        resposta_get = self.client.get(reverse("logout"))
        self.assertEqual(resposta_get.status_code, 405)

        resposta_post = self.client.post(reverse("logout"))
        self.assertRedirects(resposta_post, reverse("artigos:lista"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_meus_posts_exige_login(self):
        url = reverse("artigos:meus_posts")
        resposta = self.client.get(url)
        self.assertRedirects(resposta, f"{reverse('login')}?next={url}")

    def test_meus_posts_inclui_rascunho_proprio_e_exclui_alheios(self):
        self.client.force_login(self.redator2)
        resposta = self.client.get(reverse("artigos:meus_posts"))
        self.assertContains(resposta, self.rascunho_redator2.titulo)
        self.assertNotContains(resposta, self.post_redator3.titulo)

    def test_lista_publica_anonima_nao_exibe_link_de_criacao(self):
        resposta = self.client.get(reverse("artigos:lista"))
        self.assertNotContains(resposta, reverse("artigos:criar"))
        self.assertContains(resposta, reverse("login"))

    def test_redator_nao_ve_acoes_em_post_de_outro_autor(self):
        self.client.force_login(self.redator2)
        resposta = self.client.get(self.post_redator3.get_absolute_url())
        self.assertNotContains(
            resposta,
            reverse("artigos:editar", args=[self.post_redator3.slug]),
        )
        self.assertNotContains(
            resposta,
            reverse("artigos:excluir", args=[self.post_redator3.slug]),
        )

    def test_detalhe_exibe_o_autor(self):
        resposta = self.client.get(self.post_redator3.get_absolute_url())
        self.assertContains(resposta, self.redator3.username)

    def test_autor_e_obrigatorio_protegido_e_tem_relacao_reversa(self):
        campo = Post._meta.get_field("autor")
        self.assertFalse(campo.null)
        self.assertIn(self.post_redator3, self.redator3.posts.all())
        with self.assertRaises(ProtectedError):
            self.redator3.delete()

    def test_grupos_possuem_as_permissoes_planejadas(self):
        self.assertTrue(self.redator2.has_perm("artigos.add_post"))
        self.assertTrue(self.redator2.has_perm("artigos.change_post"))
        self.assertFalse(self.redator2.has_perm("artigos.delete_post"))
        self.assertTrue(self.editor4.has_perm("artigos.delete_post"))

    def test_troca_de_senha_exige_atual_e_mantem_sessao(self):
        self.client.force_login(self.redator2)
        resposta = self.client.post(
            reverse("password_change"),
            {
                "old_password": self.senha,
                "new_password1": "SenhaNovaSegura@2026",
                "new_password2": "SenhaNovaSegura@2026",
            },
        )
        self.assertRedirects(resposta, reverse("password_change_done"))
        self.redator2.refresh_from_db()
        self.assertTrue(self.redator2.check_password("SenhaNovaSegura@2026"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_troca_de_senha_recusa_quatro_digitos(self):
        self.client.force_login(self.redator2)
        resposta = self.client.post(
            reverse("password_change"),
            {
                "old_password": self.senha,
                "new_password1": "1234",
                "new_password2": "1234",
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("new_password2", resposta.context["form"].errors)

    def test_senha_e_armazenada_com_hash_em_quatro_partes(self):
        partes = self.redator2.password.split("$")
        self.assertEqual(len(partes), 4)
        self.assertEqual(partes[0], "pbkdf2_sha256")
        self.assertNotEqual(self.redator2.password, self.senha)
