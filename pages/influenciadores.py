"""
Pagina: Influenciadores
Base de influenciadores com lista e botao unico para adicionar
"""

import streamlit as st
from utils import data_manager, funcoes_auxiliares, api_client

def render():
    """Renderiza pagina de Influenciadores"""
    
    st.markdown('<p class="main-header">Base de Influenciadores</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Gerencie seus influenciadores com integracao API</p>', unsafe_allow_html=True)
    
    # Botao unico no topo
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col2:
        if st.button("Atualizar Dados", use_container_width=True):
            atualizar_todos_influenciadores()
    
    with col3:
        if st.button("+ Adicionar", type="primary", use_container_width=True):
            st.session_state.show_add_influenciador = True
    
    # Modal de adicionar influenciador
    if st.session_state.get('show_add_influenciador', False):
        render_modal_adicionar()
    
    st.markdown("---")
    
    # Lista de influenciadores
    render_lista_influenciadores()


def render_modal_adicionar():
    """Modal para adicionar influenciador - manual ou API"""
    
    with st.expander("Adicionar Influenciador", expanded=True):
        modo = st.radio("Modo de cadastro:", ["Buscar na API", "Cadastro Manual"], horizontal=True)
        
        st.markdown("---")
        
        if modo == "Buscar na API":
            render_form_api()
        else:
            render_form_manual()
        
        if st.button("Cancelar", key="cancel_add"):
            st.session_state.show_add_influenciador = False
            st.rerun()


def render_form_api():
    """Formulario para buscar influenciador na API"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        username = st.text_input("Username (sem @)", placeholder="casaldr_ofc")
    
    with col2:
        network = st.selectbox("Rede Social", ["instagram", "tiktok", "youtube"])
    
    if st.button("Buscar na API", type="primary", use_container_width=True):
        if username:
            with st.spinner("Buscando perfil..."):
                resultado = api_client.buscar_profile_id(username, network)
                
                if resultado.get('success'):
                    dados = api_client.processar_dados_api(resultado.get('data', {}))
                    
                    if dados:
                        st.session_state.preview_influenciador = dados
                        st.success("Perfil encontrado!")
                    else:
                        st.error("Erro ao processar dados do perfil")
                else:
                    st.error(f"Erro: {resultado.get('error', 'Perfil nao encontrado')}")
        else:
            st.warning("Digite o username")
    
    # Preview do perfil encontrado
    if st.session_state.get('preview_influenciador'):
        dados = st.session_state.preview_influenciador
        
        st.markdown("---")
        st.subheader("Preview do Perfil")
        
        col1, col2, col3 = st.columns([1, 2, 2])
        
        with col1:
            if dados.get('foto'):
                st.image(dados['foto'], width=100)
        
        with col2:
            st.write(f"**{dados['nome']}**")
            st.write(f"@{dados['usuario']}")
            st.write(f"Rede: {dados['network'].title()}")
            st.write(f"Seguidores: {funcoes_auxiliares.formatar_numero(dados['seguidores'])}")
        
        with col3:
            st.write(f"AIR Score: **{dados['air_score']}**")
            st.write(f"Taxa Eng.: {dados['engagement_rate']:.2f}%")
            st.write(f"Classificacao: {dados['classificacao']}")
        
        if st.button("Adicionar a Base", type="primary", use_container_width=True):
            # Verificar se ja existe
            existente = data_manager.get_influenciador_por_profile_id(dados.get('profile_id', ''))
            if existente:
                st.warning("Este influenciador ja esta cadastrado na base")
            else:
                data_manager.criar_influenciador(dados)
                st.session_state.preview_influenciador = None
                st.session_state.show_add_influenciador = False
                st.success("Influenciador adicionado!")
                st.rerun()


def render_form_manual():
    """Formulario manual - campos iguais aos da API"""
    
    with st.form("form_manual"):
        st.caption("Preencha os dados conforme retornados pela API")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome *")
            usuario = st.text_input("Username *", placeholder="sem @")
            network = st.selectbox("Rede Social *", ["instagram", "tiktok", "youtube"])
            seguidores = st.number_input("Seguidores *", min_value=0, value=0)
            foto = st.text_input("URL da Foto", placeholder="https://...")
        
        with col2:
            bio = st.text_area("Bio", height=68)
            engagement_rate = st.number_input("Taxa de Engajamento (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.01)
            air_score = st.number_input("AIR Score", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            reach_rate = st.number_input("Taxa de Alcance (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.01)
        
        st.markdown("**Counters (opcional)**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_posts = st.number_input("Total Posts", min_value=0, value=0)
        with col2:
            total_likes = st.number_input("Total Likes", min_value=0, value=0)
        with col3:
            total_views = st.number_input("Total Views", min_value=0, value=0)
        with col4:
            total_comments = st.number_input("Total Comments", min_value=0, value=0)
        
        if st.form_submit_button("Salvar", use_container_width=True):
            if nome and usuario and seguidores > 0:
                dados = {
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
                    'total_likes': total_likes,
                    'total_views': total_views,
                    'total_comments': total_comments
                }
                data_manager.criar_influenciador(dados)
                st.session_state.show_add_influenciador = False
                st.success("Influenciador cadastrado!")
                st.rerun()
            else:
                st.error("Preencha os campos obrigatorios")


def render_lista_influenciadores():
    """Renderiza lista de influenciadores com todos os dados"""
    
    influenciadores = data_manager.get_influenciadores()
    
    if not influenciadores:
        st.info("Nenhum influenciador cadastrado. Clique em '+ Adicionar' para comecar.")
        return
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtro_rede = st.multiselect("Filtrar por rede", ["instagram", "tiktok", "youtube"])
    
    with col2:
        filtro_classe = st.multiselect("Filtrar por classificacao", ["Nano", "Micro", "Mid", "Macro", "Mega"])
    
    with col3:
        busca = st.text_input("Buscar por nome ou usuario")
    
    st.markdown("---")
    st.markdown(f"**{len(influenciadores)} influenciadores na base**")
    
    # Cabecalho da tabela
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.8, 2, 1, 1, 1, 1, 1, 0.8])
    
    with col1:
        st.markdown("**Foto**")
    with col2:
        st.markdown("**Nome / Usuario**")
    with col3:
        st.markdown("**Rede**")
    with col4:
        st.markdown("**Seguidores**")
    with col5:
        st.markdown("**AIR Score**")
    with col6:
        st.markdown("**Taxa Eng.**")
    with col7:
        st.markdown("**Classificacao**")
    with col8:
        st.markdown("**Acoes**")
    
    st.markdown("---")
    
    # Lista
    for inf in influenciadores:
        # Aplicar filtros
        if filtro_rede and inf['network'] not in filtro_rede:
            continue
        if filtro_classe and inf['classificacao'] not in filtro_classe:
            continue
        if busca and busca.lower() not in inf['nome'].lower() and busca.lower() not in inf['usuario'].lower():
            continue
        
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.8, 2, 1, 1, 1, 1, 1, 0.8])
        
        with col1:
            if inf.get('foto'):
                st.image(inf['foto'], width=50)
            else:
                st.write("-")
        
        with col2:
            st.write(f"**{inf['nome']}**")
            st.caption(f"@{inf['usuario']}")
        
        with col3:
            st.write(inf['network'].title())
        
        with col4:
            st.write(funcoes_auxiliares.formatar_numero(inf['seguidores']))
        
        with col5:
            st.write(f"{inf['air_score']}")
        
        with col6:
            st.write(f"{inf['engagement_rate']:.2f}%")
        
        with col7:
            st.write(inf['classificacao'])
        
        with col8:
            if st.button("...", key=f"more_{inf['id']}", help="Ver detalhes"):
                st.session_state.inf_detail_id = inf['id']
        
        # Expandir detalhes
        if st.session_state.get('inf_detail_id') == inf['id']:
            with st.expander("Detalhes", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Bio:**")
                    st.caption(inf.get('bio', '-') or '-')
                    st.write(f"**Taxa Alcance:** {inf['reach_rate']:.2f}%")
                
                with col2:
                    st.write("**Counters:**")
                    st.write(f"Posts: {inf.get('total_posts', 0):,}")
                    st.write(f"Likes: {inf.get('total_likes', 0):,}")
                    st.write(f"Views: {inf.get('total_views', 0):,}")
                    st.write(f"Comments: {inf.get('total_comments', 0):,}")
                
                with col3:
                    st.write("**Hashtags mais usadas:**")
                    hashtags = inf.get('hashtags', [])[:5]
                    if hashtags:
                        st.caption(", ".join([f"#{h}" for h in hashtags]))
                    else:
                        st.caption("-")
                    
                    st.write(f"**Profile ID:** {inf.get('profile_id', '-')}")
                    st.caption(f"Atualizado: {funcoes_auxiliares.formatar_data_br(inf.get('updated_at', ''))}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if inf.get('profile_id') and st.button("Atualizar Dados", key=f"upd_{inf['id']}", use_container_width=True):
                        atualizar_influenciador(inf)
                with col2:
                    if st.button("Fechar", key=f"close_{inf['id']}", use_container_width=True):
                        st.session_state.inf_detail_id = None
                        st.rerun()
        
        st.markdown("---")


def atualizar_influenciador(inf):
    """Atualiza dados de um influenciador via API"""
    
    if not inf.get('profile_id'):
        st.error("Este influenciador nao possui profile_id para atualizacao")
        return
    
    with st.spinner(f"Atualizando {inf['nome']}..."):
        resultado = api_client.atualizar_influenciador_api(inf['profile_id'])
        
        if resultado.get('success'):
            data_manager.atualizar_influenciador(inf['id'], resultado['data'])
            st.success("Dados atualizados!")
            st.rerun()
        else:
            st.error(f"Erro: {resultado.get('error', 'Falha na atualizacao')}")


def atualizar_todos_influenciadores():
    """Atualiza dados de todos os influenciadores com profile_id"""
    
    influenciadores = data_manager.get_influenciadores()
    com_profile_id = [i for i in influenciadores if i.get('profile_id')]
    
    if not com_profile_id:
        st.warning("Nenhum influenciador possui profile_id para atualizacao")
        return
    
    progress = st.progress(0)
    status = st.empty()
    
    for idx, inf in enumerate(com_profile_id):
        status.text(f"Atualizando {inf['nome']}...")
        resultado = api_client.atualizar_influenciador_api(inf['profile_id'])
        
        if resultado.get('success'):
            data_manager.atualizar_influenciador(inf['id'], resultado['data'])
        
        progress.progress((idx + 1) / len(com_profile_id))
    
    status.text("")
    progress.empty()
    st.success(f"{len(com_profile_id)} influenciadores atualizados!")
    st.rerun()
