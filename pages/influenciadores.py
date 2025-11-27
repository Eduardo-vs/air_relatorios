"""
Pagina: Influenciadores
Gerenciamento da base de influenciadores com integracao API
"""

import streamlit as st
from utils import data_manager, funcoes_auxiliares, api_client

def render():
    """Renderiza pagina de Influenciadores"""
    
    st.markdown('<p class="main-header">Base de Influenciadores</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Gerencie influenciadores com integracao a API</p>', unsafe_allow_html=True)
    
    # Tabs principais
    tab1, tab2 = st.tabs(["Lista", "Adicionar via API"])
    
    # ========================================
    # TAB 1: LISTA DE INFLUENCIADORES
    # ========================================
    with tab1:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("+ Cadastro Manual", use_container_width=True):
                st.session_state.show_new_inf = True
        
        # FORMULARIO MANUAL
        if st.session_state.get('show_new_inf', False):
            with st.form("form_inf"):
                st.subheader("Cadastrar Influenciador Manualmente")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    nome = st.text_input("Nome *")
                    usuario = st.text_input("Usuario (@) *")
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
                    endereco = st.text_area("Endereco", height=100)
                
                redes = []
                if instagram: redes.append("Instagram")
                if tiktok: redes.append("TikTok")
                if youtube: redes.append("YouTube")
                if twitter: redes.append("Twitter/X")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salvar", use_container_width=True):
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
                            st.success("Influenciador cadastrado!")
                            st.rerun()
                        else:
                            st.error("Preencha os campos obrigatorios")
                
                with col2:
                    if st.form_submit_button("Cancelar", use_container_width=True):
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
                filtro_classe = st.multiselect("Filtrar por classificacao",
                                              ["Nano", "Micro", "Mid", "Macro", "Mega"])
            with col3:
                busca_nome = st.text_input("Buscar por nome")
            
            st.markdown("---")
            
            # Lista
            for inf in st.session_state.influenciadores_base:
                if filtro_rede and not any(r in inf['redes_sociais'] for r in filtro_rede):
                    continue
                if filtro_classe and inf['classificacao'] not in filtro_classe:
                    continue
                if busca_nome and busca_nome.lower() not in inf['nome'].lower():
                    continue
                
                with st.expander(f"{inf['nome']} ({inf['usuario']}) - {inf['classificacao']}"):
                    col1, col2, col3 = st.columns([1, 2, 2])
                    
                    with col1:
                        if inf.get('foto'):
                            st.image(inf['foto'], width=80)
                        else:
                            st.markdown("Sem foto")
                    
                    with col2:
                        st.write(f"**Redes:** {', '.join(inf['redes_sociais'])}")
                        st.write(f"**Seguidores:** {inf['base_seguidores']}")
                        st.write(f"**Classificacao:** {inf['classificacao']}")
                    
                    with col3:
                        st.write(f"**Taxa Eng.:** {inf['taxa_engajamento']}%")
                        st.write(f"**Cidade:** {inf.get('cidade', '-')}")
                        if inf.get('perfil_link'):
                            st.markdown(f"[Ver Perfil]({inf['perfil_link']})")
        else:
            st.info("Nenhum influenciador na base")
    
    # ========================================
    # TAB 2: ADICIONAR VIA API
    # ========================================
    with tab2:
        st.subheader("Buscar Influenciadores via API")
        st.markdown("Adicione multiplos influenciadores de uma vez buscando na API.")
        
        if 'api_usernames' not in st.session_state:
            st.session_state.api_usernames = []
        
        st.markdown("### Adicionar Perfis para Buscar")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            novo_username = st.text_input("Username (sem @)", key="novo_user")
        
        with col2:
            nova_rede = st.selectbox("Rede Social", ["instagram", "tiktok", "youtube"], key="nova_rede")
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("+ Adicionar a Lista", use_container_width=True):
                if novo_username:
                    st.session_state.api_usernames.append({
                        'username': novo_username.replace("@", "").strip(),
                        'network': nova_rede
                    })
                    st.success(f"Adicionado: @{novo_username} ({nova_rede})")
                    st.rerun()
        
        if st.session_state.api_usernames:
            st.markdown("### Perfis na Fila")
            
            for idx, item in enumerate(st.session_state.api_usernames):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"@{item['username']} ({item['network']})")
                with col3:
                    if st.button("Remover", key=f"remove_{idx}"):
                        st.session_state.api_usernames.pop(idx)
                        st.rerun()
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Buscar Todos na API", type="primary", use_container_width=True):
                    with st.spinner("Buscando perfis na API..."):
                        resultados = api_client.buscar_profiles_batch(st.session_state.api_usernames)
                        
                        for res in resultados:
                            if res['result'].get('success'):
                                dados = api_client.processar_dados_influenciador(res['result'])
                                if dados:
                                    data_manager.criar_influenciador_base(dados)
                                    st.success(f"{res['username']} adicionado com sucesso!")
                            else:
                                st.error(f"Erro ao buscar {res['username']}: {res['result'].get('error', 'Erro desconhecido')}")
                        
                        st.session_state.api_usernames = []
                        st.rerun()
            
            with col2:
                if st.button("Limpar Lista", use_container_width=True):
                    st.session_state.api_usernames = []
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### Busca Rapida Individual")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            busca_rapida = st.text_input("Username", key="busca_rap")
        
        with col2:
            rede_rapida = st.selectbox("Rede", ["instagram", "tiktok", "youtube"], key="rede_rap")
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Buscar", use_container_width=True, key="btn_busca_rap"):
                if busca_rapida:
                    with st.spinner("Buscando..."):
                        resultado = api_client.buscar_profile_id(busca_rapida, rede_rapida)
                        
                        if resultado.get('success'):
                            st.success("Perfil encontrado!")
                            
                            dados = api_client.processar_dados_influenciador(resultado)
                            if dados:
                                col1, col2 = st.columns([1, 3])
                                with col1:
                                    if dados.get('foto'):
                                        st.image(dados['foto'], width=100)
                                with col2:
                                    st.write(f"**{dados['nome']}** ({dados['usuario']})")
                                    st.write(f"Seguidores: {dados['base_seguidores']}")
                                    st.write(f"Taxa Eng.: {dados['taxa_engajamento']}%")
                                
                                if st.button("Adicionar a Base", key="add_rapido"):
                                    data_manager.criar_influenciador_base(dados)
                                    st.success("Adicionado!")
                                    st.rerun()
                        else:
                            st.error(f"Erro: {resultado.get('error', 'Perfil nao encontrado')}")
