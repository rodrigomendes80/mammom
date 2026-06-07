import streamlit as st
import pandas as pd
from database.connection import execute_query
from datetime import date
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go

# ── FUNÇÕES AUXILIARES ───────────────────────────────────
def get_valor_unico(query, params=()):
    resultado = execute_query(query, params, fetch=True)
    if resultado and len(resultado) > 0:
        item = resultado[0]
        if isinstance(item, dict):
            return list(item.values())[0]
        return item[0]
    return 0

def fmt_brl(valor):
    return f"R$ {float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ── TÍTULO ───────────────────────────────────────────────
st.markdown("<h1>Dashboard</h1>", unsafe_allow_html=True)

# ── BUSCA DE DADOS ───────────────────────────────────────
total_pagar   = get_valor_unico("SELECT COALESCE(SUM(valor),0) FROM contas_pagar WHERE status = 'pendente'")
total_receber = get_valor_unico("SELECT COALESCE(SUM(valor),0) FROM contas_receber WHERE status = 'pendente'")
qtd_vencidas  = get_valor_unico("SELECT COUNT(*) FROM contas_pagar WHERE status = 'pendente' AND vencimento < %s", (date.today(),))

# ── SALDO REAL ATUAL (mesma lógica do Fluxo de Caixa) ───
saldo_inicial_bancos  = get_valor_unico("SELECT COALESCE(SUM(saldo_inicial),0) FROM contas_bancarias WHERE ativo=true")
entradas_pagas        = get_valor_unico("SELECT COALESCE(SUM(valor),0) FROM contas_receber WHERE status = 'pago'")
saidas_pagas          = get_valor_unico("SELECT COALESCE(SUM(valor),0) FROM contas_pagar WHERE status = 'pago'")
saldo_atual           = float(saldo_inicial_bancos) + float(entradas_pagas) - float(saidas_pagas)

# ── CARDS ────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
cards = [
    ("A Pagar (em aberto)",   total_pagar,   "#dc2626", "#fef2f2"),
    ("A Receber (em aberto)", total_receber, "#16a34a", "#f0fdf4"),
    ("Saldo Atual em Bancos", saldo_atual,   "#2563eb", "#eff6ff"),  # ← corrigido
    ("Contas Vencidas",       int(qtd_vencidas),
     "#b45309" if qtd_vencidas > 0 else "#64748b",
     "#fffbeb"  if qtd_vencidas > 0 else "#f8fafc")
]

for i, col in enumerate([c1, c2, c3, c4]):
    title, val, border, bg = cards[i]
    with col:
        st.markdown(f'''
        <div style="background-color: {bg}; padding: 14px; border-radius: 10px; border-left: 4px solid {border};">
            <span style="font-size: 11px; color: #94a3b8;">{title}</span>
            <h3 style="margin:0; color: {border};">{fmt_brl(val) if title != "Contas Vencidas" else val}</h3>
        </div>''', unsafe_allow_html=True)

# ── GRÁFICO — Últimos 6 meses ────────────────────────────
st.markdown("<br><b>Entradas × Saídas — últimos 6 meses</b>", unsafe_allow_html=True)
inicio_janela = (date.today() - relativedelta(months=5)).replace(day=1)

dados_r = execute_query("SELECT vencimento, valor FROM contas_receber WHERE vencimento >= %s", (inicio_janela,), fetch=True) or []
dados_p = execute_query("SELECT vencimento, valor FROM contas_pagar WHERE vencimento >= %s",   (inicio_janela,), fetch=True) or []

def agrupar_por_mes(dados):
    res = {}
    for row in dados:
        dt  = pd.to_datetime(row['vencimento'] if isinstance(row, dict) else row[0])
        val = float(row['valor']      if isinstance(row, dict) else row[1])
        res[(dt.year, dt.month)] = res.get((dt.year, dt.month), 0) + val
    return res

map_r, map_p = agrupar_por_mes(dados_r), agrupar_por_mes(dados_p)
meses    = [(inicio_janela + relativedelta(months=i)) for i in range(6)]
labels   = [m.strftime('%b') for m in meses]
entradas = [map_r.get((m.year, m.month), 0) for m in meses]
saidas   = [map_p.get((m.year, m.month), 0) for m in meses]

fig = go.Figure()
fig.add_trace(go.Bar(name="Entradas", x=labels, y=entradas, marker_color="#16a34a"))
fig.add_trace(go.Bar(name="Saídas",   x=labels, y=saidas,   marker_color="#dc2626"))
fig.update_layout(height=300, barmode="group", plot_bgcolor="#ffffff", margin=dict(t=20, b=20))
st.plotly_chart(fig, use_container_width=True)