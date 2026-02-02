"""
Pagina: Central da Campanha
Gerenciamento de influenciadores, posts e configuracoes da campanha
"""

import streamlit as st
from datetime import datetime, timedelta
import base64
from utils import data_manager, funcoes_auxiliares, api_client
from utils.ui_components import (
    open_modal, close_modal, is_modal_open, 
    render_modal_trigger, render_empty_state, render_badge
)

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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Influenciadores e Posts",
        "Configuracoes da Campanha",
        "Top Conteudos",
        "Dados Personalizados",
        "Configurar Insights",
        "Comentarios",
        "Categorias de Comentarios"
    ])
    
    with tab1:
        render_influenciadores_posts(campanha)
    
    with tab2:
        render_configuracoes_campanha(campanha)
    
    with tab3:
        render_top_conteudos(campanha)
    
    with tab4:
        render_dados_personalizados(campanha)
    
    with tab5:
        render_configurar_insights(campanha)
    
    with tab6:
        render_comentarios(campanha)
    
    with tab7:
        render_categorias_comentarios(campanha)


def render_influenciadores_posts(campanha):
    """Gerencia influenciadores e posts da campanha"""
    
    st.subheader("Influenciadores da Campanha")
    
    # Mostrar classificacoes especificas se existirem
    class_especificas = campanha.get('classificacoes_especificas', {})
    if class_especificas:
        with st.expander("Classificacoes Especificas da Campanha", expanded=False):
            for i in range(1, 4):
                nome = class_especificas.get(f'nome{i}', '')
                valores = class_especificas.get(f'valores{i}', '')
                if nome and valores:
                    st.write(f"**{nome}:** {valores}")
    
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
                    try:
                        st.image(inf['foto'], width=80)
                    except:
                        st.markdown("### ")
                else:
                    st.markdown("### ")
            
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
            
            # Classificacoes especificas do influenciador nesta campanha
            if class_especificas:
                st.markdown("**Classificacoes Especificas:**")
                cols = st.columns(3)
                
                # Buscar classificacoes atuais do influenciador na campanha
                class_inf = inf.get('classificacoes_especificas', {}) or {}
                
                for i in range(1, 4):
                    nome_class = class_especificas.get(f'nome{i}', '')
                    valores_class = class_especificas.get(f'valores{i}', '')
                    
                    if nome_class and valores_class:
                        with cols[i-1]:
                            opcoes = [''] + [v.strip() for v in valores_class.split(',')]
                            valor_atual = class_inf.get(f'class{i}', '')
                            idx = opcoes.index(valor_atual) if valor_atual in opcoes else 0
                            
                            novo_valor = st.selectbox(
                                nome_class,
                                opcoes,
                                index=idx,
                                key=f"class_esp_{inf['id']}_{i}"
                            )
                            
                            if novo_valor != valor_atual:
                                if st.button("Salvar", key=f"salvar_class_{inf['id']}_{i}"):
                                    class_inf[f'class{i}'] = novo_valor
                                    data_manager.atualizar_classificacoes_influenciador_campanha(
                                        campanha['id'], inf['id'], class_inf
                                    )
                                    st.success("Salvo!")
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
                                if st.button("", key=f"edit_{post_key}", help="Editar"):
                                    st.session_state[f'editing_post_{post_key}'] = True
                                    st.rerun()
                            with col_del:
                                if st.button("", key=f"del_{post_key}", help="Excluir"):
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
                        try:
                            st.image(post['thumbnail'], width=60)
                        except:
                            st.markdown("📷")
                    else:
                        st.markdown("📷")
                
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
                            try:
                                st.image(post['thumbnail'], width=40)
                            except:
                                st.markdown("📷")
                        else:
                            st.markdown("📷")
                    
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
    
    metricas_raw = campanha.get('metricas_selecionadas')
    metricas_config = metricas_raw if isinstance(metricas_raw, dict) else {}
    
    # Escolher formato primeiro para mostrar opcoes de Stories
    col_fmt, col_plat = st.columns(2)
    with col_fmt:
        formato = st.selectbox("Formato *", ["Reels", "Stories", "Carrossel", "Feed", "TikTok", "YouTube"], key=f"fmt_{inf['id']}")
    with col_plat:
        plataforma = st.selectbox("Plataforma", ["Instagram", "TikTok", "YouTube"], key=f"plat_{inf['id']}")
    
    # Se for Stories, interface especial para múltiplas telas
    qtd_telas = 1
    if formato == "Stories":
        st.markdown("---")
        st.info("📱 **Stories**: Adicione todas as telas de um mesmo dia de uma vez!")
        
        modo_stories = st.radio(
            "Modo de entrada:",
            ["Dados consolidados (soma de todas as telas)", "Tela por tela (mais detalhado)"],
            key=f"modo_stories_{inf['id']}"
        )
        
        if modo_stories == "Dados consolidados (soma de todas as telas)":
            qtd_telas = st.number_input("Quantidade de telas (Stories)", min_value=1, max_value=50, value=1, key=f"qtd_telas_{inf['id']}")
            if qtd_telas > 1:
                st.caption(f"Você está adicionando {qtd_telas} telas de Stories do mesmo dia como 1 publicação")
        else:
            # Modo tela por tela
            st.markdown("**Adicionar telas individualmente:**")
            
            # Inicializar lista de telas na sessão
            key_telas = f"stories_telas_{inf['id']}"
            if key_telas not in st.session_state:
                st.session_state[key_telas] = []
            
            col_add, col_info = st.columns([2, 1])
            with col_add:
                nova_views = st.number_input("Views desta tela", min_value=0, value=0, key=f"nova_views_{inf['id']}")
                nova_alcance = st.number_input("Alcance desta tela", min_value=0, value=0, key=f"nova_alcance_{inf['id']}")
                nova_inter = st.number_input("Interações desta tela", min_value=0, value=0, key=f"nova_inter_{inf['id']}")
                
                if st.button("Adicionar tela", key=f"add_tela_{inf['id']}"):
                    st.session_state[key_telas].append({
                        'views': nova_views,
                        'alcance': nova_alcance,
                        'interacoes': nova_inter
                    })
                    st.rerun()
            
            with col_info:
                st.markdown("**Telas adicionadas:**")
                if st.session_state[key_telas]:
                    total_views = sum(t['views'] for t in st.session_state[key_telas])
                    max_alcance = max(t['alcance'] for t in st.session_state[key_telas])
                    total_inter = sum(t['interacoes'] for t in st.session_state[key_telas])
                    
                    for i, tela in enumerate(st.session_state[key_telas]):
                        col_t, col_del = st.columns([3, 1])
                        with col_t:
                            st.caption(f"Tela {i+1}: {tela['views']} views")
                        with col_del:
                            if st.button("", key=f"del_tela_{inf['id']}_{i}"):
                                st.session_state[key_telas].pop(i)
                                st.rerun()
                    
                    st.markdown(f"**Total:** {len(st.session_state[key_telas])} telas")
                    st.markdown(f"Views: {total_views:,}")
                    st.markdown(f"Alcance (maior): {max_alcance:,}")
                    st.markdown(f"Interações: {total_inter:,}")
                    
                    qtd_telas = len(st.session_state[key_telas])
                else:
                    st.caption("Nenhuma tela adicionada ainda")
    
    with st.form(f"form_post_manual_{inf['id']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            data_pub = st.date_input("Data Publicacao *")
        
        with col2:
            link_post = st.text_input("Link do Post")
        
        # Se Stories no modo tela por tela com telas adicionadas
        if formato == "Stories" and modo_stories != "Dados consolidados (soma de todas as telas)" and st.session_state.get(f"stories_telas_{inf['id']}"):
            telas = st.session_state[f"stories_telas_{inf['id']}"]
            views = sum(t['views'] for t in telas)
            impressoes = views  # Para Stories, views = impressoes
            alcance = max(t['alcance'] for t in telas)
            interacoes = sum(t['interacoes'] for t in telas)
            curtidas = 0
            comentarios_qtd = 0
            
            st.info(f"Usando dados das {len(telas)} telas adicionadas")
        else:
            if formato == "Stories" and qtd_telas > 1:
                st.markdown("**Métricas totais (soma de todas as telas):**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                views = st.number_input("Views (total)", min_value=0, value=0)
                impressoes = st.number_input("Impressões (total)", min_value=0, value=0)
            with col2:
                alcance = st.number_input("Alcance (maior)", min_value=0, value=0, help="Para Stories, use o maior alcance entre as telas")
                interacoes = st.number_input("Interações (total)", min_value=0, value=0)
            with col3:
                curtidas = st.number_input("Curtidas (total)", min_value=0, value=0)
                comentarios_qtd = st.number_input("Comentários (total)", min_value=0, value=0)
        
        col1, col2 = st.columns(2)
        with col1:
            compartilhamentos = st.number_input("Compartilhamentos", min_value=0, value=0)
        with col2:
            saves = st.number_input("Salvamentos", min_value=0, value=0)
        
        # Metricas opcionais
        col1, col2 = st.columns(2)
        with col1:
            clique_link = st.number_input("Cliques no Link", min_value=0, value=0) if metricas_config.get('clique_link') else 0
        with col2:
            cupom_conversoes = st.number_input("Conversões Cupom", min_value=0, value=0) if metricas_config.get('cupom_conversoes') else 0
        
        col1, col2 = st.columns(2)
        submitted = col1.form_submit_button("Adicionar Post", use_container_width=True, type="primary")
        cancel = col2.form_submit_button("Cancelar", use_container_width=True)
        
        if submitted:
            post_data = {
                'formato': formato,
                'plataforma': plataforma,
                'data_publicacao': data_pub.strftime('%d/%m/%Y'),
                'link': link_post,
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
                'imagens': [],
                'qtd_telas': qtd_telas if formato == "Stories" else 1
            }
            
            data_manager.adicionar_post(campanha['id'], inf['id'], post_data)
            
            # Limpar telas de Stories da sessão
            if f"stories_telas_{inf['id']}" in st.session_state:
                del st.session_state[f"stories_telas_{inf['id']}"]
            
            st.session_state.show_manual_post_inf = None
            st.success(f"Post adicionado!" + (f" ({qtd_telas} telas de Stories)" if qtd_telas > 1 else ""))
            st.rerun()
        
        if cancel:
            # Limpar telas de Stories da sessão
            if f"stories_telas_{inf['id']}" in st.session_state:
                del st.session_state[f"stories_telas_{inf['id']}"]
            st.session_state.show_manual_post_inf = None
            st.rerun()


def render_modal_add_influenciador(campanha):
    """Modal para adicionar influenciador a campanha"""
    
    st.markdown("---")
    st.markdown("#### Adicionar Influenciadores")
    
    # Tabs para escolher modo
    modo = st.radio("Modo:", ["Selecionar da base", "Cadastrar novo"], horizontal=True)
    
    if modo == "Selecionar da base":
        # Influenciadores ja na campanha
        inf_na_campanha = [inf['id'] for inf in data_manager.get_influenciadores_campanha(campanha['id'])]
        
        # Buscar da base
        todos_inf = data_manager.get_influenciadores()
        disponiveis = [inf for inf in todos_inf if inf['id'] not in inf_na_campanha]
        
        if disponiveis:
            # Filtros
            st.markdown("**Filtrar influenciadores:**")
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                # Classificacoes disponiveis
                classif_disponiveis = sorted(list(set([inf.get('classificacao', 'N/A') for inf in disponiveis])))
                filtro_classif = st.multiselect(
                    "Classificacao:",
                    classif_disponiveis,
                    placeholder="Todas"
                )
            
            with col_f2:
                # Redes disponiveis
                redes_disponiveis = sorted(list(set([inf.get('network', 'instagram') for inf in disponiveis])))
                filtro_rede = st.selectbox("Rede:", ["Todas"] + redes_disponiveis)
            
            with col_f3:
                filtro_busca = st.text_input("Buscar:", placeholder="Nome ou usuario...")
            
            # Aplicar filtros
            disponiveis_filtrados = disponiveis.copy()
            
            if filtro_classif:
                disponiveis_filtrados = [inf for inf in disponiveis_filtrados if inf.get('classificacao') in filtro_classif]
            
            if filtro_rede != "Todas":
                disponiveis_filtrados = [inf for inf in disponiveis_filtrados if inf.get('network') == filtro_rede]
            
            if filtro_busca:
                busca = filtro_busca.lower()
                disponiveis_filtrados = [inf for inf in disponiveis_filtrados if busca in inf['nome'].lower() or busca in inf['usuario'].lower()]
            
            st.caption(f"{len(disponiveis_filtrados)} de {len(disponiveis)} influenciadores disponiveis")
            
            if disponiveis_filtrados:
                # Criar opcoes para multiselect
                opcoes = {f"{inf['nome']} (@{inf['usuario']}) - {inf.get('classificacao', 'N/A')} - {funcoes_auxiliares.formatar_numero(inf.get('seguidores', 0))} seg": inf['id'] for inf in disponiveis_filtrados}
                
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
                st.info("Nenhum influenciador encontrado com os filtros selecionados.")
                if st.button("Limpar Filtros"):
                    st.rerun()
        else:
            st.info("Todos os influenciadores ja estao na campanha ou nao ha influenciadores cadastrados.")
            if st.button("Fechar"):
                st.session_state.show_add_inf_to_campaign = False
                st.rerun()
    
    else:  # Cadastrar novo
        st.markdown("**Cadastrar novo influenciador:**")
        
        with st.form("form_novo_inf_campanha"):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome *")
                usuario = st.text_input("Username *", placeholder="sem @")
                network = st.selectbox("Rede Social *", ["instagram", "tiktok", "youtube"])
                seguidores = st.number_input("Seguidores", min_value=0, value=0)
            
            with col2:
                foto = st.text_input("URL da Foto", placeholder="https://...")
                engagement_rate = st.number_input("Taxa de Engajamento (%)", min_value=0.0, value=0.0, step=0.01)
                air_score = st.number_input("AIR Score (0-1)", min_value=0.0, max_value=1.0, value=0.0, step=0.01)
                custo = st.number_input("Custo (R$)", min_value=0.0, value=0.0, step=100.0)
            
            st.markdown("---")
            st.markdown("**Categorias do Influenciador** (para filtrar insights)")
            st.caption("Separe múltiplas categorias por vírgula (ex: Cabelo Liso, Pele Clara, 25-35 anos)")
            categoria = st.text_input("Categorias:", placeholder="Ex: Cabelo Crespo, Pele Negra, 18-24 anos")
            
            # Vincular a outra conta
            st.markdown("---")
            st.markdown("**Vincular a outra conta** (opcional)")
            st.caption("Se este influenciador tem contas em outras redes, vincule para somar métricas")
            
            # Buscar influenciadores existentes para vincular
            todos_inf_vinculo = data_manager.get_influenciadores()
            opcoes_vinculo = ["Nenhum"] + [f"{inf['nome']} (@{inf['usuario']}) - {inf.get('network', 'instagram')}" for inf in todos_inf_vinculo]
            vinculo_map = {opcoes_vinculo[0]: None}
            for i, inf in enumerate(todos_inf_vinculo):
                vinculo_map[opcoes_vinculo[i+1]] = inf['id']
            
            vinculo_sel = st.selectbox("Vincular a:", opcoes_vinculo)
            vinculo_id = vinculo_map.get(vinculo_sel)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Cadastrar e Adicionar", type="primary", use_container_width=True):
                    if nome and usuario:
                        # Criar influenciador
                        novo_inf = data_manager.criar_influenciador({
                            'nome': nome,
                            'usuario': usuario.replace('@', ''),
                            'network': network,
                            'seguidores': seguidores,
                            'foto': foto,
                            'engagement_rate': engagement_rate,
                            'air_score': air_score,
                            'classificacao': data_manager.calcular_classificacao(seguidores),
                            'categoria': categoria,
                            'vinculo_id': vinculo_id
                        })
                        
                        if novo_inf:
                            # Se vinculou, atualizar o outro influenciador também
                            if vinculo_id:
                                inf_vinculo = data_manager.get_influenciador(vinculo_id)
                                if inf_vinculo:
                                    data_manager.atualizar_influenciador(vinculo_id, {
                                        **inf_vinculo,
                                        'vinculo_id': novo_inf['id']
                                    })
                            
                            # Adicionar a campanha com custo e categoria
                            data_manager.adicionar_influenciador_campanha(campanha['id'], novo_inf['id'], custo=custo, categoria=categoria)
                            st.session_state.show_add_inf_to_campaign = False
                            st.success(f"Influenciador {nome} cadastrado e adicionado!")
                            st.rerun()
                    else:
                        st.error("Preencha nome e username")
            
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
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
        
        metricas_raw = campanha.get('metricas_selecionadas')
        metricas = metricas_raw if isinstance(metricas_raw, dict) else {}
        
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
        
        st.markdown("---")
        st.markdown("**Configuracoes do Relatorio:**")
        
        mostrar_aba_categoria = st.checkbox(
            "Mostrar aba 'KPIs por Categoria' no relatorio",
            value=campanha.get('mostrar_aba_categoria', True),
            help="Quando habilitado e existirem influenciadores com categoria definida, exibe uma aba adicional no relatorio agrupando metricas por categoria"
        )
        
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
                'investimento_total': investimento_total,
                'mostrar_aba_categoria': mostrar_aba_categoria
            })
            
            st.success("Configuracoes salvas!")
            st.rerun()


def render_top_conteudos(campanha):
    """Configura os top 3 conteúdos que mais desempenharam para exibir no relatório"""
    
    st.subheader("Top Conteudos")
    st.caption("Selecione os 3 conteudos que mais desempenharam para destacar no relatorio de Top Performance")
    
    campanha_id = campanha['id']
    
    # Buscar influenciadores e posts
    influenciadores = data_manager.get_influenciadores_campanha(campanha_id)
    
    # Coletar todos os posts com informações
    todos_posts = []
    for inf in influenciadores:
        for idx, post in enumerate(inf.get('posts', [])):
            link = post.get('link', '') or post.get('link_post', '') or post.get('permalink', '') or post.get('url', '') or ''
            
            # Calcular engajamento
            views = post.get('views', 0) or 0
            impressoes = post.get('impressoes', 0) or 0
            alcance = post.get('alcance', 0) or 0
            interacoes = post.get('interacoes', 0) or 0
            curtidas = post.get('curtidas', 0) or 0
            comentarios = post.get('comentarios', 0) or post.get('comentarios_qtd', 0) or 0
            if isinstance(comentarios, list):
                comentarios = len(comentarios)
            saves = post.get('saves', 0) or 0
            
            total_imp = views + impressoes
            
            post_id = f"{inf['id']}_{idx}"
            
            todos_posts.append({
                'post_id': post_id,
                'influenciador': inf.get('nome', ''),
                'influenciador_id': inf.get('id'),
                'usuario': inf.get('usuario', ''),
                'formato': post.get('formato', 'N/A'),
                'data': post.get('data_publicacao', ''),
                'link': link,
                'thumbnail': post.get('thumbnail', ''),
                'views': views,
                'impressoes': total_imp,
                'alcance': alcance,
                'interacoes': interacoes,
                'curtidas': curtidas,
                'comentarios': comentarios,
                'saves': saves,
                'legenda': post.get('legenda', '') or post.get('caption', '') or ''
            })
    
    if not todos_posts:
        st.warning("Nenhum post encontrado na campanha.")
        return
    
    # Buscar configuração atual dos top conteúdos
    top_conteudos = campanha.get('top_conteudos', {})
    
    st.markdown("---")
    st.markdown("### Selecionar Top 3 Conteudos")
    st.info("Selecione manualmente os 3 conteudos de melhor desempenho e escreva uma breve descricao explicando a escolha de cada um.")
    
    # Ordenar posts por interações para sugestão
    posts_ordenados = sorted(todos_posts, key=lambda x: x['interacoes'], reverse=True)
    
    # Criar opções para selectbox
    opcoes_posts = ["(Nenhum)"] + [
        f"{p['influenciador']} - {p['formato']} - {funcoes_auxiliares.formatar_numero(p['interacoes'])} inter. ({p['data']})"
        for p in posts_ordenados
    ]
    
    # Mapear opções para post_ids
    opcoes_map = {opcoes_posts[0]: None}
    for i, p in enumerate(posts_ordenados):
        opcoes_map[opcoes_posts[i+1]] = p['post_id']
    
    # Inverso: post_id para opção
    post_id_to_opcao = {v: k for k, v in opcoes_map.items()}
    
    with st.form("form_top_conteudos"):
        for i in range(1, 4):
            st.markdown(f"#### Top {i}")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Valor atual
                atual_post_id = top_conteudos.get(f'top{i}_post_id', None)
                atual_opcao = post_id_to_opcao.get(atual_post_id, "(Nenhum)")
                
                try:
                    idx_default = opcoes_posts.index(atual_opcao)
                except:
                    idx_default = 0
                
                selected = st.selectbox(
                    f"Conteudo Top {i}:",
                    opcoes_posts,
                    index=idx_default,
                    key=f"top{i}_select"
                )
                
                # Mostrar preview do post selecionado
                selected_post_id = opcoes_map.get(selected)
                if selected_post_id:
                    post_info = next((p for p in todos_posts if p['post_id'] == selected_post_id), None)
                    if post_info:
                        if post_info.get('thumbnail'):
                            try:
                                st.image(post_info['thumbnail'], width=150)
                            except:
                                pass
                        st.caption(f"@{post_info['usuario']} | {post_info['formato']}")
                        st.caption(f"👁 {funcoes_auxiliares.formatar_numero(post_info['impressoes'])} | ❤️ {funcoes_auxiliares.formatar_numero(post_info['curtidas'])} | 💬 {funcoes_auxiliares.formatar_numero(post_info['comentarios'])}")
            
            with col2:
                atual_descricao = top_conteudos.get(f'top{i}_descricao', '')
                descricao = st.text_area(
                    f"Descricao da escolha (Top {i}):",
                    value=atual_descricao,
                    height=120,
                    placeholder="Explique por que este conteudo foi destaque na campanha...",
                    key=f"top{i}_desc"
                )
            
            st.markdown("---")
        
        submitted = st.form_submit_button("Salvar Top Conteudos", type="primary", use_container_width=True)
        
        if submitted:
            novo_top_conteudos = {}
            
            for i in range(1, 4):
                selected = st.session_state.get(f"top{i}_select", "(Nenhum)")
                descricao = st.session_state.get(f"top{i}_desc", "")
                
                selected_post_id = opcoes_map.get(selected)
                
                if selected_post_id:
                    # Buscar dados completos do post
                    post_info = next((p for p in todos_posts if p['post_id'] == selected_post_id), None)
                    if post_info:
                        novo_top_conteudos[f'top{i}_post_id'] = selected_post_id
                        novo_top_conteudos[f'top{i}_descricao'] = descricao
                        novo_top_conteudos[f'top{i}_influenciador'] = post_info['influenciador']
                        novo_top_conteudos[f'top{i}_usuario'] = post_info['usuario']
                        novo_top_conteudos[f'top{i}_formato'] = post_info['formato']
                        novo_top_conteudos[f'top{i}_link'] = post_info['link']
                        novo_top_conteudos[f'top{i}_thumbnail'] = post_info['thumbnail']
                        novo_top_conteudos[f'top{i}_impressoes'] = post_info['impressoes']
                        novo_top_conteudos[f'top{i}_alcance'] = post_info['alcance']
                        novo_top_conteudos[f'top{i}_interacoes'] = post_info['interacoes']
                        novo_top_conteudos[f'top{i}_curtidas'] = post_info['curtidas']
                        novo_top_conteudos[f'top{i}_comentarios'] = post_info['comentarios']
                        novo_top_conteudos[f'top{i}_saves'] = post_info['saves']
            
            data_manager.atualizar_campanha(campanha_id, {'top_conteudos': novo_top_conteudos})
            st.success("Top conteudos salvos com sucesso!")
            st.rerun()
    
    # Mostrar preview dos tops configurados
    if top_conteudos:
        st.markdown("### Preview dos Top Conteudos Configurados")
        
        cols = st.columns(3)
        for i, col in enumerate(cols, 1):
            with col:
                post_id = top_conteudos.get(f'top{i}_post_id')
                if post_id:
                    st.markdown(f"**Top {i}**")
                    thumb = top_conteudos.get(f'top{i}_thumbnail', '')
                    if thumb:
                        try:
                            st.image(thumb, use_container_width=True)
                        except:
                            st.markdown("📷")
                    
                    st.markdown(f"**@{top_conteudos.get(f'top{i}_usuario', '')}**")
                    st.caption(top_conteudos.get(f'top{i}_formato', ''))
                    st.caption(top_conteudos.get(f'top{i}_descricao', '')[:100] + '...' if len(top_conteudos.get(f'top{i}_descricao', '')) > 100 else top_conteudos.get(f'top{i}_descricao', ''))
                else:
                    st.info(f"Top {i} nao configurado")


def render_dados_personalizados(campanha):
    """Configuração de colunas personalizadas para lista de influenciadores"""
    
    st.subheader("Dados Personalizados")
    st.caption("Configure colunas extras para a lista de influenciadores no relatório (ex: Tipo de Cabelo, Faixa Etária)")
    
    campanha_id = campanha['id']
    
    # Obter configuração atual
    colunas_config = campanha.get('colunas_personalizadas', {})
    col1_nome = colunas_config.get('col1_nome', '')
    col2_nome = colunas_config.get('col2_nome', '')
    
    st.markdown("### Configurar Nomes das Colunas")
    
    col1, col2 = st.columns(2)
    with col1:
        novo_col1_nome = st.text_input(
            "Nome da Coluna 1:", 
            value=col1_nome, 
            placeholder="Ex: Tipo de Cabelo",
            key="config_col1_nome_tab"
        )
    with col2:
        novo_col2_nome = st.text_input(
            "Nome da Coluna 2:", 
            value=col2_nome, 
            placeholder="Ex: Faixa Etária",
            key="config_col2_nome_tab"
        )
    
    if st.button("Salvar Nomes das Colunas", type="primary"):
        data_manager.atualizar_campanha(campanha_id, {
            'colunas_personalizadas': {
                'col1_nome': novo_col1_nome,
                'col2_nome': novo_col2_nome
            }
        })
        st.success("Nomes das colunas salvos!")
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Preencher Dados dos Influenciadores")
    
    if not novo_col1_nome and not novo_col2_nome and not col1_nome and not col2_nome:
        st.info("Configure os nomes das colunas acima primeiro")
        return
    
    # Nomes a usar (novos ou salvos)
    nome_col1 = novo_col1_nome or col1_nome or "Coluna 1"
    nome_col2 = novo_col2_nome or col2_nome or "Coluna 2"
    
    # Listar influenciadores da campanha
    influenciadores = campanha.get('influenciadores', [])
    
    if not influenciadores:
        st.info("Nenhum influenciador na campanha")
        return
    
    # Criar formulário para editar dados
    st.markdown(f"**Preencha os dados para cada influenciador:**")
    
    # Header da tabela
    col_header = st.columns([2, 2, 2])
    with col_header[0]:
        st.markdown("**Influenciador**")
    with col_header[1]:
        st.markdown(f"**{nome_col1}**")
    with col_header[2]:
        st.markdown(f"**{nome_col2}**")
    
    st.markdown("---")
    
    # Coletar dados em session_state para não perder ao digitar
    if 'dados_custom_temp' not in st.session_state:
        st.session_state.dados_custom_temp = {}
    
    for idx, inf_camp in enumerate(influenciadores):
        inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
        if not inf:
            continue
        
        inf_id = inf['id']
        nome_inf = inf.get('nome', 'Desconhecido')
        usuario_inf = inf.get('usuario', '')
        
        cols = st.columns([2, 2, 2])
        
        with cols[0]:
            st.markdown(f"**{nome_inf}**")
            st.caption(f"@{usuario_inf}")
        
        with cols[1]:
            val1 = st.text_input(
                nome_col1,
                value=inf_camp.get('dado_custom1', ''),
                key=f"dados_custom1_{inf_id}",
                label_visibility="collapsed",
                placeholder=nome_col1
            )
        
        with cols[2]:
            val2 = st.text_input(
                nome_col2,
                value=inf_camp.get('dado_custom2', ''),
                key=f"dados_custom2_{inf_id}",
                label_visibility="collapsed",
                placeholder=nome_col2
            )
        
        # Armazenar temporariamente
        st.session_state.dados_custom_temp[inf_id] = {'col1': val1, 'col2': val2}
    
    st.markdown("---")
    
    if st.button("Salvar Dados dos Influenciadores", type="primary", use_container_width=True):
        # Atualizar dados dos influenciadores
        for inf_camp in influenciadores:
            inf_id = inf_camp.get('influenciador_id')
            if inf_id in st.session_state.dados_custom_temp:
                inf_camp['dado_custom1'] = st.session_state.dados_custom_temp[inf_id]['col1']
                inf_camp['dado_custom2'] = st.session_state.dados_custom_temp[inf_id]['col2']
        
        # Salvar campanha com influenciadores atualizados
        data_manager.atualizar_campanha(campanha_id, {
            'influenciadores': influenciadores,
            'colunas_personalizadas': {
                'col1_nome': novo_col1_nome or col1_nome,
                'col2_nome': novo_col2_nome or col2_nome
            }
        })
        
        st.success("Dados personalizados salvos com sucesso!")
        st.session_state.dados_custom_temp = {}
        st.rerun()
    
    # Preview da tabela
    st.markdown("---")
    st.markdown("### Preview da Lista de Influenciadores")
    
    preview_data = []
    for inf_camp in influenciadores:
        inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
        if inf:
            preview_data.append({
                'Nome': inf.get('nome', ''),
                'Usuário': f"@{inf.get('usuario', '')}",
                nome_col1: inf_camp.get('dado_custom1', ''),
                nome_col2: inf_camp.get('dado_custom2', '')
            })
    
    if preview_data:
        import pandas as pd
        df_preview = pd.DataFrame(preview_data)
        st.dataframe(df_preview, use_container_width=True, hide_index=True)


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


def preparar_dados_para_ia(campanha: dict, filtro_periodo: dict = None) -> dict:
    """Prepara todos os dados da campanha para enviar à IA
    
    Args:
        campanha: dados da campanha
        filtro_periodo: dict com data_inicio e data_fim no formato dd/mm/yyyy
    """
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
    
    # Parse das datas do filtro
    filtro_inicio = None
    filtro_fim = None
    if filtro_periodo:
        try:
            filtro_inicio = datetime.strptime(filtro_periodo.get('data_inicio', ''), '%d/%m/%Y')
            filtro_fim = datetime.strptime(filtro_periodo.get('data_fim', ''), '%d/%m/%Y')
        except:
            pass
    
    for inf in influenciadores:
        posts = inf.get('posts', [])
        inf_impressoes = 0
        inf_alcance = 0
        inf_interacoes = 0
        
        for post in posts:
            # Aplicar filtro de periodo se definido
            if filtro_inicio and filtro_fim:
                data_post_str = post.get('data_publicacao', '')
                try:
                    if '/' in data_post_str:
                        data_post = datetime.strptime(data_post_str, '%d/%m/%Y')
                    elif '-' in data_post_str:
                        data_post = datetime.strptime(data_post_str[:10], '%Y-%m-%d')
                    else:
                        data_post = None
                    
                    if data_post and (data_post < filtro_inicio or data_post > filtro_fim):
                        continue  # Pular post fora do periodo
                except:
                    pass  # Se nao conseguir parsear, inclui o post
            
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
    """Upload de CSV de comentarios por post e classificacao automatica com IA"""
    import time
    import requests
    import pandas as pd
    
    st.subheader("Comentarios por Conteudo")
    st.caption("Faca upload do CSV de comentarios de cada conteudo. O sistema classifica automaticamente com IA.")
    
    campanha_id = campanha['id']
    
    # Webhook para classificacao
    WEBHOOK_URL = "https://n8n.air.com.vc/webhook/e19fe530-62b6-44af-b6d1-3aeed59cfe0b"
    
    # Categorias configuradas
    categorias_raw = campanha.get('categorias_comentarios', [])
    if categorias_raw and isinstance(categorias_raw[0], str):
        categorias = [{'nome': cat, 'descricao': ''} for cat in categorias_raw]
    elif categorias_raw and isinstance(categorias_raw[0], dict):
        categorias = categorias_raw
    else:
        categorias = []
    
    if not categorias:
        st.warning("Configure as categorias na aba 'Categorias de Comentarios' antes de importar.")
        return
    
    cats_texto = ", ".join([c.get('nome', '') for c in categorias[:10]])
    st.caption(f"Categorias: {cats_texto}")
    
    st.markdown("---")
    
    # Buscar influenciadores e posts
    influenciadores = data_manager.get_influenciadores_campanha(campanha_id)
    
    posts_campanha = []
    for inf in influenciadores:
        for idx, post in enumerate(inf.get('posts', [])):
            link = post.get('link', '') or post.get('link_post', '') or post.get('permalink', '') or post.get('url', '') or ''
            posts_campanha.append({
                'influenciador': inf.get('nome', ''),
                'influenciador_id': inf.get('id'),
                'usuario': inf.get('usuario', ''),
                'link': link,
                'formato': post.get('formato', ''),
                'data': post.get('data_publicacao', ''),
                'post_idx': idx
            })
    
    if not posts_campanha:
        st.info("Nenhum post encontrado na campanha.")
        return
    
    # Comentarios salvos no banco (por post)
    comentarios_salvos = data_manager.get_comentarios_campanha(campanha_id)
    
    # Agrupar comentarios salvos por post_url
    coments_por_post = {}
    for c in comentarios_salvos:
        post_url = c.get('post_url', '')
        if post_url not in coments_por_post:
            coments_por_post[post_url] = []
        coments_por_post[post_url].append(c)
    
    # Resumo geral
    total_coments = len(comentarios_salvos)
    total_classificados = len([c for c in comentarios_salvos if c.get('categoria') and c.get('categoria') != 'Nao Classificado'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Comentarios", total_coments)
    with col2:
        st.metric("Classificados", total_classificados)
    with col3:
        st.metric("Posts com Coments", len(coments_por_post))
    
    st.markdown("---")
    
    # Lista de posts com upload
    st.markdown(f"**Conteudos da Campanha ({len(posts_campanha)})**")
    
    for i, post in enumerate(posts_campanha):
        link = post['link']
        nome = post['influenciador']
        formato = post['formato']
        data_post = post['data']
        qtd_salvos = len(coments_por_post.get(link, []))
        
        # Link curto para exibicao
        link_curto = link[:60] + '...' if len(link) > 60 else link
        
        # Card do post
        col_info, col_link, col_status, col_upload = st.columns([2, 3, 1, 2])
        
        with col_info:
            st.markdown(f"**{nome}**")
            st.caption(f"{formato} | {data_post}")
        
        with col_link:
            if link:
                st.markdown(f"<a href='{link}' target='_blank' style='font-size:11px;color:#374151;word-break:break-all;'>{link_curto}</a>", unsafe_allow_html=True)
            else:
                st.caption("Sem link")
        
        with col_status:
            if qtd_salvos > 0:
                st.markdown(f"<span style='font-size:12px;color:#16a34a;font-weight:500;'>{qtd_salvos} coments</span>", unsafe_allow_html=True)
            else:
                st.caption("-")
        
        with col_upload:
            uploaded = st.file_uploader(
                "CSV",
                type=["csv"],
                key=f"csv_upload_{campanha_id}_{i}",
                label_visibility="collapsed"
            )
            
            if uploaded is not None:
                # Processar CSV
                _processar_csv_comentarios(
                    uploaded, campanha_id, post, categorias, 
                    WEBHOOK_URL, i
                )
        
        # Separador sutil
        if i < len(posts_campanha) - 1:
            st.markdown("<hr style='margin:0.5rem 0;border-color:#f3f4f6;'>", unsafe_allow_html=True)
    
    # Secao: comentarios salvos
    if total_coments > 0:
        st.markdown("---")
        st.markdown("**Resumo de Comentarios Salvos**")
        
        # Estatisticas por categoria
        stats = data_manager.get_estatisticas_comentarios(campanha_id)
        
        if stats.get('por_categoria'):
            for cat, dados in stats['por_categoria'].items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.progress(dados['percentual'] / 100)
                with col2:
                    st.caption(f"{cat}: {dados['quantidade']} ({dados['percentual']}%)")
        
        # Tabela completa em expander
        with st.expander(f"Ver todos ({total_coments} comentarios)"):
            df = pd.DataFrame([
                {
                    'Usuario': c.get('usuario', ''),
                    'Texto': c.get('texto', '')[:80] + '...' if len(c.get('texto', '')) > 80 else c.get('texto', ''),
                    'Categoria': c.get('categoria', '-'),
                    'Likes': c.get('likes', 0)
                }
                for c in comentarios_salvos
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Botao excluir
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("Excluir todos", key="btn_excluir_coments"):
                data_manager.excluir_comentarios_campanha(campanha_id)
                st.success("Comentarios excluidos!")
                import time
                time.sleep(1)
                st.rerun()


def _processar_csv_comentarios(uploaded_file, campanha_id, post_info, categorias, webhook_url, post_index):
    """Processa CSV de comentarios e envia para classificacao"""
    import pandas as pd
    import requests
    import time
    
    try:
        # Ler CSV
        df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        
        # Validar colunas obrigatorias
        colunas_necessarias = ['Comment']
        colunas_presentes = [c for c in df.columns if c in ['Comment', 'Username', 'Name', 'Date', 'Likes', 'Comment ID', 'Profile URL', 'Comment URL']]
        
        if 'Comment' not in df.columns:
            st.error("CSV invalido: coluna 'Comment' nao encontrada. Use o formato CSV do ExportComments.")
            return
        
        # Filtrar linhas vazias
        df = df[df['Comment'].notna() & (df['Comment'].str.strip() != '')]
        
        if len(df) == 0:
            st.warning("Nenhum comentario valido no CSV.")
            return
        
        st.info(f"{len(df)} comentarios encontrados no CSV de {post_info['influenciador']}")
        
        # Converter para lista de comentarios
        comentarios = []
        for _, row in df.iterrows():
            comentarios.append({
                'id': str(row.get('Comment ID', '')),
                'usuario': str(row.get('Username', row.get('Name', ''))),
                'texto': str(row.get('Comment', '')),
                'likes': int(row.get('Likes', 0)) if pd.notna(row.get('Likes', 0)) else 0,
                'data': str(row.get('Date', '')),
                'perfil_url': str(row.get('Profile URL', '')),
                'comentario_url': str(row.get('Comment URL', '')),
                'post_link': post_info['link'],
                'influenciador': post_info['influenciador'],
                'influenciador_id': post_info['influenciador_id']
            })
        
        # Enviar para webhook de classificacao automaticamente
        progress = st.progress(0)
        status = st.empty()
        
        status.text(f"Classificando {len(comentarios)} comentarios com IA...")
        progress.progress(0.3)
        
        # Preparar payload
        payload = {
            "acao": "classificar_comentarios",
            "campanha_id": campanha_id,
            "post_url": post_info['link'],
            "influenciador": post_info['influenciador'],
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
        
        progress.progress(0.5)
        
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=180,
                headers={"Content-Type": "application/json"}
            )
            
            progress.progress(0.8)
            
            if response.status_code == 200:
                resultado = response.json()
                
                # Processar classificacoes
                classificacoes = extrair_classificacoes_webhook(resultado)
                comentarios_classificados = aplicar_classificacoes(comentarios, classificacoes, categorias)
                
                # Salvar no banco
                salvos = data_manager.salvar_comentarios(
                    campanha_id,
                    post_info['link'],
                    comentarios_classificados,
                    influenciador_id=post_info['influenciador_id'],
                    post_shortcode=post_info['link'].split('/')[-2] if '/' in post_info['link'] else ''
                )
                
                progress.progress(1.0)
                status.empty()
                st.success(f"{salvos} comentarios classificados e salvos!")
                time.sleep(1.5)
                st.rerun()
            else:
                progress.progress(1.0)
                status.empty()
                st.error(f"Erro na classificacao: HTTP {response.status_code}")
                
                # Salvar sem classificacao
                for c in comentarios:
                    c['categoria'] = 'Nao Classificado'
                    c['classificado'] = 0
                
                salvos = data_manager.salvar_comentarios(
                    campanha_id,
                    post_info['link'],
                    comentarios,
                    influenciador_id=post_info['influenciador_id'],
                    post_shortcode=post_info['link'].split('/')[-2] if '/' in post_info['link'] else ''
                )
                st.warning(f"{salvos} comentarios salvos sem classificacao (erro no webhook)")
                time.sleep(1.5)
                st.rerun()
                
        except requests.exceptions.Timeout:
            progress.progress(1.0)
            status.empty()
            st.error("Timeout na classificacao. Salvando comentarios sem classificacao...")
            
            for c in comentarios:
                c['categoria'] = 'Nao Classificado'
                c['classificado'] = 0
            
            data_manager.salvar_comentarios(
                campanha_id, post_info['link'], comentarios,
                influenciador_id=post_info['influenciador_id'],
                post_shortcode=post_info['link'].split('/')[-2] if '/' in post_info['link'] else ''
            )
            time.sleep(1.5)
            st.rerun()
            
        except Exception as e:
            progress.progress(1.0)
            status.empty()
            st.error(f"Erro: {str(e)}")
    
    except Exception as e:
        st.error(f"Erro ao ler CSV: {str(e)}. Verifique se o arquivo esta no formato correto (CSV do ExportComments).")


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
        st.markdown("####  Editar Post")
        
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
                if st.form_submit_button("Salvar Alteracoes", type="primary", use_container_width=True):
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
