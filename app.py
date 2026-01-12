"""
AIR Relatorios v8.8
Sistema Completo de Analise de Campanhas
Com autenticacao por login
"""

import streamlit as st
import sys
from pathlib import Path

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from pages import dashboard, clientes, influenciadores, campanhas, configuracoes, relatorios, central_campanha
from pages import relatorio_publico, auth
from utils import funcoes_auxiliares, data_manager

# Configuracao
st.set_page_config(
    page_title="AIR Relatorios",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inicializar banco de dados
data_manager.init_db()

# Criar admin inicial se necessario
auth.criar_admin_inicial()

# Inicializacao
data_manager.inicializar_session_state()

# Verificar query params
query_params = st.query_params

# ========================================
# MODO 1: ACESSO PUBLICO - Link compartilhavel de relatorio
# ========================================
token_relatorio = query_params.get('t', None) or query_params.get('token', None)

if token_relatorio:
    primary_color = '#7c3aed'
    try:
        cfg = data_manager.get_configuracao('primary_color')
        if cfg:
            primary_color = cfg
    except:
        pass
    
    funcoes_auxiliares.aplicar_css_global(primary_color)
    relatorio_publico.render_publico(token_relatorio)
    st.stop()

# ========================================
# MODO 2: CONVITE PARA CRIAR CONTA
# ========================================
token_convite = query_params.get('convite', None)

if token_convite:
    st.session_state.token_convite = token_convite

# ========================================
# MODO 3: APP NORMAL - Requer login
# ========================================

# Verificar se usuario esta logado
if not auth.verificar_autenticacao():
    # Mostrar tela de login
    auth.render_login()
    st.stop()

# ========================================
# USUARIO AUTENTICADO - App completo
# ========================================

usuario = st.session_state.get('usuario_logado', {})
primary_color = st.session_state.primary_color

# CSS
funcoes_auxiliares.aplicar_css_global(primary_color)

# Header com navegacao
col1, col2, col3 = st.columns([1, 4, 1])

with col1:
    st.markdown("""
    <div class="top-nav-logo">
        <h1>air</h1>
        <p>Respiramos<br>influencia</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown('<div class="nav-btn-container">', unsafe_allow_html=True)
    
    # Paginas disponiveis
    pages = ['Dashboard', 'Clientes', 'Influenciadores', 'Campanhas', 'Relatorios', 'Ajustes']
    
    # Admin tem acesso a Usuarios
    if usuario.get('role') == 'admin':
        pages.append('Usuarios')
    
    cols = st.columns(len(pages))
    
    for idx, page in enumerate(pages):
        with cols[idx]:
            if st.button(page, key=f"nav_{page}", use_container_width=True):
                if page == 'Ajustes':
                    st.session_state.current_page = 'Configuracoes'
                else:
                    st.session_state.current_page = page
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    # Menu do usuario
    st.markdown(f"""
    <div style="text-align: right; padding-top: 10px;">
        <span style="color: #6b7280; font-size: 0.85rem;">👤 {usuario.get('nome', 'Usuario')}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Sair", key="btn_logout", use_container_width=True):
        auth.fazer_logout()

st.markdown('<div style="margin-bottom: 1.5rem;"></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### Campanha Ativa")
    
    campanhas_list = data_manager.get_campanhas()
    
    if campanhas_list:
        opcoes = ["Selecione..."] + [c['nome'] for c in campanhas_list]
        
        current_idx = 0
        if st.session_state.campanha_atual_id:
            camp_atual = data_manager.get_campanha(st.session_state.campanha_atual_id)
            if camp_atual:
                try:
                    current_idx = opcoes.index(camp_atual['nome'])
                except:
                    pass
        
        sel = st.selectbox("Campanha", opcoes, index=current_idx, label_visibility="collapsed")
        
        if sel != "Selecione...":
            camp = next((c for c in campanhas_list if c['nome'] == sel), None)
            if camp:
                st.session_state.campanha_atual_id = camp['id']
                
                metricas = data_manager.calcular_metricas_campanha(camp)
                aon = "[AON]" if camp.get('is_aon') else ""
                
                st.markdown(f"""
                <div style='background: {primary_color}; 
                            color: white; padding: 1rem; border-radius: 12px; text-align: center; margin: 1rem 0;'>
                    <div style='font-size: 2rem; font-weight: 700;'>{metricas['engajamento_efetivo']}%</div>
                    <div style='font-size: 0.75rem;'>TAXA ENG. {aon}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.caption(f"{camp.get('cliente_nome', '')}")
                st.caption(f"{metricas['total_influenciadores']} influs | {metricas['total_posts']} posts")
                st.caption(f"{funcoes_auxiliares.formatar_numero(metricas['total_views'])} views")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Central", key="sb_central", use_container_width=True):
                        st.session_state.current_page = 'Central'
                        st.rerun()
                with col2:
                    if st.button("Relatorio", key="sb_rel", use_container_width=True):
                        st.session_state.modo_relatorio = 'campanha'
                        st.session_state.current_page = 'Relatorios'
                        st.rerun()
        else:
            st.session_state.campanha_atual_id = None
    else:
        st.info("Sem campanhas")
    
    st.markdown("---")
    st.markdown("**Atalhos**")
    
    if st.button("+ Nova Campanha", key="s1", use_container_width=True):
        st.session_state.current_page = 'Campanhas'
        st.session_state.show_new_campaign = True
        st.rerun()
    
    if st.button("+ Novo Cliente", key="s2", use_container_width=True):
        st.session_state.current_page = 'Clientes'
        st.session_state.show_new_cliente = True
        st.rerun()
    
    if st.button("+ Novo Influenciador", key="s3", use_container_width=True):
        st.session_state.current_page = 'Influenciadores'
        st.session_state.show_add_influenciador = True
        st.rerun()
    
    st.markdown("---")
    st.caption(f"v8.8 | {usuario.get('role', 'user')}")

# Roteamento
if st.session_state.current_page == 'Dashboard':
    dashboard.render()
elif st.session_state.current_page == 'Clientes':
    clientes.render()
elif st.session_state.current_page == 'Influenciadores':
    influenciadores.render()
elif st.session_state.current_page == 'Campanhas':
    campanhas.render()
elif st.session_state.current_page == 'Central':
    central_campanha.render()
elif st.session_state.current_page == 'Relatorios':
    relatorios.render()
elif st.session_state.current_page == 'Configuracoes':
    configuracoes.render()
elif st.session_state.current_page == 'Usuarios':
    if usuario.get('role') == 'admin':
        auth.render_gerenciar_usuarios()
    else:
        st.warning("Acesso restrito")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #9ca3af; padding: 1rem 0; font-size: 0.85rem;'>
    <strong>air</strong> | Respiramos influencia | v8.8
</div>
""", unsafe_allow_html=True)
