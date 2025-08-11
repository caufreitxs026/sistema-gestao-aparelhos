import streamlit as st
import sqlite3
import hashlib

def hash_password(password):
    """Gera um hash seguro para a senha."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    """Verifica as credenciais do usuário no banco de dados."""
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
    """Exibe o formulário de login centralizado."""
    st.title("Sistema de Gerenciamento de Aparelhos")
    
    # Usa colunas para criar espaço nas laterais e centralizar o formulário
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        with st.form("login_form"):
            st.subheader("Login")
            username = st.text_input("Usuário", placeholder="admin")
            password = st.text_input("Senha", type="password", placeholder="admin")
            submitted = st.form_submit_button("Entrar")

            if submitted:
                if check_login(username, password):
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")

def logout():
    """Faz o logout do usuário, limpando a sessão."""
    st.session_state['logged_in'] = False
    st.session_state.pop('username', None)
    st.session_state.pop('user_role', None)
    st.session_state.pop('user_name', None)
    st.rerun()
