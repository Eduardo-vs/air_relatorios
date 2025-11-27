"""
AIR Relatorios - Sistema Completo v4.1
Arquivo Principal - Estrutura Modular
"""

import streamlit as st
from datetime import datetime
import json
import sys
from pathlib import Path

# Adicionar o diretorio raiz ao path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Importar paginas
try:
    from pages import dashboard, clientes, influenciadores, campanhas, configuracoes, relatorios
    from utils import funcoes_auxiliares, data_manager
except ImportError as e:
    st.error(f"Erro ao importar modulos: {e}")
    st.stop()

# ========================================
# CONFIGURACAO
# ========================================
st.set_page_config(
    page_title="AIR Relatorios",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# INICIALIZACAO
# ========================================
data_manager.inicializar_session_state()

primary_color = st.session_state.primary_color
secondary_color = st.session_state.secondary_color

# ========================================
# CSS GLOBAL
# ========================================
funcoes_auxiliares.aplicar_css_global(primary_color, secondary_color)

# ========================================
# NAVEGACAO TOP
# ========================================
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("""
    <div class="top-nav-logo">
        <h1>air</h1>
        <p>Respiramos<br>influencia</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    cols = st.columns(6)
    pages = ['Dashboard', 'Clientes', 'Influenciadores', 'Campanhas', 'Relatorios', 'Configuracoes']
    
    for idx, page in enumerate(pages):
        with cols[idx]:
            if st.button(page, key=f"nav_{page}", use_container_width=True):
                st.session_state.current_page = page
                st.rerun()

st.markdown('<div style="margin-bottom: 2rem;"></div>', unsafe_allow_html=True)

# ========================================
# SIDEBAR
# ========================================
with st.sidebar:
    st.markdown("### Campanha Ativa")
    
    if st.session_state.campanhas:
        opcoes = ["Nenhuma"] + [c['nome'] for c in st.session_state.campanhas]
        current_index = 0
        
        if st.session_state.campanha_atual_id:
            campanha_atual = data_manager.get_campanha(st.session_state.campanha_atual_id)
            if campanha_atual:
                try:
                    current_index = opcoes.index(campanha_atual['nome'])
                except:
                    pass
        
        selecionada = st.selectbox("", opcoes, index=current_index, label_visibility="collapsed")
        
        if selecionada != "Nenhuma":
            for camp in st.session_state.campanhas:
                if camp['nome'] == selecionada:
                    st.session_state.campanha_atual_id = camp['id']
                    
                    air_score = funcoes_auxiliares.calcular_air_score(camp)
                    aon_badge = "[AON]" if camp.get('is_aon') else ""
                    
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, {primary_color}, {secondary_color}); 
                                color: white; padding: 1rem; border-radius: 12px; text-align: center; margin-bottom: 1rem;'>
                        <div style='font-size: 2.5rem; font-weight: 700;'>{air_score}</div>
                        <div style='font-size: 0.75rem; opacity: 0.9;'>AIR SCORE {aon_badge}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    metricas = data_manager.calcular_metricas_campanha(camp)
                    
                    st.markdown(f"""
                    <div class="sidebar-campaign-card">
                        <div style="font-weight: 600; margin-bottom: 0.25rem;">{camp['nome']}</div>
                        <div style="font-size: 0.7rem; color: #6b7280;">
                            {camp['cliente_nome']}<br>
                            {funcoes_auxiliares.formatar_data_br(camp['data_inicio'])} ate {funcoes_auxiliares.formatar_data_br(camp['data_fim'])}<br>
                            <strong>{metricas['total_influenciadores']}</strong> influs | 
                            <strong>{metricas['total_posts']}</strong> posts<br>
                            <strong>{funcoes_auxiliares.formatar_numero(metricas['total_views'])}</strong> views
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Ver Relatorio", key="sidebar_rel", use_container_width=True):
                        st.session_state.modo_relatorio = 'campanha'
                        st.session_state.current_page = 'Relatorios'
                        st.rerun()
                    
                    break
        else:
            st.session_state.campanha_atual_id = None
    else:
        st.info("Sem campanhas")
    
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Atalhos Rapidos**")
    
    if st.button("Nova Campanha", key="s1", use_container_width=True):
        st.session_state.current_page = 'Campanhas'
        st.session_state.show_new_campaign = True
        st.rerun()
    
    if st.button("Novo Cliente", key="s2", use_container_width=True):
        st.session_state.current_page = 'Clientes'
        st.session_state.show_new_cliente = True
        st.rerun()
    
    if st.button("Novo Influenciador", key="s3", use_container_width=True):
        st.session_state.current_page = 'Influenciadores'
        st.session_state.show_new_inf = True
        st.rerun()
    
    st.markdown("---")
    st.caption("v4.1 - Com integracao API")

# ========================================
# ROTEAMENTO DE PAGINAS
# ========================================

if st.session_state.current_page == 'Dashboard':
    dashboard.render()

elif st.session_state.current_page == 'Clientes':
    clientes.render()

elif st.session_state.current_page == 'Influenciadores':
    influenciadores.render()

elif st.session_state.current_page == 'Campanhas':
    campanhas.render()

elif st.session_state.current_page == 'Relatorios':
    relatorios.render()

elif st.session_state.current_page == 'Configuracoes':
    configuracoes.render()

# ========================================
# FOOTER
# ========================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #9ca3af; padding: 1.5rem 0; font-size: 0.85rem;'>
    <div style='display: flex; justify-content: center; align-items: center; gap: 1rem; margin-bottom: 0.5rem;'>
        <strong style='font-size: 1.1rem; color: #1a1a1a;'>air</strong>
        <span style='color: #d1d5db;'>|</span>
        <span>Respiramos influencia</span>
    </div>
    <div>Sistema de Analise de Campanhas 2025 | Versao 4.1</div>
</div>
""", unsafe_allow_html=True)
