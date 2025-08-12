import streamlit as st
import sqlite3
from datetime import datetime
import io

# --- Autenticação e Permissão ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("app.py")

if st.session_state.get('user_role') != 'Administrador':
    st.error("Acesso negado. Apenas administradores podem aceder a esta página.")
    st.stop()

# --- Funções de Backup e Restauração ---

def gerar_backup_sql():
    """
    Lê o banco de dados SQLite e gera um script SQL para recriá-lo.
    Retorna o script como uma string.
    """
    try:
        conn = sqlite3.connect('inventario.db')
        script_sql = ""
        for line in conn.iterdump():
            script_sql += f'{line}\n'
        conn.close()
        return script_sql
    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o backup: {e}")
        return None

def restaurar_backup_sql(sql_script):
    """
    Apaga as tabelas existentes e executa um script SQL para restaurar o banco de dados.
    """
    conn = None # Inicializa a variável de conexão
    try:
        # Conecta com um timeout maior para esperar por bloqueios
        conn = sqlite3.connect('inventario.db', timeout=15.0)
        cursor = conn.cursor()
        
        # Pede um bloqueio exclusivo no banco de dados para evitar conflitos
        cursor.execute('BEGIN EXCLUSIVE')
        
        # --- CORREÇÃO: Apagar tabelas existentes antes de restaurar ---
        # 1. Obter a lista de todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # 2. Desativar temporariamente as chaves estrangeiras para permitir apagar
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # 3. Apagar cada tabela
        for table_name in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]}")
        
        # 4. Executa o script SQL completo do backup, que irá recriar tudo
        # O script gerado pelo iterdump já reativa as foreign_keys.
        cursor.executescript(sql_script)
        
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback() # Desfaz quaisquer alterações parciais em caso de erro
        st.error(f"Ocorreu um erro durante a restauração: {e}")
        return False
    finally:
        if conn:
            conn.close()

# --- UI ---
st.title("Backup e Restauração do Sistema")
st.markdown("---")

# --- Secção de Backup ---
st.subheader("1. Gerar Backup do Banco de Dados")
st.warning("Esta ação irá criar uma cópia de segurança de todos os dados do sistema no estado atual. Guarde o ficheiro gerado num local seguro.")

if st.button("Gerar e Preparar Backup para Download"):
    with st.spinner("Gerando script de backup..."):
        backup_script = gerar_backup_sql()
        if backup_script:
            st.session_state['backup_data'] = backup_script
            st.success("Backup gerado com sucesso! Clique no botão abaixo para baixar.")

if 'backup_data' in st.session_state and st.session_state['backup_data']:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    st.download_button(
        label="Baixar Ficheiro de Backup (.sql)",
        data=st.session_state['backup_data'],
        file_name=f"backup_inventario_{timestamp}.sql",
        mime="application/sql"
    )
    st.session_state['backup_data'] = None

st.markdown("---")

# --- Secção de Restauração ---
st.subheader("2. Restaurar Sistema a Partir de um Backup")
st.error("⚠️ **Atenção:** A restauração irá **APAGAR TODOS OS DADOS ATUAIS** e substituí-los pelos dados contidos no ficheiro de backup. Esta ação é irreversível.")

uploaded_file = st.file_uploader("Escolha um ficheiro de backup (.sql) para restaurar", type="sql")

if uploaded_file is not None:
    sql_script_bytes = uploaded_file.getvalue()
    sql_script = sql_script_bytes.decode('utf-8')
    
    st.text_area("Conteúdo do Script (pré-visualização)", sql_script, height=200)

    # Este botão agora apenas define o estado de confirmação e força um rerun.
    if st.button("Iniciar Restauração"):
        st.session_state.confirm_restore = True
        st.rerun()
        
    # Este bloco será executado numa nova execução do script, mostrando a confirmação.
    if st.session_state.get('confirm_restore'):
        st.warning("Tem a certeza absoluta de que deseja continuar? Todos os dados atuais serão perdidos.")
        col1, col2 = st.columns(2)
        if col1.button("Sim, quero restaurar", type="primary"):
            with st.spinner("Restaurando banco de dados... A aplicação será reiniciada."):
                if restaurar_backup_sql(sql_script):
                    st.success("Restauração concluída com sucesso! A aplicação será reiniciada.")
                    st.session_state.confirm_restore = False
                    st.rerun()
                else:
                    st.error("A restauração falhou. Verifique os logs para mais detalhes.")
                    st.session_state.confirm_restore = False
        
        if col2.button("Não, cancelar"):
            st.session_state.confirm_restore = False
            st.rerun()
