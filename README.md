# Blog IFPB — RAD LAB 03, 04 e 05

Projeto Django desenvolvido nos Laboratórios 03, 04 e 05 da disciplina de Rapid Application Development.

## Funcionalidades

- listagem e detalhe de posts com templates e parciais reutilizáveis;
- criação e edição pelo mesmo `ModelForm` e pelo mesmo template;
- exclusão com confirmação e processamento exclusivo por `POST`;
- slug automático e único gerado a partir do título;
- validação de título e de resumo para posts publicados;
- mensagens de sucesso após criar, editar e excluir;
- busca por título ou conteúdo usando `GET`;
- rascunhos ausentes da listagem e da busca pública;
- login, logout por `POST` e troca de senha com as views nativas do Django;
- cadastro público com login automático e sem concessão de permissões;
- grupos Redatores e Editores com permissões distintas;
- criação, edição e exclusão protegidas por autenticação e autorização;
- cada autor altera somente os próprios posts;
- página `Meus posts`, incluindo os rascunhos do usuário;
- paginação, filtros por categoria e tag e posts relacionados.

## Execução

```powershell
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py carregar_blog
python manage.py configurar_lab05
python manage.py runserver
```

Página pública: <http://127.0.0.1:8000/>

Administração: <http://127.0.0.1:8000/admin/>

Cadastro público: <http://127.0.0.1:8000/cadastro/>

Login: <http://127.0.0.1:8000/contas/login/>

## Contas locais de demonstração

O comando `configurar_lab05` cria quatro contas para os testes de autorização:

| Usuário | Papel |
| --- | --- |
| `admin_lab05` | Superusuário e acesso ao Admin |
| `redator2` | Cria e edita os próprios posts |
| `redator3` | Cria e edita os próprios posts |
| `editor4` | Cria, edita e exclui os próprios posts |

A senha local inicial é `Laboratorio@2026`. Ela é apenas demonstrativa e não deve ser usada em produção. A quinta conta deve ser criada em `/cadastro/` para comprovar que o cadastro público não concede grupos nem permissões.

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

Os 57 testes automatizados cobrem os critérios de aceitação dos três laboratórios, incluindo CSRF, autenticação, permissões, propriedade dos posts e armazenamento seguro das senhas.
