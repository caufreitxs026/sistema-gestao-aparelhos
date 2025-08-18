import streamlit as st
import sqlite3
import json
import pandas as pd
from auth import show_login_form, logout
import asyncio
import httpx
from datetime import date, datetime

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

def executar_criar_colaborador(dados):
    """Adiciona um novo colaborador ao banco de dados."""
    if not dados or not dados.get('nome_completo') or not dados.get('codigo'):
        return "Não foi possível criar o colaborador. Faltam informações essenciais (nome e código)."
    
    conn = get_db_connection()
    try:
        setor_id = None
        if dados.get('nome_setor'):
            setor = conn.execute("SELECT id FROM setores WHERE nome_setor LIKE ?", (f"%{dados['nome_setor']}%",)).fetchone()
            if setor:
                setor_id = setor['id']

        conn.execute(
            "INSERT INTO colaboradores (nome_completo, codigo, cpf, gmail, setor_id, data_cadastro) VALUES (?, ?, ?, ?, ?, ?)",
            (dados['nome_completo'], dados.get('codigo'), dados.get('cpf'), dados.get('gmail'), setor_id, date.today())
        )
        conn.commit()
        return f"Colaborador '{dados['nome_completo']}' criado com sucesso!"
    except sqlite3.IntegrityError:
        return f"Erro: Já existe um colaborador com o código '{dados.get('codigo')}' ou CPF '{dados.get('cpf')}'."
    except Exception as e:
        return f"Ocorreu um erro inesperado ao criar o colaborador: {e}"
    finally:
        conn.close()

def executar_criar_aparelho(dados):
    """Adiciona um novo aparelho ao banco de dados."""
    if not dados or not all(k in dados for k in ['marca', 'modelo', 'numero_serie', 'valor']):
        return "Faltam informações para criar o aparelho (Marca, Modelo, N/S, Valor)."
    
    conn = get_db_connection()
    try:
        modelo_completo = f"{dados['marca']} - {dados['modelo']}"
        modelo_id_row = conn.execute("SELECT mo.id FROM modelos mo JOIN marcas ma ON mo.marca_id = ma.id WHERE (ma.nome_marca || ' - ' || mo.nome_modelo) = ?", (modelo_completo,)).fetchone()
        if not modelo_id_row:
            return f"Erro: O modelo '{modelo_completo}' não foi encontrado nos cadastros."
        
        modelo_id = modelo_id_row[0]
        status_id = conn.execute("SELECT id FROM status WHERE nome_status = 'Em estoque'").fetchone()[0]

        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION;")
        cursor.execute(
            "INSERT INTO aparelhos (numero_serie, imei1, imei2, valor, modelo_id, status_id, data_cadastro) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (dados['numero_serie'], dados.get('imei1'), dados.get('imei2'), float(dados['valor']), modelo_id, status_id, date.today())
        )
        aparelho_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO historico_movimentacoes (data_movimentacao, aparelho_id, status_id, localizacao_atual, observacoes) VALUES (?, ?, ?, ?, ?)",
            (datetime.now(), aparelho_id, status_id, "Estoque Interno", "Entrada via assistente Flow.")
        )
        conn.commit()
        return f"Aparelho '{modelo_completo}' (N/S: {dados['numero_serie']}) criado com sucesso!"
    except sqlite3.IntegrityError:
        conn.rollback()
        return f"Erro: Já existe um aparelho com o Número de Série '{dados['numero_serie']}'."
    except Exception as e:
        conn.rollback()
        return f"Ocorreu um erro inesperado: {e}"
    finally:
        conn.close()

def executar_pesquisa_movimentacoes(filtros):
    """Executa uma pesquisa no histórico de movimentações."""
    if not filtros:
        return "Por favor, forneça um critério de pesquisa (colaborador, N/S ou data)."

    conn = get_db_connection()
    query = """
        SELECT h.data_movimentacao, a.numero_serie, mo.nome_modelo, c.nome_completo as colaborador, s.nome_status, h.observacoes
        FROM historico_movimentacoes h
        JOIN aparelhos a ON h.aparelho_id = a.id
        JOIN status s ON h.status_id = s.id
        LEFT JOIN colaboradores c ON h.colaborador_id = c.id
        LEFT JOIN modelos mo ON a.modelo_id = mo.id
    """
    params = []
    where_clauses = []

    if filtros.get("nome_colaborador"):
        where_clauses.append("c.nome_completo LIKE ?")
        params.append(f"%{filtros['nome_colaborador']}%")
    if filtros.get("numero_serie"):
        where_clauses.append("a.numero_serie LIKE ?")
        params.append(f"%{filtros['numero_serie']}%")
    if filtros.get("data"):
        where_clauses.append("date(h.data_movimentacao) = ?")
        params.append(filtros['data'])

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    query += " ORDER BY h.data_movimentacao DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# --- Lógica do Chatbot ---

schema = {
    "type": "OBJECT",
    "properties": {
        "acao": {
            "type": "STRING",
            "enum": ["criar_colaborador", "criar_aparelho", "pesquisar_aparelho", "pesquisar_movimentacoes", "limpar_chat", "logout", "saudacao", "desconhecido"]
        },
        "dados": {
            "type": "OBJECT",
            "properties": {
                "nome_completo": {"type": "STRING"}, "codigo": {"type": "STRING"},
                "cpf": {"type": "STRING"}, "gmail": {"type": "STRING"}, "nome_setor": {"type": "STRING"},
                "marca": {"type": "STRING"}, "modelo": {"type": "STRING"},
                "numero_serie": {"type": "STRING"}, "imei1": {"type": "STRING"},
                "imei2": {"type": "STRING"}, "valor": {"type": "NUMBER"}
            }
        },
        "filtros": { "type": "OBJECT", "properties": { "nome_colaborador": {"type": "STRING"}, "numero_serie": {"type": "STRING"}, "data": {"type": "STRING", "description": "Data no formato YYYY-MM-DD"} } }
    },
    "required": ["acao"]
}

async def get_flow_response(prompt, user_name):
    contextual_prompt = f"O utilizador '{user_name}' pediu: {prompt}"
    chatHistory = [
        {"role": "user", "parts": [{"text": "Você é o Flow, um assistente para um sistema de gestão de ativos. Sua função é interpretar os pedidos do utilizador e traduzi-los para um formato JSON estruturado, de acordo com o schema fornecido. Seja conciso e direto."}]},
        {"role": "model", "parts": [{"text": "Entendido. Estou pronto para processar os pedidos e retornar o JSON correspondente."}]},
        {"role": "user", "parts": [{"text": contextual_prompt}]}
    ]
    payload = { "contents": chatHistory, "generationConfig": { "responseMimeType": "application/json", "responseSchema": schema } }
    try:
        apiKey = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        return {"acao": "desconhecido", "dados": {"erro": "Chave de API não configurada."}}
    apiUrl = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={apiKey}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(apiUrl, headers={'Content-Type': 'application/json'}, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        if result.get('candidates'):
            json_text = result['candidates'][0]['content']['parts'][0]['text']
            return json.loads(json_text)
        else:
            return {"acao": "desconhecido", "dados": {"erro": f"Não consegui entender o pedido. Resposta da API: {result}"}}
    except Exception as e:
        return {"acao": "desconhecido", "dados": {"erro": f"Ocorreu um erro de comunicação: {e}"}}

def get_info_text():
    return """
    Olá! Sou o Flow, o seu assistente. Veja como me pode usar:

    **1. Para Pesquisar:**
    - **Aparelhos:** Diga "pesquisar aparelho do [nome do colaborador]" ou "encontrar aparelho com n/s [número de série]".
    - **Movimentações:** Diga "mostrar histórico do [nome do colaborador]", "ver movimentações do aparelho [número de série]" ou "o que aconteceu em [data no formato AAAA-MM-DD]?".

    **2. Para Criar Novos Registos:**
    - **Colaborador:** Comece por dizer "criar colaborador". Eu irei guiá-lo sobre os dados necessários.
      - *Exemplo de dados:* `código 123, nome João Silva, cpf 11122233344, setor TI`
    - **Aparelho:** Comece por dizer "criar aparelho". Eu irei guiá-lo sobre os dados necessários.
      - *Exemplo de dados:* `marca Samsung, modelo S24, n/s ABC123XYZ, valor 5500`

    **3. Comandos do Chat:**
    - **`#info`:** Mostra esta mensagem de ajuda.
    - **`limpar chat`:** Apaga o histórico da nossa conversa.
    - **`encerrar chat` ou `logout`:** Faz o logout do sistema.

    Estou aqui para ajudar a tornar a sua gestão mais rápida e fácil!
    """

# --- Interface do Chatbot ---
st.title("💬 Converse com o Flow")
st.markdown("---")
st.info("Sou o Flow, seu assistente inteligente. Diga `#info` para ver os comandos, `limpar chat` para recomeçar ou `encerrar chat` para sair.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": f"Olá {st.session_state['user_name']}! Como posso ajudar a gerir os seus ativos hoje? Diga `#info` para ver o que posso fazer."}]
if "pending_action" not in st.session_state:
    st.session_state.pending_action = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], pd.DataFrame):
            st.dataframe(message["content"], hide_index=True, use_container_width=True)
        else:
            st.markdown(message["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Como posso ajudar?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("A pensar..."):
            if prompt.strip().lower() == '#info':
                response_data = {"acao": "ajuda"}
            else:
                response_data = asyncio.run(get_flow_response(prompt, st.session_state['user_name']))
            
            acao = response_data.get('acao')
            dados = response_data.get('dados')
            
            if acao in ['criar_colaborador', 'criar_aparelho']:
                if (acao == 'criar_colaborador' and not (dados and dados.get('nome_completo') and dados.get('codigo'))) or \
                   (acao == 'criar_aparelho' and not (dados and all(k in dados for k in ['marca', 'modelo', 'numero_serie', 'valor']))):
                    if acao == 'criar_colaborador':
                        response_content = "Entendido. Para adicionar um novo colaborador, por favor, informe os seguintes dados: **Código**, **Nome Completo**, **CPF**, **Gmail** (opcional) e **Setor**."
                    else:
                        response_content = "Entendido. Para adicionar um novo aparelho, por favor, informe: **Marca**, **Modelo**, **Número de Série**, **Valor** e **IMEIs** (opcional)."
                    st.markdown(response_content)
                    st.session_state.messages.append({"role": "assistant", "content": response_content})
                else:
                    st.session_state.pending_action = {"acao": acao, "dados": dados}
                    entidade = "colaborador" if acao == 'criar_colaborador' else 'aparelho'
                    nome_entidade = dados.get('nome_completo') if entidade == 'colaborador' else f"{dados.get('marca')} {dados.get('modelo')}"
                    response_content = f"A registar o {entidade} **{nome_entidade}**. Confirma as informações?"
                    st.markdown(response_content)
                    st.session_state.messages.append({"role": "assistant", "content": response_content})

            elif acao in ['pesquisar_aparelho', 'pesquisar_movimentacoes']:
                executor = executar_pesquisa_aparelho if acao == 'pesquisar_aparelho' else executar_pesquisa_movimentacoes
                resultados = executor(response_data.get('filtros'))
                if isinstance(resultados, pd.DataFrame) and not resultados.empty:
                    response_content = f"Encontrei {len(resultados)} resultado(s) com esses critérios:"
                    st.markdown(response_content)
                    st.dataframe(resultados, hide_index=True, use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": resultados})
                elif isinstance(resultados, pd.DataFrame) and resultados.empty:
                    response_content = "Não encontrei nenhum resultado com esses critérios."
                    st.markdown(response_content)
                    st.session_state.messages.append({"role": "assistant", "content": response_content})
                else:
                    st.markdown(resultados)
                    st.session_state.messages.append({"role": "assistant", "content": resultados})

            elif acao == 'ajuda':
                response_content = get_info_text()
                st.markdown(response_content, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response_content})

            elif acao == 'limpar_chat':
                st.session_state.messages = [{"role": "assistant", "content": "Chat limpo! Como posso ajudar a recomeçar?"}]
                st.session_state.pending_action = None
                st.rerun()

            elif acao == 'logout':
                st.info("A encerrar a sessão...")
                logout()

            elif acao == 'saudacao':
                response_content = f"Olá {st.session_state['user_name']}! Sou o Flow. Diga `#info` para ver o que posso fazer."
                st.markdown(response_content)
                st.session_state.messages.append({"role": "assistant", "content": response_content})

            else:
                erro = response_data.get("dados", {}).get("erro")
                if erro:
                    response_content = f"Ocorreu um erro: {erro}"
                else:
                    response_content = "Desculpe, não consegui entender o seu pedido. Pode tentar reformular? Diga `#info` para ver exemplos."
                st.markdown(response_content)
                st.session_state.messages.append({"role": "assistant", "content": response_content})

# --- Botões de Confirmação ---
if st.session_state.pending_action:
    action_data = st.session_state.pending_action
    col1, col2, col3 = st.columns([1, 1, 5])
    with col1:
        if st.button("Sim, confirmo", type="primary"):
            resultado = ""
            if action_data["acao"] == "criar_colaborador":
                resultado = executar_criar_colaborador(action_data["dados"])
            elif action_data["acao"] == "criar_aparelho":
                resultado = executar_criar_aparelho(action_data["dados"])
            
            st.success(resultado)
            st.session_state.messages.append({"role": "assistant", "content": f"✅ **Sucesso:** {resultado}"})
            st.session_state.pending_action = None
            st.rerun()

    with col2:
        if st.button("Não, cancelar"):
            st.warning("Ação cancelada.")
            st.session_state.messages.append({"role": "assistant", "content": "Ação cancelada pelo utilizador."})
            st.session_state.pending_action = None
            st.rerun()
