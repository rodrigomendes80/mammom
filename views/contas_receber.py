import streamlit as st
import pandas as pd
from database.connection import execute_query
from datetime import date, datetime

# ── CONFIGURAÇÃO DE ESTADO DO FILTRO ─────────────────────
if "status_filtro_receber" not in st.session_state:
    st.session_state.status_filtro_receber = "Todos"

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
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "R$ 0,00"

def converter(v):
    try:
        return float(v.replace(".", "").replace(",", "."))
    except:
        return None

# ── CONSULTAS AO BANCO (SUPABASE) ────────────────────────
def listar():
    return execute_query("""
        SELECT
            cr.id,
            cr.descricao,
            cr.valor,
            cr.vencimento,
            cr.status,
            cr.forma_pagamento,
            ca.descricao        AS categoria,
            cl.nome              AS cliente,
            cb.nome             AS conta_bancaria,
            cr.categoria_id,
            cr.cliente_id,
            cr.conta_bancaria_id
        FROM contas_receber cr
        LEFT JOIN categorias       ca ON cr.categoria_id     = ca.id
        LEFT JOIN clientes         cl ON cr.cliente_id       = cl.id
        LEFT JOIN contas_bancarias cb ON cr.conta_bancaria_id = cb.id
        ORDER BY cr.vencimento
    """, fetch=True)

def buscar_por_id(id_conta):
    res = execute_query("SELECT * FROM contas_receber WHERE id = %s", (id_conta,), fetch=True)
    return res[0] if res else None

def listar_clientes():
    return execute_query("SELECT id, nome FROM clientes WHERE ativo = true ORDER BY nome", fetch=True)

def listar_categorias():
    return execute_query("SELECT id, descricao FROM categorias WHERE tipo = 'receber' AND ativo = true ORDER BY descricao", fetch=True)

def listar_contas_bancarias():
    return execute_query("SELECT id, nome FROM contas_bancarias WHERE ativo = true ORDER BY nome", fetch=True)

def inserir(descricao, valor, vencimento, forma_pagamento, conta_bancaria_id, categoria_id, cliente_id):
    execute_query("""
        INSERT INTO contas_receber
            (descricao, valor, vencimento, forma_pagamento, conta_bancaria_id, categoria_id, cliente_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (descricao, valor, vencimento, forma_pagamento, conta_bancaria_id, categoria_id, cliente_id))

def atualizar_conta(id_conta, dados):
    execute_query("""
        UPDATE contas_receber
        SET descricao = %s, valor = %s, vencimento = %s, forma_pagamento = %s,
            conta_bancaria_id = %s, categoria_id = %s, cliente_id = %s, status = %s
        WHERE id = %s
    """, (*dados, id_conta))

def baixar(id):
    execute_query("UPDATE contas_receber SET status = 'pago', pago_em = %s WHERE id = %s", (date.today(), id))

def deletar(id):
    execute_query("DELETE FROM contas_receber WHERE id = %s", (id,))

FORMAS = ["Pix", "Boleto", "Cartão de Crédito", "Cartão de Débito", "TED/DOC", "Dinheiro"]
STATUS_OPCOES = ["pendente", "pago"]

# ── JANELA MODAL POP-UP CADASTRAR ────────────────────────
@st.dialog("Nova Conta a Receber", width="medium")
def modal_cadastrar_conta():
    clientes    = listar_clientes()
    categorias  = listar_categorias()
    cbs         = listar_contas_bancarias()

    opc_cli = {c["nome"]: c["id"] for c in clientes} if clientes else {}
    opc_cat = {c["descricao"]: c["id"] for c in categorias} if categorias else {}
    opc_cb  = {c["nome"]: c["id"] for c in cbs} if cbs else {}

    with st.form("form_modal_receber", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cli_nome = st.selectbox("Cliente *", ["— Selecione —"] + list(opc_cli.keys()))
            descricao = st.text_input("Descrição *", placeholder="Ex: Venda NF 456")
            valor_str = st.text_input("Valor (R$) *", placeholder="0,00")
            
        with col2:
            vencimento = st.date_input("Vencimento *", value=date.today(), format="DD/MM/YYYY")
            forma_recebimento = st.selectbox("Forma de Recebimento *", FORMAS)
            cb_nome = st.selectbox("Conta Bancária *", ["— Selecione —"] + list(opc_cb.keys()))

        cat_nome = st.selectbox("Categoria", ["— Selecione —"] + list(opc_cat.keys()))

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        
        _, col_btn_cancelar, col_btn_salvar = st.columns([4, 2.5, 2.5])
        with col_btn_cancelar:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)
        with col_btn_salvar:
            submitted = st.form_submit_button("✓ Salvar", type="primary", use_container_width=True)

    if cancelar:
        st.rerun()

    if submitted:
        valor = converter(valor_str) if valor_str else None
        if not descricao: st.error("Descrição é obrigatória!")
        elif not valor: st.error("Digite um valor válido.")
        else:
            try:
                inserir(descricao, valor, vencimento, forma_recebimento,
                        opc_cb.get(cb_nome), opc_cat.get(cat_nome), opc_cli.get(cli_nome))
                st.success("Conta a receber cadastrada!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# ── JANELA MODAL POP-UP EDITAR ───────────────────────────
@st.dialog("Editar Conta a Receber", width="medium")
def modal_editar_conta(id_conta):
    conta = buscar_por_id(id_conta)
    if not conta:
        st.error("Conta não encontrada.")
        return

    clientes    = listar_clientes()
    categorias  = listar_categorias()
    cbs         = listar_contas_bancarias()

    opc_cli = {c["nome"]: c["id"] for c in clientes} if clientes else {}
    opc_cat = {c["descricao"]: c["id"] for c in categorias} if categorias else {}
    opc_cb  = {c["nome"]: c["id"] for c in cbs} if cbs else {}

    nome_cli_natal = next((k for k, v in opc_cli.items() if v == conta["cliente_id"]), "— Selecione —")
    nome_cat_atual = next((k for k, v in opc_cat.items() if v == conta["categoria_id"]), "— Selecione —")
    nome_cb_atual  = next((k for k, v in opc_cb.items() if v == conta["conta_bancaria_id"]), "— Selecione —")

    lista_cli = ["— Selecione —"] + list(opc_cli.keys())
    lista_cat = ["— Selecione —"] + list(opc_cat.keys())
    lista_cb  = ["— Selecione —"] + list(opc_cb.keys())

    with st.form("form_modal_editar_receber"):
        col1, col2 = st.columns(2)
        with col1:
            cli_nome = st.selectbox("Cliente *", lista_cli, index=lista_cli.index(nome_cli_natal))
            descricao = st.text_input("Descrição *", value=conta["descricao"] or "")
            valor_str = st.text_input("Valor (R$) *", value=f"{float(conta['valor']):,.2f}".replace('.', ','))
            
        with col2:
            vencimento = st.date_input("Vencimento *", value=conta["vencimento"] if isinstance(conta["vencimento"], date) else datetime.strptime(str(conta["vencimento"]), "%Y-%m-%d").date(), format="DD/MM/YYYY")
            forma_recebimento = st.selectbox("Forma de Recebimento *", FORMAS, index=FORMAS.index(conta["forma_pagamento"]) if conta["forma_pagamento"] in FORMAS else 0)
            cb_nome = st.selectbox("Conta Bancária *", lista_cb, index=lista_cb.index(nome_cb_atual))

        cat_nome = st.selectbox("Categoria", lista_cat, index=lista_cat.index(nome_cat_atual))
        status_atual = st.selectbox("Status *", STATUS_OPCOES, index=STATUS_OPCOES.index(conta["status"]) if conta["status"] in STATUS_OPCOES else 0)

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        
        _, col_btn_cancelar, col_btn_salvar = st.columns([4, 2.5, 2.5])
        with col_btn_cancelar:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)
        with col_btn_salvar:
            submitted = st.form_submit_button("✓ Salvar", type="primary", use_container_width=True)

    if cancelar:
        st.rerun()

    if submitted:
        valor = converter(valor_str)
        if not descricao: st.error("Descrição é obrigatória!")
        elif not valor: st.error("Digite um valor válido.")
        else:
            dados_atualizados = (
                descricao, valor, vencimento, forma_recebimento,
                opc_cb.get(cb_nome), opc_cat.get(cat_nome), opc_cli.get(cli_nome), status_atual
            )
            atualizar_conta(id_conta, dados_atualizados)
            st.success("Lançamento atualizado com sucesso!")
            st.rerun()


# Fetch inicial dos dados
contas = listar()

# ── TÍTULO (LARGURA TOTAL E PROTEGIDO) ───────────────────
st.markdown("<h1>Contas a Receber</h1>", unsafe_allow_html=True)

# ── MÉTRICAS SUPER COMPACTAS ─────────────────────────────
if contas:
    df_m = pd.DataFrame(contas)
    df_m["valor"] = df_m["valor"].astype(float)
    
    total_a_receber = df_m["valor"].sum()
    total_pendente = df_m[df_m["status"] == "pendente"]["valor"].sum()
    total_recebido = df_m[df_m["status"] == "pago"]["valor"].sum()

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'<div style="background-color: #f5f5f5; padding: 8px 12px; border-radius: 5px; border-left: 3px solid #64748b;">'
                    f'<span style="font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Total a Receber</span>'
                    f'<h4 style="margin: 0; color: #1e293b; font-weight: 700; font-size: 16px;">{fmt(total_a_receber)}</h4></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div style="background-color: #fef2f2; padding: 8px 12px; border-radius: 5px; border-left: 3px solid #dc2626;">'
                    f'<span style="font-size: 10px; font-weight: 600; color: #dc2626; text-transform: uppercase; letter-spacing: 0.5px;">Pendente</span>'
                    f'<h4 style="margin: 0; color: #dc2626; font-weight: 700; font-size: 16px;">{fmt(total_pendente)}</h4></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div style="background-color: #f0fdf4; padding: 8px 12px; border-radius: 5px; border-left: 3px solid #16a34a;">'
                    f'<span style="font-size: 10px; font-weight: 600; color: #16a34a; text-transform: uppercase; letter-spacing: 0.5px;">Já Recebido</span>'
                    f'<h4 style="margin: 0; color: #16a34a; font-weight: 700; font-size: 16px;">{fmt(total_recebido)}</h4></div>', unsafe_allow_html=True)

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

# ── LINHA DE CONTROLES: FILTROS E NOVA CONTA LADO A LADO ──
col_todos, col_pendente, col_pago, _, col_nova_conta = st.columns([1, 1.2, 1, 4.3, 2.5], vertical_alignment="center")

with col_todos:
    t_style = "primary" if st.session_state.status_filtro_receber == "Todos" else "secondary"
    if st.button("Todos", type=t_style, use_container_width=True, key="btn_rec_todos"):
        st.session_state.status_filtro_receber = "Todos"
        st.rerun()

with col_pendente:
    p_style = "primary" if st.session_state.status_filtro_receber == "Pendente" else "secondary"
    if st.button("Pendente", type=p_style, use_container_width=True, key="btn_rec_pend"):
        st.session_state.status_filtro_receber = "Pendente"
        st.rerun()

with col_pago:
    pg_style = "primary" if st.session_state.status_filtro_receber == "Pago" else "secondary"
    if st.button("Pago", type=pg_style, use_container_width=True, key="btn_rec_pago"):
        st.session_state.status_filtro_receber = "Pago"
        st.rerun()

with col_nova_conta:
    if st.button("Nova Conta", type="primary", use_container_width=True, key="btn_rec_nova"):
        modal_cadastrar_conta()

st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

# ── EXIBIÇÃO DA TABELA FILTRADA ─────────────────────────
if contas:
    df = pd.DataFrame(contas)
    
    if st.session_state.status_filtro_receber == "Pendente":
        df = df[df["status"] == "pendente"]
    elif st.session_state.status_filtro_receber == "Pago":
        df = df[df["status"] == "pago"]

    if not df.empty:
        df_visual = df.copy()
        
        df_visual = df_visual[["id", "cliente", "valor", "vencimento", "status", "forma_pagamento", "categoria", "conta_bancaria"]]
        df_visual.columns = ["ID", "Cliente",  "Valor", "Vencimento", "Status",
                             "Forma Recebimento", "Categoria",  "Conta Bancária"]
        
        df_visual["Status"] = df_visual["Status"].map({"pendente": "⏳ pendente", "pago": "✅ pago", "cancelado": "❌ cancelado"})
        df_visual["Valor"] = df_visual["Valor"].apply(fmt)
        df_visual["Vencimento"] = pd.to_datetime(df_visual["Vencimento"]).dt.strftime("%d/%m/%Y")
        
        st.dataframe(df_visual, use_container_width=True, hide_index=True)
        st.caption(f"Exibindo {len(df_visual)} registro(s).")
        
        # Bloco de Gerenciamento de Linha
        st.markdown("---")
        st.markdown("⚙️ **Ações Rápidas para a Linha Selecionada**")
        opc_linha = {f"ID: {row['id']} — {row['descricao']} | {fmt(row['valor'])}": row['id'] for _, row in df.iterrows()}
        escolha_id = st.selectbox("Escolha uma conta da lista para dar baixa ou remover:", list(opc_linha.keys()), label_visibility="collapsed", key="sel_linha_rec")
        
        row_sel = df[df["id"] == opc_linha[escolha_id]].iloc[0]
        
        act1, act2, act3, _ = st.columns([2, 2, 2, 4])
        with act1:
            if row_sel["status"] == "pendente":
                if st.button("✅ Confirmar Recebimento", use_container_width=True):
                    baixar(int(row_sel["id"]))
                    st.success("Recebimento liquidado!")
                    st.rerun()
            else:
                st.info("Linha já Recebida.")
        with act2:
            if st.button("✏️ Editar Conta", use_container_width=True):
                modal_editar_conta(int(row_sel["id"]))
        with act3:
            if st.button("🗑️ Excluir Lançamento", use_container_width=True):
                deletar(int(row_sel["id"]))
                st.warning("Removido.")
                st.rerun()
    else:
        st.info(f"Nenhum lançamento com o status '{st.session_state.status_filtro_receber}停")
else:
    st.info("Nenhuma conta registrada no banco de dados.")