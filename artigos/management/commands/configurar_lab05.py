from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from artigos.models import Post


class Command(BaseCommand):
    help = "Cria grupos e contas demonstrativas da Atividade 05."

    def add_arguments(self, parser):
        parser.add_argument(
            "--senha",
            default="Laboratorio@2026",
            help="Senha aplicada apenas às quatro contas locais de demonstração.",
        )

    def handle(self, *args, **options):
        senha = options["senha"]
        try:
            validate_password(senha)
        except ValidationError as erro:
            raise CommandError("Senha recusada: " + " ".join(erro.messages))

        permissoes = {
            permissao.codename: permissao
            for permissao in Permission.objects.filter(
                content_type__app_label="artigos",
                codename__in=("add_post", "change_post", "delete_post"),
            )
        }
        esperadas = {"add_post", "change_post", "delete_post"}
        if set(permissoes) != esperadas:
            raise CommandError("As permissões do model Post não foram encontradas.")

        redatores, _ = Group.objects.get_or_create(name="Redatores")
        redatores.permissions.set(
            [permissoes["add_post"], permissoes["change_post"]]
        )

        editores, _ = Group.objects.get_or_create(name="Editores")
        editores.permissions.set(
            [
                permissoes["add_post"],
                permissoes["change_post"],
                permissoes["delete_post"],
            ]
        )

        Usuario = get_user_model()
        contas = (
            ("admin_lab05", None, True),
            ("redator2", redatores, False),
            ("redator3", redatores, False),
            ("editor4", editores, False),
        )
        usuarios = {}

        for username, grupo, superusuario in contas:
            usuario, _ = Usuario.objects.get_or_create(username=username)
            usuario.is_active = True
            usuario.is_staff = superusuario
            usuario.is_superuser = superusuario
            usuario.set_password(senha)
            usuario.save()
            usuario.groups.clear()
            usuario.user_permissions.clear()
            if grupo is not None:
                usuario.groups.add(grupo)
            usuarios[username] = usuario

        atribuicoes = {
            "redator2": (
                "primeiros-passos-python-web",
                "paginacao-resultados",
            ),
            "redator3": (
                "relacionamentos-orm-django",
                "heranca-parciais-templates",
            ),
            "editor4": (
                "consultas-sql-queryset",
                "otimizacao-consultas-banco",
            ),
        }
        for username, slugs in atribuicoes.items():
            Post.objects.filter(slug__in=slugs).update(
                autor=usuarios[username]
            )

        self.stdout.write(self.style.SUCCESS("Grupos e contas configurados."))
        self.stdout.write("Usuários: admin_lab05, redator2, redator3 e editor4")
        self.stdout.write(f"Senha local de demonstração: {senha}")
        self.stdout.write(
            "Crie a quinta conta pela tela /cadastro/ para testar o fluxo público."
        )
