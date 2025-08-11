import streamlit as st
import sqlite3
from datetime import datetime
from fpdf import FPDF
from auth import show_login_form
import base64
import io

# --- Autenticação ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    show_login_form()
    st.stop()

# --- Logo da Mirasol em Base64 ---
LOGO_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAASwAAACACAYAAACx28soAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAARTSURBVHhe7d3/S9t3fcfxL9wN3Y1u0I2b3U2n053pZJrdcTqd6UwnO9Npd3fT6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9.png"

# --- Classe para gerar o PDF com Design ---
class PDF(FPDF):
    def header(self):
        try:
            image_data = base64.b64decode(LOGO_BASE64)
            image_file = io.BytesIO(image_data)
            self.image(image_file, x=10, y=8, w=50)
        except Exception as e:
            st.error(f"Erro ao carregar a logo: {e}")
            self.set_font('Arial', 'B', 10)
            self.cell(40, 10, 'LOGO', 1, 0, 'C')
        
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 51, 102) # Azul Mirasol
        self.cell(0, 10, 'TERMO DE RESPONSABILIDADE', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.set_text_color(227, 6, 19) # Vermelho Mirasol
        self.cell(0, 5, 'PROTOCOLO DE RECEBIMENTO E DEVOLUÇÃO DE SMARTPHONE', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'B', 8)
        self.cell(0, 5, 'BOAS PRÁTICAS', 0, 1, 'L')
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.multi_cell(0, 4, '- Mantenha seu aparelho na capa e com película, isso evita problemas com quedas e possíveis acidentes.\n- Carregue seu aparelho somente com o carregador original, isso mantem a vida útil da bateria por mais tempo.\n- Lembre-se que trata-se de um equipamento de trabalho, faça bom uso!', 0, 'L')
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def section_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, title, 1, 1, 'C', fill=True)
        self.set_text_color(0, 0, 0)

    def section_body(self, data):
        self.set_font('Arial', '', 10)
        for key, value in data.items():
            self.cell(95, 7, f" {key}: {value}", 1, 1 if 'CPF' in key or 'EMAIL' in key else 0)
        if len(data) % 2 != 0: self.ln()

# --- Funções do DB ---
def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

def carregar_setores():
    conn = get_db_connection()
    setores = conn.execute("SELECT nome_setor FROM setores ORDER BY nome_setor").fetchall()
    conn.close()
    return [s['nome_setor'] for s in setores]

def buscar_dados_termo(mov_id):
    conn = get_db_connection()
    dados = conn.execute("""
        SELECT
            c.nome_completo, c.cpf, s.nome_setor, c.gmail, c.codigo as codigo_colaborador,
            m.nome_marca, mo.nome_modelo, a.imei1, a.imei2,
            h.id as protocolo, h.data_movimentacao
        FROM historico_movimentacoes h
        JOIN colaboradores c ON h.colaborador_id = c.id
        JOIN setores s ON c.setor_id = s.id
        JOIN aparelhos a ON h.aparelho_id = a.id
        JOIN modelos mo ON a.modelo_id = mo.id
        JOIN marcas m ON mo.marca_id = m.id
        WHERE h.id = ?
    """, (mov_id,)).fetchone()
    conn.close()
    return dict(dados) if dados else None

def gerar_pdf_termo(dados, checklist_data):
    pdf = PDF()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(95, 7, f"CÓDIGO: {dados['protocolo']}", 1, 0, 'C')
    pdf.cell(95, 7, f"DATA: {dados['data_movimentacao']}", 1, 1, 'C')
    pdf.ln(5)

    pdf.section_title('DADOS DO COLABORADOR')
    pdf.section_body({'NOME': dados['nome_completo'], 'CPF': dados['cpf'], 'SETOR': dados['nome_setor'], 'EMAIL': dados['gmail']})
    pdf.ln(5)
    pdf.section_title('DADOS DO SMARTPHONE')
    pdf.section_body({'MARCA': dados['nome_marca'], 'MODELO': dados['nome_modelo'], 'IMEI 1': dados['imei1'], 'IMEI 2': dados['imei2']})
    pdf.ln(5)

    pdf.section_title('DOCUMENTAÇÃO')
    pdf.set_font('Arial', '', 8)
    texto_doc = "Declaro para os devidos fins que os materiais registrados nesta ficha encontram-se em meu poder para uso em minhas atividades, cabendo-me a responsabilidade por sua guarda e conservação... (Art. 462 CLT). Declaro estar ciente e de acordo com a utilização de meus dados pessoais neste documento, para fins de controle."
    pdf.multi_cell(0, 5, texto_doc, 1, 'J')
    pdf.ln(5)

    pdf.section_title('CHECKLIST DE RECEBIMENTO')
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(95, 6, 'ITEM', 1, 0, 'C')
    pdf.cell(47.5, 6, 'ENTREGA', 1, 0, 'C')
    pdf.cell(47.5, 6, 'ESTADO', 1, 1, 'C')
    pdf.set_font('Arial', '', 10)
    for item, detalhes in checklist_data.items():
        pdf.cell(95, 6, item, 1, 0)
        pdf.cell(47.5, 6, 'SIM' if detalhes['entregue'] else 'NÃO', 1, 0, 'C')
        pdf.cell(47.5, 6, detalhes['estado'], 1, 1, 'C')
    pdf.ln(15)

    pdf.cell(0, 10, '_________________________________________', 0, 1, 'C')
    pdf.cell(0, 5, dados['nome_completo'], 0, 1, 'C')
    
    return bytes(pdf.output())

# --- UI ---
st.title("Gerar Termo de Responsabilidade")
movimentacoes = get_db_connection().execute("SELECT h.id, h.data_movimentacao, a.numero_serie, c.nome_completo FROM historico_movimentacoes h JOIN aparelhos a ON h.aparelho_id = a.id JOIN colaboradores c ON h.colaborador_id = c.id WHERE h.status_id = (SELECT id FROM status WHERE nome_status = 'Em uso') ORDER BY h.data_movimentacao DESC").fetchall()

if not movimentacoes:
    st.info("Nenhuma movimentação de entrega encontrada para gerar termos.")
else:
    mov_dict = {f"{datetime.fromisoformat(m['data_movimentacao']).strftime('%d/%m/%Y')} - {m['nome_completo']} (S/N: {m['numero_serie']})": m['id'] for m in movimentacoes}
    mov_selecionada_str = st.selectbox("1. Selecione a entrega para gerar o termo:", options=mov_dict.keys())
    
    dados_termo = buscar_dados_termo(mov_dict[mov_selecionada_str])

    if dados_termo:
        st.markdown("---")
        st.subheader("2. Confira e Edite as Informações (Checkout)")
        
        with st.form("checkout_form"):
            dados_termo['protocolo'] = st.text_input("Código do Termo", value=dados_termo['protocolo'])
            dados_termo['data_movimentacao'] = st.text_input("Data", value=datetime.fromisoformat(dados_termo['data_movimentacao']).strftime('%d/%m/%Y'))
            
            st.markdown("##### Dados do Colaborador")
            dados_termo['nome_completo'] = st.text_input("Nome", value=dados_termo['nome_completo'])
            dados_termo['cpf'] = st.text_input("CPF", value=dados_termo['cpf'])
            
            # Carrega os setores e define o índice do setor atual
            setores_options = carregar_setores()
            current_sector_index = setores_options.index(dados_termo['nome_setor']) if dados_termo['nome_setor'] in setores_options else 0
            dados_termo['nome_setor'] = st.selectbox("Setor", options=setores_options, index=current_sector_index)
            
            dados_termo['gmail'] = st.text_input("Email", value=dados_termo['gmail'])

            st.markdown("##### Dados do Smartphone")
            dados_termo['imei1'] = st.text_input("IMEI 1", value=dados_termo['imei1'])
            dados_termo['imei2'] = st.text_input("IMEI 2", value=dados_termo['imei2'])
            
            st.markdown("---")
            st.subheader("3. Preencha o Checklist de Entrega")
            
            checklist_data = {}
            itens_checklist = ["Tela", "Carcaça", "Bateria", "Botões", "USB", "Chip", "Carregador", "Cabo USB", "Capa", "Película"]
            opcoes_estado = ["NOVO NA CAIXA", "BOM", "REGULAR", "AVARIADO"]
            
            for item in itens_checklist:
                col1, col2 = st.columns(2)
                entregue = col1.checkbox(f"{item}", value=True, key=f"entregue_{item}")
                estado = col2.selectbox(f"Estado de {item}", options=opcoes_estado, key=f"estado_{item}")
                checklist_data[item] = {'entregue': entregue, 'estado': estado}

            submitted = st.form_submit_button("Gerar Terme em PDF")
            if submitted:
                pdf_bytes = gerar_pdf_termo(dados_termo, checklist_data)
                st.session_state['pdf_gerado'] = pdf_bytes
                st.session_state['pdf_filename'] = f"Termo_{dados_termo['nome_completo'].replace(' ', '_')}.pdf"

if 'pdf_gerado' in st.session_state and st.session_state['pdf_gerado']:
    st.download_button(
        label="Baixar Termo em PDF",
        data=st.session_state['pdf_gerado'],
        file_name=st.session_state['pdf_filename'],
        mime="application/pdf"
    )
    st.session_state['pdf_gerado'] = None
