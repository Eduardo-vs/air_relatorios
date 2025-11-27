"""
Página: Clientes
Gerenciamento de clientes
"""

import streamlit as st
from utils import data_manager

def render():
    """Renderiza página de Clientes"""
    
    st.markdown('<p class="main-header">👥 Clientes</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Gerencie seus clientes</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Novo Cliente", use_container_width=True):
            st.session_state.show_new_cliente = True
    
    # ========================================
    # FORMULÁRIO NOVO CLIENTE
    # ========================================
    if st.session_state.get('show_new_cliente', False):
        with st.form("form_cliente"):
            st.subheader("Cadastrar Cliente")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                nome_cli = st.text_input("Nome da Empresa *")
                cnpj = st.text_input("CNPJ")
            with col2:
                contato = st.text_input("Contato")
                email = st.text_input("E-mail")
            with col3:
                st.info("💡 AON agora é configurado por campanha, não mais por cliente")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Salvar", use_container_width=True):
                    if nome_cli:
                        data_manager.criar_cliente({
                            'nome': nome_cli, 
                            'cnpj': cnpj, 
                            'contato': contato, 
                            'email': email,
                            'tipo': 'normal'
                        })
                        st.session_state.show_new_cliente = False
                        st.success("✅ Cliente cadastrado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Preencha o nome da empresa")
            
            with col2:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_new_cliente = False
                    st.rerun()
    
    st.markdown("---")
    
    # ========================================
    # LISTA DE CLIENTES
    # ========================================
    if st.session_state.clientes:
        # Filtros
        busca = st.text_input("🔍 Buscar cliente", placeholder="Digite o nome...")
        
        st.markdown("---")
        
        # Exibir clientes
        for cli in st.session_state.clientes:
            # Aplicar filtros
            if busca and busca.lower() not in cli['nome'].lower():
                continue
            
            # Calcular métricas do cliente
            metricas_cli = data_manager.calcular_metricas_por_cliente(cli['id'])
            
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
            
            with col1:
                st.write(f"**{cli['nome']}**")
            
            with col2:
                st.caption(cli.get('email', '-'))
            
            with col3:
                st.caption(f"📊 {metricas_cli['total_campanhas']} campanhas")
            
            with col4:
                st.caption(f"👁️ {metricas_cli['total_views']:,} views")
            
            with col5:
                st.caption(f"👤 {metricas_cli['total_influenciadores']} influs")
            
            st.markdown("---")
    else:
        st.info("📋 Nenhum cliente cadastrado ainda")
        
        with st.expander("💡 Dica: Como começar"):
            st.markdown("""
            **Primeiros passos:**
            
            1. Clique em **"Novo Cliente"** no canto superior direito
            2. Preencha as informações do cliente
            3. Salve e comece a criar campanhas!
            
            **Nota:** A configuração AON agora é feita por campanha, permitindo
            mais flexibilidade no tipo de relatório oferecido.
            """)
