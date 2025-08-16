import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from auth import show_login_form, logout
from datetime import datetime, timedelta

# --- Configuração inicial da página e do estado da sessão ---
st.set_page_config(page_title="AssetFlow", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- Lógica de Autenticação ---
# Se o utilizador não estiver logado, mostra apenas o formulário de login.
if not st.session_state['logged_in']:
    show_login_form()
else:
    # --- Se logado, mostra a aplicação completa ---

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
        .logo-asset { color: #003366; }
        .logo-flow { color: #E30613; }

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
            logout()

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

    # --- Funções do Banco de Dados para o Dashboard ---
    def get_db_connection():
        conn = sqlite3.connect('inventario.db')
        conn.row_factory = sqlite3.Row
        return conn

    @st.cache_data(ttl=600) # O cache otimiza o desempenho
    def carregar_dados_dashboard():
        conn = get_db_connection()
        
        # KPIs
        total_aparelhos = conn.execute("SELECT COUNT(id) FROM aparelhos").fetchone()[0] or 0
        valor_total = conn.execute("SELECT SUM(valor) FROM aparelhos").fetchone()[0] or 0
        total_colaboradores = conn.execute("SELECT COUNT(id) FROM colaboradores").fetchone()[0] or 0
        
        kpis_manutencao = conn.execute("""
            SELECT COUNT(a.id), SUM(a.valor) 
            FROM aparelhos a JOIN status s ON a.status_id = s.id 
            WHERE s.nome_status = 'Em manutenção'
        """).fetchone()
        aparelhos_manutencao = kpis_manutencao[0] or 0
        valor_manutencao = kpis_manutencao[1] or 0
        
        aparelhos_estoque = conn.execute("""
            SELECT COUNT(a.id) FROM aparelhos a JOIN status s ON a.status_id = s.id WHERE s.nome_status = 'Em estoque'
        """).fetchone()[0] or 0

        # Gráficos
        df_status = pd.read_sql_query("SELECT s.nome_status, COUNT(a.id) as quantidade FROM aparelhos a JOIN status s ON a.status_id = s.id GROUP BY s.nome_status", conn)
        df_setor = pd.read_sql_query("""
            SELECT s.nome_setor, COUNT(a.id) as quantidade
            FROM aparelhos a
            JOIN historico_movimentacoes h ON a.id = h.aparelho_id
            JOIN (SELECT aparelho_id, MAX(data_movimentacao) as max_data FROM historico_movimentacoes GROUP BY aparelho_id) hm ON h.aparelho_id = hm.aparelho_id AND h.data_movimentacao = hm.max_data
            JOIN colaboradores c ON h.colaborador_id = c.id
            JOIN setores s ON c.setor_id = s.id
            WHERE a.status_id = (SELECT id FROM status WHERE nome_status = 'Em uso')
            GROUP BY s.nome_setor
        """, conn)

        # Painel de Ação Rápida
        data_limite = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        df_manut_atrasadas = pd.read_sql_query(f"""
            SELECT a.numero_serie, mo.nome_modelo, m.fornecedor, m.data_envio
            FROM manutencoes m
            JOIN aparelhos a ON m.aparelho_id = a.id
            JOIN modelos mo ON a.modelo_id = mo.id
            WHERE m.status_manutencao = 'Em Andamento' AND m.data_envio < '{data_limite}'
        """, conn)

        df_ultimas_mov = pd.read_sql_query("""
            SELECT h.data_movimentacao, c.nome_completo, s.nome_status, a.numero_serie
            FROM historico_movimentacoes h
            LEFT JOIN colaboradores c ON h.colaborador_id = c.id
            JOIN status s ON h.status_id = s.id
            JOIN aparelhos a ON h.aparelho_id = a.id
            ORDER BY h.data_movimentacao DESC LIMIT 5
        """, conn)

        conn.close()
        return {
            "kpis": {
                "total_aparelhos": total_aparelhos, "valor_total": valor_total,
                "total_colaboradores": total_colaboradores, "aparelhos_manutencao": aparelhos_manutencao,
                "valor_manutencao": valor_manutencao, "aparelhos_estoque": aparelhos_estoque
            },
            "graficos": {"status": df_status, "setor": df_setor},
            "acao_rapida": {"manut_atrasadas": df_manut_atrasadas, "ultimas_mov": df_ultimas_mov}
        }

    # --- Conteúdo do Dashboard ---
    
    # Título e Botão de Atualização
    col_titulo, col_botao = st.columns([3, 1])
    with col_titulo:
        st.title("Dashboard Gerencial")
    with col_botao:
        if st.button("Atualizar Dados"):
            carregar_dados_dashboard.clear()
            st.rerun()

    st.markdown("---")

    dados = carregar_dados_dashboard()
    kpis = dados['kpis']
    graficos = dados['graficos']
    acao_rapida = dados['acao_rapida']

    # 1. Visão Geral
    st.subheader("Visão Geral")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Aparelhos", f"{kpis['total_aparelhos']:,}".replace(",", "."))
    col2.metric("Valor Total do Inventário", f"R$ {kpis['valor_total']:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))
    col3.metric("Total de Colaboradores", f"{kpis['total_colaboradores']:,}".replace(",", "."))
    
    col4, col5, col6 = st.columns(3)
    col4.metric("Aparelhos em Manutenção", f"{kpis['aparelhos_manutencao']:,}".replace(",", "."))
    col5.metric("Valor em Manutenção", f"R$ {kpis['valor_manutencao']:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))
    col6.metric("Aparelhos em Estoque", f"{kpis['aparelhos_estoque']:,}".replace(",", "."))

    st.markdown("---")

    # 2. Análise Operacional
    st.subheader("Análise Operacional")
    gcol1, gcol2 = st.columns(2)
    with gcol1:
        st.markdown("###### Aparelhos por Status")
        if not graficos['status'].empty:
            fig = px.pie(graficos['status'], names='nome_status', values='quantidade', hole=.4)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não há dados de status para exibir.")
    with gcol2:
        st.markdown("###### Distribuição de Aparelhos por Setor")
        if not graficos['setor'].empty:
            fig2 = px.bar(graficos['setor'], x='nome_setor', y='quantidade', text_auto=True)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Não há aparelhos 'Em uso' para exibir a distribuição por setor.")

    st.markdown("---")

    # 3. Painel de Ação Rápida
    st.subheader("Painel de Ação Rápida")
    acol1, acol2 = st.columns(2)
    with acol1:
        st.markdown("###### Alerta: Manutenções Atrasadas (> 5 dias)")
        st.dataframe(acao_rapida['manut_atrasadas'], hide_index=True, use_container_width=True)
    with acol2:
        st.markdown("###### Últimas 5 Movimentações")
        st.dataframe(acao_rapida['ultimas_mov'], hide_index=True, use_container_width=True)


