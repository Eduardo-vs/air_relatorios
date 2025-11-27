"""
Pagina: Dashboard
Visao geral do sistema
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils import funcoes_auxiliares, data_manager

def render():
    """Renderiza pagina do Dashboard"""
    
    st.markdown('<p class="main-header">Dashboard Geral</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Visao panoramica do sistema</p>', unsafe_allow_html=True)
    
    # Big Numbers
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        campanhas_ativas = len([c for c in st.session_state.campanhas if c['status'] == 'ativa'])
        st.metric("Campanhas Ativas", campanhas_ativas)
    
    with col2:
        st.metric("Clientes", len(st.session_state.clientes))
    
    with col3:
        st.metric("Influenciadores Base", len(st.session_state.influenciadores_base))
    
    with col4:
        total_posts = sum([len(inf['posts']) for c in st.session_state.campanhas for inf in c['influenciadores']])
        st.metric("Posts Totais", total_posts)
    
    with col5:
        total_views = sum([sum([p['metricas']['views'] for p in inf['posts']]) 
                          for c in st.session_state.campanhas for inf in c['influenciadores']])
        st.metric("Views Totais", f"{total_views:,}")
    
    st.markdown("---")
    
    if not st.session_state.campanhas:
        st.info("Crie campanhas para ver analises detalhadas")
        return
    
    # ========================================
    # RESUMO POR CLIENTE
    # ========================================
    st.subheader("Resumo por Cliente")
    
    for cliente in st.session_state.clientes:
        metricas_cliente = data_manager.calcular_metricas_por_cliente(cliente['id'])
        
        if metricas_cliente['total_campanhas'] > 0:
            with st.expander(f"{cliente['nome']} - {metricas_cliente['total_campanhas']} campanhas"):
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                
                with col1:
                    st.metric("Campanhas", metricas_cliente['total_campanhas'])
                with col2:
                    st.metric("Influenciadores", metricas_cliente['total_influenciadores'])
                with col3:
                    st.metric("Posts", metricas_cliente['total_posts'])
                with col4:
                    st.metric("Views", f"{metricas_cliente['total_views']:,}")
                with col5:
                    st.metric("Alcance", f"{metricas_cliente['total_alcance']:,}")
                with col6:
                    if st.button("Ver Relatorio", key=f"dash_rel_{cliente['id']}"):
                        st.session_state.modo_relatorio = 'cliente'
                        st.session_state.filtro_cliente_id = cliente['id']
                        st.session_state.current_page = 'Relatorios'
                        st.rerun()
    
    st.markdown("---")
    
    # ========================================
    # ULTIMAS CAMPANHAS
    # ========================================
    st.subheader("Ultimas Campanhas")
    
    ultimas = st.session_state.campanhas[-5:] if len(st.session_state.campanhas) > 5 else st.session_state.campanhas
    
    for camp in reversed(ultimas):
        metricas = data_manager.calcular_metricas_campanha(camp)
        air_score = funcoes_auxiliares.calcular_air_score(camp)
        
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        
        with col1:
            aon = "[AON]" if camp.get('is_aon') else ""
            st.write(f"**{camp['nome']}** {aon}")
            st.caption(camp['cliente_nome'])
        
        with col2:
            st.metric("Posts", metricas['total_posts'])
        
        with col3:
            st.metric("Views", funcoes_auxiliares.formatar_numero(metricas['total_views']))
        
        with col4:
            st.metric("AIR Score", air_score)
        
        with col5:
            if st.button("Abrir", key=f"dash_camp_{camp['id']}"):
                st.session_state.modo_relatorio = 'campanha'
                st.session_state.campanha_atual_id = camp['id']
                st.session_state.current_page = 'Relatorios'
                st.rerun()
        
        st.markdown("---")
