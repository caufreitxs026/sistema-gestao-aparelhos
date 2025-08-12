import sqlite3

def limpar_dados_transacionais():
    """
    Remove todos os registos das tabelas de dados, mantendo as tabelas de
    referência (status, setores, marcas) e a tabela de utilizadores.
    """
    try:
        conn = sqlite3.connect('inventario.db')
        cursor = conn.cursor()

        print("Iniciando a limpeza do banco de dados...")

        # Lista de tabelas a serem limpas
        tabelas_para_limpar = [
            #'historico_movimentacoes',
            #'manutencoes',
            #'aparelhos',
            #'colaboradores',
            #'contas_gmail',
            #'modelos'
        ]

        for tabela in tabelas_para_limpar:
            cursor.execute(f"DELETE FROM {tabela};")
            print(f"Todos os registos da tabela '{tabela}' foram removidos.")

        # Opcional: Se também quiser limpar as tabelas de referência, descomente as linhas abaixo
        # cursor.execute("DELETE FROM marcas;")
        # print("Todos os registos da tabela 'marcas' foram removidos.")
        # cursor.execute("DELETE FROM setores;")
        # print("Todos os registos da tabela 'setores' foram removidos.")

        conn.commit()
        print("\nLimpeza concluída com sucesso!")
        print("A tabela 'usuarios' não foi alterada.")

    except Exception as e:
        print(f"\nOcorreu um erro durante a limpeza: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Confirmação de segurança
    resposta = input("Tem a certeza de que deseja apagar todos os dados de aparelhos, colaboradores, movimentações, etc. (exceto utilizadores)? Esta ação é irreversível. (s/n): ")
    if resposta.lower() == 's':
        limpar_dados_transacionais()
    else:
        print("Operação de limpeza cancelada.")

