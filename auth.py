"""
Módulo de autenticação para o Scouting Dashboard Botafogo-SP.

Gerencia usuários, login e sessão usando SQLite + werkzeug para hash seguro.
"""

import sqlite3
import os
import re
import logging
import streamlit as st
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)

# Caminho do banco de dados SQLite
DB_PATH = os.environ.get("AUTH_DB_PATH", os.path.join(os.path.dirname(__file__), "users.db"))


def _get_connection() -> sqlite3.Connection:
    """Cria conexão com o banco SQLite de usuários."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Inicializa a tabela de usuários se não existir.
    Cria um admin padrão caso a tabela esteja vazia."""
    try:
        conn = _get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'analyst',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # Criar admin padrão se não houver nenhum usuário
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            default_password = os.environ.get("ADMIN_DEFAULT_PASSWORD", "botafogo2024")
            conn.execute(
                "INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)",
                (
                    "admin@botafogo-sp.com",
                    generate_password_hash(default_password),
                    "Administrador",
                    "admin",
                ),
            )
            conn.commit()
            logger.info("Usuário admin padrão criado: admin@botafogo-sp.com")

        conn.close()
    except sqlite3.Error as e:
        logger.error("Erro ao inicializar banco de autenticação: %s", e)
        raise


def _validate_email(email: str) -> bool:
    """Valida formato básico de e-mail."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def authenticate_user(email: str, password: str) -> dict | None:
    """Valida credenciais contra o banco de dados.

    Returns:
        dict com dados do usuário se autenticado, None caso contrário.
    """
    if not email or not password:
        return None

    email = email.strip().lower()

    try:
        conn = _get_connection()
        cursor = conn.execute(
            "SELECT id, email, password_hash, name, role FROM users WHERE email = ?",
            (email,),
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        user_id, user_email, password_hash, name, role = row

        if check_password_hash(password_hash, password):
            return {
                "id": user_id,
                "email": user_email,
                "name": name,
                "role": role,
            }

        return None

    except sqlite3.Error as e:
        logger.error("Erro ao autenticar usuário: %s", e)
        return None


def is_authenticated() -> bool:
    """Verifica se o usuário está autenticado na sessão atual."""
    return st.session_state.get("authenticated", False)


def get_current_user() -> dict | None:
    """Retorna dados do usuário logado ou None."""
    if is_authenticated():
        return st.session_state.get("user")
    return None


def logout():
    """Encerra a sessão do usuário."""
    st.session_state["authenticated"] = False
    st.session_state["user"] = None


def render_login_page():
    """Renderiza a página de login com o design system do dashboard.

    Returns:
        True se o login foi bem-sucedido, False caso contrário.
    """
    # CSS específico da página de login
    st.markdown("""
    <style>
        /* Centralizar formulário de login */
        .login-container {
            max-width: 420px;
            margin: 0 auto;
            padding: 40px 32px;
            background: #111118;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.08);
        }
        .login-header {
            text-align: center;
            margin-bottom: 32px;
        }
        .login-header img {
            width: 80px;
            height: 80px;
            margin-bottom: 16px;
            border-radius: 8px;
        }
        .login-brand-scouting {
            color: #dc2626;
            font-size: 11px;
            letter-spacing: 3px;
            font-weight: 600;
        }
        .login-brand-name {
            color: white;
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -1px;
        }
        .login-brand-city {
            color: #6b7280;
            font-size: 10px;
            letter-spacing: 2px;
            margin-bottom: 8px;
        }
        .login-subtitle {
            color: #9ca3af;
            font-size: 14px;
            margin-top: 12px;
        }
        .login-error {
            background: rgba(220, 38, 38, 0.15);
            border: 1px solid rgba(220, 38, 38, 0.3);
            color: #fca5a5;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            margin-bottom: 16px;
            text-align: center;
        }
        .login-info {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.2);
            color: #86efac;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 13px;
            text-align: center;
            margin-top: 24px;
        }
        /* Ocultar sidebar na página de login */
        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
        /* Estilizar botão de login */
        .stButton > button {
            width: 100%;
            background: #dc2626 !important;
            color: white !important;
            border: none !important;
            padding: 10px 24px !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            cursor: pointer !important;
            transition: background 0.2s !important;
        }
        .stButton > button:hover {
            background: #b91c1c !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Espaçamento superior
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Container centralizado
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        # Header com logo e branding
        st.markdown("""
        <div class="login-header">
            <img src="https://cdn-img.zerozero.pt/img/logos/equipas/3154_imgbank_1685113109.png"
                 onerror="this.style.display='none'"
                 alt="Botafogo-SP">
            <div class="login-brand-scouting">SCOUTING</div>
            <div class="login-brand-name">BOTAFOGO</div>
            <div class="login-brand-city">RIBEIRÃO PRETO</div>
            <div class="login-subtitle">Acesse o painel de scouting</div>
        </div>
        """, unsafe_allow_html=True)

        # Exibir mensagem de erro se houver
        if st.session_state.get("login_error"):
            st.markdown(
                f'<div class="login-error">{st.session_state["login_error"]}</div>',
                unsafe_allow_html=True,
            )

        # Formulário de login
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "E-mail",
                placeholder="seu.email@exemplo.com",
                key="login_email",
            )
            password = st.text_input(
                "Senha",
                type="password",
                placeholder="Digite sua senha",
                key="login_password",
            )

            submitted = st.form_submit_button("Entrar")

            if submitted:
                # Limpar erro anterior
                st.session_state["login_error"] = ""

                # Validar inputs
                if not email or not password:
                    st.session_state["login_error"] = "Preencha todos os campos."
                    st.rerun()
                elif not _validate_email(email):
                    st.session_state["login_error"] = "Formato de e-mail inválido."
                    st.rerun()
                else:
                    try:
                        user = authenticate_user(email, password)
                        if user:
                            st.session_state["authenticated"] = True
                            st.session_state["user"] = user
                            st.session_state["login_error"] = ""
                            st.rerun()
                        else:
                            st.session_state["login_error"] = "E-mail ou senha incorretos."
                            st.rerun()
                    except Exception:
                        st.session_state["login_error"] = (
                            "Erro de conexão com o banco de dados. Tente novamente."
                        )
                        st.rerun()

        # Info com credenciais padrão
        st.markdown("""
        <div class="login-info">
            <strong>Primeiro acesso?</strong><br>
            admin@botafogo-sp.com / botafogo2024
        </div>
        """, unsafe_allow_html=True)

    return False
