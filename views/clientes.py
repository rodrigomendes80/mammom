import streamlit as st
import pandas as pd
from database.connection import execute_query

st.set_page_config(page_title="Clientes", page_icon="👥", layout="wide")
st.title("👥 Cadastro de Clientes")

# ── CONSTANTES ───────────────────────────────────────────
TIPOS_CONTRATO = ["Mensal", "Trimestral", "Semestral", "Anual", "Avulso", "Outros"]

# ── FUNÇÕES ──────────────────────────────────────────────
def listar_clientes():
    return execute_query(
        """SELECT id, nome, cpf_cnpj, email, telefone, tipo_contrato, valor, ativo
           FROM clientes ORDER BY nome""",
        fetch=True
    )

def inserir_cliente(nome, cpf_cnpj, email, telefone, endereco, tipo_contrato, valor):
    execute_query(
        """INSERT INTO clientes (nome, cpf_cnpj, email, telefone, endereco, tipo_contrato, valor)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (nome, cpf_cnpj, email, telefone, endereco, tipo_contrato, valor)
    )

def atualizar_cliente(id, nome, cpf_cnpj, email, telefone, endereco, tipo_contrato, valor, ativo):
    execute_query(
        """UPDATE clientes SET nome=%s, cpf_cnpj=%s, email=%s,
           telefone=%s, endereco=%s, tipo_contrato=%s, valor=%s, ativo=%s
           WHERE id=%s""",
        (nome, cpf_cnpj, email, telefone, endereco, tipo_contrato, valor, ativo, id)
    )

def deletar_cliente(id):
    execute_query("DELETE FROM clientes WHERE id=%s", (id,))

# ── ABAS ─────────────────────────────────────────────────
aba1, aba2, aba3 = st.tabs(["📋 Listar Clientes", "➕ Novo Cliente", "✏️ Editar / Excluir"])

# ── ABA 1: LISTAR ────────────────────────────────────────
with aba1:
    clientes = listar_clientes()
    if clientes:
        df = pd.DataFrame(clientes)
        df.columns = ["ID", "Nome", "CPF/CNPJ", "Email", "Telefone", "Tipo Contrato", "Valor (R$)", "Ativo"]
        df["Ativo"] = df["Ativo"].map({True: "✅ Sim", False: "❌ Não"})
        df["Valor (R$)"] = df["Valor (R$)"].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if x else "—"
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Total: {len(df)} cliente(s) cadastrado(s)")
    else:
        st.info("Nenhum cliente cadastrado ainda.")

# ── ABA 2: NOVO CLIENTE ──────────────────────────────────
with aba2:
    st.subheader("Novo Cliente")
    with st.form("form_novo_cliente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome          = st.text_input("Nome completo *", placeholder="Ex: João Silva")
            email         = st.text_input("Email", placeholder="joao@email.com")
            telefone      = st.text_input("Telefone", placeholder="(11) 99999-9999")
            tipo_contrato = st.selectbox("Tipo de Contrato", TIPOS_CONTRATO)
        with col2:
            cpf_cnpj = st.text_input("CPF / CNPJ", placeholder="000.000.000-00")
            endereco = st.text_area("Endereço", placeholder="Rua, número, bairro, cidade")
            valor    = st.number_input(
                "Valor do Contrato (R$)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                help="Informe o valor mensal ou total conforme o tipo de contrato"
            )

        submitted = st.form_submit_button("💾 Salvar Cliente", use_container_width=True)
        if submitted:
            if not nome:
                st.error("O campo Nome é obrigatório!")
            else:
                try:
                    inserir_cliente(nome, cpf_cnpj, email, telefone, endereco, tipo_contrato, valor)
                    st.success(f"✅ Cliente '{nome}' cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# ── ABA 3: EDITAR / EXCLUIR ──────────────────────────────
with aba3:
    clientes = listar_clientes()
    if not clientes:
        st.info("Nenhum cliente cadastrado ainda.")
    else:
        opcoes  = {f"{c['id']} — {c['nome']}": c for c in clientes}
        escolha = st.selectbox("Selecione o cliente", list(opcoes.keys()))
        c       = opcoes[escolha]

        with st.form("form_editar_cliente"):
            col1, col2 = st.columns(2)
            with col1:
                nome     = st.text_input("Nome *", value=c["nome"])
                email    = st.text_input("Email", value=c["email"] or "")
                telefone = st.text_input("Telefone", value=c["telefone"] or "")
                tipo_contrato = st.selectbox(
                    "Tipo de Contrato",
                    TIPOS_CONTRATO,
                    index=TIPOS_CONTRATO.index(c["tipo_contrato"]) if c["tipo_contrato"] in TIPOS_CONTRATO else 0
                )
            with col2:
                cpf_cnpj = st.text_input("CPF / CNPJ", value=c["cpf_cnpj"] or "")
                endereco = st.text_area("Endereço")
                valor    = st.number_input(
                    "Valor do Contrato (R$)",
                    min_value=0.0,
                    value=float(c["valor"]) if c["valor"] else 0.0,
                    step=0.01,
                    format="%.2f"
                )
                ativo = st.checkbox("Cliente ativo", value=c["ativo"])

            col_salvar, col_excluir = st.columns(2)
            with col_salvar:
                salvar  = st.form_submit_button("💾 Salvar alterações", use_container_width=True)
            with col_excluir:
                excluir = st.form_submit_button("🗑️ Excluir cliente", use_container_width=True)

        if salvar:
            atualizar_cliente(c["id"], nome, cpf_cnpj, email, telefone, endereco, tipo_contrato, valor, ativo)
            st.success("✅ Cliente atualizado com sucesso!")
            st.rerun()

        if excluir:
            deletar_cliente(c["id"])
            st.warning(f"🗑️ Cliente '{c['nome']}' excluído.")
            st.rerun()