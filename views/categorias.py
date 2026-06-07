import streamlit as st
import pandas as pd
from database.connection import execute_query

st.title("🏷️ Cadastro de Categorias")

def listar():
    return execute_query(
        "SELECT id, descricao, tipo, ativo FROM categorias ORDER BY tipo, descricao",
        fetch=True
    )

def inserir(descricao, tipo):
    execute_query(
        "INSERT INTO categorias (descricao, tipo) VALUES (%s, %s)",
        (descricao, tipo)
    )

def atualizar(id, descricao, tipo, ativo):
    execute_query(
        "UPDATE categorias SET descricao=%s, tipo=%s, ativo=%s WHERE id=%s",
        (descricao, tipo, ativo, id)
    )

def deletar(id):
    execute_query("DELETE FROM categorias WHERE id=%s", (id,))

TIPOS = ["pagar", "receber"]

# Métricas
cats = listar()
if cats:
    df_m = pd.DataFrame(cats)
    c1, c2 = st.columns(2)
    c1.metric("💸 Categorias de Pagar",   len(df_m[df_m["tipo"]=="pagar"]))
    c2.metric("💰 Categorias de Receber", len(df_m[df_m["tipo"]=="receber"]))
    st.markdown("---")

aba1, aba2, aba3 = st.tabs(["📋 Listar", "➕ Nova Categoria", "✏️ Editar / Excluir"])

with aba1:
    cats = listar()
    if cats:
        df = pd.DataFrame(cats)
        df.columns = ["ID", "Descrição", "Tipo", "Ativo"]
        df["Tipo"]  = df["Tipo"].map({"pagar": "💸 Pagar", "receber": "💰 Receber"})
        df["Ativo"] = df["Ativo"].map({True: "✅ Sim", False: "❌ Não"})
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma categoria cadastrada.")

with aba2:
    with st.form("form_cat", clear_on_submit=True):
        descricao = st.text_input("Descrição *", placeholder="Ex: Aluguel, Vendas, Impostos")
        tipo      = st.selectbox("Tipo *", TIPOS,
                       format_func=lambda x: "💸 Contas a Pagar" if x=="pagar" else "💰 Contas a Receber")
        submitted = st.form_submit_button("💾 Salvar Categoria", use_container_width=True)
    if submitted:
        if not descricao:
            st.error("Descrição é obrigatória!")
        else:
            try:
                inserir(descricao, tipo)
                st.success(f"✅ Categoria '{descricao}' criada!")
            except Exception as e:
                st.error(f"Erro: {e}")

with aba3:
    cats = listar()
    if not cats:
        st.info("Nenhuma categoria ainda.")
    else:
        opc     = {f"{c['id']} — {c['descricao']} ({c['tipo']})": c for c in cats}
        escolha = st.selectbox("Selecione", list(opc.keys()))
        c       = opc[escolha]
        with st.form("form_edit_cat"):
            descricao = st.text_input("Descrição *", value=c["descricao"])
            tipo      = st.selectbox("Tipo", TIPOS,
                           index=TIPOS.index(c["tipo"]) if c["tipo"] in TIPOS else 0,
                           format_func=lambda x: "💸 Contas a Pagar" if x=="pagar" else "💰 Contas a Receber")
            ativo     = st.checkbox("Ativa", value=c["ativo"])
            col1, col2 = st.columns(2)
            with col1:
                salvar  = st.form_submit_button("💾 Salvar", use_container_width=True)
            with col2:
                excluir = st.form_submit_button("🗑️ Excluir", use_container_width=True)
        if salvar:
            atualizar(c["id"], descricao, tipo, ativo)
            st.success("✅ Categoria atualizada!")
            st.rerun()
        if excluir:
            deletar(c["id"])
            st.warning("🗑️ Excluída.")
            st.rerun()