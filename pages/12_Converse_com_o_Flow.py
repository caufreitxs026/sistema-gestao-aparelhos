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
    /* Estilos da Logo Principal */
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
    .sidebar-footer a { margin-right: 15px; text-decoration: none; }
    .sidebar-footer img {
        width: 25px; height: 25px; filter: grayscale(1) opacity(0.5);
        transition: filter 0.3s;
    }
    .sidebar-footer img:hover { filter: grayscale(0) opacity(1); }
    @media (prefers-color-scheme: dark) {
        .sidebar-footer img { filter: grayscale(1) opacity(0.6) invert(1); }
        .sidebar-footer img:hover { filter: opacity(1) invert(1); }
    }

    /* --- NOVO: Estilos para a Logo do Chat --- */
    .flow-title {
        display: flex;
        align-items: center;
        padding-bottom: 10px;
    }
    .flow-title .icon {
        font-size: 2.5em;
        margin-right: 15px;
    }
    .flow-title h1 {
        font-family: 'Courier New', monospace;
        font-size: 3em;
        font-weight: bold;
        margin: 0;
        padding: 0;
        line-height: 1;
    }
    .flow-title .text-chat { color: #003366; }
    .flow-title .text-flow { color: #E30613; }
    @media (prefers-color-scheme: dark) {
        .flow-title .text-chat { color: #FFFFFF; }
        .flow-title .text-flow { color: #FF4B4B; }
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

def executar_criar_conta_gmail(dados):
    """Adiciona uma nova conta Gmail ao banco de dados."""
    if not dados or not dados.get('email'):
        return "Não foi possível criar a conta. O e-mail é obrigatório."
    
    conn = get_db_connection()
    try:
        setor_id, colaborador_id = None, None
        if dados.get('nome_setor'):
            setor = conn.execute("SELECT id FROM setores WHERE nome_setor LIKE ?", (f"%{dados['nome_setor']}%",)).fetchone()
            if setor: setor_id = setor['id']
        
        if dados.get('nome_colaborador'):
            colaborador = conn.execute("SELECT id FROM colaboradores WHERE nome_completo LIKE ?", (f"%{dados['nome_colaborador']}%",)).fetchone()
            if colaborador: colaborador_id = colaborador['id']

        conn.execute(
            "INSERT INTO contas_gmail (email, senha, telefone_recuperacao, email_recuperacao, setor_id, colaborador_id) VALUES (?, ?, ?, ?, ?, ?)",
            (dados['email'], dados.get('senha'), dados.get('telefone_recuperacao'), dados.get('email_recuperacao'), setor_id, colaborador_id)
        )
        conn.commit()
        return f"Conta Gmail '{dados['email']}' criada com sucesso!"
    except sqlite3.IntegrityError:
        return f"Erro: A conta Gmail '{dados['email']}' já existe."
    except Exception as e:
        return f"Ocorreu um erro inesperado ao criar a conta: {e}"
    finally:
        conn.close()

# --- Lógica do Chatbot ---

schema = {
    "type": "OBJECT",
    "properties": {
        "acao": {
            "type": "STRING",
            "enum": ["iniciar_criacao", "fornecer_dado", "pesquisar_aparelho", "pesquisar_movimentacoes", "limpar_chat", "logout", "saudacao", "desconhecido"]
        },
        "entidade": {"type": "STRING", "enum": ["colaborador", "aparelho", "conta_gmail"]},
        "dados": {
            "type": "OBJECT",
            "properties": {
                "valor_dado": {"type": "STRING", "description": "O valor fornecido pelo utilizador para um campo específico."}
            }
        },
        "filtros": { "type": "OBJECT", "properties": { "nome_colaborador": {"type": "STRING"}, "numero_serie": {"type": "STRING"}, "data": {"type": "STRING"} } }
    },
    "required": ["acao"]
}


async def get_flow_response(prompt, user_name, current_action=None):
    """Envia o prompt para a API Gemini e retorna a resposta estruturada."""
    if current_action:
        contextual_prompt = f"O utilizador '{user_name}' está no meio de um processo de criação ({current_action}) e forneceu a seguinte informação: {prompt}. Interprete este dado como o valor para o campo que está a ser solicitado."
    else:
        contextual_prompt = f"O utilizador '{user_name}' pediu: {prompt}"
    
    chatHistory = [
        {"role": "user", "parts": [{"text": "Você é o Flow, um assistente para um sistema de gestão de ativos. Sua função é interpretar os pedidos do utilizador e traduzi-los para um formato JSON estruturado, de acordo com o schema fornecido. Se o utilizador iniciar um processo de criação (ex: 'criar aparelho'), a sua ação deve ser 'iniciar_criacao' e a entidade correspondente. Se o utilizador fornecer um dado no meio de uma conversa, a sua ação deve ser 'fornecer_dado'. Seja conciso e direto."}]},
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

    **2. Para Criar Novos Registos (Fluxo Guiado):**
    - **Colaborador:** Comece por dizer "criar colaborador".
    - **Aparelho:** Comece por dizer "criar aparelho".
    - **Conta Gmail:** Comece por dizer "criar conta gmail".
    Eu irei guiá-lo passo a passo, pedindo cada informação necessária.

    **3. Comandos do Chat:**
    - **`#info`:** Mostra esta mensagem de ajuda.
    - **`limpar chat`:** Apaga o histórico da nossa conversa.
    - **`encerrar chat` ou `logout`:** Faz o logout do sistema.

    Estou aqui para ajudar a tornar a sua gestão mais rápida e fácil!
    """

# --- Campos de Cadastro ---
CAMPOS_CADASTRO = {
    "colaborador": ["codigo", "nome_completo", "cpf", "gmail", "nome_setor"],
    "aparelho": ["marca", "modelo", "numero_serie", "valor", "imei1", "imei2"],
    "conta_gmail": ["email", "senha", "telefone_recuperacao", "email_recuperacao", "nome_setor", "nome_colaborador"]
}

# --- Interface do Chatbot ---
st.markdown(
    """
    <div class="flow-title">
        <span class="icon">💬</span>
        <h1><span class="text-chat">Converse com o </span><span class="text-flow">Flow</span></h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")
st.info("Sou o Flow, seu assistente inteligente. Diga `#info` para ver os comandos, `limpar chat` para recomeçar ou `encerrar chat` para sair.")

# Inicialização dos estados da sessão
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": f"Olá {st.session_state['user_name']}! Como posso ajudar?"}]
if "pending_action" not in st.session_state:
    st.session_state.pending_action = None
if "conversa_em_andamento" not in st.session_state:
    st.session_state.conversa_em_andamento = None
if "dados_recolhidos" not in st.session_state:
    st.session_state.dados_recolhidos = {}
if "campo_para_corrigir" not in st.session_state:
    st.session_state.campo_para_corrigir = None
if "modo_correcao" not in st.session_state:
    st.session_state.modo_correcao = False

# Exibe o histórico do chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], pd.DataFrame):
            st.dataframe(message["content"], hide_index=True, use_container_width=True)
        else:
            st.markdown(message["content"], unsafe_allow_html=True)

def proximo_campo():
    """Determina qual o próximo campo a ser solicitado."""
    entidade = st.session_state.conversa_em_andamento
    if not entidade: return None
    campos_necessarios = CAMPOS_CADASTRO[entidade]
    for campo in campos_necessarios:
        if campo not in st.session_state.dados_recolhidos:
            return campo
    return None

def adicionar_mensagem(role, content):
    """Adiciona uma mensagem ao histórico e à tela."""
    st.session_state.messages.append({"role": role, "content": content})
    with st.chat_message(role):
        if isinstance(content, pd.DataFrame):
            st.dataframe(content, hide_index=True, use_container_width=True)
        else:
            st.markdown(content, unsafe_allow_html=True)

def apresentar_resumo():
    """Apresenta o resumo dos dados recolhidos para confirmação."""
    # CORREÇÃO: Lógica mais robusta para encontrar a entidade
    entidade = st.session_state.get('conversa_em_andamento') or st.session_state.get('entidade_em_correcao')
    if not entidade:
        adicionar_mensagem("assistant", "Ocorreu um erro interno ao tentar apresentar o resumo.")
        return

    dados = st.session_state.dados_recolhidos
    resumo = f"Perfeito! Recolhi as informações. Por favor, confirme os dados para criar o **{entidade}**:\n"
    for key, value in dados.items():
        resumo += f"- **{key.replace('_', ' ').title()}:** {value}\n"
    adicionar_mensagem("assistant", resumo)
    st.session_state.pending_action = {
        "acao": f"criar_{entidade}",
        "dados": dados
    }
    st.session_state.conversa_em_andamento = None
    st.session_state.campo_para_corrigir = None
    st.session_state.entidade_em_correcao = None # Limpa o estado de correção


if prompt := st.chat_input("Como posso ajudar?"):
    adicionar_mensagem("user", prompt)

    with st.spinner("A pensar..."):
        # Se estivermos a corrigir um campo
        if st.session_state.campo_para_corrigir:
            campo = st.session_state.campo_para_corrigir
            st.session_state.dados_recolhidos[campo] = prompt
            st.session_state.campo_para_corrigir = None
            apresentar_resumo()
            st.rerun()

        # Se estivermos num fluxo de cadastro
        elif st.session_state.conversa_em_andamento:
            campo_atual = proximo_campo()
            st.session_state.dados_recolhidos[campo_atual] = prompt
            
            proximo = proximo_campo()
            if proximo:
                adicionar_mensagem("assistant", f"Entendido. Agora, qual é o **{proximo.replace('_', ' ')}**?")
            else: # Todos os campos foram recolhidos
                apresentar_resumo()
                st.rerun()
        
        # Se não houver conversa em andamento, interpreta o comando inicial
        else:
            if prompt.strip().lower() == '#info':
                response_data = {"acao": "ajuda"}
            else:
                response_data = asyncio.run(get_flow_response(prompt, st.session_state['user_name']))
            
            acao = response_data.get('acao')
            
            if acao == 'iniciar_criacao':
                entidade = response_data.get('entidade')
                if entidade in CAMPOS_CADASTRO:
                    st.session_state.conversa_em_andamento = entidade
                    st.session_state.dados_recolhidos = {}
                    primeiro_campo = proximo_campo()
                    adicionar_mensagem("assistant", f"Ótimo! Para criar um novo **{entidade}**, vamos começar. Qual é o **{primeiro_campo.replace('_', ' ')}**?")
                else:
                    adicionar_mensagem("assistant", "Desculpe, não sei como criar essa entidade.")
            
            elif acao in ['pesquisar_aparelho', 'pesquisar_movimentacoes']:
                executor = executar_pesquisa_aparelho if acao == 'pesquisar_aparelho' else executar_pesquisa_movimentacoes
                resultados = executor(response_data.get('filtros'))
                if isinstance(resultados, pd.DataFrame) and not resultados.empty:
                    adicionar_mensagem("assistant", f"Encontrei {len(resultados)} resultado(s):")
                    adicionar_mensagem("assistant", resultados)
                else:
                    adicionar_mensagem("assistant", "Não encontrei nenhum resultado com esses critérios.")

            elif acao == 'ajuda':
                adicionar_mensagem("assistant", get_info_text())

            elif acao == 'limpar_chat':
                st.session_state.messages = [{"role": "assistant", "content": "Chat limpo! Como posso ajudar a recomeçar?"}]
                st.session_state.pending_action = None
                st.rerun()

            elif acao == 'logout':
                adicionar_mensagem("assistant", "A encerrar a sessão...")
                logout()

            elif acao == 'saudacao':
                adicionar_mensagem("assistant", f"Olá {st.session_state['user_name']}! Sou o Flow. Diga `#info` para ver o que posso fazer.")

            else: # Ação desconhecida ou erro
                erro = response_data.get("dados", {}).get("erro", "Não consegui entender o seu pedido. Pode tentar reformular? Diga `#info` para ver exemplos.")
                adicionar_mensagem("assistant", f"Desculpe, ocorreu um problema: {erro}")

# --- Botões de Confirmação ---
if st.session_state.pending_action:
    action_data = st.session_state.pending_action
    
    col1, col2, col3 = st.columns([1, 1, 5])
    
    with col1:
        if st.button("Sim, confirmo", type="primary"):
            resultado = ""
            acao_executar = action_data["acao"]
            dados_executar = action_data["dados"]
            
            if acao_executar == "criar_colaborador":
                resultado = executar_criar_colaborador(dados_executar)
            elif acao_executar == "criar_aparelho":
                resultado = executar_criar_aparelho(dados_executar)
            elif acao_executar == "criar_conta_gmail":
                resultado = executar_criar_conta_gmail(dados_executar)

            # Lógica de Sucesso/Erro
            if "Erro:" in resultado:
                adicionar_mensagem("assistant", f"❌ **Falha:** {resultado}")
            else:
                adicionar_mensagem("assistant", f"✅ **Sucesso:** {resultado}")

            st.session_state.pending_action = None
            st.rerun()

    with col2:
        if st.button("Não, cancelar"):
            adicionar_mensagem("assistant", "Ação cancelada pelo utilizador.")
            st.session_state.pending_action = None
            st.rerun()

    with col3:
        if st.button("Corrigir uma informação"):
            # CORREÇÃO: Guarda a entidade e os dados para o modo de correção
            st.session_state.entidade_em_correcao = action_data['acao'].split('_')[1]
            st.session_state.dados_para_corrigir = action_data["dados"]
            st.session_state.modo_correcao = True
            st.session_state.pending_action = None
            st.rerun()

# --- Lógica de Correção (fora do loop principal) ---
if st.session_state.get('modo_correcao'):
    dados_para_corrigir = st.session_state.dados_para_corrigir
    campo_selecionado = st.selectbox(
        "Qual campo deseja corrigir?",
        options=dados_para_corrigir.keys(),
        key="campo_correcao",
        index=None,
        placeholder="Selecione um campo..."
    )
    if campo_selecionado:
        st.session_state.campo_para_corrigir = campo_selecionado
        adicionar_mensagem("assistant", f"Entendido. Por favor, insira o novo valor para **{campo_selecionado.replace('_', ' ')}**.")
        st.session_state.modo_correcao = False
        st.session_state.dados_recolhidos = dados_para_corrigir # Prepara para a correção
        st.rerun()
