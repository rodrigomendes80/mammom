import streamlit as st
import pandas as pd
from database.connection import execute_query
from datetime import date

st.title("🏦 Contas Bancárias")

# ── FUNÇÕES DE SUPORTE ───────────────────────────────────
def fmt(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def listar_contas_bancarias():
    return execute_query(
        "SELECT id, nome, banco, saldo_inicial, ativo FROM contas_bancarias ORDER BY nome",
        fetch=True
    )

def inserir_conta_bancaria(nome, banco, saldo):
    execute_query(
        "INSERT INTO contas_bancarias (nome, banco, saldo_inicial) VALUES (%s, %s, %s)",
        (nome, banco, saldo)
    )

def atualizar_conta_bancaria(id, nome, banco, saldo, ativo):
    execute_query(
        "UPDATE contas_bancarias SET nome=%s, banco=%s, saldo_inicial=%s, ativo=%s WHERE id=%s",
        (nome, banco, saldo, ativo, id)
    )

def deletar_conta(id):
    execute_query("DELETE FROM contas_bancarias WHERE id=%s", (id,))

# ── ABAS ─────────────────────────────────────────────────
aba1, aba2, aba3 = st.tabs(["📋 Listar", "➕ Nova", "✏️ Editar/Excluir"])

# ── ABA 1: LISTAR ────────────────────────────────────────
with aba1:
    contas = listar_contas_bancarias()
if contas:
    df = pd.DataFrame(contas)
    df.columns = ["ID", "Nome", "Banco", "Saldo Inicial", "Ativo"]
    df["Saldo Inicial"] = df["Saldo Inicial"].apply(fmt)
    df["Ativo"] = df["Ativo"].apply(lambda x: "✅" if x else "❌")
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Nenhuma conta cadastrada.")

# ── ABA 2: NOVA CONTA BANCÁRIA ───────────────────────────
with aba2:
    with st.form("form_nova_conta_bancaria", clear_on_submit=True):
    nome = st.text_input("Nome da conta *", placeholder="Ex: Conta Principal, Caixa")
    banco = st.text_input("Banco *", placeholder="Ex: Nubank, Itaú, Bradesco")
    saldo_inicial = st.text_input("Saldo inicial (R$)", placeholder="0,00")

    submitted = st.form_submit_button("💾 Salvar Conta Bancária", use_container_width=True)

if submitted:
    if not nome or not banco:
        st.error("Nome e Banco são obrigatórios!")
    else:
        try:
            saldo = float(saldo_inicial.replace(".", "").replace(",", ".")) if saldo_inicial else 0.0
            inserir_conta_bancaria(nome, banco, saldo)
            st.success(f"✅ Conta '{nome}' cadastrada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# ── ABA 3: EDITAR / EXCLUIR ──────────────────────────────
with aba3:
   contas = listar_contas_bancarias()
if contas:
    opcoes = {c['nome']: c for c in contas}
    escolha = st.selectbox("Selecione a conta", list(opcoes.keys()))
    c = opcoes[escolha]

    with st.form("edit_conta_bancaria"):
        nome = st.text_input("Nome", value=c['nome'])
        banco = st.text_input("Banco", value=c['banco'] or "")
        saldo = st.text_input("Saldo inicial", value=str(c['saldo_inicial']).replace(".", ","))
        ativo = st.checkbox("Ativo", value=c['ativo'] if c['ativo'] is not None else True)

        col_s, col_e = st.columns(2)
        if col_s.form_submit_button("💾 Salvar"):
            s_float = float(saldo.replace(".", "").replace(",", "."))
            atualizar_conta_bancaria(c['id'], nome, banco, s_float, ativo)
            st.success("Atualizado!")
            st.rerun()
        if col_e.form_submit_button("🗑️ Excluir"):
            execute_query("DELETE FROM contas_bancarias WHERE id=%s", (c['id'],))
            st.warning("Excluído!")
            st.rerun()
else:
    st.info("Nenhuma conta cadastrada.")