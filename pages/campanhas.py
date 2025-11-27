"""
Pagina: Campanhas (Lista)
Lista de campanhas
"""

import streamlit as st
from datetime import datetime, timedelta
from utils import data_manager, funcoes_auxiliares

def render():
    """Renderiza lista de campanhas"""
    
    st.markdown('<p class="main-header">Campanhas</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Gerencie campanhas</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("+ Nova Campanha", use_container_width=True):
            st.session_state.show_new_campaign = True
    
    # FORMULARIO NOVA CAMPANHA
    if st.session_state.get('show_new_campaign', False):
        with st.form("form_nova_campanha"):
            st.subheader("Criar Campanha")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome *", placeholder="Campanha Verao 2025")
                
                if st.session_state.clientes:
                    opcoes_clientes = [f"{c['nome']}" for c in st.session_state.clientes]
                    cliente_sel = st.selectbox("Cliente *", opcoes_clientes)
                    cliente_obj = next((c for c in st.session_state.clientes if c['nome'] == cliente_sel), None)
                    cliente_id = cliente_obj['id'] if cliente_obj else None
                    cliente_nome = cliente_sel
                else:
                    st.warning("Cadastre um cliente primeiro")
                    cliente_id = None
                    cliente_nome = ""
                
                data_inicio = st.date_input("Data Inicio *", value=datetime.now())
            
            with col2:
                tipo_dados = st.radio("Tipo de Dados", ["Estatico", "Dinamico"], 
                                     help="Estatico: dados fixos | Dinamico: atualizacao via API")
                
                is_aon = st.checkbox("Campanha AON", 
                                    help="Habilita graficos de evolucao temporal e analises avancadas")
                
                data_fim = st.date_input("Data Fim *", value=datetime.now() + timedelta(days=30))
            
            objetivo = st.text_area("Objetivo *", height=100)
            
            st.markdown("---")
            st.subheader("Selecione as Metricas da Campanha")
            st.caption("Marque apenas as metricas que serao coletadas")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                views_check = st.checkbox("Views", value=True)
                alcance_check = st.checkbox("Alcance", value=True)
            
            with col2:
                interacoes_check = st.checkbox("Interacoes", value=True)
                impressoes_check = st.checkbox("Impressoes", value=True)
            
            with col3:
                curtidas_check = st.checkbox("Curtidas", value=True)
                comentarios_check = st.checkbox("Comentarios", value=True)
            
            with col4:
                compartilhamentos_check = st.checkbox("Compartilhamentos", value=True)
                saves_check = st.checkbox("Saves", value=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                clique_link_check = st.checkbox("Cliques Link (Stories)", value=False)
            
            with col2:
                cupom_check = st.checkbox("Conversoes Cupom", value=False)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Criar Campanha", use_container_width=True):
                    if nome and cliente_id and objetivo:
                        data_manager.criar_campanha({
                            'nome': nome,
                            'cliente_id': cliente_id,
                            'cliente_nome': cliente_nome,
                            'objetivo': objetivo,
                            'data_inicio': data_inicio.strftime('%d/%m/%Y'),
                            'data_fim': data_fim.strftime('%d/%m/%Y'),
                            'tipo_dados': tipo_dados.lower(),
                            'is_aon': is_aon,
                            'metricas_selecionadas': {
                                'views': views_check,
                                'alcance': alcance_check,
                                'interacoes': interacoes_check,
                                'impressoes': impressoes_check,
                                'curtidas': curtidas_check,
                                'comentarios': comentarios_check,
                                'compartilhamentos': compartilhamentos_check,
                                'saves': saves_check,
                                'clique_link': clique_link_check,
                                'cupom_conversoes': cupom_check
                            }
                        })
                        st.session_state.show_new_campaign = False
                        st.success("Campanha criada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Preencha todos os campos obrigatorios")
            
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.show_new_campaign = False
                    st.rerun()
    
    st.markdown("---")
    
    # Filtro por cliente
    col1, col2 = st.columns(2)
    with col1:
        opcoes_clientes = ["Todos"] + [c['nome'] for c in st.session_state.clientes]
        cliente_filtro = st.selectbox("Filtrar por Cliente", opcoes_clientes)
    
    campanhas_filtradas = st.session_state.campanhas
    if cliente_filtro != "Todos":
        cliente_obj = next((c for c in st.session_state.clientes if c['nome'] == cliente_filtro), None)
        if cliente_obj:
            campanhas_filtradas = [c for c in st.session_state.campanhas if c['cliente_id'] == cliente_obj['id']]
    
    # LISTA DE CAMPANHAS
    if campanhas_filtradas:
        for camp in campanhas_filtradas:
            air_score = funcoes_auxiliares.calcular_air_score(camp)
            metricas = data_manager.calcular_metricas_campanha(camp)
            
            aon_badge = "[AON]" if camp.get('is_aon') else ""
            
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{camp['nome']}** {aon_badge}")
                st.caption(f"{camp['cliente_nome']} | {funcoes_auxiliares.formatar_data_br(camp['data_inicio'])}")
            
            with col2:
                st.caption("Influenciadores")
                st.write(f"**{metricas['total_influenciadores']}**")
            
            with col3:
                st.caption("Posts")
                st.write(f"**{metricas['total_posts']}**")
            
            with col4:
                st.caption("Views")
                st.write(f"**{funcoes_auxiliares.formatar_numero(metricas['total_views'])}**")
            
            with col5:
                st.caption("AIR Score")
                st.write(f"**{air_score}**")
            
            with col6:
                if st.button("Ver Relatorio", key=f"open_{camp['id']}", use_container_width=True):
                    st.session_state.modo_relatorio = 'campanha'
                    st.session_state.campanha_atual_id = camp['id']
                    st.session_state.current_page = 'Relatorios'
                    st.rerun()
            
            st.markdown("---")
    else:
        st.info("Nenhuma campanha encontrada")
