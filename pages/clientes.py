"""
Pagina: Clientes
Gerenciamento de clientes
"""

import streamlit as st
from utils import data_manager

def render():
    """Renderiza pagina de Clientes"""
    
    st.markdown('<p class="main-header">Clientes</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Gerencie seus clientes</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("+ Novo Cliente", use_container_width=True):
            st.session_state.show_new_cliente = True
    
    if st.session_state.get('show_new_cliente', False):
        with st.form("form_cliente"):
            st.subheader("Cadastrar Cliente")
            
            col1, col2 = st.columns(2)
            with col1:
                nome_cli = st.text_input("Nome da Empresa *")
                cnpj = st.text_input("CNPJ")
            with col2:
                contato = st.text_input("Contato")
                email = st.text_input("E-mail")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Salvar", use_container_width=True):
                    if nome_cli:
                        data_manager.criar_cliente({
                            'nome': nome_cli, 
                            'cnpj': cnpj, 
                            'contato': contato, 
                            'email': email,
                            'tipo': 'normal'
                        })
                        st.session_state.show_new_cliente = False
                        st.success("Cliente cadastrado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Preencha o nome da empresa")
            
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.show_new_cliente = False
                    st.rerun()
    
    st.markdown("---")
    
    if st.session_state.clientes:
        busca = st.text_input("Buscar cliente", placeholder="Digite o nome...")
        
        st.markdown("---")
        
        for cli in st.session_state.clientes:
            if busca and busca.lower() not in cli['nome'].lower():
                continue
            
            metricas_cli = data_manager.calcular_metricas_por_cliente(cli['id'])
            
            col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 1, 1, 1, 1])
            
            with col1:
                st.write(f"**{cli['nome']}**")
            
            with col2:
                st.caption(cli.get('email', '-'))
            
            with col3:
                st.caption(f"{metricas_cli['total_campanhas']} campanhas")
            
            with col4:
                st.caption(f"{metricas_cli['total_views']:,} views")
            
            with col5:
                st.caption(f"{metricas_cli['total_influenciadores']} influs")
            
            with col6:
                if st.button("Ver Relatorio", key=f"rel_cli_{cli['id']}", use_container_width=True):
                    st.session_state.modo_relatorio = 'cliente'
                    st.session_state.filtro_cliente_id = cli['id']
                    st.session_state.current_page = 'Relatorios'
                    st.rerun()
            
            st.markdown("---")
    else:
        st.info("Nenhum cliente cadastrado ainda")
