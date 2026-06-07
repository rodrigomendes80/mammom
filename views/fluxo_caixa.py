import streamlit as st
import pandas as pd
from database.connection import execute_query
from datetime import date
import calendar

# ── CONFIGURAÇÃO DE ESTADO DO FILTRO ─────────────────────
if "status_filtro_fluxo" not in st.session_state:
    st.session_state.status_filtro_fluxo = "Todos"


# ── INJEÇÃO DE CSS: CORREÇÃO DEFINITIVA DO TOPO ──────────
st.markdown(

    """

    <style>

        .block-container {

            padding-top: 3rem !important;

            padding-bottom: 1rem !important;

        }

        h1 {

            margin-top: 0rem !important;

            padding-top: 0rem !important;

            margin-bottom: 0.8rem !important;

            font-size: 28px !important;

            font-weight: 700 !important;

            color: #1e293b;

            line-height: 1.3 !important;

        }

    </style>

    """,

    unsafe_allow_html=True

)



# ── FUNÇÕES DE SUPORTE ───────────────────────────────────

def fmt(valor):
    try:
        v = float(valor)
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "R$ 0,00"

def saldo_inicial_bancos():
    result = execute_query(
        "SELECT COALESCE(SUM(saldo_inicial),0) AS total FROM contas_bancarias WHERE ativo=true",
        fetch=True
    )
    return float(result[0]["total"]) if result else 0.0



def contas_do_mes(ano, mes):
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
    """, (primeiro_dia, ultimo_dia), fetch=True)

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
    """, (primeiro_dia, ultimo_dia), fetch=True)

    todos = (receber or []) + (pagar or [])
    return sorted(todos, key=lambda x: (x["data"], x["tipo"]), reverse=False)


MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}


# ── TÍTULO (LARGURA TOTAL E PROTEGIDO) ───────────────────
st.markdown("<h1>Fluxo de Caixa</h1>", unsafe_allow_html=True)

# ── BUSCA DOS DADOS BASE ─────────────────────────────────
saldo_ini = saldo_inicial_bancos()


# ── CONTROLES DO PERÍODO E BOTÕES DE FILTRO ──────────────
col_mes, col_ano, col_f_todos, col_f_pend, col_f_pago = st.columns([2, 1.2, 1.2, 1.2, 1.2], vertical_alignment="bottom")

with col_mes:
    mes_sel = st.selectbox("Mês", list(MESES.keys()), index=date.today().month - 1, format_func=lambda x: MESES[x])
with col_ano:
    ano_sel = st.number_input("Ano", min_value=2020, max_value=2030, value=date.today().year)


# Executa busca dos movimentos após seleção
movimentos = contas_do_mes(ano_sel, mes_sel)



# Cálculos dos blocos de métricas
if movimentos:
    df_calc = pd.DataFrame(movimentos)
    entradas = float(df_calc[df_calc["tipo"] == "receber"]["valor"].sum())
    saidas = float(df_calc[df_calc["tipo"] == "pagar"]["valor"].sum())
    saldo_final_previsto = saldo_ini + entradas - saidas

   
    entradas_pagas = float(df_calc[(df_calc["tipo"] == "receber") & (df_calc["status"] == "pago")]["valor"].sum())
    saidas_pagas = float(df_calc[(df_calc["tipo"] == "pagar") & (df_calc["status"] == "pago")]["valor"].sum())
    saldo_atual = saldo_ini + entradas_pagas - saidas_pagas
else:
    entradas, saidas, saldo_final_previsto, saldo_atual = 0.0, 0.0, saldo_ini, saldo_ini

with col_f_todos:
    t_style = "primary" if st.session_state.status_filtro_fluxo == "Todos" else "secondary"
    if st.button("Todos", type=t_style, use_container_width=True, key="fluxo_f_todos"):
        st.session_state.status_filtro_fluxo = "Todos"
        st.rerun()

with col_f_pend:
    p_style = "primary" if st.session_state.status_filtro_fluxo == "Pendente" else "secondary"
    if st.button("Pendentes", type=p_style, use_container_width=True, key="fluxo_f_pend"):
        st.session_state.status_filtro_fluxo = "Pendente"
        st.rerun()

with col_f_pago:
    pg_style = "primary" if st.session_state.status_filtro_fluxo == "Pago" else "secondary"
    if st.button("Pagos", type=pg_style, use_container_width=True, key="fluxo_f_pago"):
        st.session_state.status_filtro_fluxo = "Pago"
        st.rerun()


st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)



# ── MÉTRICAS SUPER COMPACTAS EM GRID ─────────────────────

m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.markdown(f'<div style="background-color: #f5f5f5; padding: 8px 12px; border-radius: 5px; border-left: 3px solid #64748b;">'
                f'<span style="font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase;">Saldo Inicial</span>'
                f'<h4 style="margin: 0; color: #1e293b; font-weight: 700; font-size: 14px;">{fmt(saldo_ini)}</h4></div>', unsafe_allow_html=True)

with m2:
    st.markdown(f'<div style="background-color: #f0fdf4; padding: 8px 12px; border-radius: 5px; border-left: 3px solid #16a34a;">'
                f'<span style="font-size: 10px; font-weight: 600; color: #16a34a; text-transform: uppercase;">Entradas Previstas</span>'
                f'<h4 style="margin: 0; color: #16a34a; font-weight: 700; font-size: 14px;">{fmt(entradas)}</h4></div>', unsafe_allow_html=True)

with m3:
    st.markdown(f'<div style="background-color: #fef2f2; padding: 8px 12px; border-radius: 5px; border-left: 3px solid #dc2626;">'
                f'<span style="font-size: 10px; font-weight: 600; color: #dc2626; text-transform: uppercase;">Saídas Previstas</span>'
                f'<h4 style="margin: 0; color: #dc2626; font-weight: 700; font-size: 14px;">{fmt(saidas)}</h4></div>', unsafe_allow_html=True)

with m4:

    st.markdown(f'<div style="background-color: #eff6ff; padding: 8px 12px; border-radius: 5px; border-left: 3px solid #2563eb;">'
                f'<span style="font-size: 10px; font-weight: 600; color: #2563eb; text-transform: uppercase;">Saldo Real Atual</span>'
                f'<h4 style="margin: 0; color: #2563eb; font-weight: 700; font-size: 14px;">{fmt(saldo_atual)}</h4></div>', unsafe_allow_html=True)

with m5:

    cor_final = "#16a34a" if saldo_final_previsto >= saldo_ini else "#dc2626"
    bg_final = "#f0fdf4" if saldo_final_previsto >= saldo_ini else "#fef2f2"
    st.markdown(f'<div style="background-color: {bg_final}; padding: 8px 12px; border-radius: 5px; border-left: 3px solid {cor_final};">'
                f'<span style="font-size: 10px; font-weight: 600; color: {cor_final}; text-transform: uppercase;">Saldo Final Previsto</span>'
                f'<h4 style="margin: 0; color: {cor_final}; font-weight: 700; font-size: 14px;">{fmt(saldo_final_previsto)}</h4></div>', unsafe_allow_html=True)



st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)



# ── EXIBIÇÃO DA TABELA DO EXTRATO ────────────────────────

if movimentos:
    linhas = [{
        "Data": f"01/{mes_sel:02d}/{ano_sel}",
        "Descrição": "🏦 Saldo Inicial (Contas Bancárias)",
        "Tipo": "—",
        "Entrada": "",
        "Saída": "",
        "Saldo": fmt(saldo_ini),
        "Status": "✅ Pago",
        "Categoria": "—",
        "Forma Pgto": "—",

    }]



    saldo_corrente = saldo_ini
    for row in sorted(movimentos, key=lambda x: x["data"]):
        is_entrada = row["tipo"] == "receber"
        valor = float(row["valor"])
        saldo_corrente += valor if is_entrada else -valor
        
        # --- ALTERAÇÃO AQUI ---
        # Se for conta a pagar, usamos o nome do cadastro (Beneficiário)
        # Se for conta a receber, usamos o nome do cadastro (Cliente)
        # Se o cadastro estiver vazio, mantemos a descrição original
        nome_exibicao = row["cadastro"] if row["cadastro"] else row["descricao"]

        linhas.append({
            "Data": pd.to_datetime(str(row["data"])).strftime("%d/%m/%Y"),
            "Descrição": nome_exibicao, # Substituímos row["descricao"] por nome_exibicao
            "Tipo": "💰 Receber" if is_entrada else "💸 Pagar",
            "Entrada": fmt(valor) if is_entrada else "",
            "Saída": "" if is_entrada else fmt(valor),
            "Saldo": fmt(saldo_corrente),
            "Status": "✅ Pago" if row["status"] == "pago" else "⏳ Pendente",
            "Categoria": row["categoria"] or "—",
            "Forma Pgto": row["forma_pagamento"] or "—",
        })



    df_view = pd.DataFrame(linhas)



    # Aplicação do Filtro de Estado Visual selecionado nos botões superiores

    if st.session_state.status_filtro_fluxo == "Pendente":

        # Mantém a linha 0 (Saldo inicial) e filtra as pendentes

        df_view = df_view[(df_view.index == 0) | (df_view["Status"] == "⏳ Pendente")]

    elif st.session_state.status_filtro_fluxo == "Pago":

        df_view = df_view[df_view["Status"] == "✅ Pago"]



    if not df_view.empty:

        def colorir(row):

            if row["Descrição"].startswith("🏦 Saldo"):

                return [""] * len(row)

            if row["Status"] == "⏳ Pendente":

                return ["background-color: #fffbeb; color: #b45309;"] * len(row)

            elif row["Tipo"] == "💰 Receber":

                return ["background-color: #f0fdf4; color: #15803d;"] * len(row)

            elif row["Tipo"] == "💸 Pagar":

                return ["background-color: #fef2f2; color: #b91c1c;"] * len(row)

            return [""] * len(row)



        st.dataframe(df_view.style.apply(colorir, axis=1), use_container_width=True, hide_index=True)

        st.caption(f"Exibindo {len(df_view)} registro(s) no fluxo histórico do período.")

       

        # Área de exportação alinhada no rodapé

        st.markdown("---")

        csv = df_view.to_csv(index=False).encode("utf-8")

        st.download_button(

            "⬇️ Exportar Extrato Mensal (CSV)",

            csv,

            f"fluxo_{MESES[mes_sel]}_{ano_sel}.csv",

            "text/csv",

            use_container_width=True

        )

    else:

        st.info(f"Nenhum registro correspondente ao filtro '{st.session_state.status_filtro_fluxo}'.")

else:

    st.info(f"Nenhum lançamento ou movimentação financeira encontrada para {MESES[mes_sel]}/{ano_sel}.") 