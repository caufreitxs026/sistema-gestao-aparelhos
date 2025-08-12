import streamlit as st
import sqlite3
import pandas as pd
from auth import show_login_form, hash_password # Importa a função de hash

# --- Autenticação ---
# Se o utilizador não estiver logado, redireciona para a página principal de login
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("app.py")

# Verifica se o usuário é Administrador
if st.session_state.get('user_role') != 'Administrador':
    st.error("Acesso negado. Apenas administradores podem acessar esta página.")
    st.stop()

# --- Configurações da Página ---
st.set_page_config(page_title="Gerenciar Usuários", layout="wide")
st.title("Gerenciamento de Usuários")
st.markdown("---")

# --- Funções do Banco de Dados ---
def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

def adicionar_usuario(nome, login, senha, cargo):
    """Adiciona um novo usuário ao banco de dados."""
    if not all([nome, login, senha, cargo]):
        st.error("Todos os campos são obrigatórios.")
        return
    try:
        conn = get_db_connection()
        senha_hashed = hash_password(senha)
        conn.execute(
            "INSERT INTO usuarios (nome, login, senha, cargo) VALUES (?, ?, ?, ?)",
            (nome, login, senha_hashed, cargo)
        )
        conn.commit()
        conn.close()
        st.success(f"Usuário '{login}' criado com sucesso!")
    except sqlite3.IntegrityError:
        st.error(f"O login '{login}' já existe.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao criar o usuário: {e}")

def carregar_usuarios():
    """Carrega a lista de usuários do banco de dados."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, nome, login, cargo FROM usuarios ORDER BY nome", conn)
    conn.close()
    return df

def atualizar_usuario(user_id, nome, cargo):
    """Atualiza os dados de um usuário existente."""
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE usuarios SET nome = ?, cargo = ? WHERE id = ?",
            (nome, cargo, user_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar o usuário ID {user_id}: {e}")
        return False

# --- Interface do Usuário ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Adicionar Novo Usuário")
    with st.form("form_novo_usuario", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        login = st.text_input("Login de Acesso")
        senha = st.text_input("Senha", type="password")
        cargo = st.selectbox("Cargo/Permissão", ["Administrador", "Editor", "Leitor"])
        
        if st.form_submit_button("Criar Usuário"):
            adicionar_usuario(nome, login, senha, cargo)

with col2:
    # Usando st.expander para criar uma seção que pode ser minimizada
    with st.expander("Ver e Editar Usuários Cadastrados", expanded=True):
        usuarios_df = carregar_usuarios()
        
        # Usando st.data_editor para permitir a edição dos dados
        edited_df = st.data_editor(
            usuarios_df,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "nome": st.column_config.TextColumn("Nome", required=True),
                "login": st.column_config.TextColumn("Login", disabled=True),
                "cargo": st.column_config.SelectboxColumn(
                    "Cargo",
                    options=["Administrador", "Editor", "Leitor"],
                    required=True,
                ),
            },
            hide_index=True,
            num_rows="dynamic", # Permite adicionar e deletar (desativaremos a lógica por enquanto)
            key="usuarios_editor"
        )

        if st.button("Salvar Alterações"):
            # Lógica para comparar o dataframe original com o editado e salvar as mudanças
            for index, row in edited_df.iterrows():
                original_row = usuarios_df.iloc[index]
                if not row.equals(original_row):
                    user_id = row['id']
                    novo_nome = row['nome']
                    novo_cargo = row['cargo']
                    if atualizar_usuario(user_id, novo_nome, novo_cargo):
                        st.toast(f"Usuário '{novo_nome}' atualizado!", icon="✅")
            
            # Recarrega a página para mostrar os dados atualizados
            st.rerun()

