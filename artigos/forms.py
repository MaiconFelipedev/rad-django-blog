from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = (
            "titulo",
            "resumo",
            "conteudo",
            "categoria",
            "tags",
            "situacao",
        )
        widgets = {
            "conteudo": forms.Textarea(attrs={"rows": 12}),
            "resumo": forms.Textarea(attrs={"rows": 3}),
            "tags": forms.CheckboxSelectMultiple(),
        }

    def clean_titulo(self):
        titulo = self.cleaned_data["titulo"].strip()
        if len(titulo) < 10:
            raise ValidationError(
                "O título precisa ter pelo menos 10 caracteres."
            )
        return titulo

    def clean(self):
        dados = super().clean()
        resumo = (dados.get("resumo") or "").strip()
        if (
            dados.get("situacao") == Post.Situacao.PUBLICADO
            and not resumo
        ):
            raise ValidationError(
                "Um post publicado precisa ter um resumo."
            )
        return dados

    def _slug_unico(self, titulo):
        campo_slug = Post._meta.get_field("slug")
        base = slugify(titulo)[: campo_slug.max_length] or "post"
        candidato = base
        numero = 2
        existentes = Post.objects.exclude(pk=self.instance.pk)

        while existentes.filter(slug=candidato).exists():
            sufixo = f"-{numero}"
            candidato = f"{base[: campo_slug.max_length - len(sufixo)]}{sufixo}"
            numero += 1
        return candidato

    def save(self, commit=True):
        post = super().save(commit=False)
        post.slug = self._slug_unico(post.titulo)
        if commit:
            post.save()
            self.save_m2m()
        return post


class BuscaForm(forms.Form):
    termo = forms.CharField(
        label="Termo de busca",
        max_length=200,
        strip=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Buscar nos posts",
                "autocomplete": "off",
            }
        ),
    )
