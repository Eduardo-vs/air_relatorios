"""
Pagina: Clientes
"""

import streamlit as st
from utils import data_manager, funcoes_auxiliares

def render():
    st.markdown('<p class="main-header">Clientes</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Gerencie seus clientes</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("+ Novo Cliente", type="primary", use_container_width=True):
            st.session_state.show_new_cliente = True
            st.session_state.edit_cliente_id = None
    
    # Form novo/editar cliente
    if st.session_state.get('show_new_cliente', False) or st.session_state.get('edit_cliente_id'):
        edit_id = st.session_state.get('edit_cliente_id')
        cliente_edit = data_manager.get_cliente(edit_id) if edit_id else None
        
        with st.form("form_cliente"):
            st.subheader("Editar Cliente" if cliente_edit else "Cadastrar Cliente")
            
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome da Empresa *", value=cliente_edit['nome'] if cliente_edit else "")
                cnpj = st.text_input("CNPJ", value=cliente_edit.get('cnpj', '') if cliente_edit else "")
            with col2:
                contato = st.text_input("Contato", value=cliente_edit.get('contato', '') if cliente_edit else "")
                email = st.text_input("E-mail", value=cliente_edit.get('email', '') if cliente_edit else "")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.form_submit_button("Salvar", use_container_width=True):
                    if nome:
                        dados = {'nome': nome, 'cnpj': cnpj, 'contato': contato, 'email': email}
                        if cliente_edit:
                            data_manager.atualizar_cliente(edit_id, dados)
                            st.success("Cliente atualizado!")
                        else:
                            data_manager.criar_cliente(dados)
                            st.success("Cliente cadastrado!")
                        st.session_state.show_new_cliente = False
                        st.session_state.edit_cliente_id = None
                        st.rerun()
                    else:
                        st.error("Preencha o nome")
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.show_new_cliente = False
                    st.session_state.edit_cliente_id = None
                    st.rerun()
            with col3:
                if cliente_edit:
                    if st.form_submit_button("Excluir", use_container_width=True):
                        data_manager.excluir_cliente(edit_id)
                        st.session_state.edit_cliente_id = None
                        st.success("Cliente excluido!")
                        st.rerun()
    
    st.markdown("---")
    
    # Lista de clientes
    clientes = data_manager.get_clientes()
    
    if clientes:
        for cli in clientes:
            metricas = data_manager.calcular_metricas_por_cliente(cli['id'])
            campanhas_cliente = data_manager.get_campanhas_por_cliente(cli['id'])
            
            with st.expander(f"**{cli['nome']}** - {metricas['total_campanhas']} campanhas", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.caption(cli.get('email', ''))
                    st.metric("Campanhas", metricas['total_campanhas'])
                with col2:
                    st.metric("Influenciadores", metricas['total_influenciadores'])
                    st.metric("Posts", metricas['total_posts'])
                with col3:
                    st.metric("Views", funcoes_auxiliares.formatar_numero(metricas['total_views']))
                    st.metric("Alcance", funcoes_auxiliares.formatar_numero(metricas['total_alcance']))
                with col4:
                    st.metric("Interacoes", funcoes_auxiliares.formatar_numero(metricas['total_interacoes']))
                    st.metric("Eng. Efetivo", f"{metricas['engajamento_efetivo']:.2f}%")
                
                st.markdown("---")
                
                # Selecao de campanhas para relatorio
                if campanhas_cliente:
                    st.markdown("**Gerar Relatorio**")
                    
                    # Opcoes de campanhas
                    opcoes_camp = {c['nome']: c['id'] for c in campanhas_cliente}
                    
                    campanhas_selecionadas = st.multiselect(
                        "Selecione as campanhas:",
                        options=list(opcoes_camp.keys()),
                        default=list(opcoes_camp.keys()),
                        key=f"camp_sel_{cli['id']}"
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("Ver Relatorio", key=f"rel_cli_{cli['id']}", use_container_width=True):
                            if campanhas_selecionadas:
                                st.session_state.modo_relatorio = 'cliente'
                                st.session_state.relatorio_cliente_id = cli['id']
                                st.session_state.relatorio_campanhas_ids = [opcoes_camp[nome] for nome in campanhas_selecionadas]
                                st.session_state.current_page = 'Relatorios'
                                st.rerun()
                            else:
                                st.warning("Selecione pelo menos uma campanha")
                    
                    with col2:
                        if st.button("Editar Cliente", key=f"edit_cli_{cli['id']}", use_container_width=True):
                            st.session_state.edit_cliente_id = cli['id']
                            st.session_state.show_new_cliente = False
                            st.rerun()
                else:
                    st.info("Nenhuma campanha cadastrada para este cliente")
                    
                    if st.button("Editar Cliente", key=f"edit_cli_alt_{cli['id']}"):
                        st.session_state.edit_cliente_id = cli['id']
                        st.session_state.show_new_cliente = False
                        st.rerun()
    else:
        st.info("Nenhum cliente cadastrado")
