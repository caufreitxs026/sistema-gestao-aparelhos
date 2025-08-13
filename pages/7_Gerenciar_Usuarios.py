import streamlit as st
import sqlite3
import pandas as pd
from auth import show_login_form, hash_password # Importa a função de hash

# --- Autenticação ---
# Se o utilizador não estiver logado, redireciona para a página principal de login
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("app.py")

# --- NOVO: Configuração de Layout (Header, Footer e CSS) ---
st.markdown("""
<style>
    /* Estilos da Logo */
    .logo-text {
        font-family: 'Courier New', monospace;
        font-size: 28px;
        font-weight: bold;
        padding-top: 20px;
    }
    /* Cor para o tema claro (padrão) */
    .logo-asset { color: #003366; }
    .logo-flow { color: #E30613; }

    /* Cor para o tema escuro (usando media query) */
    @media (prefers-color-scheme: dark) {
        .logo-asset { color: #FFFFFF; }
        .logo-flow { color: #FF4B4B; }
    }

    /* Estilos para o footer na barra lateral */
    .sidebar-footer {
        text-align: center;
        padding-top: 20px;
        padding-bottom: 20px;
    }
    .sidebar-footer a {
        margin-right: 15px;
        text-decoration: none;
    }
    .sidebar-footer img {
        width: 25px;
        height: 25px;
        filter: grayscale(1) opacity(0.5);
        transition: filter 0.3s;
    }
    .sidebar-footer img:hover {
        filter: grayscale(0) opacity(1);
    }
    
    @media (prefers-color-scheme: dark) {
        .sidebar-footer img {
            filter: grayscale(1) opacity(0.6) invert(1);
        }
        .sidebar-footer img:hover {
            filter: opacity(1) invert(1);
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Header (Logo no canto superior esquerdo) ---
st.markdown(
    """
    <div class="logo-text">
        <span class="logo-asset">ASSET</span><span class="logo-flow">FLOW</span>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Barra Lateral (Agora contém informações e o footer) ---
with st.sidebar:
    st.write(f"Bem-vindo, **{st.session_state['user_name']}**!")
    st.write(f"Cargo: **{st.session_state['user_role']}**")
    if st.button("Logout"):
        from auth import logout
        logout()

    # Footer (Ícones agora no fundo da barra lateral)
    st.markdown("---")
    st.markdown(
        f"""
        <div class="sidebar-footer">
            <a href="https://github.com/caufreitxs026" target="_blank" title="GitHub">
                <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/brands/github.svg">
            </a>
            <a href="https://linkedin.com/in/cauafreitas" target="_blank" title="LinkedIn">
                <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/brands/linkedin.svg">
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )


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



