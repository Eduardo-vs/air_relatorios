"""
Pagina: Autenticacao
Login, registro por convite e gerenciamento de usuarios
"""

import streamlit as st
from utils import data_manager
import hashlib
import base64


def gerar_token_sessao(email: str, senha_hash: str) -> str:
    """Gera token de sessao baseado no email e hash da senha"""
    dados = f"{email}:{senha_hash}:air_2024_secret"
    return hashlib.sha256(dados.encode()).hexdigest()


def gerar_token_url(email: str, senha_hash: str) -> str:
    """Gera token para URL/localStorage"""
    token = gerar_token_sessao(email, senha_hash)
    dados = f"{email}|{token}"
    return base64.b64encode(dados.encode()).decode('utf-8')


def verificar_login_salvo():
    """Verifica se existe login salvo via query params"""
    if st.session_state.get('autenticado'):
        return True
    
    # Verificar token na URL (via query params)
    token_param = st.query_params.get('auth_token')
    
    if token_param:
        try:
            # Decodificar token base64
            dados = base64.b64decode(token_param).decode('utf-8')
            partes = dados.split('|')
            
            if len(partes) >= 2:
                email = partes[0]
                token_hash = partes[1]
                
                # Buscar usuario
                usuario = data_manager.get_usuario_por_email(email)
                
                if usuario:
                    # Verificar token
                    token_esperado = gerar_token_sessao(email, usuario.get('senha_hash', ''))
                    
                    if token_hash == token_esperado:
                        st.session_state.usuario_logado = usuario
                        st.session_state.autenticado = True
                        return True
        except:
            pass
    
    return False


def injetar_script_login(token: str):
    """Injeta JavaScript para salvar token no localStorage e atualizar URL"""
    js_code = f"""
    <script>
        localStorage.setItem('air_auth_token', '{token}');
        const url = new URL(window.location.href);
        url.searchParams.set('auth_token', '{token}');
        window.history.replaceState({{}}, '', url.toString());
    </script>
    """
    st.components.v1.html(js_code, height=0)


def injetar_script_verificar_login():
    """Injeta JavaScript para verificar localStorage e redirecionar se tiver token"""
    js_code = """
    <script>
        (function() {
            const urlParams = new URLSearchParams(window.location.search);
            const tokenUrl = urlParams.get('auth_token');
            
            if (!tokenUrl) {
                const tokenLocal = localStorage.getItem('air_auth_token');
                
                if (tokenLocal) {
                    const url = new URL(window.location.href);
                    url.searchParams.set('auth_token', tokenLocal);
                    window.location.href = url.toString();
                }
            }
        })();
    </script>
    """
    st.components.v1.html(js_code, height=0)


def injetar_script_logout():
    """Injeta JavaScript para limpar localStorage"""
    js_code = """
    <script>
        localStorage.removeItem('air_auth_token');
        const url = new URL(window.location.href);
        url.searchParams.delete('auth_token');
        window.history.replaceState({}, '', url.toString());
    </script>
    """
    st.components.v1.html(js_code, height=0)


def render_login():
    """Renderiza tela de login"""
    
    # Verificar login salvo antes de mostrar formulario
    if verificar_login_salvo():
        st.rerun()
        return
    
    # Injetar script para verificar localStorage
    injetar_script_verificar_login()
    
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 50px auto;
        padding: 30px;
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .login-logo {
        text-align: center;
        margin-bottom: 30px;
    }
    .login-logo h1 {
        color: #111827;
        font-size: 48px;
        margin: 0;
    }
    .login-logo p {
        color: #6b7280;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-logo">
            <h1>air</h1>
            <p>Respiramos influencia</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs Login / Criar Conta
        tab1, tab2 = st.tabs(["Entrar", "Criar Conta"])
        
        with tab1:
            render_form_login()
        
        with tab2:
            render_form_registro()


def render_form_login():
    """Formulario de login"""
    
    with st.form("form_login"):
        email = st.text_input("Email", placeholder="seu@email.com")
        senha = st.text_input("Senha", type="password", placeholder="Sua senha")
        
        col1, col2 = st.columns(2)
        with col1:
            lembrar = st.checkbox("Lembrar-me", value=True)
        
        if st.form_submit_button("Entrar", use_container_width=True, type="primary"):
            if email and senha:
                usuario = data_manager.autenticar_usuario(email, senha)
                
                if usuario:
                    st.session_state.usuario_logado = usuario
                    st.session_state.autenticado = True
                    
                    # Salvar token se "Lembrar-me" estiver marcado
                    if lembrar:
                        token = gerar_token_url(email, usuario.get('senha_hash', ''))
                        st.query_params['auth_token'] = token
                        injetar_script_login(token)
                    
                    st.success(f"Bem-vindo, {usuario['nome']}!")
                    st.rerun()
                else:
                    st.error("Email ou senha incorretos")
            else:
                st.warning("Preencha todos os campos")


def render_form_registro():
    """Formulario de registro por convite"""
    
    st.caption("Voce precisa de um link de convite para criar uma conta")
    
    # Verificar se tem token de convite na URL
    token_convite = st.session_state.get('token_convite') or st.query_params.get('convite')
    
    if token_convite:
        convite = data_manager.validar_convite(token_convite)
        
        if convite:
            st.success("Convite valido! Preencha seus dados para criar sua conta.")
            
            with st.form("form_registro"):
                nome = st.text_input("Nome completo", placeholder="Seu nome")
                
                # Se convite tem email especifico, usar ele
                if convite.get('email_convidado'):
                    email = convite['email_convidado']
                    st.text_input("Email", value=email, disabled=True)
                else:
                    email = st.text_input("Email", placeholder="seu@email.com")
                
                senha = st.text_input("Senha", type="password", placeholder="Minimo 6 caracteres")
                senha_confirm = st.text_input("Confirmar senha", type="password", placeholder="Repita a senha")
                
                if st.form_submit_button("Criar Conta", use_container_width=True, type="primary"):
                    if not nome or not email or not senha:
                        st.warning("Preencha todos os campos")
                    elif len(senha) < 6:
                        st.warning("A senha deve ter no minimo 6 caracteres")
                    elif senha != senha_confirm:
                        st.error("As senhas nao conferem")
                    elif data_manager.get_usuario_por_email(email):
                        st.error("Este email ja esta cadastrado")
                    else:
                        # Criar usuario
                        user_id = data_manager.criar_usuario(email, nome, senha)
                        
                        if user_id:
                            # Marcar convite como usado
                            data_manager.usar_convite(token_convite, user_id)
                            
                            st.success("Conta criada com sucesso! Faca login para continuar.")
                            st.balloons()
                        else:
                            st.error("Erro ao criar conta")
        else:
            st.error("Convite invalido ou expirado")
    else:
        st.info("Solicite um convite para criar sua conta")


def render_gerenciar_usuarios():
    """Renderiza gerenciamento de usuarios (apenas admins)"""
    
    usuario = st.session_state.get('usuario_logado', {})
    if usuario.get('role') != 'admin':
        st.warning("Acesso restrito a administradores")
        return
    
    st.subheader("Gerenciar Usuarios")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Usuarios", "Convites", "Novo Convite"])
    
    with tab1:
        usuarios = data_manager.get_usuarios()
        
        if usuarios:
            for u in usuarios:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.write(f"**{u['nome']}**")
                        st.caption(u['email'])
                    
                    with col2:
                        role_atual = u.get('role', 'user')
                        novo_role = st.selectbox(
                            "Role",
                            ["user", "admin"],
                            index=0 if role_atual == 'user' else 1,
                            key=f"role_{u['id']}",
                            label_visibility="collapsed"
                        )
                        if novo_role != role_atual:
                            if st.button("Salvar", key=f"save_role_{u['id']}"):
                                data_manager.atualizar_role_usuario(u['id'], novo_role)
                                st.rerun()
                    
                    with col3:
                        status = "Ativo" if u.get('ativo', True) else "Inativo"
                        st.caption(status)
                    
                    with col4:
                        if u['id'] != usuario['id']:  # Nao pode desativar a si mesmo
                            if u.get('ativo', True):
                                if st.button("Desativar", key=f"desat_{u['id']}"):
                                    data_manager.desativar_usuario(u['id'])
                                    st.rerun()
                            else:
                                if st.button("Ativar", key=f"ativar_{u['id']}"):
                                    data_manager.ativar_usuario(u['id'])
                                    st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("Nenhum usuario cadastrado")
    
    with tab2:
        convites = data_manager.get_convites()
        
        if convites:
            for c in convites:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        email_conv = c.get('email_convidado', 'Qualquer email')
                        st.write(f"**{email_conv}**")
                        st.caption(f"Token: {c['token'][:20]}...")
                    
                    with col2:
                        status = "Usado" if c.get('usado') else "Pendente"
                        st.caption(f"Status: {status}")
                        if c.get('expira_em'):
                            st.caption(f"Expira: {c['expira_em']}")
                    
                    with col3:
                        if not c.get('usado'):
                            # Copiar link
                            app_url = st.session_state.get('app_url', '')
                            link = f"{app_url}?convite={c['token']}"
                            st.code(link, language=None)
                    
                    st.markdown("---")
        else:
            st.info("Nenhum convite criado")
    
    with tab3:
        st.markdown("### Criar Novo Convite")
        
        with st.form("form_convite"):
            email_convite = st.text_input(
                "Email especifico (opcional)",
                placeholder="deixe vazio para aceitar qualquer email"
            )
            
            dias_validade = st.number_input(
                "Dias de validade",
                min_value=1,
                max_value=90,
                value=7
            )
            
            if st.form_submit_button("Criar Convite", type="primary"):
                token = data_manager.criar_convite(
                    criado_por=usuario['id'],
                    email_convidado=email_convite if email_convite else None,
                    dias_validade=dias_validade
                )
                
                if token:
                    app_url = st.session_state.get('app_url', '')
                    link = f"{app_url}?convite={token}"
                    st.success("Convite criado!")
                    st.code(link)
                    st.caption("Compartilhe este link com a pessoa que deseja convidar")
                else:
                    st.error("Erro ao criar convite")


def fazer_logout():
    """Faz logout do usuario e limpa localStorage"""
    # Limpar query params
    if 'auth_token' in st.query_params:
        del st.query_params['auth_token']
    
    # Injetar script para limpar localStorage
    injetar_script_logout()
    
    st.session_state.autenticado = False
    st.session_state.usuario_logado = None
    st.rerun()
