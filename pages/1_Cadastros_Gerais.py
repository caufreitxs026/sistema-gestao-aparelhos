import streamlit as st
import pandas as pd
import sqlite3

# --- Autenticação e Permissão ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("app.py")

# Apenas Administradores podem aceder a esta página
if st.session_state.get('user_role') != 'Administrador':
    st.error("Acesso negado. Apenas administradores podem aceder a esta página.")
    st.stop()

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


# --- Configurações da Página ---
st.set_page_config(page_title="Cadastros Gerais", layout="wide")
st.title("Cadastros Gerais")
st.markdown("---")

# --- Funções de Banco de Dados ---

def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Funções para Marcas ---
def carregar_marcas():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, nome_marca FROM marcas ORDER BY nome_marca", conn)
    conn.close()
    return df

def adicionar_marca(nome_marca):
    if not nome_marca:
        st.error("O nome da marca não pode ser vazio.")
        return
    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO marcas (nome_marca) VALUES (?)", (nome_marca,))
        conn.commit()
        conn.close()
        st.success(f"Marca '{nome_marca}' adicionada com sucesso!")
    except sqlite3.IntegrityError:
        st.warning(f"A marca '{nome_marca}' já existe.")

def atualizar_marca(marca_id, nome_marca):
    conn = get_db_connection()
    conn.execute("UPDATE marcas SET nome_marca = ? WHERE id = ?", (nome_marca, marca_id))
    conn.commit()
    conn.close()
    return True

# --- Funções para Modelos ---
def carregar_modelos():
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT m.id, m.nome_modelo, ma.nome_marca 
        FROM modelos m
        JOIN marcas ma ON m.marca_id = ma.id
        ORDER BY ma.nome_marca, m.nome_modelo
    """, conn)
    conn.close()
    return df

def adicionar_modelo(nome_modelo, marca_id):
    if not nome_modelo or not marca_id:
        st.error("O nome do modelo e a marca são obrigatórios.")
        return
    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO modelos (nome_modelo, marca_id) VALUES (?, ?)", (nome_modelo, marca_id))
        conn.commit()
        conn.close()
        st.success(f"Modelo '{nome_modelo}' adicionado com sucesso!")
    except Exception as e:
        st.error(f"Ocorreu um erro ao adicionar o modelo: {e}")

def atualizar_modelo(modelo_id, nome_modelo, marca_id):
    conn = get_db_connection()
    conn.execute("UPDATE modelos SET nome_modelo = ?, marca_id = ? WHERE id = ?", (nome_modelo, marca_id, modelo_id))
    conn.commit()
    conn.close()
    return True

# --- Funções para Setores ---
def carregar_setores():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, nome_setor FROM setores ORDER BY nome_setor", conn)
    conn.close()
    return df

def adicionar_setor(nome_setor):
    if not nome_setor:
        st.error("O nome do setor não pode ser vazio.")
        return
    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO setores (nome_setor) VALUES (?)", (nome_setor,))
        conn.commit()
        conn.close()
        st.success(f"Setor '{nome_setor}' adicionado com sucesso!")
    except sqlite3.IntegrityError:
        st.warning(f"O setor '{nome_setor}' já existe.")

def atualizar_setor(setor_id, nome_setor):
    conn = get_db_connection()
    conn.execute("UPDATE setores SET nome_setor = ? WHERE id = ?", (nome_setor, setor_id))
    conn.commit()
    conn.close()
    return True


# --- Interface do Usuário ---

tab1, tab2 = st.tabs(["Marcas e Modelos", "Setores"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Marcas")
        with st.form("form_nova_marca", clear_on_submit=True):
            novo_nome_marca = st.text_input("Cadastrar nova marca")
            if st.form_submit_button("Adicionar Marca"):
                adicionar_marca(novo_nome_marca)
        
        with st.expander("Ver e Editar Marcas", expanded=True):
            marcas_df = carregar_marcas()
            edited_marcas_df = st.data_editor(marcas_df, key="edit_marcas", hide_index=True, disabled=["id"])
            if st.button("Salvar Alterações de Marcas"):
                for index, row in edited_marcas_df.iterrows():
                    original_row = marcas_df.loc[index]
                    if not row.equals(original_row):
                        if atualizar_marca(row['id'], row['nome_marca']):
                            st.toast(f"Marca '{row['nome_marca']}' atualizada!", icon="✅")
                st.rerun()

    with col2:
        st.subheader("Modelos")
        marcas_df = carregar_marcas()
        marcas_dict = {row['nome_marca']: row['id'] for index, row in marcas_df.iterrows()}

        with st.form("form_novo_modelo", clear_on_submit=True):
            novo_nome_modelo = st.text_input("Cadastrar novo modelo")
            marca_selecionada_nome = st.selectbox("Selecione a Marca", options=marcas_dict.keys())
            if st.form_submit_button("Adicionar Modelo"):
                if marca_selecionada_nome:
                    adicionar_modelo(novo_nome_modelo, marcas_dict[marca_selecionada_nome])

        with st.expander("Ver e Editar Modelos", expanded=True):
            modelos_df = carregar_modelos()
            edited_modelos_df = st.data_editor(
                modelos_df,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "nome_modelo": st.column_config.TextColumn("Modelo", required=True),
                    "nome_marca": st.column_config.SelectboxColumn(
                        "Marca", options=marcas_dict.keys(), required=True
                    )
                },
                hide_index=True, key="edit_modelos"
            )
            if st.button("Salvar Alterações de Modelos"):
                for index, row in edited_modelos_df.iterrows():
                    original_row = modelos_df.loc[index]
                    if not row.equals(original_row):
                        nova_marca_id = marcas_dict[row['nome_marca']]
                        if atualizar_modelo(row['id'], row['nome_modelo'], nova_marca_id):
                            st.toast(f"Modelo '{row['nome_modelo']}' atualizado!", icon="✅")
                st.rerun()


with tab2:
    st.subheader("Setores")
    col1_setor, col2_setor = st.columns(2)
    with col1_setor:
        with st.form("form_novo_setor", clear_on_submit=True):
            novo_nome_setor = st.text_input("Cadastrar novo setor")
            if st.form_submit_button("Adicionar Setor"):
                adicionar_setor(novo_nome_setor)
    
    with col2_setor:
        with st.expander("Ver e Editar Setores", expanded=True):
            setores_df = carregar_setores()
            edited_setores_df = st.data_editor(setores_df, key="edit_setores", hide_index=True, disabled=["id"])
            if st.button("Salvar Alterações de Setores"):
                for index, row in edited_setores_df.iterrows():
                    original_row = setores_df.loc[index]
                    if not row.equals(original_row):
                        if atualizar_setor(row['id'], row['nome_setor']):
                            st.toast(f"Setor '{row['nome_setor']}' atualizado!", icon="✅")
                st.rerun()



