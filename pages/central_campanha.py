"""
Pagina: Central da Campanha
Gerenciamento de influenciadores, posts e configuracoes da campanha
"""

import streamlit as st
from datetime import datetime, timedelta
import base64
from utils import data_manager, funcoes_auxiliares, api_client

def render():
    """Renderiza central de controle da campanha"""
    
    campanha = data_manager.get_campanha(st.session_state.campanha_atual_id)
    
    if not campanha:
        st.warning("Selecione uma campanha na barra lateral")
        return
    
    # Header
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        aon_badge = "[AON]" if campanha.get('is_aon') else ""
        st.markdown(f'<p class="main-header">Central: {campanha["nome"]} {aon_badge}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="subtitle">{campanha.get("cliente_nome", "")} | {funcoes_auxiliares.formatar_data_br(campanha["data_inicio"])} - {funcoes_auxiliares.formatar_data_br(campanha["data_fim"])}</p>', unsafe_allow_html=True)
    with col2:
        # Exportar CSV normal
        influenciadores_data = data_manager.get_influenciadores_campanha(campanha['id'])
        csv_data = funcoes_auxiliares.exportar_campanha_csv(campanha, influenciadores_data)
        st.download_button(
            "CSV Campanha",
            data=csv_data,
            file_name=f"{campanha['nome']}_dados.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col3:
        # Exportar CSV Balizadores
        csv_balizadores = funcoes_auxiliares.exportar_csv_balizadores(campanha, influenciadores_data)
        st.download_button(
            "CSV Balizadores",
            data=csv_balizadores,
            file_name=f"{campanha['nome']}_balizadores.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col4:
        if st.button("Ver Relatorio", type="primary", use_container_width=True):
            st.session_state.modo_relatorio = 'campanha'
            st.session_state.current_page = 'Relatorios'
            st.rerun()
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Influenciadores e Posts",
        "Configuracoes da Campanha",
        "Configurar Insights",
        "Comentarios",
        "Categorias de Comentarios"
    ])
    
    with tab1:
        render_influenciadores_posts(campanha)
    
    with tab2:
        render_configuracoes_campanha(campanha)
    
    with tab3:
        render_configurar_insights(campanha)
    
    with tab4:
        render_comentarios(campanha)
    
    with tab5:
        render_categorias_comentarios(campanha)


def render_influenciadores_posts(campanha):
    """Gerencia influenciadores e posts da campanha"""
    
    st.subheader("Influenciadores da Campanha")
    
    if st.button("+ Adicionar Influenciador", use_container_width=False):
        st.session_state.show_add_inf_to_campaign = True
    
    if st.session_state.get('show_add_inf_to_campaign', False):
        render_modal_add_influenciador(campanha)
    
    st.markdown("---")
    
    influenciadores = data_manager.get_influenciadores_campanha(campanha['id'])
    
    if not influenciadores:
        st.info("Nenhum influenciador adicionado a campanha")
        return
    
    for inf in influenciadores:
        with st.expander(f"{inf['nome']} (@{inf['usuario']}) - {inf['classificacao']} - {len(inf['posts'])} posts"):
            col1, col2, col3, col4 = st.columns([1, 2, 2, 1.5])
            
            with col1:
                if inf.get('foto'):
                    st.image(inf['foto'], width=80)
            
            with col2:
                st.write(f"**Seguidores:** {funcoes_auxiliares.formatar_numero(inf['seguidores'])}")
                st.write(f"**AIR Score:** {inf['air_score']:.2f}")
                st.write(f"**Taxa Eng.:** {inf['engagement_rate']:.2f}%")
            
            with col3:
                st.write(f"**Rede:** {inf['network'].title()}")
                st.write(f"**Classificacao:** {inf['classificacao']}")
                if inf.get('nicho'):
                    st.write(f"**Nicho:** {inf['nicho']}")
                if campanha['tipo_dados'] == 'estatico':
                    st.caption("Dados congelados (campanha estatica)")
            
            with col4:
                # CUSTO POR INFLUENCIADOR NA CAMPANHA
                custo_atual = inf.get('custo_campanha', 0)
                novo_custo = st.number_input(
                    "Custo (R$)",
                    min_value=0.0,
                    value=float(custo_atual),
                    step=100.0,
                    key=f"custo_inf_{inf['id']}"
                )
                if novo_custo != custo_atual:
                    if st.button("Salvar Custo", key=f"salvar_custo_{inf['id']}"):
                        data_manager.atualizar_custo_influenciador_campanha(
                            campanha['id'], inf['id'], novo_custo
                        )
                        st.success("Custo salvo!")
                        st.rerun()
            
            st.markdown("---")
            st.markdown("**Posts:**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("+ Buscar Posts na API", key=f"api_post_{inf['id']}"):
                    st.session_state.show_api_post_inf = inf['id']
                    st.session_state.show_manual_post_inf = None
            with col2:
                if st.button("+ Adicionar Manualmente", key=f"manual_post_{inf['id']}"):
                    st.session_state.show_manual_post_inf = inf['id']
                    st.session_state.show_api_post_inf = None
            
            # Form API posts
            if st.session_state.get('show_api_post_inf') == inf['id']:
                render_form_post_api(campanha, inf)
            
            # Form manual
            if st.session_state.get('show_manual_post_inf') == inf['id']:
                render_form_post_manual(campanha, inf)
            
            # Lista de posts
            if inf['posts']:
                for idx, post in enumerate(inf['posts']):
                    post_key = f"post_{inf['id']}_{idx}"
                    
                    # Verificar se está editando este post
                    if st.session_state.get(f'editing_post_{post_key}'):
                        render_form_editar_post(campanha, inf, idx, post)
                    else:
                        col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1, 1, 1, 0.5, 0.8])
                        
                        with col1:
                            st.write(f"**{post['formato']}** ({post['plataforma']})")
                            st.caption(post['data_publicacao'])
                            if post.get('link_post'):
                                st.markdown(f"[Link]({post['link_post']})")
                        
                        with col2:
                            st.caption("Impressoes")
                            impressoes = post.get('impressoes', 0) + post.get('views', 0)
                            st.write(f"{impressoes:,}".replace(",", "."))
                        
                        with col3:
                            st.caption("Alcance")
                            st.write(f"{post.get('alcance', 0):,}".replace(",", "."))
                        
                        with col4:
                            st.caption("Interacoes")
                            st.write(f"{post.get('interacoes', 0):,}".replace(",", "."))
                        
                        with col5:
                            if post.get('imagens') and len(post['imagens']) > 0:
                                try:
                                    img = post['imagens'][0]
                                    if img.startswith('http'):
                                        st.image(img, width=50)
                                except:
                                    pass
                        
                        with col6:
                            col_edit, col_del = st.columns(2)
                            with col_edit:
                                if st.button("✏️", key=f"edit_{post_key}", help="Editar"):
                                    st.session_state[f'editing_post_{post_key}'] = True
                                    st.rerun()
                            with col_del:
                                if st.button("🗑️", key=f"del_{post_key}", help="Excluir"):
                                    data_manager.remover_post_campanha(campanha['id'], inf['id'], idx)
                                    st.success("Post removido!")
                                    st.rerun()
                        
                        st.markdown("---")
            else:
                st.caption("Nenhum post cadastrado")
            
            if st.button("Remover da Campanha", key=f"rem_inf_{inf['id']}", type="secondary"):
                data_manager.remover_influenciador_campanha(campanha['id'], inf['id'])
                st.success("Influenciador removido!")
                st.rerun()


def render_form_post_api(campanha, inf):
    """Formulario para buscar posts via API"""
    
    st.markdown("---")
    st.markdown("#### Buscar Posts na API")
    
    inf_id = inf['id']
    
    # Inicializar estados
    if f'api_posts_sel_{inf_id}' not in st.session_state:
        st.session_state[f'api_posts_sel_{inf_id}'] = []
    if f'api_result_{inf_id}' not in st.session_state:
        st.session_state[f'api_result_{inf_id}'] = None
    if f'busca_tipo_{inf_id}' not in st.session_state:
        st.session_state[f'busca_tipo_{inf_id}'] = 'filtros'
    if f'api_filters_{inf_id}' not in st.session_state:
        st.session_state[f'api_filters_{inf_id}'] = {
            'profile_id': inf.get('profile_id'),
            'start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'post_types': ['post', 'reel'],
            'text': ''
        }
    
    # SLIDE PARA ALTERNAR TIPO DE BUSCA
    st.markdown("**Tipo de Busca:**")
    tipo_busca = st.radio(
        "Selecione o modo de busca:",
        ["Por Filtros (data, tipo, texto)", "Por Link do Post"],
        horizontal=True,
        key=f"tipo_busca_radio_{inf_id}",
        index=0 if st.session_state[f'busca_tipo_{inf_id}'] == 'filtros' else 1
    )
    
    st.session_state[f'busca_tipo_{inf_id}'] = 'filtros' if 'Filtros' in tipo_busca else 'link'
    
    st.markdown("---")
    
    if st.session_state[f'busca_tipo_{inf_id}'] == 'filtros':
        # BUSCA POR FILTROS (modo original)
        render_busca_por_filtros(campanha, inf)
    else:
        # BUSCA POR LINK
        render_busca_por_link(campanha, inf)


def render_busca_por_filtros(campanha, inf):
    """Busca de posts por filtros de data, tipo e texto"""
    
    inf_id = inf['id']
    filters = st.session_state[f'api_filters_{inf_id}']
    
    st.markdown("**Filtros:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        start_date = st.date_input(
            "Data Inicio", 
            value=datetime.strptime(filters['start_date'], '%Y-%m-%d'),
            key=f"di_{inf_id}"
        )
    with col2:
        end_date = st.date_input(
            "Data Fim", 
            value=datetime.strptime(filters['end_date'], '%Y-%m-%d'),
            key=f"df_{inf_id}"
        )
    with col3:
        post_types = st.multiselect(
            "Tipos", 
            ["post", "reel", "story"], 
            default=filters['post_types'],
            key=f"types_{inf_id}"
        )
    with col4:
        text_filter = st.text_input(
            "Texto", 
            value=filters['text'],
            placeholder="Ex: pantene", 
            key=f"text_{inf_id}"
        )
    
    # Funcao para buscar posts
    def buscar_pagina(pagina):
        resultado = api_client.buscar_posts(
            profile_id=filters['profile_id'],
            start_date=filters['start_date'],
            end_date=filters['end_date'],
            post_types=filters['post_types'] if filters['post_types'] else None,
            text=filters['text'] if filters['text'] else None,
            page=pagina
        )
        return resultado
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Buscar Posts", use_container_width=True, key=f"buscar_{inf_id}"):
            st.session_state[f'api_filters_{inf_id}'] = {
                'profile_id': inf.get('profile_id'),
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'post_types': post_types if post_types else ['post', 'reel'],
                'text': text_filter
            }
            
            with st.spinner("Buscando posts..."):
                profile_id = inf.get('profile_id')
                if profile_id:
                    resultado = api_client.buscar_posts(
                        profile_id=profile_id,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        post_types=post_types if post_types else None,
                        text=text_filter if text_filter else None,
                        page=0
                    )
                    
                    if resultado.get('success'):
                        st.session_state[f'api_result_{inf_id}'] = resultado.get('data', {})
                        st.success(f"Encontrados {resultado.get('data', {}).get('count', 0)} posts!")
                        st.rerun()
                    else:
                        st.error(f"Erro: {resultado.get('error', 'Erro desconhecido')}")
                else:
                    st.error("Influenciador sem profile_id")
    
    with col2:
        if st.button("Cancelar", use_container_width=True, key=f"cancel_{inf_id}"):
            st.session_state.show_api_post_inf = None
            st.session_state[f'api_result_{inf_id}'] = None
            st.session_state[f'api_posts_sel_{inf_id}'] = []
            st.rerun()
    
    # Exibir resultados
    render_resultados_api(campanha, inf, buscar_pagina)


def render_busca_por_link(campanha, inf):
    """Busca de post por link (permalink)"""
    
    inf_id = inf['id']
    
    st.markdown("**Cole o link do post:**")
    link_post = st.text_input(
        "Link do Post",
        placeholder="https://www.instagram.com/p/ABC123...",
        key=f"link_post_{inf_id}"
    )
    
    # Validar link
    link_valido = False
    if link_post:
        if 'instagram.com' in link_post or 'tiktok.com' in link_post or 'youtube.com' in link_post:
            link_valido = True
    
    col1, col2 = st.columns(2)
    
    with col1:
        buscar_disabled = not link_valido
        if st.button("Buscar Post", use_container_width=True, key=f"buscar_link_{inf_id}", disabled=buscar_disabled):
            with st.spinner("Buscando post... (pode levar alguns segundos)"):
                profile_id = inf.get('profile_id')
                if profile_id:
                    # Buscar de 30 em 30 dias ate encontrar
                    resultado = buscar_post_por_link(profile_id, link_post)
                    
                    if resultado:
                        st.session_state[f'api_result_{inf_id}'] = {'items': [resultado], 'count': 1, 'pages': 1}
                        st.success("Post encontrado!")
                        st.rerun()
                    else:
                        st.error("Post nao encontrado. Verifique o link ou tente busca por filtros.")
                else:
                    st.error("Influenciador sem profile_id")
    
    with col2:
        if st.button("Cancelar", use_container_width=True, key=f"cancel_link_{inf_id}"):
            st.session_state.show_api_post_inf = None
            st.session_state[f'api_result_{inf_id}'] = None
            st.session_state[f'api_posts_sel_{inf_id}'] = []
            st.rerun()
    
    if not link_valido and link_post:
        st.warning("Insira um link valido do Instagram, TikTok ou YouTube")
    
    # Exibir resultado se encontrado
    result = st.session_state.get(f'api_result_{inf_id}')
    if result and result.get('items'):
        render_resultados_api(campanha, inf, lambda p: result)


def extrair_post_id_do_link(link: str) -> str:
    """
    Extrai o ID do post de diferentes formatos de URL do Instagram
    Exemplos:
    - https://www.instagram.com/reel/DRvG5iMD5fx
    - https://www.instagram.com/oboticario/reel/DRvG5iMD5fx/?hl=pt-br
    - https://www.instagram.com/p/ABC123/
    - https://www.instagram.com/user/p/ABC123/?hl=pt
    """
    import re
    
    if not link:
        return ''
    
    # Remover parametros de query
    link_limpo = link.split('?')[0]
    
    # Padroes para extrair o ID do post
    padroes = [
        r'/reel/([A-Za-z0-9_-]+)',      # /reel/DRvG5iMD5fx
        r'/p/([A-Za-z0-9_-]+)',          # /p/ABC123
        r'/tv/([A-Za-z0-9_-]+)',         # /tv/ABC123
    ]
    
    for padrao in padroes:
        match = re.search(padrao, link_limpo)
        if match:
            return match.group(1)
    
    return ''


def buscar_post_por_link(profile_id: str, link: str, max_dias: int = 365) -> dict:
    """
    Busca post por link fazendo requisicoes de 30 em 30 dias
    ate encontrar o post com o permalink correspondente
    """
    
    # Extrair ID do post do link fornecido pelo usuario
    post_id_buscado = extrair_post_id_do_link(link)
    
    if not post_id_buscado:
        st.warning(f"Nao foi possivel extrair ID do link: {link}")
        return None
    
    data_fim = datetime.now()
    dias_buscados = 0
    
    while dias_buscados < max_dias:
        data_inicio = data_fim - timedelta(days=30)
        
        resultado = api_client.buscar_posts(
            profile_id=profile_id,
            start_date=data_inicio.strftime('%Y-%m-%d'),
            end_date=data_fim.strftime('%Y-%m-%d'),
            post_types=None,
            text=None,
            page=0
        )
        
        if resultado.get('success'):
            data = resultado.get('data', {})
            items = data.get('items', [])
            total_pages = data.get('pages', 1)
            
            # Buscar em todas as paginas deste periodo
            for page in range(total_pages):
                if page > 0:
                    resultado = api_client.buscar_posts(
                        profile_id=profile_id,
                        start_date=data_inicio.strftime('%Y-%m-%d'),
                        end_date=data_fim.strftime('%Y-%m-%d'),
                        post_types=None,
                        text=None,
                        page=page
                    )
                    items = resultado.get('data', {}).get('items', [])
                
                for post in items:
                    # Tentar varias formas de pegar o link do post
                    permalink = post.get('permalink', '') or post.get('link', '') or post.get('url', '')
                    
                    # Se nao tem permalink, tentar construir a partir do shortcode
                    if not permalink:
                        shortcode = post.get('shortcode', '') or post.get('code', '')
                        if shortcode:
                            permalink = f"https://www.instagram.com/p/{shortcode}/"
                    
                    # Extrair o ID do permalink da API
                    post_id_api = extrair_post_id_do_link(permalink)
                    
                    # Tambem tentar comparar diretamente com shortcode
                    shortcode = post.get('shortcode', '') or post.get('code', '')
                    
                    # Comparar os IDs extraidos ou shortcode
                    if post_id_buscado:
                        if (post_id_api and post_id_buscado == post_id_api) or \
                           (shortcode and post_id_buscado == shortcode):
                            return post
        
        # Avancar para o periodo anterior
        data_fim = data_inicio
        dias_buscados += 30
    
    return None


def render_resultados_api(campanha, inf, buscar_pagina_func):
    """Renderiza resultados da API"""
    
    inf_id = inf['id']
    result = st.session_state[f'api_result_{inf_id}']
    
    if not result:
        return
    
    col_posts, col_selecionados = st.columns([3, 2])
    
    with col_posts:
        st.markdown("**Posts Encontrados:**")
        
        items = result.get('items', [])
        total_pages = result.get('pages', 1)
        current_page = result.get('current_page', 0)
        
        # Paginacao
        if total_pages > 1:
            col_prev, col_info, col_next = st.columns([1, 2, 1])
            with col_prev:
                if current_page > 0:
                    if st.button("< Anterior", key=f"prev_{inf_id}", use_container_width=True):
                        with st.spinner("Carregando..."):
                            resultado = buscar_pagina_func(current_page - 1)
                            if resultado.get('success'):
                                st.session_state[f'api_result_{inf_id}'] = resultado.get('data', {})
                                st.rerun()
            with col_info:
                st.markdown(f"<p style='text-align:center'><b>Pagina {current_page + 1} de {total_pages}</b></p>", unsafe_allow_html=True)
            with col_next:
                if current_page < total_pages - 1:
                    if st.button("Proximo >", key=f"next_{inf_id}", use_container_width=True):
                        with st.spinner("Carregando..."):
                            resultado = buscar_pagina_func(current_page + 1)
                            if resultado.get('success'):
                                st.session_state[f'api_result_{inf_id}'] = resultado.get('data', {})
                                st.rerun()
        
        # Container com scroll
        posts_container = st.container(height=400)
        
        with posts_container:
            posts_selecionados = st.session_state[f'api_posts_sel_{inf_id}']
            ids_selecionados = [p.get('post_id') for p in posts_selecionados]
            
            for post in items:
                post_id = post.get('post_id')
                is_selected = post_id in ids_selecionados
                
                col_a, col_b, col_c = st.columns([1, 3, 1])
                
                with col_a:
                    if post.get('thumbnail'):
                        st.image(post['thumbnail'], width=60)
                
                with col_b:
                    legenda = post.get('caption', '')[:80] + '...' if len(post.get('caption', '')) > 80 else post.get('caption', '')
                    st.write(f"**{post.get('type', '')}** - {post.get('posted_at', '')[:10]}")
                    st.caption(legenda if legenda else "(sem legenda)")
                    st.caption(f"Views: {post.get('counters', {}).get('views', 0):,} | Likes: {post.get('counters', {}).get('likes', 0):,}")
                
                with col_c:
                    if is_selected:
                        st.success("Selecionado")
                    else:
                        if st.button("+ Add", key=f"sel_{inf_id}_{post_id}"):
                            st.session_state[f'api_posts_sel_{inf_id}'].append(post)
                            st.rerun()
                
                st.divider()
    
    with col_selecionados:
        st.markdown("**Posts Selecionados:**")
        
        posts_selecionados = st.session_state[f'api_posts_sel_{inf_id}']
        
        sel_container = st.container(height=400)
        
        with sel_container:
            if posts_selecionados:
                for idx, post in enumerate(posts_selecionados):
                    col_a, col_b, col_c = st.columns([1, 2, 1])
                    
                    with col_a:
                        if post.get('thumbnail'):
                            st.image(post['thumbnail'], width=40)
                    
                    with col_b:
                        legenda = post.get('caption', '')[:40] + '...' if len(post.get('caption', '')) > 40 else post.get('caption', '')
                        st.caption(f"{post.get('type', '')} - {post.get('posted_at', '')[:10]}")
                        st.caption(legenda if legenda else "(sem legenda)")
                    
                    with col_c:
                        if st.button("X", key=f"rem_{inf_id}_{idx}"):
                            st.session_state[f'api_posts_sel_{inf_id}'].pop(idx)
                            st.rerun()
                    
                    st.divider()
            else:
                st.info("Selecione posts na lista ao lado")
        
        # Botao de adicionar
        if posts_selecionados:
            st.markdown(f"**{len(posts_selecionados)} posts selecionados**")
            if st.button("Adicionar Posts a Campanha", type="primary", use_container_width=True, key=f"add_all_{inf_id}"):
                count = len(posts_selecionados)
                for post in posts_selecionados:
                    post_processado = api_client.processar_post_api(post)
                    data_manager.adicionar_post(campanha['id'], inf['id'], post_processado)
                
                st.session_state.show_api_post_inf = None
                st.session_state[f'api_result_{inf_id}'] = None
                st.session_state[f'api_posts_sel_{inf_id}'] = []
                st.success(f"{count} posts adicionados!")
                st.rerun()


def render_form_post_manual(campanha, inf):
    """Formulario para adicionar post manualmente"""
    
    st.markdown("---")
    st.markdown("#### Adicionar Post Manualmente")
    
    metricas_config = campanha.get('metricas_selecionadas', {})
    
    with st.form(f"form_post_manual_{inf['id']}"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            formato = st.selectbox("Formato *", ["Reels", "Stories", "Carrossel", "Feed", "TikTok", "YouTube"])
            plataforma = st.selectbox("Plataforma", ["Instagram", "TikTok", "YouTube"])
        
        with col2:
            data_pub = st.date_input("Data Publicacao *")
            link_post = st.text_input("Link do Post")
        
        with col3:
            views = st.number_input("Views", min_value=0, value=0)
            alcance = st.number_input("Alcance", min_value=0, value=0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            interacoes = st.number_input("Interacoes", min_value=0, value=0)
            impressoes = st.number_input("Impressoes", min_value=0, value=0)
        with col2:
            curtidas = st.number_input("Curtidas", min_value=0, value=0)
            comentarios_qtd = st.number_input("Comentarios", min_value=0, value=0)
        with col3:
            compartilhamentos = st.number_input("Compartilhamentos", min_value=0, value=0)
            saves = st.number_input("Salvamentos", min_value=0, value=0)
        
        # Metricas opcionais
        col1, col2 = st.columns(2)
        with col1:
            clique_link = st.number_input("Cliques no Link", min_value=0, value=0) if metricas_config.get('clique_link') else 0
        with col2:
            cupom_conversoes = st.number_input("Conversoes Cupom", min_value=0, value=0) if metricas_config.get('cupom_conversoes') else 0
        
        col1, col2 = st.columns(2)
        submitted = col1.form_submit_button("Adicionar Post", use_container_width=True, type="primary")
        cancel = col2.form_submit_button("Cancelar", use_container_width=True)
        
        if submitted:
            post_data = {
                'formato': formato,
                'plataforma': plataforma,
                'data_publicacao': data_pub.strftime('%d/%m/%Y'),
                'link_post': link_post,
                'views': views,
                'alcance': alcance,
                'interacoes': interacoes,
                'impressoes': impressoes,
                'curtidas': curtidas,
                'comentarios_qtd': comentarios_qtd,
                'compartilhamentos': compartilhamentos,
                'saves': saves,
                'clique_link': clique_link,
                'cupom_conversoes': cupom_conversoes,
                'imagens': []
            }
            
            data_manager.adicionar_post(campanha['id'], inf['id'], post_data)
            st.session_state.show_manual_post_inf = None
            st.success("Post adicionado!")
            st.rerun()
        
        if cancel:
            st.session_state.show_manual_post_inf = None
            st.rerun()


def render_modal_add_influenciador(campanha):
    """Modal para adicionar influenciador a campanha"""
    
    st.markdown("---")
    st.markdown("#### Adicionar Influenciadores")
    
    # Influenciadores ja na campanha
    inf_na_campanha = [inf['id'] for inf in data_manager.get_influenciadores_campanha(campanha['id'])]
    
    # Buscar da base
    todos_inf = data_manager.get_influenciadores()
    disponiveis = [inf for inf in todos_inf if inf['id'] not in inf_na_campanha]
    
    if disponiveis:
        # Criar opcoes para multiselect
        opcoes = {f"{inf['nome']} (@{inf['usuario']}) - {inf.get('classificacao', 'N/A')}": inf['id'] for inf in disponiveis}
        
        selecionados = st.multiselect(
            "Selecione os influenciadores:",
            list(opcoes.keys()),
            placeholder="Escolha um ou mais influenciadores..."
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if selecionados:
                if st.button(f"Adicionar {len(selecionados)} influenciador(es)", type="primary", use_container_width=True):
                    for sel in selecionados:
                        inf_id = opcoes[sel]
                        data_manager.adicionar_influenciador_campanha(campanha['id'], inf_id)
                    st.session_state.show_add_inf_to_campaign = False
                    st.success(f"{len(selecionados)} influenciador(es) adicionado(s)!")
                    st.rerun()
        
        with col2:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.show_add_inf_to_campaign = False
                st.rerun()
    else:
        st.info("Todos os influenciadores ja estao na campanha ou nao ha influenciadores cadastrados.")
        if st.button("Fechar"):
            st.session_state.show_add_inf_to_campaign = False
            st.rerun()


def render_configuracoes_campanha(campanha):
    """Configuracoes gerais da campanha"""
    
    st.subheader("Configuracoes")
    
    with st.form("form_config_campanha"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome da Campanha *", value=campanha['nome'])
            objetivo = st.text_area("Objetivo", value=campanha.get('objetivo', ''))
            is_aon = st.checkbox("Campanha AON", value=campanha.get('is_aon', False))
        
        with col2:
            data_inicio = st.date_input(
                "Data Inicio",
                value=data_manager.parse_data_flexivel(campanha.get('data_inicio', '')) if campanha.get('data_inicio') else datetime.now()
            )
            data_fim = st.date_input(
                "Data Fim",
                value=data_manager.parse_data_flexivel(campanha.get('data_fim', '')) if campanha.get('data_fim') else datetime.now()
            )
            tipo_dados = st.selectbox(
                "Tipo de Dados",
                ["estatico", "dinamico"],
                index=0 if campanha.get('tipo_dados') == 'estatico' else 1
            )
        
        st.markdown("---")
        st.markdown("**Estimativas da Campanha:**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            estimativa_alcance = st.number_input(
                "Estimativa de Alcance",
                min_value=0,
                value=campanha.get('estimativa_alcance', 0)
            )
        with col2:
            estimativa_impressoes = st.number_input(
                "Estimativa de Impressoes/Views",
                min_value=0,
                value=campanha.get('estimativa_impressoes', 0)
            )
        with col3:
            investimento_total = st.number_input(
                "Investimento Total (R$)",
                min_value=0.0,
                value=float(campanha.get('investimento_total', 0)),
                step=1000.0
            )
        
        st.markdown("---")
        st.markdown("**Metricas a Coletar:**")
        
        metricas = campanha.get('metricas_selecionadas', {})
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            m_views = st.checkbox("Views", value=metricas.get('views', True))
            m_alcance = st.checkbox("Alcance", value=metricas.get('alcance', True))
        with col2:
            m_interacoes = st.checkbox("Interacoes", value=metricas.get('interacoes', True))
            m_impressoes = st.checkbox("Impressoes", value=metricas.get('impressoes', True))
        with col3:
            m_curtidas = st.checkbox("Curtidas", value=metricas.get('curtidas', True))
            m_comentarios = st.checkbox("Comentarios", value=metricas.get('comentarios', True))
        with col4:
            m_compartilhamentos = st.checkbox("Compartilhamentos", value=metricas.get('compartilhamentos', True))
            m_saves = st.checkbox("Salvamentos", value=metricas.get('saves', True))
        
        col1, col2 = st.columns(2)
        with col1:
            m_clique_link = st.checkbox("Cliques no Link", value=metricas.get('clique_link', False))
        with col2:
            m_cupom = st.checkbox("Conversoes por Cupom", value=metricas.get('cupom_conversoes', False))
        
        submitted = st.form_submit_button("Salvar Configuracoes", type="primary", use_container_width=True)
        
        if submitted:
            novas_metricas = {
                'views': m_views,
                'alcance': m_alcance,
                'interacoes': m_interacoes,
                'impressoes': m_impressoes,
                'curtidas': m_curtidas,
                'comentarios': m_comentarios,
                'compartilhamentos': m_compartilhamentos,
                'saves': m_saves,
                'clique_link': m_clique_link,
                'cupom_conversoes': m_cupom
            }
            
            data_manager.atualizar_campanha(campanha['id'], {
                'nome': nome,
                'objetivo': objetivo,
                'data_inicio': data_inicio.strftime('%Y-%m-%d'),
                'data_fim': data_fim.strftime('%Y-%m-%d'),
                'tipo_dados': tipo_dados,
                'is_aon': is_aon,
                'metricas_selecionadas': novas_metricas,
                'estimativa_alcance': estimativa_alcance,
                'estimativa_impressoes': estimativa_impressoes,
                'investimento_total': investimento_total
            })
            
            st.success("Configuracoes salvas!")
            st.rerun()


def render_configurar_insights(campanha):
    """Gestão completa de insights do relatório por página"""
    import requests
    import time
    
    WEBHOOK_IA_URL = "https://n8n.air.com.vc/webhook/e19fe530-62b6-44af-b6d1-3aeed59cfe0b"
    
    st.subheader("Gestao de Insights")
    st.caption("Gerencie os insights que aparecem em cada pagina do relatorio")
    
    campanha_id = campanha['id']
    
    # Páginas disponíveis
    PAGINAS = {
        'big_numbers': 'Big Numbers',
        'visao_aon': 'Visao AON',
        'kpis_influenciador': 'KPIs por Influenciador',
        'top_performance': 'Top Performance'
    }
    
    # Botão para gerar insights de todas as páginas
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**Gerar insights para todas as paginas de uma vez:**")
    with col2:
        if st.button("Gerar Todos com IA", type="primary", use_container_width=True):
            st.session_state['gerando_todos'] = True
            st.rerun()
    
    # Processar geração de todos
    if st.session_state.get('gerando_todos', False):
        st.markdown("---")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        dados = preparar_dados_para_ia(campanha)
        total_paginas = len(PAGINAS)
        
        for idx, (pagina_key, pagina_nome) in enumerate(PAGINAS.items()):
            status_text.text(f"Gerando insights para {pagina_nome}...")
            progress_bar.progress((idx) / total_paginas)
            
            try:
                payload = {
                    "pagina": pagina_key,
                    "campanha_id": campanha_id,
                    "dados": dados,
                    "timestamp": datetime.now().isoformat()
                }
                
                response = requests.post(
                    WEBHOOK_IA_URL,
                    json=payload,
                    timeout=120,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    resultado = response.json()
                    insights = extrair_insights_resposta(resultado)
                    
                    if insights:
                        data_manager.atualizar_insights_ia(campanha_id, pagina_key, insights)
                        st.success(f"{pagina_nome}: {len(insights)} insights gerados")
                    else:
                        st.warning(f"{pagina_nome}: Nenhum insight na resposta")
                else:
                    st.error(f"{pagina_nome}: Erro HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                st.error(f"{pagina_nome}: Timeout")
            except Exception as e:
                st.error(f"{pagina_nome}: Erro - {str(e)[:50]}")
        
        progress_bar.progress(1.0)
        status_text.text("Concluido!")
        st.session_state['gerando_todos'] = False
        time.sleep(1)
        st.rerun()
    
    st.markdown("---")
    
    # Selecionar página individual
    pagina_selecionada = st.selectbox(
        "Selecione a pagina para gerenciar:",
        options=list(PAGINAS.keys()),
        format_func=lambda x: PAGINAS[x]
    )
    
    # Botões de ação para página individual
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Gerar com IA", use_container_width=True):
            st.session_state[f'gerando_ia_{pagina_selecionada}'] = True
            st.rerun()
    
    with col2:
        if st.button("Adicionar Manual", use_container_width=True):
            st.session_state[f'adicionando_insight_{pagina_selecionada}'] = True
            st.rerun()
    
    with col3:
        mostrar_excluidos = st.checkbox("Mostrar excluidos", key=f"mostrar_exc_{pagina_selecionada}")
    
    # Processar geração de IA para página individual
    if st.session_state.get(f'gerando_ia_{pagina_selecionada}', False):
        with st.spinner(f"Gerando insights para {PAGINAS[pagina_selecionada]}..."):
            dados = preparar_dados_para_ia(campanha)
            
            try:
                payload = {
                    "pagina": pagina_selecionada,
                    "campanha_id": campanha_id,
                    "dados": dados,
                    "timestamp": datetime.now().isoformat()
                }
                
                response = requests.post(
                    WEBHOOK_IA_URL,
                    json=payload,
                    timeout=120,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    resultado = response.json()
                    insights = extrair_insights_resposta(resultado)
                    
                    if insights:
                        data_manager.atualizar_insights_ia(campanha_id, pagina_selecionada, insights)
                        st.success(f"{len(insights)} insights gerados!")
                    else:
                        st.error("Nenhum insight encontrado na resposta")
                else:
                    st.error(f"Erro HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                st.error("Timeout - A IA demorou muito para responder")
            except Exception as e:
                st.error(f"Erro: {e}")
        
        st.session_state[f'gerando_ia_{pagina_selecionada}'] = False
        time.sleep(1)
        st.rerun()
    
    # Formulário para adicionar insight manualmente
    if st.session_state.get(f'adicionando_insight_{pagina_selecionada}', False):
        st.markdown("---")
        st.markdown("**Adicionar Insight Manual**")
        
        with st.form(f"form_add_insight_{pagina_selecionada}"):
            col1, col2 = st.columns(2)
            with col1:
                tipo = st.selectbox("Tipo:", ['sucesso', 'alerta', 'info', 'destaque', 'critico'])
            with col2:
                pass
            
            titulo = st.text_input("Titulo:", placeholder="Ex: Meta de Impressoes Superada")
            texto = st.text_area("Texto:", placeholder="Descricao detalhada do insight...", height=150)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Salvar", type="primary", use_container_width=True):
                    if titulo and texto:
                        data_manager.adicionar_insight(campanha_id, pagina_selecionada, {
                            'tipo': tipo,
                            'icone': '',
                            'titulo': titulo,
                            'texto': texto
                        }, fonte='manual')
                        st.session_state[f'adicionando_insight_{pagina_selecionada}'] = False
                        st.success("Insight adicionado!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.warning("Preencha titulo e texto")
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state[f'adicionando_insight_{pagina_selecionada}'] = False
                    st.rerun()
    
    # Listar insights existentes
    st.markdown("---")
    st.markdown(f"**Insights - {PAGINAS[pagina_selecionada]}**")
    
    insights = data_manager.get_insights_campanha(campanha_id, pagina_selecionada, apenas_ativos=not mostrar_excluidos)
    
    if not insights:
        st.info("Nenhum insight cadastrado para esta pagina.")
    else:
        for insight in insights:
            render_card_insight_editavel(insight, campanha_id, pagina_selecionada)


def extrair_insights_resposta(resultado) -> list:
    """Extrai insights da resposta do webhook n8n"""
    # Formato: [{"output": {"insights": [...]}}]
    if isinstance(resultado, list) and len(resultado) > 0:
        primeiro = resultado[0]
        if isinstance(primeiro, dict):
            if 'output' in primeiro and 'insights' in primeiro['output']:
                return primeiro['output']['insights']
            elif 'insights' in primeiro:
                return primeiro['insights']
    elif isinstance(resultado, dict):
        if 'output' in resultado and 'insights' in resultado['output']:
            return resultado['output']['insights']
        elif 'insights' in resultado:
            return resultado['insights']
    return None


def render_card_insight_editavel(insight: dict, campanha_id: int, pagina: str):
    """Renderiza card de insight com opções de edição"""
    import requests
    import time
    import re
    
    WEBHOOK_IA_URL = "https://n8n.air.com.vc/webhook/e19fe530-62b6-44af-b6d1-3aeed59cfe0b"
    
    insight_id = insight.get('id')
    tipo = insight.get('tipo', 'info')
    titulo = insight.get('titulo', 'Insight')
    texto = insight.get('texto', '')
    fonte = insight.get('fonte', 'ia')
    ativo = insight.get('ativo', 1)
    created_at = insight.get('created_at', '')
    
    # Converter markdown **texto** para HTML <strong>texto</strong>
    texto_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', texto)
    
    # Formatar data
    data_criacao = ''
    if created_at:
        try:
            if 'T' in created_at:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(created_at[:19], '%Y-%m-%d %H:%M:%S')
            data_criacao = dt.strftime('%d/%m/%Y %H:%M')
        except:
            data_criacao = created_at[:16] if len(created_at) > 16 else created_at
    
    cores = {
        'sucesso': '#dcfce7',
        'alerta': '#fef3c7',
        'info': '#dbeafe',
        'destaque': '#f3e8ff',
        'critico': '#fee2e2'
    }
    
    cor_fundo = cores.get(tipo, '#f3f4f6')
    if not ativo:
        cor_fundo = '#e5e7eb'
    
    fonte_label = "IA" if fonte == 'ia' else "Manual"
    status_label = "EXCLUIDO - " if not ativo else ""
    opacity = "0.6" if not ativo else "1"
    
    # Container do card
    with st.container():
        st.markdown(f"""
        <div style="background: {cor_fundo}; border-radius: 12px; padding: 1rem; margin-bottom: 0.5rem; opacity: {opacity};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.1rem;">{status_label}<strong>{titulo}</strong></span>
                <span style="font-size: 0.75rem; color: #6b7280;">{fonte_label} | {data_criacao}</span>
            </div>
            <div style="font-size: 0.9rem; color: #374151;">{texto_html}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botões de ação
        editing_key = f'editing_{insight_id}'
        regenerating_key = f'regenerating_{insight_id}'
        
        if st.session_state.get(editing_key, False):
            # Modo de edição
            with st.form(f"form_edit_{insight_id}"):
                col1, col2 = st.columns(2)
                with col1:
                    novo_tipo = st.selectbox(
                        "Tipo:", 
                        ['sucesso', 'alerta', 'info', 'destaque', 'critico'],
                        index=['sucesso', 'alerta', 'info', 'destaque', 'critico'].index(tipo) if tipo in ['sucesso', 'alerta', 'info', 'destaque', 'critico'] else 2,
                        key=f"tipo_{insight_id}"
                    )
                with col2:
                    pass
                
                novo_titulo = st.text_input("Titulo:", value=titulo, key=f"titulo_{insight_id}")
                novo_texto = st.text_area("Texto:", value=texto, height=150, key=f"texto_{insight_id}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Salvar", type="primary", use_container_width=True):
                        data_manager.atualizar_insight(insight_id, {
                            'tipo': novo_tipo,
                            'titulo': novo_titulo,
                            'texto': novo_texto
                        })
                        st.session_state[editing_key] = False
                        st.rerun()
                with col2:
                    if st.form_submit_button("Cancelar", use_container_width=True):
                        st.session_state[editing_key] = False
                        st.rerun()
        
        elif st.session_state.get(regenerating_key, False):
            # Regenerando com IA
            with st.spinner("Pedindo para IA regenerar este insight..."):
                try:
                    campanha = data_manager.get_campanha(campanha_id)
                    dados = preparar_dados_para_ia(campanha)
                    
                    payload = {
                        "pagina": pagina,
                        "campanha_id": campanha_id,
                        "dados": dados,
                        "acao": "regenerar_insight",
                        "insight_atual": {
                            "titulo": titulo,
                            "texto": texto,
                            "tipo": tipo
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    response = requests.post(
                        WEBHOOK_IA_URL,
                        json=payload,
                        timeout=120,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        resultado = response.json()
                        insights = extrair_insights_resposta(resultado)
                        
                        if insights and len(insights) > 0:
                            novo_insight = insights[0]
                            data_manager.atualizar_insight(insight_id, {
                                'tipo': novo_insight.get('tipo', tipo),
                                'titulo': novo_insight.get('titulo', titulo),
                                'texto': novo_insight.get('texto', texto)
                            })
                            st.success("Insight regenerado!")
                        else:
                            st.error("Nao foi possivel regenerar")
                    else:
                        st.error(f"Erro HTTP {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Erro: {e}")
            
            st.session_state[regenerating_key] = False
            time.sleep(0.5)
            st.rerun()
        
        else:
            # Botões normais
            if ativo:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Editar", key=f"edit_{insight_id}", use_container_width=True):
                        st.session_state[editing_key] = True
                        st.rerun()
                with col2:
                    if st.button("Regenerar IA", key=f"regen_{insight_id}", use_container_width=True):
                        st.session_state[regenerating_key] = True
                        st.rerun()
                with col3:
                    if st.button("Excluir", key=f"del_{insight_id}", use_container_width=True):
                        data_manager.excluir_insight(insight_id)
                        st.rerun()
            else:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Restaurar", key=f"restore_{insight_id}", use_container_width=True):
                        data_manager.atualizar_insight(insight_id, {'ativo': 1})
                        st.rerun()
                with col2:
                    if st.button("Apagar", key=f"delete_{insight_id}", use_container_width=True):
                        data_manager.excluir_insight(insight_id, soft_delete=False)
                        st.rerun()
        
        st.markdown("")  # Espaçamento


def preparar_dados_para_ia(campanha: dict) -> dict:
    """Prepara todos os dados da campanha para enviar à IA"""
    campanha_id = campanha['id']
    
    # Buscar influenciadores e posts
    influenciadores = data_manager.get_influenciadores_campanha(campanha_id)
    
    # Calcular métricas gerais
    total_impressoes = 0
    total_alcance = 0
    total_interacoes = 0
    total_views = 0
    total_curtidas = 0
    total_comentarios = 0
    total_compartilhamentos = 0
    total_saves = 0
    total_posts = 0
    
    dados_influenciadores = []
    dados_posts = []
    
    for inf in influenciadores:
        posts = inf.get('posts', [])
        inf_impressoes = 0
        inf_alcance = 0
        inf_interacoes = 0
        
        for post in posts:
            total_posts += 1
            impressoes = post.get('impressoes', 0) or 0
            alcance = post.get('alcance', 0) or 0
            views = post.get('views', 0) or 0
            curtidas = post.get('curtidas', 0) or 0
            comentarios = post.get('comentarios', 0) or 0
            compartilhamentos = post.get('compartilhamentos', 0) or 0
            saves = post.get('saves', 0) or 0
            interacoes = post.get('interacoes', 0) or (curtidas + comentarios + compartilhamentos + saves)
            
            total_impressoes += impressoes
            total_alcance += alcance
            total_views += views
            total_curtidas += curtidas
            total_comentarios += comentarios
            total_compartilhamentos += compartilhamentos
            total_saves += saves
            total_interacoes += interacoes
            
            inf_impressoes += impressoes
            inf_alcance += alcance
            inf_interacoes += interacoes
            
            dados_posts.append({
                'influenciador': inf.get('nome', ''),
                'formato': post.get('formato', ''),
                'plataforma': post.get('plataforma', inf.get('network', 'instagram')),
                'data': post.get('data_publicacao', ''),
                'impressoes': impressoes,
                'alcance': alcance,
                'views': views,
                'interacoes': interacoes,
                'curtidas': curtidas,
                'comentarios': comentarios,
                'compartilhamentos': compartilhamentos,
                'saves': saves
            })
        
        dados_influenciadores.append({
            'nome': inf.get('nome', ''),
            'usuario': inf.get('usuario', ''),
            'network': inf.get('network', 'instagram'),
            'classificacao': inf.get('classificacao', ''),
            'seguidores': inf.get('seguidores', 0),
            'air_score': inf.get('air_score', 0),
            'custo': inf.get('custo', 0),
            'total_posts': len(posts),
            'impressoes': inf_impressoes,
            'alcance': inf_alcance,
            'interacoes': inf_interacoes
        })
    
    # Calcular taxas
    engajamento_efetivo = round((total_interacoes / total_impressoes * 100), 2) if total_impressoes > 0 else 0
    taxa_alcance = round((total_alcance / sum([i.get('seguidores', 0) for i in influenciadores]) * 100), 2) if influenciadores else 0
    
    return {
        "campanha": {
            "id": campanha_id,
            "nome": campanha.get('nome', ''),
            "cliente": campanha.get('cliente_nome', ''),
            "data_inicio": campanha.get('data_inicio', ''),
            "data_fim": campanha.get('data_fim', ''),
            "estimativa_alcance": campanha.get('estimativa_alcance', 0),
            "estimativa_impressoes": campanha.get('estimativa_impressoes', 0),
            "investimento": campanha.get('investimento_total', 0)
        },
        "influenciadores": dados_influenciadores,
        "posts": dados_posts,
        "metricas_gerais": {
            "total_influenciadores": len(influenciadores),
            "total_posts": total_posts,
            "total_impressoes": total_impressoes,
            "total_alcance": total_alcance,
            "total_views": total_views,
            "total_interacoes": total_interacoes,
            "total_curtidas": total_curtidas,
            "total_comentarios": total_comentarios,
            "total_compartilhamentos": total_compartilhamentos,
            "total_saves": total_saves,
            "engajamento_efetivo": engajamento_efetivo,
            "taxa_alcance": taxa_alcance
        }
    }


def render_comentarios(campanha):
    """Extrair e classificar comentarios de posts da campanha"""
    import time
    import requests
    
    st.subheader("Extracao e Classificacao de Comentarios")
    st.caption("Extraia comentarios dos posts da campanha e classifique-os com IA")
    
    campanha_id = campanha['id']
    
    # Webhook para classificacao
    WEBHOOK_URL = "https://n8n.air.com.vc/webhook/e19fe530-62b6-44af-b6d1-3aeed59cfe0b"
    
    # Categorias configuradas (formato novo com descricao)
    categorias_raw = campanha.get('categorias_comentarios', [])
    
    # Converter para formato com descricao se necessario
    if categorias_raw and isinstance(categorias_raw[0], str):
        categorias = [{'nome': cat, 'descricao': ''} for cat in categorias_raw]
    elif categorias_raw and isinstance(categorias_raw[0], dict):
        categorias = categorias_raw
    else:
        categorias = []
    
    if not categorias:
        st.warning("Configure as categorias de comentarios na aba 'Categorias de Comentarios' antes de classificar.")
        return
    
    # Buscar influenciadores e posts da campanha
    influenciadores = data_manager.get_influenciadores_campanha(campanha_id)
    
    # Coletar todos os posts com links
    posts_campanha = []
    for inf in influenciadores:
        for idx, post in enumerate(inf.get('posts', [])):
            link = post.get('link', '')
            if link and ('instagram.com' in link):
                posts_campanha.append({
                    'influenciador': inf.get('nome', ''),
                    'influenciador_id': inf.get('id'),
                    'usuario': inf.get('usuario', ''),
                    'link': link,
                    'formato': post.get('formato', ''),
                    'data': post.get('data_publicacao', ''),
                    'curtidas': post.get('curtidas', 0),
                    'comentarios_qtd': post.get('comentarios', 0) or post.get('comentarios_qtd', 0),
                    'post_idx': idx
                })
    
    if not posts_campanha:
        st.warning("Nenhum post com link do Instagram encontrado na campanha.")
        st.caption("Adicione links aos posts dos influenciadores para extrair comentarios.")
        return
    
    st.markdown("---")
    
    # Mostrar categorias configuradas
    st.markdown(f"**Categorias configuradas ({len(categorias)}):**")
    cats_texto = ", ".join([c.get('nome', '') for c in categorias[:10]])
    st.caption(cats_texto)
    
    st.markdown("---")
    
    # Posts disponiveis
    st.markdown(f"**Posts da Campanha ({len(posts_campanha)} com link)**")
    
    import pandas as pd
    
    df_posts = pd.DataFrame([
        {
            'Influenciador': p['influenciador'],
            'Formato': p['formato'],
            'Data': p['data'],
            'Curtidas': p['curtidas'],
            'Coments': p['comentarios_qtd']
        }
        for p in posts_campanha
    ])
    
    st.dataframe(df_posts, use_container_width=True, hide_index=True)
    
    # Selecionar post para extrair
    st.markdown("---")
    st.markdown("**1. Extrair Comentarios**")
    
    opcoes_posts = [f"{p['influenciador']} - {p['formato']} ({p['data']})" for p in posts_campanha]
    opcoes_posts.insert(0, "Todos os posts")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        post_selecionado = st.selectbox(
            "Selecione o post:",
            opcoes_posts,
            key="select_post_comentarios"
        )
    with col2:
        limite_comentarios = st.number_input("Limite por post:", min_value=10, max_value=500, value=100, step=10)
    
    if st.button("Extrair Comentarios"):
        st.session_state['extraindo_comentarios'] = True
        st.session_state['post_selecionado'] = post_selecionado
        st.session_state['limite_extracao'] = limite_comentarios
        st.rerun()
    
    # Processar extracao
    if st.session_state.get('extraindo_comentarios', False):
        post_sel = st.session_state.get('post_selecionado', '')
        limite = st.session_state.get('limite_extracao', 100)
        
        # Determinar quais posts extrair
        if post_sel == "Todos os posts":
            posts_extrair = posts_campanha
        else:
            idx = opcoes_posts.index(post_sel) - 1
            posts_extrair = [posts_campanha[idx]]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        comentarios_por_post = {}
        
        try:
            from utils.comentarios_extractor import ComentariosExtractor
            
            extractor = ComentariosExtractor()
            
            for i, post in enumerate(posts_extrair):
                status_text.text(f"Extraindo de {post['influenciador']} ({i+1}/{len(posts_extrair)})...")
                progress_bar.progress((i) / len(posts_extrair))
                
                resultado = extractor.extrair_comentarios(post['link'], limite=limite)
                
                if resultado.get('sucesso'):
                    comentarios = resultado.get('comentarios', [])
                    # Adicionar info do post aos comentarios
                    for c in comentarios:
                        c['post_link'] = post['link']
                        c['influenciador'] = post['influenciador']
                        c['influenciador_id'] = post['influenciador_id']
                    
                    comentarios_por_post[post['link']] = {
                        'comentarios': comentarios,
                        'influenciador': post['influenciador'],
                        'influenciador_id': post['influenciador_id']
                    }
                    status_text.text(f"{post['influenciador']}: {len(comentarios)} comentarios")
                else:
                    st.warning(f"{post['influenciador']}: {resultado.get('erro', 'Erro')}")
                
                time.sleep(1)
            
            progress_bar.progress(1.0)
            
            total = sum(len(p['comentarios']) for p in comentarios_por_post.values())
            if total > 0:
                st.session_state['comentarios_por_post'] = comentarios_por_post
                st.success(f"Total: {total} comentarios de {len(comentarios_por_post)} posts")
            else:
                st.warning("Nenhum comentario extraido")
                
        except ImportError:
            st.error("Biblioteca instaloader nao instalada. Execute: pip install instaloader")
        except Exception as e:
            st.error(f"Erro na extracao: {str(e)}")
        
        st.session_state['extraindo_comentarios'] = False
        time.sleep(1)
        st.rerun()
    
    # Mostrar comentarios extraidos e classificar
    comentarios_por_post = st.session_state.get('comentarios_por_post', {})
    
    if comentarios_por_post:
        total = sum(len(p['comentarios']) for p in comentarios_por_post.values())
        
        st.markdown("---")
        st.markdown(f"**Comentarios Extraidos: {total} de {len(comentarios_por_post)} posts**")
        
        # Preview
        with st.expander("Ver preview"):
            for post_link, dados in list(comentarios_por_post.items())[:3]:
                st.markdown(f"**{dados['influenciador']}** ({len(dados['comentarios'])} comentarios)")
                for c in dados['comentarios'][:3]:
                    st.caption(f"@{c.get('usuario', '')}: {c.get('texto', '')[:100]}")
                st.markdown("---")
        
        # Classificar
        st.markdown("**2. Classificar com IA**")
        st.caption("Envia os comentarios de cada post em lote para a IA classificar")
        
        if st.button("Classificar Comentarios", type="primary"):
            st.session_state['classificando'] = True
            st.rerun()
        
        # Processar classificacao
        if st.session_state.get('classificando', False):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_posts = len(comentarios_por_post)
            total_classificados = 0
            
            for idx, (post_link, dados) in enumerate(comentarios_por_post.items()):
                status_text.text(f"Classificando {dados['influenciador']} ({idx+1}/{total_posts})...")
                progress_bar.progress(idx / total_posts)
                
                comentarios = dados['comentarios']
                
                # Preparar payload para o webhook
                # Envia todos os comentarios do post + categorias com descricoes
                payload = {
                    "acao": "classificar_comentarios",
                    "campanha_id": campanha_id,
                    "post_url": post_link,
                    "influenciador": dados['influenciador'],
                    "comentarios": [
                        {
                            "id": c.get('id', ''),
                            "usuario": c.get('usuario', ''),
                            "texto": c.get('texto', ''),
                            "likes": c.get('likes', 0)
                        }
                        for c in comentarios
                    ],
                    "categorias": [
                        {
                            "nome": cat.get('nome', ''),
                            "descricao": cat.get('descricao', '')
                        }
                        for cat in categorias[:10]
                    ],
                    "timestamp": datetime.now().isoformat()
                }
                
                try:
                    response = requests.post(
                        WEBHOOK_URL,
                        json=payload,
                        timeout=180,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        resultado = response.json()
                        
                        # Processar resposta
                        # Formato esperado: lista de classificacoes por comentario
                        # Cada classificacao tem {"categoria_nome": {"teste": true/false}}
                        classificacoes = extrair_classificacoes_webhook(resultado)
                        
                        # Aplicar classificacoes aos comentarios
                        comentarios_classificados = aplicar_classificacoes(comentarios, classificacoes, categorias)
                        
                        # Salvar no banco
                        salvos = data_manager.salvar_comentarios(
                            campanha_id,
                            post_link,
                            comentarios_classificados,
                            influenciador_id=dados['influenciador_id'],
                            post_shortcode=post_link.split('/')[-2] if '/' in post_link else ''
                        )
                        total_classificados += salvos
                        
                    else:
                        st.warning(f"{dados['influenciador']}: Erro HTTP {response.status_code}")
                        
                except requests.exceptions.Timeout:
                    st.warning(f"{dados['influenciador']}: Timeout")
                except Exception as e:
                    st.warning(f"{dados['influenciador']}: {str(e)[:50]}")
                
                time.sleep(0.5)
            
            progress_bar.progress(1.0)
            st.success(f"{total_classificados} comentarios classificados e salvos!")
            
            # Limpar extraidos
            st.session_state['comentarios_por_post'] = {}
            st.session_state['classificando'] = False
            time.sleep(1)
            st.rerun()
    
    # Comentarios salvos
    st.markdown("---")
    st.markdown("**Comentarios Salvos**")
    
    comentarios_salvos = data_manager.get_comentarios_campanha(campanha_id)
    
    if comentarios_salvos:
        stats = data_manager.get_estatisticas_comentarios(campanha_id)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", stats.get('total', 0))
        with col2:
            classificados = len([c for c in comentarios_salvos if c.get('categoria')])
            st.metric("Classificados", classificados)
        
        # Por categoria
        if stats.get('por_categoria'):
            st.markdown("**Por Categoria:**")
            for cat, dados in stats['por_categoria'].items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.progress(dados['percentual'] / 100)
                with col2:
                    st.caption(f"{cat}: {dados['quantidade']} ({dados['percentual']}%)")
        
        # Tabela
        with st.expander(f"Ver todos ({len(comentarios_salvos)})"):
            df = pd.DataFrame([
                {
                    'Usuario': c.get('usuario', ''),
                    'Texto': c.get('texto', '')[:60] + '...' if len(c.get('texto', '')) > 60 else c.get('texto', ''),
                    'Categoria': c.get('categoria', '-'),
                    'Likes': c.get('likes', 0)
                }
                for c in comentarios_salvos
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Excluir
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Excluir todos", type="secondary"):
                data_manager.excluir_comentarios_campanha(campanha_id)
                st.success("Excluidos!")
                time.sleep(1)
                st.rerun()
    else:
        st.info("Nenhum comentario salvo. Extraia e classifique os comentarios dos posts acima.")


def extrair_classificacoes_webhook(resultado) -> list:
    """
    Extrai classificacoes da resposta do webhook
    Formato esperado do n8n: [{"output": {"classificacoes": [...]}}]
    ou {"classificacoes": [...]}
    
    Cada item em classificacoes:
    {
        "comment_id": "123",
        "categorias": {
            "Elogio ao Produto": {"teste": true},
            "Intencao de Compra": {"teste": false},
            ...
        }
    }
    """
    try:
        if isinstance(resultado, list) and len(resultado) > 0:
            primeiro = resultado[0]
            if isinstance(primeiro, dict):
                if 'output' in primeiro:
                    return primeiro['output'].get('classificacoes', [])
                elif 'classificacoes' in primeiro:
                    return primeiro['classificacoes']
        elif isinstance(resultado, dict):
            if 'output' in resultado:
                return resultado['output'].get('classificacoes', [])
            elif 'classificacoes' in resultado:
                return resultado['classificacoes']
    except:
        pass
    return []


def aplicar_classificacoes(comentarios: list, classificacoes: list, categorias: list) -> list:
    """
    Aplica classificacoes aos comentarios
    Encontra a categoria com teste=true para cada comentario
    """
    # Criar mapa de classificacoes por comment_id
    mapa_class = {}
    for classif in classificacoes:
        comment_id = str(classif.get('comment_id', classif.get('id', '')))
        if comment_id:
            mapa_class[comment_id] = classif.get('categorias', {})
    
    # Aplicar aos comentarios
    comentarios_result = []
    for c in comentarios:
        comment_id = str(c.get('id', ''))
        categoria_encontrada = None
        
        if comment_id in mapa_class:
            cats = mapa_class[comment_id]
            # Encontrar categoria com teste=true
            for cat_nome, cat_result in cats.items():
                if isinstance(cat_result, dict) and cat_result.get('teste', False):
                    categoria_encontrada = cat_nome
                    break
                elif cat_result == True:
                    categoria_encontrada = cat_nome
                    break
        
        comentarios_result.append({
            **c,
            'categoria': categoria_encontrada or 'Nao Classificado',
            'classificado': 1 if categoria_encontrada else 0
        })
    
    return comentarios_result


def render_categorias_comentarios(campanha):
    """Configurar categorias para classificacao de comentarios com descricoes"""
    
    st.subheader("Categorias de Comentarios")
    st.caption("Configure ate 10 categorias com descricoes para a IA classificar os comentarios")
    
    # Formato novo: lista de dicts com nome e descricao
    categorias_raw = campanha.get('categorias_comentarios', [])
    
    # Converter formato antigo (lista de strings) para novo (lista de dicts)
    if categorias_raw and isinstance(categorias_raw[0], str):
        categorias = [
            {'nome': cat, 'descricao': ''} 
            for cat in categorias_raw
        ]
    elif categorias_raw and isinstance(categorias_raw[0], dict):
        categorias = categorias_raw
    else:
        # Categorias padrao
        categorias = [
            {'nome': 'Elogio ao Produto', 'descricao': 'Comentarios positivos sobre o produto, servico ou marca'},
            {'nome': 'Intencao de Compra', 'descricao': 'Usuario demonstra interesse em comprar ou pergunta onde/como comprar'},
            {'nome': 'Conexao Emocional', 'descricao': 'Relaciona o produto com experiencias pessoais, memorias ou sentimentos'},
            {'nome': 'Duvida', 'descricao': 'Perguntas sobre o produto, uso, disponibilidade ou especificacoes'},
            {'nome': 'Critica', 'descricao': 'Reclamacoes, insatisfacao ou comentarios negativos sobre o produto'},
            {'nome': 'Geral', 'descricao': 'Comentarios que nao se encaixam nas outras categorias, tags ou emojis soltos'}
        ]
    
    st.markdown("---")
    st.markdown(f"**Categorias cadastradas: {len(categorias)}/10**")
    
    # Listar categorias existentes
    for i, cat in enumerate(categorias):
        with st.expander(f"{i+1}. {cat.get('nome', 'Sem nome')}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                novo_nome = st.text_input(
                    "Nome:", 
                    value=cat.get('nome', ''), 
                    key=f"cat_nome_{i}"
                )
                nova_desc = st.text_area(
                    "Descricao para a IA:", 
                    value=cat.get('descricao', ''),
                    height=80,
                    key=f"cat_desc_{i}",
                    placeholder="Descreva quando um comentario deve ser classificado nesta categoria..."
                )
            
            with col2:
                st.markdown("")
                st.markdown("")
                if st.button("Excluir", key=f"del_cat_{i}", use_container_width=True):
                    categorias.pop(i)
                    data_manager.atualizar_campanha(campanha['id'], {
                        'categorias_comentarios': categorias
                    })
                    st.rerun()
            
            if st.button("Salvar alteracoes", key=f"save_cat_{i}", use_container_width=True):
                categorias[i] = {'nome': novo_nome, 'descricao': nova_desc}
                data_manager.atualizar_campanha(campanha['id'], {
                    'categorias_comentarios': categorias
                })
                st.success("Categoria atualizada!")
                st.rerun()
    
    # Adicionar nova categoria
    if len(categorias) < 10:
        st.markdown("---")
        st.markdown("**Adicionar nova categoria:**")
        
        with st.form("form_nova_categoria"):
            col1, col2 = st.columns(2)
            with col1:
                novo_nome = st.text_input("Nome da categoria:", placeholder="Ex: Mencao a Concorrente")
            with col2:
                pass
            
            nova_desc = st.text_area(
                "Descricao:", 
                placeholder="Descreva em detalhes quando um comentario deve ser classificado nesta categoria...",
                height=100
            )
            
            if st.form_submit_button("Adicionar Categoria", type="primary"):
                if novo_nome:
                    categorias.append({'nome': novo_nome, 'descricao': nova_desc})
                    data_manager.atualizar_campanha(campanha['id'], {
                        'categorias_comentarios': categorias
                    })
                    st.success(f"Categoria '{novo_nome}' adicionada!")
                    st.rerun()
                else:
                    st.warning("Preencha o nome da categoria")
    else:
        st.info("Limite de 10 categorias atingido. Exclua alguma para adicionar nova.")


def render_form_editar_post(campanha, inf, post_idx, post):
    """Formulario para editar um post existente"""
    
    post_key = f"post_{inf['id']}_{post_idx}"
    
    with st.container():
        st.markdown("#### ✏️ Editar Post")
        
        with st.form(f"form_edit_post_{post_key}"):
            col1, col2 = st.columns(2)
            
            with col1:
                formato = st.selectbox(
                    "Formato",
                    ["Reels", "Feed", "Stories", "Carrossel", "IGTV", "Video"],
                    index=["Reels", "Feed", "Stories", "Carrossel", "IGTV", "Video"].index(post.get('formato', 'Reels')) if post.get('formato') in ["Reels", "Feed", "Stories", "Carrossel", "IGTV", "Video"] else 0,
                    key=f"edit_formato_{post_key}"
                )
                data_pub = st.date_input(
                    "Data Publicacao",
                    value=data_manager.parse_data_flexivel(post.get('data_publicacao', '')),
                    key=f"edit_data_{post_key}"
                )
                link_post = st.text_input(
                    "Link do Post",
                    value=post.get('link_post', ''),
                    key=f"edit_link_{post_key}"
                )
            
            with col2:
                plataforma = st.selectbox(
                    "Plataforma",
                    ["Instagram", "TikTok", "YouTube", "Twitter"],
                    index=["Instagram", "TikTok", "YouTube", "Twitter"].index(post.get('plataforma', 'Instagram')) if post.get('plataforma') in ["Instagram", "TikTok", "YouTube", "Twitter"] else 0,
                    key=f"edit_plat_{post_key}"
                )
            
            st.markdown("---")
            st.markdown("**Metricas Principais:**")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                impressoes = st.number_input(
                    "Impressoes/Views",
                    min_value=0,
                    value=post.get('impressoes', 0) + post.get('views', 0),
                    key=f"edit_imp_{post_key}"
                )
            with col2:
                alcance = st.number_input(
                    "Alcance",
                    min_value=0,
                    value=post.get('alcance', 0),
                    key=f"edit_alc_{post_key}"
                )
            with col3:
                interacoes = st.number_input(
                    "Interacoes",
                    min_value=0,
                    value=post.get('interacoes', 0),
                    key=f"edit_int_{post_key}"
                )
            with col4:
                curtidas = st.number_input(
                    "Curtidas",
                    min_value=0,
                    value=post.get('curtidas', 0),
                    key=f"edit_curt_{post_key}"
                )
            
            st.markdown("**Metricas Adicionais:**")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                comentarios = st.number_input(
                    "Comentarios",
                    min_value=0,
                    value=post.get('comentarios', 0) if isinstance(post.get('comentarios'), int) else len(post.get('comentarios', [])) if isinstance(post.get('comentarios'), list) else 0,
                    key=f"edit_com_{post_key}"
                )
            with col2:
                compartilhamentos = st.number_input(
                    "Compartilhamentos",
                    min_value=0,
                    value=post.get('compartilhamentos', 0),
                    key=f"edit_comp_{post_key}"
                )
            with col3:
                saves = st.number_input(
                    "Salvamentos",
                    min_value=0,
                    value=post.get('saves', 0),
                    key=f"edit_saves_{post_key}"
                )
            with col4:
                clique_link = st.number_input(
                    "Cliques no Link",
                    min_value=0,
                    value=post.get('clique_link', 0),
                    key=f"edit_clink_{post_key}"
                )
            
            col1, col2 = st.columns(2)
            with col1:
                clique_arroba = st.number_input(
                    "Cliques no @",
                    min_value=0,
                    value=post.get('clique_arroba', 0),
                    key=f"edit_carroba_{post_key}"
                )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Salvar Alteracoes", type="primary", use_container_width=True):
                    post_atualizado = {
                        'formato': formato,
                        'plataforma': plataforma,
                        'data_publicacao': data_pub.strftime('%Y-%m-%d'),
                        'link_post': link_post,
                        'impressoes': impressoes,
                        'views': 0,  # Tudo fica em impressoes
                        'alcance': alcance,
                        'interacoes': interacoes,
                        'curtidas': curtidas,
                        'comentarios': comentarios,
                        'compartilhamentos': compartilhamentos,
                        'saves': saves,
                        'clique_link': clique_link,
                        'clique_arroba': clique_arroba,
                        'imagens': post.get('imagens', []),
                        'post_id': post.get('post_id', ''),
                        'legenda': post.get('legenda', '')
                    }
                    
                    data_manager.atualizar_post_campanha(campanha['id'], inf['id'], post_idx, post_atualizado)
                    st.session_state[f'editing_post_{post_key}'] = False
                    st.success("Post atualizado!")
                    st.rerun()
            
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state[f'editing_post_{post_key}'] = False
                    st.rerun()
