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
        
        st.info("""
        **Recomendacao: PostgreSQL**
        
        Para producao, recomendamos usar PostgreSQL. Configure a variavel de ambiente:
        
        `DATABASE_URL=postgresql://user:password@host:port/database`
        
        Para desenvolvimento, o sistema usa SQLite automaticamente.
        """)
        
        st.markdown("**Status atual:**")
        
        try:
            from utils.database import DATABASE_URL, DB_AVAILABLE
            if 'postgresql' in DATABASE_URL.lower():
                st.success("Conectado ao PostgreSQL")
            else:
                st.warning("Usando SQLite (desenvolvimento)")
        except:
            st.warning("Usando session_state (sem persistencia)")
    
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
