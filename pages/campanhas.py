"""
Pagina: Campanhas
"""

import streamlit as st
from datetime import datetime, timedelta
from utils import data_manager, funcoes_auxiliares

def render():
    st.markdown('<p class="main-header">Campanhas</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Gerencie suas campanhas</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("+ Nova Campanha", type="primary", use_container_width=True):
            st.session_state.show_new_campaign = True
    
    # Form nova campanha
    if st.session_state.get('show_new_campaign', False):
        with st.form("form_campanha"):
            st.subheader("Criar Campanha")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome da Campanha *")
                
                clientes = data_manager.get_clientes()
                if clientes:
                    opcoes = {c['nome']: c for c in clientes}
                    cliente_sel = st.selectbox("Cliente *", list(opcoes.keys()))
                    cliente_obj = opcoes.get(cliente_sel)
                else:
                    st.warning("Cadastre um cliente primeiro")
                    cliente_obj = None
                
                data_inicio = st.date_input("Data Inicio", value=datetime.now())
                data_fim = st.date_input("Data Fim", value=datetime.now() + timedelta(days=30))
            
            with col2:
                tipo_dados = st.selectbox("Tipo de Dados", ["estatico", "dinamico"],
                                         help="Estatico: dados congelados | Dinamico: atualiza via API")
                is_aon = st.checkbox("Campanha AON", help="Habilita graficos de evolucao temporal")
                objetivo = st.text_area("Objetivo", height=100)
            
            st.markdown("**Metricas a Coletar:**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                views = st.checkbox("Views", value=True)
                alcance = st.checkbox("Alcance", value=True)
            with col2:
                interacoes = st.checkbox("Interacoes", value=True)
                impressoes = st.checkbox("Impressoes", value=True)
            with col3:
                curtidas = st.checkbox("Curtidas", value=True)
                comentarios = st.checkbox("Comentarios", value=True)
            with col4:
                compartilhamentos = st.checkbox("Compartilhamentos", value=True)
                saves = st.checkbox("Saves", value=True)
            
            col1, col2 = st.columns(2)
            with col1:
                clique_link = st.checkbox("Cliques Link (Stories)")
            with col2:
                cupom = st.checkbox("Conversoes Cupom")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Criar Campanha", use_container_width=True):
                    if nome and cliente_obj:
                        data_manager.criar_campanha({
                            'nome': nome,
                            'cliente_id': cliente_obj['id'],
                            'cliente_nome': cliente_obj['nome'],
                            'objetivo': objetivo,
                            'data_inicio': data_inicio.strftime('%d/%m/%Y'),
                            'data_fim': data_fim.strftime('%d/%m/%Y'),
                            'tipo_dados': tipo_dados,
                            'is_aon': is_aon,
                            'metricas_selecionadas': {
                                'views': views, 'alcance': alcance, 'interacoes': interacoes,
                                'impressoes': impressoes, 'curtidas': curtidas, 'comentarios': comentarios,
                                'compartilhamentos': compartilhamentos, 'saves': saves,
                                'clique_link': clique_link, 'cupom_conversoes': cupom
                            }
                        })
                        st.session_state.show_new_campaign = False
                        st.success("Campanha criada!")
                        st.rerun()
                    else:
                        st.error("Preencha os campos obrigatorios")
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.show_new_campaign = False
                    st.rerun()
    
    st.markdown("---")
    
    # Filtro
    col1, col2 = st.columns(2)
    with col1:
        clientes = data_manager.get_clientes()
        opcoes_cli = ["Todos"] + [c['nome'] for c in clientes]
        filtro_cli = st.selectbox("Filtrar por Cliente", opcoes_cli)
    
    campanhas = data_manager.get_campanhas()
    
    if filtro_cli != "Todos":
        cliente_obj = next((c for c in clientes if c['nome'] == filtro_cli), None)
        if cliente_obj:
            campanhas = [c for c in campanhas if c['cliente_id'] == cliente_obj['id']]
    
    # Lista
    if campanhas:
        for camp in campanhas:
            metricas = data_manager.calcular_metricas_campanha(camp)
            aon = "[AON]" if camp.get('is_aon') else ""
            
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
            
            with col1:
                st.write(f"**{camp['nome']}** {aon}")
                st.caption(f"{camp.get('cliente_nome', '')} | {funcoes_auxiliares.formatar_data_br(camp['data_inicio'])}")
            with col2:
                st.metric("Influs", metricas['total_influenciadores'])
            with col3:
                st.metric("Posts", metricas['total_posts'])
            with col4:
                st.metric("Views", funcoes_auxiliares.formatar_numero(metricas['total_views']))
            with col5:
                if st.button("Central", key=f"ctrl_{camp['id']}"):
                    st.session_state.campanha_atual_id = camp['id']
                    st.session_state.current_page = 'Central'
                    st.rerun()
            with col6:
                if st.button("Relatorio", key=f"rel_{camp['id']}"):
                    st.session_state.campanha_atual_id = camp['id']
                    st.session_state.modo_relatorio = 'campanha'
                    st.session_state.current_page = 'Relatorios'
                    st.rerun()
            
            st.markdown("---")
    else:
        st.info("Nenhuma campanha encontrada")
