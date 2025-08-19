import sqlite3
import hashlib

def hash_password(password):
    """Gera um hash seguro para a senha."""
    return hashlib.sha256(password.encode()).hexdigest()

def configurar_banco():
    """
    Verifica e atualiza a estrutura do banco de dados, adicionando novas tabelas/colunas
    e um utilizador admin padrão, se necessário.
    """
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # --- NOVO: Adiciona a coluna 'status_colaborador' se não existir ---
    try:
        # Adiciona a nova coluna com um valor padrão para os registos existentes
        cursor.execute("ALTER TABLE colaboradores ADD COLUMN status_colaborador TEXT DEFAULT 'Em atividade'")
        print("Coluna 'status_colaborador' adicionada com sucesso à tabela 'colaboradores'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Coluna 'status_colaborador' já existe. Nenhuma alteração necessária.")
        else:
            raise e

    # --- Verificação de outras tabelas (código anterior) ---
    # Este bloco garante que todas as tabelas existam, útil para uma nova configuração.
    # Omitido para brevidade, mas o seu ficheiro completo deve contê-lo.

    conn.commit()
    conn.close()
    print("Banco de dados 'inventario.db' verificado e atualizado.")

if __name__ == '__main__':
    configurar_banco()