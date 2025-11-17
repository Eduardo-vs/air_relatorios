"""
Página: Campanhas (Lista)
Lista de campanhas quando nenhuma está selecionada
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
        if st.button("Nova Campanha", use_container_width=True):
            st.session_state.show_new_campaign = True
    
    # FORMULÁRIO NOVA CAMPANHA
    if st.session_state.get('show_new_campaign', False):
        with st.form("form_nova_campanha"):
            st.subheader("Criar Campanha")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome *", placeholder="Campanha Verão 2025")
                
                if st.session_state.clientes:
                    opcoes_clientes = [f"{c['nome']}" for c in st.session_state.clientes]
                    cliente_sel = st.selectbox("Cliente *", opcoes_clientes)
                    cliente_obj = next((c for c in st.session_state.clientes if c['nome'] == cliente_sel), None)
                    cliente_id = cliente_obj['id'] if cliente_obj else None
                    cliente_nome = cliente_sel
                else:
                    st.warning("⚠️ Cadastre um cliente primeiro")
                    cliente_id = None
                    cliente_nome = ""
                
                data_inicio = st.date_input("Data Início *", value=datetime.now())
            
            with col2:
                tipo_dados = st.radio("Tipo de Dados", ["Estático", "Dinâmico"], 
                                     help="Estático: dados fixos | Dinâmico: atualização via API")
                data_fim = st.date_input("Data Fim *", value=datetime.now() + timedelta(days=30))
            
            objetivo = st.text_area("Objetivo *", height=100)
            
            st.markdown("---")
            st.subheader("📊 Selecione as Métricas da Campanha")
            st.caption("Marque apenas as métricas que serão coletadas")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                views_check = st.checkbox("Views", value=True)
                interacoes_check = st.checkbox("Interações", value=True)
            
            with col2:
                curtidas_check = st.checkbox("Curtidas", value=True)
                comentarios_check = st.checkbox("Comentários", value=True)
            
            with col3:
                compartilhamentos_check = st.checkbox("Compartilhamentos", value=True)
                saves_check = st.checkbox("Saves", value=True)
            
            with col4:
                clique_link_check = st.checkbox("Cliques Link (Stories)", value=False)
                cupom_check = st.checkbox("Conversões Cupom", value=False)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Criar Campanha", use_container_width=True):
                    if nome and cliente_id and objetivo:
                        data_manager.criar_campanha({
                            'nome': nome,
                            'cliente_id': cliente_id,
                            'cliente_nome': cliente_nome,
                            'objetivo': objetivo,
                            'data_inicio': data_inicio.strftime('%d/%m/%Y'),
                            'data_fim': data_fim.strftime('%d/%m/%Y'),
                            'tipo_dados': tipo_dados.lower(),
                            'metricas_selecionadas': {
                                'views': views_check,
                                'interacoes': interacoes_check,
                                'curtidas': curtidas_check,
                                'comentarios': comentarios_check,
                                'compartilhamentos': compartilhamentos_check,
                                'saves': saves_check,
                                'clique_link': clique_link_check,
                                'cupom_conversoes': cupom_check
                            }
                        })
                        st.session_state.show_new_campaign = False
                        st.success("✅ Campanha criada com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Preencha todos os campos obrigatórios")
            
            with col2:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_new_campaign = False
                    st.rerun()
    
    st.markdown("---")
    
    # LISTA DE CAMPANHAS
    if st.session_state.campanhas:
        for camp in st.session_state.campanhas:
            air_score = funcoes_auxiliares.calcular_air_score(camp)
            
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{camp['nome']}**")
                st.caption(f"{camp['cliente_nome']} • {funcoes_auxiliares.formatar_data_br(camp['data_inicio'])}")
            
            with col2:
                st.caption("Influenciadores")
                st.write(f"**{len(camp['influenciadores'])}**")
            
            with col3:
                st.caption("Posts")
                total_posts = sum([len(inf['posts']) for inf in camp['influenciadores']])
                st.write(f"**{total_posts}**")
            
            with col4:
                st.caption("AIR Score")
                cor_score = "🟢" if air_score > 60 else "🟡" if air_score > 40 else "🔴"
                st.write(f"**{cor_score} {air_score}**")
            
            with col5:
                if st.button("📊 Abrir", key=f"open_{camp['id']}", use_container_width=True):
                    st.session_state.campanha_atual_id = camp['id']
                    st.rerun()
            
            st.markdown("---")
    else:
        st.info("📭 Nenhuma campanha criada ainda")
        
        with st.expander("💡 Como começar"):
            st.markdown("""
            **Criando sua primeira campanha:**
            
            1. Clique em **"Nova Campanha"**
            2. Preencha nome, cliente e objetivo
            3. Defina o período da campanha
            4. **Importante**: Selecione apenas as métricas que você vai coletar
            5. Salve e comece a adicionar influenciadores!
            """)
