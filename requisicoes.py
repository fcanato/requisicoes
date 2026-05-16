import pandas as pd
import numpy as np
import sqlite3
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

# ========================
# Paleta de Cores Profissional
# ========================
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
    "gradiente": ["#1B2A4A", "#2E86AB", "#48C9B0", "#F39C12", "#E74C3C", "#8E44AD", "#3498DB"],
}

PLOTLY_TEMPLATE = "plotly_white"

# ========================
# CSS Customizado
# ========================
def aplicar_css():
    st.markdown("""
    <style>
        /* Esconder menu e rodapé padrão */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* KPI Cards */
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

        /* Cabeçalho */
        .header-container {
            background: linear-gradient(135deg, #1B2A4A 0%, #2E86AB 100%);
            padding: 30px 40px;
            border-radius: 16px;
            margin-bottom: 25px;
            color: white;
        }
        .header-container h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
        }
        .header-container p {
            margin: 5px 0 0 0;
            font-size: 0.95rem;
            opacity: 0.85;
        }

        /* Seções */
        .secao-titulo {
            font-size: 1.15rem;
            font-weight: 700;
            color: #1B2A4A;
            border-bottom: 3px solid #2E86AB;
            padding-bottom: 8px;
            margin: 30px 0 15px 0;
        }

        /* Sidebar */
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

        /* Tabela */
        .dataframe-container {
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        }

        /* Divider */
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #2E86AB, transparent);
            margin: 20px 0;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 10px 24px;
            font-weight: 600;
        }

        /* Botão nativo de toggle da sidebar */
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
        [data-testid="stSidebarCollapsedControl"] button:hover,
        [data-testid="collapsedControl"] button:hover {
            transform: scale(1.1) !important;
            box-shadow: 0 5px 18px rgba(27,42,74,0.45) !important;
        }

        /* Botão de fechar dentro da sidebar */
        [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button {
            color: #ffffff !important;
            background: rgba(255,255,255,0.1) !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button:hover {
            background: rgba(255,255,255,0.25) !important;
        }

        /* Sidebar com transição suave */
        [data-testid="stSidebar"] > div:first-child {
            transition: all 0.3s ease;
        }
    </style>
    """, unsafe_allow_html=True)


# ========================
# Funções Banco de Dados
# ========================
def init_db():
    conn = sqlite3.connect("movimentacoes.db")
    cursor = conn.cursor()
    cursor.execute("""
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
            'Descrição Segmento Destino' TEXT,
            'Estoque Físico' TEXT,
            'Estoque' TEXT,
            'Status' TEXT,
            'dia_semana' TEXT,
            'Cidade' TEXT,
            'Dia_Retirada' TEXT,
            'Status_Retirada' TEXT,
            'SUPERVISOR' TEXT
        )
    """)
    conn.commit()
    conn.close()

def salvar_no_banco(df: pd.DataFrame):
    conn = sqlite3.connect("movimentacoes.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS movimentacoes")
    conn.commit()
    df.to_sql("movimentacoes", conn, if_exists="replace", index=False)
    conn.close()

def carregar_dados():
    conn = sqlite3.connect("movimentacoes.db")
    df = pd.read_sql("SELECT * FROM movimentacoes", conn, parse_dates=["Data/Hora Empenho"])
    conn.close()
    return df


# ========================
# Função de tratamento
# ========================
@st.cache_data
def carregar_funcionarios():
    """Carrega cadastro de funcionários do Excel (IDTEL -> MUNICIPIO + Dia Retirada)."""
    caminho = Path(__file__).parent / "Funcionarios.xlsx"
    if not caminho.exists():
        return pd.DataFrame(columns=["IDTEL", "MUNICIPIO_FUNCIONARIO"])
    df = pd.read_excel(caminho)
    df.columns = [c.strip() for c in df.columns]
    df["IDTEL"] = pd.to_numeric(df["IDTEL"], errors="coerce")
    df = df.drop_duplicates(subset="IDTEL", keep="first")
    cols = ["IDTEL", "MUNICIPIO_FUNCIONARIO"]
    if "Requisicoes_Dia" in df.columns:
        cols.append("Requisicoes_Dia")
    if "SUPERVISOR" in df.columns:
        cols.append("SUPERVISOR")
    return df[cols].copy()


def tratar_dados(df: pd.DataFrame):
    df.columns = [x.strip() for x in df.columns]
    df = df[['Data/Hora Empenho','Código Requisição', 'Id Volante','Volante',
             'Código do Produto','Descrição do Produto','Qtde Atendida',
             'Qtde Empenhada','Qtde Requisitada','Descrição Segmento Destino',
             'Estoque Físico']]

    dias_da_semana = {0: 'Segunda-feira',1: 'Terça-feira',2: 'Quarta-feira',
                      3: 'Quinta-feira',4: 'Sexta-feira',5: 'Sábado',6: 'Domingo'}
    df['dia_semana'] = df['Data/Hora Empenho'].apply(
        lambda x: dias_da_semana[x.dayofweek] if pd.notnull(x) else None
    )

    df['Estoque Físico'] = df['Estoque Físico'].str.replace(' - ',' ').str[4:].str.strip()

    mapa_estoque = {
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
        'OSX/PEE IMPLANTAÇÃO RPO CLIENTE':'IMPLANTACAO'
    }
    df['Estoque'] = df['Estoque Físico'].apply(lambda x: mapa_estoque.get(x, x))

    df['Status'] = df.groupby('Código Requisição')['Qtde Atendida'] \
                     .transform(lambda x: "Separado" if (x > 0).any() else "A Separar")

    def manter_nao_proprio(gr):
        nao_proprio = gr[gr['Estoque'] != 'PROPRIO']
        if not nao_proprio.empty:
            return nao_proprio.iloc[0]
        return gr.iloc[0]

    df = df.groupby('Código Requisição', group_keys=False).apply(manter_nao_proprio)
    df.drop(columns=['Descrição Segmento Destino', 'Estoque Físico'], errors='ignore', inplace=True)

    # ── Cruzamento com Funcionarios para obter Cidade e Dia de Retirada ──
    df_func = carregar_funcionarios()
    if not df_func.empty:
        df["Id Volante"] = pd.to_numeric(df["Id Volante"], errors="coerce")
        df = df.merge(
            df_func,
            left_on="Id Volante",
            right_on="IDTEL",
            how="left",
        )
        df.rename(columns={"MUNICIPIO_FUNCIONARIO": "Cidade"}, inplace=True)
        if "Requisicoes_Dia" in df.columns:
            df.rename(columns={"Requisicoes_Dia": "Dia_Retirada"}, inplace=True)
        else:
            df["Dia_Retirada"] = None
        if "SUPERVISOR" not in df.columns:
            df["SUPERVISOR"] = None
        df["SUPERVISOR"] = df["SUPERVISOR"].fillna("Não identificado")
        df.drop(columns=["IDTEL"], errors="ignore", inplace=True)
        df["Cidade"] = df["Cidade"].fillna("Outras Localidades")
    else:
        df["Cidade"] = "Outras Localidades"
        df["Dia_Retirada"] = None
        df["SUPERVISOR"] = "Não identificado"

    # ── Calcular Status de Retirada ──
    hoje = datetime.now()
    dia_hoje = hoje.strftime("%A")  # Nome em inglês
    mapa_en_pt = {
        "Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira",
        "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado", "Sunday": "Domingo"
    }
    dia_hoje_pt = mapa_en_pt.get(dia_hoje, dia_hoje)

    # Mapa para normalizar maiúsculas do Excel para o padrão do sistema
    mapa_normalizar = {
        "SEGUNDA-FEIRA": "Segunda-feira", "TERÇA-FEIRA": "Terça-feira",
        "QUARTA-FEIRA": "Quarta-feira", "QUINTA-FEIRA": "Quinta-feira",
        "SEXTA-FEIRA": "Sexta-feira", "SÁBADO": "Sábado", "DOMINGO": "Domingo",
        "TERCA-FEIRA": "Terça-feira", "SABADO": "Sábado",
    }

    # Ordem dos dias para calcular atraso
    ordem_dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

    def calcular_status_retirada(row):
        dia_ret = row.get("Dia_Retirada")
        status = row.get("Status")
        if pd.isna(dia_ret) or dia_ret is None or str(dia_ret).strip() == "":
            return "Sem dia definido"
        # Normalizar: converter MAIÚSCULAS para padrão título
        dia_ret_norm = str(dia_ret).strip().upper()
        dia_ret = mapa_normalizar.get(dia_ret_norm, str(dia_ret).strip().title())

        if status != "Separado":
            return "⏳ Aguardando separação"
        if dia_ret == dia_hoje_pt:
            return "📅 Retirar Hoje"
        # Verificar se o dia de retirada já passou na semana
        idx_hoje = ordem_dias.index(dia_hoje_pt) if dia_hoje_pt in ordem_dias else -1
        idx_ret = ordem_dias.index(dia_ret) if dia_ret in ordem_dias else -1
        if idx_ret != -1 and idx_hoje != -1 and idx_ret < idx_hoje:
            return "🚨 Técnico Não Compareceu"
        return f"🗓️ Aguardar ({dia_ret})"

    if "Dia_Retirada" in df.columns:
        df["Status_Retirada"] = df.apply(calcular_status_retirada, axis=1)
    else:
        df["Status_Retirada"] = "Sem dia definido"

    return df


# ========================
# Componentes de UI
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
    st.markdown(f"""
        <div class="header-container">
            <h1>📦 Painel de Controle — Requisições</h1>
            <p>Monitoramento em tempo real de separação e atendimento de requisições &nbsp;|&nbsp; Atualizado em {now}</p>
        </div>
    """, unsafe_allow_html=True)


def render_secao(titulo):
    st.markdown(f'<div class="secao-titulo">{titulo}</div>', unsafe_allow_html=True)


def layout_plotly(fig, altura=420, mostrar_titulo_layout=True):
    """Aplica layout profissional padronizado aos gráficos Plotly."""
    layout_opts = dict(
        template=PLOTLY_TEMPLATE,
        height=altura,
        margin=dict(l=40, r=30, t=60, b=40),
        font=dict(family="Segoe UI, sans-serif", size=12, color="#333"),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5,
            font=dict(size=11),
            bgcolor="rgba(255,255,255,0.7)",
            bordercolor="rgba(0,0,0,0.08)",
            borderwidth=1,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor="white", font_size=12, font_family="Segoe UI, sans-serif",
            bordercolor="#ddd"
        ),
    )
    if mostrar_titulo_layout:
        layout_opts["title_font"] = dict(size=15, color=CORES["primaria"], family="Segoe UI, sans-serif")
    fig.update_layout(**layout_opts)
    fig.update_xaxes(showgrid=False, tickfont=dict(size=10))
    fig.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)", tickfont=dict(size=10))
    return fig


@st.cache_data
def converter_excel(df):
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Movimentacoes")
    return output.getvalue()


# ========================
# CONFIGURAÇÃO DA PÁGINA
# ========================
st.set_page_config(
    page_title="Painel de Requisições",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)
aplicar_css()
init_db()

# ========================
# SIDEBAR
# ========================
with st.sidebar:
    st.markdown("""
        <div style="text-align:center; padding: 10px 0 5px 0;">
            <span style="font-size: 2.2rem;">📦</span>
            <h2 style="margin: 5px 0 0 0; font-size: 1.3rem;">Painel de Controle</h2>
            <p style="font-size: 0.75rem; opacity: 0.6; margin-top: 2px;">Filtros &amp; Configurações</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### 📂 Importação de Dados")
    arquivo = st.file_uploader("Upload do arquivo Excel", type=["xlsx"], label_visibility="collapsed")

    if arquivo:
        df_raw = pd.read_excel(arquivo)
        df_tratado = tratar_dados(df_raw)

        if st.button("💾 Salvar no Banco de Dados", use_container_width=True):
            salvar_no_banco(df_tratado)
            st.success("✅ Dados salvos com sucesso!")
            st.rerun()

        excel_bytes = converter_excel(df_tratado)
        st.download_button(
            label="📥 Baixar Excel Tratado",
            data=excel_bytes,
            file_name="movimentacoes_tratadas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.markdown("---")

    # Filtros (só aparecem se houver dados)
    try:
        df_db = carregar_dados()
    except Exception:
        df_db = pd.DataFrame()

    filtro_estoques = []
    filtro_status = []
    filtro_volantes = []
    filtro_dia = []
    filtro_cidades = []

    if not df_db.empty:
        st.markdown("### 🔍 Filtros")

        # Filtro de Cidade
        if "Cidade" in df_db.columns:
            cidades_disp = sorted(df_db["Cidade"].dropna().unique().tolist())
            filtro_cidades = st.multiselect("🏙️ Cidade", cidades_disp, default=cidades_disp)

        estoques_disp = sorted(df_db["Estoque"].dropna().unique().tolist())
        filtro_estoques = st.multiselect("Estoque", estoques_disp, default=estoques_disp)

        status_disp = sorted(df_db["Status"].dropna().unique().tolist())
        filtro_status = st.multiselect("Status", status_disp, default=status_disp)

        volantes_disp = sorted(df_db["Volante"].dropna().unique().tolist())
        filtro_volantes = st.multiselect("Volante", volantes_disp, default=volantes_disp)

        dias_disp = ['Segunda-feira','Terça-feira','Quarta-feira','Quinta-feira','Sexta-feira','Sábado','Domingo']
        dias_existentes = [d for d in dias_disp if d in df_db["dia_semana"].dropna().unique()]
        filtro_dia = st.multiselect("Dia da Semana", dias_existentes, default=dias_existentes)

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; opacity:0.5; font-size:0.75rem; color:#ccc;'>"
        "Desenvolvido Felipe G Canato<br>© 2026</div>",
        unsafe_allow_html=True,
    )


# ========================
# CONTEÚDO PRINCIPAL
# ========================
render_header()

if df_db.empty:
    st.info("📂 Nenhum dado disponível no banco ainda. Utilize a **sidebar** para fazer upload de um arquivo Excel.")
    st.stop()

# Aplicar filtros
df_filtrado = df_db.copy()
if filtro_cidades and "Cidade" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Cidade"].isin(filtro_cidades)]
if filtro_estoques:
    df_filtrado = df_filtrado[df_filtrado["Estoque"].isin(filtro_estoques)]
if filtro_status:
    df_filtrado = df_filtrado[df_filtrado["Status"].isin(filtro_status)]
if filtro_volantes:
    df_filtrado = df_filtrado[df_filtrado["Volante"].isin(filtro_volantes)]
if filtro_dia:
    df_filtrado = df_filtrado[df_filtrado["dia_semana"].isin(filtro_dia)]

if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

# ========================
# KPIs
# ========================
total_req = df_filtrado["Código Requisição"].nunique()
total_separado = df_filtrado[df_filtrado["Status"] == "Separado"]["Código Requisição"].nunique()
total_a_separar = df_filtrado[df_filtrado["Status"] == "A Separar"]["Código Requisição"].nunique()
perc_separado = (total_separado / total_req * 100) if total_req > 0 else 0
total_estoques = df_filtrado["Estoque"].nunique()
total_volantes = df_filtrado["Volante"].nunique()
total_cidades = df_filtrado["Cidade"].nunique() if "Cidade" in df_filtrado.columns else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    render_kpi("Total Requisições", f"{total_req:,}".replace(",", "."), CORES["primaria"], "📋", "Requisições únicas")
with k2:
    render_kpi("Separadas", f"{total_separado:,}".replace(",", "."), CORES["separado"], "✅", "Já atendidas")
with k3:
    render_kpi("A Separar", f"{total_a_separar:,}".replace(",", "."), CORES["a_separar"], "⏳", "Pendentes")
with k4:
    render_kpi("% Separado", f"{perc_separado:.1f}%", CORES["secundaria"], "📊", "Taxa de conclusão")
with k5:
    render_kpi("Cidades", f"{total_cidades}", CORES["info"], "�️", "Municípios ativos")
with k6:
    render_kpi("Volantes", f"{total_volantes}", CORES["alerta"], "👷", "Profissionais")

st.markdown("---")

# ========================
# ABAS PRINCIPAIS
# ========================
tab_visao, tab_estoques, tab_cidades, tab_volantes, tab_dados = st.tabs([
    "📊 Visão Geral", "🏭 Análise por Estoque", "🏙️ Análise por Cidade", "👷 Análise por Volante", "📋 Dados"
])

# ─────────────────────────────────────
# ABA 1 — Visão Geral
# ─────────────────────────────────────
with tab_visao:
    col_a, col_b = st.columns(2)

    # Gráfico Gauge — Taxa de separação
    with col_a:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=perc_separado,
            number={"suffix": "%", "font": {"size": 42, "color": CORES["primaria"]}},
            delta={"reference": 100, "increasing": {"color": CORES["separado"]}, "suffix": "%"},
            title={"text": "Taxa de Separação", "font": {"size": 16, "color": CORES["primaria"]}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": CORES["secundaria"], "thickness": 0.3},
                "steps": [
                    {"range": [0, 40], "color": "#FDEDEC"},
                    {"range": [40, 70], "color": "#FEF9E7"},
                    {"range": [70, 100], "color": "#EAFAF1"},
                ],
                "threshold": {
                    "line": {"color": CORES["a_separar"], "width": 3},
                    "thickness": 0.8,
                    "value": perc_separado,
                },
            },
        ))
        fig_gauge = layout_plotly(fig_gauge, altura=350, mostrar_titulo_layout=False)
        st.plotly_chart(fig_gauge, use_container_width=True)

    # Donut — Separado vs A Separar
    with col_b:
        fig_donut = go.Figure(go.Pie(
            labels=["Separado", "A Separar"],
            values=[total_separado, total_a_separar],
            hole=0.55,
            marker=dict(colors=[CORES["separado"], CORES["a_separar"]], line=dict(color="white", width=3)),
            textinfo="label+percent",
            textfont=dict(size=13),
            hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>",
        ))
        fig_donut.update_layout(
            title=dict(text="Distribuição Geral", font=dict(size=15, color=CORES["primaria"])),
            annotations=[dict(text=f"{total_req}", x=0.5, y=0.5, font_size=28, font_color=CORES["primaria"], showarrow=False)],
        )
        fig_donut = layout_plotly(fig_donut, altura=350, mostrar_titulo_layout=False)
        st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown("---")

    # Barras agrupadas — por Estoque
    agrupado = df_filtrado.groupby(["Estoque", "Status"]).size().reset_index(name="Quantidade")

    fig_bar = px.bar(
        agrupado, x="Estoque", y="Quantidade", color="Status",
        barmode="group",
        title="Comparativo Separado vs A Separar por Estoque",
        color_discrete_map={"Separado": CORES["separado"], "A Separar": CORES["a_separar"]},
        text="Quantidade",
    )
    fig_bar.update_traces(textposition="outside", textfont_size=10)
    fig_bar = layout_plotly(fig_bar, altura=440)
    st.plotly_chart(fig_bar, use_container_width=True)

    # Distribuição por dia da semana
    if "dia_semana" in df_filtrado.columns:
        ordem_dias = ['Segunda-feira','Terça-feira','Quarta-feira','Quinta-feira','Sexta-feira','Sábado','Domingo']
        df_dia = df_filtrado.groupby(["dia_semana", "Status"]).size().reset_index(name="Quantidade")
        df_dia["dia_semana"] = pd.Categorical(df_dia["dia_semana"], categories=ordem_dias, ordered=True)
        df_dia = df_dia.sort_values("dia_semana")

        fig_dia = px.bar(
            df_dia, x="dia_semana", y="Quantidade", color="Status",
            barmode="stack",
            title="Distribuição por Dia da Semana",
            color_discrete_map={"Separado": CORES["separado"], "A Separar": CORES["a_separar"]},
            labels={"dia_semana": "Dia da Semana"},
        )
        fig_dia = layout_plotly(fig_dia, altura=380)
        st.plotly_chart(fig_dia, use_container_width=True)


# ─────────────────────────────────────
# ABA 2 — Análise por Estoque
# ─────────────────────────────────────
with tab_estoques:
    render_secao("🏭 Performance por Estoque")

    # Tabela resumo por estoque
    resumo_est = df_filtrado.groupby("Estoque").agg(
        Total=("Código Requisição", "nunique"),
        Separado=("Status", lambda x: (x == "Separado").sum()),
        A_Separar=("Status", lambda x: (x == "A Separar").sum()),
    ).reset_index()
    resumo_est["% Separado"] = (resumo_est["Separado"] / resumo_est["Total"] * 100).round(1)
    resumo_est = resumo_est.sort_values("Total", ascending=False)

    # Heatmap-style horizontal bar
    fig_h = go.Figure()
    fig_h.add_trace(go.Bar(
        y=resumo_est["Estoque"], x=resumo_est["Separado"],
        name="Separado", orientation="h",
        marker_color=CORES["separado"], text=resumo_est["Separado"], textposition="inside",
    ))
    fig_h.add_trace(go.Bar(
        y=resumo_est["Estoque"], x=resumo_est["A_Separar"],
        name="A Separar", orientation="h",
        marker_color=CORES["a_separar"], text=resumo_est["A_Separar"], textposition="inside",
    ))
    fig_h.update_layout(barmode="stack", title="Requisições por Estoque")
    fig_h = layout_plotly(fig_h, altura=max(350, len(resumo_est) * 32))
    fig_h.update_yaxes(showgrid=False)
    st.plotly_chart(fig_h, use_container_width=True)

    # Treemap
    fig_tree = px.treemap(
        agrupado, path=["Estoque", "Status"], values="Quantidade",
        title="Estoques e Status",
        color="Quantidade",
        color_continuous_scale=["#eaf6f6", CORES["secundaria"], CORES["primaria"]],
    )
    fig_tree = layout_plotly(fig_tree, altura=480)
    fig_tree.update_traces(textinfo="label+value+percent root")
    st.plotly_chart(fig_tree, use_container_width=True)

    # Tabela detalhada
    render_secao("📋 Tabela Resumo por Estoque")
    st.dataframe(
        resumo_est.style
            .format({"% Separado": "{:.1f}%"})
            .background_gradient(cmap="RdYlGn", subset=["% Separado"])
            .set_properties(**{"text-align": "center"}),
        use_container_width=True,
        hide_index=True,
        height=min(400, 40 + len(resumo_est) * 35),
    )


# ─────────────────────────────────────
# ABA 3 — Análise por Cidade
# ─────────────────────────────────────
with tab_cidades:
    render_secao("🏙️ Requisições por Cidade (Município do Funcionário)")

    if "Cidade" in df_filtrado.columns:
        # Resumo por Cidade
        resumo_cid = df_filtrado.groupby("Cidade").agg(
            Total=("Código Requisição", "nunique"),
            Separado=("Status", lambda x: (x == "Separado").sum()),
            A_Separar=("Status", lambda x: (x == "A Separar").sum()),
            Volantes=("Volante", "nunique"),
            Estoques=("Estoque", "nunique"),
        ).reset_index()
        resumo_cid["% Separado"] = (resumo_cid["Separado"] / resumo_cid["Total"] * 100).round(1)
        resumo_cid = resumo_cid.sort_values("Total", ascending=False)

        # KPIs por cidade
        col_c1, col_c2, col_c3 = st.columns(3)
        for i, (_, row) in enumerate(resumo_cid.iterrows()):
            col = [col_c1, col_c2, col_c3][i % 3]
            with col:
                render_kpi(
                    row["Cidade"],
                    f"{row['Total']}",
                    CORES["gradiente"][i % len(CORES["gradiente"])],
                    "🏙️",
                    f"✅ {row['Separado']} sep. | ⏳ {row['A_Separar']} pend. | {row['% Separado']:.0f}%"
                )

        st.markdown("---")

        col_g1, col_g2 = st.columns(2)

        # Barras agrupadas por Cidade
        with col_g1:
            agrup_cid = df_filtrado.groupby(["Cidade", "Status"]).size().reset_index(name="Quantidade")
            fig_cid_bar = px.bar(
                agrup_cid, x="Cidade", y="Quantidade", color="Status",
                barmode="group",
                title="Separado vs A Separar por Cidade",
                color_discrete_map={"Separado": CORES["separado"], "A Separar": CORES["a_separar"]},
                text="Quantidade",
            )
            fig_cid_bar.update_traces(textposition="outside", textfont_size=11)
            fig_cid_bar = layout_plotly(fig_cid_bar, altura=420)
            st.plotly_chart(fig_cid_bar, use_container_width=True)

        # Donut por Cidade
        with col_g2:
            fig_cid_pie = px.pie(
                resumo_cid, values="Total", names="Cidade",
                title="Distribuição de Requisições por Cidade",
                hole=0.5,
                color_discrete_sequence=CORES["gradiente"],
            )
            fig_cid_pie.update_traces(
                textinfo="label+percent+value",
                textfont_size=12,
                hovertemplate="<b>%{label}</b><br>Requisições: %{value}<br>Percentual: %{percent}<extra></extra>",
            )
            fig_cid_pie = layout_plotly(fig_cid_pie, altura=420, mostrar_titulo_layout=False)
            fig_cid_pie.update_layout(
                title=dict(text="Distribuição de Requisições por Cidade", font=dict(size=15, color=CORES["primaria"])),
            )
            st.plotly_chart(fig_cid_pie, use_container_width=True)

        # Cidade x Estoque (heatmap)
        st.markdown("---")
        cidade_estoque = df_filtrado.groupby(["Cidade", "Estoque"]).size().reset_index(name="Quantidade")
        pivot_ce = cidade_estoque.pivot(index="Cidade", columns="Estoque", values="Quantidade").fillna(0)

        fig_heatmap = px.imshow(
            pivot_ce,
            title="Mapa de Calor — Cidade x Estoque",
            labels=dict(x="Estoque", y="Cidade", color="Qtd Requisições"),
            color_continuous_scale=["#f0f4f8", CORES["secundaria"], CORES["primaria"]],
            text_auto=True,
            aspect="auto",
        )
        fig_heatmap = layout_plotly(fig_heatmap, altura=max(300, len(pivot_ce) * 80))
        st.plotly_chart(fig_heatmap, use_container_width=True)

        # Tabela resumo
        render_secao("📋 Tabela Resumo por Cidade")
        st.dataframe(
            resumo_cid.style
                .format({"% Separado": "{:.1f}%"})
                .background_gradient(cmap="RdYlGn", subset=["% Separado"])
                .set_properties(**{"text-align": "center"}),
            use_container_width=True,
            hide_index=True,
            height=min(400, 40 + len(resumo_cid) * 35),
        )
    else:
        st.warning("⚠️ Coluna 'Cidade' não disponível. Reimporte os dados para ativar o cruzamento com Funcionarios.xlsx.")


# ─────────────────────────────────────
# ABA 4 — Análise por Volante
# ─────────────────────────────────────
with tab_volantes:
    render_secao("👷 Performance por Volante")

    # ── Painel de Alertas de Retirada ──
    if "Status_Retirada" in df_filtrado.columns:
        df_nao_comp = df_filtrado[df_filtrado["Status_Retirada"] == "🚨 Técnico Não Compareceu"]
        df_hoje = df_filtrado[df_filtrado["Status_Retirada"] == "📅 Retirar Hoje"]
        df_aguard_sep = df_filtrado[df_filtrado["Status_Retirada"] == "⏳ Aguardando separação"]

        # KPIs de alerta
        col_al1, col_al2, col_al3 = st.columns(3)
        with col_al1:
            render_kpi(
                "Técnico Não Compareceu",
                f"{df_nao_comp['Volante'].nunique()}",
                CORES["a_separar"],
                "🚨",
                f"{len(df_nao_comp)} requisições separadas não retiradas no prazo"
            )
        with col_al2:
            render_kpi(
                "Retirar Hoje",
                f"{df_hoje['Volante'].nunique()}",
                CORES["alerta"],
                "📅",
                f"{len(df_hoje)} requisições aguardando retirada hoje"
            )
        with col_al3:
            render_kpi(
                "Aguardando Separação",
                f"{df_aguard_sep['Volante'].nunique()}",
                CORES["info"],
                "⏳",
                f"{len(df_aguard_sep)} requisições pendentes de separação"
            )

        st.markdown("---")

        # ── Gráfico de Status de Retirada — Donut + Barras ──
        col_g1, col_g2 = st.columns(2)

        cores_ret = {
            "🚨 Técnico Não Compareceu": CORES["a_separar"],
            "📅 Retirar Hoje": CORES["alerta"],
            "⏳ Aguardando separação": CORES["info"],
            "Sem dia definido": "#adb5bd",
        }
        # Adicionar cores para status "Aguardar (Dia)"
        df_ret_chart = df_filtrado.groupby("Status_Retirada").size().reset_index(name="Quantidade")
        for st_val in df_ret_chart["Status_Retirada"]:
            if st_val not in cores_ret:
                cores_ret[st_val] = CORES["separado"]

        with col_g1:
            fig_ret_pie = px.pie(
                df_ret_chart,
                values="Quantidade",
                names="Status_Retirada",
                title="Distribuição por Status de Retirada",
                hole=0.5,
                color="Status_Retirada",
                color_discrete_map=cores_ret,
            )
            fig_ret_pie.update_traces(
                textinfo="label+percent+value",
                textfont_size=11,
                hovertemplate="<b>%{label}</b><br>Qtd: %{value}<br>%{percent}<extra></extra>",
                pull=[0.08 if "Não Compareceu" in str(v) else 0 for v in df_ret_chart["Status_Retirada"]],
            )
            fig_ret_pie = layout_plotly(fig_ret_pie, altura=400, mostrar_titulo_layout=False)
            fig_ret_pie.update_layout(
                title=dict(text="Distribuição por Status de Retirada", font=dict(size=15, color=CORES["primaria"])),
            )
            st.plotly_chart(fig_ret_pie, use_container_width=True)

        with col_g2:
            df_ret_bar = df_ret_chart.sort_values("Quantidade", ascending=True)
            fig_ret_bar = px.bar(
                df_ret_bar,
                x="Quantidade",
                y="Status_Retirada",
                orientation="h",
                title="Quantidade por Status de Retirada",
                color="Status_Retirada",
                color_discrete_map=cores_ret,
                text="Quantidade",
            )
            fig_ret_bar.update_traces(textposition="outside", textfont_size=12)
            fig_ret_bar = layout_plotly(fig_ret_bar, altura=400)
            fig_ret_bar.update_yaxes(showgrid=False)
            fig_ret_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_ret_bar, use_container_width=True)

        # ── Tabela de técnicos que não compareceram ──
        if not df_nao_comp.empty:
            render_secao("🚨 Técnicos que NÃO Compareceram para Retirada")
            cols_exibir = ["Volante", "SUPERVISOR", "Código Requisição", "Dia_Retirada", "dia_semana", "Cidade", "Estoque", "Status_Retirada"]
            cols_exibir = [c for c in cols_exibir if c in df_nao_comp.columns]
            st.dataframe(
                df_nao_comp[cols_exibir].sort_values("Volante"),
                use_container_width=True,
                hide_index=True,
            )

        # ── Tabela de retirada hoje ──
        if not df_hoje.empty:
            render_secao("📅 Técnicos que Devem Retirar Hoje")
            cols_exibir = ["Volante", "SUPERVISOR", "Código Requisição", "Dia_Retirada", "Cidade", "Estoque", "Status_Retirada"]
            cols_exibir = [c for c in cols_exibir if c in df_hoje.columns]
            st.dataframe(
                df_hoje[cols_exibir].sort_values("Volante"),
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("---")

    resumo_vol = df_filtrado.groupby("Volante").agg(
        Total=("Código Requisição", "nunique"),
        Separado=("Status", lambda x: (x == "Separado").sum()),
        A_Separar=("Status", lambda x: (x == "A Separar").sum()),
    ).reset_index()
    resumo_vol["% Separado"] = (resumo_vol["Separado"] / resumo_vol["Total"] * 100).round(1)
    resumo_vol = resumo_vol.sort_values("Total", ascending=False)

    # Top 15 volantes
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

    # Tabela
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
# ABA 4 — Dados
# ─────────────────────────────────────
with tab_dados:
    render_secao("📋 Dados Completos (Filtrados)")

    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("Linhas", f"{len(df_filtrado):,}".replace(",", "."))
    with col_info2:
        st.metric("Colunas", f"{len(df_filtrado.columns)}")
    with col_info3:
        st.metric("Requisições únicas", f"{df_filtrado['Código Requisição'].nunique():,}".replace(",", "."))

    # Busca na tabela
    busca = st.text_input("🔎 Buscar na tabela (código, produto, volante...)", "")
    df_exibir = df_filtrado.copy()
    if busca:
        mask = df_exibir.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_exibir = df_exibir[mask]

    st.dataframe(
        df_exibir,
        use_container_width=True,
        hide_index=True,
        height=600,
    )

    # Download dos dados filtrados
    excel_filtrado = converter_excel(df_exibir)
    st.download_button(
        label="📥 Baixar Dados Filtrados (.xlsx)",
        data=excel_filtrado,
        file_name="requisicoes_filtradas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )



