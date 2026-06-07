import streamlit as st
from database.connection import get_connection

st.set_page_config(
    page_title="FinancePME",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS GLOBAL: SIDEBAR ESCURA ESTILO DASHBOARD ───────────
st.markdown("""
<style>
    /* ── Fundo da sidebar ── */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #1e293b !important;
    }   

    /* ── Todos os textos da sidebar ── */
    [data-testid="stSidebar"] * {
        color: #f5f5f5 !important;
        font-family: 'Segoe UI', sans-serif !important;
    }

    /* ── Logo / título do app ── */
    [data-testid="stSidebarHeader"] {
        background-color: #0f172a !important;
        padding: 1.5rem 1.2rem 1rem 1.2rem !important;
        border-bottom: 1px solid #1e293b !important;
    }

    /* ── Cabeçalhos de seção (Visão Geral, Cadastros...) ── */
    [data-testid="stSidebarNavSeparator"],
    [data-testid="stSidebar"] .st-emotion-cache-1cypcdb,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #57677D !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }

    /* ── Links de navegação (itens do menu) ── */
    [data-testid="stSidebarNav"] a {
        color: #94a3b8 !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        padding: 8px 14px !important;
        border-radius: 8px !important;
        margin: 2px 8px !important;
        text-decoration: none !important;
        display: flex !important;
        align-items: center !important;
        transition: background 0.15s ease, color 0.15s ease !important;
    }

    /* ── Hover nos itens ── */
    [data-testid="stSidebarNav"] a:hover {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
    }

    /* ── Item ativo (página atual) ── */
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* ── Ícones dos itens ativos ── */
    [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: #ffffff !important;
    }

    /* ── Remove fundo padrão branco que o Streamlit injeta ── */
    [data-testid="stSidebarContent"] {
        background-color: #0f172a !important;
        padding-top: 0.5rem !important;
    }

    /* ── Scrollbar da sidebar ── */
    [data-testid="stSidebar"]::-webkit-scrollbar {
        width: 4px;
    }
    [data-testid="stSidebar"]::-webkit-scrollbar-track {
        background: #0f172a;
    }
    [data-testid="stSidebar"]::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 4px;
    }

    /* ── Botão de colapsar a sidebar ── */
    [data-testid="stSidebarCollapseButton"] {
        color: #475569 !important;
    }

    /* ── Área principal: fundo levemente off-white ── */
    [data-testid="stMain"] {
        background-color: #f8fafc !important;
    }
</style>
""", unsafe_allow_html=True)

# Substitua as definições de páginas e o st.navigation por isso:

dashboard        = st.Page("views/dashboard.py",    title="Dashboard",     icon="📊")
cadastros        = st.Page("views/cadastros.py",    title="Cadastros",     icon="🗂️")
contas_pagar     = st.Page("views/contas_pagar.py", title="Contas a Pagar",   icon="📉")
contas_receber   = st.Page("views/contas_receber.py", title="Contas a Receber", icon="📈")
fluxo_caixa      = st.Page("views/fluxo_caixa.py", title="Fluxo de Caixa",    icon="🧮")

pg = st.navigation({
    "Visão Geral":   [dashboard],
    "Cadastros":     [cadastros],
    "Movimentações": [contas_pagar, contas_receber, fluxo_caixa],
})

pg.run()