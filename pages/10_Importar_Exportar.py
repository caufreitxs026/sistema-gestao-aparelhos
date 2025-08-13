import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
import io

# --- Autenticação ---
# Se o utilizador não estiver logado, redireciona para a página principal de login
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("app.py")

# --- NOVO: Configuração de Layout (Header, Footer e CSS) ---
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
            <a href="https://instagram.com/Caufreitxs" target="_blank" title="Instagram">
                <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/brands/instagram.svg">
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

def get_foreign_key_map(table_name, column_name, key_column='id'):
    """Cria um dicionário mapeando nomes a IDs para chaves estrangeiras."""
    conn = get_db_connection()
    query = f"SELECT {key_column}, {column_name} FROM {table_name}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return pd.Series(df[key_column].values, index=df[column_name]).to_dict()

# --- UI ---
st.title("Importar e Exportar Dados em Lote")
st.markdown("---")

st.info("Selecione a tabela, baixe o modelo, preencha com seus dados e faça o upload para importar em massa.")

tabela_selecionada = st.selectbox(
    "1. Selecione a tabela para importar/exportar dados:",
    ["Colaboradores", "Aparelhos", "Marcas", "Contas Gmail"]
)

# --- LÓGICA PARA COLABORADORES ---
if tabela_selecionada == "Colaboradores":
    st.markdown("---")
    st.subheader("Importar Novos Colaboradores")

    # 2. Baixar Planilha Modelo
    setores_map = get_foreign_key_map("setores", "nome_setor")
    exemplo_setor = list(setores_map.keys())[0] if setores_map else "TI"
    df_modelo = pd.DataFrame({
        "codigo": ["1001"], "nome_completo": ["Nome Sobrenome Exemplo"],
        "cpf": ["12345678900"], "gmail": ["exemplo.email@gmail.com"],
        "nome_setor": [exemplo_setor]
    })
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_modelo.to_excel(writer, index=False, sheet_name='Colaboradores')
    
    st.download_button(label="Baixar Planilha Modelo", data=output.getvalue(),
                       file_name="modelo_colaboradores.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # 3. Fazer Upload da Planilha Preenchida
    uploaded_file = st.file_uploader("Escolha a planilha de Colaboradores (.xlsx)", type="xlsx", key="upload_colab")
    if uploaded_file:
        try:
            df_upload = pd.read_excel(uploaded_file)
            st.dataframe(df_upload)

            if st.button("Importar Dados dos Colaboradores"):
                conn = get_db_connection()
                cursor = conn.cursor()
                sucesso = 0
                erros = 0
                
                with st.spinner("Importando dados... Por favor, aguarde."):
                    for index, row in df_upload.iterrows():
                        try:
                            setor_id = setores_map.get(row['nome_setor'])
                            if setor_id is None:
                                st.warning(f"Linha {index+2}: Setor '{row['nome_setor']}' não encontrado. Pulando registo.")
                                erros += 1
                                continue

                            cursor.execute(
                                "INSERT INTO colaboradores (codigo, nome_completo, cpf, gmail, setor_id, data_cadastro) VALUES (?, ?, ?, ?, ?, ?)",
                                (str(row['codigo']), row['nome_completo'], str(row['cpf']), row['gmail'], setor_id, date.today())
                            )
                            sucesso += 1
                        except sqlite3.IntegrityError:
                            st.warning(f"Linha {index+2}: Colaborador com código '{row['codigo']}' ou CPF '{row['cpf']}' já existe. Pulando registo.")
                            erros += 1
                        except Exception as e:
                            st.error(f"Linha {index+2}: Erro inesperado ao importar - {e}. Pulando registo.")
                            erros += 1
                
                conn.commit()
                conn.close()

                st.success(f"Importação concluída! {sucesso} registos importados com sucesso.")
                if erros > 0:
                    st.error(f"{erros} registos continham erros e não foram importados.")

        except Exception as e:
            st.error(f"Ocorreu um erro ao ler o ficheiro: {e}")

# --- LÓGICA PARA APARELHOS ---
elif tabela_selecionada == "Aparelhos":
    st.markdown("---")
    st.subheader("Importar Novos Aparelhos")

    # 2. Baixar Planilha Modelo
    conn = get_db_connection()
    modelos_df = pd.read_sql_query("SELECT mo.id, ma.nome_marca || ' - ' || mo.nome_modelo as nome_completo FROM modelos mo JOIN marcas ma ON mo.marca_id = ma.id", conn)
    status_df = pd.read_sql_query("SELECT nome_status FROM status", conn)
    conn.close()
    
    exemplo_modelo = modelos_df['nome_completo'].iloc[0] if not modelos_df.empty else "Samsung - Galaxy S24"
    exemplo_status = status_df['nome_status'].iloc[0] if not status_df.empty else "Em estoque"

    df_modelo = pd.DataFrame({
        "numero_serie": ["ABC123456789"], "imei1": ["111111111111111"], "imei2": ["222222222222222"],
        "valor": [4999.90], "modelo_completo": [exemplo_modelo], "status_inicial": [exemplo_status]
    })
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_modelo.to_excel(writer, index=False, sheet_name='Aparelhos')
    
    st.download_button(label="Baixar Planilha Modelo", data=output.getvalue(),
                       file_name="modelo_aparelhos.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # 3. Fazer Upload da Planilha Preenchida
    uploaded_file = st.file_uploader("Escolha a planilha de Aparelhos (.xlsx)", type="xlsx", key="upload_aparelho")
    if uploaded_file:
        try:
            df_upload = pd.read_excel(uploaded_file)
            st.dataframe(df_upload)

            if st.button("Importar Dados dos Aparelhos"):
                conn = get_db_connection()
                cursor = conn.cursor()
                modelos_map = get_foreign_key_map("modelos", "ma.nome_marca || ' - ' || mo.nome_modelo", key_column="mo.id")
                status_map = get_foreign_key_map("status", "nome_status")
                sucesso = 0
                erros = 0

                with st.spinner("Importando dados... Por favor, aguarde."):
                    for index, row in df_upload.iterrows():
                        try:
                            modelo_id = modelos_map.get(row['modelo_completo'])
                            status_id = status_map.get(row['status_inicial'])
                            
                            if not all([modelo_id, status_id]):
                                st.warning(f"Linha {index+2}: Modelo '{row['modelo_completo']}' ou Status '{row['status_inicial']}' inválido. Pulando registo.")
                                erros += 1
                                continue
                            
                            cursor.execute("BEGIN TRANSACTION;")
                            cursor.execute(
                                "INSERT INTO aparelhos (numero_serie, imei1, imei2, valor, modelo_id, status_id, data_cadastro) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (str(row['numero_serie']), str(row['imei1']), str(row['imei2']), float(row['valor']), modelo_id, status_id, date.today())
                            )
                            aparelho_id = cursor.lastrowid
                            cursor.execute(
                                "INSERT INTO historico_movimentacoes (data_movimentacao, aparelho_id, status_id, localizacao_atual, observacoes) VALUES (?, ?, ?, ?, ?)",
                                (datetime.now(), aparelho_id, status_id, "Estoque Interno", "Entrada inicial via importação de planilha.")
                            )
                            conn.commit()
                            sucesso += 1
                        except sqlite3.IntegrityError:
                            conn.rollback()
                            st.warning(f"Linha {index+2}: Aparelho com N/S '{row['numero_serie']}' já existe. Pulando registo.")
                            erros += 1
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Linha {index+2}: Erro inesperado ao importar - {e}. Pulando registo.")
                            erros += 1
                
                conn.close()
                st.success(f"Importação concluída! {sucesso} registos importados com sucesso.")
                if erros > 0:
                    st.error(f"{erros} registos continham erros e não foram importados.")

        except Exception as e:
            st.error(f"Ocorreu um erro ao ler o ficheiro: {e}")

# --- LÓGICA PARA MARCAS ---
elif tabela_selecionada == "Marcas":
    st.markdown("---")
    st.subheader("Importar Novas Marcas")

    # 2. Baixar Planilha Modelo
    df_modelo = pd.DataFrame({"nome_marca": ["Nome da Marca Exemplo"]})
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_modelo.to_excel(writer, index=False, sheet_name='Marcas')
    
    st.download_button(label="Baixar Planilha Modelo", data=output.getvalue(),
                       file_name="modelo_marcas.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # 3. Fazer Upload da Planilha Preenchida
    uploaded_file = st.file_uploader("Escolha a planilha de Marcas (.xlsx)", type="xlsx", key="upload_marca")
    if uploaded_file:
        try:
            df_upload = pd.read_excel(uploaded_file)
            st.dataframe(df_upload)

            if st.button("Importar Dados de Marcas"):
                conn = get_db_connection()
                cursor = conn.cursor()
                sucesso = 0
                erros = 0

                with st.spinner("Importando dados..."):
                    for index, row in df_upload.iterrows():
                        try:
                            cursor.execute("INSERT INTO marcas (nome_marca) VALUES (?)", (row['nome_marca'],))
                            sucesso += 1
                        except sqlite3.IntegrityError:
                            st.warning(f"Linha {index+2}: Marca '{row['nome_marca']}' já existe. Pulando registo.")
                            erros += 1
                        except Exception as e:
                            st.error(f"Linha {index+2}: Erro inesperado - {e}. Pulando registo.")
                            erros += 1
                
                conn.commit()
                conn.close()
                st.success(f"Importação concluída! {sucesso} registos importados com sucesso.")
                if erros > 0:
                    st.error(f"{erros} registos continham erros e não foram importados.")

        except Exception as e:
            st.error(f"Ocorreu um erro ao ler o ficheiro: {e}")

# --- LÓGICA PARA CONTAS GMAIL ---
elif tabela_selecionada == "Contas Gmail":
    st.markdown("---")
    st.subheader("Importar Novas Contas Gmail")

    # 2. Baixar Planilha Modelo
    setores_map = get_foreign_key_map("setores", "nome_setor")
    colaboradores_map = get_foreign_key_map("colaboradores", "nome_completo")
    exemplo_setor = list(setores_map.keys())[0] if setores_map else "TI"
    exemplo_colaborador = list(colaboradores_map.keys())[0] if colaboradores_map else ""

    df_modelo = pd.DataFrame({
        "email": ["conta.exemplo@gmail.com"], "senha": ["senhaforte123"],
        "telefone_recuperacao": ["11999998888"], "email_recuperacao": ["recuperacao@email.com"],
        "nome_setor": [exemplo_setor], "nome_colaborador": [exemplo_colaborador]
    })
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_modelo.to_excel(writer, index=False, sheet_name='Contas_Gmail')
    
    st.download_button(label="Baixar Planilha Modelo", data=output.getvalue(),
                       file_name="modelo_contas_gmail.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # 3. Fazer Upload da Planilha Preenchida
    uploaded_file = st.file_uploader("Escolha a planilha de Contas Gmail (.xlsx)", type="xlsx", key="upload_gmail")
    if uploaded_file:
        try:
            df_upload = pd.read_excel(uploaded_file)
            st.dataframe(df_upload)

            if st.button("Importar Dados de Contas Gmail"):
                conn = get_db_connection()
                cursor = conn.cursor()
                sucesso = 0
                erros = 0

                with st.spinner("Importando dados..."):
                    for index, row in df_upload.iterrows():
                        try:
                            setor_id = setores_map.get(row['nome_setor'])
                            colaborador_id = colaboradores_map.get(row['nome_colaborador']) if pd.notna(row['nome_colaborador']) else None
                            
                            cursor.execute(
                                "INSERT INTO contas_gmail (email, senha, telefone_recuperacao, email_recuperacao, setor_id, colaborador_id) VALUES (?, ?, ?, ?, ?, ?)",
                                (row['email'], row['senha'], str(row['telefone_recuperacao']), row['email_recuperacao'], setor_id, colaborador_id)
                            )
                            sucesso += 1
                        except sqlite3.IntegrityError:
                            st.warning(f"Linha {index+2}: E-mail '{row['email']}' já existe. Pulando registo.")
                            erros += 1
                        except Exception as e:
                            st.error(f"Linha {index+2}: Erro inesperado - {e}. Pulando registo.")
                            erros += 1
                
                conn.commit()
                conn.close()
                st.success(f"Importação concluída! {sucesso} registos importados com sucesso.")
                if erros > 0:
                    st.error(f"{erros} registos continham erros e não foram importados.")

        except Exception as e:
            st.error(f"Ocorreu um erro ao ler o ficheiro: {e}")


