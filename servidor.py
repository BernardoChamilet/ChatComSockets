import socket
import random
import sqlite3
import threading
import time

#gerarNovoNumeroValido gera um número aleatório de 13 digitos que não consta no banco de dados do servidor, o salva e o retorna
def gerarNovoNumeroValido(n):
    if n == 0:
        n = 'codigoUsuarios'
    else:
        n = 'grupos'
    conexao = sqlite3.connect('servidorOpa.db')
    cursor = conexao.cursor()
    while True:
        #gerando numero
        numeroAleatorio = ''.join(random.choices('1234567890',k=13))
        #verificando se existe
        try:
            cursor.execute(f"INSERT INTO {n} (codigo) VALUES (?)",(numeroAleatorio,))
            break        
        except:
            print("Numero já existe, gerando outro...")
    conexao.commit()
    conexao.close()
    return numeroAleatorio

#verificaNumero não é usada no gerar numero pois há uma baixa chance de ao gerar um numero ele já exista
#assim é melhor não fazer uma consulta extra ao banco para melhor desempenho
#verificaNumero verifica se um número consta no banco
def verificaNumero(numero):
    conexao = sqlite3.connect('servidorOpa.db')
    cursor = conexao.cursor()
    cursor.execute("SELECT codigo FROM codigoUsuarios WHERE codigo=?",(numero,))
    resposta = cursor.fetchone()
    conexao.close()
    if resposta != None:
        return True
    return False

#verificandoMensagensPendentes verifica se um numero numero possui mensagens pendentes e as retorna
def verificaMensagensPendentes(numero):
    conexao = sqlite3.connect('servidorOpa.db')
    cursor = conexao.cursor()
    cursor.execute("SELECT id, originador, mensagem, timestamp FROM mensagensPendentes WHERE destinatario=?",(numero,))
    m = cursor.fetchall()
    conexao.close()
    return m

#salvarMensagemPendente salva uma mensagem de um cliente no servidor para ser enviada a outro cliente
def salvarMensagemPendente(mensagem):
    conexao = sqlite3.connect('servidorOpa.db')
    cursor = conexao.cursor()
    src = mensagem[2:15]
    dest = mensagem[15:28]
    t = mensagem[28:38]
    m = mensagem[38::]
    cursor.execute("INSERT INTO mensagensPendentes (originador, destinatario, mensagem, timestamp) VALUES (?, ?, ?, ?) ",(src, dest, m, t))
    conexao.commit()
    conexao.close()
    return True

#deletarMensagemPendente deleta uma mensagem da tabela de mensagens pendentes
def deletarMensagemPendente(id):
    conexao = sqlite3.connect('servidorOpa.db')
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM mensagensPendentes WHERE id=?",(id,))
    conexao.commit()
    conexao.close()
    return(True)

#criarGrupo salva informação de um grupo no banco de dados
def criarGrupo(id, listaMembros):
    conexao = sqlite3.connect('servidorOpa.db')
    cursor = conexao.cursor()
    for i in range(0, len(listaMembros)):
        cursor.execute("INSERT INTO grupoXusuario (grupo, usuario) VALUES (?,?)", (id,listaMembros[i]))
    conexao.commit()
    conexao.close()
    return True

#verificaSeEhGrupo verifica se determinado código de 13 digitos pertence a um grupo
def verificaSeEhGrupo(dest):
    conexao = sqlite3.connect('servidorOpa.db')
    cursor = conexao.cursor()
    cursor.execute("SELECT codigo FROM grupos WHERE codigo=?",(dest,))
    retorno = cursor.fetchone()
    conexao.close()
    if retorno != None:
        return True
    return False

#obterMembrosDoGrupo retorna membros de um grupo de codigo codigo
def obterMembrosDoGrupo(codigo):
    conexao = sqlite3.connect('servidorOpa.db')
    cursor = conexao.cursor()
    cursor.execute("SELECT usuario FROM grupoXusuario WHERE grupo=?",(codigo,))
    membros = cursor.fetchall()
    conexao.close()
    return membros

#lidandoComCliente é o que é executado em cada thread. Ela recebe uma mensagem do cliente e verifica o que fazer.
def lidandoComRequisicao(conexao, enderecoCliente):
    print(f"Conectado com {enderecoCliente}")
    #Recebendo dados do cliente
    mensagem = conexao.recv(2048)
    #Verificando o que fazer
    mensagem = mensagem.decode('utf-8')
    #Registrar novo cliente
    if mensagem == '01':
        mensagem = '02' + gerarNovoNumeroValido(0)
        mensagem = mensagem.encode('utf-8')
        #Enviando dados pro cliente
        while True:
            try:
                print("Numero novo gerado e enviado ao cliente com sucesso")
                conexao.sendall(mensagem)
                conexao.close()
                #encerrando thread
                return
            except:
                continue
    #Cliente conectou = verificar se tem mensagem pendentes
    elif mensagem[0:2] == '03':
        destinatario = mensagem[2::]
        #recebe lista de tuplas [(id, originador, mensagem, timestamp),(id, originador, mensagem, timestamp)]
        mensagensPendentes = verificaMensagensPendentes(destinatario)
        #Nenhuma mensagem pendente
        if len(mensagensPendentes) == 0:
            mensagem = '06'.encode('utf-8')
            while True:
                try:
                    print("Mensagem pendente enviada ao cliente nao tinha")
                    conexao.sendall(mensagem)
                    conexao.close()
                    #encerrando thread
                    return
                except:
                    continue
        #Tem mensagens pendentes
        else:
            #enviando todas
            for t in mensagensPendentes:
                mensagem = '06' + t[1] + destinatario + str(t[3]) + t[2]
                mensagem = mensagem.encode('utf-8')
                while True:
                    try:
                        #se cliente recebeu não dará erro.
                        print("Mensagem pendente enviada ao cliente")
                        conexao.sendall(mensagem)
                        #apagando mensagem pendente do servidor
                        deletarMensagemPendente(t[0])
                        #mandando confirmação de recebimento a quem enviou
                        #perceba que não é necessário confirmar uma mensagem de confirmação
                        if t[2][0:8] != 'recebida' and t[2][0:5] != 'Lidas':
                            timestamp = (str(time.time()))[0:10]
                            #vendo se originador é um grupo para enviar confirmação de recebimento para todos os membros
                            ehGrupo = verificaSeEhGrupo(t[1])
                            if ehGrupo:
                                #obterMembrosDoGrupo retorna [(membro1,),(membro2,),...] 
                                membros = obterMembrosDoGrupo(t[1])
                                for m in range(0, len(membros)):
                                    novaMensagem = '05' + t[1] + membros[m][0] + timestamp + 'recebida' + destinatario
                                    print("Mensagem pendente salva")
                                    salvarMensagemPendente(novaMensagem)
                            else:
                                confirmacao = '05' + destinatario + t[1] + timestamp + 'recebida'
                                salvarMensagemPendente(confirmacao)
                        break
                    except:
                        continue
            conexao.close()
            #encerrando thread
            return
    #Cliente enviou mensagem para outro cliente
    elif mensagem[0:2] == '05':
        #se destinatario estiver na tabela grupos então salvar como mensagem pendente para todos do grupo
        dest = mensagem[15:28]
        ehGrupo = verificaSeEhGrupo(dest)
        if ehGrupo:
            #obterMembrosDoGrupo retorna [(membro1,),(membro2,),...] 
            membros = obterMembrosDoGrupo(dest)
            for m in range(0, len(membros)):
                novaMensagem = '05' + mensagem[15:28] + membros[m][0] + mensagem[28:38] + mensagem[38::] + mensagem[2:15]
                print("Mensagem pendente salva")
                salvarMensagemPendente(novaMensagem)
        else:
            print("Mensagem pendente salva")
            salvarMensagemPendente(mensagem)
        conexao.close()
        #encerrando thread
        return
    #Cliente está criando um grupo
    elif mensagem[0:2] == '10':
        #criando identificador do grupo
        idGrupo = gerarNovoNumeroValido(1)
        timestamp = mensagem[2:12]
        stringMembros = mensagem[12::]
        listaMembros = []
        for i in range(0,len(stringMembros),13):
            listaMembros.append(stringMembros[i:i+13])
        #Salvando grupo no banco de dados
        print("Grupo criado")
        criarGrupo(idGrupo, listaMembros)
        #notificar aos membros do grupo que ele foi criado
        for i in range(0, len(listaMembros)):
            mensagem = '05' + idGrupo + listaMembros[i] + timestamp + stringMembros
            print("Mensagem pendente salva")
            salvarMensagemPendente(mensagem)
        conexao.close()
        #encerrando thread
        return
    #Verificar se um número consta no banco
    elif mensagem[0:2] == '19':
        if verificaNumero(mensagem[2::]):
            mensagem = '201'
        else:
            mensagem = '200'
        mensagem = mensagem.encode('utf-8')
        while True:
            try:
                print("Verificação da validez do número feita com sucesso")
                conexao.sendall(mensagem)
                conexao.close()
                #encerrando thread
                return
            except:
                continue
        
print("Escutando na porta 5000...")
#Endereço IP de loopback
HOST = "127.0.0.1"
#Porta onde o servidor estará escutando 
PORT = 5000
#criando socket TCP(SOCK_STREAM) usando IPV4(AF_INET)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#Vinculando socket com endereço e porta
s.bind((HOST, PORT))
#Escutando
s.listen()
while True:
    #Estabelecendo conexão
    conexao, enderecoCliente = s.accept()
    threadRequisicao = threading.Thread(target=lidandoComRequisicao, args=(conexao, enderecoCliente))
    threadRequisicao.start()
        