import pandas as pd
import numpy as np
import unicodedata
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import text
from database import get_engine, init_movimentacoes
from auth import login_required, is_admin, cidade_usuario, logout, alterar_senha, registrar_usuario


def _norm(s: str) -> str:
    """Normaliza string para comparação: sem acento, sem espaços extras, minúsculo."""
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode("ascii").strip().lower()

# ========================
# Configurações Globais
# ========================
PRAZO_RETIRADA_DIAS = 5

CORES = {
    "primaria": "#1B2A4A",
    "secundaria": "#2E86AB",
    "sucesso": "#28A745",
    "perigo": "#DC3545",
    "alerta": "#FFC107",
    "info": "#17A2B8",
    "claro": "#F8F9FA",
    "escuro": "#343A40",
    "separado": "#2ECC71",
    "a_separar": "#E74C3C",
    "expirada": "#8E44AD",
    "gradiente": ["#1B2A4A", "#2E86AB", "#48C9B0", "#F39C12", "#E74C3C", "#8E44AD", "#3498DB"],
}

PLOTLY_TEMPLATE = "plotly_white"

# Possíveis nomes de coluna de cidade no geral.xlsx
COLUNAS_CIDADE_POSSIVEIS = [
    "Cidade", "CIDADE", "Municipio", "Município", "MUNICIPIO", "MUNICÍPIO",
    "Localidade", "LOCALIDADE", "Local", "LOCAL", "Regional", "REGIONAL",
    "UF_Cidade", "Filial", "FILIAL",
]

MAPA_ESTOQUE = {
    'PROPRIO GERAL': 'PROPRIO',
    'O&M PROPRIO GERAL TIM FATURA B': 'GERAL TIM',
    'SPEEDY/FTTX CLIENTE': 'CASA CLIENTE',
    'MANUTENCAO RPO CLIENTE': 'MANUTENCAO',
    'EXEC SEGREGADO IMPLANTACAO RPO CLIENTE': 'EXEC SEGREGADO',
    'BOL IMPLANTACAO RPO CLIENTE': 'IMPLANTACAO',
    'DADOS CLIENTE': 'DADOS',
    'FERRAMENTAL': 'FERRAMENTAL',
    'UNIFORME': 'UNIFORME',
    'EPI-EPC': 'EPI',
    'BRINDES': 'BRINDES',
    'RPO MANUTENCAO FIBRA OPTICA BACKBONE': 'BACKBONE',
    'CLASSE D': 'CLASSE D',
    'MANUTENCAO RPO MATERIAL REUTILIZACAO': 'MANUTENCAO REUT',
    'EQUIPAMENTOS': 'EQUIPAMENTOS',
    'PROPRIO GERAL TIM': 'PROPRIO TIM',
    'KIT FERRAMENTAL CONTRATACOES': 'KIT CONTRATACOES',
    'MATERIAL DE ESCRITORIO': 'MATERIAL DE ESCRITORIO',
    'CELULARES': 'CELULARES',
    'MANUTENCAO RPO-MATERIAL REUTILIZACAO': 'MANUTENCAO-REUTILIZACAO',
    'MATERIAIS ENTREGUES EM OBRA': 'MATERIAIS ENTREGUES EM OBRA',
    'EQUIPAMENTOS TI': 'EQUIPAMENTOS TI',
    'LVUT IMPLANTACAO RPO CLIENTE': 'IMPLANTACAO',
    'PLANTA INTERNA FIXA': 'PLANTA INTERNA',
    'OSX/PEE IMPLANTAÇÃO RPO CLIENTE': 'IMPLANTACAO',
}

# ========================
# CSS Customizado
# ========================
def aplicar_css():
    st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        .kpi-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 16px;
            padding: 24px 20px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            border-left: 5px solid;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            margin-bottom: 10px;
        }
        .kpi-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        }
        .kpi-titulo {
            font-size: 0.85rem;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .kpi-valor {
            font-size: 2.2rem;
            font-weight: 800;
            margin: 4px 0;
            line-height: 1.1;
        }
        .kpi-subtexto {
            font-size: 0.78rem;
            color: #868e96;
            margin-top: 6px;
        }

        .header-container {
            background: linear-gradient(135deg, #1B2A4A 0%, #2E86AB 100%);
            padding: 30px 40px;
            border-radius: 16px;
            margin-bottom: 25px;
            color: white;
        }
        .header-container h1 { margin: 0; font-size: 2rem; font-weight: 700; }
        .header-container p { margin: 5px 0 0 0; font-size: 0.95rem; opacity: 0.85; }

        .alerta-expiracao {
            background: linear-gradient(135deg, #2d1b1b 0%, #5c1c1c 100%);
            border: 1px solid #dc3545;
            border-radius: 12px;
            padding: 16px 20px;
            color: #ff8080;
            font-weight: 600;
            margin-bottom: 15px;
        }

        .secao-titulo {
            font-size: 1.15rem;
            font-weight: 700;
            color: #1B2A4A;
            border-bottom: 3px solid #2E86AB;
            padding-bottom: 8px;
            margin: 30px 0 15px 0;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1B2A4A 0%, #1a3a5c 100%);
        }
        [data-testid="stSidebar"] .stMarkdown h1,
        [data-testid="stSidebar"] .stMarkdown h2,
        [data-testid="stSidebar"] .stMarkdown h3,
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stMarkdown label,
        [data-testid="stSidebar"] .stMarkdown span {
            color: #ffffff !important;
        }

        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #2E86AB, transparent);
            margin: 20px 0;
        }

        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 10px 24px;
            font-weight: 600;
        }

        [data-testid="stSidebarCollapsedControl"] button,
        [data-testid="collapsedControl"] button {
            background: linear-gradient(135deg, #1B2A4A 0%, #2E86AB 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 0 10px 10px 0 !important;
            width: 48px !important;
            height: 48px !important;
            box-shadow: 0 3px 12px rgba(27,42,74,0.3) !important;
            transition: all 0.3s ease !important;
            margin-top: 10px !important;
        }
    </style>
    """, unsafe_allow_html=True)


# ========================
# Banco de Dados
# ========================
def salvar_no_banco(df: pd.DataFrame, cidade: str | None = None):
    """Salva dados no banco. Se cidade fornecida, substitui apenas essa cidade (multi-cidade seguro)."""
    engine = get_engine()
    if cidade:
        # Partial update: apaga só a cidade e insere novos dados
        with engine.connect() as conn:
            try:
                conn.execute(text('DELETE FROM movimentacoes WHERE "Cidade" = :c'), {"c": cidade})
                conn.commit()
            except Exception:
                pass  # Tabela pode não existir ainda
        df.to_sql("movimentacoes", engine, if_exists="append", index=False, method="multi")
    else:
        # Admin: substitui tudo
        df.to_sql("movimentacoes", engine, if_exists="replace", index=False, method="multi")


def _norm_col(s: str) -> str:
    """Normaliza nome de coluna: remove acentos, lowercase, sem espaços extras."""
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode("ascii").strip().lower()

# Nomes canônicos esperados das colunas
_COLUNAS_CANONICAS = [
    'Data/Hora Empenho', 'Código Requisição', 'Id Volante', 'Volante',
    'Código do Produto', 'Descrição do Produto', 'Qtde Atendida',
    'Qtde Empenhada', 'Qtde Requisitada', 'Estoque Físico', 'Estoque',
    'dia_semana', 'Status', 'Status_Prazo', 'Cidade', 'dias_restantes',
]
_MAP_NORM_CANONICO = {_norm_col(c): c for c in _COLUNAS_CANONICAS}


def carregar_dados():
    engine = get_engine()
    df = pd.read_sql(
        "SELECT * FROM movimentacoes", engine,
        parse_dates=["Data/Hora Empenho"],
    )
    # Corrige nomes de colunas que possam ter vindo com encoding/case diferente do PostgreSQL
    rename = {
        col: _MAP_NORM_CANONICO[_norm_col(col)]
        for col in df.columns
        if _norm_col(col) in _MAP_NORM_CANONICO and col != _MAP_NORM_CANONICO[_norm_col(col)]
    }
    if rename:
        df = df.rename(columns=rename)
    return df


# ========================
# Detecção de Coluna Cidade
# ========================
def detectar_coluna_cidade(df: pd.DataFrame) -> str | None:
    """Tenta encontrar a coluna de cidade no DataFrame."""
    for col in COLUNAS_CIDADE_POSSIVEIS:
        if col in df.columns:
            return col
    # Busca parcial (case-insensitive)
    for col in df.columns:
        col_lower = col.lower().strip()
        if any(p in col_lower for p in ["cidade", "municipio", "município", "localidade", "filial", "regional"]):
            return col
    return None


# ========================
# Tratamento de Dados
# ========================
def calcular_prazo(row, hoje: datetime) -> dict:
    """Calcula status de prazo baseado em 5 dias desde o empenho."""
    empenho = row.get("Data/Hora Empenho")
    status = row.get("Status", "")

    if pd.isna(empenho):
        return {"Status_Prazo": "⚠️ Sem data", "Dias_Empenho": None, "Dias_Restantes": None}

    if not isinstance(empenho, datetime):
        try:
            empenho = pd.to_datetime(empenho)
        except Exception:
            return {"Status_Prazo": "⚠️ Sem data", "Dias_Empenho": None, "Dias_Restantes": None}

    dias = (hoje - empenho).days
    restantes = max(0, PRAZO_RETIRADA_DIAS - dias)

    if dias >= PRAZO_RETIRADA_DIAS:
        prazo = "🚨 Expirada"
    elif status == "Separado":
        prazo = f"📦 Retirar em {restantes} dia(s)"
    else:
        prazo = f"⏳ Separar/Retirar em {restantes} dia(s)"

    return {"Status_Prazo": prazo, "Dias_Empenho": dias, "Dias_Restantes": restantes}


def tratar_dados(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Normaliza encoding dos nomes de colunas (NFC) — resolve diferenças NFD/NFC vindas do Excel
    df.columns = [unicodedata.normalize("NFC", str(x).strip()) for x in df.columns]

    # Detectar coluna de cidade antes de filtrar colunas
    col_cidade = detectar_coluna_cidade(df)

    colunas_base = [
        'Data/Hora Empenho', 'Código Requisição', 'Id Volante', 'Volante',
        'Código do Produto', 'Descrição do Produto', 'Qtde Atendida',
        'Qtde Empenhada', 'Qtde Requisitada', 'Estoque Físico',
    ]
    if col_cidade and col_cidade not in colunas_base:
        colunas_base.append(col_cidade)

    # Manter apenas colunas que existem
    colunas_existentes = [c for c in colunas_base if c in df.columns]
    df = df[colunas_existentes].copy()

    # Padronizar data
    df['Data/Hora Empenho'] = pd.to_datetime(df['Data/Hora Empenho'], errors='coerce')

    # Dia da semana
    dias_da_semana = {
        0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira',
        3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
    }
    df['dia_semana'] = df['Data/Hora Empenho'].apply(
        lambda x: dias_da_semana[x.dayofweek] if pd.notnull(x) else None
    )

    # Tratar Estoque Físico → Estoque (nome abreviado)
    if 'Estoque Físico' in df.columns:
        df['Estoque Físico'] = df['Estoque Físico'].astype(str).str.replace(' - ', ' ').str[4:].str.strip()
        df['Estoque'] = df['Estoque Físico'].apply(lambda x: MAPA_ESTOQUE.get(x, x))

    # Status separação
    df['Status'] = df.groupby('Código Requisição')['Qtde Atendida'] \
                     .transform(lambda x: "Separado" if (x > 0).any() else "A Separar")

    # Manter linha mais representativa por requisição (prefere não-PROPRIO)
    def manter_nao_proprio(gr):
        nao_proprio = gr[gr['Estoque'] != 'PROPRIO']
        return nao_proprio.iloc[0] if not nao_proprio.empty else gr.iloc[0]

    df = df.groupby('Código Requisição', group_keys=False).apply(manter_nao_proprio)

    # Cidade
    if col_cidade and col_cidade in df.columns:
        df.rename(columns={col_cidade: "Cidade"}, inplace=True)
        df["Cidade"] = df["Cidade"].fillna("Não Identificada").astype(str).str.strip()
    else:
        df["Cidade"] = "Não Identificada"

    # Calcular prazo de retirada (5 dias desde empenho)
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    prazo_df = df.apply(lambda row: calcular_prazo(row, hoje), axis=1, result_type='expand')
    df = pd.concat([df, prazo_df], axis=1)

    # Remover colunas desnecessárias
    df.drop(columns=['Estoque Físico'], errors='ignore', inplace=True)

    return df.reset_index(drop=True)


# ========================
# Componentes UI
# ========================
def render_kpi(titulo, valor, cor, icone="", subtexto=""):
    st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {cor};">
            <div class="kpi-titulo">{icone} {titulo}</div>
            <div class="kpi-valor" style="color: {cor};">{valor}</div>
            <div class="kpi-subtexto">{subtexto}</div>
        </div>
    """, unsafe_allow_html=True)


def render_header():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    u = st.session_state.get("usuario_logado", {})
    nome = u.get("nome", "") if u else ""
    cidade = u.get("cidade") if u else None
    scope_label = f"🏙️ {cidade}" if cidade else "🌐 Todas as Cidades"
    st.markdown(f"""
        <div class="header-container">
            <h1>🌐 Painel Geral de Requisições</h1>
            <p>Monitoramento multi-cidade · Prazo de retirada: {PRAZO_RETIRADA_DIAS} dias ·
               Atualizado em {now} &nbsp;|  {scope_label} &nbsp;|  {nome}</p>
        </div>
    """, unsafe_allow_html=True)


def render_secao(titulo):
    st.markdown(f'<div class="secao-titulo">{titulo}</div>', unsafe_allow_html=True)


def layout_plotly(fig, altura=420, mostrar_titulo_layout=True):
    layout_opts = dict(
        template=PLOTLY_TEMPLATE,
        height=altura,
        margin=dict(l=40, r=30, t=60, b=40),
        font=dict(family="Segoe UI, sans-serif", size=12, color="#333"),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5,
            font=dict(size=11),
            bgcolor="rgba(255,255,255,0.7)",
            bordercolor="rgba(0,0,0,0.08)",
            borderwidth=1,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Segoe UI, sans-serif", bordercolor="#ddd"),
    )
    if mostrar_titulo_layout:
        layout_opts["title_font"] = dict(size=15, color=CORES["primaria"], family="Segoe UI, sans-serif")
    fig.update_layout(**layout_opts)
    fig.update_xaxes(showgrid=False, tickfont=dict(size=10))
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", tickfont=dict(size=10))
    return fig


@st.cache_data
def converter_excel(df: pd.DataFrame) -> bytes:
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Requisicoes")
    return output.getvalue()


# ========================
# CONFIGURAÇÃO DA PÁGINA
# ========================
st.set_page_config(
    page_title="Painel Geral de Requisições",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)
aplicar_css()
init_movimentacoes()

# ── Autenticação ── (bloqueia acesso antes de qualquer render)
usuario_logado = login_required()
_cidade_restrita = cidade_usuario()   # None = admin (vê tudo)

# ========================
# SIDEBAR
# ========================
with st.sidebar:
    # ── Info do usuário logado ──
    badge_role = "🔑 Admin" if is_admin() else "👤 Usuário"
    cidade_label = "🌐 Todas as cidades" if not _cidade_restrita else f"🏙️ {_cidade_restrita}"
    st.markdown(f"""
        <div style="text-align:center; padding: 10px 0 5px 0;">
            <span style="font-size: 2.2rem;">🌐</span>
            <h2 style="margin: 5px 0 0 0; font-size: 1.3rem;">Painel Geral</h2>
            <p style="font-size: 0.72rem; opacity: 0.75; margin-top: 4px;">{badge_role} · {usuario_logado['nome']}</p>
            <p style="font-size: 0.72rem; opacity: 0.6; margin-top: 0;">{cidade_label}</p>
        </div>
    """, unsafe_allow_html=True)

    col_l1, col_l2 = st.columns(2)
    with col_l1:
        if st.button("🚪 Sair", use_container_width=True, key="btn_logout"):
            logout()
    with col_l2:
        if st.button("🔑 Senha", use_container_width=True, key="btn_senha"):
            st.session_state["show_senha"] = not st.session_state.get("show_senha", False)

    # Formulário de troca de senha (expansível)
    if st.session_state.get("show_senha", False):
        with st.form("form_alterar_senha", clear_on_submit=True):
            st.markdown("**🔑 Alterar Senha**")
            senha_atual  = st.text_input("Senha atual",      type="password", key="sa")
            nova_senha   = st.text_input("Nova senha",        type="password", key="ns",
                                         help="Mínimo 6 caracteres")
            confirma     = st.text_input("Confirmar nova senha", type="password", key="cs")
            if st.form_submit_button("✅ Confirmar", use_container_width=True, type="primary"):
                ok, msg = alterar_senha(
                    usuario_logado["id"], senha_atual, nova_senha, confirma
                )
                if ok:
                    st.success(msg)
                    st.session_state["show_senha"] = False
                else:
                    st.error(msg)

    if is_admin():
        st.markdown("---")
        if st.button("⚙️ Administração", use_container_width=True, key="btn_admin"):
            st.session_state["pagina"] = "admin" if st.session_state.get("pagina") != "admin" else "dashboard"
            st.rerun()

    st.markdown("---")

    # Upload: admin e usuários com todas as cidades enviam qualquer base; demais só a própria cidade
    if is_admin() or not _cidade_restrita:
        st.markdown("### 📂 Importar geral.xlsx")
        upload_label = "Arquivo com requisições de todas as cidades."
    else:
        st.markdown(f"### 📂 Importar base — {_cidade_restrita}")
        upload_label = f"Arquivo de requisições da cidade: {_cidade_restrita}"

    arquivo = st.file_uploader(
        "Selecione o arquivo Excel",
        type=["xlsx"],
        label_visibility="collapsed",
        help=upload_label,
    )

    if arquivo:
        with st.spinner("Processando dados..."):
            df_raw = pd.read_excel(arquivo)
            df_tratado = tratar_dados(df_raw)

        # Usuário comum: filtrar apenas as linhas da própria cidade
        if not is_admin() and _cidade_restrita:
            if "Cidade" in df_tratado.columns:
                mascara = df_tratado["Cidade"].astype(str).apply(_norm) == _norm(_cidade_restrita)
                total_original = len(df_tratado)
                df_tratado = df_tratado[mascara].copy()
                ignorados = total_original - len(df_tratado)
                if ignorados:
                    st.info(f"ℹ️ {ignorados:,} registro(s) de outras cidades ignorados — apenas '{_cidade_restrita}' será atualizado.")
            else:
                # Se não há coluna Cidade, força a cidade do usuário
                df_tratado["Cidade"] = _cidade_restrita

        col_cidade_detectada = "Cidade" if "Cidade" in df_tratado.columns else None
        if col_cidade_detectada:
            n_cidades = df_tratado["Cidade"].nunique()
            st.success(f"✅ {len(df_tratado):,} registros · {n_cidades} cidade(s)")
        else:
            st.warning("⚠️ Coluna de cidade não encontrada.")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("💾 Salvar", use_container_width=True):
                # cidade_restrita=None significa acesso a todas → salva sem filtrar por cidade
                cidade_para_salvar = _cidade_restrita  # None = substitui tudo; str = substitui só a cidade
                salvar_no_banco(df_tratado, cidade=cidade_para_salvar)
                st.success("Salvo!")
                st.rerun()
        with col_b2:
            st.download_button(
                label="📥 Baixar",
                data=converter_excel(df_tratado),
                file_name="geral_tratado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    st.markdown("---")

    # Carregar dados do banco para filtros
    try:
        df_db = carregar_dados()
    except Exception:
        df_db = pd.DataFrame()

    filtro_cidades = []
    filtro_estoques = []
    filtro_status = []
    filtro_prazo = []
    filtro_volantes = []

    if not df_db.empty:
        st.markdown("### 🔍 Filtros")

        if "Cidade" in df_db.columns:
            cidades_disp = sorted(df_db["Cidade"].dropna().unique().tolist())
            if _cidade_restrita:
                # Usuário com cidade específica: busca case-insensitive
                cidade_match = next(
                    (c for c in cidades_disp
                     if _norm(c) == _norm(_cidade_restrita)),
                    None
                )
                if cidade_match:
                    filtro_cidades = [cidade_match]
                    st.markdown(f"🏙️ **Cidade:** {cidade_match}")
                else:
                    filtro_cidades = []
                    st.error(
                        f"⚠️ Sua cidade **'{_cidade_restrita}'** não foi encontrada nos dados. "
                        f"Contate o administrador para verificar o cadastro."
                    )
            else:
                # Admin ou usuário com todas as cidades: filtro livre
                todos_cidades = st.checkbox("Todas as Cidades", value=True, key="chk_cidades")
                filtro_cidades = st.multiselect(
                    "🏙️ Cidade", cidades_disp,
                    default=cidades_disp if todos_cidades else [],
                    disabled=todos_cidades,
                )
                if todos_cidades:
                    filtro_cidades = cidades_disp

        estoques_disp = sorted(df_db["Estoque"].dropna().unique().tolist())
        todos_estoques = st.checkbox("Todos os Estoques", value=True, key="chk_estoques")
        filtro_estoques = st.multiselect(
            "🏭 Estoque", estoques_disp,
            default=estoques_disp if todos_estoques else [],
            disabled=todos_estoques,
        )
        if todos_estoques:
            filtro_estoques = estoques_disp

        status_disp = sorted(df_db["Status"].dropna().unique().tolist())
        todos_status = st.checkbox("Todos os Status", value=True, key="chk_status")
        filtro_status = st.multiselect(
            "📊 Status", status_disp,
            default=status_disp if todos_status else [],
            disabled=todos_status,
        )
        if todos_status:
            filtro_status = status_disp

        if "Status_Prazo" in df_db.columns:
            prazo_categorias = ["🚨 Expirada", "📦 Em prazo", "⏳ Sem separação"]
            todos_prazo = st.checkbox("Todos os Prazos", value=True, key="chk_prazo")
            filtro_prazo = st.multiselect(
                "⏱️ Prazo", prazo_categorias,
                default=prazo_categorias if todos_prazo else [],
                disabled=todos_prazo,
            )
            if todos_prazo:
                filtro_prazo = prazo_categorias

        volantes_disp = sorted(df_db["Volante"].dropna().unique().tolist())
        todos_volantes = st.checkbox("Todos os Volantes", value=True, key="chk_volantes")
        filtro_volantes = st.multiselect(
            "👷 Volante", volantes_disp,
            default=volantes_disp if todos_volantes else [],
            disabled=todos_volantes,
        )
        if todos_volantes:
            filtro_volantes = volantes_disp

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; opacity:0.5; font-size:0.75rem; color:#ccc;'>"
        f"Desenvolvido Felipe G Canato<br>© 2026</div>",
        unsafe_allow_html=True,
    )


# ========================
# CONTEÚDO PRINCIPAL
# ========================
render_header()

if df_db.empty:
    st.info("📂 Nenhum dado no banco. Importe o **geral.xlsx** na sidebar para começar.")
    st.stop()

# ── Aplicar Filtros ──
df_filtrado = df_db.copy()

# Aplicar filtro de cidade
if _cidade_restrita:
    # Usuário com cidade específica: SEMPRE filtra, mesmo se não achou nos dados
    if filtro_cidades and "Cidade" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Cidade"].isin(filtro_cidades)]
    else:
        df_filtrado = df_filtrado.iloc[0:0]  # cidade não encontrada → vazio
elif filtro_cidades and "Cidade" in df_filtrado.columns:
    # Admin ou usuário com todas as cidades: aplica filtro livre
    df_filtrado = df_filtrado[df_filtrado["Cidade"].isin(filtro_cidades)]
if filtro_estoques:
    df_filtrado = df_filtrado[df_filtrado["Estoque"].isin(filtro_estoques)]
if filtro_status:
    df_filtrado = df_filtrado[df_filtrado["Status"].isin(filtro_status)]
if filtro_volantes:
    df_filtrado = df_filtrado[df_filtrado["Volante"].isin(filtro_volantes)]

# Filtro de prazo por categoria
if filtro_prazo and "Status_Prazo" in df_filtrado.columns:
    masks = []
    if "🚨 Expirada" in filtro_prazo:
        masks.append(df_filtrado["Status_Prazo"] == "🚨 Expirada")
    if "📦 Em prazo" in filtro_prazo:
        masks.append(df_filtrado["Status_Prazo"].str.startswith("📦"))
    if "⏳ Sem separação" in filtro_prazo:
        masks.append(df_filtrado["Status_Prazo"].str.startswith("⏳"))
    if masks:
        mask_total = masks[0]
        for m in masks[1:]:
            mask_total = mask_total | m
        df_filtrado = df_filtrado[mask_total]

if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

# ========================
# KPIs PRINCIPAIS
# ========================
if "Código Requisição" not in df_filtrado.columns:
    st.error(
        "❌ O banco de dados está com estrutura incompleta (coluna 'Código Requisição' ausente). "
        "Faça o upload do arquivo **geral.xlsx** novamente para reconstruir a tabela."
    )
    st.stop()

total_req = df_filtrado["Código Requisição"].nunique()
total_separado = df_filtrado[df_filtrado["Status"] == "Separado"]["Código Requisição"].nunique()
total_a_separar = df_filtrado[df_filtrado["Status"] == "A Separar"]["Código Requisição"].nunique()
total_expiradas = df_filtrado[df_filtrado["Status_Prazo"] == "🚨 Expirada"]["Código Requisição"].nunique() if "Status_Prazo" in df_filtrado.columns else 0
perc_separado = (total_separado / total_req * 100) if total_req > 0 else 0
total_cidades = df_filtrado["Cidade"].nunique() if "Cidade" in df_filtrado.columns else 0
total_volantes = df_filtrado["Volante"].nunique()

k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
with k1:
    render_kpi("Total Requisições", f"{total_req:,}".replace(",", "."), CORES["primaria"], "📋", "Únicas")
with k2:
    render_kpi("Separadas", f"{total_separado:,}".replace(",", "."), CORES["separado"], "✅", "Prontas")
with k3:
    render_kpi("A Separar", f"{total_a_separar:,}".replace(",", "."), CORES["a_separar"], "⏳", "Pendentes")
with k4:
    render_kpi("Expiradas", f"{total_expiradas:,}".replace(",", "."), CORES["expirada"], "🚨", f"+{PRAZO_RETIRADA_DIAS} dias")
with k5:
    render_kpi("% Separado", f"{perc_separado:.1f}%", CORES["secundaria"], "📊", "Taxa conclusão")
with k6:
    render_kpi("Cidades", f"{total_cidades}", CORES["info"], "🌐", "Municípios")
with k7:
    render_kpi("Volantes", f"{total_volantes}", CORES["alerta"], "👷", "Profissionais")

st.markdown("---")

# ── Alerta de expiradas ──
if total_expiradas > 0:
    st.markdown(f"""
        <div class="alerta-expiracao">
            🚨 ATENÇÃO: <strong>{total_expiradas}</strong> requisição(ões) expiraram o prazo de {PRAZO_RETIRADA_DIAS} dias.
            Verifique a aba <strong>⏱️ Prazos</strong> para detalhes.
        </div>
    """, unsafe_allow_html=True)

# ========================
# PAINEL ADMIN (inline — para Streamlit Cloud)
# ========================
if is_admin() and st.session_state.get("pagina") == "admin":
    from auth import (
        listar_usuarios, criar_usuario, atualizar_usuario,
        excluir_usuario, listar_cidades_dados, _norm_cidade,
    )
    import pandas as _pd

    st.markdown("## ⚙️ Administração de Usuários")
    if st.button("← Voltar ao Painel", key="btn_voltar_admin"):
        st.session_state["pagina"] = "dashboard"
        st.rerun()
    st.markdown("---")

    aba_lista_a, aba_criar_a, aba_senha_a = st.tabs(["📋 Usuários", "➕ Criar", "🔑 Alterar Senha"])

    with aba_lista_a:
        _usuarios = listar_usuarios()
        if _usuarios:
            _m1, _m2, _m3 = st.columns(3)
            _m1.metric("Total", len(_usuarios))
            _m2.metric("Admins", sum(1 for u in _usuarios if u["role"] == "admin"))
            _m3.metric("Cidades", len({u["cidade"] for u in _usuarios if u["cidade"]}))
            _df = _pd.DataFrame(_usuarios)[["username", "nome", "cidade", "role", "criado_em"]]
            _df.columns = ["Username", "Nome", "Cidade", "Perfil", "Criado em"]
            _df["Cidade"] = _df["Cidade"].fillna("🌐 Todas")
            _df["Perfil"] = _df["Perfil"].map({"admin": "🔑 Admin", "usuario": "👤 Usuário"})
            _df["Criado em"] = _pd.to_datetime(_df["Criado em"], errors="coerce").dt.strftime("%d/%m/%Y %H:%M")
            st.dataframe(_df, use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("### ✏️ Editar Usuário")
            _cidades_d = listar_cidades_dados()
            _sel = st.selectbox("Usuário", [u["username"] for u in _usuarios],
                                format_func=lambda x: next(f"{'🔑' if u['role']=='admin' else '👤'} {u['nome']} ({x})" for u in _usuarios if u["username"] == x),
                                key="admin_sel_edit")
            _u = next(u for u in _usuarios if u["username"] == _sel)
            with st.form("admin_form_editar"):
                _c1, _c2 = st.columns(2)
                with _c1:
                    _novo_nome = st.text_input("Nome", value=_u["nome"])
                    _novo_role = st.selectbox("Perfil", ["usuario", "admin"], index=0 if _u["role"] == "usuario" else 1)
                with _c2:
                    if _novo_role == "admin":
                        st.info("🌐 Admin tem acesso a todas as cidades automaticamente.")
                        _nova_cidade = ""
                        _edit_todas = True
                    else:
                        _edit_todas = st.checkbox("🌐 Liberar todas as cidades", value=(_u["cidade"] is None), key="edit_todas_cidades")
                        if _edit_todas:
                            _nova_cidade = ""
                            st.info("Usuário terá acesso a todas as cidades (sem ser admin).")
                        elif _cidades_d:
                            _idx_edit = next((i for i, c in enumerate(_cidades_d) if _norm_cidade(c) == _norm_cidade(_u["cidade"] or "")), None)
                            _sel_c = st.selectbox("Cidade", _cidades_d + ["(outra)"], index=_idx_edit if _idx_edit is not None else 0)
                            _nova_cidade = st.text_input("Outra cidade", value=_u["cidade"] or "", placeholder="Digite o nome da cidade") if _sel_c == "(outra)" else _sel_c
                        else:
                            _nova_cidade = st.text_input("Cidade", value=_u["cidade"] or "")
                _btn_s, _btn_d = st.columns(2)
                with _btn_s: _salvar = st.form_submit_button("💾 Salvar", use_container_width=True, type="primary")
                with _btn_d: _excluir = st.form_submit_button("🗑️ Excluir", use_container_width=True)
            if _salvar:
                _cv = None if (_novo_role == "admin" or _edit_todas) else _nova_cidade.strip() or None
                ok, msg = atualizar_usuario(_u["id"], _novo_nome, _cv, _novo_role)
                st.success(msg) if ok else st.error(msg)
                if ok: st.rerun()
            if _excluir:
                ok, msg = excluir_usuario(_u["id"])
                st.success(msg) if ok else st.error(msg)
                if ok: st.rerun()

    with aba_criar_a:
        _cidades_d2 = listar_cidades_dados()
        with st.form("admin_form_criar", clear_on_submit=True):
            _c1, _c2 = st.columns(2)
            with _c1:
                _n_user = st.text_input("Username *", placeholder="joao.silva")
                _n_nome = st.text_input("Nome *", placeholder="João Silva")
            with _c2:
                _n_role = st.selectbox("Perfil *", ["usuario", "admin"])
                if _n_role == "admin":
                    st.info("🌐 Admin tem acesso a todas as cidades automaticamente.")
                    _n_cidade = ""
                    _n_todas = True
                else:
                    _n_todas = st.checkbox("🌐 Liberar todas as cidades", key="criar_todas_cidades")
                    if _n_todas:
                        _n_cidade = ""
                        st.info("Usuário terá acesso a todas as cidades (sem ser admin).")
                    elif _cidades_d2:
                        _s_nc = st.selectbox("Cidade * (obrigatória)", _cidades_d2 + ["(outra)"])
                        _n_cidade = st.text_input("Outra cidade *", placeholder="Digite o nome da cidade") if _s_nc == "(outra)" else _s_nc
                    else:
                        _n_cidade = st.text_input("Cidade * (obrigatória)", placeholder="Ex: Ribeirão Preto")
            _n_senha = st.text_input("Senha *", type="password")
            _n_conf  = st.text_input("Confirmar senha *", type="password")
            _sub = st.form_submit_button("✅ Criar Usuário", use_container_width=True, type="primary")
        if _sub:
            if _n_senha != _n_conf: st.error("❌ Senhas não coincidem.")
            elif len(_n_senha) < 6: st.error("❌ Mínimo 6 caracteres.")
            elif _n_role == "usuario" and not _n_todas and not _n_cidade.strip(): st.error("❌ Selecione uma cidade ou marque 'Liberar todas as cidades'.")
            else:
                _cv = None if (_n_role == "admin" or _n_todas) else _n_cidade.strip()
                ok, msg = criar_usuario(_n_user, _n_nome, _n_senha, _cv, _n_role)
                st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")
                if ok: st.rerun()

    with aba_senha_a:
        _usuarios_s = listar_usuarios()
        _sel_s = st.selectbox("Usuário", [u["username"] for u in _usuarios_s],
                              format_func=lambda x: next(f"{'🔑' if u['role']=='admin' else '👤'} {u['nome']} ({x})" for u in _usuarios_s if u["username"] == x),
                              key="admin_sel_senha")
        _u_s = next(u for u in _usuarios_s if u["username"] == _sel_s)
        with st.form("admin_form_senha", clear_on_submit=True):
            st.markdown(f"**{_u_s['nome']}** (`{_u_s['username']}`)")
            _ns = st.text_input("Nova senha *", type="password")
            _nc = st.text_input("Confirmar *", type="password")
            _btn_r = st.form_submit_button("🔑 Redefinir", use_container_width=True, type="primary")
        if _btn_r:
            if not _ns or not _nc: st.error("❌ Preencha os campos.")
            elif _ns != _nc: st.error("❌ Senhas não coincidem.")
            elif len(_ns) < 6: st.error("❌ Mínimo 6 caracteres.")
            else:
                ok, msg = atualizar_usuario(_u_s["id"], _u_s["nome"], _u_s["cidade"], _u_s["role"], _ns)
                st.success(f"✅ Senha de **{_u_s['nome']}** redefinida.") if ok else st.error(msg)

    st.stop()

# ========================
# ABAS PRINCIPAIS
# ========================
tab_visao, tab_estoques, tab_cidades, tab_prazos, tab_volantes, tab_dados = st.tabs([
    "📊 Visão Geral",
    "🏭 Estoques (Multi-Cidade)",
    "🌐 Análise por Cidade",
    "⏱️ Prazos de Retirada",
    "👷 Volantes",
    "📋 Dados",
])


# ─────────────────────────────────────
# ABA 1 — Visão Geral
# ─────────────────────────────────────
with tab_visao:
    col_a, col_b = st.columns(2)

    with col_a:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=perc_separado,
            number={"suffix": "%", "font": {"size": 42, "color": CORES["primaria"]}},
            delta={"reference": 100, "increasing": {"color": CORES["separado"]}, "suffix": "%"},
            title={"text": "Taxa de Separação (Todas as Cidades)", "font": {"size": 14, "color": CORES["primaria"]}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": CORES["secundaria"], "thickness": 0.3},
                "steps": [
                    {"range": [0, 40], "color": "#FDEDEC"},
                    {"range": [40, 70], "color": "#FEF9E7"},
                    {"range": [70, 100], "color": "#EAFAF1"},
                ],
                "threshold": {"line": {"color": CORES["a_separar"], "width": 3}, "thickness": 0.8, "value": perc_separado},
            },
        ))
        fig_gauge = layout_plotly(fig_gauge, altura=350, mostrar_titulo_layout=False)
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_b:
        labels = ["Separado", "A Separar", "Expirada"]
        values = [total_separado, total_a_separar, total_expiradas]
        colors = [CORES["separado"], CORES["a_separar"], CORES["expirada"]]
        fig_donut = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.55,
            marker=dict(colors=colors, line=dict(color="white", width=3)),
            textinfo="label+percent", textfont=dict(size=12),
            hovertemplate="<b>%{label}</b><br>Qtd: %{value}<br>%{percent}<extra></extra>",
        ))
        fig_donut.update_layout(
            title=dict(text="Distribuição Geral", font=dict(size=15, color=CORES["primaria"])),
            annotations=[dict(text=f"{total_req}", x=0.5, y=0.5, font_size=26, font_color=CORES["primaria"], showarrow=False)],
        )
        fig_donut = layout_plotly(fig_donut, altura=350, mostrar_titulo_layout=False)
        st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown("---")

    # Barras: Status por Estoque
    agrupado_est = df_filtrado.groupby(["Estoque", "Status"]).size().reset_index(name="Quantidade")
    fig_bar = px.bar(
        agrupado_est, x="Estoque", y="Quantidade", color="Status", barmode="group",
        title="Separado vs A Separar por Estoque (Todas as Cidades)",
        color_discrete_map={"Separado": CORES["separado"], "A Separar": CORES["a_separar"]},
        text="Quantidade",
    )
    fig_bar.update_traces(textposition="outside", textfont_size=10)
    fig_bar = layout_plotly(fig_bar, altura=440)
    st.plotly_chart(fig_bar, use_container_width=True)

    # Distribuição por dia da semana
    if "dia_semana" in df_filtrado.columns:
        ordem_dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
        df_dia = df_filtrado.groupby(["dia_semana", "Status"]).size().reset_index(name="Quantidade")
        df_dia["dia_semana"] = pd.Categorical(df_dia["dia_semana"], categories=ordem_dias, ordered=True)
        df_dia = df_dia.sort_values("dia_semana")
        fig_dia = px.bar(
            df_dia, x="dia_semana", y="Quantidade", color="Status", barmode="stack",
            title="Distribuição por Dia da Semana (Empenho)",
            color_discrete_map={"Separado": CORES["separado"], "A Separar": CORES["a_separar"]},
            labels={"dia_semana": "Dia da Semana"},
        )
        fig_dia = layout_plotly(fig_dia, altura=380)
        st.plotly_chart(fig_dia, use_container_width=True)


# ─────────────────────────────────────
# ABA 2 — Estoques Multi-Cidade
# ─────────────────────────────────────
with tab_estoques:
    render_secao("🏭 Mapa de Estoques — Padrão entre Cidades")

    # Resumo por estoque
    resumo_est = df_filtrado.groupby("Estoque").agg(
        Total=("Código Requisição", "nunique"),
        Separado=("Status", lambda x: (x == "Separado").sum()),
        A_Separar=("Status", lambda x: (x == "A Separar").sum()),
        Cidades=("Cidade", "nunique"),
    ).reset_index()
    resumo_est["% Separado"] = (resumo_est["Separado"] / resumo_est["Total"] * 100).round(1)
    resumo_est = resumo_est.sort_values("Total", ascending=False)

    # Barras horizontais empilhadas
    fig_h = go.Figure()
    fig_h.add_trace(go.Bar(
        y=resumo_est["Estoque"], x=resumo_est["Separado"], name="Separado",
        orientation="h", marker_color=CORES["separado"],
        text=resumo_est["Separado"], textposition="inside",
    ))
    fig_h.add_trace(go.Bar(
        y=resumo_est["Estoque"], x=resumo_est["A_Separar"], name="A Separar",
        orientation="h", marker_color=CORES["a_separar"],
        text=resumo_est["A_Separar"], textposition="inside",
    ))
    fig_h.update_layout(barmode="stack", title="Requisições por Estoque (Todas as Cidades)")
    fig_h = layout_plotly(fig_h, altura=max(350, len(resumo_est) * 35))
    fig_h.update_yaxes(showgrid=False)
    st.plotly_chart(fig_h, use_container_width=True)

    st.markdown("---")
    render_secao("🗺️ Mapa de Calor — Cidade × Estoque")

    # Heatmap Cidade x Estoque
    if "Cidade" in df_filtrado.columns:
        cidade_estoque = df_filtrado.groupby(["Cidade", "Estoque"]).size().reset_index(name="Quantidade")
        pivot_ce = cidade_estoque.pivot(index="Cidade", columns="Estoque", values="Quantidade").fillna(0)

        fig_heat = px.imshow(
            pivot_ce,
            title="Volume de Requisições: Cidade × Estoque",
            labels=dict(x="Estoque", y="Cidade", color="Qtd"),
            color_continuous_scale=["#f0f4f8", CORES["secundaria"], CORES["primaria"]],
            text_auto=True,
            aspect="auto",
        )
        fig_heat = layout_plotly(fig_heat, altura=max(300, len(pivot_ce) * 45))
        st.plotly_chart(fig_heat, use_container_width=True)

        # Heatmap de % Separado por Cidade x Estoque
        st.markdown("---")
        render_secao("📊 % Separado por Cidade × Estoque")

        sep_ce = df_filtrado[df_filtrado["Status"] == "Separado"].groupby(["Cidade", "Estoque"]).size().reset_index(name="Separado")
        total_ce = df_filtrado.groupby(["Cidade", "Estoque"]).size().reset_index(name="Total")
        merged_ce = total_ce.merge(sep_ce, on=["Cidade", "Estoque"], how="left").fillna(0)
        merged_ce["% Separado"] = (merged_ce["Separado"] / merged_ce["Total"] * 100).round(1)
        pivot_perc = merged_ce.pivot(index="Cidade", columns="Estoque", values="% Separado").fillna(0)

        fig_heat_perc = px.imshow(
            pivot_perc,
            title="% Separado por Cidade × Estoque",
            labels=dict(x="Estoque", y="Cidade", color="% Sep."),
            color_continuous_scale=["#FDEDEC", "#FEF9E7", "#EAFAF1"],
            zmin=0, zmax=100,
            text_auto=".1f",
            aspect="auto",
        )
        fig_heat_perc = layout_plotly(fig_heat_perc, altura=max(300, len(pivot_perc) * 45))
        st.plotly_chart(fig_heat_perc, use_container_width=True)

    st.markdown("---")
    render_secao("📋 Resumo por Estoque")
    st.dataframe(
        resumo_est.rename(columns={"Cidades": "Nº Cidades"}).style
            .format({"% Separado": "{:.1f}%"})
            .background_gradient(cmap="RdYlGn", subset=["% Separado"])
            .set_properties(**{"text-align": "center"}),
        use_container_width=True,
        hide_index=True,
        height=min(450, 40 + len(resumo_est) * 35),
    )

    # Treemap
    st.markdown("---")
    if "Cidade" in df_filtrado.columns:
        agrup_tree = df_filtrado.groupby(["Cidade", "Estoque", "Status"]).size().reset_index(name="Quantidade")
        fig_tree = px.treemap(
            agrup_tree, path=["Cidade", "Estoque", "Status"], values="Quantidade",
            title="Treemap — Cidade → Estoque → Status",
            color="Quantidade",
            color_continuous_scale=["#eaf6f6", CORES["secundaria"], CORES["primaria"]],
        )
        fig_tree = layout_plotly(fig_tree, altura=550)
        fig_tree.update_traces(textinfo="label+value+percent root")
        st.plotly_chart(fig_tree, use_container_width=True)


# ─────────────────────────────────────
# ABA 3 — Análise por Cidade
# ─────────────────────────────────────
with tab_cidades:
    render_secao("🌐 Performance por Cidade")

    if "Cidade" in df_filtrado.columns:
        resumo_cid = df_filtrado.groupby("Cidade").agg(
            Total=("Código Requisição", "nunique"),
            Separado=("Status", lambda x: (x == "Separado").sum()),
            A_Separar=("Status", lambda x: (x == "A Separar").sum()),
            Expiradas=("Status_Prazo", lambda x: (x == "🚨 Expirada").sum()) if "Status_Prazo" in df_filtrado.columns else ("Status", lambda x: 0),
            Volantes=("Volante", "nunique"),
            Estoques=("Estoque", "nunique"),
        ).reset_index()
        resumo_cid["% Separado"] = (resumo_cid["Separado"] / resumo_cid["Total"] * 100).round(1)
        resumo_cid = resumo_cid.sort_values("Total", ascending=False)

        # KPI cards por cidade
        cols = st.columns(min(4, len(resumo_cid)))
        for i, (_, row) in enumerate(resumo_cid.iterrows()):
            with cols[i % len(cols)]:
                render_kpi(
                    row["Cidade"],
                    f"{row['Total']}",
                    CORES["gradiente"][i % len(CORES["gradiente"])],
                    "🌐",
                    f"✅ {row['Separado']} | ⏳ {row['A_Separar']} | 🚨 {row.get('Expiradas', 0)} exp. | {row['% Separado']:.0f}%"
                )

        st.markdown("---")

        # Barras horizontais empilhadas — funciona bem com qualquer nº de cidades
        agrup_cid = df_filtrado.groupby(["Cidade", "Status"]).size().reset_index(name="Quantidade")
        resumo_cid_ord = resumo_cid.sort_values("Total", ascending=True)

        fig_cid_h = go.Figure()
        fig_cid_h.add_trace(go.Bar(
            y=resumo_cid_ord["Cidade"],
            x=resumo_cid_ord["Separado"],
            name="Separado",
            orientation="h",
            marker_color=CORES["separado"],
            text=resumo_cid_ord["Separado"],
            textposition="inside",
            insidetextanchor="middle",
            hovertemplate="<b>%{y}</b><br>Separado: %{x}<extra></extra>",
        ))
        fig_cid_h.add_trace(go.Bar(
            y=resumo_cid_ord["Cidade"],
            x=resumo_cid_ord["A_Separar"],
            name="A Separar",
            orientation="h",
            marker_color=CORES["a_separar"],
            text=resumo_cid_ord["A_Separar"],
            textposition="inside",
            insidetextanchor="middle",
            hovertemplate="<b>%{y}</b><br>A Separar: %{x}<extra></extra>",
        ))
        fig_cid_h.update_layout(
            barmode="stack",
            title="Distribuição de Requisições por Cidade",
        )
        fig_cid_h = layout_plotly(fig_cid_h, altura=max(380, len(resumo_cid_ord) * 42))
        fig_cid_h.update_yaxes(showgrid=False, tickfont=dict(size=12))
        fig_cid_h.update_xaxes(showgrid=True)
        st.plotly_chart(fig_cid_h, use_container_width=True)

        # % Separado por cidade — barras horizontais com gradiente de cor
        st.markdown("---")
        fig_perc_cid = px.bar(
            resumo_cid_ord,
            x="% Separado",
            y="Cidade",
            orientation="h",
            title="% Separado por Cidade",
            color="% Separado",
            color_continuous_scale=["#E74C3C", "#F39C12", "#2ECC71"],
            range_color=[0, 100],
            text="% Separado",
        )
        fig_perc_cid.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            textfont_size=11,
        )
        fig_perc_cid.update_xaxes(range=[0, 115])
        fig_perc_cid = layout_plotly(fig_perc_cid, altura=max(380, len(resumo_cid_ord) * 42))
        fig_perc_cid.update_yaxes(showgrid=False, tickfont=dict(size=12))
        st.plotly_chart(fig_perc_cid, use_container_width=True)

        # Gráfico de expiradas por cidade
        if "Status_Prazo" in df_filtrado.columns:
            st.markdown("---")
            exp_cid = df_filtrado[df_filtrado["Status_Prazo"] == "🚨 Expirada"] \
                .groupby("Cidade").size().reset_index(name="Expiradas") \
                .sort_values("Expiradas", ascending=False)

            if not exp_cid.empty:
                fig_exp = px.bar(
                    exp_cid, x="Cidade", y="Expiradas",
                    title="🚨 Requisições Expiradas por Cidade",
                    color="Expiradas",
                    color_continuous_scale=["#FEF9E7", "#E74C3C", "#8E44AD"],
                    text="Expiradas",
                )
                fig_exp.update_traces(textposition="outside")
                fig_exp = layout_plotly(fig_exp, altura=380)
                st.plotly_chart(fig_exp, use_container_width=True)

        render_secao("📋 Tabela Resumo por Cidade")
        st.dataframe(
            resumo_cid.style
                .format({"% Separado": "{:.1f}%"})
                .background_gradient(cmap="RdYlGn", subset=["% Separado"])
                .set_properties(**{"text-align": "center"}),
            use_container_width=True,
            hide_index=True,
            height=min(450, 40 + len(resumo_cid) * 35),
        )
    else:
        st.warning("⚠️ Coluna 'Cidade' não detectada nos dados. Verifique se o geral.xlsx possui essa coluna.")


# ─────────────────────────────────────
# ABA 4 — Prazos de Retirada
# ─────────────────────────────────────
with tab_prazos:
    render_secao(f"⏱️ Controle de Prazo de Retirada ({PRAZO_RETIRADA_DIAS} dias desde o empenho)")

    if "Status_Prazo" not in df_filtrado.columns:
        st.warning("⚠️ Dados de prazo não disponíveis. Reimporte o arquivo.")
    else:
        # KPIs de prazo
        df_exp = df_filtrado[df_filtrado["Status_Prazo"] == "🚨 Expirada"]
        df_em_prazo = df_filtrado[df_filtrado["Status_Prazo"].str.startswith("📦", na=False)]
        df_aguard_sep = df_filtrado[df_filtrado["Status_Prazo"].str.startswith("⏳", na=False)]

        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        with col_p1:
            render_kpi("Expiradas", f"{len(df_exp)}", CORES["expirada"], "🚨",
                       f"{df_exp['Cidade'].nunique() if 'Cidade' in df_exp.columns else 0} cidades afetadas")
        with col_p2:
            render_kpi("Em Prazo (Separado)", f"{len(df_em_prazo)}", CORES["separado"], "📦",
                       "Aguardando retirada")
        with col_p3:
            render_kpi("Aguardando Separação", f"{len(df_aguard_sep)}", CORES["info"], "⏳",
                       "Dentro do prazo")
        with col_p4:
            avg_dias = df_filtrado["Dias_Empenho"].mean() if "Dias_Empenho" in df_filtrado.columns else 0
            render_kpi("Média Dias Empenho", f"{avg_dias:.1f}", CORES["alerta"], "📅",
                       "Dias desde empenho")

        st.markdown("---")

        # Gráfico de distribuição de dias desde empenho
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            df_ret_chart = df_filtrado.groupby("Status_Prazo").size().reset_index(name="Quantidade")
            cores_prazo = {}
            for val in df_ret_chart["Status_Prazo"]:
                if "Expirada" in val:
                    cores_prazo[val] = CORES["expirada"]
                elif val.startswith("📦"):
                    cores_prazo[val] = CORES["separado"]
                else:
                    cores_prazo[val] = CORES["info"]

            fig_prazo_pie = px.pie(
                df_ret_chart, values="Quantidade", names="Status_Prazo",
                title="Distribuição por Status de Prazo",
                hole=0.5, color="Status_Prazo", color_discrete_map=cores_prazo,
            )
            fig_prazo_pie.update_traces(
                textinfo="label+percent+value", textfont_size=11,
                pull=[0.1 if "Expirada" in str(v) else 0 for v in df_ret_chart["Status_Prazo"]],
            )
            fig_prazo_pie = layout_plotly(fig_prazo_pie, altura=400, mostrar_titulo_layout=False)
            fig_prazo_pie.update_layout(
                title=dict(text="Distribuição por Status de Prazo", font=dict(size=15, color=CORES["primaria"])),
            )
            st.plotly_chart(fig_prazo_pie, use_container_width=True)

        with col_g2:
            if "Dias_Empenho" in df_filtrado.columns:
                fig_hist = px.histogram(
                    df_filtrado, x="Dias_Empenho", nbins=20,
                    title="Distribuição de Dias desde Empenho",
                    color_discrete_sequence=[CORES["secundaria"]],
                    labels={"Dias_Empenho": "Dias desde o Empenho", "count": "Requisições"},
                )
                fig_hist.add_vline(
                    x=PRAZO_RETIRADA_DIAS, line_dash="dash", line_color=CORES["perigo"],
                    annotation_text=f"Limite ({PRAZO_RETIRADA_DIAS} dias)",
                    annotation_position="top right",
                )
                fig_hist = layout_plotly(fig_hist, altura=400)
                st.plotly_chart(fig_hist, use_container_width=True)

        # Expiradas por cidade
        if not df_exp.empty and "Cidade" in df_exp.columns:
            st.markdown("---")
            render_secao("🚨 Detalhamento das Requisições Expiradas")

            exp_cidade = df_exp.groupby("Cidade").agg(
                Expiradas=("Código Requisição", "nunique"),
                Volantes=("Volante", "nunique"),
                Media_Dias=("Dias_Empenho", "mean"),
            ).reset_index().sort_values("Expiradas", ascending=False)
            exp_cidade["Media_Dias"] = exp_cidade["Media_Dias"].round(1)

            fig_exp_cid = px.bar(
                exp_cidade, x="Expiradas", y="Cidade", orientation="h",
                title="Expiradas por Cidade",
                color="Expiradas",
                color_continuous_scale=["#FEF9E7", CORES["perigo"], CORES["expirada"]],
                text="Expiradas",
            )
            fig_exp_cid.update_traces(textposition="outside")
            fig_exp_cid = layout_plotly(fig_exp_cid, altura=max(300, len(exp_cidade) * 40))
            fig_exp_cid.update_yaxes(showgrid=False)
            st.plotly_chart(fig_exp_cid, use_container_width=True)

            cols_exp = ["Volante", "Cidade", "Código Requisição", "Data/Hora Empenho",
                        "Estoque", "Status", "Dias_Empenho", "Status_Prazo"]
            cols_exp = [c for c in cols_exp if c in df_exp.columns]
            st.dataframe(
                df_exp[cols_exp].sort_values("Dias_Empenho", ascending=False),
                use_container_width=True, hide_index=True,
            )

        # Requisições que vencem em breve (próximos 2 dias)
        if "Dias_Restantes" in df_filtrado.columns:
            df_urgente = df_filtrado[
                (df_filtrado["Dias_Restantes"] <= 2) & (df_filtrado["Dias_Restantes"] > 0)
            ]
            if not df_urgente.empty:
                st.markdown("---")
                render_secao(f"⚠️ Requisições Urgentes — Vencem em até 2 dia(s)")
                cols_urg = ["Volante", "Cidade", "Código Requisição", "Data/Hora Empenho",
                            "Estoque", "Status", "Dias_Restantes", "Status_Prazo"]
                cols_urg = [c for c in cols_urg if c in df_urgente.columns]
                st.dataframe(
                    df_urgente[cols_urg].sort_values("Dias_Restantes"),
                    use_container_width=True, hide_index=True,
                )


# ─────────────────────────────────────
# ABA 5 — Volantes
# ─────────────────────────────────────
with tab_volantes:
    render_secao("👷 Performance por Volante")

    resumo_vol = df_filtrado.groupby("Volante").agg(
        Total=("Código Requisição", "nunique"),
        Separado=("Status", lambda x: (x == "Separado").sum()),
        A_Separar=("Status", lambda x: (x == "A Separar").sum()),
        Expiradas=("Status_Prazo", lambda x: (x == "🚨 Expirada").sum()) if "Status_Prazo" in df_filtrado.columns else ("Status", lambda x: 0),
        Cidades=("Cidade", "nunique") if "Cidade" in df_filtrado.columns else ("Status", lambda x: 0),
    ).reset_index()
    resumo_vol["% Separado"] = (resumo_vol["Separado"] / resumo_vol["Total"] * 100).round(1)
    resumo_vol = resumo_vol.sort_values("Total", ascending=False)

    top_vol = resumo_vol.head(15)

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        fig_vol_bar = px.bar(
            top_vol, x="Total", y="Volante", orientation="h",
            title="Top 15 Volantes — Total de Requisições",
            color="% Separado",
            color_continuous_scale=["#E74C3C", "#F39C12", "#2ECC71"],
            text="Total",
        )
        fig_vol_bar.update_traces(textposition="outside")
        fig_vol_bar = layout_plotly(fig_vol_bar, altura=480)
        fig_vol_bar.update_yaxes(showgrid=False)
        st.plotly_chart(fig_vol_bar, use_container_width=True)

    with col_v2:
        fig_vol_scatter = px.scatter(
            resumo_vol, x="Separado", y="A_Separar", size="Total",
            color="% Separado", hover_name="Volante",
            title="Dispersão — Separado vs A Separar",
            color_continuous_scale=["#E74C3C", "#F39C12", "#2ECC71"],
            labels={"Separado": "Qtd Separado", "A_Separar": "Qtd A Separar"},
        )
        fig_vol_scatter = layout_plotly(fig_vol_scatter, altura=480)
        st.plotly_chart(fig_vol_scatter, use_container_width=True)

    # Volantes com mais expiradas
    if "Expiradas" in resumo_vol.columns and resumo_vol["Expiradas"].sum() > 0:
        st.markdown("---")
        render_secao("🚨 Volantes com Requisições Expiradas")
        vol_exp = resumo_vol[resumo_vol["Expiradas"] > 0].sort_values("Expiradas", ascending=False)
        fig_vol_exp = px.bar(
            vol_exp.head(20), x="Expiradas", y="Volante", orientation="h",
            title="Top Volantes — Requisições Expiradas",
            color="Expiradas",
            color_continuous_scale=["#FEF9E7", CORES["perigo"], CORES["expirada"]],
            text="Expiradas",
        )
        fig_vol_exp.update_traces(textposition="outside")
        fig_vol_exp = layout_plotly(fig_vol_exp, altura=max(300, len(vol_exp.head(20)) * 38))
        fig_vol_exp.update_yaxes(showgrid=False)
        st.plotly_chart(fig_vol_exp, use_container_width=True)

    render_secao("📋 Tabela Detalhada — Volantes")
    st.dataframe(
        resumo_vol.style
            .format({"% Separado": "{:.1f}%"})
            .background_gradient(cmap="RdYlGn", subset=["% Separado"])
            .set_properties(**{"text-align": "center"}),
        use_container_width=True,
        hide_index=True,
        height=min(500, 40 + len(resumo_vol) * 35),
    )


# ─────────────────────────────────────
# ABA 6 — Dados
# ─────────────────────────────────────
with tab_dados:
    render_secao("📋 Dados Completos (Filtrados)")

    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
    with col_info1:
        st.metric("Linhas", f"{len(df_filtrado):,}".replace(",", "."))
    with col_info2:
        st.metric("Colunas", f"{len(df_filtrado.columns)}")
    with col_info3:
        st.metric("Requisições Únicas", f"{df_filtrado['Código Requisição'].nunique():,}".replace(",", "."))
    with col_info4:
        st.metric("Cidades", f"{df_filtrado['Cidade'].nunique() if 'Cidade' in df_filtrado.columns else 'N/A'}")

    busca = st.text_input("🔎 Buscar na tabela (código, produto, volante, cidade...)", "")
    df_exibir = df_filtrado.copy()
    if busca:
        mask = df_exibir.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_exibir = df_exibir[mask]

    st.dataframe(df_exibir, use_container_width=True, hide_index=True, height=600)

    st.download_button(
        label="📥 Baixar Dados Filtrados (.xlsx)",
        data=converter_excel(df_exibir),
        file_name="requisicoes_filtradas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
