import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from auth import show_login_form

# --- Autenticação ---
# Se o utilizador não estiver logado, redireciona para a página principal de login
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("app.py")

# --- Funções do DB ---
def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

def carregar_setores():
    conn = get_db_connection()
    setores = conn.execute("SELECT id, nome_setor FROM setores ORDER BY nome_setor").fetchall()
    conn.close()
    return setores

def adicionar_colaborador(nome, cpf, gmail, setor_id, codigo):
    if not nome or not cpf or not codigo:
        st.error("Nome, CPF e Código são campos obrigatórios.")
        return
    try:
        conn = get_db_connection()
        data_hoje = date.today()
        conn.execute(
            "INSERT INTO colaboradores (nome_completo, cpf, gmail, setor_id, data_cadastro, codigo) VALUES (?, ?, ?, ?, ?, ?)",
            (nome, cpf, gmail, setor_id, data_hoje, codigo)
        )
        conn.commit()
        conn.close()
        st.success(f"Colaborador '{nome}' adicionado com sucesso!")
    except sqlite3.IntegrityError:
        st.warning("Um colaborador com este CPF ou Código já existe.")
    except Exception as e:
        st.error(f"Erro ao adicionar colaborador: {e}")

def carregar_colaboradores():
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT c.id, c.codigo, c.nome_completo, c.cpf, c.gmail, s.nome_setor
        FROM colaboradores c
        LEFT JOIN setores s ON c.setor_id = s.id
        ORDER BY c.nome_completo
    """, conn)
    conn.close()
    return df

def atualizar_colaborador(col_id, codigo, nome, gmail, setor_id):
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE colaboradores SET codigo = ?, nome_completo = ?, gmail = ?, setor_id = ? WHERE id = ?",
            (codigo, nome, gmail, setor_id, col_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar o colaborador ID {col_id}: {e}")
        return False

# --- UI ---
st.title("Gestão de Colaboradores")
st.markdown("---")

setores_list = carregar_setores()
setores_dict = {s['nome_setor']: s['id'] for s in setores_list}

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Adicionar Novo Colaborador")
    with st.form("form_novo_colaborador", clear_on_submit=True):
        novo_codigo = st.text_input("Código*")
        novo_nome = st.text_input("Nome Completo*")
        novo_cpf = st.text_input("CPF*")
        novo_gmail = st.text_input("Gmail")
        setor_selecionado_nome = st.selectbox("Setor", options=setores_dict.keys())

        if st.form_submit_button("Adicionar Colaborador"):
            setor_id = setores_dict.get(setor_selecionado_nome)
            adicionar_colaborador(novo_nome, novo_cpf, novo_gmail, setor_id, novo_codigo)

with col2:
    with st.expander("Ver e Editar Colaboradores Cadastrados", expanded=True):
        colaboradores_df = carregar_colaboradores()
        setores_options = list(setores_dict.keys())

        edited_df = st.data_editor(
            colaboradores_df,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "codigo": st.column_config.TextColumn("Código", required=True),
                "nome_completo": st.column_config.TextColumn("Nome Completo", required=True),
                "cpf": st.column_config.TextColumn("CPF", disabled=True),
                "gmail": st.column_config.TextColumn("Gmail"),
                "nome_setor": st.column_config.SelectboxColumn(
                    "Setor", options=setores_options, required=True
                ),
            },
            hide_index=True,
            key="colaboradores_editor"
        )
        
        if st.button("Salvar Alterações dos Colaboradores"):
            for index, row in edited_df.iterrows():
                original_row = colaboradores_df.loc[index]
                if not row.equals(original_row):
                    col_id = row['id']
                    novo_codigo = row['codigo']
                    novo_nome = row['nome_completo']
                    novo_gmail = row['gmail']
                    novo_setor_id = setores_dict.get(row['nome_setor'])
                    
                    if atualizar_colaborador(col_id, novo_codigo, novo_nome, novo_gmail, novo_setor_id):
                        st.toast(f"Colaborador '{novo_nome}' atualizado!", icon="✅")
            st.rerun()
