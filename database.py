"""
Módulo de conexão com banco de dados.
Suporta Supabase (PostgreSQL) em produção e SQLite local como fallback.
Configure DATABASE_URL em .streamlit/secrets.toml ou variável de ambiente.
"""
import os
import streamlit as st
from sqlalchemy import create_engine, text

# ── URL do banco ──────────────────────────────────────────────────────
_SQLITE_DADOS    = "sqlite:///movimentacoes_geral.db"
_SQLITE_USUARIOS = "sqlite:///usuarios.db"
_PLACEHOLDERS    = ("SEU-REF", "[SUA-SENHA]", "[SEU-REF]")


def _is_placeholder(url: str) -> bool:
    return any(p in url for p in _PLACEHOLDERS)


def _get_database_url() -> str:
    try:
        url = st.secrets["DATABASE_URL"]
        if _is_placeholder(url):
            return _SQLITE_DADOS  # secrets ainda tem o texto de exemplo
        return url
    except (KeyError, FileNotFoundError, AttributeError):
        pass
    url = os.environ.get("DATABASE_URL", "")
    if url and not _is_placeholder(url):
        return url
    return _SQLITE_DADOS


def _get_usuarios_url() -> str:
    try:
        url = st.secrets["DATABASE_URL"]
        if _is_placeholder(url):
            return _SQLITE_USUARIOS
        return url
    except (KeyError, FileNotFoundError, AttributeError):
        pass
    url = os.environ.get("DATABASE_URL", "")
    if url and not _is_placeholder(url):
        return url
    return _SQLITE_USUARIOS

def is_postgres() -> bool:
    url = _get_database_url()
    return url.startswith("postgresql") or url.startswith("postgres")

# ── SQLAlchemy engine (cacheado) ──────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_engine():
    url = _get_database_url()
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True, pool_recycle=300)

@st.cache_resource(show_spinner=False)
def get_usuarios_engine():
    url = _get_usuarios_url()
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True, pool_recycle=300)

# ── Placeholder de parâmetros (%s para PG, ? para SQLite) ────────────
def ph() -> str:
    return "%s" if is_postgres() else "?"

# ── Inicializar tabelas ───────────────────────────────────────────────
def init_movimentacoes():
    engine = get_engine()
    if is_postgres():
        ddl = """
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id                    SERIAL PRIMARY KEY,
            "Data/Hora Empenho"   TIMESTAMP,
            "Código Requisição"   TEXT,
            "Id Volante"          TEXT,
            "Volante"             TEXT,
            "Código do Produto"   TEXT,
            "Descrição do Produto" TEXT,
            "Qtde Atendida"       REAL,
            "Qtde Empenhada"      REAL,
            "Qtde Requisitada"    REAL,
            "Estoque Físico"      TEXT,
            "Estoque"             TEXT,
            "Cidade"              TEXT,
            "Status"              TEXT,
            "Dias_Empenho"        INTEGER,
            "Status_Prazo"        TEXT,
            "Dias_Restantes"      INTEGER,
            "dia_semana"          TEXT
        )
        """
    else:
        ddl = """
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            'Data/Hora Empenho' TEXT,
            'Código Requisição' TEXT,
            'Id Volante' TEXT,
            'Volante' TEXT,
            'Código do Produto' TEXT,
            'Descrição do Produto' TEXT,
            'Qtde Atendida' REAL,
            'Qtde Empenhada' REAL,
            'Qtde Requisitada' REAL,
            'Estoque Físico' TEXT,
            'Estoque' TEXT,
            'Cidade' TEXT,
            'Status' TEXT,
            'Dias_Empenho' INTEGER,
            'Status_Prazo' TEXT,
            'Dias_Restantes' INTEGER,
            'dia_semana' TEXT
        )
        """
    with engine.connect() as conn:
        conn.execute(text(ddl))
        conn.commit()
