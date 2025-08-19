import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from auth import show_login_form, logout

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

    def carregar_kpis():
        conn = get_db_connection()
        total_aparelhos = conn.execute("SELECT COUNT(id) FROM aparelhos").fetchone()[0]
        valor_total = conn.execute("SELECT SUM(valor) FROM aparelhos").fetchone()[0]
        total_colaboradores = conn.execute("SELECT COUNT(id) FROM colaboradores").fetchone()[0]
        conn.close()
        return {
            "total_aparelhos": total_aparelhos or 0,
            "valor_total": valor_total or 0,
            "total_colaboradores": total_colaboradores or 0
        }

    def carregar_aparelhos_por_status():
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT s.nome_status, COUNT(a.id) as quantidade FROM aparelhos a JOIN status s ON a.status_id = s.id GROUP BY s.nome_status", conn)
        conn.close()
        return df

    # --- Conteúdo do Dashboard ---
    st.title("Dashboard Gerencial")
    st.markdown("---")

    kpis = carregar_kpis()
    df_status = carregar_aparelhos_por_status()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Aparelhos", f"{kpis['total_aparelhos']:,}".replace(",", "."))
    col2.metric("Valor Total do Inventário", f"R$ {kpis['valor_total']:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))
    col3.metric("Total de Colaboradores", f"{kpis['total_colaboradores']:,}".replace(",", "."))

    st.markdown("---")

    st.subheader("Aparelhos por Status")
    if not df_status.empty:
        fig = px.pie(df_status, names='nome_status', values='quantidade', hole=.3)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Não há dados de status para exibir.")
