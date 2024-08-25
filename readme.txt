Requisitos do cliente:
    bibliotecas nativas do python3 (não requer instalação): time, os, sqlite3, socket
Requisitos do servidor:
    bibliotecas nativas do python3 (não requer instalação): time, socket, random, sqlite3, threading
Para melhor visualização das tabelas do banco sqlite recomendo baixar sqlite db bronser em: sqlitebrowser.org/dl/

códigos:

01: registro de novo cliente feito pelo cliente
02: resposta de novo cliente registrado pelo servidor
03: pedido de verificação de mensagens pendentes de cliente ao servidor 
05: envio de mensagem de um cliente para outro cliente (passando pelo servidor)(mensagens de confirmação de recebimento e leitura ou criação de grupo também)
06: envio de mensagem pendente do servidor para um cliente
07: envio de confirmação de recebimento do servidor para o cliente originador
10: solicitaão de criação de grupo feita pelo cliente ao servidor
19: solicitação ao servidor pelo cliente se um número é válido
20: resposta do servidor ao cliente se um número é válido (201 se é Válido e 200 se não é)


Obs: No nosso trabalho o servidor está criando uma thread por requisição e não por cliente portanto houve mudanças na lógica do código 03
Agora o código 03 é uma requisição de verificação de mensagens pedentes ao servidor, que a executa em uma thread. Todas as threads nascem
quando uma requisição é feita e morrem após resposta do servidor, portanto não existem usuários "conectados". Lado negativo são muitas consultas
ao banco de dados no servidor para verificar mensagens pendentes. No caso do whatsapp parece melhor usar uma thread por cliente e não por
requisição. De qualquer modo deu para aprender muito sobre protocolos e em uma próxima vez com certeza iríamos prestar mais atenção nisso
e escolher o método mais adequado.

Mensagens de recebimento e leitura não necessitam de mensagem de recebimento e leitura: para isso foi identificado se o conteúdo de uma
mensagem começa com 'recebida' ou 'lida' para facilitar a exibição no chat. Contudo o certo seria colocar 1 bit fora da mensagem no protocolo da mensagem 
para definir se é um mensagem que requer mensagem de recebimento ou leitura (0 se não requer e 1 se requere). 
Ex: cod(2)src(13)dst(13)timestamp(10)requerCouL(1)data(217)
Isso seria super fácil de modificar e implementar. 