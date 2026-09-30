from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from artigos.models import Categoria, Post, Tag


class Command(BaseCommand):
    help = "Cadastra os dados demonstrativos exigidos pelo LAB 03."

    @staticmethod
    def fonte(tamanho):
        candidatos = (
            Path(r"C:\Windows\Fonts\arial.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        )
        for caminho in candidatos:
            if caminho.exists():
                return ImageFont.truetype(str(caminho), tamanho)
        return ImageFont.load_default(size=tamanho)

    @classmethod
    def criar_capa(cls, titulo, cor, caminho):
        imagem = Image.new("RGB", (960, 480), cor)
        desenho = ImageDraw.Draw(imagem)
        fonte_titulo = cls.fonte(44)
        fonte_marca = cls.fonte(24)
        desenho.text((60, 55), "BLOG IFPB", fill="white", font=fonte_marca)

        palavras = titulo.split()
        linhas = []
        linha = []
        for palavra in palavras:
            tentativa = " ".join((*linha, palavra))
            largura = desenho.textbbox(
                (0, 0), tentativa, font=fonte_titulo
            )[2]
            if largura > 820 and linha:
                linhas.append(" ".join(linha))
                linha = [palavra]
            else:
                linha.append(palavra)
        if linha:
            linhas.append(" ".join(linha))

        desenho.multiline_text(
            (60, 170),
            "\n".join(linhas),
            fill="white",
            font=fonte_titulo,
            spacing=12,
        )
        caminho.parent.mkdir(parents=True, exist_ok=True)
        imagem.save(caminho, format="PNG")

    def handle(self, *args, **options):
        categorias = {}
        for nome, slug in (
            ("Python", "python"),
            ("Django", "django"),
            ("Banco de Dados", "banco-de-dados"),
        ):
            categorias[slug], _ = Categoria.objects.update_or_create(
                slug=slug,
                defaults={"nome": nome},
            )

        tags = {}
        for nome, slug in (
            ("ORM", "orm"),
            ("Templates", "templates"),
            ("SQL", "sql"),
            ("Tutorial", "tutorial"),
            ("Django", "django"),
        ):
            tags[slug], _ = Tag.objects.update_or_create(
                slug=slug,
                defaults={"nome": nome},
            )

        agora = timezone.now()
        dados = (
            {
                "titulo": "Primeiros passos com Python para a web",
                "slug": "primeiros-passos-python-web",
                "resumo": "Uma introdução ao uso de Python no desenvolvimento web.",
                "conteudo": "Python oferece uma sintaxe clara e um ecossistema maduro.\n\nCom Django, podemos transformar regras de negócio em aplicações web de forma produtiva.",
                "categoria": categorias["python"],
                "situacao": Post.Situacao.PUBLICADO,
                "publicado_em": agora - timedelta(days=5),
                "tags": ("tutorial", "django"),
                "cor": "#1d4ed8",
            },
            {
                "titulo": "Relacionamentos com o ORM do Django",
                "slug": "relacionamentos-orm-django",
                "resumo": "Entenda ForeignKey, ManyToManyField e consultas reversas.",
                "conteudo": "O ORM representa os relacionamentos do banco por meio dos models.\n\nForeignKey modela um relacionamento de muitos para um, enquanto ManyToManyField cria uma tabela intermediária.",
                "categoria": categorias["django"],
                "situacao": Post.Situacao.PUBLICADO,
                "publicado_em": agora - timedelta(days=4),
                "tags": ("orm", "django"),
                "cor": "#047857",
            },
            {
                "titulo": "Consultas SQL geradas pelo QuerySet",
                "slug": "consultas-sql-queryset",
                "resumo": "Veja como inspecionar o SQL produzido pelas consultas do Django.",
                "conteudo": "Um QuerySet somente consulta o banco quando é avaliado.\n\nA propriedade query permite observar o SQL gerado e compreender os JOINs utilizados.",
                "categoria": categorias["banco-de-dados"],
                "situacao": Post.Situacao.PUBLICADO,
                "publicado_em": agora - timedelta(days=3),
                "tags": ("orm", "sql"),
                "cor": "#7c3aed",
            },
            {
                "titulo": "Herança e parciais nos templates",
                "slug": "heranca-parciais-templates",
                "resumo": "Reutilize layouts e pequenos componentes com a DTL.",
                "conteudo": "A herança de templates concentra o layout comum em um arquivo base.\n\nOs parciais evitam a repetição de componentes, como o cartão de cada publicação.",
                "categoria": categorias["django"],
                "situacao": Post.Situacao.PUBLICADO,
                "publicado_em": agora - timedelta(days=2),
                "tags": ("templates", "tutorial"),
                "cor": "#be123c",
            },
            {
                "titulo": "Paginação de resultados",
                "slug": "paginacao-resultados",
                "resumo": "Rascunho sobre paginação de listas extensas.",
                "conteudo": "Este artigo ainda está sendo revisado e não deve aparecer no site público.",
                "categoria": categorias["django"],
                "situacao": Post.Situacao.RASCUNHO,
                "publicado_em": agora - timedelta(days=1),
                "tags": ("django", "tutorial"),
                "cor": "#b45309",
            },
            {
                "titulo": "Otimização de consultas no banco",
                "slug": "otimizacao-consultas-banco",
                "resumo": "Rascunho sobre select_related e prefetch_related.",
                "conteudo": "Este conteúdo será publicado depois que os exemplos de desempenho forem revisados.",
                "categoria": categorias["banco-de-dados"],
                "situacao": Post.Situacao.RASCUNHO,
                "publicado_em": agora,
                "tags": ("orm", "sql"),
                "cor": "#334155",
            },
        )

        for item in dados:
            valores = item.copy()
            nomes_tags = valores.pop("tags")
            cor = valores.pop("cor")
            post, _ = Post.objects.update_or_create(
                slug=valores["slug"],
                defaults=valores,
            )
            post.tags.set(tags[slug] for slug in nomes_tags)
            nome_capa = f"{post.slug}.png"
            caminho_capa = Path(settings.MEDIA_ROOT) / "capas" / nome_capa
            self.criar_capa(post.titulo, cor, caminho_capa)
            post.capa = f"capas/{nome_capa}"
            post.save(update_fields=["capa"])

        self.stdout.write(
            self.style.SUCCESS(
                "Dados carregados: 3 categorias, 5 tags, 6 posts e capas."
            )
        )
