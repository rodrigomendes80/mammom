import streamlit as st
import pandas as pd
from database.connection import execute_query

st.set_page_config(page_title="Beneficiários", page_icon="🏦", layout="wide")
st.title("🏦 Cadastro de Favorecido")

# ── FUNÇÕES ──────────────────────────────────────────────
def listar_beneficiarios():
    return execute_query(
        """SELECT id, nome, email, telefone, endereco, ativo
           FROM beneficiarios ORDER BY nome""",
        fetch=True
    )

def inserir_beneficiario(nome, email, telefone, endereco):
    execute_query(
        """INSERT INTO beneficiarios (nome, email, telefone, endereco)
           VALUES (%s, %s, %s, %s)""",
        (nome, email, telefone, endereco)
    )

def atualizar_beneficiario(id, nome, email, telefone, endereco, ativo):
    execute_query(
        """UPDATE beneficiarios
           SET nome=%s, email=%s, telefone=%s, endereco=%s, ativo=%s
           WHERE id=%s""",
        (nome, email, telefone, endereco, ativo, id)
    )

def deletar_beneficiario(id):
    execute_query("DELETE FROM beneficiarios WHERE id=%s", (id,))

# ── ABAS ─────────────────────────────────────────────────
aba1, aba2, aba3 = st.tabs(["📋 Listar Favorecido", "➕ Novo Favorecido", "✏️ Editar / Excluir"])

# ── ABA 1: LISTAR ────────────────────────────────────────
with aba1:
    beneficiarios = listar_beneficiarios()
    if beneficiarios:
        df = pd.DataFrame(beneficiarios)
        df.columns = ["ID", "Nome", "Email", "Telefone", "Endereço", "Ativo"]
        df["Ativo"] = df["Ativo"].map({True: "✅ Sim", False: "❌ Não"})
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Total: {len(df)} beneficiário(s) cadastrado(s)")
    else:
        st.info("Nenhum beneficiário cadastrado ainda.")

# ── ABA 2: NOVO BENEFICIÁRIO ─────────────────────────────
with aba2:
    st.subheader("Novo Favorecido")
    with st.form("form_novo_beneficiario", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome     = st.text_input("Nome completo *", placeholder="Ex: Empresa XYZ Ltda")
            email    = st.text_input("Email", placeholder="contato@empresa.com")
        with col2:
            telefone = st.text_input("Telefone", placeholder="(11) 99999-9999")
            endereco = st.text_area("Endereço", placeholder="Rua, número, bairro, cidade")

        submitted = st.form_submit_button("💾 Salvar Beneficiário", use_container_width=True)
        if submitted:
            if not nome:
                st.error("O campo Nome é obrigatório!")
            else:
                try:
                    inserir_beneficiario(nome, email, telefone, endereco)
                    st.success(f"✅ Beneficiário '{nome}' cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# ── ABA 3: EDITAR / EXCLUIR ──────────────────────────────
with aba3:
    beneficiarios = listar_beneficiarios()
    if not beneficiarios:
        st.info("Nenhum beneficiário cadastrado ainda.")
    else:
        opcoes  = {f"{b['id']} — {b['nome']}": b for b in beneficiarios}
        escolha = st.selectbox("Selecione o beneficiário", list(opcoes.keys()))
        b       = opcoes[escolha]

        with st.form("form_editar_beneficiario"):
            col1, col2 = st.columns(2)
            with col1:
                nome     = st.text_input("Nome *", value=b["nome"])
                email    = st.text_input("Email", value=b["email"] or "")
            with col2:
                telefone = st.text_input("Telefone", value=b["telefone"] or "")
                endereco = st.text_area("Endereço", value=b["endereco"] or "")
                ativo    = st.checkbox("Beneficiário ativo", value=b["ativo"] if b["ativo"] is not None else True)

            col_salvar, col_excluir = st.columns(2)
            with col_salvar:
                salvar  = st.form_submit_button("💾 Salvar alterações", use_container_width=True)
            with col_excluir:
                excluir = st.form_submit_button("🗑️ Excluir beneficiário", use_container_width=True)

        if salvar:
            atualizar_beneficiario(b["id"], nome, email, telefone, endereco, ativo)
            st.success("✅ Beneficiário atualizado com sucesso!")
            st.rerun()

        if excluir:
            deletar_beneficiario(b["id"])
            st.warning(f"🗑️ Beneficiário '{b['nome']}' excluído.")
            st.rerun()