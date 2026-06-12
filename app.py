import streamlit as st
import streamlit_authenticator as stauth
from database.connection import get_connection

st.set_page_config(
    page_title="FinancePME",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── AUTENTICAÇÃO ─────────────────────────────────────────
config = {
    "credentials": {
        "usernames": {
            "rodrigo": {
                "email":    "seu@email.com",
                "name":     "Rodrigo",
                "password": "$2b$12$Jp2bDY61EgjpyzyN720hQObQrrcf0RDX2Xb6N0uXDnz.bsP7lXCg2",
            }
        }
    },
    "cookie": {
        "expiry_days": 7,
        "key":  "financepme_cookie_secret_2024",
        "name": "financepme_auth",
    }
}

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

authenticator.login()

if st.session_state.get("authentication_status") is False:
    st.error("❌ Usuário ou senha incorretos.")
    st.stop()

elif st.session_state.get("authentication_status") is None:
    st.info("👆 Digite suas credenciais para acessar o FinancePME.")
    st.stop()

# ── A PARTIR DAQUI SÓ EXECUTA SE AUTENTICADO ─────────────

# ── CSS GLOBAL ───────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #1e293b !important;
    }   
    [data-testid="stSidebar"] * {
        color: #f5f5f5 !important;
        font-family: 'Segoe UI', sans-serif !important;
    }
    [data-testid="stSidebarHeader"] {
        background-color: #0f172a !important;
        padding: 1.5rem 1.2rem 1rem 1.2rem !important;
        border-bottom: 1px solid #1e293b !important;
    }
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
    [data-testid="stSidebarNav"] a:hover {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: #ffffff !important;
    }
    [data-testid="stSidebarContent"] {
        background-color: #0f172a !important;
        padding-top: 0.5rem !important;
    }
    [data-testid="stSidebar"]::-webkit-scrollbar { width: 4px; }
    [data-testid="stSidebar"]::-webkit-scrollbar-track { background: #0f172a; }
    [data-testid="stSidebar"]::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
    [data-testid="stSidebarCollapseButton"] { color: #475569 !important; }
    [data-testid="stMain"] { background-color: #f8fafc !important; }
</style>
""", unsafe_allow_html=True)

# ── BOTÃO DE LOGOUT NA SIDEBAR ───────────────────────────
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.get('name', '')}**")
    st.markdown("---")
    authenticator.logout("🚪 Sair", "sidebar")

# ── NAVEGAÇÃO ────────────────────────────────────────────
dashboard       = st.Page("views/dashboard.py",       title="Dashboard",        icon="📊")
cadastros       = st.Page("views/cadastros.py",       title="Cadastros",        icon="🗂️")
contas_pagar    = st.Page("views/contas_pagar.py",    title="Contas a Pagar",   icon="📉")
contas_receber  = st.Page("views/contas_receber.py",  title="Contas a Receber", icon="📈")
fluxo_caixa     = st.Page("views/fluxo_caixa.py",    title="Fluxo de Caixa",   icon="🧮")
transferencias  = st.Page("views/transferencias.py",  title="Transferências",   icon="💸")  # ← NOVO

pg = st.navigation({
    "Visão Geral":   [dashboard],
    "Cadastros":     [cadastros],
    "Movimentações": [contas_pagar, contas_receber, fluxo_caixa, transferencias],  # ← INCLUÍDO AQUI
})

pg.run()