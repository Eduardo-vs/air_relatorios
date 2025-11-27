"""
Pagina: Dashboard
"""

import streamlit as st
from utils import data_manager, funcoes_auxiliares

def render():
    st.markdown('<p class="main-header">Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Visao geral do sistema</p>', unsafe_allow_html=True)
    
    # Big Numbers
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        campanhas_ativas = len([c for c in data_manager.get_campanhas() if c['status'] == 'ativa'])
        st.metric("Campanhas Ativas", campanhas_ativas)
    with col2:
        st.metric("Clientes", len(data_manager.get_clientes()))
    with col3:
        st.metric("Influenciadores", len(data_manager.get_influenciadores()))
    with col4:
        total_posts = sum([sum([len(inf['posts']) for inf in c['influenciadores']]) for c in data_manager.get_campanhas()])
        st.metric("Posts", total_posts)
    with col5:
        total_views = sum([sum([sum([p.get('views', 0) for p in inf['posts']]) for inf in c['influenciadores']]) for c in data_manager.get_campanhas()])
        st.metric("Views Totais", funcoes_auxiliares.formatar_numero(total_views))
    
    st.markdown("---")
    
    # Ultimas campanhas
    st.subheader("Ultimas Campanhas")
    
    campanhas = data_manager.get_campanhas()
    if campanhas:
        for camp in campanhas[-5:]:
            metricas = data_manager.calcular_metricas_campanha(camp)
            aon = "[AON]" if camp.get('is_aon') else ""
            
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                st.write(f"**{camp['nome']}** {aon}")
                st.caption(camp.get('cliente_nome', ''))
            with col2:
                st.metric("Posts", metricas['total_posts'])
            with col3:
                st.metric("Views", funcoes_auxiliares.formatar_numero(metricas['total_views']))
            with col4:
                st.metric("Taxa Eng.", f"{metricas['engajamento_efetivo']}%")
            with col5:
                if st.button("Abrir", key=f"dash_{camp['id']}"):
                    st.session_state.campanha_atual_id = camp['id']
                    st.session_state.current_page = 'Central'
                    st.rerun()
            
            st.markdown("---")
    else:
        st.info("Nenhuma campanha criada ainda")
