import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def configurar_banco():
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # --- Adiciona a coluna 'codigo' à tabela de colaboradores se não existir ---
    try:
        cursor.execute("ALTER TABLE colaboradores ADD COLUMN codigo TEXT")
        print("Coluna 'codigo' adicionada com sucesso à tabela 'colaboradores'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Coluna 'codigo' já existe em 'colaboradores'. Nenhuma alteração necessária.")
        else:
            raise e

    # --- Criação das tabelas (garante que todas existam) ---
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (...)''') # Omitido para brevidade
    # ... (outras tabelas) ...

    conn.commit()
    conn.close()
    print("Banco de dados 'inventario.db' verificado e atualizado.")

if __name__ == '__main__':
    # Código completo para garantir a execução correta
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    try:
        cursor.execute("ALTER TABLE colaboradores ADD COLUMN codigo TEXT")
    except: pass
    cursor.execute('''CREATE TABLE IF NOT EXISTS status (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_status TEXT NOT NULL UNIQUE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS setores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_setor TEXT NOT NULL UNIQUE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS marcas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_marca TEXT NOT NULL UNIQUE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS modelos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_modelo TEXT NOT NULL, marca_id INTEGER NOT NULL, FOREIGN KEY (marca_id) REFERENCES marcas (id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS colaboradores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_completo TEXT NOT NULL, cpf TEXT NOT NULL UNIQUE, gmail TEXT, setor_id INTEGER, data_cadastro DATE NOT NULL, codigo TEXT, FOREIGN KEY (setor_id) REFERENCES setores (id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS aparelhos (id INTEGER PRIMARY KEY AUTOINCREMENT, numero_serie TEXT NOT NULL UNIQUE, imei1 TEXT, imei2 TEXT, valor REAL, modelo_id INTEGER NOT NULL, status_id INTEGER NOT NULL, data_cadastro DATE NOT NULL, FOREIGN KEY (modelo_id) REFERENCES modelos (id), FOREIGN KEY (status_id) REFERENCES status (id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS historico_movimentacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, data_movimentacao DATETIME NOT NULL, aparelho_id INTEGER NOT NULL, colaborador_id INTEGER, status_id INTEGER NOT NULL, localizacao_atual TEXT, observacoes TEXT, checklist_devolucao TEXT, FOREIGN KEY (aparelho_id) REFERENCES aparelhos (id), FOREIGN KEY (colaborador_id) REFERENCES colaboradores (id), FOREIGN KEY (status_id) REFERENCES status (id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS contas_gmail (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE, senha TEXT, telefone_recuperacao TEXT, email_recuperacao TEXT, setor_id INTEGER, colaborador_id INTEGER, FOREIGN KEY (setor_id) REFERENCES setores (id), FOREIGN KEY (colaborador_id) REFERENCES colaboradores (id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, login TEXT NOT NULL UNIQUE, senha TEXT NOT NULL, cargo TEXT NOT NULL CHECK(cargo IN ('Administrador', 'Editor', 'Leitor')))''')
    conn.commit()
    conn.close()
    print("Banco de dados verificado.")
