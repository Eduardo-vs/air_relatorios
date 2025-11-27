"""
Página: Configurações
Personalização e gerenciamento do sistema
"""

import streamlit as st
import json
from datetime import datetime
from utils import funcoes_auxiliares

def render():
    """Renderiza página de Configurações"""
    
    st.markdown('<p class="main-header">⚙️ Configurações</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Personalize o sistema</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🎨 Aparência", "💾 Sistema"])
    
    # TAB APARÊNCIA
    with tab1:
        st.subheader("Personalizar Cores")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Cor Principal**")
            nova_cor_primary = st.color_picker("Botões e destaques", value=st.session_state.primary_color)
            
            st.markdown("**Cor Secundária**")
            nova_cor_secondary = st.color_picker("Elementos secundários", value=st.session_state.secondary_color)
            
            if st.button("🎨 Aplicar Cores", use_container_width=True):
                st.session_state.primary_color = nova_cor_primary
                st.session_state.secondary_color = nova_cor_secondary
                st.success("✅ Cores alteradas! A página será recarregada.")
                st.rerun()
        
        with col2:
            st.markdown("**Preview:**")
            
            # Preview cor primária
            text_preview_primary = funcoes_auxiliares.get_text_color(nova_cor_primary)
            st.markdown(f"""
            <div style='background: {nova_cor_primary}; color: {text_preview_primary}; 
                        padding: 1rem; border-radius: 8px; text-align: center; 
                        font-weight: 600; margin-bottom: 1rem;'>
                Botão Principal
            </div>
            """, unsafe_allow_html=True)
            
            # Preview cor secundária
            text_preview_secondary = funcoes_auxiliares.get_text_color(nova_cor_secondary)
            st.markdown(f"""
            <div style='background: {nova_cor_secondary}; color: {text_preview_secondary}; 
                        padding: 1rem; border-radius: 8px; text-align: center; font-weight: 600;'>
                Elemento Secundário
            </div>
            """, unsafe_allow_html=True)
    
    # TAB SISTEMA
    with tab2:
        st.subheader("Informações do Sistema")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Campanhas", len(st.session_state.campanhas))
            st.metric("Clientes", len(st.session_state.clientes))
        
        with col2:
            st.metric("Influenciadores", len(st.session_state.influenciadores_base))
            total_posts = sum([sum([len(inf['posts']) for inf in c['influenciadores']]) 
                              for c in st.session_state.campanhas])
            st.metric("Posts Totais", total_posts)
        
        with col3:
            campanhas_aon = len([c for c in st.session_state.campanhas if c.get('is_aon')])
            st.metric("Campanhas AON", campanhas_aon)
            campanhas_ativas = len([c for c in st.session_state.campanhas if c['status'] == 'ativa'])
            st.metric("Campanhas Ativas", campanhas_ativas)
        
        st.markdown("---")
        
        # Backup e Restauração
        st.subheader("💾 Backup e Restauração")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Exportar Dados**")
            if st.button("📥 Baixar Backup (JSON)", use_container_width=True):
                backup_data = {
                    'campanhas': st.session_state.campanhas,
                    'clientes': st.session_state.clientes,
                    'influenciadores_base': st.session_state.influenciadores_base,
                    'export_date': datetime.now().isoformat(),
                    'version': '4.1'
                }
                
                json_data = json.dumps(backup_data, indent=2, ensure_ascii=False).encode('utf-8')
                st.download_button(
                    "📥 Download Backup",
                    data=json_data,
                    file_name=f"air_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col2:
            st.markdown("**Importar Dados**")
            uploaded_file = st.file_uploader("📤 Carregar Backup", type=['json'])
            if uploaded_file:
                try:
                    backup_data = json.loads(uploaded_file.read().decode('utf-8'))
                    if st.button("✅ Restaurar Backup", type="primary", use_container_width=True):
                        st.session_state.campanhas = backup_data.get('campanhas', [])
                        st.session_state.clientes = backup_data.get('clientes', [])
                        st.session_state.influenciadores_base = backup_data.get('influenciadores_base', [])
                        st.success("✅ Backup restaurado com sucesso!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao ler backup: {str(e)}")
        
        st.markdown("---")
        
        # Zona de Perigo
        st.warning("⚠️ **Zona de Perigo**")
        
        if st.button("🗑️ Limpar Todos os Dados", use_container_width=True):
            st.session_state.show_delete_confirm = True
        
        if st.session_state.get('show_delete_confirm', False):
            st.error("⚠️ **ATENÇÃO**: Esta ação é irreversível!")
            if st.checkbox("Confirmo que quero deletar TODOS os dados do sistema"):
                if st.button("🗑️ SIM, DELETAR TUDO", type="primary"):
                    st.session_state.campanhas = []
                    st.session_state.clientes = []
                    st.session_state.influenciadores_base = []
                    st.session_state.campanha_atual_id = None
                    st.session_state.show_delete_confirm = False
                    st.success("✅ Todos os dados foram removidos!")
                    st.rerun()
