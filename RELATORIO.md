# Relatório — RAD LAB 03

## 1. Por que a pasta de templates do app repete o nome do app?

A pasta `artigos/templates/artigos/` utiliza o nome do app como um namespace. O Django procura templates em todos os apps instalados; sem essa repetição, dois apps poderiam possuir um arquivo chamado `lista.html` e causar uma colisão. Com o namespace, o caminho `artigos/lista.html` identifica exatamente qual template deve ser carregado.

## 2. Onde os rascunhos são impedidos de aparecer e por que em dois lugares diferentes?

Na listagem, a view `lista` filtra `situacao=Post.Situacao.PUBLICADO`, impedindo que rascunhos sejam exibidos entre as publicações. Na página individual, a view `detalhe` aplica o mesmo filtro dentro de `get_object_or_404`, fazendo com que o acesso direto ao slug de um rascunho retorne 404. Os dois filtros são necessários porque esconder o item na lista não impediria que alguém digitasse sua URL diretamente.

## 3. Por que `default=timezone.now` não leva parênteses?

Sem parênteses, o campo recebe a função para que o Django a execute quando cada objeto for criado. Se fosse usado `timezone.now()`, a função seria executada durante a importação do arquivo e o resultado daquele momento seria reutilizado como valor padrão.

## 4. Como um mesmo template serve às views `lista` e `por_categoria`?

As duas views renderizam `artigos/lista.html` e fornecem a variável `posts`. A view `por_categoria` também fornece `categoria`. O template verifica `{% if categoria %}`: quando ela existe, apresenta o nome da categoria; quando não existe, apresenta o título geral. Assim, o mesmo arquivo atende aos dois contextos.

## 5. O que faz o botão VER NO SITE aparecer no Admin?

O botão aparece porque o model `Post` implementa o método `get_absolute_url()`. O Django Admin reconhece essa convenção e utiliza a URL retornada pelo método para direcionar o usuário à página pública do objeto.

## Desafios opcionais realizados

1. Foi criada a rota de listagem por tag, reutilizando `artigos/lista.html`.
2. Um context processor disponibiliza todas as categorias no rodapé de todas as páginas.
3. A página de detalhe apresenta até três posts recentes da mesma categoria, sem repetir o post atual.
4. O model `Post` possui imagem de capa, apresentada nos cartões e na página de detalhe.
5. O parcial `_lista_tags.html` é utilizado tanto nos cartões quanto nos detalhes.
6. O Django Admin exibe a quantidade de tags de cada post.
7. As listagens possuem paginação de três posts por página.

---

# Relatório — RAD LAB 04: Formulários no blog

## 1. Estrutura do formulário

O arquivo `artigos/forms.py` contém o `PostForm`, derivado de `ModelForm`, com os campos declarados explicitamente: título, resumo, conteúdo, categoria, tags e situação. O slug não é apresentado ao usuário; ele é criado com `slugify` no momento em que o formulário é salvo. Quando o slug já existe, o sistema acrescenta um sufixo numérico para preservar a restrição de unicidade.

O conteúdo utiliza `Textarea` com 12 linhas, e as tags são exibidas com caixas de seleção. O mesmo formulário e o mesmo template `artigos/form_post.html` são utilizados na criação e na edição.

## 2. Validações personalizadas

A validação de campo foi implementada em `clean_titulo()`. Depois de remover espaços nas extremidades, títulos com menos de 10 caracteres são recusados e o erro aparece junto ao campo.

A validação cruzada foi implementada em `clean()`. Ela consulta os valores por meio de `dados.get()`, pois um campo que falhou anteriormente pode não estar em `cleaned_data`. Quando a situação é Publicado e o resumo está vazio, é levantado um erro geral do formulário. Rascunhos podem ser salvos sem resumo.

## 3. Escolha entre views por função e por classe

A criação usa a class-based view `CreateView`, combinada com `SuccessMessageMixin`. Essa escolha reduz código repetitivo porque o fluxo de exibir, validar, salvar e redirecionar já segue o padrão da classe genérica.

A edição usa uma function-based view para deixar explícito o fluxo canônico de formulário: recuperar o objeto, vincular `request.POST` e `instance`, validar, salvar, registrar a mensagem e redirecionar. Essa implementação também evidencia por que informar `instance=post` é indispensável para alterar o registro existente em vez de criar outro.

A exclusão utiliza `DeleteView`. Requisições `GET` exibem somente a confirmação, enquanto a remoção ocorre exclusivamente após o envio do formulário por `POST`.

## 4. Por que a busca usa GET?

A busca apenas consulta informações e não altera o estado do servidor. Por isso utiliza `GET`: o termo fica visível na URL, a página pode ser atualizada sem reenviar uma operação de escrita e o resultado pode ser favoritado ou compartilhado. O `BuscaForm`, derivado de `forms.Form`, valida o termo, e a consulta combina título e conteúdo com objetos `Q`. Antes da consulta é aplicado o filtro de situação Publicado, mantendo rascunhos fora dos resultados.

## 5. Mensagens e padrão POST/Redirect/GET

Criar, editar e excluir registram mensagens de sucesso pelo framework de mensagens do Django. A exibição fica em `templates/base.html`, portanto funciona em qualquer página sem repetição. Após todo `POST` válido há um redirecionamento. Com o padrão POST/Redirect/GET, atualizar a página seguinte não repete a gravação.

## 6. Teste de segurança CSRF

Foi realizado um `POST` para `/novo/` sem enviar o token CSRF, usando o cliente de testes do Django com a verificação de CSRF ativada.

- Código HTTP recebido: **403**.
- Mensagem exibida: **“Verificação CSRF falhou. Pedido cancelado.”**
- Motivo: a requisição não continha o cookie e o token de segurança esperados pelo `CsrfViewMiddleware`, então o Django recusou a operação antes que os dados chegassem à lógica de gravação.

A tag `{% csrf_token %}` está presente nos formulários finais de criação, edição e exclusão.

## 7. Validação da entrega

Os testes automatizados verificam formulário vazio, título curto, publicação sem resumo, preservação dos campos após erro, criação, geração e colisão de slug, gravação das tags, edição sem duplicação, confirmação e execução da exclusão, mensagens, rascunhos, busca e proteção CSRF. Ao final da implementação, os 33 testes do projeto foram aprovados e o `manage.py check` não encontrou problemas.

---

# Relatório — RAD LAB 05: Autenticação e autorização

## 1. Estratégia para adicionar o autor

O model `Post` recebeu uma `ForeignKey` obrigatória para `settings.AUTH_USER_MODEL`, com `related_name="posts"` e `on_delete=PROTECT`. A relação inversa permite consultar `usuario.posts`, enquanto o `PROTECT` impede a exclusão de usuários que possuem conteúdo e preserva a autoria histórica.

Como o banco já continha posts, a migration foi dividida em três operações. Primeiro, o campo foi acrescentado temporariamente com `null=True`. Depois, uma operação de dados criou ou recuperou o usuário técnico inativo `autor_legado`, com senha inutilizável, e atribuiu a ele todos os registros antigos. Por último, o campo foi alterado para obrigatório. Essa estratégia não depende de um ID existente, preserva todos os posts e funciona também em uma instalação nova.

## 2. Autenticação nativa do Django

As URLs de `django.contrib.auth.urls` foram incluídas sob `/contas/`. Login, logout e troca de senha usam as views nativas; foram escritos somente os templates esperados em `templates/registration/`.

O logout é enviado por formulário `POST` com token CSRF, pois encerra a sessão e altera o estado do servidor. Uma requisição `GET` para a rota de logout recebe HTTP 405. `LOGIN_URL`, `LOGIN_REDIRECT_URL` e `LOGOUT_REDIRECT_URL` foram configurados, e o parâmetro `next` devolve o usuário ao endereço protegido que ele tentou acessar.

## 3. Cadastro público

O cadastro usa `UserCreationForm`, fornecido pelo Django. Ele verifica a confirmação da senha, executa os validadores configurados e grava o hash. Após `form.save()`, a view chama `login()` para iniciar a sessão automaticamente.

O novo usuário não é colocado em grupo e não recebe permissão individual. Assim, pode navegar pelo site, mas uma tentativa de criar post recebe HTTP 403. O autor nunca aparece no `PostForm`; a `PostCreateView` o preenche com `request.user` em `form_valid()`.

## 4. Proteções por mixin e decorador

A criação e a exclusão utilizam `LoginRequiredMixin` e `PermissionRequiredMixin`. O comportamento foi ajustado para redirecionar visitantes anônimos ao login, preservando `next`, mas devolver 403 quando um usuário autenticado não possui a permissão necessária.

A edição utiliza os decoradores `@login_required` e `@permission_required("artigos.change_post", raise_exception=True)`. Dessa forma, a entrega contém exemplos das duas formas de proteção exigidas: mixins em class-based views e decoradores em function-based views.

## 5. Grupos e permissões

Foram definidos os seguintes papéis:

- **Redatores:** `add_post` e `change_post`;
- **Editores:** `add_post`, `change_post` e `delete_post`.

O comando idempotente `configurar_lab05` cria os grupos e as quatro contas administrativas/de teste. A quinta conta é criada pela tela pública e permanece sem grupos e sem permissões, conforme o requisito.

## 6. Propriedade dos posts

Além da permissão sobre o model, edição e exclusão filtram os objetos por `autor=request.user`. Foi escolhida a resposta **404** para tentativas contra posts de outro autor. Essa abordagem não confirma ao usuário indevido que o identificador consultado corresponde a um post existente, reduzindo o vazamento de informação. Já a ausência de uma permissão do model devolve **403**, pois o usuário está autenticado, mas não tem autorização para aquela ação.

## 7. Interface e área do autor

O cabeçalho apresenta entrada e cadastro para visitantes. Para usuários autenticados, mostra o nome, `Meus posts`, troca de senha e logout por `POST`. O link de criação depende de `perms.artigos.add_post`. Os botões de editar e excluir dependem simultaneamente da permissão adequada e da autoria do post.

A rota `/meus-posts/` exige login, filtra por `request.user` e inclui publicados e rascunhos. A lista pública e a busca permanecem abertas e continuam filtrando somente posts publicados. A página de detalhe exibe o nome do autor.

## 8. Teste de segurança A — acesso direto por URL

O usuário `redator2` abriu um post de `redator3`. Os botões de edição e exclusão não foram exibidos. Em seguida, foi acessada diretamente a URL de edição desse post.

- Código HTTP: **404**.
- Tela exibida: página “Página não encontrada”, informando que o conteúdo não existe ou não está disponível para a conta.
- Proteção responsável: a view `editar`, além dos decoradores de autenticação e permissão, chama `get_object_or_404(Post, slug=slug, autor=request.user)`.

O mesmo filtro de proprietário existe em `PostDeleteView.get_queryset()`.

## 9. Teste de segurança B — armazenamento da senha

O campo de senha de `redator2` foi inspecionado no shell e apresentou um valor com o formato:

```text
pbkdf2_sha256$1000000$salt$hash
```

O valor possui quatro partes:

1. `pbkdf2_sha256`: algoritmo usado;
2. `1000000`: quantidade de iterações;
3. `salt`: valor aleatório que faz senhas iguais produzirem resultados diferentes;
4. `hash`: resultado derivado da senha, armazenado no banco.

A senha original não pode ser recuperada porque hash não é criptografia reversível. Durante o login, o Django aplica o mesmo processo à senha informada e compara os resultados. As contas de teste foram criadas com `create_user()` ou `set_password()`; nenhuma senha foi atribuída diretamente ao campo do model.

## 10. Validação da entrega

Os testes automatizados cobrem os 22 critérios de aceitação: redirecionamento com `next`, cadastro e validadores de senha, login automático, ausência de permissões no novo usuário, autoria automática, campo de autor oculto, propriedade por objeto, 403 para falta de permissão, exclusão pelo Editor, logout por POST, área `Meus posts`, interface por permissão, preservação dos posts antigos, troca de senha e hash. Ao final, os **57 testes** foram aprovados, não há migrations pendentes e o `manage.py check` não encontrou problemas.
