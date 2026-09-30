from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations, models
import django.db.models.deletion


def atribuir_autor_aos_posts(apps, schema_editor):
    Usuario = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    Post = apps.get_model("artigos", "Post")
    autor_legado, _ = Usuario.objects.get_or_create(
        username="autor_legado",
        defaults={
            "password": make_password(None),
            "is_active": False,
        },
    )
    Post.objects.filter(autor__isnull=True).update(autor=autor_legado)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("artigos", "0002_post_capa"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="autor",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="posts",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Autor",
            ),
        ),
        migrations.RunPython(
            atribuir_autor_aos_posts,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="post",
            name="autor",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="posts",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Autor",
            ),
        ),
    ]
