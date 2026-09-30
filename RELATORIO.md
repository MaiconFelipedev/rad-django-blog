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
