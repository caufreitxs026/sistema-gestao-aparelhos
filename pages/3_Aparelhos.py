import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from auth import show_login_form

# --- Verificação de Autenticação ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("app.py")

# --- Configurações da Página (Movido para o topo) ---
st.set_page_config(page_title="Gestão de Aparelhos", layout="wide")

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

# --- Conteúdo Principal da Página ---
st.title("Gestão de Aparelhos")
st.markdown("---")

# --- Funções de Banco de Dados ---

def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

def carregar_dados_para_selects():
    conn = get_db_connection()
    modelos = conn.execute("""
        SELECT m.id, m.nome_modelo, ma.nome_marca 
        FROM modelos m 
        JOIN marcas ma ON m.marca_id = ma.id 
        ORDER BY ma.nome_marca, m.nome_modelo
    """).fetchall()
    status = conn.execute("SELECT id, nome_status FROM status ORDER BY nome_status").fetchall()
    conn.close()
    return modelos, status

def adicionar_aparelho_e_historico(serie, imei1, imei2, valor, modelo_id, status_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    data_hoje = date.today()
    try:
        cursor.execute("BEGIN TRANSACTION;")
        cursor.execute(
            "INSERT INTO aparelhos (numero_serie, imei1, imei2, valor, modelo_id, status_id, data_cadastro) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (serie, imei1, imei2, valor, modelo_id, status_id, data_hoje)
        )
        aparelho_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO historico_movimentacoes (data_movimentacao, aparelho_id, status_id, localizacao_atual, observacoes) VALUES (?, ?, ?, ?, ?)",
            (date.today(), aparelho_id, status_id, "Estoque Interno", "Entrada inicial no sistema.")
        )
        conn.commit()
        st.success(f"Aparelho N/S '{serie}' cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        conn.rollback()
        st.error(f"O aparelho com Número de Série '{serie}' já existe.")
    except Exception as e:
        conn.rollback()
        st.error(f"Ocorreu um erro: {e}")
    finally:
        conn.close()

def carregar_inventario_completo(order_by="a.data_cadastro DESC"):
    """
    Carrega uma visão completa do inventário, incluindo o responsável atual e permitindo ordenação.
    """
    conn = get_db_connection()
    query = f"""
        WITH UltimoResponsavel AS (
            SELECT
                h.aparelho_id,
                h.colaborador_id,
                ROW_NUMBER() OVER(PARTITION BY h.aparelho_id ORDER BY h.data_movimentacao DESC) as rn
            FROM historico_movimentacoes h
        )
        SELECT 
            a.id,
            a.numero_serie,
            ma.nome_marca || ' - ' || mo.nome_modelo as modelo_completo,
            s.nome_status,
            c.nome_completo as responsavel_atual,
            a.valor,
            a.imei1,
            a.imei2,
            a.data_cadastro
        FROM aparelhos a
        LEFT JOIN modelos mo ON a.modelo_id = mo.id
        LEFT JOIN marcas ma ON mo.marca_id = ma.id
        LEFT JOIN status s ON a.status_id = s.id
        LEFT JOIN UltimoResponsavel ur ON a.id = ur.aparelho_id AND ur.rn = 1
        LEFT JOIN colaboradores c ON ur.colaborador_id = c.id
        ORDER BY {order_by}
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def atualizar_aparelho_completo(aparelho_id, serie, imei1, imei2, valor, modelo_id):
    """Atualiza todos os campos editáveis de um aparelho."""
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE aparelhos SET numero_serie = ?, imei1 = ?, imei2 = ?, valor = ?, modelo_id = ? WHERE id = ?",
            (serie, imei1, imei2, valor, modelo_id, aparelho_id)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        st.error(f"Erro: O Número de Série '{serie}' já pertence a outro aparelho.")
        return False
    except Exception as e:
        st.error(f"Erro ao atualizar o aparelho ID {aparelho_id}: {e}")
        return False

def excluir_aparelho(aparelho_id):
    """Exclui um aparelho do banco de dados."""
    try:
        conn = get_db_connection()
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("DELETE FROM aparelhos WHERE id = ?", (aparelho_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        st.error(f"Erro: Não é possível excluir o aparelho ID {aparelho_id}, pois ele possui um histórico de movimentações ou manutenções.")
        return False
    except Exception as e:
        st.error(f"Erro ao excluir o aparelho ID {aparelho_id}: {e}")
        return False

# --- Interface do Usuário ---

modelos_list, status_list = carregar_dados_para_selects()
modelos_dict = {f"{m['nome_marca']} - {m['nome_modelo']}": m['id'] for m in modelos_list}

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Adicionar Novo Aparelho")
    with st.form("form_novo_aparelho", clear_on_submit=True):
        novo_serie = st.text_input("Número de Série*")
        
        modelo_selecionado_str = st.selectbox(
            "Modelo*",
            options=modelos_dict.keys(),
            help="Clique na lista e comece a digitar para pesquisar."
        )
        
        novo_imei1 = st.text_input("IMEI 1")
        novo_imei2 = st.text_input("IMEI 2")
        novo_valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        status_dict = {s['nome_status']: s['id'] for s in status_list}
        status_selecionado_str = st.selectbox("Status Inicial*", options=status_dict.keys(), index=0)

        if st.form_submit_button("Adicionar Aparelho"):
            if not novo_serie or not modelo_selecionado_str:
                st.error("Número de Série e Modelo são campos obrigatórios.")
            else:
                modelo_id = modelos_dict[modelo_selecionado_str]
                status_id = status_dict[status_selecionado_str]
                adicionar_aparelho_e_historico(novo_serie, novo_imei1, novo_imei2, novo_valor, modelo_id, status_id)

with col2:
    with st.expander("Ver, Editar e Excluir Inventário de Aparelhos", expanded=True):
        
        # --- NOVO: Caixa de seleção para ordenação ---
        sort_options = {
            "Data de Entrada (Mais Recente)": "a.data_cadastro DESC",
            "Número de Série (A-Z)": "a.numero_serie ASC",
            "Modelo (A-Z)": "modelo_completo ASC",
            "Status (A-Z)": "s.nome_status ASC",
            "Responsável (A-Z)": "responsavel_atual ASC"
        }
        sort_selection = st.selectbox("Organizar por:", options=sort_options.keys())

        # Carrega os dados com a ordenação selecionada
        inventario_df = carregar_inventario_completo(order_by=sort_options[sort_selection])
        
        edited_df = st.data_editor(
            inventario_df,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "numero_serie": st.column_config.TextColumn("N/S", required=True),
                "modelo_completo": st.column_config.SelectboxColumn(
                    "Modelo",
                    options=modelos_dict.keys(),
                    required=True
                ),
                "nome_status": st.column_config.TextColumn("Status Atual", disabled=True),
                "responsavel_atual": st.column_config.TextColumn("Responsável Atual", disabled=True),
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", required=True),
                "imei1": st.column_config.TextColumn("IMEI 1"),
                "imei2": st.column_config.TextColumn("IMEI 2"),
                "data_cadastro": st.column_config.DateColumn("Data de Entrada", disabled=True),
            },
            hide_index=True,
            num_rows="dynamic", # Permite adicionar e excluir linhas
            key="aparelhos_editor"
        )
        
        if st.button("Salvar Alterações"):
            # Lógica para Exclusão
            deleted_ids = set(inventario_df['id']) - set(edited_df['id'])
            for aparelho_id in deleted_ids:
                if excluir_aparelho(aparelho_id):
                    st.toast(f"Aparelho ID {aparelho_id} excluído!", icon="🗑️")

            # Lógica para Atualização
            for index, row in edited_df.iterrows():
                if index < len(inventario_df): # Apenas verifica linhas existentes
                    original_row = inventario_df.loc[index]
                    if not row.equals(original_row):
                        aparelho_id = row['id']
                        novo_serie = row['numero_serie']
                        novo_imei1 = row['imei1']
                        novo_imei2 = row['imei2']
                        novo_valor = row['valor']
                        novo_modelo_id = modelos_dict[row['modelo_completo']]
                        
                        if atualizar_aparelho_completo(aparelho_id, novo_serie, novo_imei1, novo_imei2, novo_valor, novo_modelo_id):
                            st.toast(f"Aparelho N/S '{row['numero_serie']}' atualizado!", icon="✅")
            st.rerun()
