import sqlite3

conexao = sqlite3.connect('numeroCliente.db')
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

conexao.commit()
conexao.close()