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
    tab1, tab2, tab3, tab4 = st.tabs([
        "Influenciadores e Posts",
        "Configuracoes da Campanha",
        "Configurar Insights",
        "Categorias de Comentarios"
    ])
    
    with tab1:
        render_influenciadores_posts(campanha)
    
    with tab2:
        render_configuracoes_campanha(campanha)
    
    with tab3:
        render_configurar_insights(campanha)
    
    with tab4:
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
    st.markdown("#### Adicionar Influenciador")
    
    # Influenciadores ja na campanha
    inf_na_campanha = [inf['id'] for inf in data_manager.get_influenciadores_campanha(campanha['id'])]
    
    # Buscar da base
    todos_inf = data_manager.get_influenciadores()
    disponiveis = [inf for inf in todos_inf if inf['id'] not in inf_na_campanha]
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if disponiveis:
            opcoes = {f"{inf['nome']} (@{inf['usuario']}) - {inf['classificacao']}": inf['id'] for inf in disponiveis}
            selecionado = st.selectbox("Selecione:", list(opcoes.keys()))
            
            if selecionado:
                inf_id = opcoes[selecionado]
                if st.button("Adicionar a Campanha", type="primary"):
                    data_manager.adicionar_influenciador_campanha(campanha['id'], inf_id)
                    st.session_state.show_add_inf_to_campaign = False
                    st.success("Influenciador adicionado!")
                    st.rerun()
        else:
            st.info("Todos os influenciadores ja estao na campanha ou nao ha influenciadores cadastrados.")
    
    with col2:
        if st.button("Cancelar"):
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
    """Configuracao de insights do relatorio"""
    
    st.subheader("Configurar Insights")
    
    insights = campanha.get('insights_config', {})
    
    with st.form("form_insights"):
        st.markdown("**Secoes do Relatorio:**")
        
        col1, col2 = st.columns(2)
        with col1:
            mostrar_eng = st.checkbox("Mostrar Engajamento", value=insights.get('mostrar_engajamento', True))
            mostrar_alc = st.checkbox("Mostrar Alcance", value=insights.get('mostrar_alcance', True))
            mostrar_conv = st.checkbox("Mostrar Conversao", value=insights.get('mostrar_conversao', True))
        with col2:
            mostrar_saves = st.checkbox("Mostrar Saves", value=insights.get('mostrar_saves', True))
            mostrar_formato = st.checkbox("Comparativo por Formato", value=insights.get('mostrar_comparativo_formato', True))
            mostrar_top = st.checkbox("Top Influenciadores", value=insights.get('mostrar_top_influenciadores', True))
        
        st.markdown("---")
        st.markdown("**Insights Personalizados:**")
        
        insights_pers = insights.get('insights_personalizados', [])
        
        insights_influenciadores = st.text_area(
            "Insights sobre Influenciadores:",
            value=insights.get('insights_influenciadores', ''),
            height=100,
            placeholder="Escreva insights sobre performance dos influenciadores..."
        )
        
        insights_campanha = st.text_area(
            "Insights sobre a Campanha:",
            value=insights.get('insights_campanha', ''),
            height=100,
            placeholder="Escreva insights gerais sobre a campanha..."
        )
        
        notas = st.text_area(
            "Notas Gerais:",
            value=campanha.get('notas', ''),
            height=100,
            placeholder="Notas e observacoes..."
        )
        
        if st.form_submit_button("Salvar Insights", type="primary", use_container_width=True):
            novos_insights = {
                'mostrar_engajamento': mostrar_eng,
                'mostrar_alcance': mostrar_alc,
                'mostrar_conversao': mostrar_conv,
                'mostrar_saves': mostrar_saves,
                'mostrar_comparativo_formato': mostrar_formato,
                'mostrar_top_influenciadores': mostrar_top,
                'insights_personalizados': insights_pers,
                'insights_influenciadores': insights_influenciadores,
                'insights_campanha': insights_campanha
            }
            
            data_manager.atualizar_campanha(campanha['id'], {
                'insights_config': novos_insights,
                'notas': notas
            })
            
            st.success("Insights salvos!")
            st.rerun()


def render_categorias_comentarios(campanha):
    """Configurar categorias para classificacao de comentarios"""
    
    st.subheader("Categorias de Comentarios")
    st.caption("Configure as categorias que a IA usara para classificar os comentarios")
    
    categorias = campanha.get('categorias_comentarios', [
        'Elogio ao Produto',
        'Intencao de Compra',
        'Conexao Emocional',
        'Duvida',
        'Critica',
        'Geral'
    ])
    
    with st.form("form_categorias"):
        st.markdown("**Categorias atuais:**")
        
        novas_categorias = []
        for i, cat in enumerate(categorias):
            col1, col2 = st.columns([4, 1])
            with col1:
                nova_cat = st.text_input(f"Categoria {i+1}", value=cat, key=f"cat_{i}")
                if nova_cat:
                    novas_categorias.append(nova_cat)
        
        st.markdown("---")
        nova_categoria = st.text_input("Adicionar nova categoria:", placeholder="Ex: Mencao a Concorrente")
        
        if st.form_submit_button("Salvar Categorias", type="primary", use_container_width=True):
            if nova_categoria and nova_categoria not in novas_categorias:
                novas_categorias.append(nova_categoria)
            
            data_manager.atualizar_campanha(campanha['id'], {
                'categorias_comentarios': novas_categorias
            })
            
            st.success("Categorias salvas!")
            st.rerun()


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
