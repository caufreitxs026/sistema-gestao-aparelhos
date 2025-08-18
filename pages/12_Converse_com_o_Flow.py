import streamlit as st
import sqlite3
import json
import pandas as pd
from auth import show_login_form
import asyncio
import httpx

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
    chatHistory = [
        {
            "role": "user",
            "parts": [{"text": "Você é o Flow, um assistente para um sistema de gestão de ativos. Sua função é interpretar os pedidos do utilizador e traduzi-los para um formato JSON estruturado, de acordo com o schema fornecido. Seja conciso e direto."}]
        },
        {
            "role": "model",
            "parts": [{"text": "Entendido. Estou pronto para processar os pedidos e retornar o JSON correspondente."}]
        },
        {"role": "user", "parts": [{"text": prompt}]}
    ]
    
    payload = {
        "contents": chatHistory,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema
        }
    }
    
    try:
        apiKey = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        return {"acao": "desconhecido", "dados": {"erro": "Chave de API não encontrada. Por favor, configure o segredo 'GEMINI_API_KEY'."}}

    apiUrl = f"https://generativelace.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={apiKey}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                apiUrl,
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )
        response.raise_for_status()
        result = response.json()
        
        if result.get('candidates'):
            json_text = result['candidates'][0]['content']['parts'][0]['text']
            return json.loads(json_text)
        else:
            return {"acao": "desconhecido", "dados": {"erro": f"Não consegui entender o pedido. Resposta da API: {result}"}}
    except Exception as e:
        return {"acao": "desconhecido", "dados": {"erro": f"Ocorreu um erro de comunicação: {e}"}}

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
            response_data = asyncio.run(get_flow_response(prompt))

            # --- O EXECUTOR DE AÇÕES ---
            acao = response_data.get('acao')
            
            if acao == 'pesquisar_aparelho':
                resultados = executar_pesquisa_aparelho(response_data.get('filtros'))
                if isinstance(resultados, pd.DataFrame) and not resultados.empty:
                    response_content = f"Encontrei {len(resultados)} aparelho(s) com esses critérios:"
                    st.markdown(response_content)
                    st.dataframe(resultados, hide_index=True, use_container_width=True)
                    # Guarda a tabela nos logs do chat para ser re-exibida
                    st.session_state.messages.append({"role": "assistant", "content": resultados})
                elif isinstance(resultados, pd.DataFrame) and resultados.empty:
                    response_content = "Não encontrei nenhum aparelho com esses critérios."
                    st.markdown(response_content)
                    st.session_state.messages.append({"role": "assistant", "content": response_content})
                else: # Caso a função retorne uma string de erro
                    st.markdown(resultados)
                    st.session_state.messages.append({"role": "assistant", "content": resultados})

            elif acao == 'saudacao':
                response_content = "Olá! Sou o Flow. Pode pedir-me para pesquisar aparelhos por colaborador ou número de série."
                st.markdown(response_content)
                st.session_state.messages.append({"role": "assistant", "content": response_content})

            else: # Ação desconhecida ou erro da API
                erro = response_data.get("dados", {}).get("erro")
                if erro:
                    response_content = f"Ocorreu um erro: {erro}"
                else:
                    response_content = "Desculpe, não consegui entender o seu pedido. Pode tentar reformular? Por exemplo: 'Encontre os aparelhos do Cauã Freitas'."
                st.markdown(response_content)
                st.session_state.messages.append({"role": "assistant", "content": response_content})
