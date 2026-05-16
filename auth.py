"""
Módulo de autenticação — gerencia usuários, sessão e permissões.
Suporta SQLite (local) e PostgreSQL/Supabase (produção) via database.py
"""
import hashlib
import hmac
import os
import unicodedata
import streamlit as st
from sqlalchemy import text


def _norm_cidade(s: str) -> str:
    """Normaliza nome de cidade: sem acento, sem espaços extras, minúsculo."""
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode("ascii").strip().lower()


def _now_expr() -> str:
    from database import is_postgres
    return "NOW()" if is_postgres() else "datetime('now','localtime')"


def listar_cidades_dados() -> list[str]:
    """Retorna as cidades disponíveis no banco de dados principal."""
    try:
        from database import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT DISTINCT \"Cidade\" FROM movimentacoes WHERE \"Cidade\" IS NOT NULL ORDER BY \"Cidade\"")
            ).fetchall()
        return [r[0] for r in rows if r[0] and str(r[0]).strip()]
    except Exception:
        return []


# ========================
# Banco de Usuários
# ========================
def _get_ue():
    """Retorna o engine de usuários."""
    from database import get_usuarios_engine
    return get_usuarios_engine()


def init_usuarios_db():
    from database import is_postgres
    engine = _get_ue()
    if is_postgres():
        ddl = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id         SERIAL PRIMARY KEY,
            username   TEXT UNIQUE NOT NULL,
            nome       TEXT NOT NULL,
            senha_hash TEXT NOT NULL,
            cidade     TEXT,
            role       TEXT NOT NULL DEFAULT 'usuario',
            criado_em  TIMESTAMP DEFAULT NOW()
        )
        """
    else:
        ddl = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE NOT NULL,
            nome       TEXT NOT NULL,
            senha_hash TEXT NOT NULL,
            cidade     TEXT,
            role       TEXT NOT NULL DEFAULT 'usuario',
            criado_em  TEXT
        )
        """
    with engine.connect() as conn:
        conn.execute(text(ddl))
        # Migração: criado_em para SQLite legado
        if not is_postgres():
            try:
                cols = [r[1] for r in conn.execute(text("PRAGMA table_info(usuarios)")).fetchall()]
                if "criado_em" not in cols:
                    conn.execute(text("ALTER TABLE usuarios ADD COLUMN criado_em TEXT"))
                    conn.execute(text("UPDATE usuarios SET criado_em = datetime('now','localtime') WHERE criado_em IS NULL"))
            except Exception:
                pass
        conn.commit()
        # Admin padrão
        count = conn.execute(text("SELECT COUNT(*) FROM usuarios")).scalar()
        if count == 0:
            _criar_usuario_interno_conn(conn, "admin", "Administrador", "admin123", None, "admin")
            conn.commit()


def _hash_senha(senha: str) -> str:
    salt = os.environ.get("APP_SALT", "req_painel_2026_salt")
    return hmac.new(salt.encode(), senha.encode(), hashlib.sha256).hexdigest()


def _criar_usuario_interno_conn(conn, username: str, nome: str, senha: str, cidade, role: str):
    conn.execute(
        text(f"INSERT INTO usuarios (username, nome, senha_hash, cidade, role, criado_em) VALUES (:u, :n, :h, :c, :r, {_now_expr()})"),
        {"u": username.strip().lower(), "n": nome.strip(), "h": _hash_senha(senha), "c": cidade, "r": role},
    )


def registrar_usuario(username: str, nome: str, senha: str, confirma: str, cidade: str) -> tuple[bool, str]:
    """Auto-cadastro."""
    if not all([username, nome, senha, confirma, cidade]):
        return False, "Preencha todos os campos."
    if len(senha) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres."
    if senha != confirma:
        return False, "As senhas não coincidem."
    username = username.strip().lower()
    if not username.replace(".", "").replace("_", "").isalnum():
        return False, "Username só pode conter letras, números, ponto e underscore."
    cidade_digitada = cidade.strip()
    cidades_dados = listar_cidades_dados()
    cidade_resolvida = next(
        (c for c in cidades_dados if _norm_cidade(c) == _norm_cidade(cidade_digitada)),
        cidade_digitada,
    )
    try:
        engine = _get_ue()
        with engine.connect() as conn:
            _criar_usuario_interno_conn(conn, username, nome, senha, cidade_resolvida, "usuario")
            conn.commit()
        return True, "Conta criada com sucesso! Faça login na aba Entrar."
    except Exception as e:
        msg = str(e)
        if "unique" in msg.lower() or "UNIQUE" in msg:
            return False, f"Username '{username}' já está em uso. Escolha outro."
        return False, msg


# ========================
# CRUD Usuários
# ========================
def listar_usuarios() -> list[dict]:
    engine = _get_ue()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, username, nome, cidade, role, criado_em FROM usuarios ORDER BY criado_em DESC NULLS LAST")
        ).fetchall()
    return [
        {"id": r[0], "username": r[1], "nome": r[2], "cidade": r[3], "role": r[4], "criado_em": r[5]}
        for r in rows
    ]


def criar_usuario(username: str, nome: str, senha: str, cidade, role: str) -> tuple[bool, str]:
    if not username or not nome or not senha:
        return False, "Preencha todos os campos obrigatórios."
    try:
        engine = _get_ue()
        with engine.connect() as conn:
            _criar_usuario_interno_conn(conn, username, nome, senha, cidade or None, role)
            conn.commit()
        return True, "Usuário criado com sucesso."
    except Exception as e:
        msg = str(e)
        if "unique" in msg.lower() or "UNIQUE" in msg:
            return False, f"Username '{username}' já existe."
        return False, msg


def atualizar_usuario(user_id: int, nome: str, cidade, role: str, nova_senha: str = "") -> tuple[bool, str]:
    if cidade:
        cidades_dados = listar_cidades_dados()
        cidade = next(
            (c for c in cidades_dados if _norm_cidade(c) == _norm_cidade(cidade)),
            str(cidade).strip(),
        )
    try:
        engine = _get_ue()
        with engine.connect() as conn:
            if nova_senha:
                conn.execute(
                    text("UPDATE usuarios SET nome=:n, cidade=:c, role=:r, senha_hash=:h WHERE id=:id"),
                    {"n": nome.strip(), "c": cidade, "r": role, "h": _hash_senha(nova_senha), "id": user_id},
                )
            else:
                conn.execute(
                    text("UPDATE usuarios SET nome=:n, cidade=:c, role=:r WHERE id=:id"),
                    {"n": nome.strip(), "c": cidade, "r": role, "id": user_id},
                )
            conn.commit()
        return True, "Usuário atualizado com sucesso."
    except Exception as e:
        return False, str(e)


def excluir_usuario(user_id: int) -> tuple[bool, str]:
    try:
        engine = _get_ue()
        with engine.connect() as conn:
            row = conn.execute(text("SELECT username FROM usuarios WHERE id=:id"), {"id": user_id}).fetchone()
            if not row:
                return False, "Usuário não encontrado."
            logado = st.session_state.get("usuario_logado", {})
            if row[0] == logado.get("username"):
                return False, "Não é possível excluir o próprio usuário logado."
            conn.execute(text("DELETE FROM usuarios WHERE id=:id"), {"id": user_id})
            conn.commit()
        return True, "Usuário excluído."
    except Exception as e:
        return False, str(e)


def alterar_senha(user_id: int, senha_atual: str, nova_senha: str, confirma_senha: str) -> tuple[bool, str]:
    if not nova_senha or not confirma_senha:
        return False, "Preencha todos os campos."
    if len(nova_senha) < 6:
        return False, "A nova senha deve ter pelo menos 6 caracteres."
    if nova_senha != confirma_senha:
        return False, "As senhas não coincidem."
    try:
        engine = _get_ue()
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT id FROM usuarios WHERE id=:id AND senha_hash=:h"),
                {"id": user_id, "h": _hash_senha(senha_atual)},
            ).fetchone()
            if not row:
                return False, "Senha atual incorreta."
            conn.execute(
                text("UPDATE usuarios SET senha_hash=:h WHERE id=:id"),
                {"h": _hash_senha(nova_senha), "id": user_id},
            )
            conn.commit()
    except Exception as e:
        return False, str(e)


# ========================
# Autenticação
# ========================
def autenticar(username: str, senha: str) -> dict | None:
    engine = _get_ue()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, username, nome, cidade, role FROM usuarios WHERE username=:u AND senha_hash=:h"),
            {"u": username.strip().lower(), "h": _hash_senha(senha)},
        ).fetchone()
    if row:
        return {"id": row[0], "username": row[1], "nome": row[2], "cidade": row[3], "role": row[4]}
    return None


# ========================
# Sessão Streamlit
# ========================
def login_required():
    init_usuarios_db()
    if "usuario_logado" not in st.session_state:
        st.session_state["usuario_logado"] = None
    if st.session_state["usuario_logado"]:
        return st.session_state["usuario_logado"]
    _render_login()
    st.stop()


def logout():
    st.session_state["usuario_logado"] = None
    st.rerun()


def is_admin() -> bool:
    u = st.session_state.get("usuario_logado")
    return u is not None and u["role"] == "admin"


def cidade_usuario() -> str | None:
    u = st.session_state.get("usuario_logado")
    if u and u["role"] != "admin":
        return u["cidade"]
    return None


# ========================
# Renderização Login
# ========================
def _render_login():
    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown("<h2 style='text-align:center;color:#1B2A4A'>🌐 Painel de Requisições</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#6c757d'>Acesso restrito — faça login para continuar</p>", unsafe_allow_html=True)

        aba_login, aba_cadastro = st.tabs(["🔐 Entrar", "📝 Criar Conta"])

        with aba_login:
            with st.form("form_login", clear_on_submit=False):
                username  = st.text_input("👤 Usuário", placeholder="seu.usuario")
                senha     = st.text_input("🔒 Senha", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")
            if submitted:
                if not username or not senha:
                    st.error("Preencha usuário e senha.")
                else:
                    usuario = autenticar(username, senha)
                    if usuario:
                        st.session_state["usuario_logado"] = usuario
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha inválidos.")

        with aba_cadastro:
            st.caption("Crie sua conta abaixo. Após o cadastro, acesse a aba Entrar.")
            with st.form("form_cadastro", clear_on_submit=True):
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    r_username = st.text_input("👤 Usuário *", placeholder="joao.silva", help="Letras, números, ponto e underscore")
                    r_nome     = st.text_input("📛 Nome completo *", placeholder="João Silva")
                with r_col2:
                    r_cidade = st.text_input("🏙️ Cidade *", placeholder="Ex: Ribeirão Preto", help="Digite como aparece nos dados. Sem acento também funciona.")
                    r_senha  = st.text_input("🔑 Senha *", type="password", placeholder="Mínimo 6 caracteres")
                r_confirma = st.text_input("🔑 Confirmar senha *", type="password")
                r_submitted = st.form_submit_button("✅ Criar Minha Conta", use_container_width=True, type="primary")
            if r_submitted:
                ok, msg = registrar_usuario(r_username, r_nome, r_senha, r_confirma, r_cidade)
                st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")
