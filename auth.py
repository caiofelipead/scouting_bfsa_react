"""
Módulo de autenticação para o Scouting Dashboard Botafogo-SP.

Backend duplo: PostgreSQL (produção via DATABASE_URL) ou SQLite (dev local).
Usa psycopg2 para PostgreSQL e sqlite3 como fallback.
Werkzeug para hash seguro de senhas.
"""

import os
import re
import logging
import streamlit as st
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURAÇÃO DO BANCO
# ============================================

DATABASE_URL = os.environ.get("DATABASE_URL")

# SQLite fallback path (desenvolvimento local)
_SQLITE_PATH = os.environ.get(
    "AUTH_DB_PATH", os.path.join(os.path.dirname(__file__), "users.db")
)

_USE_PG = bool(DATABASE_URL)

# Importar driver correto
if _USE_PG:
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        logger.warning("psycopg2 não instalado — fallback para SQLite")
        _USE_PG = False

if not _USE_PG:
    import sqlite3


# ============================================
# CONEXÃO (abstração PostgreSQL / SQLite)
# ============================================

def _get_connection():
    """Retorna conexão ao banco configurado (PG ou SQLite)."""
    if _USE_PG:
        url = DATABASE_URL
        # Render.com usa postgres:// mas psycopg2 exige postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url)
        conn.autocommit = False
        return conn
    else:
        conn = sqlite3.connect(_SQLITE_PATH)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn


def _execute(conn, sql: str, params: tuple = ()):
    """Executa SQL adaptando placeholders ao driver."""
    if _USE_PG:
        # SQLite usa ?, PostgreSQL usa %s
        sql = sql.replace("?", "%s")
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur


def _fetchone(conn, sql: str, params: tuple = ()):
    cur = _execute(conn, sql, params)
    return cur.fetchone()


def _fetchall(conn, sql: str, params: tuple = ()):
    cur = _execute(conn, sql, params)
    return cur.fetchall()


# ============================================
# INICIALIZAÇÃO DO BANCO
# ============================================

def init_db():
    """Inicializa a tabela de usuários. Cria admin padrão se vazia."""
    try:
        conn = _get_connection()

        if _USE_PG:
            _execute(conn, """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'analyst',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            _execute(conn, """
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

        row = _fetchone(conn, "SELECT COUNT(*) FROM users")
        if row[0] == 0:
            default_password = os.environ.get("ADMIN_DEFAULT_PASSWORD", "botafogo2024")
            _execute(
                conn,
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
    except Exception as e:
        logger.error("Erro ao inicializar banco de autenticação: %s", e)
        raise


# ============================================
# VALIDAÇÃO
# ============================================

def _validate_email(email: str) -> bool:
    """Valida formato básico de e-mail."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


# ============================================
# AUTENTICAÇÃO
# ============================================

def authenticate_user(email: str, password: str) -> dict | None:
    """Valida credenciais. Retorna dict do usuário ou None."""
    if not email or not password:
        return None

    email = email.strip().lower()

    try:
        conn = _get_connection()
        row = _fetchone(
            conn,
            "SELECT id, email, password_hash, name, role FROM users WHERE email = ?",
            (email,),
        )
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

    except Exception as e:
        logger.error("Erro ao autenticar usuário: %s", e)
        return None


# ============================================
# SESSÃO (Streamlit)
# ============================================

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


# ============================================
# UI — PÁGINA DE LOGIN
# ============================================

def render_login_page():
    """Renderiza a página de login com o design system do dashboard.

    Returns:
        True se o login foi bem-sucedido, False caso contrário.
    """
    st.markdown("""
    <style>
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
        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
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

    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
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

        if st.session_state.get("login_error"):
            st.markdown(
                f'<div class="login-error">{st.session_state["login_error"]}</div>',
                unsafe_allow_html=True,
            )

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
                st.session_state["login_error"] = ""

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

        st.markdown("""
        <div class="login-info">
            <strong>Primeiro acesso?</strong><br>
        </div>
        """, unsafe_allow_html=True)

    return False


# ============================================
# GERENCIAMENTO DE USUÁRIOS (Admin)
# ============================================

def list_users() -> list[dict]:
    """Lista todos os usuários cadastrados."""
    try:
        conn = _get_connection()
        rows = _fetchall(
            conn, "SELECT id, email, name, role, created_at FROM users ORDER BY id"
        )
        conn.close()
        return [
            {"id": r[0], "email": r[1], "name": r[2], "role": r[3], "created_at": r[4]}
            for r in rows
        ]
    except Exception as e:
        logger.error("Erro ao listar usuários: %s", e)
        return []


def create_user(email: str, password: str, name: str, role: str = "analyst") -> str | None:
    """Cria novo usuário. Retorna None em sucesso, mensagem de erro caso contrário."""
    email = email.strip().lower()
    name = name.strip()

    if not email or not password or not name:
        return "Todos os campos são obrigatórios."
    if not _validate_email(email):
        return "Formato de e-mail inválido."
    if len(password) < 6:
        return "A senha deve ter pelo menos 6 caracteres."
    if role not in ("admin", "analyst"):
        return "Papel inválido."

    try:
        conn = _get_connection()
        _execute(
            conn,
            "INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)",
            (email, generate_password_hash(password), name, role),
        )
        conn.commit()
        conn.close()
        return None
    except Exception as e:
        err_str = str(e).lower()
        if "unique" in err_str or "duplicate" in err_str or "integrity" in err_str:
            return "Este e-mail já está cadastrado."
        logger.error("Erro ao criar usuário: %s", e)
        return f"Erro no banco de dados: {e}"


def delete_user(user_id: int) -> str | None:
    """Remove usuário pelo ID. Retorna None em sucesso, mensagem de erro caso contrário."""
    try:
        conn = _get_connection()

        row = _fetchone(conn, "SELECT role FROM users WHERE id = ?", (user_id,))
        if row is None:
            conn.close()
            return "Usuário não encontrado."

        if row[0] == "admin":
            count_row = _fetchone(
                conn, "SELECT COUNT(*) FROM users WHERE role = 'admin'"
            )
            if count_row[0] <= 1:
                conn.close()
                return "Não é possível remover o único administrador."

        _execute(conn, "DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return None
    except Exception as e:
        logger.error("Erro ao remover usuário: %s", e)
        return f"Erro no banco de dados: {e}"


def render_admin_panel():
    """Renderiza o painel de gerenciamento de usuários (apenas para admins)."""
    user = get_current_user()
    if not user or user.get("role") != "admin":
        st.warning("Acesso restrito a administradores.")
        return

    st.markdown("### Usuários Cadastrados")

    users = list_users()
    if users:
        for u in users:
            col1, col2, col3, col4 = st.columns([3, 2, 1.5, 1])
            with col1:
                st.markdown(f"**{u['name']}**")
            with col2:
                st.caption(u['email'])
            with col3:
                role_label = "Admin" if u['role'] == 'admin' else "Analista"
                color = "#dc2626" if u['role'] == 'admin' else "#9ca3af"
                st.markdown(
                    f'<span style="color:{color}; font-size:12px; font-weight:600;">{role_label}</span>',
                    unsafe_allow_html=True,
                )
            with col4:
                if u['id'] != user['id']:
                    if st.button("Remover", key=f"del_user_{u['id']}", type="secondary"):
                        err = delete_user(u['id'])
                        if err:
                            st.error(err)
                        else:
                            st.rerun()
    else:
        st.info("Nenhum usuário cadastrado.")

    st.divider()
    st.markdown("### Cadastrar Novo Usuário")

    with st.form("add_user_form", clear_on_submit=True):
        new_name = st.text_input("Nome", placeholder="Nome completo", key="adm_name")
        new_email = st.text_input("E-mail", placeholder="email@exemplo.com", key="adm_email")
        new_password = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres", key="adm_pass")
        new_role = st.selectbox(
            "Papel", ["analyst", "admin"],
            format_func=lambda x: "Analista" if x == "analyst" else "Admin",
            key="adm_role",
        )

        if st.form_submit_button("Cadastrar"):
            err = create_user(new_email, new_password, new_name, new_role)
            if err:
                st.error(err)
            else:
                st.success(f"Usuário {new_email} cadastrado com sucesso!")
                st.rerun()
