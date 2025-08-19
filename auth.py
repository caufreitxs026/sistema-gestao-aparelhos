import streamlit as st
import sqlite3
import hashlib

def hash_password(password):
    """Gera um hash seguro para a senha."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    """Verifica as credenciais do utilizador no banco de dados."""
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    hashed_password = hash_password(password)
    
    cursor.execute(
        "SELECT * FROM usuarios WHERE login = ? AND senha = ?",
        (username, hashed_password)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user:
        st.session_state['logged_in'] = True
        st.session_state['username'] = user['login']
        st.session_state['user_role'] = user['cargo']
        st.session_state['user_name'] = user['nome']
        return True
    return False

def show_login_form():
    """Exibe o formulário de login centralizado e personalizado."""
    st.markdown("""
    <style>
        .login-logo-text { font-family: 'Courier New', monospace; font-size: 48px; font-weight: bold; text-align: center; margin-bottom: 20px; }
        .login-logo-asset { color: #003366; } .login-logo-flow { color: #E30613; }
        @media (prefers-color-scheme: dark) { .login-logo-asset { color: #FFFFFF; } .login-logo-flow { color: #FF4B4B; } }
        .login-footer { text-align: center; margin-top: 30px; } .login-footer a { margin: 0 10px; }
        .login-footer img { width: 25px; height: 25px; filter: grayscale(1) opacity(0.5); transition: filter 0.3s; }
        .login-footer img:hover { filter: grayscale(0) opacity(1); }
        @media (prefers-color-scheme: dark) { .login-footer img { filter: grayscale(1) opacity(0.6) invert(1); } .login-footer img:hover { filter: opacity(1) invert(1); } }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="login-logo-text">
            <span class="login-logo-asset">ASSET</span><span class="login-logo-flow">FLOW</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        with st.form("login_form"):
            st.subheader("Login")
            username = st.text_input("Utilizador", placeholder="Usuário")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submitted = st.form_submit_button("Entrar")

            if submitted:
                if check_login(username, password):
                    st.rerun()
                else:
                    st.error("Utilizador ou senha inválidos.")

    st.markdown(
        f"""
        <div class="login-footer">
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

def logout():
    """Faz o logout do utilizador, limpando a sessão."""
    st.session_state['logged_in'] = False
    st.session_state.pop('username', None)
    st.session_state.pop('user_role', None)
    st.session_state.pop('user_name', None)
    st.rerun()

def build_sidebar():
    """Constrói a barra lateral personalizada com navegação organizada e footer."""
    with st.sidebar:
        # 1. Menu de Navegação Organizado por Categorias
        st.page_link("app.py", label="Dashboard", icon="📊")
        
        st.markdown("##### Operacional")
        st.page_link("pages/4_Movimentacoes.py", label="Movimentações", icon="🔄")
        st.page_link("pages/9_Devolucoes.py", label="Devoluções", icon="📦")
        st.page_link("pages/8_Manutencoes.py", label="Manutenções", icon="🔧")
        st.page_link("pages/6_Gerar_Documentos.py", label="Gerar Documentos", icon="�")
        
        st.markdown("##### Cadastros")
        st.page_link("pages/3_Aparelhos.py", label="Aparelhos", icon="📱")
        st.page_link("pages/2_Colaboradores.py", label="Colaboradores", icon="👥")
        st.page_link("pages/5_Contas_Gmail.py", label="Contas Gmail", icon="📧")
        st.page_link("pages/1_Cadastros_Gerais.py", label="Cadastros Gerais", icon="🗃️")
        
        # Páginas de Admin (só aparecem para administradores)
        if st.session_state.get('user_role') == 'Administrador':
            st.markdown("##### Administração")
            st.page_link("pages/7_Gerenciar_Usuarios.py", label="Gerir Utilizadores", icon="🛡️")
            st.page_link("pages/10_Importar_Exportar.py", label="Importar / Exportar", icon="📤")
            st.page_link("pages/11_Backup_Restauracao.py", label="Backup e Restauro", icon="💾")

        st.markdown("##### Assistente IA")
        st.page_link("pages/12_Converse_com_o_Flow.py", label="Converse com o Flow", icon="💬")
        
        # 2. Informações do Utilizador e Footer (empurrados para o fundo)
        st.markdown("""
            <style>
                .sidebar .sidebar-content {
                    display: flex;
                    flex-direction: column;
                    min-height: 100%;
                }
                .sidebar .sidebar-content .stButton {
                    width: 100%;
                }
                .sidebar-footer-container {
                    margin-top: auto;
                    padding-top: 20px;
                }
            </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-footer-container">', unsafe_allow_html=True)
        st.write(f"Utilizador: **{st.session_state['user_name']}**")
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
        st.markdown('</div>', unsafe_allow_html=True)
�
