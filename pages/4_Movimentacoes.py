import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from auth import show_login_form

# --- Verificação de Autenticação ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("app.py")

# --- Configuração de Layout (Header, Footer e CSS) ---
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

def registar_movimentacao(aparelho_id, colaborador_id, novo_status_id, novo_status_nome, localizacao, observacoes):
    conn = get_db_connection()
    cursor = conn.cursor()
    data_hora_agora = datetime.now()
    try:
        cursor.execute("BEGIN TRANSACTION;")
        
        id_colaborador_final = colaborador_id
        if novo_status_nome == "Em manutenção":
            ultimo_colaborador = cursor.execute("SELECT colaborador_id FROM historico_movimentacoes WHERE aparelho_id = ? AND colaborador_id IS NOT NULL ORDER BY data_movimentacao DESC LIMIT 1", (aparelho_id,)).fetchone()
            if ultimo_colaborador:
                id_colaborador_final = ultimo_colaborador[0]

        cursor.execute(
            "INSERT INTO historico_movimentacoes (data_movimentacao, aparelho_id, colaborador_id, status_id, localizacao_atual, observacoes) VALUES (?, ?, ?, ?, ?, ?)",
            (data_hora_agora, aparelho_id, id_colaborador_final, novo_status_id, localizacao, observacoes)
        )
        cursor.execute(
            "UPDATE aparelhos SET status_id = ? WHERE id = ?",
            (novo_status_id, aparelho_id)
        )
        
        if novo_status_nome == "Em manutenção":
            cursor.execute("""
                INSERT INTO manutencoes (aparelho_id, colaborador_id_no_envio, data_envio, defeito_reportado, status_manutencao)
                VALUES (?, ?, ?, ?, ?)
            """, (aparelho_id, id_colaborador_final, date.today(), observacoes, 'Em Andamento'))

        conn.commit()
        st.success("Movimentação registada com sucesso!")
        if novo_status_nome == "Em manutenção":
            st.info("Uma Ordem de Serviço preliminar foi aberta. Aceda à página 'Manutenções' para adicionar o fornecedor.")

    except Exception as e:
        conn.rollback()
        st.error(f"Ocorreu um erro ao registar a movimentação: {e}")
    finally:
        conn.close()

def carregar_historico_completo(status_filter=None, start_date=None, end_date=None):
    """Carrega o histórico completo de movimentações, com filtros avançados."""
    conn = get_db_connection()
    query = """
        SELECT 
            h.id, h.data_movimentacao, a.numero_serie, mo.nome_modelo,
            c.nome_completo as colaborador, s.nome_status,
            h.localizacao_atual, h.observacoes
        FROM historico_movimentacoes h
        JOIN aparelhos a ON h.aparelho_id = a.id
        JOIN status s ON h.status_id = s.id
        LEFT JOIN colaboradores c ON h.colaborador_id = c.id
        LEFT JOIN modelos mo ON a.modelo_id = mo.id
    """
    params = []
    where_clauses = []

    if status_filter and status_filter != "Todos":
        where_clauses.append("s.nome_status = ?")
        params.append(status_filter)
    
    if start_date and end_date:
        where_clauses.append("date(h.data_movimentacao) BETWEEN ? AND ?")
        params.append(start_date.strftime('%Y-%m-%d'))
        params.append(end_date.strftime('%Y-%m-%d'))
    elif start_date:
        where_clauses.append("date(h.data_movimentacao) >= ?")
        params.append(start_date.strftime('%Y-%m-%d'))
    elif end_date:
        where_clauses.append("date(h.data_movimentacao) <= ?")
        params.append(end_date.strftime('%Y-%m-%d'))

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    query += " ORDER BY h.data_movimentacao DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# --- Interface do Usuário ---

aparelhos_list, colaboradores_list, status_list = carregar_dados_para_selects()

st.subheader("Formulário de Movimentação")

with st.form("form_movimentacao", clear_on_submit=True):
    aparelhos_dict = {f"{ap['nome_marca']} {ap['nome_modelo']} (S/N: {ap['numero_serie']})": ap['id'] for ap in aparelhos_list}
    aparelho_selecionado_str = st.selectbox(
        "Selecione o Aparelho*",
        options=aparelhos_dict.keys(),
        help="Clique na lista e comece a digitar para pesquisar."
    )

    colaboradores_dict = {col['nome_completo']: col['id'] for col in colaboradores_list}
    opcoes_colaborador_com_nenhum = {"Nenhum": None}
    opcoes_colaborador_com_nenhum.update(colaboradores_dict)
    
    colaborador_selecionado_str = st.selectbox(
        "Atribuir ao Colaborador",
        options=opcoes_colaborador_com_nenhum.keys(),
        help="Clique na lista e comece a digitar para pesquisar."
    )
    
    status_dict = {s['nome_status']: s['id'] for s in status_list}
    novo_status_str = st.selectbox("Novo Status do Aparelho*", options=status_dict.keys())
    nova_localizacao = st.text_input("Nova Localização", placeholder="Ex: Mesa do colaborador, Assistência Técnica XYZ")
    observacoes = st.text_area("Observações", placeholder="Ex: Devolução com tela trincada, Envio para troca de bateria.")

    submitted = st.form_submit_button("Registar Movimentação")
    if submitted:
        if not aparelho_selecionado_str or not novo_status_str:
            st.error("Aparelho e Novo Status são campos obrigatórios.")
        else:
            aparelho_id = aparelhos_dict[aparelho_selecionado_str]
            colaborador_id = opcoes_colaborador_com_nenhum[colaborador_selecionado_str]
            novo_status_id = status_dict[novo_status_str]
            registar_movimentacao(aparelho_id, colaborador_id, novo_status_id, novo_status_str, nova_localizacao, observacoes)

st.markdown("---")

with st.expander("Ver e Filtrar Histórico de Movimentações", expanded=True):
    
    # --- NOVOS FILTROS AVANÇADOS ---
    st.markdown("###### Filtros do Relatório")
    
    status_options = ["Todos"] + [s['nome_status'] for s in status_list]
    status_filtro = st.selectbox("Filtrar por Status:", status_options)

    col_data1, col_data2 = st.columns(2)
    data_inicio = col_data1.date_input("Período de:", value=None, format="DD/MM/YYYY")
    data_fim = col_data2.date_input("Até:", value=None, format="DD/MM/YYYY")

    # Carrega os dados com os filtros aplicados
    historico_df = carregar_historico_completo(status_filter=status_filtro, start_date=data_inicio, end_date=data_fim)
    
    st.markdown("###### Resultados")
    st.dataframe(historico_df, use_container_width=True, hide_index=True, column_config={
        "data_movimentacao": "Data e Hora",
        "numero_serie": "N/S do Aparelho",
        "nome_modelo": "Modelo",
        "colaborador": "Colaborador",
        "nome_status": "Status Registado",
        "localizacao_atual": "Localização",
        "observacoes": "Observações"
    })
