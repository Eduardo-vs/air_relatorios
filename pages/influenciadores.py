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
                erros = 0
                for inf in data_manager.get_influenciadores():
                    if inf.get('profile_id'):
                        try:
                            resultado = api_client.atualizar_influenciador_api(inf['profile_id'])
                            if resultado.get('success') and resultado.get('data'):
                                # Extrair dados do resultado
                                dados_atualizados = resultado['data']
                                # Preservar campos que a API nao retorna
                                dados_atualizados['nicho'] = inf.get('nicho', '')
                                data_manager.atualizar_influenciador(inf['id'], dados_atualizados)
                                atualizados += 1
                            else:
                                erros += 1
                        except Exception as e:
                            erros += 1
                
                if atualizados > 0:
                    st.success(f"{atualizados} influenciadores atualizados!")
                if erros > 0:
                    st.warning(f"{erros} influenciadores nao puderam ser atualizados")
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
                funcoes_auxiliares.exibir_foto_influenciador(inf.get('foto'), inf.get('nome', ''), 40)
            
            with col2:
                st.write(f"**{inf['nome']}**")
                st.caption(f"@{inf['usuario']}")
            
            with col3:
                st.write(inf.get('network', '-').title())
            
            with col4:
                st.write(funcoes_auxiliares.formatar_numero(inf.get('seguidores', 0)))
            
            with col5:
                st.write(funcoes_auxiliares.formatar_air_score(inf.get('air_score', 0)))
            
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
            st.markdown("**Digite os usernames separados por virgula para adicionar varios de uma vez**")
            
            col1, col2 = st.columns(2)
            with col1:
                usernames = st.text_input("Usernames", placeholder="@usuario1, @usuario2, @usuario3")
            with col2:
                network = st.selectbox("Rede Social", ["instagram", "tiktok", "youtube"])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Buscar", use_container_width=True):
                    if usernames:
                        # Separar por virgula
                        lista_users = [u.strip().replace("@", "") for u in usernames.split(",") if u.strip()]
                        
                        if lista_users:
                            st.session_state.api_preview_list = []
                            st.session_state.api_not_found = []
                            
                            with st.spinner(f"Buscando {len(lista_users)} perfis..."):
                                for username in lista_users:
                                    resultado = api_client.buscar_profile_id(username, network)
                                    if resultado.get('success') and resultado.get('data'):
                                        dados = api_client.processar_dados_api(resultado['data'])
                                        # Validar se perfil tem dados minimos (nome ou usuario preenchido)
                                        if dados and (dados.get('nome') or dados.get('usuario')) and dados.get('seguidores', 0) > 0:
                                            st.session_state.api_preview_list.append(dados)
                                        else:
                                            st.session_state.api_not_found.append(username)
                                    else:
                                        st.session_state.api_not_found.append(username)
                            
                            # Mostrar resultados
                            if st.session_state.api_preview_list:
                                st.success(f"Encontrados {len(st.session_state.api_preview_list)} de {len(lista_users)} perfis!")
                            
                            if st.session_state.api_not_found:
                                st.error(f"Perfis nao encontrados: {', '.join(st.session_state.api_not_found)}")
                            
                            if not st.session_state.api_preview_list and not st.session_state.api_not_found:
                                st.error("Nenhum perfil encontrado")
                                
            with col2:
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.show_add_influenciador = False
                    st.session_state.api_preview_list = []
                    st.session_state.api_not_found = []
                    st.rerun()
            
            # Mostrar perfis nao encontrados
            if st.session_state.get('api_not_found'):
                st.warning(f"Nao foi possivel encontrar: {', '.join(st.session_state.api_not_found)}")
            
            # Preview de todos encontrados
            if st.session_state.get('api_preview_list'):
                st.markdown("---")
                st.markdown(f"**{len(st.session_state.api_preview_list)} perfis encontrados:**")
                
                for idx, dados in enumerate(st.session_state.api_preview_list):
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        if dados.get('foto'):
                            try:
                                st.image(dados['foto'], width=50)
                            except:
                                st.markdown("👤")
                        else:
                            st.markdown("👤")
                    with col2:
                        st.write(f"**{dados['nome']}** (@{dados['usuario']})")
                        st.caption(f"{funcoes_auxiliares.formatar_numero(dados.get('seguidores', 0))} seguidores | AIR Score: {dados.get('air_score', 0):.2f}")
                    with col3:
                        # Verificar se ja existe
                        existente = next((i for i in data_manager.get_influenciadores() 
                                         if i.get('profile_id') == dados.get('profile_id')), None)
                        if existente:
                            st.caption("Ja existe")
                        else:
                            st.caption("Novo")
                    st.markdown("---")
                
                if st.button("Adicionar Todos a Base", type="primary", use_container_width=True):
                    adicionados = 0
                    for dados in st.session_state.api_preview_list:
                        existente = next((i for i in data_manager.get_influenciadores() 
                                         if i.get('profile_id') == dados.get('profile_id')), None)
                        if not existente:
                            data_manager.criar_influenciador(dados)
                            adicionados += 1
                    
                    st.session_state.show_add_influenciador = False
                    st.session_state.api_preview_list = []
                    st.success(f"{adicionados} influenciadores adicionados!")
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
                
                st.markdown("---")
                st.markdown("**Categorias** (para filtrar insights no relatório)")
                st.caption("Separe múltiplas categorias por vírgula (ex: Cabelo Liso, Pele Clara, 25-35 anos)")
                categoria = st.text_input("Categorias:", placeholder="Ex: Cabelo Crespo, Pele Negra, 18-24 anos")
                
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
                                'categoria': categoria,
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
        
        # Secao de vinculacao de contas
        if inf.get('network') == 'instagram':
            st.markdown("**Vincular conta TikTok:**")
            # Buscar influs TikTok disponiveis
            todos_inf = data_manager.get_influenciadores()
            tiktok_disponiveis = [i for i in todos_inf if i.get('network') == 'tiktok' and i.get('id') != inf_id]
            
            if tiktok_disponiveis:
                opcoes_vinculo = ["Nenhum"] + [f"{i['nome']} (@{i['usuario']})" for i in tiktok_disponiveis]
                vinculo_atual = inf.get('vinculo_id')
                idx_atual = 0
                if vinculo_atual:
                    vinculado = next((i for i in tiktok_disponiveis if i['id'] == vinculo_atual), None)
                    if vinculado:
                        try:
                            idx_atual = opcoes_vinculo.index(f"{vinculado['nome']} (@{vinculado['usuario']})")
                        except:
                            pass
                
                vinculo_sel = st.selectbox("Conta TikTok vinculada:", opcoes_vinculo, index=idx_atual)
                
                if vinculo_sel != "Nenhum":
                    vinculo_inf = next((i for i in tiktok_disponiveis if f"{i['nome']} (@{i['usuario']})" == vinculo_sel), None)
                    if vinculo_inf and st.button("Salvar Vinculo"):
                        data_manager.atualizar_influenciador(inf_id, {'vinculo_id': vinculo_inf['id']})
                        st.success("Vinculo salvo!")
                        st.rerun()
                elif vinculo_atual and st.button("Remover Vinculo"):
                    data_manager.atualizar_influenciador(inf_id, {'vinculo_id': None})
                    st.success("Vinculo removido!")
                    st.rerun()
            else:
                st.caption("Nenhuma conta TikTok cadastrada para vincular")
            
            st.markdown("---")
        
        elif inf.get('network') == 'tiktok':
            st.markdown("**Vincular conta Instagram:**")
            todos_inf = data_manager.get_influenciadores()
            insta_disponiveis = [i for i in todos_inf if i.get('network') == 'instagram' and i.get('id') != inf_id]
            
            if insta_disponiveis:
                opcoes_vinculo = ["Nenhum"] + [f"{i['nome']} (@{i['usuario']})" for i in insta_disponiveis]
                vinculo_atual = inf.get('vinculo_id')
                idx_atual = 0
                if vinculo_atual:
                    vinculado = next((i for i in insta_disponiveis if i['id'] == vinculo_atual), None)
                    if vinculado:
                        try:
                            idx_atual = opcoes_vinculo.index(f"{vinculado['nome']} (@{vinculado['usuario']})")
                        except:
                            pass
                
                vinculo_sel = st.selectbox("Conta Instagram vinculada:", opcoes_vinculo, index=idx_atual)
                
                if vinculo_sel != "Nenhum":
                    vinculo_inf = next((i for i in insta_disponiveis if f"{i['nome']} (@{i['usuario']})" == vinculo_sel), None)
                    if vinculo_inf and st.button("Salvar Vinculo"):
                        data_manager.atualizar_influenciador(inf_id, {'vinculo_id': vinculo_inf['id']})
                        st.success("Vinculo salvo!")
                        st.rerun()
                elif vinculo_atual and st.button("Remover Vinculo"):
                    data_manager.atualizar_influenciador(inf_id, {'vinculo_id': None})
                    st.success("Vinculo removido!")
                    st.rerun()
            else:
                st.caption("Nenhuma conta Instagram cadastrada para vincular")
            
            st.markdown("---")
        
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
            
            st.markdown("---")
            st.markdown("**Categorias** (para filtrar insights no relatório)")
            st.caption("Separe múltiplas categorias por vírgula (ex: Cabelo Liso, Pele Clara, 25-35 anos)")
            categoria = st.text_input("Categorias:", value=inf.get('categoria', ''), 
                                     placeholder="Ex: Cabelo Crespo, Pele Negra, 18-24 anos")
            
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
                            'categoria': categoria,
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
