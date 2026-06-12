import streamlit as st
import pandas as pd
from database.connection import execute_query
from datetime import date
import calendar

# ── ESTADO DO FILTRO DE STATUS ────────────────────────────
if "status_filtro_fluxo" not in st.session_state:
    st.session_state.status_filtro_fluxo = "Todos"

# ── CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 3rem !important; padding-bottom: 1rem !important; }
    h1 { margin-top: 0rem !important; padding-top: 0rem !important;
         margin-bottom: 0.8rem !important; font-size: 28px !important;
         font-weight: 700 !important; color: #1e293b; line-height: 1.3 !important; }
</style>
""", unsafe_allow_html=True)

# ── FUNÇÕES ───────────────────────────────────────────────
def fmt(valor):
    try:
        v = float(valor)
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "R$ 0,00"

def listar_contas_bancarias():
    return execute_query(
        "SELECT id, nome, banco, saldo_inicial FROM contas_bancarias WHERE ativo = true ORDER BY nome",
        fetch=True
    )

def contas_do_mes(ano, mes, conta_bancaria_id):
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia   = date(ano, mes, calendar.monthrange(ano, mes)[1])

    receber = execute_query("""
        SELECT
            cr.vencimento   AS data,
            cr.descricao,
            'receber'       AS tipo,
            cr.valor,
            cr.status,
            cr.forma_pagamento,
            cat.descricao   AS categoria,
            cl.nome         AS cadastro
        FROM contas_receber cr
        LEFT JOIN categorias       cat ON cr.categoria_id      = cat.id
        LEFT JOIN clientes          cl ON cr.cliente_id        = cl.id
        WHERE cr.vencimento BETWEEN %s AND %s
          AND cr.conta_bancaria_id = %s
    """, (primeiro_dia, ultimo_dia, conta_bancaria_id), fetch=True)

    pagar = execute_query("""
        SELECT
            cp.vencimento   AS data,
            cp.descricao,
            'pagar'         AS tipo,
            cp.valor,
            cp.status,
            cp.forma_pagamento,
            cat.descricao   AS categoria,
            b.nome          AS cadastro
        FROM contas_pagar cp
        LEFT JOIN categorias       cat ON cp.categoria_id      = cat.id
        LEFT JOIN beneficiarios     b  ON cp.beneficiario_id   = b.id
        WHERE cp.vencimento BETWEEN %s AND %s
          AND cp.conta_bancaria_id = %s
    """, (primeiro_dia, ultimo_dia, conta_bancaria_id), fetch=True)

    todos = (receber or []) + (pagar or [])
    return sorted(todos, key=lambda x: (x["data"], x["tipo"]))

MESES = {
    1:"Janeiro", 2:"Fevereiro", 3:"Março",    4:"Abril",
    5:"Maio",    6:"Junho",     7:"Julho",     8:"Agosto",
    9:"Setembro",10:"Outubro",  11:"Novembro", 12:"Dezembro"
}

# ── TÍTULO ────────────────────────────────────────────────
st.markdown("<h1>📊 Fluxo de Caixa</h1>", unsafe_allow_html=True)

# ── SELETOR DE CONTA BANCÁRIA ─────────────────────────────
contas_bancarias = listar_contas_bancarias()

if not contas_bancarias:
    st.warning("Nenhuma conta bancária ativa cadastrada. Cadastre uma conta em **Contas Bancárias** primeiro.")
    st.stop()

opc_cb      = {f"{c['nome']} — {c['banco']}": c for c in contas_bancarias}
cb_escolha  = st.selectbox("🏛️ Conta Bancária", list(opc_cb.keys()))
cb_selecion = opc_cb[cb_escolha]
saldo_ini   = float(cb_selecion["saldo_inicial"] or 0)

st.markdown("---")

# ── SELETOR DE PERÍODO E FILTROS ──────────────────────────
col_mes, col_ano, col_f_todos, col_f_pend, col_f_pago = st.columns(
    [2, 1.2, 1.2, 1.2, 1.2], vertical_alignment="bottom"
)

with col_mes:
    mes_sel = st.selectbox("Mês", list(MESES.keys()),
                index=date.today().month - 1,
                format_func=lambda x: MESES[x])
with col_ano:
    ano_sel = st.number_input("Ano", min_value=2020, max_value=2030, value=date.today().year)

# ── MOVIMENTOS DO MÊS PARA A CONTA SELECIONADA ───────────
movimentos = contas_do_mes(ano_sel, mes_sel, cb_selecion["id"])

# ── CÁLCULOS ──────────────────────────────────────────────
if movimentos:
    df_calc = pd.DataFrame(movimentos)
    entradas             = float(df_calc[df_calc["tipo"] == "receber"]["valor"].sum())
    saidas               = float(df_calc[df_calc["tipo"] == "pagar"]["valor"].sum())
    saldo_final_previsto = saldo_ini + entradas - saidas
    entradas_pagas       = float(df_calc[(df_calc["tipo"] == "receber") & (df_calc["status"] == "pago")]["valor"].sum())
    saidas_pagas         = float(df_calc[(df_calc["tipo"] == "pagar")   & (df_calc["status"] == "pago")]["valor"].sum())
    saldo_atual          = saldo_ini + entradas_pagas - saidas_pagas
else:
    entradas = saidas = 0.0
    saldo_final_previsto = saldo_atual = saldo_ini

# ── BOTÕES DE FILTRO ──────────────────────────────────────
with col_f_todos:
    if st.button("Todos", type="primary" if st.session_state.status_filtro_fluxo == "Todos" else "secondary",
                 use_container_width=True, key="fluxo_f_todos"):
        st.session_state.status_filtro_fluxo = "Todos"; st.rerun()
with col_f_pend:
    if st.button("Pendentes", type="primary" if st.session_state.status_filtro_fluxo == "Pendente" else "secondary",
                 use_container_width=True, key="fluxo_f_pend"):
        st.session_state.status_filtro_fluxo = "Pendente"; st.rerun()
with col_f_pago:
    if st.button("Pagos", type="primary" if st.session_state.status_filtro_fluxo == "Pago" else "secondary",
                 use_container_width=True, key="fluxo_f_pago"):
        st.session_state.status_filtro_fluxo = "Pago"; st.rerun()

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

# ── MÉTRICAS ──────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)

def card(bg, border, label_color, label, valor):
    return (f'<div style="background-color:{bg};padding:8px 12px;border-radius:5px;border-left:3px solid {border};">'
            f'<span style="font-size:10px;font-weight:600;color:{label_color};text-transform:uppercase;">{label}</span>'
            f'<h4 style="margin:0;color:{label_color};font-weight:700;font-size:14px;">{valor}</h4></div>')

cor_final = "#16a34a" if saldo_final_previsto >= saldo_ini else "#dc2626"
bg_final  = "#f0fdf4" if saldo_final_previsto >= saldo_ini else "#fef2f2"

with m1: st.markdown(card("#f5f5f5","#64748b","#64748b","Saldo Inicial",       fmt(saldo_ini)),            unsafe_allow_html=True)
with m2: st.markdown(card("#f0fdf4","#16a34a","#16a34a","Entradas Previstas",  fmt(entradas)),             unsafe_allow_html=True)
with m3: st.markdown(card("#fef2f2","#dc2626","#dc2626","Saídas Previstas",    fmt(saidas)),               unsafe_allow_html=True)
with m4: st.markdown(card("#eff6ff","#2563eb","#2563eb","Saldo Real Atual",    fmt(saldo_atual)),          unsafe_allow_html=True)
with m5: st.markdown(card(bg_final, cor_final, cor_final,"Saldo Final Previsto",fmt(saldo_final_previsto)),unsafe_allow_html=True)

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

# ── EXTRATO ───────────────────────────────────────────────
if movimentos:
    linhas = [{
        "Data":       f"01/{mes_sel:02d}/{ano_sel}",
        "Descrição":  f"🏦 Saldo Inicial — {cb_escolha}",
        "Tipo":       "—",
        "Entrada":    "",
        "Saída":      "",
        "Saldo":      fmt(saldo_ini),
        "Status":     "✅ Pago",
        "Categoria":  "—",
        "Forma Pgto": "—",
    }]

    saldo_corrente = saldo_ini
    for row in sorted(movimentos, key=lambda x: x["data"]):
        is_entrada = row["tipo"] == "receber"
        valor      = float(row["valor"])
        saldo_corrente += valor if is_entrada else -valor
        nome_exibicao = row["cadastro"] if row["cadastro"] else (row["descricao"] or "—")

        linhas.append({
            "Data":       pd.to_datetime(str(row["data"])).strftime("%d/%m/%Y"),
            "Descrição":  nome_exibicao,
            "Tipo":       "💰 Receber" if is_entrada else "💸 Pagar",
            "Entrada":    fmt(valor) if is_entrada else "",
            "Saída":      "" if is_entrada else fmt(valor),
            "Saldo":      fmt(saldo_corrente),
            "Status":     "✅ Pago" if row["status"] == "pago" else "⏳ Pendente",
            "Categoria":  row["categoria"] or "—",
            "Forma Pgto": row["forma_pagamento"] or "—",
        })

    df_view = pd.DataFrame(linhas)

    if st.session_state.status_filtro_fluxo == "Pendente":
        df_view = df_view[(df_view.index == 0) | (df_view["Status"] == "⏳ Pendente")]
    elif st.session_state.status_filtro_fluxo == "Pago":
        df_view = df_view[df_view["Status"] == "✅ Pago"]

    if not df_view.empty:
        def colorir(row):
            if row["Descrição"].startswith("🏦 Saldo"):
                return [""] * len(row)
            if row["Status"] == "⏳ Pendente":
                return ["background-color:#fffbeb;color:#b45309;"] * len(row)
            elif row["Tipo"] == "💰 Receber":
                return ["background-color:#f0fdf4;color:#15803d;"] * len(row)
            elif row["Tipo"] == "💸 Pagar":
                return ["background-color:#fef2f2;color:#b91c1c;"] * len(row)
            return [""] * len(row)

        st.dataframe(df_view.style.apply(colorir, axis=1), use_container_width=True, hide_index=True)
        st.caption(f"Exibindo {len(df_view)} registro(s) — {cb_escolha} — {MESES[mes_sel]}/{ano_sel}")

        st.markdown("---")
        csv = df_view.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Exportar Extrato Mensal (CSV)",
            csv,
            f"fluxo_{cb_escolha}_{MESES[mes_sel]}_{ano_sel}.csv",
            "text/csv",
            use_container_width=True
        )
    else:
        st.info(f"Nenhum registro para o filtro '{st.session_state.status_filtro_fluxo}'.")
else:
    st.info(f"Nenhum lançamento encontrado para {cb_escolha} em {MESES[mes_sel]}/{ano_sel}.")