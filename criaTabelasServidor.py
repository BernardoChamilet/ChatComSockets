import sqlite3

conexao = sqlite3.connect('servidorOpa.db')
cursor = conexao.cursor()

cursor.execute('''
                CREATE TABLE IF NOT EXISTS codigoUsuarios
                    (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE
                    )
                ''')

cursor.execute('''
                CREATE TABLE IF NOT EXISTS mensagensPendentes
                    (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    originador TEXT,
                    destinatario TEXT,
                    mensagem TEXT,
                    timestamp INTEGER,
                    FOREIGN KEY (originador) REFERENCES codigoUsuarios(codigo) ON DELETE SET NULL,
                    FOREIGN KEY (destinatario) REFERENCES codigoUsuarios(codigo) ON DELETE SET NULL
                    )
                ''')

cursor.execute('''
                CREATE TABLE IF NOT EXISTS grupos
                    (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE
                    )
                ''')

cursor.execute('''
                CREATE TABLE IF NOT EXISTS grupoXusuario
                    (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grupo TEXT,
                    usuario TEXT,
                    FOREIGN KEY (grupo) REFERENCES grupos(codigo) ON DELETE SET NULL,
                    FOREIGN KEY (usuario) REFERENCES codigoUsuarios(codigo) ON DELETE SET NULL
                    )
                ''')

conexao.commit()
conexao.close()