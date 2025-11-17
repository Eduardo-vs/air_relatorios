"""
AIR Relatórios - Sistema Completo v4.0
Arquivo Principal - Estrutura Modular
"""

import streamlit as st
from datetime import datetime
import json
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Importar páginas
try:
    from pages import dashboard, clientes, influenciadores, campanhas, configuracoes
    from pages.campanha import relatorio_completo
    from utils import funcoes_auxiliares, data_manager
except ImportError as e:
    st.error(f"Erro ao importar módulos: {e}")
    st.stop()

# ========================================
# CONFIGURAÇÃO
# ========================================
st.set_page_config(
    page_title="AIR Relatórios",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# INICIALIZAÇÃO
# ========================================
data_manager.inicializar_session_state()

primary_color = st.session_state.primary_color
secondary_color = st.session_state.secondary_color

# ========================================
# CSS GLOBAL
# ========================================
funcoes_auxiliares.aplicar_css_global(primary_color, secondary_color)

# ========================================
# NAVEGAÇÃO TOP
# ========================================
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("""
    <div class="top-nav-logo">
        <h1>air</h1>
        <p>Respiramos<br>influência</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    cols = st.columns(5)
    pages = ['Dashboard', 'Clientes', 'Influenciadores', 'Campanhas', 'Configurações']
    
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
                    
                    # AIR Score na sidebar
                    air_score = funcoes_auxiliares.calcular_air_score(camp)
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, {primary_color}, {secondary_color}); 
                                color: white; padding: 1rem; border-radius: 12px; text-align: center; margin-bottom: 1rem;'>
                        <div style='font-size: 2.5rem; font-weight: 700;'>{air_score}</div>
                        <div style='font-size: 0.75rem; opacity: 0.9;'>AIR SCORE</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="sidebar-campaign-card">
                        <div style="font-weight: 600; margin-bottom: 0.25rem;">{camp['nome']}</div>
                        <div style="font-size: 0.7rem; color: #6b7280;">
                            {camp['cliente_nome']}<br>
                            {funcoes_auxiliares.formatar_data_br(camp['data_inicio'])} até {funcoes_auxiliares.formatar_data_br(camp['data_fim'])}<br>
                            <strong>{len(camp['influenciadores'])}</strong> influs • 
                            <strong>{sum([len(inf['posts']) for inf in camp['influenciadores']])}</strong> posts
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    break
        else:
            st.session_state.campanha_atual_id = None
    else:
        st.info("Sem campanhas")
    
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Atalhos Rápidos**")
    
    if st.button("➕ Nova Campanha", key="s1", use_container_width=True):
        st.session_state.current_page = 'Campanhas'
        st.session_state.show_new_campaign = True
        st.rerun()
    
    if st.button("👥 Novo Cliente", key="s2", use_container_width=True):
        st.session_state.current_page = 'Clientes'
        st.session_state.show_new_cliente = True
        st.rerun()
    
    if st.button("⭐ Novo Influenciador", key="s3", use_container_width=True):
        st.session_state.current_page = 'Influenciadores'
        st.session_state.show_new_inf = True
        st.rerun()

# ========================================
# ROTEAMENTO DE PÁGINAS
# ========================================

if st.session_state.current_page == 'Dashboard':
    dashboard.render()

elif st.session_state.current_page == 'Clientes':
    clientes.render()

elif st.session_state.current_page == 'Influenciadores':
    influenciadores.render()

elif st.session_state.current_page == 'Campanhas':
    # Se há campanha selecionada, mostra relatório completo
    if st.session_state.campanha_atual_id:
        relatorio_completo.render()
    else:
        campanhas.render()

elif st.session_state.current_page == 'Configurações':
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
        <span>Respiramos influência</span>
    </div>
    <div>Sistema de Análise de Campanhas © 2025 | Versão 4.0 Modular</div>
</div>
""", unsafe_allow_html=True)
