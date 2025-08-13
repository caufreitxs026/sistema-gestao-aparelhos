import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
from auth import show_login_form

# --- Autenticação ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("app.py")

# --- Funções do DB ---
def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

def carregar_aparelhos_para_manutencao():
    conn = get_db_connection()
    aparelhos = conn.execute("""
        WITH UltimoHistorico AS (
            SELECT
                aparelho_id, colaborador_id,
                ROW_NUMBER() OVER(PARTITION BY aparelho_id ORDER BY data_movimentacao DESC) as rn
            FROM historico_movimentacoes
        )
        SELECT
            a.id, a.numero_serie, mo.nome_modelo, ma.nome_marca,
            c.nome_completo as ultimo_colaborador
        FROM aparelhos a
        JOIN modelos mo ON a.modelo_id = mo.id
        JOIN marcas ma ON mo.marca_id = ma.id
        LEFT JOIN UltimoHistorico uh ON a.id = uh.aparelho_id AND uh.rn = 1
        LEFT JOIN colaboradores c ON uh.colaborador_id = c.id
        WHERE a.status_id != (SELECT id FROM status WHERE nome_status = 'Em manutenção')
          AND a.status_id != (SELECT id FROM status WHERE nome_status = 'Baixado/Inutilizado')
        ORDER BY ma.nome_marca, mo.nome_modelo
    """).fetchall()
    conn.close()
    return aparelhos

def abrir_ordem_servico(aparelho_id, fornecedor, defeito):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION;")
        ultimo_colaborador_id = cursor.execute("SELECT colaborador_id FROM historico_movimentacoes WHERE aparelho_id = ? ORDER BY data_movimentacao DESC LIMIT 1", (aparelho_id,)).fetchone()
        status_manutencao_id = cursor.execute("SELECT id FROM status WHERE nome_status = 'Em manutenção'").fetchone()[0]
        cursor.execute("INSERT INTO manutencoes (aparelho_id, colaborador_id_no_envio, fornecedor, data_envio, defeito_reportado, status_manutencao) VALUES (?, ?, ?, ?, ?, ?)",
                       (aparelho_id, ultimo_colaborador_id[0] if ultimo_colaborador_id else None, fornecedor, date.today(), defeito, 'Em Andamento'))
        cursor.execute("UPDATE aparelhos SET status_id = ? WHERE id = ?", (status_manutencao_id, aparelho_id))
        cursor.execute("INSERT INTO historico_movimentacoes (data_movimentacao, aparelho_id, status_id, localizacao_atual, observacoes) VALUES (?, ?, ?, ?, ?)",
                       (datetime.now(), aparelho_id, status_manutencao_id, f"Assistência: {fornecedor}", f"Defeito: {defeito}"))
        conn.commit()
        st.success("Ordem de Serviço aberta e aparelho enviado para manutenção!")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao abrir a Ordem de Serviço: {e}")
    finally:
        conn.close()

def carregar_manutencoes_em_andamento():
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT m.id, a.numero_serie, mo.nome_modelo, m.fornecedor, m.data_envio, m.defeito_reportado
        FROM manutencoes m
        JOIN aparelhos a ON m.aparelho_id = a.id
        JOIN modelos mo ON a.modelo_id = mo.id
        WHERE m.status_manutencao = 'Em Andamento'
        ORDER BY m.data_envio ASC
    """, conn)
    conn.close()
    return df

def fechar_ordem_servico(manutencao_id, solucao, custo, novo_status_nome):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION;")
        aparelho_id = cursor.execute("SELECT aparelho_id FROM manutencoes WHERE id = ?", (manutencao_id,)).fetchone()[0]
        novo_status_id = cursor.execute("SELECT id FROM status WHERE nome_status = ?", (novo_status_nome,)).fetchone()[0]
        status_manutencao = 'Concluída' if novo_status_nome == 'Em estoque' else 'Sem Reparo'
        
        cursor.execute("""
            UPDATE manutencoes 
            SET data_retorno = ?, solucao_aplicada = ?, custo_reparo = ?, status_manutencao = ?
            WHERE id = ?
        """, (date.today(), solucao, custo, status_manutencao, manutencao_id))
        
        cursor.execute("UPDATE aparelhos SET status_id = ? WHERE id = ?", (novo_status_id, aparelho_id))
        
        cursor.execute("""
            INSERT INTO historico_movimentacoes (data_movimentacao, aparelho_id, status_id, localizacao_atual, observacoes)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now(), aparelho_id, novo_status_id, "Estoque Interno", f"Retorno da manutenção. Solução: {solucao}. Custo: R${custo}"))
        
        conn.commit()
        st.success("Ordem de Serviço fechada com sucesso!")
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao fechar a Ordem de Serviço: {e}")
    finally:
        conn.close()

def atualizar_manutencao(manutencao_id, fornecedor, defeito):
    conn = get_db_connection()
    try:
        conn.execute("UPDATE manutencoes SET fornecedor = ?, defeito_reportado = ? WHERE id = ?", (fornecedor, defeito, manutencao_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar manutenção: {e}")
        return False
    finally:
        conn.close()

# --- UI ---
st.title("Fluxo de Manutenção")
st.markdown("---")

tab1, tab2 = st.tabs(["Abrir Ordem de Serviço", "Acompanhar e Fechar O.S."])

with tab1:
    st.subheader("1. Enviar Aparelho para Manutenção")
    aparelhos_list = carregar_aparelhos_para_manutencao()
    
    filtro_aparelho_manut = st.text_input("Pesquisar Aparelho", key="filtro_manut_abrir")
    
    aparelhos_dict = {f"{ap['nome_marca']} {ap['nome_modelo']} (S/N: {ap['numero_serie']}) - [Com: {ap['ultimo_colaborador'] or 'Ninguém'}]": ap['id'] for ap in aparelhos_list}
    opcoes_filtradas_abrir = {k: v for k, v in aparelhos_dict.items() if filtro_aparelho_manut.lower() in k.lower()}

    if not opcoes_filtradas_abrir:
        st.info("Nenhum aparelho disponível para enviar para manutenção (ou correspondente à pesquisa).")
    else:
        with st.form("form_nova_os"):
            aparelho_selecionado_str = st.selectbox("Selecione o Aparelho*", options=opcoes_filtradas_abrir.keys())
            fornecedor = st.text_input("Fornecedor / Assistência Técnica*")
            defeito = st.text_area("Defeito Reportado*")
            if st.form_submit_button("Abrir Ordem de Serviço"):
                if not all([aparelho_selecionado_str, fornecedor, defeito]):
                    st.error("Todos os campos são obrigatórios.")
                else:
                    aparelho_id = opcoes_filtradas_abrir[aparelho_selecionado_str]
                    abrir_ordem_servico(aparelho_id, fornecedor, defeito)
                    st.rerun()

with tab2:
    st.subheader("2. Ordens de Serviço em Andamento")
    manutencoes_df = carregar_manutencoes_em_andamento()

    with st.expander("Ver e Editar Ordens de Serviço em Andamento", expanded=True):
        if manutencoes_df.empty:
            st.info("Nenhuma ordem de serviço em andamento no momento.")
        else:
            edited_df = st.data_editor(
                manutencoes_df,
                column_config={
                    "id": st.column_config.NumberColumn("O.S. Nº", disabled=True),
                    "numero_serie": st.column_config.TextColumn("N/S", disabled=True),
                    "nome_modelo": st.column_config.TextColumn("Modelo", disabled=True),
                    "fornecedor": st.column_config.TextColumn("Fornecedor", required=True),
                    "data_envio": st.column_config.DateColumn("Data Envio", disabled=True),
                    "defeito_reportado": st.column_config.TextColumn("Defeito Reportado", required=True),
                },
                hide_index=True, key="manutencoes_editor"
            )
            if st.button("Salvar Alterações nas O.S."):
                for index, row in edited_df.iterrows():
                    original_row = manutencoes_df.loc[index]
                    if not row.equals(original_row):
                        if atualizar_manutencao(row['id'], row['fornecedor'], row['defeito_reportado']):
                            st.toast(f"O.S. Nº {row['id']} atualizada!", icon="✅")
                st.rerun()

    st.markdown("---")
    st.subheader("3. Fechar Ordem de Serviço")
    
    if manutencoes_df.empty:
        st.info("Nenhuma O.S. para fechar.")
    else:
        with st.form("form_fechar_os"):
            filtro_os_fechar = st.text_input("Pesquisar O.S. (por N/S ou modelo)", key="filtro_manut_fechar")
            os_dict = {f"O.S. Nº {row['id']} - {row['nome_modelo']} (S/N: {row['numero_serie']})": row['id'] for index, row in manutencoes_df.iterrows()}
            opcoes_filtradas_fechar = {k: v for k, v in os_dict.items() if filtro_os_fechar.lower() in k.lower()}

            os_selecionada_str = st.selectbox("Selecione a Ordem de Serviço para fechar*", options=opcoes_filtradas_fechar.keys())
            solucao = st.text_area("Solução Aplicada / Laudo Técnico*")
            custo = st.number_input("Custo do Reparo (R$)", min_value=0.0, format="%.2f")
            novo_status_final = st.selectbox("Status Final do Aparelho*", ["Em estoque", "Baixado/Inutilizado"])

            if st.form_submit_button("Fechar Ordem de Serviço"):
                if not all([os_selecionada_str, solucao]):
                    st.error("Ordem de Serviço e Solução são campos obrigatórios.")
                else:
                    os_id = opcoes_filtradas_fechar[os_selecionada_str]
                    fechar_ordem_servico(os_id, solucao, custo, novo_status_final)
                    st.rerun()
