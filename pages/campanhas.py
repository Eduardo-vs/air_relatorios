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
            st.session_state.edit_campanha_id = None
    
    # Form nova/editar campanha
    if st.session_state.get('show_new_campaign', False) or st.session_state.get('edit_campanha_id'):
        edit_id = st.session_state.get('edit_campanha_id')
        camp_edit = data_manager.get_campanha(edit_id) if edit_id else None
        
        with st.form("form_campanha"):
            st.subheader("Editar Campanha" if camp_edit else "Criar Campanha")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome da Campanha *", value=camp_edit['nome'] if camp_edit else "")
                
                clientes = data_manager.get_clientes()
                if clientes:
                    opcoes = {c['nome']: c for c in clientes}
                    cliente_atual = camp_edit.get('cliente_nome', '') if camp_edit else None
                    idx = list(opcoes.keys()).index(cliente_atual) if cliente_atual in opcoes else 0
                    cliente_sel = st.selectbox("Cliente *", list(opcoes.keys()), index=idx)
                    cliente_obj = opcoes.get(cliente_sel)
                else:
                    st.warning("Cadastre um cliente primeiro")
                    cliente_obj = None
                
                di_val = datetime.strptime(camp_edit['data_inicio'], '%d/%m/%Y') if camp_edit else datetime.now()
                df_val = datetime.strptime(camp_edit['data_fim'], '%d/%m/%Y') if camp_edit else datetime.now() + timedelta(days=30)
                data_inicio = st.date_input("Data Inicio", value=di_val)
                data_fim = st.date_input("Data Fim", value=df_val)
            
            with col2:
                tipo_idx = 0 if camp_edit and camp_edit.get('tipo_dados') == 'estatico' else 1
                tipo_dados = st.selectbox("Tipo de Dados", ["estatico", "dinamico"], index=tipo_idx if camp_edit else 0,
                                         help="Estatico: dados congelados | Dinamico: atualiza via API")
                is_aon = st.checkbox("Campanha AON", value=camp_edit.get('is_aon', False) if camp_edit else False,
                                    help="Habilita graficos de evolucao temporal")
                objetivo = st.text_area("Objetivo", value=camp_edit.get('objetivo', '') if camp_edit else "", height=100)
            
            st.markdown("**Metricas a Coletar:**")
            metricas_cfg = camp_edit.get('metricas_selecionadas', {}) if camp_edit else {}
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                views = st.checkbox("Views", value=metricas_cfg.get('views', True))
                alcance = st.checkbox("Alcance", value=metricas_cfg.get('alcance', True))
            with col2:
                interacoes = st.checkbox("Interacoes", value=metricas_cfg.get('interacoes', True))
                impressoes = st.checkbox("Impressoes", value=metricas_cfg.get('impressoes', True))
            with col3:
                curtidas = st.checkbox("Curtidas", value=metricas_cfg.get('curtidas', True))
                comentarios = st.checkbox("Comentarios", value=metricas_cfg.get('comentarios', True))
            with col4:
                compartilhamentos = st.checkbox("Compartilhamentos", value=metricas_cfg.get('compartilhamentos', True))
                saves = st.checkbox("Saves", value=metricas_cfg.get('saves', True))
            
            col1, col2 = st.columns(2)
            with col1:
                clique_link = st.checkbox("Cliques Link (Stories)", value=metricas_cfg.get('clique_link', False))
            with col2:
                cupom = st.checkbox("Conversoes Cupom", value=metricas_cfg.get('cupom_conversoes', False))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.form_submit_button("Salvar", use_container_width=True):
                    if nome and cliente_obj:
                        dados = {
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
                        }
                        if camp_edit:
                            data_manager.atualizar_campanha(edit_id, dados)
                            st.success("Campanha atualizada!")
                        else:
                            data_manager.criar_campanha(dados)
                            st.success("Campanha criada!")
                        st.session_state.show_new_campaign = False
                        st.session_state.edit_campanha_id = None
                        st.rerun()
                    else:
                        st.error("Preencha os campos obrigatorios")
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.show_new_campaign = False
                    st.session_state.edit_campanha_id = None
                    st.rerun()
            with col3:
                if camp_edit:
                    if st.form_submit_button("Excluir", use_container_width=True):
                        data_manager.excluir_campanha(edit_id)
                        st.session_state.edit_campanha_id = None
                        st.success("Campanha excluida!")
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
            
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2.5, 0.8, 0.8, 1, 1.2, 1.2, 0.8])
            
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
                if st.button("Central da Campanha", key=f"ctrl_{camp['id']}"):
                    st.session_state.campanha_atual_id = camp['id']
                    st.session_state.current_page = 'Central'
                    st.rerun()
            with col6:
                if st.button("Relatorio", key=f"rel_{camp['id']}"):
                    st.session_state.campanha_atual_id = camp['id']
                    st.session_state.modo_relatorio = 'campanha'
                    st.session_state.current_page = 'Relatorios'
                    st.rerun()
            with col7:
                if st.button("Editar", key=f"edit_{camp['id']}"):
                    st.session_state.edit_campanha_id = camp['id']
                    st.session_state.show_new_campaign = False
                    st.rerun()
            
            st.markdown("---")
    else:
        st.info("Nenhuma campanha encontrada")
