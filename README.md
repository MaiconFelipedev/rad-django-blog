# RAD LAB 03 — Blog IFPB

Projeto Django do Roteiro de Laboratório 03 da disciplina de Rapid Application Development.

## Execução

```powershell
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py carregar_blog
python manage.py runserver
```

Página pública: <http://127.0.0.1:8000/>

Administração: <http://127.0.0.1:8000/admin/>

## Dados demonstrativos

O comando `carregar_blog` cria, de forma idempotente:

- 3 categorias;
- 5 tags;
- 4 posts publicados;
- 2 posts em rascunho.
- imagens de capa demonstrativas.

## Desafios opcionais implementados

- listagem de posts por tag;
- categorias disponíveis no rodapé por meio de context processor;
- três posts relacionados na página de detalhe;
- imagem de capa nos posts;
- parcial reutilizável para tags;
- quantidade de tags no Django Admin;
- paginação das listagens.

## Testes

```powershell
python manage.py test
```
