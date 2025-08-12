import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from auth import show_login_form

# --- Verificação de Autenticação ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("app.py")

# --- Configurações da Página ---
st.set_page_config(page_title="Movimentações", layout="wide")
st.title("Registar Movimentação de Aparelho")
st.markdown("---")

# --- Funções de Banco de Dados ---

def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

def carregar_dados_para_selects():
    """Carrega aparelhos, colaboradores e status para as caixas de seleção."""
    conn = get_db_connection()
    # Carrega apenas aparelhos que não estão "Baixado/Inutilizado"
    aparelhos = conn.execute("""
        SELECT a.id, a.numero_serie, mo.nome_modelo, ma.nome_marca
        FROM aparelhos a
        JOIN modelos mo ON a.modelo_id = mo.id
        JOIN marcas ma ON mo.marca_id = ma.id
        WHERE a.status_id != (SELECT id FROM status WHERE nome_status = 'Baixado/Inutilizado')
        ORDER BY ma.nome_marca, mo.nome_modelo, a.numero_serie
    """).fetchall()

    colaboradores = conn.execute("SELECT id, nome_completo FROM colaboradores ORDER BY nome_completo").fetchall()
    status = conn.execute("SELECT id, nome_status FROM status ORDER BY nome_status").fetchall()
    conn.close()
    return aparelhos, colaboradores, status

def registar_movimentacao(aparelho_id, colaborador_id, novo_status_id, localizacao, observacoes):
    """
    Regista uma nova movimentação no histórico e atualiza o status do aparelho.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    data_hora_agora = datetime.now()

    try:
        cursor.execute("BEGIN TRANSACTION;")

        # 1. Insere o novo registo no histórico
        cursor.execute(
            """
            INSERT INTO historico_movimentacoes (data_movimentacao, aparelho_id, colaborador_id, status_id, localizacao_atual, observacoes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (data_hora_agora, aparelho_id, colaborador_id, novo_status_id, localizacao, observacoes)
        )

        # 2. Atualiza o status atual na tabela principal de aparelhos
        cursor.execute(
            "UPDATE aparelhos SET status_id = ? WHERE id = ?",
            (novo_status_id, aparelho_id)
        )

        conn.commit()
        st.success("Movimentação registada com sucesso!")

    except Exception as e:
        conn.rollback()
        st.error(f"Ocorreu um erro ao registar a movimentação: {e}")
    finally:
        conn.close()

def carregar_historico_completo():
    """Carrega o histórico completo de movimentações para exibição."""
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT 
            h.id,
            h.data_movimentacao,
            a.numero_serie,
            mo.nome_modelo,
            c.nome_completo as colaborador,
            s.nome_status,
            h.localizacao_atual,
            h.observacoes
        FROM historico_movimentacoes h
        JOIN aparelhos a ON h.aparelho_id = a.id
        JOIN status s ON h.status_id = s.id
        LEFT JOIN colaboradores c ON h.colaborador_id = c.id
        LEFT JOIN modelos mo ON a.modelo_id = mo.id
        ORDER BY h.data_movimentacao DESC
    """, conn)
    conn.close()
    return df

# --- Interface do Usuário ---

aparelhos_list, colaboradores_list, status_list = carregar_dados_para_selects()

st.subheader("Formulário de Movimentação")

with st.form("form_movimentacao", clear_on_submit=True):
    # --- Pesquisa e seleção de Aparelho ---
    filtro_aparelho = st.text_input("Pesquisar Aparelho (por N/S, marca ou modelo)")
    aparelhos_dict = {f"{ap['nome_marca']} {ap['nome_modelo']} (S/N: {ap['numero_serie']})": ap['id'] for ap in aparelhos_list}
    opcoes_aparelho_filtradas = {k: v for k, v in aparelhos_dict.items() if filtro_aparelho.lower() in k.lower()}
    aparelho_selecionado_str = st.selectbox("Selecione o Aparelho*", options=opcoes_aparelho_filtradas.keys())

    # --- Seleção de Colaborador (sem campo de pesquisa extra) ---
    colaboradores_dict = {col['nome_completo']: col['id'] for col in colaboradores_list}
    opcoes_colaborador_com_nenhum = {"Nenhum": None}
    opcoes_colaborador_com_nenhum.update(colaboradores_dict)
    
    colaborador_selecionado_str = st.selectbox(
        "Atribuir ao Colaborador",
        options=opcoes_colaborador_com_nenhum.keys(),
        help="Clique na lista e comece a digitar para pesquisar um colaborador."
    )
    
    # --- Outros campos ---
    status_dict = {s['nome_status']: s['id'] for s in status_list}
    novo_status_str = st.selectbox("Novo Status do Aparelho*", options=status_dict.keys())
    nova_localizacao = st.text_input("Nova Localização", placeholder="Ex: Mesa do colaborador, Assistência Técnica XYZ")
    observacoes = st.text_area("Observações", placeholder="Ex: Devolução com tela trincada, Envio para troca de bateria.")

    submitted = st.form_submit_button("Registar Movimentação")
    if submitted:
        if not aparelho_selecionado_str or not novo_status_str:
            st.error("Aparelho e Novo Status são campos obrigatórios.")
        else:
            aparelho_id = opcoes_aparelho_filtradas[aparelho_selecionado_str]
            colaborador_id = opcoes_colaborador_com_nenhum[colaborador_selecionado_str]
            novo_status_id = status_dict[novo_status_str]
            registar_movimentacao(aparelho_id, colaborador_id, novo_status_id, nova_localizacao, observacoes)

st.markdown("---")

with st.expander("Ver Histórico de Movimentações", expanded=False):
    historico_df = carregar_historico_completo()
    st.dataframe(historico_df, use_container_width=True, hide_index=True, column_config={
        "data_movimentacao": "Data e Hora",
        "numero_serie": "N/S do Aparelho",
        "nome_modelo": "Modelo",
        "colaborador": "Colaborador",
        "nome_status": "Status Registado",
        "localizacao_atual": "Localização",
        "observacoes": "Observações"
    })
