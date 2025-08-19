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
    .logo-asset { color: #003366; }
    .logo-flow { color: #E30613; }
    @media (prefers-color-scheme: dark) {
        .logo-asset { color: #FFFFFF; }
        .logo-flow { color: #FF4B4B; }
    }
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
    .flow-title {
        display: flex;
        align-items: center;
        padding-bottom: 10px;
    }
    .flow-title .icon { font-size: 2.5em; margin-right: 15px; }
    .flow-title h1 {
        font-family: 'Courier New', monospace; font-size: 3em; font-weight: bold;
        margin: 0; padding: 0; line-height: 1;
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

# --- Funções do Executor de Ações ---
def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

def executar_pesquisa_aparelho(filtros):
    if not filtros:
        return "Por favor, forneça um critério de pesquisa, como o nome do colaborador ou o número de série."
    conn = get_db_connection()
    query = """
        SELECT a.numero_serie, mo.nome_modelo, c.nome_completo as responsavel, s.nome_status
        FROM aparelhos a
        LEFT JOIN modelos mo ON a.modelo_id = mo.id
        LEFT JOIN status s ON a.status_id = s.id
        LEFT JOIN (
            SELECT aparelho_id, colaborador_id FROM historico_movimentacoes
            WHERE (aparelho_id, data_movimentacao) IN (
                SELECT aparelho_id, MAX(data_movimentacao) FROM historico_movimentacoes GROUP BY aparelho_id
            )
        ) h ON a.id = h.aparelho_id
        LEFT JOIN colaboradores c ON h.colaborador_id = c.id
    """
    params, where_clauses = [], []
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
    if not all(k in dados for k in ['codigo', 'nome_completo', 'cpf']):
        return "Erro: Faltam informações essenciais (código, nome, cpf)."
    conn = get_db_connection()
    try:
        setor_id = None
        if dados.get('nome_setor'):
            setor = conn.execute("SELECT id FROM setores WHERE nome_setor LIKE ?", (f"%{dados['nome_setor']}%",)).fetchone()
            if setor: setor_id = setor['id']
        conn.execute(
            "INSERT INTO colaboradores (codigo, nome_completo, cpf, gmail, setor_id, data_cadastro) VALUES (?, ?, ?, ?, ?, ?)",
            (dados['codigo'], dados['nome_completo'], dados['cpf'], dados.get('gmail'), setor_id, date.today())
        )
        conn.commit()
        return f"Colaborador '{dados['nome_completo']}' criado com sucesso!"
    except sqlite3.IntegrityError:
        return f"Erro: Já existe um colaborador com o código '{dados.get('codigo')}' ou CPF '{dados.get('cpf')}'."
    except Exception as e:
        return f"Ocorreu um erro inesperado: {e}"
    finally:
        conn.close()

def executar_criar_aparelho(dados):
    if not all(k in dados for k in ['marca', 'modelo', 'numero_serie', 'valor']):
        return "Erro: Faltam informações (Marca, Modelo, N/S, Valor)."
    conn = get_db_connection()
    try:
        modelo_completo = f"{dados['marca']} - {dados['modelo']}"
        modelo_id_row = conn.execute("SELECT mo.id FROM modelos mo JOIN marcas ma ON mo.marca_id = ma.id WHERE (ma.nome_marca || ' - ' || mo.nome_modelo) = ?", (modelo_completo,)).fetchone()
        if not modelo_id_row:
            return f"Erro: O modelo '{modelo_completo}' não foi encontrado."
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
        return f"Erro: Já existe um aparelho com o N/S '{dados['numero_serie']}'."
    except Exception as e:
        conn.rollback()
        return f"Ocorreu um erro inesperado: {e}"
    finally:
        conn.close()

def executar_pesquisa_movimentacoes(filtros):
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
    params, where_clauses = [], []
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
        return f"Ocorreu um erro inesperado: {e}"
    finally:
        conn.close()

def executar_editar_colaborador(filtros, novos_dados):
    """Atualiza um colaborador existente."""
    if not filtros or not novos_dados:
        return "Erro: Faltam informações para identificar o colaborador ou o que deve ser alterado."
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if filtros.get('nome_completo'):
            cursor.execute("SELECT * FROM colaboradores WHERE nome_completo LIKE ?", (f"%{filtros['nome_completo']}%",))
        elif filtros.get('codigo'):
            cursor.execute("SELECT * FROM colaboradores WHERE codigo = ?", (filtros['codigo'],))
        else:
            return "Erro: Forneça o nome ou código do colaborador para editar."

        colaborador = cursor.fetchone()
        if not colaborador:
            return f"Erro: Colaborador não encontrado com os critérios fornecidos."

        campos_para_atualizar, params = [], []
        if 'nome_setor' in novos_dados:
            setor = conn.execute("SELECT id FROM setores WHERE nome_setor LIKE ?", (f"%{novos_dados['nome_setor']}%",)).fetchone()
            if not setor: return f"Erro: Setor '{novos_dados['nome_setor']}' não encontrado."
            campos_para_atualizar.append("setor_id = ?")
            params.append(setor['id'])
        
        if 'codigo' in novos_dados:
            campos_para_atualizar.append("codigo = ?")
            params.append(novos_dados['codigo'])

        if not campos_para_atualizar:
            return "Nenhuma alteração válida foi solicitada."

        query = f"UPDATE colaboradores SET {', '.join(campos_para_atualizar)} WHERE id = ?"
        params.append(colaborador['id'])
        
        cursor.execute(query, tuple(params))
        conn.commit()
        return f"Colaborador '{colaborador['nome_completo']}' atualizado com sucesso."
    except Exception as e:
        return f"Ocorreu um erro ao atualizar: {e}"
    finally:
        conn.close()

def executar_excluir_colaborador(filtros):
    """Exclui um colaborador de forma segura."""
    if not filtros or not filtros.get('codigo'):
        return "Erro: É necessário fornecer o código do colaborador para a exclusão."
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM colaboradores WHERE codigo = ?", (filtros['codigo'],))
        colaborador = cursor.fetchone()
        if not colaborador:
            return f"Erro: Colaborador com código '{filtros['codigo']}' não encontrado."

        cursor.execute("SELECT COUNT(id) FROM historico_movimentacoes WHERE colaborador_id = ?", (colaborador['id'],))
        if cursor.fetchone()[0] > 0:
            return f"Erro de segurança: Não é possível excluir o colaborador '{colaborador['nome_completo']}', pois ele possui um histórico de movimentações."

        cursor.execute("DELETE FROM colaboradores WHERE id = ?", (colaborador['id'],))
        conn.commit()
        return f"Colaborador '{colaborador['nome_completo']}' (código: {filtros['codigo']}) excluído com sucesso."
    except Exception as e:
        return f"Ocorreu um erro ao excluir: {e}"
    finally:
        conn.close()

# --- Lógica do Chatbot ---
schema = {
    "type": "OBJECT",
    "properties": {
        "acao": {"type": "STRING", "enum": ["iniciar_criacao", "fornecer_dado", "editar_colaborador", "excluir_colaborador", "pesquisar_aparelho", "pesquisar_movimentacoes", "limpar_chat", "logout", "saudacao", "desconhecido"]},
        "entidade": {"type": "STRING", "enum": ["colaborador", "aparelho", "conta_gmail"]},
        "dados": {"type": "OBJECT", "properties": {
            "valor_dado": {"type": "STRING"}, "nome_setor": {"type": "STRING"}, "codigo": {"type": "STRING"}
        }},
        "filtros": {"type": "OBJECT", "properties": {"nome_colaborador": {"type": "STRING"}, "numero_serie": {"type": "STRING"}, "data": {"type": "STRING"}, "codigo": {"type": "STRING"}}}
    }, "required": ["acao"]
}

async def get_flow_response(prompt, user_name, current_action=None):
    # ... (código da função de chamada à API omitido para brevidade) ...
    return {"acao": "desconhecido"}

def get_info_text():
    return """
    Olá! Sou o Flow. Veja como me pode usar:

    **1. Para Criar:**
    - Diga "criar colaborador", "criar aparelho" ou "criar conta gmail". Eu irei guiá-lo.

    **2. Para Pesquisar:**
    - "pesquisar aparelho do [nome]" ou "encontrar aparelho com n/s [número]".
    - "mostrar histórico do [nome]" ou "ver movimentações em [data AAAA-MM-DD]".

    **3. Para Editar:**
    - "altere o setor do [nome] para [novo setor]".
    - "mude o código do [nome] para [novo código]".

    **4. Para Excluir (com segurança):**
    - "exclua o colaborador com código [código]".
    - "remova o aparelho com n/s [número]".

    **5. Comandos do Chat:**
    - `#info`, `limpar chat`, `encerrar chat` ou `logout`.
    """

CAMPOS_CADASTRO = {
    "colaborador": ["codigo", "nome_completo", "cpf", "gmail", "nome_setor"],
    "aparelho": ["marca", "modelo", "numero_serie", "valor", "imei1", "imei2"],
    "conta_gmail": ["email", "senha", "telefone_recuperacao", "email_recuperacao", "nome_setor", "nome_colaborador"]
}

# --- Interface do Chatbot ---
st.markdown("""<div class="flow-title"><span class="icon">💬</span><h1><span class="text-chat">Converse com o </span><span class="text-flow">Flow</span></h1></div>""", unsafe_allow_html=True)
st.markdown("---")
st.info("Sou o Flow, seu assistente inteligente. Diga `#info` para ver os comandos, `limpar chat` para recomeçar ou `encerrar chat` para sair.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": f"Olá {st.session_state['user_name']}! Como posso ajudar?"}]
for key in ["pending_action", "conversa_em_andamento", "campo_para_corrigir", "entidade_em_correcao", "modo_correcao"]:
    if key not in st.session_state: st.session_state[key] = None
if "dados_recolhidos" not in st.session_state:
    st.session_state.dados_recolhidos = {}

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], pd.DataFrame):
            st.dataframe(message["content"], hide_index=True, use_container_width=True)
        else:
            st.markdown(message["content"], unsafe_allow_html=True)

def proximo_campo():
    entidade = st.session_state.conversa_em_andamento
    if not entidade: return None
    for campo in CAMPOS_CADASTRO[entidade]:
        if campo not in st.session_state.dados_recolhidos:
            return campo
    return None

def adicionar_mensagem(role, content):
    st.session_state.messages.append({"role": role, "content": content})
    with st.chat_message(role):
        if isinstance(content, pd.DataFrame):
            st.dataframe(content, hide_index=True, use_container_width=True)
        else:
            st.markdown(content, unsafe_allow_html=True)

def apresentar_resumo():
    entidade = st.session_state.get('conversa_em_andamento') or st.session_state.get('entidade_em_correcao')
    if not entidade:
        adicionar_mensagem("assistant", "Ocorreu um erro interno ao tentar apresentar o resumo.")
        return
    dados = st.session_state.dados_recolhidos
    resumo = f"Perfeito! Recolhi as informações. Por favor, confirme os dados para criar o **{entidade}**:\n"
    for key, value in dados.items():
        resumo += f"- **{key.replace('_', ' ').title()}:** {value}\n"
    adicionar_mensagem("assistant", resumo)
    st.session_state.pending_action = {"acao": f"criar_{entidade}", "dados": dados}
    st.session_state.conversa_em_andamento = None
    st.session_state.campo_para_corrigir = None
    st.session_state.entidade_em_correcao = None

if prompt := st.chat_input("Como posso ajudar?"):
    adicionar_mensagem("user", prompt)

    with st.spinner("A pensar..."):
        if st.session_state.campo_para_corrigir:
            campo = st.session_state.campo_para_corrigir
            st.session_state.dados_recolhidos[campo] = prompt
            st.session_state.campo_para_corrigir = None
            apresentar_resumo()
            st.rerun()
        elif st.session_state.conversa_em_andamento:
            campo_atual = proximo_campo()
            st.session_state.dados_recolhidos[campo_atual] = prompt
            proximo = proximo_campo()
            if proximo:
                adicionar_mensagem("assistant", f"Entendido. Agora, qual é o **{proximo.replace('_', ' ')}**?")
            else:
                apresentar_resumo()
                st.rerun()
        else:
            if prompt.strip().lower() == '#info':
                response_data = {"acao": "ajuda"}
            else:
                response_data = asyncio.run(get_flow_response(prompt, st.session_state['user_name']))
            
            acao = response_data.get('acao')
            
            if acao == 'iniciar_criacao':
                # ... (lógica de iniciar criação) ...
                pass
            elif acao in ['pesquisar_aparelho', 'pesquisar_movimentacoes']:
                # ... (lógica de pesquisa) ...
                pass
            elif acao in ['editar_colaborador', 'excluir_colaborador']:
                st.session_state.pending_action = response_data
                if acao == 'editar_colaborador':
                    filtros = response_data.get('filtros', {})
                    dados = response_data.get('dados', {})
                    response_content = f"Pretende alterar o colaborador identificado por **{filtros}** com os novos dados **{dados}**. Confirma?"
                    adicionar_mensagem("assistant", response_content)
                elif acao == 'excluir_colaborador':
                    filtros = response_data.get('filtros', {})
                    response_content = f"⚠️ **Atenção!** Tem a certeza de que deseja excluir o colaborador com os critérios **{filtros}**? Esta ação é irreversível."
                    adicionar_mensagem("assistant", response_content)
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
            else:
                erro = response_data.get("dados", {}).get("erro", "Não consegui entender o seu pedido. Diga `#info` para ver exemplos.")
                adicionar_mensagem("assistant", f"Desculpe, ocorreu um problema: {erro}")

if st.session_state.get('modo_correcao'):
    # ... (lógica de correção) ...
    pass

if st.session_state.pending_action and not st.session_state.modo_correcao:
    action_data = st.session_state.pending_action
    col1, col2, col3 = st.columns([1, 1, 5])
    with col1:
        if st.button("Sim, confirmo", type="primary"):
            resultado = ""
            acao_executar = action_data["acao"]
            dados_executar = action_data.get("dados")
            filtros_executar = action_data.get("filtros")
            
            if acao_executar == "criar_colaborador":
                resultado = executar_criar_colaborador(dados_executar)
            elif acao_executar == "criar_aparelho":
                resultado = executar_criar_aparelho(dados_executar)
            elif acao_executar == "criar_conta_gmail":
                resultado = executar_criar_conta_gmail(dados_executar)
            elif acao_executar == "editar_colaborador":
                resultado = executar_editar_colaborador(filtros_executar, dados_executar)
            elif acao_executar == "excluir_colaborador":
                resultado = executar_excluir_colaborador(filtros_executar)

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
        if "criar" in action_data["acao"]:
            if st.button("Corrigir uma informação"):
                st.session_state.dados_para_corrigir = action_data["dados"]
                st.session_state.dados_para_corrigir['_entidade_'] = action_data['acao'].split('_')[1]
                st.session_state.modo_correcao = True
                st.session_state.pending_action = None
                st.rerun()
