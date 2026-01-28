"""
AIR Relatorios v9.0
Sistema Completo de Analise de Campanhas
Com design moderno e modais
"""

import streamlit as st
import sys
from pathlib import Path

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from pages import dashboard, clientes, influenciadores, campanhas, configuracoes, relatorios, central_campanha
from pages import relatorio_publico, auth
from utils import funcoes_auxiliares, data_manager
from utils.ui_components import inject_modern_styles

# URL base do app
APP_URL = "https://airrelatoriosgit-csve5an6pncvhztci8rbn9.streamlit.app"

# Configuracao - sidebar sempre escondida
st.set_page_config(
    page_title="AIR Relatorios",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Injetar estilos modernos globais
inject_modern_styles()

# CSS para esconder sidebar completamente
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="stSidebarNav"] {
        display: none;
    }
    .css-1d391kg {
        display: none;
    }
    [data-testid="collapsedControl"] {
        display: none;
    }
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    button[kind="header"] {
        display: none;
    }
    .st-emotion-cache-1gwvy71 {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar banco de dados
data_manager.init_db()

# Criar admin inicial se necessario
auth.criar_admin_inicial()

# Inicializacao
data_manager.inicializar_session_state()

# Salvar URL do app no session_state
st.session_state['app_url'] = APP_URL

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
    
    st.session_state.primary_color = primary_color
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
col1, col2, col3 = st.columns([1, 5, 1])

with col1:
    st.markdown("""
    <div class="top-nav-logo">
        <h1>air</h1>
        <p>Respiramos<br>influencia</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown('<div class="nav-btn-container">', unsafe_allow_html=True)
    
    # Paginas disponiveis (sem Relatorios e sem Usuarios separado)
    pages = ['Dashboard', 'Clientes', 'Influenciadores', 'Campanhas', 'Ajustes']
    
    cols = st.columns(len(pages))
    
    for idx, page in enumerate(pages):
        with cols[idx]:
            is_active = False
            current = st.session_state.current_page
            if page == 'Ajustes' and current in ['Configuracoes', 'Usuarios']:
                is_active = True
            elif current == page:
                is_active = True
            
            btn_type = "primary" if is_active else "secondary"
            if st.button(page, key=f"nav_{page}", use_container_width=True, type=btn_type):
                if page == 'Ajustes':
                    st.session_state.current_page = 'Configuracoes'
                else:
                    st.session_state.current_page = page
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    # Menu do usuario
    st.markdown(f"""
    <div style="text-align: right; padding-top: 5px;">
        <span style="color: #6b7280; font-size: 0.8rem;"> {usuario.get('nome', 'Usuario')}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Sair", key="btn_logout", use_container_width=True):
        auth.fazer_logout()

st.markdown('<div style="margin-bottom: 1rem;"></div>', unsafe_allow_html=True)

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
elif st.session_state.current_page in ['Configuracoes', 'Usuarios']:
    configuracoes.render()

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #9ca3af; padding: 0.5rem 0; font-size: 0.8rem;'>
    <strong>air</strong> | Respiramos influencia | v8.9
</div>
""", unsafe_allow_html=True)
