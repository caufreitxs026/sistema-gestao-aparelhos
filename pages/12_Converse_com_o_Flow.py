import streamlit as st
import sqlite3
import json
from auth import show_login_form

# --- Autenticação e Configuração da Página ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("app.py")

st.set_page_config(page_title="Converse com o Flow", layout="wide")

# --- Configuração de Layout (Header, Footer e CSS) ---
# ... (o seu código de layout atual vai aqui) ...

# --- Lógica do Chatbot ---

# Definição dos "Contratos" JSON que o Gemini deve seguir
schema = {
    "type": "OBJECT",
    "properties": {
        "acao": {
            "type": "STRING",
            "enum": ["criar_colaborador", "pesquisar_aparelho", "editar_colaborador", "excluir_aparelho", "desconhecido"]
        },
        "entidade": {
            "type": "STRING",
            "description": "A entidade principal da ação, ex: 'colaborador', 'aparelho'."
        },
        "dados": {
            "type": "OBJECT",
            "description": "Os dados necessários para a ação.",
            "properties": {
                "nome_completo": {"type": "STRING"},
                "codigo": {"type": "STRING"},
                "cpf": {"type": "STRING"},
                "numero_serie": {"type": "STRING"},
                "marca": {"type": "STRING"},
                "modelo": {"type": "STRING"},
                "valor": {"type": "NUMBER"}
            }
        },
        "filtros": {
            "type": "OBJECT",
            "description": "Filtros para ações de pesquisa.",
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
    
    # CORREÇÃO: Lê a chave de API a partir dos segredos do Streamlit
    try:
        apiKey = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        return {"acao": "desconhecido", "dados": {"erro": "Chave de API não encontrada. Por favor, configure o segredo 'GEMINI_API_KEY' nas definições da aplicação."}}

    apiUrl = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={apiKey}"
    
    try:
        import httpx
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
st.info("Sou o Flow, seu assistente inteligente. Peça-me para adicionar, editar, excluir ou pesquisar registos no sistema.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Como posso ajudar?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("A pensar..."):
            import asyncio
            response_data = asyncio.run(get_flow_response(prompt))
            
            st.markdown("Entendi o seu pedido da seguinte forma:")
            st.json(response_data)
            
            response_content = f"**Ação Detetada:** `{response_data.get('acao')}`. (A lógica para executar esta ação será implementada na próxima etapa)."
            st.session_state.messages.append({"role": "assistant", "content": response_content})
