import streamlit as st
import sqlite3
from datetime import datetime
from auth import show_login_form
import json
import streamlit.components.v1 as components

# --- Autenticação ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("app.py")

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

# --- Funções do DB ---
def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

def carregar_movimentacoes_entrega():
    conn = get_db_connection()
    movs = conn.execute("""
        SELECT h.id, h.data_movimentacao, a.numero_serie, c.nome_completo
        FROM historico_movimentacoes h
        JOIN aparelhos a ON h.aparelho_id = a.id
        JOIN colaboradores c ON h.colaborador_id = c.id
        WHERE h.status_id = (SELECT id FROM status WHERE nome_status = 'Em uso')
        ORDER BY h.data_movimentacao DESC
    """).fetchall()
    conn.close()
    return movs

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

# --- UI ---
st.title("Gerar Termo de Responsabilidade")
movimentacoes = carregar_movimentacoes_entrega()

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

            submitted = st.form_submit_button("Gerar e Baixar PDF")
            if submitted:
                # Converte os dados para um formato que o JavaScript entende (JSON)
                dados_json = json.dumps(dados_termo)
                checklist_json = json.dumps(checklist_data)
                
                # O componente HTML que irá gerar o PDF no navegador
                components.html(f"""
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.23/jspdf.plugin.autotable.min.js"></script>
                    <script>
                        const {{ jsPDF }} = window.jspdf;
                        const doc = new jsPDF();
                        const dados = {dados_json};
                        const checklist = {checklist_json};
                        const logoBase64 = "data:image/png;base64,{st.secrets.get('LOGO_BASE64', '')}"; // Usa a logo dos segredos

                        // --- Design do PDF ---
                        doc.addImage(logoBase64, 'PNG', 10, 8, 50, 0);
                        doc.setFont('helvetica', 'bold');
                        doc.setFontSize(16);
                        doc.setTextColor(0, 51, 102);
                        doc.text('TERMO DE RESPONSABILIDADE', 105, 15, {{ align: 'center' }});
                        doc.setFont('helvetica', 'italic');
                        doc.setFontSize(10);
                        doc.setTextColor(227, 6, 19);
                        doc.text('PROTOCOLO DE RECEBIMENTO E DEVOLUÇÃO', 105, 22, {{ align: 'center' }});

                        let y = 40; // Posição vertical inicial

                        // Função para criar uma secção
                        function createSection(title, dataPairs) {{
                            doc.setFont('helvetica', 'bold');
                            doc.setFontSize(12);
                            doc.setFillColor(0, 51, 102);
                            doc.setTextColor(255, 255, 255);
                            doc.rect(10, y, 190, 8, 'F');
                            doc.text(title, 15, y + 6);
                            y += 10;
                            doc.setTextColor(0, 0, 0);
                            doc.setFont('helvetica', 'normal');
                            doc.setFontSize(10);
                            dataPairs.forEach(pair => {{
                                doc.text(`{{pair[0]}}:`, 15, y);
                                doc.text(String(pair[1] || '-'), 50, y);
                                y += 7;
                            }});
                            y += 5;
                        }}

                        createSection('DADOS DO COLABORADOR', [
                            ['NOME', dados.nome_completo],
                            ['CPF', dados.cpf],
                            ['SETOR', dados.nome_setor],
                            ['EMAIL', dados.gmail]
                        ]);

                        createSection('DADOS DO SMARTPHONE', [
                            ['MARCA', dados.nome_marca],
                            ['MODELO', dados.nome_modelo],
                            ['IMEI 1', dados.imei1],
                            ['IMEI 2', dados.imei2]
                        ]);
                        
                        // Tabela do Checklist
                        const head = [['ITEM', 'ENTREGA', 'ESTADO']];
                        const body = Object.entries(checklist).map(([item, details]) => [
                            item,
                            details.entregue ? 'SIM' : 'NÃO',
                            details.estado
                        ]);
                        doc.autoTable({{
                            startY: y,
                            head: head,
                            body: body,
                            theme: 'grid',
                            headStyles: {{ fillColor: [227, 6, 19] }}
                        }});
                        y = doc.autoTable.previous.finalY + 20;

                        // Assinatura
                        doc.text('_________________________________________', 105, y + 10, {{ align: 'center' }});
                        doc.text(dados.nome_completo, 105, y + 17, {{ align: 'center' }});

                        // Download
                        doc.save(`Termo_${{dados.nome_completo.replace(/ /g, '_')}}.pdf`);
                    </script>
                """, height=0)
