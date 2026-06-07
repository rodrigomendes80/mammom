from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import streamlit as st
import pandas as pd
from database.connection import execute_query
from datetime import date, datetime
import uuid

# ── CONFIGURAÇÃO DE ESTADO DO FILTRO ─────────────────────
if "status_filtro" not in st.session_state:
    st.session_state.status_filtro = "Todos"

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

def adicionar_meses(data_origem, meses):
    ano = data_origem.year + (data_origem.month + meses - 1) // 12
    mes = (data_origem.month + meses - 1) % 12 + 1
    dia = min(data_origem.day, [31,
        29 if ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0) else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1])
    return date(ano, mes, dia)

# ── CONSULTAS AO BANCO (SUPABASE) ────────────────────────
def listar():
    return execute_query("""
        SELECT
            cp.id,
            b.nome              AS beneficiario,
            cp.descricao,
            cp.valor,
            cp.vencimento,
            cp.status,
            cp.forma_pagamento,
            cp.numero_documento,
            ca.descricao        AS categoria,
            cb.nome             AS conta_bancaria,
            cp.categoria_id,
            cp.beneficiario_id,
            cp.conta_bancaria_id
        FROM contas_pagar cp
        LEFT JOIN categorias       ca ON cp.categoria_id     = ca.id
        LEFT JOIN beneficiarios    b ON cp.beneficiario_id  = b.id
        LEFT JOIN contas_bancarias cb ON cp.conta_bancaria_id = cb.id
        ORDER BY cp.vencimento
    """, fetch=True)

def buscar_por_id(id_conta):
    res = execute_query("SELECT * FROM contas_pagar WHERE id = %s", (id_conta,), fetch=True)
    return res[0] if res else None

def listar_beneficiarios():
    return execute_query("SELECT id, nome FROM beneficiarios WHERE ativo = true ORDER BY nome", fetch=True)

def listar_categorias():
    return execute_query("SELECT id, descricao FROM categorias WHERE tipo = 'pagar' AND ativo = true ORDER BY descricao", fetch=True)

def listar_contas_bancarias():
    return execute_query("SELECT id, nome FROM contas_bancarias WHERE ativo = true ORDER BY nome", fetch=True)

def inserir_multiplos(registros):
    for reg in registros:
        execute_query("""
            INSERT INTO contas_pagar
                (descricao, valor, vencimento, forma_pagamento,
                 conta_bancaria_id, numero_documento, categoria_id, beneficiario_id, recorrente, grupo_recorrencia_id, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, reg)

def atualizar_conta(id_conta, dados):
    execute_query("""
        UPDATE contas_pagar
        SET descricao = %s, valor = %s, vencimento = %s, forma_pagamento = %s,
            conta_bancaria_id = %s, numero_documento = %s, categoria_id = %s, beneficiario_id = %s, status = %s
        WHERE id = %s
    """, (*dados, id_conta))

def baixar(id):
    execute_query("UPDATE contas_pagar SET status = 'pago', pago_em = %s WHERE id = %s", (date.today(), id))

def deletar(id):
    execute_query("DELETE FROM contas_pagar WHERE id = %s", (id,))

FORMAS = ["Boleto", "Pix", "TED/DOC", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Fatura"]
STATUS_OPCOES = ["pendente", "pago"]

# ── JANELA MODAL POP-UP CADASTRAR ────────────────────────
@st.dialog("Nova Conta a Pagar", width="medium")
def modal_cadastrar_conta():
    beneficiarios = listar_beneficiarios()
    categorias    = listar_categorias()
    cbs           = listar_contas_bancarias()

    opc_ben = {b["nome"]: b["id"] for b in beneficiarios} if beneficiarios else {}
    opc_cat = {c["descricao"]: c["id"] for c in categorias} if categorias else {}
    opc_cb  = {c["nome"]: c["id"] for c in cbs} if cbs else {}

    with st.form("form_modal_pagar", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            ben_nome = st.selectbox("Favorecido / Fornecedor *", ["— Selecione —"] + list(opc_ben.keys()))
            valor_str = st.text_input("Valor (R$) *", placeholder="0,00")
            vencimento = st.date_input("Data de Vencimento *", value=None, format="DD/MM/YYYY")
            
        with col2:
            forma_pagamento = st.selectbox("Forma de Pagamento *", FORMAS)
            cb_nome = st.selectbox("Conta Bancária *", ["— Selecione —"] + list(opc_cb.keys()))
            numero_documento = st.text_input("Nº Documento", placeholder="Opcional")

        descricao = st.text_input("Descrição / Identificação do Lançamento", placeholder="Ex: Parcela Única / Assinatura Mensal")
        cat_nome = st.selectbox("Categoria", ["— Selecione —"] + list(opc_cat.keys()))
        status_atual = st.selectbox("Status *", STATUS_OPCOES, index=0)

        st.markdown("<p style='font-size: 13px; font-weight: 600; margin-bottom: -5px; color: #475569;'>🔄 Recorrência Mensal</p>", unsafe_allow_html=True)
        col_rec1, col_rec2 = st.columns([1.2, 1])
        with col_rec1:
            is_recorrente = st.checkbox("Repetir esta despesa mensalmente?", key="modal_rec_checkbox")
        with col_rec2:
            data_limite = st.date_input("Até quando?", value=None, format="DD/MM/YYYY", disabled=not is_recorrente, label_visibility="collapsed", key="modal_rec_data_limite")

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
        if not valor: st.error("Digite um valor válido.")
        elif not vencimento: st.error("Informe a data de vencimento!")
        elif is_recorrente and not data_limite: st.error("Você deve definir uma data limite para a recorrência!")
        elif is_recorrente and data_limite <= vencimento: st.error("A data limite deve ser maior que o primeiro vencimento!")
        else:
            try:
                registros_a_inserir = []
                grupo_id = str(uuid.uuid4()) if is_recorrente else None
                
                if not is_recorrente:
                    registros_a_inserir.append((
    descricao or "Sem descrição", valor, vencimento, forma_pagamento,
    opc_cb.get(cb_nome), numero_documento or None, opc_cat.get(cat_nome),
    opc_ben.get(ben_nome), False, None, status_atual # Adicione aqui
))
                else:
                    vencimento_atual = vencimento
                    mes_indice = 0
                    while vencimento_atual <= data_limite:
                        desc_parcela = f"{descricao or 'Despesa'} (Mês {mes_indice + 1})" if mes_indice > 0 else (descricao or "Despesa")
                        registros_a_inserir.append((
                            desc_parcela, valor, vencimento_atual, forma_pagamento,
                            opc_cb.get(cb_nome), numero_documento or None, opc_cat.get(cat_nome),
                            opc_ben.get(ben_nome), True, grupo_id
                        ))
                        mes_indice += 1
                        vencimento_atual = adicionar_meses(vencimento, mes_indice)

                inserir_multiplos(registros_a_inserir)
                st.success("Conta cadastrada!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao processar lote: {e}")


# ── JANELA MODAL POP-UP EDITAR ───────────────────────────
@st.dialog("Editar Conta a Pagar", width="medium")
def modal_editar_conta(id_conta):
    conta = buscar_por_id(id_conta)
    if not conta:
        st.error("Conta não encontrada.")
        return

    beneficiarios = listar_beneficiarios()
    categorias    = listar_categorias()
    cbs           = listar_contas_bancarias()

    opc_ben = {b["nome"]: b["id"] for b in beneficiarios} if beneficiarios else {}
    opc_cat = {c["descricao"]: c["id"] for c in categorias} if categorias else {}
    opc_cb  = {c["nome"]: c["id"] for c in cbs} if cbs else {}

    nome_ben_atual = next((k for k, v in opc_ben.items() if v == conta["beneficiario_id"]), "— Selecione —")
    nome_cat_atual = next((k for k, v in opc_cat.items() if v == conta["categoria_id"]), "— Selecione —")
    nome_cb_atual  = next((k for k, v in opc_cb.items() if v == conta["conta_bancaria_id"]), "— Selecione —")

    lista_ben = ["— Selecione —"] + list(opc_ben.keys())
    lista_cat = ["— Selecione —"] + list(opc_cat.keys())
    lista_cb  = ["— Selecione —"] + list(opc_cb.keys())

    with st.form("form_modal_editar"):
        col1, col2 = st.columns(2)
        with col1:
            ben_nome = st.selectbox("Favorecido / Fornecedor *", lista_ben, index=lista_ben.index(nome_ben_atual))
            valor_str = st.text_input("Valor (R$) *", value=f"{float(conta['valor']):,.2f}".replace('.', ','))
            vencimento = st.date_input("Data de Vencimento *", value=conta["vencimento"] if isinstance(conta["vencimento"], date) else datetime.strptime(str(conta["vencimento"]), "%Y-%m-%d").date(), format="DD/MM/YYYY")
            
        with col2:
            forma_pagamento = st.selectbox("Forma de Pagamento *", FORMAS, index=FORMAS.index(conta["forma_pagamento"]) if conta["forma_pagamento"] in FORMAS else 0)
            cb_nome = st.selectbox("Conta Bancária *", lista_cb, index=lista_cb.index(nome_cb_atual))
            numero_documento = st.text_input("Nº Documento", value=conta["numero_documento"] or "")

        descricao = st.text_input("Descrição / Identificação", value=conta["descricao"] or "")
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
        if not valor: 
            st.error("Digite um valor válido.")
        else:
            dados_atualizados = (
                descricao or "Sem descrição", valor, vencimento, forma_pagamento,
                opc_cb.get(cb_nome), numero_documento or None, opc_cat.get(cat_nome),
                opc_ben.get(ben_nome), status_atual
            )
            atualizar_conta(id_conta, dados_atualizados)
            st.success("Lançamento atualizado com sucesso!")
            st.rerun()


# Fetch inicial dos dados
contas = listar()

# ── TÍTULO (LARGURA TOTAL E PROTEGIDO) ───────────────────
st.markdown("<h1>Contas a Pagar</h1>", unsafe_allow_html=True)

# ── MÉTRICAS SUPER COMPACTAS ─────────────────────────────
if contas:
    df_m = pd.DataFrame(contas)
    df_m["valor"] = df_m["valor"].astype(float)
    
    total_a_pagar = df_m["valor"].sum()
    total_pendente = df_m[df_m["status"] == "pendente"]["valor"].sum()
    total_pago = df_m[df_m["status"] == "pago"]["valor"].sum()

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'<div style="background-color: #f5f5f5; padding: 8px 12px; border-radius: 5px; border-left: 3px solid #64748b;">'
                    f'<span style="font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Total a Pagar</span>'
                    f'<h4 style="margin: 0; color: #1e293b; font-weight: 700; font-size: 16px;">{fmt(total_a_pagar)}</h4></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div style="background-color: #fef2f2; padding: 8px 12px; border-radius: 5px; border-left: 3px solid #dc2626;">'
                    f'<span style="font-size: 10px; font-weight: 600; color: #dc2626; text-transform: uppercase; letter-spacing: 0.5px;">Pendente</span>'
                    f'<h4 style="margin: 0; color: #dc2626; font-weight: 700; font-size: 16px;">{fmt(total_pendente)}</h4></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div style="background-color: #f0fdf4; padding: 8px 12px; border-radius: 5px; border-left: 3px solid #16a34a;">'
                    f'<span style="font-size: 10px; font-weight: 600; color: #16a34a; text-transform: uppercase; letter-spacing: 0.5px;">Já Pago</span>'
                    f'<h4 style="margin: 0; color: #16a34a; font-weight: 700; font-size: 16px;">{fmt(total_pago)}</h4></div>', unsafe_allow_html=True)

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

# ── LINHA DE CONTROLES: FILTROS E NOVA CONTA LADO A LADO ──
col_todos, col_pendente, col_pago, _, col_nova_conta = st.columns([1, 1.2, 1, 4.3, 2.5], vertical_alignment="center")

with col_todos:
    t_style = "primary" if st.session_state.status_filtro == "Todos" else "secondary"
    if st.button("Todos", type=t_style, use_container_width=True):
        st.session_state.status_filtro = "Todos"
        st.rerun()

with col_pendente:
    p_style = "primary" if st.session_state.status_filtro == "Pendente" else "secondary"
    if st.button("Pendente", type=p_style, use_container_width=True):
        st.session_state.status_filtro = "Pendente"
        st.rerun()

with col_pago:
    pg_style = "primary" if st.session_state.status_filtro == "Pago" else "secondary"
    if st.button("Pago", type=pg_style, use_container_width=True):
        st.session_state.status_filtro = "Pago"
        st.rerun()

with col_nova_conta:
    if st.button("Nova Conta", type="primary", use_container_width=True):
        modal_cadastrar_conta()

st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

# ── EXIBIÇÃO DA TABELA FILTRADA ─────────────────────────
if contas:
    df = pd.DataFrame(contas)
    
    if st.session_state.status_filtro == "Pendente":
        df = df[df["status"] == "pendente"]
    elif st.session_state.status_filtro == "Pago":
        df = df[df["status"] == "pago"]

    if not df.empty:
        df_visual = df.copy()
        
        # Filtra apenas o subset de colunas que devem ir para a tela do usuário
        df_visual = df_visual[["id", "beneficiario", "valor", "vencimento", "status", "forma_pagamento", "categoria", "conta_bancaria"]]
        df_visual.columns = ["ID", "Beneficiário", "Valor", "Vencimento", "Status",
                             "Forma Pgto", "Categoria", "Conta Bancária"]
        
        df_visual["Status"] = df_visual["Status"].map({"pendente": "⏳ pendente", "pago": "✅ pago", "cancelado": "❌ cancelado"})
        df_visual["Valor"] = df_visual["Valor"].apply(fmt)
        df_visual["Vencimento"] = pd.to_datetime(df_visual["Vencimento"]).dt.strftime("%d/%m/%Y")
        
        st.dataframe(df_visual, use_container_width=True, hide_index=True)
        st.caption(f"Exibindo {len(df_visual)} registro(s).")
        
        # Bloco de Gerenciamento de Linha
        st.markdown("---")
        st.markdown("⚙️ **Ações Rápidas para a Linha Selecionada**")
        opc_linha = {f"ID: {row['id']} — {row['beneficiario']} | {fmt(row['valor'])}": row['id'] for _, row in df.iterrows()}
        escolha_id = st.selectbox("Escolha uma conta da lista para dar baixa ou remover:", list(opc_linha.keys()), label_visibility="collapsed")
        
        row_sel = df[df["id"] == opc_linha[escolha_id]].iloc[0]
        
        # Grid de botões atualizado para 3 colunas (Pagar, Editar, Excluir)
        act1, act2, act3, _ = st.columns([2, 2, 2, 4])
        with act1:
            if row_sel["status"] == "pendente":
                if st.button("✅ Confirmar Pagamento", use_container_width=True):
                    baixar(int(row_sel["id"]))
                    st.success("Conta liquidada!")
                    st.rerun()
            else:
                st.info("Linha já Paga.")
        with act2:
            if st.button("✏️ Editar Conta", use_container_width=True):
                modal_editar_conta(int(row_sel["id"]))
        with act3:
            if st.button("🗑️ Excluir Lançamento", use_container_width=True):
                deletar(int(row_sel["id"]))
                st.warning("Removido.")
                st.rerun()
    else:
        st.info(f"Nenhum lançamento com o status '{st.session_state.status_filtro}'.")
else:
    st.info("Nenhuma conta registrada no banco de dados.")