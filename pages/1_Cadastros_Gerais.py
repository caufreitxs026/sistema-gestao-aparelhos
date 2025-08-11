import streamlit as st
import pandas as pd
import sqlite3
from auth import show_login_form

# --- Verificação de Autenticação ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    show_login_form()
    st.stop()

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
        
        with st.expander("Ver e Editar Marcas"):
            marcas_df = carregar_marcas()
            edited_marcas_df = st.data_editor(marcas_df, key="edit_marcas", hide_index=True, disabled=["id"])
            if st.button("Salvar Alterações de Marcas"):
                # Lógica para salvar alterações
                st.rerun()

    with col2:
        st.subheader("Modelos")
        with st.form("form_novo_modelo", clear_on_submit=True):
            novo_nome_modelo = st.text_input("Cadastrar novo modelo")
            marcas_list = carregar_marcas().to_dict('records')
            marcas_dict = {marca['nome_marca']: marca['id'] for marca in marcas_list}
            marca_selecionada_nome = st.selectbox("Selecione a Marca", options=marcas_dict.keys())
            if st.form_submit_button("Adicionar Modelo"):
                if marca_selecionada_nome:
                    adicionar_modelo(novo_nome_modelo, marcas_dict[marca_selecionada_nome])

        with st.expander("Ver Modelos"):
            modelos_df = carregar_modelos()
            st.dataframe(modelos_df, hide_index=True, use_container_width=True)


with tab2:
    st.subheader("Setores")
    col1_setor, col2_setor = st.columns(2)
    with col1_setor:
        with st.form("form_novo_setor", clear_on_submit=True):
            novo_nome_setor = st.text_input("Cadastrar novo setor")
            if st.form_submit_button("Adicionar Setor"):
                adicionar_setor(novo_nome_setor)
    
    with col2_setor:
        with st.expander("Ver e Editar Setores"):
            setores_df = carregar_setores()
            edited_setores_df = st.data_editor(setores_df, key="edit_setores", hide_index=True, disabled=["id"])
            if st.button("Salvar Alterações de Setores"):
                # Lógica para salvar alterações
                st.rerun()

