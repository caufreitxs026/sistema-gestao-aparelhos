import streamlit as st
import sqlite3
from datetime import datetime
from fpdf import FPDF
from auth import show_login_form
import base64
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
            <a href="https://linkedin.com/in/cauafreitas" target="_blank" title="LinkedIn">
                <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/brands/linkedin.svg">
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )


# --- Logo da Mirasol em Base64 ---
LOGO_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAASwAAACACAYAAACx28soAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAARTSURBVHhe7d3/S9t3fcfxL9wN3Y1u0I2b3U2n053pZJrdcTqd6UwnO9Npd3fT6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9PpdDqd6UwnO9.png"

# --- Classe para gerar o PDF com Novo Design ---
class PDF(FPDF):
    def header(self):
        try:
            image_data = base64.b64decode(LOGO_BASE64)
            image_file = io.BytesIO(image_data)
            self.image(image_file, x=10, y=8, w=50)
        except Exception:
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
        self.cell(0, 8, title, 0, 1, 'L', fill=True)
        self.ln(2)

    def draw_line(self):
        self.set_draw_color(220, 220, 220) # Cinza claro
        self.cell(0, 0, '', 'T', 1)
        self.ln(2)

    def info_line(self, label, value):
        self.set_font('Arial', 'B', 10)
        self.cell(30, 7, f" {label}:", 0, 0)
        self.set_font('Arial', '', 10)
        self.cell(0, 7, f" {value}", 0, 1)

# --- Funções do DB ---
def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

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
    pdf.info_line('NOME', dados['nome_completo'])
    pdf.info_line('CPF', dados['cpf'])
    pdf.info_line('SETOR', dados['nome_setor'])
    pdf.info_line('EMAIL', dados['gmail'])
    pdf.ln(5)

    pdf.section_title('DADOS DO SMARTPHONE')
    pdf.info_line('MARCA', dados['nome_marca'])
    pdf.info_line('MODELO', dados['nome_modelo'])
    pdf.info_line('IMEI 1', dados['imei1'])
    pdf.info_line('IMEI 2', dados['imei2'])
    pdf.ln(5)

    pdf.section_title('DOCUMENTAÇÃO')
    pdf.set_font('Arial', '', 8)
    texto_doc = "Declaro para os devidos fins que os materiais registrados nesta ficha encontram-se em meu poder para uso em minhas atividades, cabendo-me a responsabilidade por sua guarda e conservação... (Art. 462 CLT). Declaro estar ciente e de acordo com a utilização de meus dados pessoais neste documento, para fins de controle."
    pdf.multi_cell(0, 5, texto_doc, 0, 'J')
    pdf.ln(5)

    pdf.section_title('CHECKLIST DE RECEBIMENTO')
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(95, 6, 'ITEM', 'B', 0, 'L')
    pdf.cell(47.5, 6, 'ENTREGA', 'B', 0, 'C')
    pdf.cell(47.5, 6, 'ESTADO', 'B', 1, 'C')
    pdf.set_font('Arial', '', 10)
    for item, detalhes in checklist_data.items():
        pdf.cell(95, 6, item, 'B', 0)
        pdf.cell(47.5, 6, 'SIM' if detalhes['entregue'] else 'NÃO', 'B', 0, 'C')
        pdf.cell(47.5, 6, detalhes['estado'], 'B', 1, 'C')
    pdf.ln(25)

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
            
            setores_options = [s['nome_setor'] for s in get_db_connection().execute("SELECT nome_setor FROM setores").fetchall()]
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

            submitted = st.form_submit_button("Gerar Termo em PDF")
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


