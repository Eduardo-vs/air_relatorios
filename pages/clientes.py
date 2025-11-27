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
    
    # Form novo cliente
    if st.session_state.get('show_new_cliente', False):
        with st.form("form_cliente"):
            st.subheader("Cadastrar Cliente")
            
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome da Empresa *")
                cnpj = st.text_input("CNPJ")
            with col2:
                contato = st.text_input("Contato")
                email = st.text_input("E-mail")
            
            is_aon = st.checkbox("Cliente AON", help="Habilita visao especial de empresa no relatorio")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Salvar", use_container_width=True):
                    if nome:
                        data_manager.criar_cliente({
                            'nome': nome, 'cnpj': cnpj, 'contato': contato, 
                            'email': email, 'is_aon': is_aon
                        })
                        st.session_state.show_new_cliente = False
                        st.success("Cliente cadastrado!")
                        st.rerun()
                    else:
                        st.error("Preencha o nome")
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.show_new_cliente = False
                    st.rerun()
    
    st.markdown("---")
    
    # Lista de clientes
    clientes = data_manager.get_clientes()
    
    if clientes:
        for cli in clientes:
            metricas = data_manager.calcular_metricas_por_cliente(cli['id'])
            aon = "[AON]" if cli.get('is_aon') else ""
            
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                st.write(f"**{cli['nome']}** {aon}")
                st.caption(cli.get('email', ''))
            with col2:
                st.metric("Campanhas", metricas['total_campanhas'])
            with col3:
                st.metric("Influs", metricas['total_influenciadores'])
            with col4:
                st.metric("Views", funcoes_auxiliares.formatar_numero(metricas['total_views']))
            with col5:
                if st.button("Relatorio", key=f"rel_cli_{cli['id']}"):
                    st.session_state.modo_relatorio = 'cliente'
                    st.session_state.relatorio_cliente_id = cli['id']
                    st.session_state.current_page = 'Relatorios'
                    st.rerun()
            
            st.markdown("---")
    else:
        st.info("Nenhum cliente cadastrado")
