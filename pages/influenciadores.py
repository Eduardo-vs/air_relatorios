"""
Página: Influenciadores
Gerenciamento da base de influenciadores
"""

import streamlit as st
from utils import data_manager, funcoes_auxiliares

def render():
    """Renderiza página de Influenciadores"""
    
    st.markdown('<p class="main-header">Base de Influenciadores</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Gerencie influenciadores</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Novo Influenciador", use_container_width=True):
            st.session_state.show_new_inf = True
    
    # FORMULÁRIO
    if st.session_state.get('show_new_inf', False):
        with st.form("form_inf"):
            st.subheader("Cadastrar Influenciador")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                nome = st.text_input("Nome *")
                usuario = st.text_input("Usuário (@) *")
                base = st.text_input("Seguidores *", placeholder="Ex: 50K, 1.2M")
                perfil_link = st.text_input("Link Perfil")
            
            with col2:
                st.markdown("**Redes Sociais**")
                instagram = st.checkbox("Instagram", value=True)
                tiktok = st.checkbox("TikTok")
                youtube = st.checkbox("YouTube")
                twitter = st.checkbox("Twitter/X")
                
                taxa_eng = st.number_input("Taxa Eng. (%)", min_value=0.0, max_value=100.0, value=0.0)
            
            with col3:
                cidade = st.text_input("Cidade")
                endereco = st.text_area("Endereço", height=100)
            
            redes = []
            if instagram: redes.append("Instagram")
            if tiktok: redes.append("TikTok")
            if youtube: redes.append("YouTube")
            if twitter: redes.append("Twitter/X")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button(" Salvar", use_container_width=True):
                    if nome and usuario and redes and base:
                        data_manager.criar_influenciador_base({
                            'nome': nome,
                            'usuario': usuario,
                            'redes_sociais': redes,
                            'base_seguidores': base,
                            'perfil_link': perfil_link,
                            'taxa_engajamento': taxa_eng,
                            'cidade': cidade,
                            'endereco': endereco
                        })
                        st.session_state.show_new_inf = False
                        st.success(" Influenciador cadastrado!")
                        st.rerun()
                    else:
                        st.error(" Preencha os campos obrigatórios")
            
            with col2:
                if st.form_submit_button(" Cancelar", use_container_width=True):
                    st.session_state.show_new_inf = False
                    st.rerun()
    
    st.markdown("---")
    
    # FILTROS E LISTA
    if st.session_state.influenciadores_base:
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_rede = st.multiselect("Filtrar por rede", 
                                        ["Instagram", "TikTok", "YouTube", "Twitter/X"])
        with col2:
            filtro_classe = st.multiselect("Filtrar por classificação",
                                          ["Nano", "Micro", "Mid", "Macro", "Mega"])
        with col3:
            busca_nome = st.text_input(" Buscar por nome")
        
        st.markdown("---")
        
        # Lista
        for inf in st.session_state.influenciadores_base:
            # Aplicar filtros
            if filtro_rede and not any(r in inf['redes_sociais'] for r in filtro_rede):
                continue
            if filtro_classe and inf['classificacao'] not in filtro_classe:
                continue
            if busca_nome and busca_nome.lower() not in inf['nome'].lower():
                continue
            
            with st.expander(f" {inf['nome']} ({inf['usuario']}) - {inf['classificacao']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Redes:** {', '.join(inf['redes_sociais'])}")
                    st.write(f"**Seguidores:** {inf['base_seguidores']}")
                with col2:
                    st.write(f"**Classificação:** {inf['classificacao']}")
                    st.write(f"**Taxa Eng.:** {inf['taxa_engajamento']}%")
                with col3:
                    st.write(f"**Cidade:** {inf.get('cidade', '-')}")
                    if inf.get('perfil_link'):
                        st.markdown(f"[ Ver Perfil]({inf['perfil_link']})")
    else:
        st.info(" Nenhum influenciador na base")
