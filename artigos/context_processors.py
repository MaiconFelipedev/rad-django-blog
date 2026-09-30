from .models import Categoria


def categorias_disponiveis(request):
    return {"categorias_disponiveis": Categoria.objects.all()}
