"""
JWT Authentication module for the Scouting API.
PostgreSQL-only backend — eliminates SQLite and users_seed.json.
"""

import os
import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────

_secret = os.environ.get("JWT_SECRET_KEY")
if not _secret:
    raise ValueError("JWT_SECRET_KEY environment variable is required")
SECRET_KEY = _secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("TOKEN_EXPIRE_MINUTES", "480"))

DATABASE_URL = os.environ.get("DATABASE_URL", "")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# ── Database ──────────────────────────────────────────────────────────

def _get_connection():
    """Returns a PostgreSQL connection. Falls back to SQLite for dev only."""
    url = DATABASE_URL
    if url:
        import psycopg2
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url)
        conn.autocommit = False
        return conn, "pg"
    else:
        import sqlite3
        db_path = os.environ.get("AUTH_DB_PATH", os.path.join(os.path.dirname(__file__), "users.db"))
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn, "sqlite"


def _execute(conn, driver: str, sql: str, params: tuple = ()):
    if driver == "pg":
        sql = sql.replace("?", "%s")
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur


def init_db():
    """Initialize users table and seed admin user(s)."""
    conn, driver = _get_connection()
    try:
        if driver == "pg":
            _execute(conn, driver, """
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
            _execute(conn, driver, """
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

        # Seed admin user from environment variables (no hardcoded credentials)
        admin_email = os.environ.get("ADMIN_EMAIL")
        admin_password = os.environ.get("ADMIN_PASSWORD")
        admin_name = os.environ.get("ADMIN_NAME", "Administrador")

        if not admin_email or not admin_password:
            logger.warning("ADMIN_EMAIL and ADMIN_PASSWORD env vars not set — skipping admin seed")
            return

        cur = _execute(conn, driver, "SELECT id, password_hash FROM users WHERE email = ?", (admin_email,))
        row = cur.fetchone()
        new_hash = hash_password(admin_password)

        if row is None:
            _execute(
                conn, driver,
                "INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)",
                (admin_email, new_hash, admin_name, "admin"),
            )
            conn.commit()
            logger.info("Admin user created: %s", admin_email)
        else:
            # Always reset password to guarantee login works after deploy
            _execute(
                conn, driver,
                "UPDATE users SET password_hash = ?, role = ? WHERE email = ?",
                (new_hash, "admin", admin_email),
            )
            conn.commit()
            logger.info("Admin user password reset: %s", admin_email)
    finally:
        conn.close()


# ── Password & Token ──────────────────────────────────────────────────

def _truncate_for_bcrypt(plain: str) -> str:
    """Bcrypt silently ignores bytes beyond 72; truncate explicitly to avoid errors."""
    return plain.encode("utf-8")[:72].decode("utf-8", errors="ignore")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_truncate_for_bcrypt(plain), hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(_truncate_for_bcrypt(plain))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── User CRUD ─────────────────────────────────────────────────────────

def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Validate credentials. Returns user dict or None."""
    if not email or not password:
        return None
    email = email.strip().lower()
    conn, driver = _get_connection()
    try:
        cur = _execute(
            conn, driver,
            "SELECT id, email, password_hash, name, role FROM users WHERE email = ?",
            (email,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        user_id, user_email, password_hash, name, role = row
        if verify_password(password, password_hash):
            return {"id": user_id, "email": user_email, "name": name, "role": role}
        return None
    except Exception as e:
        logger.error("Auth error: %s", e)
        return None
    finally:
        conn.close()


def list_users() -> list[dict]:
    conn, driver = _get_connection()
    try:
        cur = _execute(conn, driver, "SELECT id, email, name, role, created_at FROM users ORDER BY id")
        rows = cur.fetchall()
        return [
            {"id": r[0], "email": r[1], "name": r[2], "role": r[3], "created_at": str(r[4]) if r[4] else None}
            for r in rows
        ]
    except Exception as e:
        logger.error("List users error: %s", e)
        return []
    finally:
        conn.close()


def create_user(email: str, password: str, name: str, role: str = "analyst") -> Optional[str]:
    """Create user. Returns None on success, error message on failure."""
    email = email.strip().lower()
    name = name.strip()
    if not email or not password or not name:
        return "Todos os campos são obrigatórios."
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return "Formato de e-mail inválido."
    if len(password) < 6:
        return "A senha deve ter pelo menos 6 caracteres."
    if role not in ("admin", "analyst"):
        return "Papel inválido."

    conn, driver = _get_connection()
    try:
        _execute(
            conn, driver,
            "INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)",
            (email, hash_password(password), name, role),
        )
        conn.commit()
        return None
    except Exception as e:
        err = str(e).lower()
        if "unique" in err or "duplicate" in err or "integrity" in err:
            return "Este e-mail já está cadastrado."
        logger.error("Create user error: %s", e)
        return f"Erro no banco de dados: {e}"
    finally:
        conn.close()


def delete_user(user_id: int) -> Optional[str]:
    conn, driver = _get_connection()
    try:
        cur = _execute(conn, driver, "SELECT role FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if row is None:
            return "Usuário não encontrado."
        if row[0] == "admin":
            cur2 = _execute(conn, driver, "SELECT COUNT(*) FROM users WHERE role = 'admin'")
            if cur2.fetchone()[0] <= 1:
                return "Não é possível remover o único administrador."
        _execute(conn, driver, "DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return None
    except Exception as e:
        logger.error("Delete user error: %s", e)
        return f"Erro no banco de dados: {e}"
    finally:
        conn.close()


# ── FastAPI Dependency ────────────────────────────────────────────────

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI dependency: extract and validate JWT from Authorization header."""
    payload = decode_token(credentials.credentials)
    email = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    return {
        "email": email,
        "role": payload.get("role", "analyst"),
        "name": payload.get("name", ""),
    }


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current_user
