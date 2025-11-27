"""
Pagina: Relatorios
Relatorio completo unificado - funciona para campanha individual ou grupo de campanhas
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
from collections import Counter
from utils import data_manager, funcoes_auxiliares

def render():
    """Renderiza relatorio completo"""
    
    # Determinar modo de visualizacao
    modo = st.session_state.get('modo_relatorio', 'campanha')
    
    if modo == 'campanha':
        render_relatorio_campanha()
    else:
        render_relatorio_cliente()


def render_relatorio_campanha():
    """Relatorio de uma campanha individual"""
    
    campanha = data_manager.get_campanha(st.session_state.campanha_atual_id)
    
    if not campanha:
        st.error("Campanha nao encontrada")
        return
    
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        aon_badge = "[AON]" if campanha.get('is_aon') else ""
        st.markdown(f'<p class="main-header">{campanha["nome"]} {aon_badge}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="subtitle">{campanha["cliente_nome"]} | {funcoes_auxiliares.formatar_data_br(campanha["data_inicio"])} - {funcoes_auxiliares.formatar_data_br(campanha["data_fim"])}</p>', unsafe_allow_html=True)
    with col2:
        if st.button("<- Voltar", use_container_width=True):
            st.session_state.campanha_atual_id = None
            st.session_state.current_page = 'Campanhas'
            st.rerun()
    
    # Passar lista com uma campanha para o relatorio unificado
    render_relatorio_completo([campanha], campanha.get('is_aon', False))


def render_relatorio_cliente():
    """Relatorio de um cliente (multiplas campanhas)"""
    
    cliente_id = st.session_state.get('filtro_cliente_id')
    cliente = data_manager.get_cliente(cliente_id)
    
    if not cliente:
        st.error("Cliente nao encontrado")
        return
    
    campanhas_cliente = data_manager.get_campanhas_por_cliente(cliente_id)
    
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f'<p class="main-header">Relatorio: {cliente["nome"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="subtitle">{len(campanhas_cliente)} campanhas disponiveis</p>', unsafe_allow_html=True)
    with col2:
        if st.button("<- Voltar", use_container_width=True):
            st.session_state.filtro_cliente_id = None
            st.session_state.current_page = 'Clientes'
            st.rerun()
    
    # Seletor de campanhas
    st.markdown("---")
    st.subheader("Selecione as Campanhas para o Relatorio")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        nomes_campanhas = [c['nome'] for c in campanhas_cliente]
        campanhas_selecionadas = st.multiselect(
            "Campanhas:",
            nomes_campanhas,
            default=nomes_campanhas,
            key="sel_campanhas"
        )
    
    with col2:
        if st.button("Selecionar Todas", use_container_width=True):
            st.session_state.sel_campanhas = nomes_campanhas
            st.rerun()
    
    # Filtrar campanhas selecionadas
    campanhas_filtradas = [c for c in campanhas_cliente if c['nome'] in campanhas_selecionadas]
    
    if not campanhas_filtradas:
        st.warning("Selecione pelo menos uma campanha")
        return
    
    # Verificar se alguma campanha e AON
    has_aon = any(c.get('is_aon') for c in campanhas_filtradas)
    
    st.markdown("---")
    
    # Renderizar relatorio unificado
    render_relatorio_completo(campanhas_filtradas, has_aon)


def render_relatorio_completo(campanhas_list, is_aon=False):
    """Renderiza o relatorio completo para uma ou mais campanhas"""
    
    # Calcular metricas agregadas
    metricas = data_manager.calcular_metricas_multiplas_campanhas(campanhas_list)
    air_score = funcoes_auxiliares.calcular_air_score_agregado(campanhas_list)
    cores = funcoes_auxiliares.get_cores_graficos()
    
    # Criar tabs do relatorio
    if is_aon:
        tabs = st.tabs([
            "Visao Geral",
            "Graficos AON",
            "Performance por Formato",
            "Top Conteudo",
            "Influenciadores",
            "Comentarios",
            "Configuracao"
        ])
        tab_idx_offset = 0
    else:
        tabs = st.tabs([
            "Visao Geral",
            "Performance por Formato",
            "Top Conteudo",
            "Influenciadores",
            "Comentarios",
            "Configuracao"
        ])
        tab_idx_offset = -1
    
    # ========================================
    # TAB: VISAO GERAL (BIG NUMBERS + INSIGHTS)
    # ========================================
    with tabs[0]:
        render_visao_geral(campanhas_list, metricas, air_score, cores)
    
    # ========================================
    # TAB: GRAFICOS AON (se aplicavel)
    # ========================================
    if is_aon:
        with tabs[1]:
            render_graficos_aon(campanhas_list, cores)
    
    # ========================================
    # TAB: PERFORMANCE POR FORMATO
    # ========================================
    with tabs[2 + tab_idx_offset]:
        render_performance_formato(campanhas_list, cores)
    
    # ========================================
    # TAB: TOP CONTEUDO
    # ========================================
    with tabs[3 + tab_idx_offset]:
        render_top_conteudo(campanhas_list, cores)
    
    # ========================================
    # TAB: INFLUENCIADORES
    # ========================================
    with tabs[4 + tab_idx_offset]:
        render_influenciadores(campanhas_list, cores)
    
    # ========================================
    # TAB: COMENTARIOS
    # ========================================
    with tabs[5 + tab_idx_offset]:
        render_comentarios(campanhas_list, cores)
    
    # ========================================
    # TAB: CONFIGURACAO
    # ========================================
    with tabs[6 + tab_idx_offset]:
        render_configuracao(campanhas_list)


def render_visao_geral(campanhas_list, metricas, air_score, cores):
    """Renderiza a visao geral com big numbers e insights"""
    
    st.subheader("Visao Geral")
    
    # AIR Score e Big Numbers
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.markdown(f"""
        <div class='air-score-card'>
            <div class='air-score-number'>{air_score}</div>
            <div class='air-score-label'>AIR SCORE</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Linha 1
        col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)
        
        with col_a:
            st.metric("Campanhas", metricas['total_campanhas'])
        with col_b:
            st.metric("Influenciadores", metricas['total_influenciadores'])
        with col_c:
            st.metric("Seguidores", funcoes_auxiliares.formatar_numero(metricas['total_seguidores']))
        with col_d:
            st.metric("Posts", metricas['total_posts'])
        with col_e:
            st.metric("Views", funcoes_auxiliares.formatar_numero(metricas['total_views']))
        with col_f:
            st.metric("Alcance", funcoes_auxiliares.formatar_numero(metricas['total_alcance']))
        
        # Linha 2
        col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)
        
        with col_a:
            st.metric("Impressoes", funcoes_auxiliares.formatar_numero(metricas['total_impressoes']))
        with col_b:
            st.metric("Interacoes", funcoes_auxiliares.formatar_numero(metricas['total_interacoes']))
        with col_c:
            st.metric("Curtidas", funcoes_auxiliares.formatar_numero(metricas['total_curtidas']))
        with col_d:
            st.metric("Comentarios", funcoes_auxiliares.formatar_numero(metricas['total_comentarios']))
        with col_e:
            st.metric("Taxa Eng.", f"{metricas['engajamento_efetivo']}%")
        with col_f:
            st.metric("Taxa Alcance", f"{metricas['taxa_alcance']}%")
    
    st.markdown("---")
    
    if metricas['total_posts'] == 0:
        st.info("Adicione posts aos influenciadores para ver analises detalhadas")
        return
    
    # INSIGHTS AUTOMATICOS
    st.subheader("Insights Automaticos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Insight de engajamento
        if metricas['engajamento_efetivo'] > 5:
            st.success(f"Engajamento Excelente: Taxa de {metricas['engajamento_efetivo']}% esta acima da referencia de mercado (3-5%)")
        elif metricas['engajamento_efetivo'] > 3:
            st.info(f"Engajamento Adequado: Taxa de {metricas['engajamento_efetivo']}% esta dentro da referencia de mercado")
        else:
            st.warning(f"Atencao: Taxa de {metricas['engajamento_efetivo']}% esta abaixo da referencia. Considere ajustar a estrategia")
        
        # Saves
        if metricas['total_saves'] > 0 and metricas['total_views'] > 0:
            taxa_saves = (metricas['total_saves'] / metricas['total_views'] * 100)
            if taxa_saves > 2:
                st.success(f"Alto Valor Percebido: {metricas['total_saves']:,} saves ({taxa_saves:.2f}% dos views)")
    
    with col2:
        # Melhor formato
        dados_formato = coletar_dados_formato(campanhas_list)
        if dados_formato:
            df = pd.DataFrame(dados_formato)
            df_agg = df.groupby('Formato')['Views'].sum().reset_index()
            melhor = df_agg.loc[df_agg['Views'].idxmax()]
            st.info(f"Formato Mais Efetivo: {melhor['Formato']} gerou {melhor['Views']:,} views")
        
        # Conversoes
        if metricas['total_conversoes_cupom'] > 0:
            st.success(f"ROI Rastreavel: {metricas['total_conversoes_cupom']} conversoes via cupom")
    
    st.markdown("---")
    
    # NOTAS
    st.subheader("Notas e Observacoes")
    
    # Pegar notas da primeira campanha (ou criar campo consolidado)
    notas_atuais = campanhas_list[0].get('notas', '') if len(campanhas_list) == 1 else ''
    
    notas = st.text_area(
        "Adicione suas observacoes:",
        value=notas_atuais,
        height=150,
        placeholder="Digite aqui suas notas, insights e observacoes..."
    )
    
    if len(campanhas_list) == 1 and st.button("Salvar Notas"):
        campanhas_list[0]['notas'] = notas
        st.success("Notas salvas!")


def render_graficos_aon(campanhas_list, cores):
    """Renderiza graficos de evolucao temporal (AON)"""
    
    st.subheader("Graficos Dinamicos - Evolucao Temporal")
    st.caption("Funcionalidade disponivel para campanhas AON")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Coletar influenciadores de todas as campanhas
        todos_influs = []
        for camp in campanhas_list:
            for inf in camp['influenciadores']:
                if inf['nome'] not in todos_influs:
                    todos_influs.append(inf['nome'])
        
        influs_opcoes = ["Todos"] + todos_influs
        filtro_influ = st.selectbox("Influenciador", influs_opcoes)
    
    with col2:
        filtro_data_ini = st.date_input("De:", value=datetime.now() - timedelta(days=30), key="aon_ini")
    
    with col3:
        filtro_data_fim = st.date_input("Ate:", value=datetime.now(), key="aon_fim")
    
    metrica_temporal = st.selectbox("Metrica:", ["Views", "Alcance", "Interacoes", "Impressoes"])
    
    st.markdown("---")
    
    # Coletar dados temporais
    dados_tempo = []
    
    for camp in campanhas_list:
        for inf in camp['influenciadores']:
            if filtro_influ != "Todos" and inf['nome'] != filtro_influ:
                continue
            
            for post in inf['posts']:
                try:
                    data_post = datetime.strptime(post['data_publicacao'], '%d/%m/%Y')
                    
                    if filtro_data_ini <= data_post.date() <= filtro_data_fim:
                        metrica_map = {
                            'Views': post['metricas']['views'],
                            'Alcance': post['metricas'].get('alcance', 0),
                            'Interacoes': post['metricas']['interacoes'],
                            'Impressoes': post['metricas'].get('impressoes', 0)
                        }
                        
                        dados_tempo.append({
                            'Data': data_post,
                            'Valor': metrica_map[metrica_temporal],
                            'Influenciador': inf['nome'],
                            'Formato': post['formato'],
                            'Campanha': camp['nome']
                        })
                except:
                    pass
    
    if not dados_tempo:
        st.warning("Nenhum post no periodo selecionado")
        return
    
    df_tempo = pd.DataFrame(dados_tempo)
    df_tempo = df_tempo.sort_values('Data')
    
    # Agregar por data
    df_tempo_agg = df_tempo.groupby('Data')['Valor'].sum().reset_index()
    df_tempo_agg['Acumulado'] = df_tempo_agg['Valor'].cumsum()
    
    # Grafico combinado barra + linha
    fig1 = go.Figure()
    
    fig1.add_trace(go.Bar(
        x=df_tempo_agg['Data'],
        y=df_tempo_agg['Valor'],
        name=f'{metrica_temporal} Diario',
        marker_color=cores[0],
        opacity=0.7
    ))
    
    fig1.add_trace(go.Scatter(
        x=df_tempo_agg['Data'],
        y=df_tempo_agg['Acumulado'],
        name='Acumulado',
        mode='lines+markers',
        yaxis='y2',
        line=dict(color=cores[1], width=3),
        marker=dict(size=8)
    ))
    
    fig1.update_layout(
        title=f'Evolucao de {metrica_temporal}',
        yaxis=dict(title=f'{metrica_temporal} Diario'),
        yaxis2=dict(title='Acumulado', overlaying='y', side='right'),
        height=450,
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # Graficos lado a lado
    col1, col2 = st.columns(2)
    
    with col1:
        if filtro_influ == "Todos":
            df_by_inf = df_tempo.groupby('Influenciador')['Valor'].sum().reset_index()
            df_by_inf = df_by_inf.sort_values('Valor', ascending=True)
            
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=df_by_inf['Valor'],
                y=df_by_inf['Influenciador'],
                orientation='h',
                marker_color=cores[2],
                text=[funcoes_auxiliares.formatar_numero(v) for v in df_by_inf['Valor']],
                textposition='outside'
            ))
            fig2.update_layout(title=f'{metrica_temporal} por Influenciador', height=400)
            st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        df_by_formato = df_tempo.groupby('Formato')['Valor'].sum().reset_index()
        
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=df_by_formato['Formato'],
            y=df_by_formato['Valor'],
            marker_color=cores[3],
            text=[funcoes_auxiliares.formatar_numero(v) for v in df_by_formato['Valor']],
            textposition='outside'
        ))
        fig3.update_layout(title=f'{metrica_temporal} por Formato', height=400)
        st.plotly_chart(fig3, use_container_width=True)


def coletar_dados_formato(campanhas_list):
    """Coleta dados de formato de todas as campanhas"""
    dados = []
    for camp in campanhas_list:
        for inf in camp['influenciadores']:
            for post in inf['posts']:
                dados.append({
                    'Formato': post['formato'],
                    'Views': post['metricas']['views'],
                    'Alcance': post['metricas'].get('alcance', 0),
                    'Interacoes': post['metricas']['interacoes'],
                    'Impressoes': post['metricas'].get('impressoes', 0)
                })
    return dados


def render_performance_formato(campanhas_list, cores):
    """Renderiza analise de performance por formato"""
    
    st.subheader("Performance por Formato")
    
    dados_formato = coletar_dados_formato(campanhas_list)
    
    if not dados_formato:
        st.info("Adicione posts para ver a analise por formato")
        return
    
    # Seletor de metrica
    col1, col2 = st.columns(2)
    
    with col1:
        metrica_selecionada = st.selectbox(
            "Metrica para analise:",
            ["Views", "Alcance", "Interacoes", "Impressoes"]
        )
    
    df = pd.DataFrame(dados_formato)
    df_agg = df.groupby('Formato')[metrica_selecionada].sum().reset_index()
    
    # Calcular percentual
    total = df_agg[metrica_selecionada].sum()
    df_agg['Percentual'] = (df_agg[metrica_selecionada] / total * 100).round(1)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Grafico de barras com percentual
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_agg['Formato'],
            y=df_agg['Percentual'],
            text=[f"{p}%" for p in df_agg['Percentual']],
            textposition='outside',
            marker_color=cores[:len(df_agg)]
        ))
        
        fig.update_layout(
            title=f'Distribuicao de {metrica_selecionada} por Formato (%)',
            yaxis_title='Percentual (%)',
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Grafico RADAR para performance por tamanho de influenciador
        st.markdown("### Performance por Tamanho de Influenciador")
        
        dados_class = []
        for camp in campanhas_list:
            for inf in camp['influenciadores']:
                total_valor = 0
                for post in inf['posts']:
                    metrica_map = {
                        'Views': post['metricas']['views'],
                        'Alcance': post['metricas'].get('alcance', 0),
                        'Interacoes': post['metricas']['interacoes'],
                        'Impressoes': post['metricas'].get('impressoes', 0)
                    }
                    total_valor += metrica_map[metrica_selecionada]
                
                if total_valor > 0:
                    dados_class.append({
                        'Classificacao': inf['classificacao'],
                        'Valor': total_valor
                    })
        
        if dados_class:
            df_class = pd.DataFrame(dados_class)
            df_class_agg = df_class.groupby('Classificacao')['Valor'].sum().reset_index()
            
            ordem = ['Nano', 'Micro', 'Mid', 'Macro', 'Mega']
            df_class_agg['ordem'] = df_class_agg['Classificacao'].apply(
                lambda x: ordem.index(x) if x in ordem else 99
            )
            df_class_agg = df_class_agg.sort_values('ordem')
            
            fig_radar = go.Figure()
            
            fig_radar.add_trace(go.Scatterpolar(
                r=df_class_agg['Valor'].tolist() + [df_class_agg['Valor'].iloc[0]],
                theta=df_class_agg['Classificacao'].tolist() + [df_class_agg['Classificacao'].iloc[0]],
                fill='toself',
                fillcolor=f'rgba(124, 58, 237, 0.3)',
                line=dict(color=cores[0], width=2),
                name=metrica_selecionada
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, max(df_class_agg['Valor']) * 1.1])
                ),
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
    
    st.markdown("---")
    
    # Desempenho por classificacao (grafico combinado)
    st.subheader("Desempenho por Classificacao de Influenciador")
    
    if dados_class:
        df_class = pd.DataFrame(dados_class)
        df_class_agg = df_class.groupby('Classificacao').agg({
            'Valor': ['sum', 'mean', 'count']
        }).reset_index()
        df_class_agg.columns = ['Classificacao', 'Total', 'Media', 'Qtd']
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_class_agg['Classificacao'],
            y=df_class_agg['Total'],
            name='Total',
            marker_color=cores[0]
        ))
        
        fig.add_trace(go.Scatter(
            x=df_class_agg['Classificacao'],
            y=df_class_agg['Qtd'],
            name='Qtd Influs',
            mode='lines+markers',
            yaxis='y2',
            line=dict(color=cores[1], width=3),
            marker=dict(size=10)
        ))
        
        fig.update_layout(
            title=f'{metrica_selecionada} por Classificacao',
            yaxis=dict(title='Total'),
            yaxis2=dict(title='Qtd Influenciadores', overlaying='y', side='right'),
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_top_conteudo(campanhas_list, cores):
    """Renderiza top conteudo"""
    
    st.subheader("Top Conteudo - Melhores Posts")
    
    # Coletar todos os posts
    todos_posts = []
    
    for camp in campanhas_list:
        for inf in camp['influenciadores']:
            for post in inf['posts']:
                views = post['metricas']['views']
                interacoes = post['metricas']['interacoes']
                alcance = post['metricas'].get('alcance', views)
                seguidores = inf.get('seguidores_num', 1)
                
                taxa_eng = (interacoes / views * 100) if views > 0 else 0
                taxa_alcance = (alcance / seguidores * 100) if seguidores > 0 else 0
                
                todos_posts.append({
                    'campanha': camp['nome'],
                    'influenciador': inf['nome'],
                    'foto_inf': inf.get('foto', ''),
                    'classificacao': inf['classificacao'],
                    'formato': post['formato'],
                    'plataforma': post['plataforma'],
                    'views': views,
                    'interacoes': interacoes,
                    'alcance': alcance,
                    'taxa_eng': round(taxa_eng, 2),
                    'taxa_alcance': round(taxa_alcance, 2),
                    'imagens': post['imagens'],
                    'link': post.get('link_post', ''),
                    'data': post['data_publicacao']
                })
    
    if not todos_posts:
        st.info("Adicione posts para ver o top conteudo")
        return
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        metrica_ordem = st.selectbox(
            "Ordenar por:",
            ["Taxa de Engajamento", "Taxa de Alcance", "Views", "Interacoes"],
            key="top_metrica"
        )
    
    with col2:
        qtd_top = st.slider("Quantidade:", 5, 20, 10)
    
    with col3:
        formato_filtro = st.multiselect(
            "Filtrar formatos:",
            ["Reels", "Stories", "Carrossel", "Feed", "TikTok", "YouTube"]
        )
    
    # Filtrar por formato
    if formato_filtro:
        todos_posts = [p for p in todos_posts if p['formato'] in formato_filtro]
    
    if not todos_posts:
        st.warning("Nenhum post encontrado com os filtros selecionados")
        return
    
    # Ordenar
    ordem_map = {
        "Taxa de Engajamento": "taxa_eng",
        "Taxa de Alcance": "taxa_alcance",
        "Views": "views",
        "Interacoes": "interacoes"
    }
    todos_posts.sort(key=lambda x: x[ordem_map[metrica_ordem]], reverse=True)
    
    st.markdown("---")
    
    # Lista de top posts
    st.markdown(f"### Top {qtd_top} Posts por {metrica_ordem}")
    
    for idx, post in enumerate(todos_posts[:qtd_top], 1):
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([0.5, 1.5, 2, 1.5, 1.5, 1])
            
            with col1:
                medals = ['1o', '2o', '3o'] + [f'{i}o' for i in range(4, 21)]
                st.markdown(f"### {medals[idx-1]}")
            
            with col2:
                if post['imagens']:
                    try:
                        img_bytes = base64.b64decode(post['imagens'][0])
                        st.image(img_bytes, width=80)
                    except:
                        if post['foto_inf']:
                            st.image(post['foto_inf'], width=80)
                elif post['foto_inf']:
                    st.image(post['foto_inf'], width=80)
            
            with col3:
                st.markdown(f"**{post['influenciador']}**")
                st.caption(f"{post['formato']} | {post['plataforma']} | {post['data']}")
                if len(campanhas_list) > 1:
                    st.caption(f"Campanha: {post['campanha']}")
                if post['link']:
                    st.markdown(f"[Ver Post]({post['link']})")
            
            with col4:
                st.metric("Taxa Eng.", f"{post['taxa_eng']}%")
                st.caption(f"Views: {funcoes_auxiliares.formatar_numero(post['views'])}")
            
            with col5:
                st.metric("Taxa Alcance", f"{post['taxa_alcance']}%")
                st.caption(f"Alcance: {funcoes_auxiliares.formatar_numero(post['alcance'])}")
            
            with col6:
                st.metric("Interacoes", funcoes_auxiliares.formatar_numero(post['interacoes']))
            
            st.markdown("---")
    
    # Tabela resumo
    st.markdown("### Tabela Completa")
    
    df_posts = pd.DataFrame(todos_posts[:qtd_top])
    df_display = df_posts[['influenciador', 'formato', 'data', 'views', 'alcance', 
                           'interacoes', 'taxa_eng', 'taxa_alcance', 'link']]
    df_display.columns = ['Influenciador', 'Formato', 'Data', 'Views', 'Alcance', 
                          'Interacoes', 'Taxa Eng. %', 'Taxa Alcance %', 'Link']
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)


def render_influenciadores(campanhas_list, cores):
    """Renderiza gestao de influenciadores"""
    
    st.subheader("Influenciadores")
    
    # Calcular metricas por influenciador
    dados_influs = {}
    
    for camp in campanhas_list:
        for inf in camp['influenciadores']:
            key = inf.get('base_id', inf['id'])
            
            if key not in dados_influs:
                dados_influs[key] = {
                    'nome': inf['nome'],
                    'usuario': inf['usuario'],
                    'foto': inf.get('foto', ''),
                    'classificacao': inf['classificacao'],
                    'seguidores': inf.get('seguidores_num', 0),
                    'posts': 0,
                    'views': 0,
                    'interacoes': 0,
                    'alcance': 0,
                    'campanhas': [],
                    'inf_obj': inf
                }
            
            dados_influs[key]['campanhas'].append(camp['nome'])
            
            for post in inf['posts']:
                dados_influs[key]['posts'] += 1
                dados_influs[key]['views'] += post['metricas']['views']
                dados_influs[key]['interacoes'] += post['metricas']['interacoes']
                dados_influs[key]['alcance'] += post['metricas'].get('alcance', 0)
    
    # Converter para lista
    lista_influs = []
    for key, dados in dados_influs.items():
        taxa_eng = (dados['interacoes'] / dados['views'] * 100) if dados['views'] > 0 else 0
        taxa_alcance = (dados['alcance'] / dados['seguidores'] * 100) if dados['seguidores'] > 0 else 0
        
        lista_influs.append({
            **dados,
            'taxa_eng': round(taxa_eng, 2),
            'taxa_alcance': round(taxa_alcance, 2)
        })
    
    if not lista_influs:
        st.info("Nenhum influenciador nas campanhas selecionadas")
        
        if len(campanhas_list) == 1:
            if st.button("+ Adicionar Influenciador"):
                st.session_state.show_add_inf_camp = True
            
            if st.session_state.get('show_add_inf_camp', False):
                render_form_add_influenciador(campanhas_list[0])
        return
    
    st.markdown(f"**{len(lista_influs)} influenciadores encontrados**")
    
    for dados in sorted(lista_influs, key=lambda x: x['views'], reverse=True):
        with st.expander(f"{dados['nome']} - {dados['posts']} posts - {dados['classificacao']}"):
            col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
            
            with col1:
                if dados.get('foto'):
                    st.image(dados['foto'], width=80)
            
            with col2:
                st.write(f"**{dados['usuario']}**")
                st.write(f"Seguidores: {funcoes_auxiliares.formatar_numero(dados['seguidores'])}")
                if len(dados['campanhas']) > 1:
                    st.caption(f"Campanhas: {', '.join(set(dados['campanhas']))}")
            
            with col3:
                st.metric("Taxa Eng.", f"{dados['taxa_eng']}%")
                st.metric("Views", funcoes_auxiliares.formatar_numero(dados['views']))
            
            with col4:
                st.metric("Taxa Alcance", f"{dados['taxa_alcance']}%")
                st.metric("Interacoes", funcoes_auxiliares.formatar_numero(dados['interacoes']))
            
            if len(campanhas_list) == 1:
                if st.button("+ Adicionar Post", key=f"add_post_{dados['inf_obj']['id']}"):
                    st.session_state.current_influencer_id = dados['inf_obj']['id']
                    st.session_state.show_add_post = True
                
                if (st.session_state.get('show_add_post', False) and 
                    st.session_state.get('current_influencer_id') == dados['inf_obj']['id']):
                    render_form_post(campanhas_list[0], dados['inf_obj'])
                
                if dados['inf_obj']['posts']:
                    st.markdown("---")
                    st.markdown("**Posts:**")
                    
                    for post in dados['inf_obj']['posts']:
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        
                        with col1:
                            st.write(f"**{post['formato']}** ({post['plataforma']})")
                            st.caption(post['data_publicacao'])
                            if post.get('link_post'):
                                st.markdown(f"[Link]({post['link_post']})")
                        
                        with col2:
                            st.write(f"Views: {post['metricas']['views']:,}")
                        
                        with col3:
                            st.write(f"Interacoes: {post['metricas']['interacoes']:,}")
                        
                        with col4:
                            if post['imagens']:
                                try:
                                    img_bytes = base64.b64decode(post['imagens'][0])
                                    st.image(img_bytes, width=50)
                                except:
                                    pass
    
    if len(campanhas_list) == 1:
        st.markdown("---")
        if st.button("+ Adicionar Influenciador a Campanha"):
            st.session_state.show_add_inf_camp = True
        
        if st.session_state.get('show_add_inf_camp', False):
            render_form_add_influenciador(campanhas_list[0])


def render_form_add_influenciador(campanha):
    """Formulario para adicionar influenciador"""
    
    if st.session_state.influenciadores_base:
        opcoes_inf = [f"{i['nome']} ({i['usuario']}) - {i['classificacao']}" 
                     for i in st.session_state.influenciadores_base]
        inf_sel = st.selectbox("Selecione o influenciador", opcoes_inf)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Adicionar a Campanha", use_container_width=True):
                nome_sel = inf_sel.split(" (")[0]
                inf_obj = next((i for i in st.session_state.influenciadores_base 
                              if i['nome'] == nome_sel), None)
                if inf_obj:
                    data_manager.adicionar_influenciador_campanha(campanha['id'], inf_obj['id'])
                    st.session_state.show_add_inf_camp = False
                    st.success("Influenciador adicionado!")
                    st.rerun()
        with col2:
            if st.button("Cancelar", use_container_width=True, key="cancel_inf"):
                st.session_state.show_add_inf_camp = False
                st.rerun()
    else:
        st.warning("Cadastre influenciadores na base primeiro")
        if st.button("Ir para Influenciadores"):
            st.session_state.current_page = 'Influenciadores'
            st.rerun()


def render_form_post(campanha, inf):
    """Formulario para adicionar post"""
    
    with st.form(f"form_post_{inf['id']}"):
        st.markdown("##### Novo Post")
        
        col1, col2, col3 = st.columns(3)
        
        metricas_camp = campanha.get('metricas_selecionadas', {})
        
        with col1:
            formato = st.selectbox("Formato *", 
                                  ["Reels", "Stories", "Carrossel", "Feed", "TikTok", "YouTube"])
            plataforma = st.selectbox("Plataforma *", inf['redes_sociais'])
            data_pub = st.date_input("Data *", value=datetime.now())
            link_post = st.text_input("Link do Post", placeholder="https://...")
        
        with col2:
            views = st.number_input("Views *", min_value=0, value=0) if metricas_camp.get('views', True) else 0
            alcance = st.number_input("Alcance", min_value=0, value=0) if metricas_camp.get('alcance', True) else 0
            interacoes = st.number_input("Interacoes *", min_value=0, value=0) if metricas_camp.get('interacoes', True) else 0
            impressoes = st.number_input("Impressoes", min_value=0, value=0) if metricas_camp.get('impressoes', True) else 0
        
        with col3:
            curtidas = st.number_input("Curtidas", min_value=0, value=0) if metricas_camp.get('curtidas', True) else 0
            comentarios = st.number_input("Comentarios", min_value=0, value=0) if metricas_camp.get('comentarios', True) else 0
            compartilhamentos = st.number_input("Compartilh.", min_value=0, value=0) if metricas_camp.get('compartilhamentos', True) else 0
            saves = st.number_input("Saves", min_value=0, value=0) if metricas_camp.get('saves', True) else 0
        
        clique_link = 0
        if formato == "Stories" and metricas_camp.get('clique_link', False):
            clique_link = st.number_input("Cliques Link", min_value=0, value=0)
        
        cupom_codigo = ""
        cupom_conversoes = 0
        if metricas_camp.get('cupom_conversoes', False):
            cupom_codigo = st.text_input("Codigo Cupom", placeholder="PROMO10")
            if cupom_codigo:
                cupom_conversoes = st.number_input("Conversoes", min_value=0, value=0)
        
        st.markdown("**Imagens/Videos do Post**")
        imagens_upload = st.file_uploader(
            "Upload de midias",
            type=['png', 'jpg', 'jpeg', 'mp4', 'gif'],
            accept_multiple_files=True,
            key=f"upload_{inf['id']}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("Salvar Post", use_container_width=True):
                imagens_b64 = []
                if imagens_upload:
                    for img_file in imagens_upload:
                        img_bytes = img_file.read()
                        imagens_b64.append(base64.b64encode(img_bytes).decode())
                
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
                    'imagens': imagens_b64
                })
                st.session_state.show_add_post = False
                st.success("Post adicionado!")
                st.rerun()
        
        with col2:
            if st.form_submit_button("Cancelar", use_container_width=True):
                st.session_state.show_add_post = False
                st.rerun()


def render_comentarios(campanhas_list, cores):
    """Renderiza analise de comentarios"""
    
    st.subheader("Analise de Comentarios")
    
    todos_comentarios = []
    
    for camp in campanhas_list:
        for inf in camp['influenciadores']:
            for post in inf['posts']:
                for com in post.get('comentarios', []):
                    todos_comentarios.append({
                        'campanha': camp['nome'],
                        'influenciador': inf['nome'],
                        'post': f"{post['formato']} - {post['data_publicacao']}",
                        'texto': com['texto'],
                        'polaridade': com['polaridade'],
                        'categoria': com['categoria']
                    })
    
    if not todos_comentarios:
        st.info("Nenhum comentario classificado ainda")
        return
    
    total = len(todos_comentarios)
    positivos = len([c for c in todos_comentarios if c['polaridade'] == 'positivo'])
    neutros = len([c for c in todos_comentarios if c['polaridade'] == 'neutro'])
    negativos = len([c for c in todos_comentarios if c['polaridade'] == 'negativo'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Positivos", f"{positivos} ({positivos/total*100:.0f}%)")
    with col3:
        st.metric("Neutros", f"{neutros} ({neutros/total*100:.0f}%)")
    with col4:
        st.metric("Negativos", f"{negativos} ({negativos/total*100:.0f}%)")
    
    st.markdown("---")
    
    categorias_count = Counter([c['categoria'] for c in todos_comentarios])
    df_cat = pd.DataFrame(categorias_count.items(), columns=['Categoria', 'Quantidade'])
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_cat['Categoria'],
        y=df_cat['Quantidade'],
        marker_color=cores[:len(df_cat)]
    ))
    fig.update_layout(title='Comentarios por Categoria', height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Comentarios Recentes")
    
    for com in todos_comentarios[:20]:
        icon = {"positivo": "[+]", "neutro": "[~]", "negativo": "[-]"}
        st.write(f"{icon[com['polaridade']]} **{com['categoria']}** - {com['influenciador']}")
        st.caption(com['texto'][:200])
        st.markdown("---")


def render_configuracao(campanhas_list):
    """Renderiza configuracao das campanhas"""
    
    st.subheader("Configuracao")
    
    for camp in campanhas_list:
        with st.expander(f"Campanha: {camp['nome']}", expanded=len(campanhas_list)==1):
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Nome", value=camp['nome'], disabled=True, key=f"cfg_nome_{camp['id']}")
                st.text_input("Cliente", value=camp['cliente_nome'], disabled=True, key=f"cfg_cli_{camp['id']}")
                st.text_input("Periodo", 
                             value=f"{funcoes_auxiliares.formatar_data_br(camp['data_inicio'])} - {funcoes_auxiliares.formatar_data_br(camp['data_fim'])}", 
                             disabled=True, key=f"cfg_per_{camp['id']}")
            
            with col2:
                st.text_input("Tipo", value=camp.get('tipo_dados', 'estatico').title(), disabled=True, key=f"cfg_tipo_{camp['id']}")
                st.text_input("Status", value=camp['status'].title(), disabled=True, key=f"cfg_status_{camp['id']}")
                st.text_input("AON", value="Sim" if camp.get('is_aon') else "Nao", disabled=True, key=f"cfg_aon_{camp['id']}")
            
            st.text_area("Objetivo", value=camp['objetivo'], disabled=True, height=100, key=f"cfg_obj_{camp['id']}")
            
            st.markdown("**Metricas Configuradas:**")
            metricas_sel = camp.get('metricas_selecionadas', {})
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.write("[X] Views" if metricas_sel.get('views') else "[ ] Views")
                st.write("[X] Alcance" if metricas_sel.get('alcance') else "[ ] Alcance")
            with col2:
                st.write("[X] Interacoes" if metricas_sel.get('interacoes') else "[ ] Interacoes")
                st.write("[X] Impressoes" if metricas_sel.get('impressoes') else "[ ] Impressoes")
            with col3:
                st.write("[X] Curtidas" if metricas_sel.get('curtidas') else "[ ] Curtidas")
                st.write("[X] Comentarios" if metricas_sel.get('comentarios') else "[ ] Comentarios")
            with col4:
                st.write("[X] Saves" if metricas_sel.get('saves') else "[ ] Saves")
                st.write("[X] Cliques Link" if metricas_sel.get('clique_link') else "[ ] Cliques Link")
