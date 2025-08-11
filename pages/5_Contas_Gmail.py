import streamlit as st
import pandas as pd
import sqlite3
from auth import show_login_form

# --- Verificação de Autenticação ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    show_login_form()
    st.stop()

# --- Configurações da Página ---
st.set_page_config(page_title="Gestão de Contas Gmail", layout="wide")
st.title("Gestão de Contas Gmail")
st.markdown("---")

# --- Funções do Banco de Dados ---
def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

def carregar_setores_e_colaboradores():
    conn = get_db_connection()
    setores = conn.execute("SELECT id, nome_setor FROM setores ORDER BY nome_setor").fetchall()
    colaboradores = conn.execute("SELECT id, nome_completo FROM colaboradores ORDER BY nome_completo").fetchall()
    conn.close()
    return setores, colaboradores

def adicionar_conta(email, senha, tel_rec, email_rec, setor_id, col_id):
    if not email:
        st.error("O campo E-mail é obrigatório.")
        return
    try:
        conn = get_db_connection()
        # A senha não será hasheada aqui, conforme o design inicial
        conn.execute(
            "INSERT INTO contas_gmail (email, senha, telefone_recuperacao, email_recuperacao, setor_id, colaborador_id) VALUES (?, ?, ?, ?, ?, ?)",
            (email, senha, tel_rec, email_rec, setor_id, col_id)
        )
        conn.commit()
        conn.close()
        st.success(f"Conta '{email}' adicionada com sucesso!")
    except sqlite3.IntegrityError:
        st.warning(f"O e-mail '{email}' já está cadastrado.")
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")

def carregar_contas():
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT 
            cg.id, cg.email, cg.senha, cg.telefone_recuperacao, 
            cg.email_recuperacao, s.nome_setor, c.nome_completo as colaborador
        FROM contas_gmail cg
        LEFT JOIN setores s ON cg.setor_id = s.id
        LEFT JOIN colaboradores c ON cg.colaborador_id = c.id
        ORDER BY cg.email
    """, conn)
    conn.close()
    return df

def atualizar_conta(conta_id, senha, tel_rec, email_rec, setor_id, col_id):
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE contas_gmail SET senha = ?, telefone_recuperacao = ?, email_recuperacao = ?, setor_id = ?, colaborador_id = ? WHERE id = ?",
            (senha, tel_rec, email_rec, setor_id, col_id, conta_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar a conta ID {conta_id}: {e}")
        return False

# --- Interface do Usuário ---
setores_list, colaboradores_list = carregar_setores_e_colaboradores()
setores_dict = {s['nome_setor']: s['id'] for s in setores_list}
colaboradores_dict = {"Nenhum": None}
colaboradores_dict.update({c['nome_completo']: c['id'] for c in colaboradores_list})

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Adicionar Nova Conta")
    with st.form("form_nova_conta", clear_on_submit=True):
        st.warning("Atenção: As senhas são armazenadas em texto plano. Use com cautela.", icon="⚠️")
        email = st.text_input("E-mail/Gmail*")
        senha = st.text_input("Senha", type="password")
        tel_rec = st.text_input("Telefone de Recuperação")
        email_rec = st.text_input("E-mail de Recuperação")
        setor_sel = st.selectbox("Função (Setor)", options=setores_dict.keys())
        col_sel = st.selectbox("Vinculado ao Colaborador", options=colaboradores_dict.keys())

        if st.form_submit_button("Adicionar Conta"):
            setor_id = setores_dict.get(setor_sel)
            col_id = colaboradores_dict.get(col_sel)
            adicionar_conta(email, senha, tel_rec, email_rec, setor_id, col_id)

with col2:
    with st.expander("Ver e Editar Contas Cadastradas", expanded=True):
        contas_df = carregar_contas()
        
        setores_options = list(setores_dict.keys())
        colaboradores_options = list(colaboradores_dict.keys())

        edited_df = st.data_editor(
            contas_df,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "email": st.column_config.TextColumn("E-mail", disabled=True),
                "senha": st.column_config.TextColumn("Senha", help="A senha real não é exibida. Digite uma nova senha aqui para atualizá-la."),
                "telefone_recuperacao": st.column_config.TextColumn("Telefone Recuperação"),
                "email_recuperacao": st.column_config.TextColumn("E-mail Recuperação"),
                "nome_setor": st.column_config.SelectboxColumn("Setor", options=setores_options),
                "colaborador": st.column_config.SelectboxColumn("Colaborador", options=colaboradores_options),
            },
            hide_index=True,
            key="contas_editor"
        )

        if st.button("Salvar Alterações nas Contas"):
            for index, row in edited_df.iterrows():
                original_row = contas_df.loc[index]
                if not row.equals(original_row):
                    conta_id = row['id']
                    nova_senha = row['senha'] if row['senha'] else original_row['senha'] # Mantém a senha antiga se o campo estiver vazio
                    novo_tel = row['telefone_recuperacao']
                    novo_email_rec = row['email_recuperacao']
                    novo_setor_id = setores_dict.get(row['nome_setor'])
                    novo_col_id = colaboradores_dict.get(row['colaborador'])
                    
                    if atualizar_conta(conta_id, nova_senha, novo_tel, novo_email_rec, novo_setor_id, novo_col_id):
                        st.toast(f"Conta '{row['email']}' atualizada!", icon="✅")
            st.rerun()
