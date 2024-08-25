import socket
import sqlite3
import os
import time

#criarBanco cria um banco para o cliente
def criarBanco(banco,numero):
    conexao = sqlite3.connect(banco)
    cursor = conexao.cursor()
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS contatos
                    (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE,
                    apelido TEXT
                    )
                ''')
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS historico
                (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                originador TEXT,
                destinatario TEXT,
                mensagem TEXT,
                timestamp INTEGER,
                FOREIGN KEY (originador) REFERENCES contatos(codigo) ON DELETE SET NULL,
                FOREIGN KEY (destinatario) REFERENCES contatos(codigo) ON DELETE SET NULL               
                )
                ''')
    cursor.execute("INSERT INTO contatos (codigo, apelido) VALUES (?,?)",(numero,"Meu numero"))
    conexao.commit()
    conexao.close()

#verSeEstaEmContatos verifica se um contato já existe e se não adciona aos contatos
def verSeEstaEmContatos(banco, numero, apelido):
    conexao = sqlite3.connect(banco)
    cursor = conexao.cursor()
    try:
        cursor.execute("INSERT INTO contatos (codigo, apelido) VALUES (?,?)",(numero, apelido))
    except:
        conexao.commit()
        conexao.close()
        return False
    conexao.commit()
    conexao.close()
    return True

#salvarContato verifica se contato já existe, se é válido e adciona novo contato ao banco de dados banco
def salvarContato(banco, numero, apelido):
    #verificando se é válido (consta no sistema)
    mensagem = "19" + numero
    ehValido = falarComServidor(mensagem, '.')
    if ehValido == '0':
        print("Número inválido")
        return False
    #verificando se já existe (consta nos contatos)
    conexao = sqlite3.connect(banco)
    cursor = conexao.cursor()
    try:
        cursor.execute("INSERT INTO contatos (codigo, apelido) VALUES (?,?)",(numero, apelido))
    except:
        print("Contato já existe")
        conexao.commit()
        conexao.close()
        return False
    conexao.commit()
    conexao.close()
    return True

#obterContatos obtem contatos de um cliente
def obterContatos(banco):
    conexao = sqlite3.connect(banco)
    cursor = conexao.cursor()
    cursor.execute("SELECT codigo, apelido FROM contatos")
    c = cursor.fetchall()
    conexao.close()
    return c

#carregarMensagens pega todas as mensagens de um contato do cliente
def carregarMensagens(banco, contato):
    conexao = sqlite3.connect(banco)
    cursor = conexao.cursor()
    cursor.execute("SELECT originador, mensagem, timestamp FROM historico WHERE originador=? or destinatario=? ORDER BY timestamp ASC",(contato, contato))
    m = cursor.fetchall()
    conexao.close()
    return m

#adcionarAoHistorico adciona mensagens recebidas ao historico
def adcionarAoHistorico(mensagem, banco):
    conexao = sqlite3.connect(banco)
    cursor = conexao.cursor()
    src = mensagem[2:15]
    dest = mensagem[15:28]
    t = mensagem[28:38]
    m = mensagem[38::]
    cursor.execute("INSERT INTO historico (originador, destinatario, mensagem, timestamp) VALUES (?, ?, ?, ?) ",(src, dest, m, t))
    conexao.commit()
    conexao.close()
    return True

#falarComServidor envia uma mensagem ao servidor
def falarComServidor(mensagem, banco):
    bancoCliente = banco
    #Endereço do servidor
    HOST = "127.0.0.1"
    #Porta do servidor
    PORT = 5000
    #criando socket TCP(SOCK_STREAM) usando IPV4(AF_INET)
    s =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #Conectando com servidor
    s.connect((HOST, PORT))
    #Enviando dados pro servidor
    print("Conectando com servidor")
    while True:
        try:
            s.sendall(mensagem.encode('utf-8'))
            break
        except:
            #caso a mensagem não chegue dará erro.
            continue
    #Recebendo dados do servidor
    while True:
        dadosRecebidos = s.recv(2048)
        if not dadosRecebidos:
            return
        dadosRecebidos = dadosRecebidos.decode('utf-8')
        #Se foi uma resposta a registro de novo número
        if dadosRecebidos[0:2] == '02':
            s.close()
            #Cria um banco pro cliente guardar seu código e seus contatos
            novoNumero = dadosRecebidos[2::]
            bancoCliente = novoNumero + ".db"
            criarBanco(bancoCliente, novoNumero)
            print(f"{novoNumero} é seu novo número! Registro efetuado com sucesso!")
            return
        #Se foi um recebimento de mensagens pendentes
        elif dadosRecebidos[0:2] == '06':
            if dadosRecebidos == '06':
                return
            #adcionar a lista de contatos com mensagens não lidas o originador da mensagem recebida
            #perceba que somente para mensagens de fato(nao mensagens de confirmação de leitura ou recebimento)
            if dadosRecebidos[38:46] != 'recebida' and dadosRecebidos[38:43] != 'Lidas':
                contatosComMensagensNaoLidas[dadosRecebidos[2:15]] = 1
            #se quem mandou mensagem não estiver nos contatos adcionar
            verSeEstaEmContatos(bancoCliente, dadosRecebidos[2:15], 'Novo')
            #adcionar mensagens recebidas ao histórico
            adcionarAoHistorico(dadosRecebidos, bancoCliente)
            #perceba que aqui não tem return pois podem ser recebidas mais de uma mensagem pendente
        #se foi uma resposte se um numero é válido
        elif dadosRecebidos[0:2] == '20':
            s.close()
            return dadosRecebidos[2::]


contatosComMensagensNaoLidas = {}
while True:
    print("Oi, seja bem vindo! O que gostaria de fazer?")
    print("1. Novo por aqui? Registre-se")
    print("2. Já está registrado? Se conecte!")
    print("3. Sair")
    acao = input()
    #registro de novo cliente
    if acao == '1':
        #dados da mensagem definidos como registro de novo cliente
        mensagem = '01'
        falarComServidor(mensagem, '')
    #login
    elif acao == '2':
        #obtendo numero do cliente
        while True:
            numeroCliente = input("Digite seu número (1234567890123) ou 0 para voltar: ")
            if numeroCliente == "0":
                break
            banco = numeroCliente +'.db'
            if os.path.exists(banco):
                break
            print("Número não existe")
        if numeroCliente != "0":
            while True:
                print("Oi, O que deseja fazer agora?")
                print("1. Adcionar novo contato")
                print("2. Conversar")
                print("3. Criar um grupo")
                print("4. Voltar")
                acao = input()
                #adcionando contato
                if acao == '1':
                    print("Digite 0 a qualquer momento para voltar")
                    numeroContato = input('Digite o numero que deseja adcionar(1234567890123): ')
                    if numeroContato != '0':
                        apelidoContato = input("Digite um apelido (caso não queira aperte enter): ")
                        if apelidoContato != "0":
                            #vendo se numero é válido e se já está em contatos
                            if salvarContato(banco, numeroContato, apelidoContato):
                                print("Contato adcionado com sucesso!")
                #conversando
                elif acao == '2':
                    #vendo se tem mensagens pendentes
                    mensagem = '03'+numeroCliente
                    falarComServidor(mensagem, banco)
                    #contatos é uma lista de tuplas [(codigo, apelido),(codigo,apelido)...]
                    contatos = obterContatos(banco)
                    for c in range(1, len(contatos)):
                        print(f'{c}. '+ contatos[c][1])
                    print("Escolha o contato que quer conversar ou digite 0 para voltar: ")
                    acao = int(input())
                    #se selecionou número inválido
                    if acao >= len(contatos):
                        print("Opcão inválida")
                    elif acao != 0:
                        #vendo se esse contato tem mensagens não lidas
                        if contatos[acao][0] in contatosComMensagensNaoLidas:
                            #confirmar leitura das mensagens desse contato
                            contatosComMensagensNaoLidas.pop(contatos[acao][0])
                            timestamp = (str(time.time()))[0:10]
                            #enviando confirmação de leitura ao servidor
                            mensagem = '05' + numeroCliente + contatos[acao][0] + timestamp + 'Lidas'
                            falarComServidor(mensagem,'')
                        #conversa é uma lista de tuplas [(originador, mensagem, timestamp),(originador, mensagem,timestamp)...]
                        #já estão em ordem de mais antigas para mais novas
                        conversa = carregarMensagens(banco, contatos[acao][0])
                        for c in range(0, len(conversa)):
                            if conversa[c][0] == numeroCliente:
                                print(f"Eu: {conversa[c][1]} enviado em {conversa[c][2]}")
                            else:
                                print(f"{contatos[acao][1]}: {conversa[c][1]} enviado em {conversa[c][2]}")
                        print(f"1. Enviar mensagem a {contatos[acao][1]}")
                        print("2. Voltar")
                        escolha = input()
                        #enviar mensagem ao contato selecionado
                        if escolha == '1':
                            dado = input("Digite a mensagem que quer enviar: ")
                            timestamp = (str(time.time()))[0:10]
                            #montando mensagem
                            mensagem = '05'+numeroCliente+contatos[acao][0]+timestamp+dado
                            adcionarAoHistorico(mensagem, banco)
                            falarComServidor(mensagem, '')
                #Criando grupo
                elif acao == '3':
                    timestamp = (str(time.time()))[0:10]
                    mensagemCriacao = '10'+ timestamp + numeroCliente
                    #7 máximo de membros
                    for i in range(0,7):
                        membro = input("Digite o numero de quem deseja adcionar, 0 para cancelar ou 1 para prosseguir")
                        if membro == '0' or membro == '1':
                            break
                        #verificando se número é válido (consta no sistema)
                        mensagem = "19" + membro
                        ehValido = falarComServidor(mensagem, '')
                        if ehValido == '0':
                            print("Número inválido")
                        else:   
                            mensagemCriacao += membro
                    if membro != '0':
                        #enviando mensagem de criação de grupo ao servidor
                        falarComServidor(mensagemCriacao, '')
                #Voltar
                else:
                    break
    #Sair
    else:
        break