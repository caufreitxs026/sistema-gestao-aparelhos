import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import json
from auth import show_login_form

# --- Autenticação ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("app.py")

# --- NOVO: Configuração de Layout (Header e CSS) ---
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

# --- Barra Lateral (Agora contém tudo, incluindo o footer) ---
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


# --- Funções do DB ---
def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

def carregar_aparelhos_em_uso():
    """Carrega apenas os aparelhos que estão atualmente com status 'Em uso'."""
    conn = get_db_connection()
    aparelhos = conn.execute("""
        SELECT
            a.id as aparelho_id,
            a.numero_serie,
            mo.nome_modelo,
            ma.nome_marca,
            c.id as colaborador_id,
            c.nome_completo as colaborador_nome
        FROM aparelhos a
        JOIN historico_movimentacoes h ON a.id = h.aparelho_id
        JOIN (
            SELECT aparelho_id, MAX(data_movimentacao) as max_data
            FROM historico_movimentacoes
            GROUP BY aparelho_id
        ) hm ON h.aparelho_id = hm.aparelho_id AND h.data_movimentacao = hm.max_data
        JOIN colaboradores c ON h.colaborador_id = c.id
        JOIN status s ON a.status_id = s.id
        JOIN modelos mo ON a.modelo_id = mo.id
        JOIN marcas ma ON mo.marca_id = ma.id
        WHERE s.nome_status = 'Em uso'
        ORDER BY c.nome_completo
    """).fetchall()
    conn.close()
    return aparelhos

def processar_devolucao(aparelho_id, colaborador_id, checklist_data, destino_final, observacoes):
    """Processa a devolução, atualiza status e salva o histórico."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN TRANSACTION;")

        # Determina o novo status e se o colaborador será desvinculado
        if destino_final == "Devolver ao Estoque":
            novo_status_nome = "Em estoque"
            id_colaborador_final = None
            localizacao = "Estoque Interno"
        elif destino_final == "Enviar para Manutenção":
            novo_status_nome = "Em manutenção"
            id_colaborador_final = colaborador_id # Mantém o vínculo
            localizacao = "Triagem Manutenção"
        else: # Baixar/Inutilizar
            novo_status_nome = "Baixado/Inutilizado"
            id_colaborador_final = None
            localizacao = "Descarte"

        novo_status_id = cursor.execute("SELECT id FROM status WHERE nome_status = ?", (novo_status_nome,)).fetchone()[0]
        checklist_json = json.dumps(checklist_data)

        # 1. Insere o novo registo no histórico com os detalhes da devolução
        cursor.execute("""
            INSERT INTO historico_movimentacoes 
            (data_movimentacao, aparelho_id, colaborador_id, status_id, localizacao_atual, observacoes, checklist_devolucao)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (datetime.now(), aparelho_id, id_colaborador_final, novo_status_id, localizacao, observacoes, checklist_json))

        # 2. Atualiza o status principal do aparelho
        cursor.execute("UPDATE aparelhos SET status_id = ? WHERE id = ?", (novo_status_id, aparelho_id))

        conn.commit()
        st.success(f"Devolução processada com sucesso! Novo status do aparelho: {novo_status_nome}.")
        
        if destino_final == "Enviar para Manutenção":
            st.info("Aparelho encaminhado para o fluxo de manutenção. Vá para a página 'Manutenções' para abrir a Ordem de Serviço.")
        
        return True

    except Exception as e:
        conn.rollback()
        st.error(f"Ocorreu um erro ao processar a devolução: {e}")
        return False
    finally:
        conn.close()


# --- UI ---
st.title("Fluxo de Devolução e Triagem")
st.markdown("---")

# Etapa 1: Selecionar o aparelho
st.subheader("1. Selecione o Aparelho a Ser Devolvido")
aparelhos_em_uso = carregar_aparelhos_em_uso()

if not aparelhos_em_uso:
    st.info("Não há aparelhos com o status 'Em uso' para serem devolvidos no momento.")
else:
    aparelhos_dict = {
        f"{ap['colaborador_nome']} - {ap['nome_marca']} {ap['nome_modelo']} (S/N: {ap['numero_serie']})": ap
        for ap in aparelhos_em_uso
    }
    
    aparelho_selecionado_str = st.selectbox(
        "Selecione o aparelho e colaborador:",
        options=aparelhos_dict.keys(),
        help="Clique na lista e comece a digitar para pesquisar."
    )
    
    aparelho_selecionado_data = aparelhos_dict[aparelho_selecionado_str]
    aparelho_id = aparelho_selecionado_data['aparelho_id']
    colaborador_id = aparelho_selecionado_data['colaborador_id']

    st.markdown("---")

    # Etapa 2 e 3: Checklist e Decisão
    st.subheader("2. Realize a Inspeção e Decida o Destino Final")
    with st.form("form_devolucao"):
        st.markdown("##### Checklist de Devolução")
        
        checklist_data = {}
        itens_checklist = ["Tela", "Carcaça", "Bateria", "Botões", "USB", "Chip", "Carregador", "Cabo USB", "Capa", "Película"]
        opcoes_estado = ["Bom", "Riscado", "Quebrado", "Faltando"]
        
        for item in itens_checklist:
            col1, col2 = st.columns(2)
            entregue = col1.checkbox(f"{item}", value=True, key=f"entregue_{item}")
            estado = col2.selectbox(f"Estado de {item}", options=opcoes_estado, key=f"estado_{item}")
            checklist_data[item] = {'entregue': entregue, 'estado': estado}
        
        observacoes = st.text_area("Observações Gerais da Devolução", placeholder="Ex: Tela com risco profundo no canto superior direito.")
        
        st.markdown("---")
        st.markdown("##### Destino Final do Aparelho")
        destino_final = st.radio(
            "Selecione o destino do aparelho após a inspeção:",
            ["Devolver ao Estoque", "Enviar para Manutenção", "Baixar/Inutilizar"],
            horizontal=True
        )

        submitted = st.form_submit_button("Processar Devolução")
        if submitted:
            if processar_devolucao(aparelho_id, colaborador_id, checklist_data, destino_final, observacoes):
                st.rerun()

