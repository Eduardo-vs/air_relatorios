"""
Pagina: Influenciadores
Base de influenciadores com API
"""

import streamlit as st
from utils import data_manager, api_client, funcoes_auxiliares

def render():
    st.markdown('<p class="main-header">Influenciadores</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Base de influenciadores</p>', unsafe_allow_html=True)
    
    # Botoes de acao
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if st.button("Atualizar Dados", use_container_width=True):
            with st.spinner("Atualizando via API..."):
                atualizados = 0
                for inf in data_manager.get_influenciadores():
                    if inf.get('profile_id'):
                        try:
                            dados = api_client.atualizar_influenciador_api(inf['profile_id'])
                            if dados:
                                data_manager.atualizar_influenciador(inf['id'], dados)
                                atualizados += 1
                        except:
                            pass
                st.success(f"{atualizados} influenciadores atualizados!")
                st.rerun()
    
    with col3:
        if st.button("+ Adicionar", type="primary", use_container_width=True):
            st.session_state.show_add_influenciador = True
            st.session_state.edit_influenciador_id = None
    
    # Modal de adicionar
    if st.session_state.get('show_add_influenciador', False):
        render_modal_adicionar()
    
    # Modal de editar
    if st.session_state.get('edit_influenciador_id'):
        render_modal_editar()
    
    st.markdown("---")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_rede = st.selectbox("Rede", ["Todas", "instagram", "tiktok", "youtube"])
    with col2:
        filtro_class = st.selectbox("Classificacao", ["Todas", "Nano", "Micro", "Mid", "Macro", "Mega"])
    with col3:
        filtro_busca = st.text_input("Buscar", placeholder="Nome ou usuario...")
    
    st.markdown("---")
    
    # Lista de influenciadores
    influenciadores = data_manager.get_influenciadores()
    
    # Aplicar filtros
    if filtro_rede != "Todas":
        influenciadores = [i for i in influenciadores if i.get('network') == filtro_rede]
    if filtro_class != "Todas":
        influenciadores = [i for i in influenciadores if i.get('classificacao') == filtro_class]
    if filtro_busca:
        filtro_busca = filtro_busca.lower()
        influenciadores = [i for i in influenciadores if filtro_busca in i['nome'].lower() or filtro_busca in i['usuario'].lower()]
    
    if influenciadores:
        # Cabecalho
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.6, 2, 1, 1, 1, 1, 1, 0.8])
        with col1:
            st.caption("Foto")
        with col2:
            st.caption("Nome")
        with col3:
            st.caption("Rede")
        with col4:
            st.caption("Seguidores")
        with col5:
            st.caption("AIR Score")
        with col6:
            st.caption("Taxa Eng.")
        with col7:
            st.caption("Classe")
        with col8:
            st.caption("Acao")
        
        st.markdown("---")
        
        for inf in influenciadores:
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.6, 2, 1, 1, 1, 1, 1, 0.8])
            
            with col1:
                if inf.get('foto'):
                    st.image(inf['foto'], width=40)
                else:
                    st.write("-")
            
            with col2:
                st.write(f"**{inf['nome']}**")
                st.caption(f"@{inf['usuario']}")
            
            with col3:
                st.write(inf.get('network', '-').title())
            
            with col4:
                st.write(funcoes_auxiliares.formatar_numero(inf.get('seguidores', 0)))
            
            with col5:
                st.write(f"{inf.get('air_score', 0)}")
            
            with col6:
                st.write(f"{inf.get('engagement_rate', 0):.2f}%")
            
            with col7:
                st.write(inf.get('classificacao', '-'))
            
            with col8:
                if st.button("Editar", key=f"edit_{inf['id']}"):
                    st.session_state.edit_influenciador_id = inf['id']
                    st.session_state.show_add_influenciador = False
                    st.rerun()
            
            st.markdown("---")
    else:
        st.info("Nenhum influenciador encontrado")


def render_modal_adicionar():
    """Modal para adicionar influenciador"""
    
    with st.container():
        st.subheader("Adicionar Influenciador")
        
        tipo = st.radio("Tipo de cadastro:", ["Buscar na API", "Cadastro Manual"], horizontal=True)
        
        if tipo == "Buscar na API":
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Username", placeholder="@usuario")
            with col2:
                network = st.selectbox("Rede Social", ["instagram", "tiktok", "youtube"])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Buscar", use_container_width=True):
                    if username:
                        with st.spinner("Buscando..."):
                            dados = api_client.buscar_perfil_por_username(username.replace("@", ""), network)
                            if dados:
                                st.session_state.api_preview = dados
                                st.success("Encontrado!")
                            else:
                                st.error("Nao encontrado")
            with col2:
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.show_add_influenciador = False
                    st.session_state.api_preview = None
                    st.rerun()
            
            # Preview
            if st.session_state.get('api_preview'):
                dados = st.session_state.api_preview
                st.markdown("---")
                st.markdown("**Preview:**")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if dados.get('foto'):
                        st.image(dados['foto'], width=80)
                with col2:
                    st.write(f"**{dados['nome']}** (@{dados['usuario']})")
                    st.write(f"Seguidores: {funcoes_auxiliares.formatar_numero(dados.get('seguidores', 0))}")
                    st.write(f"AIR Score: {dados.get('air_score', 0)} | Taxa Eng: {dados.get('engagement_rate', 0):.2f}%")
                
                if st.button("Adicionar a Base", type="primary", use_container_width=True):
                    # Verificar duplicata
                    existente = next((i for i in data_manager.get_influenciadores() 
                                     if i.get('profile_id') == dados.get('profile_id')), None)
                    if existente:
                        st.warning("Influenciador ja existe na base!")
                    else:
                        data_manager.criar_influenciador(dados)
                        st.session_state.show_add_influenciador = False
                        st.session_state.api_preview = None
                        st.success("Adicionado!")
                        st.rerun()
        
        else:  # Cadastro Manual
            with st.form("form_manual"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nome = st.text_input("Nome *")
                    usuario = st.text_input("Username *", placeholder="sem @")
                    network = st.selectbox("Rede Social *", ["instagram", "tiktok", "youtube"])
                    seguidores = st.number_input("Seguidores", min_value=0, value=0)
                    foto = st.text_input("URL da Foto", placeholder="https://...")
                
                with col2:
                    bio = st.text_area("Bio", height=80)
                    engagement_rate = st.number_input("Taxa de Engajamento (%)", min_value=0.0, value=0.0, step=0.01)
                    air_score = st.number_input("AIR Score", min_value=0.0, max_value=100.0, value=0.0)
                    reach_rate = st.number_input("Taxa de Alcance (%)", min_value=0.0, value=0.0, step=0.01)
                    total_posts = st.number_input("Total de Posts", min_value=0, value=0)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salvar", use_container_width=True):
                        if nome and usuario:
                            data_manager.criar_influenciador({
                                'nome': nome,
                                'usuario': usuario,
                                'network': network,
                                'seguidores': seguidores,
                                'foto': foto,
                                'bio': bio,
                                'engagement_rate': engagement_rate,
                                'air_score': air_score,
                                'reach_rate': reach_rate,
                                'total_posts': total_posts,
                                'classificacao': data_manager.calcular_classificacao(seguidores)
                            })
                            st.session_state.show_add_influenciador = False
                            st.success("Influenciador cadastrado!")
                            st.rerun()
                        else:
                            st.error("Preencha nome e username")
                with col2:
                    if st.form_submit_button("Cancelar", use_container_width=True):
                        st.session_state.show_add_influenciador = False
                        st.rerun()


def render_modal_editar():
    """Modal para editar influenciador"""
    
    inf_id = st.session_state.edit_influenciador_id
    inf = data_manager.get_influenciador(inf_id)
    
    if not inf:
        st.session_state.edit_influenciador_id = None
        st.rerun()
        return
    
    with st.container():
        st.subheader(f"Editar: {inf['nome']}")
        
        with st.form("form_editar_inf"):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome *", value=inf['nome'])
                usuario = st.text_input("Username *", value=inf['usuario'])
                network = st.selectbox("Rede Social *", ["instagram", "tiktok", "youtube"],
                                      index=["instagram", "tiktok", "youtube"].index(inf.get('network', 'instagram')))
                seguidores = st.number_input("Seguidores", min_value=0, value=inf.get('seguidores', 0))
                foto = st.text_input("URL da Foto", value=inf.get('foto', ''))
            
            with col2:
                bio = st.text_area("Bio", value=inf.get('bio', ''), height=80)
                engagement_rate = st.number_input("Taxa de Engajamento (%)", min_value=0.0, 
                                                  value=float(inf.get('engagement_rate', 0)), step=0.01)
                air_score = st.number_input("AIR Score", min_value=0.0, max_value=100.0, 
                                           value=float(inf.get('air_score', 0)))
                reach_rate = st.number_input("Taxa de Alcance (%)", min_value=0.0, 
                                            value=float(inf.get('reach_rate', 0)), step=0.01)
                total_posts = st.number_input("Total de Posts", min_value=0, value=inf.get('total_posts', 0))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.form_submit_button("Salvar", use_container_width=True):
                    if nome and usuario:
                        data_manager.atualizar_influenciador(inf_id, {
                            'nome': nome,
                            'usuario': usuario,
                            'network': network,
                            'seguidores': seguidores,
                            'foto': foto,
                            'bio': bio,
                            'engagement_rate': engagement_rate,
                            'air_score': air_score,
                            'reach_rate': reach_rate,
                            'total_posts': total_posts,
                            'classificacao': data_manager.calcular_classificacao(seguidores)
                        })
                        st.session_state.edit_influenciador_id = None
                        st.success("Atualizado!")
                        st.rerun()
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.edit_influenciador_id = None
                    st.rerun()
            with col3:
                if st.form_submit_button("Excluir", use_container_width=True):
                    data_manager.excluir_influenciador(inf_id)
                    st.session_state.edit_influenciador_id = None
                    st.success("Excluido!")
                    st.rerun()
