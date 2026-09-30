# Blog IFPB — RAD LAB 03 e 04

Projeto Django desenvolvido nos Laboratórios 03 e 04 da disciplina de Rapid Application Development.

## Funcionalidades

- listagem e detalhe de posts com templates e parciais reutilizáveis;
- criação e edição pelo mesmo `ModelForm` e pelo mesmo template;
- exclusão com confirmação e processamento exclusivo por `POST`;
- slug automático e único gerado a partir do título;
- validação de título e de resumo para posts publicados;
- mensagens de sucesso após criar, editar e excluir;
- busca por título ou conteúdo usando `GET`;
- rascunhos ausentes da listagem e da busca pública;
- paginação, filtros por categoria e tag e posts relacionados.

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

Os testes automatizados cobrem os critérios de aceitação dos dois laboratórios, incluindo a recusa de requisições `POST` sem token CSRF.
