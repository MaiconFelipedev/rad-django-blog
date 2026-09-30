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
