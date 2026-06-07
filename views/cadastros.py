import streamlit as st
import pandas as pd
from database.connection import execute_query

# ── CSS DAS ABAS SUPERIORES ───────────────────────────────
st.markdown("""
<style>
    div[data-testid="stTabs"] button {
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #64748b !important;
        padding: 8px 20px !important;
        border-radius: 0 !important;
        background: transparent !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #2563eb !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #2563eb !important;
    }
    div[data-testid="stTabs"] button:hover {
        color: #1e40af !important;
        background: transparent !important;
    }
    div[data-testid="stTabsContent"] {
        padding-top: 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='margin-bottom:0.5rem;'>Cadastros</h1>", unsafe_allow_html=True)

# ── CONSTANTES ────────────────────────────────────────────
TIPOS_CONTRATO = ["Mensal", "Trimestral", "Semestral", "Anual", "Avulso", "Outros"]
TIPOS_CAT      = ["pagar", "receber"]

def fmt_brl(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except:
        return "R$ 0,00"

# ════════════════════════════════════════════════════════════
# FUNÇÕES — CLIENTES
# ════════════════════════════════════════════════════════════
def listar_clientes():
    return execute_query(
        "SELECT id, nome, cpf_cnpj, email, telefone, tipo_contrato, valor, ativo FROM clientes ORDER BY nome",
        fetch=True)

def inserir_cliente(nome, cpf_cnpj, email, telefone, endereco, tipo_contrato, valor):
    execute_query(
        "INSERT INTO clientes (nome,cpf_cnpj,email,telefone,endereco,tipo_contrato,valor) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (nome, cpf_cnpj, email, telefone, endereco, tipo_contrato, valor))

def atualizar_cliente(id, nome, cpf_cnpj, email, telefone, endereco, tipo_contrato, valor, ativo):
    execute_query(
        "UPDATE clientes SET nome=%s,cpf_cnpj=%s,email=%s,telefone=%s,endereco=%s,tipo_contrato=%s,valor=%s,ativo=%s WHERE id=%s",
        (nome, cpf_cnpj, email, telefone, endereco, tipo_contrato, valor, ativo, id))

def deletar_cliente(id):
    execute_query("DELETE FROM clientes WHERE id=%s", (id,))

# ════════════════════════════════════════════════════════════
# FUNÇÕES — FAVORECIDOS
# ════════════════════════════════════════════════════════════
def listar_beneficiarios():
    return execute_query(
        "SELECT id, nome, email, telefone, endereco, ativo FROM beneficiarios ORDER BY nome",
        fetch=True)

def inserir_beneficiario(nome, email, telefone, endereco):
    execute_query(
        "INSERT INTO beneficiarios (nome,email,telefone,endereco) VALUES (%s,%s,%s,%s)",
        (nome, email, telefone, endereco))

def atualizar_beneficiario(id, nome, email, telefone, endereco, ativo):
    execute_query(
        "UPDATE beneficiarios SET nome=%s,email=%s,telefone=%s,endereco=%s,ativo=%s WHERE id=%s",
        (nome, email, telefone, endereco, ativo, id))

def deletar_beneficiario(id):
    execute_query("DELETE FROM beneficiarios WHERE id=%s", (id,))

# ════════════════════════════════════════════════════════════
# FUNÇÕES — CATEGORIAS
# ════════════════════════════════════════════════════════════
def listar_categorias():
    return execute_query(
        "SELECT id, descricao, tipo, ativo FROM categorias ORDER BY tipo, descricao",
        fetch=True)

def inserir_categoria(descricao, tipo):
    execute_query("INSERT INTO categorias (descricao,tipo) VALUES (%s,%s)", (descricao, tipo))

def atualizar_categoria(id, descricao, tipo, ativo):
    execute_query("UPDATE categorias SET descricao=%s,tipo=%s,ativo=%s WHERE id=%s", (descricao, tipo, ativo, id))

def deletar_categoria(id):
    execute_query("DELETE FROM categorias WHERE id=%s", (id,))

# ════════════════════════════════════════════════════════════
# FUNÇÕES — CONTAS BANCÁRIAS  ✅ CORRIGIDAS
# ════════════════════════════════════════════════════════════
def listar_contas_bancarias():
    return execute_query(
        "SELECT id, nome, banco, saldo_inicial, ativo FROM contas_bancarias ORDER BY nome",
        fetch=True)

def inserir_conta_bancaria(nome, banco, saldo_inicial):
    execute_query(
        "INSERT INTO contas_bancarias (nome, banco, saldo_inicial) VALUES (%s, %s, %s)",
        (nome, banco, saldo_inicial))

def atualizar_conta_bancaria(id, nome, banco, saldo_inicial, ativo):
    execute_query(
        "UPDATE contas_bancarias SET nome=%s, banco=%s, saldo_inicial=%s, ativo=%s WHERE id=%s",
        (nome, banco, saldo_inicial, ativo, id))

def deletar_conta_bancaria(id):
    execute_query("DELETE FROM contas_bancarias WHERE id=%s", (id,))


# ════════════════════════════════════════════════════════════
# ABAS PRINCIPAIS
# ════════════════════════════════════════════════════════════
tab_cli, tab_fav, tab_cat, tab_ban = st.tabs([
    "Clientes", "Favorecidos", "Categorias", "Bancos"
])


# ╔══════════════════════════════════════════════════════════╗
# ║  ABA — CLIENTES                                         ║
# ╚══════════════════════════════════════════════════════════╝
with tab_cli:
    sub1, sub2, sub3 = st.tabs(["📋 Listar", "➕ Novo Cliente", "✏️ Editar / Excluir"])

    with sub1:
        clientes = listar_clientes()
        if clientes:
            df = pd.DataFrame(clientes)
            df.columns = ["ID","Nome","CPF/CNPJ","Email","Telefone","Tipo Contrato","Valor (R$)","Ativo"]
            df["Ativo"]      = df["Ativo"].map({True:"✅ Sim", False:"❌ Não"})
            df["Valor (R$)"] = df["Valor (R$)"].apply(lambda x: fmt_brl(x) if x else "—")
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Total: {len(df)} cliente(s)")
        else:
            st.info("Nenhum cliente cadastrado.")

    with sub2:
        with st.form("form_novo_cliente", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome          = st.text_input("Nome *", placeholder="Ex: João Silva")
                email         = st.text_input("Email", placeholder="joao@email.com")
                telefone      = st.text_input("Telefone", placeholder="(11) 99999-9999")
                tipo_contrato = st.selectbox("Tipo de Contrato", TIPOS_CONTRATO)
            with col2:
                cpf_cnpj = st.text_input("CPF / CNPJ", placeholder="000.000.000-00")
                endereco = st.text_area("Endereço", placeholder="Rua, número, bairro")
                valor    = st.number_input("Valor do Contrato (R$)", min_value=0.0, step=0.01, format="%.2f")
            if st.form_submit_button("💾 Salvar Cliente", use_container_width=True):
                if not nome:
                    st.error("Nome é obrigatório!")
                else:
                    try:
                        inserir_cliente(nome, cpf_cnpj, email, telefone, endereco, tipo_contrato, valor)
                        st.success(f"✅ Cliente '{nome}' cadastrado!")
                    except Exception as e:
                        st.error(f"Erro: {e}")

    with sub3:
        clientes = listar_clientes()
        if not clientes:
            st.info("Nenhum cliente cadastrado.")
        else:
            opc     = {f"{c['id']} — {c['nome']}": c for c in clientes}
            escolha = st.selectbox("Selecione o cliente", list(opc.keys()), key="sel_cli")
            c       = opc[escolha]
            with st.form("form_editar_cliente"):
                col1, col2 = st.columns(2)
                with col1:
                    nome     = st.text_input("Nome *", value=c["nome"])
                    email    = st.text_input("Email", value=c["email"] or "")
                    telefone = st.text_input("Telefone", value=c["telefone"] or "")
                    tipo_contrato = st.selectbox("Tipo de Contrato", TIPOS_CONTRATO,
                        index=TIPOS_CONTRATO.index(c["tipo_contrato"]) if c["tipo_contrato"] in TIPOS_CONTRATO else 0)
                with col2:
                    cpf_cnpj = st.text_input("CPF / CNPJ", value=c["cpf_cnpj"] or "")
                    endereco = st.text_area("Endereço")
                    valor    = st.number_input("Valor (R$)", min_value=0.0,
                                value=float(c["valor"]) if c["valor"] else 0.0, step=0.01, format="%.2f")
                    ativo    = st.checkbox("Cliente ativo", value=c["ativo"])
                cs, ce = st.columns(2)
                with cs: salvar  = st.form_submit_button("💾 Salvar", use_container_width=True)
                with ce: excluir = st.form_submit_button("🗑️ Excluir", use_container_width=True)
            if salvar:
                atualizar_cliente(c["id"], nome, cpf_cnpj, email, telefone, endereco, tipo_contrato, valor, ativo)
                st.success("✅ Cliente atualizado!")
                st.rerun()
            if excluir:
                deletar_cliente(c["id"])
                st.warning(f"🗑️ '{c['nome']}' excluído.")
                st.rerun()


# ╔══════════════════════════════════════════════════════════╗
# ║  ABA — FAVORECIDOS                                      ║
# ╚══════════════════════════════════════════════════════════╝
with tab_fav:
    sub1, sub2, sub3 = st.tabs(["📋 Listar", "➕ Novo Favorecido", "✏️ Editar / Excluir"])

    with sub1:
        favs = listar_beneficiarios()
        if favs:
            df = pd.DataFrame(favs)
            df.columns = ["ID","Nome","Email","Telefone","Endereço","Ativo"]
            df["Ativo"] = df["Ativo"].map({True:"✅ Sim", False:"❌ Não"})
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Total: {len(df)} favorecido(s)")
        else:
            st.info("Nenhum favorecido cadastrado.")

    with sub2:
        with st.form("form_novo_fav", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome     = st.text_input("Nome *", placeholder="Ex: Empresa XYZ Ltda")
                email    = st.text_input("Email", placeholder="contato@empresa.com")
            with col2:
                telefone = st.text_input("Telefone", placeholder="(11) 99999-9999")
                endereco = st.text_area("Endereço", placeholder="Rua, número, bairro")
            if st.form_submit_button("💾 Salvar Favorecido", use_container_width=True):
                if not nome:
                    st.error("Nome é obrigatório!")
                else:
                    try:
                        inserir_beneficiario(nome, email, telefone, endereco)
                        st.success(f"✅ Favorecido '{nome}' cadastrado!")
                    except Exception as e:
                        st.error(f"Erro: {e}")

    with sub3:
        favs = listar_beneficiarios()
        if not favs:
            st.info("Nenhum favorecido cadastrado.")
        else:
            opc     = {f"{b['id']} — {b['nome']}": b for b in favs}
            escolha = st.selectbox("Selecione o favorecido", list(opc.keys()), key="sel_fav")
            b       = opc[escolha]
            with st.form("form_editar_fav"):
                col1, col2 = st.columns(2)
                with col1:
                    nome     = st.text_input("Nome *", value=b["nome"])
                    email    = st.text_input("Email", value=b["email"] or "")
                with col2:
                    telefone = st.text_input("Telefone", value=b["telefone"] or "")
                    endereco = st.text_area("Endereço", value=b["endereco"] or "")
                    ativo    = st.checkbox("Favorecido ativo", value=b["ativo"] if b["ativo"] is not None else True)
                cs, ce = st.columns(2)
                with cs: salvar  = st.form_submit_button("💾 Salvar", use_container_width=True)
                with ce: excluir = st.form_submit_button("🗑️ Excluir", use_container_width=True)
            if salvar:
                atualizar_beneficiario(b["id"], nome, email, telefone, endereco, ativo)
                st.success("✅ Favorecido atualizado!")
                st.rerun()
            if excluir:
                deletar_beneficiario(b["id"])
                st.warning(f"🗑️ '{b['nome']}' excluído.")
                st.rerun()


# ╔══════════════════════════════════════════════════════════╗
# ║  ABA — CATEGORIAS                                       ║
# ╚══════════════════════════════════════════════════════════╝
with tab_cat:
    sub1, sub2, sub3 = st.tabs(["📋 Listar", "➕ Nova Categoria", "✏️ Editar / Excluir"])

    with sub1:
        cats = listar_categorias()
        if cats:
            df = pd.DataFrame(cats)
            df.columns = ["ID","Descrição","Tipo","Ativo"]
            df["Tipo"]  = df["Tipo"].map({"pagar":"💸 Pagar","receber":"💰 Receber"})
            df["Ativo"] = df["Ativo"].map({True:"✅ Sim", False:"❌ Não"})
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Total: {len(df)} categoria(s)")
        else:
            st.info("Nenhuma categoria cadastrada.")

    with sub2:
        with st.form("form_nova_cat", clear_on_submit=True):
            descricao = st.text_input("Descrição *", placeholder="Ex: Aluguel, Vendas")
            tipo      = st.selectbox("Tipo *", TIPOS_CAT,
                            format_func=lambda x: "💸 Contas a Pagar" if x=="pagar" else "💰 Contas a Receber")
            if st.form_submit_button("💾 Salvar Categoria", use_container_width=True):
                if not descricao:
                    st.error("Descrição é obrigatória!")
                else:
                    try:
                        inserir_categoria(descricao, tipo)
                        st.success(f"✅ Categoria '{descricao}' criada!")
                    except Exception as e:
                        st.error(f"Erro: {e}")

    with sub3:
        cats = listar_categorias()
        if not cats:
            st.info("Nenhuma categoria ainda.")
        else:
            opc     = {f"{c['id']} — {c['descricao']} ({c['tipo']})": c for c in cats}
            escolha = st.selectbox("Selecione", list(opc.keys()), key="sel_cat")
            c       = opc[escolha]
            with st.form("form_editar_cat"):
                descricao = st.text_input("Descrição *", value=c["descricao"])
                tipo      = st.selectbox("Tipo", TIPOS_CAT,
                                index=TIPOS_CAT.index(c["tipo"]) if c["tipo"] in TIPOS_CAT else 0,
                                format_func=lambda x: "💸 Contas a Pagar" if x=="pagar" else "💰 Contas a Receber")
                ativo     = st.checkbox("Ativa", value=c["ativo"])
                cs, ce = st.columns(2)
                with cs: salvar  = st.form_submit_button("💾 Salvar", use_container_width=True)
                with ce: excluir = st.form_submit_button("🗑️ Excluir", use_container_width=True)
            if salvar:
                atualizar_categoria(c["id"], descricao, tipo, ativo)
                st.success("✅ Categoria atualizada!")
                st.rerun()
            if excluir:
                deletar_categoria(c["id"])
                st.warning("🗑️ Excluída.")
                st.rerun()


# ╔══════════════════════════════════════════════════════════╗
# ║  ABA — BANCOS  ✅ CORRIGIDA                             ║
# ╚══════════════════════════════════════════════════════════╝
with tab_ban:
    sub1, sub2, sub3 = st.tabs(["📋 Listar", "➕ Nova Conta", "✏️ Editar / Excluir"])

    with sub1:
        contas = listar_contas_bancarias()
        if contas:
            df = pd.DataFrame(contas)
            df.columns = ["ID", "Nome", "Banco", "Saldo Inicial", "Ativo"]
            df["Ativo"]         = df["Ativo"].map({True:"✅ Sim", False:"❌ Não"})
            df["Saldo Inicial"] = df["Saldo Inicial"].apply(fmt_brl)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Total: {len(df)} conta(s)")
        else:
            st.info("Nenhuma conta bancária cadastrada.")

    with sub2:
        with st.form("form_nova_conta", clear_on_submit=True):
            nome          = st.text_input("Nome da conta *", placeholder="Ex: Conta Principal")
            banco         = st.text_input("Banco *", placeholder="Ex: Itaú, Nubank")
            saldo_inicial = st.text_input("Saldo inicial (R$)", placeholder="0,00")
            if st.form_submit_button("💾 Salvar Conta", use_container_width=True):
                if not nome or not banco:
                    st.error("Nome e Banco são obrigatórios!")
                else:
                    try:
                        saldo = float(saldo_inicial.replace(".","").replace(",",".")) if saldo_inicial else 0.0
                        inserir_conta_bancaria(nome, banco, saldo)
                        st.success(f"✅ Conta '{nome}' cadastrada!")
                    except Exception as e:
                        st.error(f"Erro: {e}")

    with sub3:
        contas = listar_contas_bancarias()
        if not contas:
            st.info("Nenhuma conta bancária cadastrada.")
        else:
            opc     = {f"{c['id']} — {c['nome']} | {c['banco']}": c for c in contas}
            escolha = st.selectbox("Selecione a conta", list(opc.keys()), key="sel_ban")
            c       = opc[escolha]
            with st.form("form_editar_conta"):
                nome  = st.text_input("Nome *", value=c["nome"])
                banco = st.text_input("Banco *", value=c["banco"])
                saldo_str = st.text_input("Saldo inicial (R$)",
                                value=str(c["saldo_inicial"]).replace(".",",") if c["saldo_inicial"] else "0,00")
                ativo = st.checkbox("Conta ativa", value=c["ativo"] if c["ativo"] is not None else True)
                cs, ce = st.columns(2)
                with cs: salvar  = st.form_submit_button("💾 Salvar", use_container_width=True)
                with ce: excluir = st.form_submit_button("🗑️ Excluir", use_container_width=True)
            if salvar:
                try:
                    saldo = float(saldo_str.replace(".","").replace(",",".")) if saldo_str else 0.0
                    atualizar_conta_bancaria(c["id"], nome, banco, saldo, ativo)
                    st.success("✅ Conta atualizada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
            if excluir:
                deletar_conta_bancaria(c["id"])
                st.warning(f"🗑️ '{c['nome']}' excluída.")
                st.rerun()