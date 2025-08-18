import streamlit as st
import sqlite3
import json
import pandas as pd
from auth import show_login_form

# --- Autenticação e Configuração da Página ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("app.py")

st.set_page_config(page_title="Converse com o Flow", layout="wide")

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


# --- Funções do Executor de Ações ---
def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

def executar_pesquisa_aparelho(filtros):
    """Executa uma pesquisa na base de dados com base nos filtros fornecidos pela IA."""
    if not filtros:
        return "Por favor, forneça um critério de pesquisa, como o nome do colaborador ou o número de série."

    conn = get_db_connection()
    query = """
        SELECT a.numero_serie, mo.nome_modelo, c.nome_completo as responsavel, s.nome_status
        FROM aparelhos a
        LEFT JOIN modelos mo ON a.modelo_id = mo.id
        LEFT JOIN status s ON a.status_id = s.id
        LEFT JOIN (
            SELECT aparelho_id, colaborador_id
            FROM historico_movimentacoes
            WHERE (aparelho_id, data_movimentacao) IN (
                SELECT aparelho_id, MAX(data_movimentacao)
                FROM historico_movimentacoes
                GROUP BY aparelho_id
            )
        ) h ON a.id = h.aparelho_id
        LEFT JOIN colaboradores c ON h.colaborador_id = c.id
    """
    params = []
    where_clauses = []

    if filtros.get("nome_colaborador"):
        where_clauses.append("c.nome_completo LIKE ?")
        params.append(f"%{filtros['nome_colaborador']}%")
    
    if filtros.get("numero_serie"):
        where_clauses.append("a.numero_serie LIKE ?")
        params.append(f"%{filtros['numero_serie']}%")

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# --- Lógica do Chatbot ---

# Definição dos "Contratos" JSON que o Gemini deve seguir
schema = {
    "type": "OBJECT",
    "properties": {
        "acao": {
            "type": "STRING",
            "enum": ["pesquisar_aparelho", "saudacao", "desconhecido"]
        },
        "filtros": {
            "type": "OBJECT",
            "properties": {
                "nome_colaborador": {"type": "STRING"},
                "numero_serie": {"type": "STRING"}
            }
        }
    },
    "required": ["acao"]
}

async def get_flow_response(prompt):
    """Envia o prompt para a API Gemini e retorna a resposta estruturada."""
    # ... (código da função de chamada à API omitido para brevidade) ...
    # Esta função deve ser implementada com a sua chave de API
    return {"acao": "desconhecido", "dados": {"erro": "Função de API não implementada neste exemplo."}}

# --- Interface do Chatbot ---
st.title("💬 Converse com o Flow")
st.markdown("---")
st.info("Sou o Flow, seu assistente inteligente. Peça-me para pesquisar aparelhos por colaborador ou número de série.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Olá! Como posso ajudar a gerir os seus ativos hoje?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], pd.DataFrame):
            st.dataframe(message["content"], hide_index=True, use_container_width=True)
        else:
            st.markdown(message["content"])

if prompt := st.chat_input("Como posso ajudar?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("A pensar..."):
            import asyncio
            # Simulação da resposta da IA para testes
            if "cauã" in prompt.lower():
                 response_data = {"acao": "pesquisar_aparelho", "filtros": {"nome_colaborador": "Cauã"}}
            elif "olá" in prompt.lower() or "oi" in prompt.lower():
                 response_data = {"acao": "saudacao"}
            else:
                 response_data = {"acao": "desconhecido"}

            # --- O EXECUTOR DE AÇÕES ---
            acao = response_data.get('acao')
            
            if acao == 'pesquisar_aparelho':
                resultados = executar_pesquisa_aparelho(response_data.get('filtros'))
                if isinstance(resultados, pd.DataFrame) and not resultados.empty:
                    response_content = f"Encontrei {len(resultados)} aparelho(s) com esses critérios:"
                    st.markdown(response_content)
                    st.dataframe(resultados, hide_index=True, use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": resultados})
                elif isinstance(resultados, pd.DataFrame) and resultados.empty:
                    response_content = "Não encontrei nenhum aparelho com esses critérios."
                    st.markdown(response_content)
                    st.session_state.messages.append({"role": "assistant", "content": response_content})
                else:
                    st.markdown(resultados)
                    st.session_state.messages.append({"role": "assistant", "content": resultados})

            elif acao == 'saudacao':
                response_content = "Olá! Sou o Flow, o seu assistente. Pode pedir-me para pesquisar aparelhos por colaborador ou número de série."
                st.markdown(response_content)
                st.session_state.messages.append({"role": "assistant", "content": response_content})

            else: # Ação desconhecida
                response_content = "Desculpe, não consegui entender o seu pedido. Pode tentar reformular? Por exemplo: 'Encontre os aparelhos do Cauã Freitas'."
                st.markdown(response_content)
                st.session_state.messages.append({"role": "assistant", "content": response_content})
