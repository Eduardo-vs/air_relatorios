"""
Pagina: Autenticacao
Login, registro por convite e gerenciamento de usuarios
"""

import streamlit as st
from utils import data_manager
import hashlib
import json
from datetime import datetime, timedelta

# Tentar importar cookies manager
try:
    import extra_streamlit_components as stx
    COOKIES_DISPONIVEL = True
except ImportError:
    COOKIES_DISPONIVEL = False


def get_cookie_manager():
    """Retorna o gerenciador de cookies"""
    if not COOKIES_DISPONIVEL:
        return None
    return stx.CookieManager()


def verificar_login_salvo():
    """Verifica se existe login salvo em cookie e faz login automatico"""
    if st.session_state.get('autenticado'):
        return True
    
    if not COOKIES_DISPONIVEL:
        return False
    
    try:
        cookie_manager = get_cookie_manager()
        if cookie_manager is None:
            return False
        
        # Buscar cookie de sessao
        token_cookie = cookie_manager.get("air_session")
        
        if token_cookie:
            # Decodificar token
            try:
                dados = json.loads(token_cookie)
                email = dados.get('email')
                token_hash = dados.get('token')
                expira = dados.get('expira')
                
                # Verificar expiracao
                if expira and datetime.fromisoformat(expira) < datetime.now():
                    # Cookie expirado, limpar
                    cookie_manager.delete("air_session")
                    return False
                
                # Verificar se usuario existe
                if email:
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
    except:
        pass
    
    return False


def gerar_token_sessao(email: str, senha_hash: str) -> str:
    """Gera token de sessao baseado no email e hash da senha"""
    dados = f"{email}:{senha_hash}:air_secret_key"
    return hashlib.sha256(dados.encode()).hexdigest()[:32]


def salvar_login_cookie(email: str, senha_hash: str, dias: int = 30):
    """Salva login em cookie para persistencia"""
    if not COOKIES_DISPONIVEL:
        return
    
    try:
        cookie_manager = get_cookie_manager()
        if cookie_manager is None:
            return
        
        token = gerar_token_sessao(email, senha_hash)
        expira = (datetime.now() + timedelta(days=dias)).isoformat()
        
        dados = json.dumps({
            'email': email,
            'token': token,
            'expira': expira
        })
        
        cookie_manager.set("air_session", dados, expires_at=datetime.now() + timedelta(days=dias))
    except:
        pass


def limpar_cookie_login():
    """Remove cookie de login"""
    if not COOKIES_DISPONIVEL:
        return
    
    try:
        cookie_manager = get_cookie_manager()
        if cookie_manager:
            cookie_manager.delete("air_session")
    except:
        pass


def render_login():
    """Renderiza tela de login"""
    
    # Verificar login salvo antes de mostrar formulario
    if verificar_login_salvo():
        st.rerun()
        return
    
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
        color: #7c3aed;
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
                    
                    # Salvar em cookie se "Lembrar-me" estiver marcado
                    if lembrar:
                        salvar_login_cookie(email, usuario.get('senha_hash', ''))
                    
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
                            st.session_state.token_convite = None
                            st.rerun()
                        else:
                            st.error("Erro ao criar conta. Tente novamente.")
        else:
            st.error("Convite invalido ou expirado")
            st.info("Solicite um novo link de convite a um administrador")
    else:
        # Campo para inserir codigo de convite
        with st.form("form_convite"):
            codigo = st.text_input("Codigo do convite", placeholder="Cole o codigo ou link de convite")
            
            if st.form_submit_button("Verificar Convite", use_container_width=True):
                if codigo:
                    # Extrair token se for URL completa
                    if 'convite=' in codigo:
                        token = codigo.split('convite=')[-1].split('&')[0]
                    else:
                        token = codigo.strip()
                    
                    convite = data_manager.validar_convite(token)
                    
                    if convite:
                        st.session_state.token_convite = token
                        st.rerun()
                    else:
                        st.error("Convite invalido ou expirado")
                else:
                    st.warning("Cole o codigo do convite")


def render_gerenciar_usuarios():
    """Pagina de gerenciamento de usuarios (admin)"""
    
    st.subheader("Gerenciar Usuarios")
    
    usuario_atual = st.session_state.get('usuario_logado', {})
    
    # Apenas admin pode gerenciar
    if usuario_atual.get('role') != 'admin':
        st.warning("Acesso restrito a administradores")
        return
    
    # Gerar convite
    st.markdown("### Convidar Novo Usuario")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        email_convite = st.text_input("Email do convidado (opcional)", placeholder="deixe vazio para convite generico")
    with col2:
        dias_validade = st.number_input("Validade (dias)", min_value=1, max_value=30, value=7)
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Gerar Convite", type="primary"):
            token = data_manager.gerar_convite(
                criado_por=usuario_atual['id'],
                email_convidado=email_convite if email_convite else None,
                dias_validade=dias_validade
            )
            
            # Gerar link
            base_url = st.session_state.get('app_url', 'https://airrelatoriosgit-csve5an6pncvhztci8rbn9.streamlit.app')
            link = f"{base_url}?convite={token}"
            
            st.success("Convite gerado!")
            st.code(link)
            st.caption("Compartilhe este link com a pessoa que deseja convidar")
    
    st.markdown("---")
    
    # Listar usuarios
    st.markdown("### Usuarios Cadastrados")
    
    usuarios = data_manager.get_usuarios()
    
    if usuarios:
        for user in usuarios:
            with st.expander(f"{user['nome']} ({user['email']}) - {user['role']}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Email:** {user['email']}")
                    st.write(f"**Funcao:** {user['role']}")
                    st.write(f"**Criado em:** {user.get('created_at', '-')[:10] if user.get('created_at') else '-'}")
                    st.write(f"**Ultimo login:** {user.get('last_login', '-')[:10] if user.get('last_login') else '-'}")
                
                with col2:
                    novo_role = st.selectbox(
                        "Funcao",
                        ["user", "admin"],
                        index=0 if user['role'] == 'user' else 1,
                        key=f"role_{user['id']}"
                    )
                    if novo_role != user['role']:
                        if st.button("Atualizar", key=f"update_{user['id']}"):
                            data_manager.atualizar_usuario(user['id'], {'nome': user['nome'], 'email': user['email'], 'role': novo_role})
                            st.success("Atualizado!")
                            st.rerun()
                
                with col3:
                    if user['id'] != usuario_atual['id']:  # Nao pode desativar a si mesmo
                        if user.get('ativo', 1):
                            if st.button("Desativar", key=f"desat_{user['id']}"):
                                data_manager.desativar_usuario(user['id'])
                                st.success("Usuario desativado")
                                st.rerun()
    else:
        st.info("Nenhum usuario cadastrado")
    
    st.markdown("---")
    
    # Listar convites
    st.markdown("### Convites Pendentes")
    
    convites = data_manager.get_convites()
    convites_pendentes = [c for c in convites if not c.get('usado')]
    
    if convites_pendentes:
        for conv in convites_pendentes:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                email_info = conv.get('email_convidado') or "Qualquer email"
                st.write(f"Para: {email_info}")
                st.caption(f"Expira: {conv.get('expira_em', '-')[:10] if conv.get('expira_em') else 'Nunca'}")
            
            with col2:
                base_url = st.session_state.get('app_url', 'https://airrelatoriosgit-csve5an6pncvhztci8rbn9.streamlit.app')
                link = f"{base_url}?convite={conv['token']}"
                st.code(conv['token'][:20] + "...")
            
            with col3:
                if st.button("Excluir", key=f"del_conv_{conv['id']}"):
                    data_manager.excluir_convite(conv['id'])
                    st.rerun()
    else:
        st.info("Nenhum convite pendente")


def criar_admin_inicial():
    """Cria usuario admin inicial se nao existir nenhum usuario"""
    if data_manager.contar_usuarios() == 0:
        # Criar admin padrao
        data_manager.criar_usuario(
            email="admin@air.com",
            nome="Administrador",
            senha="admin123",
            role="admin"
        )
        return True
    return False


def verificar_autenticacao():
    """Verifica se usuario esta autenticado"""
    return st.session_state.get('autenticado', False)


def fazer_logout():
    """Faz logout do usuario e limpa cookie"""
    # Limpar cookie de sessao
    limpar_cookie_login()
    
    st.session_state.autenticado = False
    st.session_state.usuario_logado = None
    st.rerun()
