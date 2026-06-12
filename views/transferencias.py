import streamlit as st
import pandas as pd
from database.connection import execute_query
from datetime import date

# ── CSS ──────────────────────────────────────────────────
st.markdown("""
    <style>
        .block-container { padding-top: 3rem !important; }
        h1 {
            margin-top: 0 !important; padding-top: 0 !important;
            margin-bottom: 0.8rem !important; font-size: 28px !important;
            font-weight: 700 !important; color: #1e293b;
        }
    </style>
""", unsafe_allow_html=True)

# ── FUNÇÕES DE SUPORTE ───────────────────────────────────
def fmt(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# ── CONSULTAS ────────────────────────────────────────────
def listar_contas_ativas():
    return execute_query(
        "SELECT id, nome, banco FROM contas_bancarias WHERE ativo = true ORDER BY nome",
        fetch=True
    )

def get_saldo_atual(conta_id):
    """Calcula saldo corrente: saldo_inicial + entradas - saídas - transferências saídas + transferências recebidas"""
    res = execute_query("""
        SELECT
            cb.saldo_inicial,
            COALESCE((SELECT SUM(valor) FROM contas_receber
                      WHERE conta_bancaria_id = cb.id AND status = 'pago'), 0) AS total_recebido,
            COALESCE((SELECT SUM(valor) FROM contas_pagar
                      WHERE conta_bancaria_id = cb.id AND status = 'pago'), 0) AS total_pago,
            COALESCE((SELECT SUM(valor) FROM transferencias
                      WHERE conta_origem_id = cb.id), 0)  AS total_transferido_saida,
            COALESCE((SELECT SUM(valor) FROM transferencias
                      WHERE conta_destino_id = cb.id), 0) AS total_transferido_entrada
        FROM contas_bancarias cb
        WHERE cb.id = %s
    """, (conta_id,), fetch=True)

    if res:
        r = res[0]
        saldo = (
            float(r["saldo_inicial"] or 0)
            + float(r["total_recebido"])
            - float(r["total_pago"])
            - float(r["total_transferido_saida"])
            + float(r["total_transferido_entrada"])
        )
        return saldo
    return 0.0

def listar_transferencias():
    return execute_query("""
        SELECT
            t.id,
            co.nome  AS origem,
            cd.nome  AS destino,
            t.valor,
            t.data_transferencia,
            t.descricao,
            t.criado_em
        FROM transferencias t
        JOIN contas_bancarias co ON t.conta_origem_id  = co.id
        JOIN contas_bancarias cd ON t.conta_destino_id = cd.id
        ORDER BY t.data_transferencia DESC, t.criado_em DESC
    """, fetch=True)

def inserir_transferencia(origem_id, destino_id, valor, data, descricao):
    execute_query("""
        INSERT INTO transferencias (conta_origem_id, conta_destino_id, valor, data_transferencia, descricao)
        VALUES (%s, %s, %s, %s, %s)
    """, (origem_id, destino_id, valor, data, descricao))

def deletar_transferencia(id):
    execute_query("DELETE FROM transferencias WHERE id = %s", (id,))

# ── MODAL: NOVA TRANSFERÊNCIA ─────────────────────────────
@st.dialog("Nova Transferência entre Contas", width="medium")
def modal_nova_transferencia():
    contas = listar_contas_ativas()
    if not contas or len(contas) < 2:
        st.warning("É necessário ter ao menos 2 contas bancárias ativas para realizar transferências.")
        return

    opc = {f"{c['nome']} — {c['banco']}": c["id"] for c in contas}

    with st.form("form_transferencia", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            origem_nome  = st.selectbox("Conta de Origem *", ["— Selecione —"] + list(opc.keys()))
        with col2:
            destino_nome = st.selectbox("Conta de Destino *", ["— Selecione —"] + list(opc.keys()))

        col3, col4 = st.columns(2)
        with col3:
            valor_str = st.text_input("Valor (R$) *", placeholder="0,00")
        with col4:
            data = st.date_input("Data da Transferência *", value=date.today(), format="DD/MM/YYYY")

        descricao = st.text_input("Descrição", placeholder="Ex: Reforço de caixa, TED entre contas")

        # Preview de saldo em tempo real (leitura antes de confirmar)
        if origem_nome != "— Selecione —":
            saldo_origem = get_saldo_atual(opc[origem_nome])
            st.info(f"💰 Saldo atual da conta de origem: **{fmt(saldo_origem)}**")

        _, col_cancelar, col_salvar = st.columns([4, 2.5, 2.5])
        with col_cancelar:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)
        with col_salvar:
            submitted = st.form_submit_button("✓ Transferir", type="primary", use_container_width=True)

    if cancelar:
        st.rerun()

    if submitted:
        # Validações em camadas
        if origem_nome == "— Selecione —" or destino_nome == "— Selecione —":
            st.error("Selecione as duas contas.")
            return
        if origem_nome == destino_nome:
            st.error("A conta de origem e destino não podem ser a mesma!")
            return

        try:
            valor = float(valor_str.replace(".", "").replace(",", "."))
        except:
            st.error("Digite um valor válido.")
            return

        if valor <= 0:
            st.error("O valor deve ser maior que zero.")
            return

        saldo_disponivel = get_saldo_atual(opc[origem_nome])
        if valor > saldo_disponivel:
            st.error(f"Saldo insuficiente! Disponível: {fmt(saldo_disponivel)}")
            return

        try:
            inserir_transferencia(opc[origem_nome], opc[destino_nome], valor, data, descricao or None)
            st.success(f"✅ Transferência de {fmt(valor)} realizada com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao registrar: {e}")


# ── TÍTULO ────────────────────────────────────────────────
st.markdown("<h1>💸 Transferências entre Contas</h1>", unsafe_allow_html=True)

# ── MÉTRICAS DE SALDO POR CONTA ───────────────────────────
contas = listar_contas_ativas()
if contas:
    st.markdown("##### Saldo Atual por Conta")
    cols = st.columns(min(len(contas), 4))  # máx 4 colunas
    for i, c in enumerate(contas):
        saldo = get_saldo_atual(c["id"])
        cor = "#16a34a" if saldo >= 0 else "#dc2626"
        bg  = "#f0fdf4" if saldo >= 0 else "#fef2f2"
        with cols[i % 4]:
            st.markdown(
                f'<div style="background:{bg}; padding:8px 12px; border-radius:5px; border-left:3px solid {cor}; margin-bottom:8px;">'
                f'<span style="font-size:10px; font-weight:600; color:{cor}; text-transform:uppercase;">{c["nome"]}</span><br>'
                f'<span style="font-size:11px; color:#64748b;">{c["banco"]}</span>'
                f'<h4 style="margin:2px 0 0; color:{cor}; font-size:16px; font-weight:700;">{fmt(saldo)}</h4></div>',
                unsafe_allow_html=True
            )

st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)

# ── BOTÃO NOVA TRANSFERÊNCIA ──────────────────────────────
_, col_btn = st.columns([7, 3])
with col_btn:
    if st.button("➕ Nova Transferência", type="primary", use_container_width=True):
        modal_nova_transferencia()

st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)

# ── HISTÓRICO ────────────────────────────────────────────
transferencias = listar_transferencias()
if transferencias:
    df = pd.DataFrame(transferencias)
    df_visual = df[["id", "origem", "destino", "valor", "data_transferencia", "descricao"]].copy()
    df_visual.columns = ["ID", "Origem", "Destino", "Valor", "Data", "Descrição"]
    df_visual["Valor"] = df_visual["Valor"].apply(fmt)
    df_visual["Data"]  = pd.to_datetime(df_visual["Data"]).dt.strftime("%d/%m/%Y")
    df_visual["Descrição"] = df_visual["Descrição"].fillna("—")

    st.dataframe(df_visual, use_container_width=True, hide_index=True)
    st.caption(f"Exibindo {len(df_visual)} transferência(s).")

    # ── EXCLUSÃO ─────────────────────────────────────────
    st.markdown("---")
    st.markdown("⚙️ **Estornar Transferência**")
    opc_del = {
        f"ID: {row['id']} | {row['origem']} → {row['destino']} | {fmt(row['valor'])} | {pd.to_datetime(row['data_transferencia']).strftime('%d/%m/%Y')}": row["id"]
        for _, row in df.iterrows()
    }
    escolha = st.selectbox("Selecione para estornar:", list(opc_del.keys()), label_visibility="collapsed")

    _, col_del = st.columns([8, 2])
    with col_del:
        if st.button("🗑️ Estornar", use_container_width=True):
            deletar_transferencia(int(opc_del[escolha]))
            st.warning("Transferência estornada.")
            st.rerun()
else:
    st.info("Nenhuma transferência registrada.")