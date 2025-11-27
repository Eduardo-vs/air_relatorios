"""
Pagina: Configuracoes
"""

import streamlit as st
import json
from datetime import datetime
from utils import funcoes_auxiliares, data_manager

def render():
    st.markdown('<p class="main-header">Configuracoes</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Personalize o sistema</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Aparencia", "Banco de Dados", "Sistema"])
    
    with tab1:
        st.subheader("Cores do Sistema")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nova_primary = st.color_picker("Cor Principal", value=st.session_state.primary_color)
            nova_secondary = st.color_picker("Cor Secundaria", value=st.session_state.secondary_color)
            
            if st.button("Aplicar Cores", use_container_width=True):
                st.session_state.primary_color = nova_primary
                st.session_state.secondary_color = nova_secondary
                st.success("Cores aplicadas!")
                st.rerun()
        
        with col2:
            st.markdown("**Preview:**")
            st.markdown(f"""
            <div style='background: {nova_primary}; color: white; padding: 1rem; 
                        border-radius: 8px; text-align: center; margin-bottom: 1rem;'>
                Botao Principal
            </div>
            <div style='background: {nova_secondary}; color: white; padding: 1rem; 
                        border-radius: 8px; text-align: center;'>
                Elemento Secundario
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        st.subheader("Configuracao de Banco de Dados")
        
        st.markdown("""
        ### Como funciona?
        
        **Por padrao**, o sistema usa **session_state** do Streamlit, ou seja, os dados ficam apenas 
        na memoria enquanto a sessao esta ativa. Se voce fechar o navegador, os dados serao perdidos.
        
        Para **persistir os dados**, voce pode configurar um banco de dados:
        
        ---
        
        ### Opcao 1: SQLite (mais simples, local)
        
        O SQLite salva os dados em um arquivo no servidor. Configure a variavel:
        ```
        DATABASE_URL=sqlite:///./air_relatorios.db
        ```
        
        ---
        
        ### Opcao 2: PostgreSQL (recomendado para producao)
        
        **Sites gratuitos para testar PostgreSQL:**
        
        1. **Neon** (https://neon.tech) - 500MB gratis, mais rapido
        2. **Supabase** (https://supabase.com) - 500MB gratis
        3. **ElephantSQL** (https://elephantsql.com) - 20MB gratis (muito pequeno)
        4. **Railway** (https://railway.app) - $5/mes de credito gratis
        
        **Como configurar (exemplo Neon):**
        
        1. Crie uma conta em https://neon.tech
        2. Crie um novo projeto
        3. Copie a connection string (algo como):
           `postgresql://user:pass@ep-xyz.us-east-2.aws.neon.tech/neondb`
        4. Configure a variavel de ambiente:
           ```
           DATABASE_URL=postgresql://user:pass@ep-xyz.us-east-2.aws.neon.tech/neondb
           ```
        
        **No Streamlit Cloud:**
        - Va em Settings > Secrets
        - Adicione: `DATABASE_URL = "sua_connection_string"`
        
        **Localmente:**
        - Crie um arquivo `.env` na raiz:
          ```
          DATABASE_URL=postgresql://user:pass@host/database
          ```
        """)
        
        st.markdown("---")
        st.markdown("**Status atual:**")
        
        import os
        db_url = os.getenv('DATABASE_URL', '')
        
        if 'postgresql' in db_url.lower():
            st.success("Conectado ao PostgreSQL")
            st.code(db_url[:50] + "..." if len(db_url) > 50 else db_url)
        elif 'sqlite' in db_url.lower():
            st.info("Usando SQLite (dados persistidos localmente)")
            st.code(db_url)
        else:
            st.warning("Usando session_state (dados NAO persistidos - serao perdidos ao fechar)")
            st.caption("Configure DATABASE_URL para persistir os dados")
    
    with tab3:
        st.subheader("Estatisticas do Sistema")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Clientes", len(data_manager.get_clientes()))
            st.metric("Campanhas", len(data_manager.get_campanhas()))
        
        with col2:
            st.metric("Influenciadores", len(data_manager.get_influenciadores()))
            total_posts = sum([sum([len(inf['posts']) for inf in c['influenciadores']]) for c in data_manager.get_campanhas()])
            st.metric("Posts", total_posts)
        
        with col3:
            aon = len([c for c in data_manager.get_campanhas() if c.get('is_aon')])
            st.metric("Campanhas AON", aon)
        
        st.markdown("---")
        st.subheader("Backup e Restauracao")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Exportar Backup (JSON)", use_container_width=True):
                backup = {
                    'clientes': data_manager.get_clientes(),
                    'influenciadores': data_manager.get_influenciadores(),
                    'campanhas': data_manager.get_campanhas(),
                    'export_date': datetime.now().isoformat(),
                    'version': '4.2'
                }
                
                json_data = json.dumps(backup, indent=2, ensure_ascii=False).encode('utf-8')
                st.download_button(
                    "Download Backup",
                    data=json_data,
                    file_name=f"air_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            uploaded = st.file_uploader("Importar Backup", type=['json'])
            if uploaded:
                try:
                    backup = json.loads(uploaded.read().decode('utf-8'))
                    if st.button("Restaurar", type="primary"):
                        st.session_state.clientes = backup.get('clientes', [])
                        st.session_state.influenciadores = backup.get('influenciadores', [])
                        st.session_state.campanhas = backup.get('campanhas', [])
                        st.success("Backup restaurado!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
