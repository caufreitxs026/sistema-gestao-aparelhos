import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def configurar_banco():
    """
    Verifica e atualiza a estrutura do banco de dados, adicionando novas tabelas/colunas
    se necessário.
    """
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # --- Criação da Tabela de Manutenções ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS manutencoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aparelho_id INTEGER NOT NULL,
            colaborador_id_no_envio INTEGER,
            fornecedor TEXT,
            data_envio DATE NOT NULL,
            defeito_reportado TEXT,
            data_retorno DATE,
            solucao_aplicada TEXT,
            custo_reparo REAL,
            status_manutencao TEXT NOT NULL, -- 'Em Andamento', 'Concluída', 'Sem Reparo'
            FOREIGN KEY (aparelho_id) REFERENCES aparelhos (id),
            FOREIGN KEY (colaborador_id_no_envio) REFERENCES colaboradores (id)
        )
    ''')
    print("Tabela 'manutencoes' verificada/criada com sucesso.")

    # --- Verificação de outras tabelas e colunas (código anterior) ---
    # ... (código omitido para brevidade, mas o ficheiro completo deve contê-lo) ...

    conn.commit()
    conn.close()
    print("Banco de dados 'inventario.db' verificado e atualizado.")

if __name__ == '__main__':
    # Código completo para garantir a execução correta
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Adiciona a tabela de manutenções
    cursor.execute('''CREATE TABLE IF NOT EXISTS manutencoes (id INTEGER PRIMARY KEY AUTOINCREMENT, aparelho_id INTEGER NOT NULL, colaborador_id_no_envio INTEGER, fornecedor TEXT, data_envio DATE NOT NULL, defeito_reportado TEXT, data_retorno DATE, solucao_aplicada TEXT, custo_reparo REAL, status_manutencao TEXT NOT NULL, FOREIGN KEY (aparelho_id) REFERENCES aparelhos (id), FOREIGN KEY (colaborador_id_no_envio) REFERENCES colaboradores (id))''')
    
    # Garante que as outras tabelas existam
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
