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
    
    # CSS para a logo e footer da tela de login
    st.markdown("""
    <style>
        .login-logo-text {
            font-family: 'Courier New', monospace;
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;
        }
        .login-logo-asset { color: #003366; }
        .login-logo-flow { color: #E30613; }

        @media (prefers-color-scheme: dark) {
            .login-logo-asset { color: #FFFFFF; }
            .login-logo-flow { color: #FF4B4B; }
        }

        .login-footer {
            text-align: center;
            margin-top: 30px;
        }
        .login-footer a {
            margin: 0 10px;
        }
        .login-footer img {
            width: 25px;
            height: 25px;
            filter: grayscale(1) opacity(0.5);
            transition: filter 0.3s;
        }
        .login-footer img:hover {
            filter: grayscale(0) opacity(1);
        }
        @media (prefers-color-scheme: dark) {
            .login-footer img {
                filter: grayscale(1) opacity(0.6) invert(1);
            }
            .login-footer img:hover {
                filter: opacity(1) invert(1);
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Logo
    st.markdown(
        """
        <div class="login-logo-text">
            <span class="login-logo-asset">ASSET</span><span class="login-logo-flow">FLOW</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Usa colunas para centralizar o formulário
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

    # Footer com ícones (Instagram trocado por LinkedIn)
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


