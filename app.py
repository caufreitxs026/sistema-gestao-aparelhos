import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from auth import show_login_form, logout

# --- Configuração inicial da página e do estado da sessão ---
st.set_page_config(page_title="Gestão de Aparelhos", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- Lógica de Autenticação ---
# Se o usuário não estiver logado, mostra apenas o formulário de login.
if not st.session_state['logged_in']:
    show_login_form()
else:
    # --- Se logado, mostra a aplicação completa ---

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
        df = pd.read_sql_query("""
            SELECT s.nome_status, COUNT(a.id) as quantidade
            FROM aparelhos a
            JOIN status s ON a.status_id = s.id
            GROUP BY s.nome_status
        """, conn)
        conn.close()
        return df

    # --- Barra Lateral com Informações do Usuário e Logout ---
    with st.sidebar:
        st.write(f"Bem-vindo, **{st.session_state['user_name']}**!")
        st.write(f"Cargo: **{st.session_state['user_role']}**")
        if st.button("Logout"):
            logout()

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


