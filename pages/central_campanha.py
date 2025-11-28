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
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        aon_badge = "[AON]" if campanha.get('is_aon') else ""
        st.markdown(f'<p class="main-header">Central: {campanha["nome"]} {aon_badge}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="subtitle">{campanha.get("cliente_nome", "")} | {funcoes_auxiliares.formatar_data_br(campanha["data_inicio"])} - {funcoes_auxiliares.formatar_data_br(campanha["data_fim"])}</p>', unsafe_allow_html=True)
    with col2:
        # Exportar CSV
        influenciadores_data = data_manager.get_influenciadores_campanha(campanha['id'])
        csv_data = funcoes_auxiliares.exportar_campanha_csv(campanha, influenciadores_data)
        st.download_button(
            "Exportar CSV",
            data=csv_data,
            file_name=f"{campanha['nome']}_dados.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col3:
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
            col1, col2, col3 = st.columns([1, 2, 2])
            
            with col1:
                if inf.get('foto'):
                    st.image(inf['foto'], width=80)
            
            with col2:
                st.write(f"**Seguidores:** {funcoes_auxiliares.formatar_numero(inf['seguidores'])}")
                st.write(f"**AIR Score:** {inf['air_score']}")
                st.write(f"**Taxa Eng.:** {inf['engagement_rate']:.2f}%")
            
            with col3:
                st.write(f"**Rede:** {inf['network'].title()}")
                st.write(f"**Classificacao:** {inf['classificacao']}")
                if campanha['tipo_dados'] == 'estatico':
                    st.caption("Dados congelados (campanha estatica)")
            
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
                for post in inf['posts']:
                    col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1, 1, 0.5])
                    
                    with col1:
                        st.write(f"**{post['formato']}** ({post['plataforma']})")
                        st.caption(post['data_publicacao'])
                        if post.get('link_post'):
                            st.markdown(f"[Link]({post['link_post']})")
                    
                    with col2:
                        st.caption("Views")
                        st.write(f"{post['views']:,}")
                    
                    with col3:
                        st.caption("Alcance")
                        st.write(f"{post['alcance']:,}")
                    
                    with col4:
                        st.caption("Interacoes")
                        st.write(f"{post['interacoes']:,}")
                    
                    with col5:
                        if post.get('imagens') and len(post['imagens']) > 0:
                            try:
                                img = post['imagens'][0]
                                if img.startswith('http'):
                                    st.image(img, width=50)
                            except:
                                pass
                    
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
    
    # Chaves unicas para este influenciador
    inf_id = inf['id']
    
    # Inicializar estados se nao existirem
    if f'api_posts_sel_{inf_id}' not in st.session_state:
        st.session_state[f'api_posts_sel_{inf_id}'] = []
    if f'api_result_{inf_id}' not in st.session_state:
        st.session_state[f'api_result_{inf_id}'] = None
    if f'api_filters_{inf_id}' not in st.session_state:
        st.session_state[f'api_filters_{inf_id}'] = {
            'profile_id': inf.get('profile_id'),
            'start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'post_types': ['post', 'reel'],
            'text': ''
        }
    
    # Pegar filtros do session state
    filters = st.session_state[f'api_filters_{inf_id}']
    
    # Filtros
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
            # Atualizar filtros no session state
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
    
    # Resultados e Selecionados lado a lado
    result = st.session_state[f'api_result_{inf_id}']
    
    if result:
        col_posts, col_selecionados = st.columns([3, 2])
        
        with col_posts:
            st.markdown("**Posts Encontrados:**")
            
            items = result.get('items', [])
            total_pages = result.get('pages', 1)
            current_page = result.get('current_page', 0)
            
            # Paginacao no topo
            col_prev, col_info, col_next = st.columns([1, 2, 1])
            with col_prev:
                if current_page > 0:
                    if st.button("< Anterior", key=f"prev_{inf_id}", use_container_width=True):
                        with st.spinner("Carregando..."):
                            resultado = buscar_pagina(current_page - 1)
                            if resultado.get('success'):
                                st.session_state[f'api_result_{inf_id}'] = resultado.get('data', {})
                                st.rerun()
            with col_info:
                st.markdown(f"<p style='text-align:center'><b>Pagina {current_page + 1} de {total_pages}</b></p>", unsafe_allow_html=True)
            with col_next:
                if current_page < total_pages - 1:
                    if st.button("Proximo >", key=f"next_{inf_id}", use_container_width=True):
                        with st.spinner("Carregando..."):
                            resultado = buscar_pagina(current_page + 1)
                            if resultado.get('success'):
                                st.session_state[f'api_result_{inf_id}'] = resultado.get('data', {})
                                st.rerun()
            
            # Container com scroll para posts
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
            
            # Container com scroll para selecionados
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
            plataforma = st.selectbox("Plataforma *", [inf['network'].title()])
            data_pub = st.date_input("Data Publicacao *", value=datetime.now())
            link_post = st.text_input("Link do Post", placeholder="https://...")
        
        with col2:
            views = st.number_input("Views", min_value=0, value=0)
            alcance = st.number_input("Alcance", min_value=0, value=0)
            interacoes = st.number_input("Interacoes", min_value=0, value=0)
            impressoes = st.number_input("Impressoes", min_value=0, value=0)
        
        with col3:
            curtidas = st.number_input("Curtidas", min_value=0, value=0)
            comentarios = st.number_input("Comentarios", min_value=0, value=0)
            compartilhamentos = st.number_input("Compartilhamentos", min_value=0, value=0)
            saves = st.number_input("Saves", min_value=0, value=0)
        
        # Metricas de Stories
        if formato == "Stories":
            st.markdown("**Metricas de Stories:**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                clique_link = st.number_input("Cliques no Link", min_value=0, value=0)
            with col2:
                taps_forward = st.number_input("Taps Forward", min_value=0, value=0)
            with col3:
                taps_back = st.number_input("Taps Back", min_value=0, value=0)
            with col4:
                exits = st.number_input("Exits", min_value=0, value=0)
        else:
            clique_link = 0
        
        # Cupom e custo
        col1, col2, col3 = st.columns(3)
        with col1:
            cupom_codigo = st.text_input("Codigo do Cupom")
        with col2:
            cupom_conversoes = st.number_input("Conversoes", min_value=0, value=0)
        with col3:
            custo = st.number_input("Custo (R$)", min_value=0.0, value=0.0, step=0.01)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Salvar Post", use_container_width=True):
                data_manager.adicionar_post(campanha['id'], inf['id'], {
                    'formato': formato,
                    'plataforma': plataforma,
                    'data_publicacao': data_pub.strftime('%d/%m/%Y'),
                    'link_post': link_post,
                    'views': views,
                    'alcance': alcance,
                    'interacoes': interacoes,
                    'impressoes': impressoes,
                    'curtidas': curtidas,
                    'comentarios_qtd': comentarios,
                    'compartilhamentos': compartilhamentos,
                    'saves': saves,
                    'clique_link': clique_link,
                    'cupom_codigo': cupom_codigo,
                    'cupom_conversoes': cupom_conversoes,
                    'custo': custo,
                    'imagens': []
                })
                st.session_state.show_manual_post_inf = None
                st.success("Post adicionado!")
                st.rerun()
        
        with col2:
            if st.form_submit_button("Cancelar", use_container_width=True):
                st.session_state.show_manual_post_inf = None
                st.rerun()


def render_modal_add_influenciador(campanha):
    """Modal para adicionar influenciador a campanha"""
    
    with st.container():
        st.markdown("### Adicionar Influenciadores")
        
        influenciadores_disponiveis = data_manager.get_influenciadores()
        
        if not influenciadores_disponiveis:
            st.warning("Cadastre influenciadores na base primeiro")
            if st.button("Ir para Influenciadores"):
                st.session_state.current_page = 'Influenciadores'
                st.rerun()
        else:
            ids_na_campanha = [i['influenciador_id'] for i in campanha['influenciadores']]
            disponiveis = [i for i in influenciadores_disponiveis if i['id'] not in ids_na_campanha]
            
            if not disponiveis:
                st.info("Todos os influenciadores da base ja estao na campanha")
            else:
                opcoes = {f"{i['nome']} (@{i['usuario']}) - {i['classificacao']}": i['id'] for i in disponiveis}
                
                # Multiselect para escolher varios
                selecionados = st.multiselect(
                    "Selecione os influenciadores:",
                    list(opcoes.keys()),
                    help="Voce pode selecionar varios de uma vez"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Adicionar Selecionados", type="primary", use_container_width=True):
                        if selecionados:
                            for sel in selecionados:
                                inf_id = opcoes[sel]
                                data_manager.adicionar_influenciador_campanha(campanha['id'], inf_id)
                            st.session_state.show_add_inf_to_campaign = False
                            st.success(f"{len(selecionados)} influenciadores adicionados!")
                            st.rerun()
                        else:
                            st.warning("Selecione pelo menos um influenciador")
                with col2:
                    if st.button("Cancelar", use_container_width=True):
                        st.session_state.show_add_inf_to_campaign = False
                        st.rerun()
        
        st.markdown("---")


def render_configuracoes_campanha(campanha):
    """Configuracoes gerais da campanha"""
    
    st.subheader("Configuracoes da Campanha")
    
    with st.form("form_config_campanha"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome da Campanha", value=campanha['nome'])
            objetivo = st.text_area("Objetivo", value=campanha.get('objetivo', ''), height=100)
            data_inicio = st.text_input("Data Inicio", value=campanha['data_inicio'], disabled=True)
        
        with col2:
            tipo_dados = st.selectbox(
                "Tipo de Dados",
                ["estatico", "dinamico"],
                index=0 if campanha.get('tipo_dados') == 'estatico' else 1,
                help="Estatico: usa dados do momento da adicao. Dinamico: atualiza via API"
            )
            is_aon = st.checkbox("Campanha AON", value=campanha.get('is_aon', False))
            data_fim = st.text_input("Data Fim", value=campanha['data_fim'], disabled=True)
            status = st.selectbox("Status", ["ativa", "pausada", "finalizada"],
                                 index=["ativa", "pausada", "finalizada"].index(campanha.get('status', 'ativa')))
        
        st.markdown("---")
        st.markdown("**Metricas a Coletar**")
        
        metricas = campanha.get('metricas_selecionadas', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            views = st.checkbox("Views", value=metricas.get('views', True))
            alcance = st.checkbox("Alcance", value=metricas.get('alcance', True))
        with col2:
            interacoes = st.checkbox("Interacoes", value=metricas.get('interacoes', True))
            impressoes = st.checkbox("Impressoes", value=metricas.get('impressoes', True))
        with col3:
            curtidas = st.checkbox("Curtidas", value=metricas.get('curtidas', True))
            comentarios_check = st.checkbox("Comentarios", value=metricas.get('comentarios', True))
        with col4:
            compartilhamentos = st.checkbox("Compartilhamentos", value=metricas.get('compartilhamentos', True))
            saves = st.checkbox("Saves", value=metricas.get('saves', True))
        
        col1, col2 = st.columns(2)
        with col1:
            clique_link = st.checkbox("Cliques Link (Stories)", value=metricas.get('clique_link', False))
        with col2:
            cupom_conversoes = st.checkbox("Conversoes Cupom", value=metricas.get('cupom_conversoes', False))
        
        st.markdown("---")
        
        notas = st.text_area("Notas e Observacoes", value=campanha.get('notas', ''), height=150,
                            placeholder="Adicione notas, insights manuais, observacoes importantes...")
        
        if st.form_submit_button("Salvar Configuracoes", use_container_width=True):
            data_manager.atualizar_campanha(campanha['id'], {
                'nome': nome,
                'objetivo': objetivo,
                'tipo_dados': tipo_dados,
                'is_aon': is_aon,
                'status': status,
                'notas': notas,
                'metricas_selecionadas': {
                    'views': views, 'alcance': alcance, 'interacoes': interacoes,
                    'impressoes': impressoes, 'curtidas': curtidas, 'comentarios': comentarios_check,
                    'compartilhamentos': compartilhamentos, 'saves': saves,
                    'clique_link': clique_link, 'cupom_conversoes': cupom_conversoes
                }
            })
            st.success("Configuracoes salvas!")
            st.rerun()


def render_configurar_insights(campanha):
    """Configura quais insights aparecem no relatorio"""
    
    st.subheader("Configurar Insights do Relatorio")
    st.caption("Selecione quais insights automaticos devem aparecer no relatorio")
    
    insights = campanha.get('insights_config', {})
    
    with st.form("form_insights"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Insights Automaticos**")
            mostrar_engajamento = st.checkbox("Analise de Engajamento", value=insights.get('mostrar_engajamento', True))
            mostrar_alcance = st.checkbox("Analise de Alcance", value=insights.get('mostrar_alcance', True))
            mostrar_conversao = st.checkbox("Analise de Conversao", value=insights.get('mostrar_conversao', True))
            mostrar_saves = st.checkbox("Analise de Saves", value=insights.get('mostrar_saves', True))
        
        with col2:
            st.markdown("**Secoes do Relatorio**")
            mostrar_comparativo_formato = st.checkbox("Comparativo por Formato", value=insights.get('mostrar_comparativo_formato', True))
            mostrar_top_influenciadores = st.checkbox("Top Influenciadores", value=insights.get('mostrar_top_influenciadores', True))
        
        st.markdown("---")
        st.markdown("**Insights Personalizados**")
        st.caption("Adicione insights manuais que devem aparecer no relatorio")
        
        insights_personalizados = insights.get('insights_personalizados', [])
        
        for idx, insight in enumerate(insights_personalizados):
            st.text_input(f"Insight {idx+1}", value=insight, key=f"insight_{idx}", disabled=True)
        
        novo_insight = st.text_input("Novo Insight", placeholder="Digite um insight personalizado...")
        
        if st.form_submit_button("Salvar Configuracao de Insights", use_container_width=True):
            novos_personalizados = insights_personalizados.copy()
            if novo_insight:
                novos_personalizados.append(novo_insight)
            
            data_manager.atualizar_campanha(campanha['id'], {
                'insights_config': {
                    'mostrar_engajamento': mostrar_engajamento,
                    'mostrar_alcance': mostrar_alcance,
                    'mostrar_conversao': mostrar_conversao,
                    'mostrar_saves': mostrar_saves,
                    'mostrar_comparativo_formato': mostrar_comparativo_formato,
                    'mostrar_top_influenciadores': mostrar_top_influenciadores,
                    'insights_personalizados': novos_personalizados
                }
            })
            st.success("Configuracao de insights salva!")
            st.rerun()


def render_categorias_comentarios(campanha):
    """Configura categorias para classificacao de comentarios pela IA"""
    
    st.subheader("Categorias para Classificacao de Comentarios")
    st.caption("Configure as categorias que a IA usara para classificar os comentarios")
    
    categorias = campanha.get('categorias_comentarios', [
        'Elogio ao Produto', 'Intencao de Compra', 'Conexao Emocional', 'Duvida', 'Critica', 'Geral'
    ])
    
    st.markdown("**Categorias Atuais:**")
    
    for idx, cat in enumerate(categorias):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"{idx+1}. {cat}")
        with col2:
            if st.button("X", key=f"rem_cat_{idx}", help="Remover categoria"):
                categorias.pop(idx)
                data_manager.atualizar_campanha(campanha['id'], {'categorias_comentarios': categorias})
                st.rerun()
    
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        nova_categoria = st.text_input("Nova Categoria", placeholder="Ex: Perguntas sobre Preco")
    with col2:
        st.write("")
        st.write("")
        if st.button("Adicionar", use_container_width=True):
            if nova_categoria and nova_categoria not in categorias:
                categorias.append(nova_categoria)
                data_manager.atualizar_campanha(campanha['id'], {'categorias_comentarios': categorias})
                st.success("Categoria adicionada!")
                st.rerun()
    
    st.markdown("---")
    st.info("A IA classificara automaticamente os comentarios nas categorias definidas acima, alem de determinar se sao positivos, neutros ou negativos.")
