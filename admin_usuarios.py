"""
Painel de administração de usuários.
Acessível apenas por usuários com role='admin'.
Execute com: streamlit run admin_usuarios.py --server.port 8502
"""
import streamlit as st
import pandas as pd
from auth import (
    login_required, is_admin, logout,
    listar_usuarios, criar_usuario, atualizar_usuario, excluir_usuario,
    listar_cidades_dados, _norm_cidade,
)

st.set_page_config(
    page_title="Admin — Usuários",
    page_icon="👥",
    layout="wide",
)

# ── Auth ──
usuario = login_required()
if not is_admin():
    st.error("⛔ Acesso restrito a administradores.")
    st.stop()

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# ── Header ──
col_h1, col_h2 = st.columns([7, 1])
with col_h1:
    st.markdown("## 👥 Gerenciar Usuários")
    st.caption(f"Logado como: **{usuario['nome']}** (admin)")
with col_h2:
    if st.button("🚪 Sair", use_container_width=True):
        logout()

st.markdown("---")

# ── Abas ──
aba_lista, aba_criar, aba_senha = st.tabs([
    "📋 Usuários",
    "➕ Criar Usuário",
    "🔑 Alterar Senha",
])

# ================================================================
# ABA 1 — Lista de usuários
# ================================================================
with aba_lista:
    usuarios = listar_usuarios()

    if not usuarios:
        st.info("Nenhum usuário cadastrado ainda.")
    else:
        total   = len(usuarios)
        admins  = sum(1 for u in usuarios if u["role"] == "admin")
        cidades = len({u["cidade"] for u in usuarios if u["cidade"]})
        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Usuários", total)
        m2.metric("Administradores",   admins)
        m3.metric("Cidades cobertas",  cidades)

        st.markdown("---")

        df_users = pd.DataFrame(usuarios)[["username", "nome", "cidade", "role", "criado_em"]]
        df_users.columns = ["Username", "Nome", "Cidade", "Perfil", "Criado em"]
        df_users["Cidade"]    = df_users["Cidade"].fillna("🌐 Todas")
        df_users["Perfil"]    = df_users["Perfil"].map({"admin": "🔑 Admin", "usuario": "👤 Usuário"})
        df_users["Criado em"] = pd.to_datetime(df_users["Criado em"], errors="coerce") \
                                   .dt.strftime("%d/%m/%Y %H:%M")
        st.dataframe(df_users, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### ✏️ Editar Usuário")

        cidades_dados = listar_cidades_dados()

        sel = st.selectbox(
            "Selecione o usuário para editar",
            [u["username"] for u in usuarios],
            format_func=lambda x: next(
                f"{chr(128273) if u['role']=='admin' else chr(128100)} {u['nome']} ({x})"
                for u in usuarios if u["username"] == x
            ),
            key="sel_editar",
        )
        u = next(u for u in usuarios if u["username"] == sel)

        with st.form("form_editar", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                novo_nome = st.text_input("Nome", value=u["nome"])
                novo_role = st.selectbox(
                    "Perfil",
                    ["usuario", "admin"],
                    index=0 if u["role"] == "usuario" else 1,
                )
            with col2:
                if cidades_dados:
                    opcoes_cidade = ["(outra)"] + cidades_dados
                    cidade_atual_idx = next(
                        (i + 1 for i, c in enumerate(cidades_dados)
                         if _norm_cidade(c) == _norm_cidade(u["cidade"] or "")),
                        0,
                    )
                    sel_cidade = st.selectbox(
                        "Cidade",
                        opcoes_cidade,
                        index=cidade_atual_idx,
                        disabled=(novo_role == "admin"),
                    )
                    if sel_cidade == "(outra)":
                        nova_cidade = st.text_input(
                            "Digite a cidade manualmente",
                            value=u["cidade"] or "",
                            disabled=(novo_role == "admin"),
                        )
                    else:
                        nova_cidade = sel_cidade
                else:
                    nova_cidade = st.text_input(
                        "Cidade (vazio = todas as cidades)",
                        value=u["cidade"] or "",
                        disabled=(novo_role == "admin"),
                    )

            col_s, col_d = st.columns(2)
            with col_s:
                salvar  = st.form_submit_button("💾 Salvar alterações",
                                                use_container_width=True, type="primary")
            with col_d:
                excluir = st.form_submit_button("🗑️ Excluir usuário",
                                                use_container_width=True)

        if salvar:
            cidade_val = nova_cidade.strip() or None
            if novo_role == "admin":
                cidade_val = None
            ok, msg = atualizar_usuario(u["id"], novo_nome, cidade_val, novo_role)
            st.success(msg) if ok else st.error(msg)
            if ok:
                st.rerun()

        if excluir:
            ok, msg = excluir_usuario(u["id"])
            st.success(msg) if ok else st.error(msg)
            if ok:
                st.rerun()

# ================================================================
# ABA 2 — Criar Usuário
# ================================================================
with aba_criar:
    st.markdown("### ➕ Novo Usuário")
    cidades_dados_c = listar_cidades_dados()

    with st.form("form_criar", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n_username = st.text_input("Username *", placeholder="joao.silva",
                                       help="Letras, números, ponto e underscore")
            n_nome     = st.text_input("Nome completo *", placeholder="João Silva")
        with col2:
            n_role = st.selectbox("Perfil *", ["usuario", "admin"])
            if cidades_dados_c:
                opcoes_c = ["(outra)"] + cidades_dados_c
                sel_nc   = st.selectbox("Cidade *", opcoes_c,
                                        disabled=(n_role == "admin"))
                if sel_nc == "(outra)":
                    n_cidade = st.text_input("Digite a cidade", placeholder="Ex: São Paulo",
                                             disabled=(n_role == "admin"))
                else:
                    n_cidade = "" if n_role == "admin" else sel_nc
            else:
                n_cidade = st.text_input(
                    "Cidade",
                    placeholder="Ex: São Paulo (deixe vazio para admin)",
                    disabled=(n_role == "admin"),
                )

        n_senha    = st.text_input("Senha *", type="password",
                                   placeholder="Mínimo 6 caracteres")
        n_confirma = st.text_input("Confirmar senha *", type="password")

        submitted = st.form_submit_button("✅ Criar Usuário",
                                          use_container_width=True, type="primary")

    if submitted:
        if n_senha != n_confirma:
            st.error("❌ As senhas não coincidem.")
        elif len(n_senha) < 6:
            st.error("❌ A senha deve ter pelo menos 6 caracteres.")
        else:
            cidade_val = n_cidade.strip() if n_cidade.strip() and n_role != "admin" else None
            ok, msg = criar_usuario(n_username, n_nome, n_senha, cidade_val, n_role)
            st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")
            if ok:
                st.rerun()

# ================================================================
# ABA 3 — Alterar Senha
# ================================================================
with aba_senha:
    st.markdown("### 🔑 Alterar Senha de Usuário")
    st.caption("O admin pode redefinir a senha de qualquer usuário sem precisar da senha atual.")

    usuarios_s = listar_usuarios()
    if not usuarios_s:
        st.info("Nenhum usuário cadastrado.")
    else:
        sel_s = st.selectbox(
            "Selecione o usuário",
            [u["username"] for u in usuarios_s],
            format_func=lambda x: next(
                f"{chr(128273) if u['role']=='admin' else chr(128100)} {u['nome']} ({x})"
                for u in usuarios_s if u["username"] == x
            ),
            key="sel_senha",
        )
        u_s = next(u for u in usuarios_s if u["username"] == sel_s)

        with st.form("form_senha_admin", clear_on_submit=True):
            st.markdown(f"**Usuário:** {u_s['nome']} (`{u_s['username']}`)")
            if u_s["cidade"]:
                st.caption(f"🏙️ Cidade: {u_s['cidade']}")
            nova_s     = st.text_input("Nova senha *", type="password",
                                       placeholder="Mínimo 6 caracteres")
            confirma_s = st.text_input("Confirmar nova senha *", type="password")
            btn_s = st.form_submit_button("🔑 Redefinir Senha",
                                          use_container_width=True, type="primary")

        if btn_s:
            if not nova_s or not confirma_s:
                st.error("❌ Preencha os dois campos de senha.")
            elif nova_s != confirma_s:
                st.error("❌ As senhas não coincidem.")
            elif len(nova_s) < 6:
                st.error("❌ A senha deve ter pelo menos 6 caracteres.")
            else:
                ok, msg = atualizar_usuario(u_s["id"], u_s["nome"], u_s["cidade"], u_s["role"], nova_s)
                if ok:
                    st.success(f"✅ Senha de **{u_s['nome']}** redefinida com sucesso.")
                else:
                    st.error(msg)

st.markdown("---")
st.caption(
    "Novos usuários também podem se auto-cadastrar no app principal — aba Criar Conta. "
    "O admin pode editar perfil, cidade e senha por aqui."
)
