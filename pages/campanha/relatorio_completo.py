"""
Relatório Completo da Campanha
TODAS as funcionalidades de análise em tabs
Versão 4.1 - Com melhorias solicitadas
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import random
from collections import Counter
from utils import data_manager, funcoes_auxiliares

def render():
    """Renderiza relatório completo da campanha"""
    
    campanha = data_manager.get_campanha(st.session_state.campanha_atual_id)
    
    if not campanha:
        st.error("Campanha não encontrada")
        return
    
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        aon_badge = "🔷 AON" if campanha.get('is_aon') else ""
        st.markdown(f'<p class="main-header">{campanha["nome"]} {aon_badge}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="subtitle">{campanha["cliente_nome"]}</p>', unsafe_allow_html=True)
    with col2:
        if st.button("← Voltar", use_container_width=True):
            st.session_state.campanha_atual_id = None
            st.rerun()
    
    # Filtros de data para o relatório
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        filtro_data_ini = st.date_input("De:", value=datetime.now() - timedelta(days=30), key="rel_data_ini")
    with col2:
        filtro_data_fim = st.date_input("Até:", value=datetime.now(), key="rel_data_fim")
    
    # AON é por campanha
    is_aon = campanha.get('is_aon', False)
    
    # Criar tabs baseado no tipo de campanha
    if is_aon:
        tabs_names = [
            "📊 Big Numbers", 
            "📈 Gráficos AON",
            "🏆 Top Conteúdo",
            "👤 Influenciadores", 
            "⚙️ Configuração",
            "💬 Comentários",
            "📖 Glossário"
        ]
    else:
        tabs_names = [
            "📊 Big Numbers", 
            "🏆 Top Conteúdo",
            "👤 Influenciadores", 
            "⚙️ Configuração",
            "💬 Comentários",
            "📖 Glossário"
        ]
    
    tabs = st.tabs(tabs_names)
    
    tab_idx = 0
    
    # ============================================
    # TAB: BIG NUMBERS
    # ============================================
    with tabs[tab_idx]:
        render_tab_big_numbers(campanha, filtro_data_ini, filtro_data_fim)
    tab_idx += 1
    
    # ============================================
    # TAB: GRÁFICOS AON (se aplicável)
    # ============================================
    if is_aon:
        with tabs[tab_idx]:
            render_tab_graficos_aon(campanha, filtro_data_ini, filtro_data_fim)
        tab_idx += 1
    
    # ============================================
    # TAB: TOP CONTEÚDO
    # ============================================
    with tabs[tab_idx]:
        render_tab_top_conteudo(campanha)
    tab_idx += 1
    
    # ============================================
    # TAB: INFLUENCIADORES
    # ============================================
    with tabs[tab_idx]:
        render_tab_influenciadores(campanha)
    tab_idx += 1
    
    # ============================================
    # TAB: CONFIGURAÇÃO
    # ============================================
    with tabs[tab_idx]:
        render_tab_configuracao(campanha)
    tab_idx += 1
    
    # ============================================
    # TAB: COMENTÁRIOS
    # ============================================
    with tabs[tab_idx]:
        render_tab_comentarios(campanha)
    tab_idx += 1
    
    # ============================================
    # TAB: GLOSSÁRIO
    # ============================================
    with tabs[tab_idx]:
        render_tab_glossario()


def render_tab_big_numbers(campanha, filtro_data_ini, filtro_data_fim):
    """Tab Big Numbers - Visão Geral com métricas melhoradas"""
    
    st.subheader("📊 Visão Geral da Campanha")
    
    metricas = data_manager.calcular_metricas_campanha(campanha)
    air_score = funcoes_auxiliares.calcular_air_score(campanha)
    cores = funcoes_auxiliares.get_cores_graficos()
    
    # AIR Score e Big Numbers principais
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.markdown(f"""
        <div class='air-score-card'>
            <div class='air-score-number'>{air_score}</div>
            <div class='air-score-label'>AIR SCORE</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Linha 1 de métricas
        col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)
        
        with col_a:
            st.metric("👤 Influenciadores", metricas['total_influenciadores'])
        with col_b:
            st.metric("📈 Seguidores", funcoes_auxiliares.formatar_numero(metricas['total_seguidores']))
        with col_c:
            st.metric("📱 Posts", metricas['total_posts'])
        with col_d:
            st.metric("👁️ Views", funcoes_auxiliares.formatar_numero(metricas['total_views']))
        with col_e:
            st.metric("🎯 Alcance", funcoes_auxiliares.formatar_numero(metricas['total_alcance']))
        with col_f:
            st.metric("💡 Impressões", funcoes_auxiliares.formatar_numero(metricas['total_impressoes']))
        
        # Linha 2 de métricas
        col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)
        
        with col_a:
            st.metric("❤️ Curtidas", funcoes_auxiliares.formatar_numero(metricas['total_curtidas']))
        with col_b:
            st.metric("💬 Comentários", funcoes_auxiliares.formatar_numero(metricas['total_comentarios']))
        with col_c:
            st.metric("🔗 Compartilh.", funcoes_auxiliares.formatar_numero(metricas['total_compartilhamentos']))
        with col_d:
            st.metric("📌 Saves", funcoes_auxiliares.formatar_numero(metricas['total_saves']))
        with col_e:
            st.metric("📈 Taxa Eng.", f"{metricas['engajamento_efetivo']}%")
        with col_f:
            st.metric("🎯 Taxa Alcance", f"{metricas['taxa_alcance']}%")
    
    st.markdown("---")
    
    if metricas['total_posts'] == 0:
        st.info("📊 Adicione posts aos influenciadores para ver análises")
        return
    
    # SELETOR DE MÉTRICAS PARA GRÁFICOS
    st.subheader("📈 Análise de Métricas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        metrica_selecionada = st.selectbox(
            "Selecione a métrica para análise:",
            ["Views", "Alcance", "Interações", "Impressões"],
            key="metrica_big"
        )
    
    with col2:
        tipo_grafico = st.radio(
            "Visualização:",
            ["Distribuição por Formato (%)", "Total por Formato"],
            horizontal=True
        )
    
    # Preparar dados por formato
    dados_formato = []
    for inf in campanha['influenciadores']:
        for post in inf['posts']:
            metrica_map = {
                'Views': post['metricas']['views'],
                'Alcance': post['metricas'].get('alcance', 0),
                'Interações': post['metricas']['interacoes'],
                'Impressões': post['metricas'].get('impressoes', 0)
            }
            dados_formato.append({
                'Formato': post['formato'],
                'Valor': metrica_map[metrica_selecionada]
            })
    
    if dados_formato:
        df_formato = pd.DataFrame(dados_formato)
        df_formato_agg = df_formato.groupby('Formato')['Valor'].sum().reset_index()
        
        # Calcular percentual
        total = df_formato_agg['Valor'].sum()
        df_formato_agg['Percentual'] = (df_formato_agg['Valor'] / total * 100).round(1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de barras com percentual
            if tipo_grafico == "Distribuição por Formato (%)":
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=df_formato_agg['Formato'],
                    y=df_formato_agg['Percentual'],
                    text=[f"{p}%" for p in df_formato_agg['Percentual']],
                    textposition='outside',
                    marker_color=cores[:len(df_formato_agg)]
                ))
                
                fig.update_layout(
                    title=f'Distribuição de {metrica_selecionada} por Formato (%)',
                    yaxis_title='Percentual (%)',
                    height=400,
                    showlegend=False
                )
            else:
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=df_formato_agg['Formato'],
                    y=df_formato_agg['Valor'],
                    text=[funcoes_auxiliares.formatar_numero(v) for v in df_formato_agg['Valor']],
                    textposition='outside',
                    marker_color=cores[:len(df_formato_agg)]
                ))
                
                fig.update_layout(
                    title=f'{metrica_selecionada} por Formato',
                    yaxis_title=metrica_selecionada,
                    height=400,
                    showlegend=False
                )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # GRÁFICO RADAR para performance por tamanho de influenciador
            st.markdown(f"### 🎯 Performance por Tamanho de Influenciador")
            
            dados_class = []
            for inf in campanha['influenciadores']:
                total_valor = 0
                for post in inf['posts']:
                    metrica_map = {
                        'Views': post['metricas']['views'],
                        'Alcance': post['metricas'].get('alcance', 0),
                        'Interações': post['metricas']['interacoes'],
                        'Impressões': post['metricas'].get('impressoes', 0)
                    }
                    total_valor += metrica_map[metrica_selecionada]
                
                if total_valor > 0:
                    dados_class.append({
                        'Classificação': inf['classificacao'],
                        'Valor': total_valor
                    })
            
            if dados_class:
                df_class = pd.DataFrame(dados_class)
                df_class_agg = df_class.groupby('Classificação')['Valor'].sum().reset_index()
                
                # Ordenar classificação
                ordem = ['Nano', 'Micro', 'Mid', 'Macro', 'Mega']
                df_class_agg['ordem'] = df_class_agg['Classificação'].apply(
                    lambda x: ordem.index(x) if x in ordem else 99
                )
                df_class_agg = df_class_agg.sort_values('ordem')
                
                # Gráfico Radar
                fig_radar = go.Figure()
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=df_class_agg['Valor'].tolist() + [df_class_agg['Valor'].iloc[0]],
                    theta=df_class_agg['Classificação'].tolist() + [df_class_agg['Classificação'].iloc[0]],
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
                    height=400,
                    title=f'{metrica_selecionada} por Classificação'
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)
    
    st.markdown("---")
    
    # CAMPO DE NOTAS/ESCRITA
    st.subheader("📝 Notas e Observações")
    
    notas = st.text_area(
        "Adicione suas observações sobre a campanha:",
        value=campanha.get('notas', ''),
        height=150,
        placeholder="Digite aqui suas notas, insights e observações sobre a campanha..."
    )
    
    if st.button("💾 Salvar Notas"):
        campanha['notas'] = notas
        st.success("✅ Notas salvas!")
    
    st.markdown("---")
    
    # INSIGHTS AUTOMÁTICOS
    st.subheader("💡 Insights Automáticos")
    
    # Melhor formato
    if dados_formato:
        melhor_formato = df_formato_agg.loc[df_formato_agg['Valor'].idxmax()]
        st.success(f"🏆 **Formato Mais Efetivo:** {melhor_formato['Formato']} representa {melhor_formato['Percentual']}% do total de {metrica_selecionada}")
    
    # Engajamento geral
    if metricas['engajamento_efetivo'] > 5:
        st.success(f"📈 **Engajamento Excelente:** Taxa de {metricas['engajamento_efetivo']}% está acima da referência de mercado (3-5%)")
    elif metricas['engajamento_efetivo'] > 3:
        st.info(f"📊 **Engajamento Adequado:** Taxa de {metricas['engajamento_efetivo']}% está dentro da referência de mercado")
    else:
        st.warning(f"⚠️ **Atenção:** Taxa de {metricas['engajamento_efetivo']}% está abaixo da referência. Considere ajustar a estratégia")


def render_tab_graficos_aon(campanha, filtro_data_ini, filtro_data_fim):
    """Tab Gráficos AON - Evolução temporal (somente campanhas AON)"""
    
    st.subheader("📈 Gráficos Dinâmicos - Evolução Temporal")
    st.caption("🔷 Funcionalidade exclusiva para campanhas AON")
    
    cores = funcoes_auxiliares.get_cores_graficos()
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        if campanha['influenciadores']:
            influs_opcoes = ["Todos"] + [inf['nome'] for inf in campanha['influenciadores']]
            filtro_influ = st.selectbox("Influenciador", influs_opcoes)
        else:
            filtro_influ = "Todos"
    
    with col2:
        metrica_temporal = st.selectbox(
            "Métrica para análise:",
            ["Views", "Alcance", "Interações", "Impressões"]
        )
    
    st.markdown("---")
    
    # Coletar dados temporais
    if not campanha['influenciadores'] or not any(inf['posts'] for inf in campanha['influenciadores']):
        st.info("📊 Adicione posts com datas para visualizar evolução temporal")
        return
    
    dados_tempo = []
    
    for inf in campanha['influenciadores']:
        if filtro_influ != "Todos" and inf['nome'] != filtro_influ:
            continue
        
        for post in inf['posts']:
            try:
                data_post = datetime.strptime(post['data_publicacao'], '%d/%m/%Y')
                
                # Filtrar por período
                if filtro_data_ini <= data_post.date() <= filtro_data_fim:
                    metrica_map = {
                        'Views': post['metricas']['views'],
                        'Alcance': post['metricas'].get('alcance', 0),
                        'Interações': post['metricas']['interacoes'],
                        'Impressões': post['metricas'].get('impressoes', 0)
                    }
                    
                    dados_tempo.append({
                        'Data': data_post,
                        'Valor': metrica_map[metrica_temporal],
                        'Influenciador': inf['nome'],
                        'Formato': post['formato']
                    })
            except:
                pass
    
    if not dados_tempo:
        st.warning("⚠️ Nenhum post no período selecionado")
        return
    
    df_tempo = pd.DataFrame(dados_tempo)
    df_tempo = df_tempo.sort_values('Data')
    
    # Gráfico combinado barra + linha
    st.markdown(f"### 📈 Evolução de {metrica_temporal} ao Longo do Tempo")
    
    # Agregar por data
    df_tempo_agg = df_tempo.groupby('Data')['Valor'].sum().reset_index()
    df_tempo_agg['Acumulado'] = df_tempo_agg['Valor'].cumsum()
    
    fig1 = go.Figure()
    
    # Barras para valores diários
    fig1.add_trace(go.Bar(
        x=df_tempo_agg['Data'],
        y=df_tempo_agg['Valor'],
        name=f'{metrica_temporal} Diário',
        marker_color=cores[0],
        opacity=0.7
    ))
    
    # Linha para acumulado
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
        yaxis=dict(title=f'{metrica_temporal} Diário'),
        yaxis2=dict(title='Acumulado', overlaying='y', side='right'),
        height=450,
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # Gráficos lado a lado
    col1, col2 = st.columns(2)
    
    with col1:
        # Por influenciador
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
            
            fig2.update_layout(
                title=f'{metrica_temporal} por Influenciador',
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        # Por formato
        df_by_formato = df_tempo.groupby('Formato')['Valor'].sum().reset_index()
        
        fig3 = go.Figure()
        
        fig3.add_trace(go.Bar(
            x=df_by_formato['Formato'],
            y=df_by_formato['Valor'],
            marker_color=cores[3],
            text=[funcoes_auxiliares.formatar_numero(v) for v in df_by_formato['Valor']],
            textposition='outside'
        ))
        
        fig3.update_layout(
            title=f'{metrica_temporal} por Formato',
            height=400
        )
        
        st.plotly_chart(fig3, use_container_width=True)
    
    # Estatísticas do período
    st.markdown("---")
    st.subheader("📊 Estatísticas do Período")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Posts", len(df_tempo))
    with col2:
        st.metric(f"Total {metrica_temporal}", funcoes_auxiliares.formatar_numero(df_tempo['Valor'].sum()))
    with col3:
        st.metric(f"Média por Post", funcoes_auxiliares.formatar_numero(int(df_tempo['Valor'].mean())))
    with col4:
        st.metric(f"Máximo", funcoes_auxiliares.formatar_numero(df_tempo['Valor'].max()))


def render_tab_top_conteudo(campanha):
    """Tab Top Conteúdo - Melhores posts com tabela melhorada"""
    
    st.subheader("🏆 Top Conteúdo - Melhores Posts")
    
    cores = funcoes_auxiliares.get_cores_graficos()
    
    if not campanha['influenciadores'] or not any(inf['posts'] for inf in campanha['influenciadores']):
        st.info("📊 Adicione posts para ver o top conteúdo")
        return
    
    # Seletor de métrica para ordenação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        metrica_ordem = st.selectbox(
            "Ordenar por:",
            ["Taxa de Engajamento", "Taxa de Alcance", "Views", "Interações"],
            key="top_metrica"
        )
    
    with col2:
        qtd_top = st.slider("Quantidade de posts:", 5, 20, 10)
    
    with col3:
        formato_filtro = st.multiselect(
            "Filtrar formatos:",
            ["Reels", "Stories", "Carrossel", "Feed", "TikTok", "YouTube"]
        )
    
    # Coletar todos os posts
    todos_posts = []
    
    for inf in campanha['influenciadores']:
        for post in inf['posts']:
            views = post['metricas']['views']
            interacoes = post['metricas']['interacoes']
            alcance = post['metricas'].get('alcance', views)  # Se não tiver alcance, usa views
            seguidores = inf.get('seguidores_num', 1)
            
            taxa_eng = (interacoes / views * 100) if views > 0 else 0
            taxa_alcance = (alcance / seguidores * 100) if seguidores > 0 else 0
            
            todos_posts.append({
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
        "Interações": "interacoes"
    }
    todos_posts.sort(key=lambda x: x[ordem_map[metrica_ordem]], reverse=True)
    
    st.markdown("---")
    
    # Tabela com foto e link
    st.markdown(f"### 🏆 Top {qtd_top} Posts por {metrica_ordem}")
    
    for idx, post in enumerate(todos_posts[:qtd_top], 1):
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([0.5, 1.5, 2, 1.5, 1.5, 1])
            
            with col1:
                medals = ['🥇', '🥈', '🥉'] + [f'{i}°' for i in range(4, 21)]
                st.markdown(f"### {medals[idx-1]}")
            
            with col2:
                # Foto do post ou influenciador
                if post['imagens']:
                    try:
                        img_bytes = base64.b64decode(post['imagens'][0])
                        st.image(img_bytes, width=80)
                    except:
                        if post['foto_inf']:
                            st.image(post['foto_inf'], width=80)
                        else:
                            st.markdown("📷")
                elif post['foto_inf']:
                    st.image(post['foto_inf'], width=80)
                else:
                    st.markdown("📷")
            
            with col3:
                st.markdown(f"**{post['influenciador']}**")
                st.caption(f"{post['formato']} • {post['plataforma']} • {post['data']}")
                if post['link']:
                    st.markdown(f"[🔗 Ver Post]({post['link']})")
            
            with col4:
                st.metric("Taxa Eng.", f"{post['taxa_eng']}%")
                st.caption(f"Views: {funcoes_auxiliares.formatar_numero(post['views'])}")
            
            with col5:
                st.metric("Taxa Alcance", f"{post['taxa_alcance']}%")
                st.caption(f"Alcance: {funcoes_auxiliares.formatar_numero(post['alcance'])}")
            
            with col6:
                st.metric("Interações", funcoes_auxiliares.formatar_numero(post['interacoes']))
            
            st.markdown("---")
    
    # Tabela resumo
    st.markdown("### 📊 Tabela Completa")
    
    df_posts = pd.DataFrame(todos_posts[:qtd_top])
    df_display = df_posts[['influenciador', 'formato', 'data', 'views', 'alcance', 
                           'interacoes', 'taxa_eng', 'taxa_alcance', 'link']]
    df_display.columns = ['Influenciador', 'Formato', 'Data', 'Views', 'Alcance', 
                          'Interações', 'Taxa Eng. %', 'Taxa Alcance %', 'Link']
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)


def render_tab_influenciadores(campanha):
    """Tab Influenciadores - Gestão e Ranking"""
    
    st.subheader("👤 Influenciadores da Campanha")
    
    cores = funcoes_auxiliares.get_cores_graficos()
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Adicionar Influenciador", use_container_width=True):
            st.session_state.show_add_inf_camp = True
    
    # Form para adicionar influenciador
    if st.session_state.get('show_add_inf_camp', False):
        if st.session_state.influenciadores_base:
            opcoes_inf = [f"{i['nome']} ({i['usuario']}) - {i['classificacao']}" 
                         for i in st.session_state.influenciadores_base]
            inf_sel = st.selectbox("Selecione o influenciador", opcoes_inf)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Adicionar à Campanha", use_container_width=True):
                    nome_sel = inf_sel.split(" (")[0]
                    inf_obj = next((i for i in st.session_state.influenciadores_base 
                                  if i['nome'] == nome_sel), None)
                    if inf_obj:
                        data_manager.adicionar_influenciador_campanha(campanha['id'], inf_obj['id'])
                        st.session_state.show_add_inf_camp = False
                        st.success("✅ Influenciador adicionado!")
                        st.rerun()
            with col2:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_add_inf_camp = False
                    st.rerun()
        else:
            st.warning("⚠️ Cadastre influenciadores na base primeiro")
            if st.button("Ir para Influenciadores"):
                st.session_state.current_page = 'Influenciadores'
                st.rerun()
    
    st.markdown("---")
    
    if not campanha['influenciadores']:
        st.info("👤 Nenhum influenciador adicionado ainda")
        return
    
    # Calcular métricas por influenciador
    dados_influs = []
    
    for inf in campanha['influenciadores']:
        total_views = sum([p['metricas']['views'] for p in inf['posts']])
        total_int = sum([p['metricas']['interacoes'] for p in inf['posts']])
        total_alcance = sum([p['metricas'].get('alcance', 0) for p in inf['posts']])
        seguidores = inf.get('seguidores_num', 1)
        
        taxa_eng = (total_int / total_views * 100) if total_views > 0 else 0
        taxa_alcance = (total_alcance / seguidores * 100) if seguidores > 0 else 0
        
        dados_influs.append({
            'id': inf['id'],
            'nome': inf['nome'],
            'usuario': inf['usuario'],
            'foto': inf.get('foto', ''),
            'classificacao': inf['classificacao'],
            'seguidores': seguidores,
            'posts': len(inf['posts']),
            'views': total_views,
            'interacoes': total_int,
            'taxa_eng': round(taxa_eng, 2),
            'taxa_alcance': round(taxa_alcance, 2),
            'inf_obj': inf
        })
    
    # RANKING DE MÉTRICAS
    st.markdown("### 🏆 Ranking de Métricas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🥇 Top Taxa de Engajamento**")
        top_eng = sorted(dados_influs, key=lambda x: x['taxa_eng'], reverse=True)[:5]
        for i, inf in enumerate(top_eng, 1):
            st.write(f"{i}. **{inf['nome']}**: {inf['taxa_eng']}%")
    
    with col2:
        st.markdown("**🥇 Top Taxa de Alcance**")
        top_alcance = sorted(dados_influs, key=lambda x: x['taxa_alcance'], reverse=True)[:5]
        for i, inf in enumerate(top_alcance, 1):
            st.write(f"{i}. **{inf['nome']}**: {inf['taxa_alcance']}%")
    
    with col3:
        st.markdown("**🥇 Top Views**")
        top_views = sorted(dados_influs, key=lambda x: x['views'], reverse=True)[:5]
        for i, inf in enumerate(top_views, 1):
            st.write(f"{i}. **{inf['nome']}**: {funcoes_auxiliares.formatar_numero(inf['views'])}")
    
    st.markdown("---")
    
    # DESEMPENHO POR CLASSIFICAÇÃO
    st.markdown("### 📊 Desempenho por Classificação")
    
    df_dados = pd.DataFrame(dados_influs)
    
    if not df_dados.empty:
        df_class = df_dados.groupby('classificacao').agg({
            'views': 'sum',
            'interacoes': 'sum',
            'taxa_eng': 'mean',
            'nome': 'count'
        }).reset_index()
        df_class.columns = ['Classificação', 'Views', 'Interações', 'Taxa Eng. Média', 'Qtd']
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=df_class['Classificação'],
                y=df_class['Views'],
                name='Views',
                marker_color=cores[0]
            ))
            
            fig.add_trace(go.Scatter(
                x=df_class['Classificação'],
                y=df_class['Taxa Eng. Média'],
                name='Taxa Eng. (%)',
                mode='lines+markers',
                yaxis='y2',
                line=dict(color=cores[1], width=3),
                marker=dict(size=10)
            ))
            
            fig.update_layout(
                title='Views e Engajamento por Classificação',
                yaxis=dict(title='Views'),
                yaxis2=dict(title='Taxa Eng. (%)', overlaying='y', side='right'),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Tabela de classificação
            st.dataframe(df_class, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # LISTA DE INFLUENCIADORES COM POSTS
    st.markdown("### 👤 Lista de Influenciadores")
    
    for dados in dados_influs:
        inf = dados['inf_obj']
        
        with st.expander(f"👤 {inf['nome']} - {dados['posts']} posts - {inf['classificacao']}"):
            col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
            
            with col1:
                if inf.get('foto'):
                    st.image(inf['foto'], width=80)
            
            with col2:
                st.write(f"**{inf['usuario']}**")
                st.write(f"Seguidores: {funcoes_auxiliares.formatar_numero(dados['seguidores'])}")
                st.write(f"Redes: {', '.join(inf['redes_sociais'])}")
            
            with col3:
                st.metric("Taxa Eng.", f"{dados['taxa_eng']}%")
                st.metric("Views", funcoes_auxiliares.formatar_numero(dados['views']))
            
            with col4:
                if st.button("➕ Add Post", key=f"add_post_{inf['id']}", use_container_width=True):
                    st.session_state.current_influencer_id = inf['id']
                    st.session_state.show_add_post = True
            
            # Form para adicionar post
            if (st.session_state.get('show_add_post', False) and 
                st.session_state.get('current_influencer_id') == inf['id']):
                render_form_post(campanha, inf)
            
            # Lista de posts
            if inf['posts']:
                st.markdown("---")
                st.markdown("**📱 Posts:**")
                
                for post in inf['posts']:
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**{post['formato']}** ({post['plataforma']})")
                        st.caption(post['data_publicacao'])
                        if post.get('link_post'):
                            st.markdown(f"[🔗 Link]({post['link_post']})")
                    
                    with col2:
                        st.write(f"👁️ {post['metricas']['views']:,}")
                    
                    with col3:
                        st.write(f"❤️ {post['metricas']['interacoes']:,}")
                    
                    with col4:
                        if post['imagens']:
                            try:
                                img_bytes = base64.b64decode(post['imagens'][0])
                                st.image(img_bytes, width=50)
                            except:
                                pass


def render_form_post(campanha, inf):
    """Renderiza formulário de adicionar post"""
    
    with st.form(f"form_post_{inf['id']}"):
        st.markdown("##### 📱 Novo Post")
        
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
            interacoes = st.number_input("Interações *", min_value=0, value=0) if metricas_camp.get('interacoes', True) else 0
            impressoes = st.number_input("Impressões", min_value=0, value=0) if metricas_camp.get('impressoes', True) else 0
        
        with col3:
            curtidas = st.number_input("Curtidas", min_value=0, value=0) if metricas_camp.get('curtidas', True) else 0
            comentarios = st.number_input("Comentários", min_value=0, value=0) if metricas_camp.get('comentarios', True) else 0
            compartilhamentos = st.number_input("Compartilh.", min_value=0, value=0) if metricas_camp.get('compartilhamentos', True) else 0
            saves = st.number_input("Saves", min_value=0, value=0) if metricas_camp.get('saves', True) else 0
        
        # Clique em link só para Stories
        clique_link = 0
        if formato == "Stories" and metricas_camp.get('clique_link', False):
            clique_link = st.number_input("Cliques Link", min_value=0, value=0)
        
        # Cupom opcional
        cupom_codigo = ""
        cupom_conversoes = 0
        if metricas_camp.get('cupom_conversoes', False):
            cupom_codigo = st.text_input("Código Cupom", placeholder="PROMO10")
            if cupom_codigo:
                cupom_conversoes = st.number_input("Conversões", min_value=0, value=0)
        
        st.markdown("**📷 Imagens/Vídeos do Post**")
        imagens_upload = st.file_uploader(
            "Upload de mídias",
            type=['png', 'jpg', 'jpeg', 'mp4', 'gif'],
            accept_multiple_files=True,
            key=f"upload_{inf['id']}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("✅ Salvar Post", use_container_width=True):
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
                st.success("✅ Post adicionado!")
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                st.session_state.show_add_post = False
                st.rerun()


def render_tab_configuracao(campanha):
    """Tab Configuração da Campanha"""
    
    st.subheader("⚙️ Configuração da Campanha")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Nome", value=campanha['nome'], disabled=True)
        st.text_input("Cliente", value=campanha['cliente_nome'], disabled=True)
        st.text_input("Período", 
                     value=f"{funcoes_auxiliares.formatar_data_br(campanha['data_inicio'])} - {funcoes_auxiliares.formatar_data_br(campanha['data_fim'])}", 
                     disabled=True)
        st.text_area("Objetivo", value=campanha['objetivo'], disabled=True, height=100)
    
    with col2:
        st.text_input("Tipo", value=campanha.get('tipo_dados', 'estático').title(), disabled=True)
        st.text_input("Status", value=campanha['status'].title(), disabled=True)
        st.text_input("AON", value="Sim" if campanha.get('is_aon') else "Não", disabled=True)
        
        # AIR Score destacado
        air_score = funcoes_auxiliares.calcular_air_score(campanha)
        st.markdown(f"""
        <div class='air-score-card' style='padding: 1rem;'>
            <div style='font-size: 2rem; font-weight: 700;'>{air_score}</div>
            <div style='font-size: 0.8rem;'>AIR SCORE</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("📊 Métricas Configuradas")
    
    metricas_sel = campanha.get('metricas_selecionadas', {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.write("✅ Views" if metricas_sel.get('views') else "❌ Views")
        st.write("✅ Alcance" if metricas_sel.get('alcance') else "❌ Alcance")
    with col2:
        st.write("✅ Interações" if metricas_sel.get('interacoes') else "❌ Interações")
        st.write("✅ Impressões" if metricas_sel.get('impressoes') else "❌ Impressões")
    with col3:
        st.write("✅ Curtidas" if metricas_sel.get('curtidas') else "❌ Curtidas")
        st.write("✅ Comentários" if metricas_sel.get('comentarios') else "❌ Comentários")
    with col4:
        st.write("✅ Saves" if metricas_sel.get('saves') else "❌ Saves")
        st.write("✅ Cliques Link" if metricas_sel.get('clique_link') else "❌ Cliques Link")


def render_tab_comentarios(campanha):
    """Tab de Comentários e Análise de Sentimento"""
    
    st.subheader("💬 Análise de Comentários")
    
    # Coletar comentários
    todos_comentarios = []
    
    for inf in campanha['influenciadores']:
        for post in inf['posts']:
            for com in post.get('comentarios', []):
                todos_comentarios.append({
                    'influenciador': inf['nome'],
                    'post': f"{post['formato']} - {post['data_publicacao']}",
                    'texto': com['texto'],
                    'polaridade': com['polaridade'],
                    'categoria': com['categoria']
                })
    
    if not todos_comentarios:
        st.info("💬 Nenhum comentário classificado ainda")
        
        with st.expander("💡 Como adicionar comentários"):
            st.markdown("""
            1. Vá até a aba **Influenciadores**
            2. Expanda um influenciador e veja seus posts
            3. Clique em **Ver Detalhes** de um post
            4. Na seção de comentários, cole textos das redes sociais
            5. A IA classificará automaticamente
            """)
        return
    
    # Estatísticas
    total = len(todos_comentarios)
    positivos = len([c for c in todos_comentarios if c['polaridade'] == 'positivo'])
    neutros = len([c for c in todos_comentarios if c['polaridade'] == 'neutro'])
    negativos = len([c for c in todos_comentarios if c['polaridade'] == 'negativo'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("✅ Positivos", f"{positivos} ({positivos/total*100:.0f}%)")
    with col3:
        st.metric("➖ Neutros", f"{neutros} ({neutros/total*100:.0f}%)")
    with col4:
        st.metric("❌ Negativos", f"{negativos} ({negativos/total*100:.0f}%)")
    
    st.markdown("---")
    
    # Gráfico de categorias
    categorias_count = Counter([c['categoria'] for c in todos_comentarios])
    df_cat = pd.DataFrame(categorias_count.items(), columns=['Categoria', 'Quantidade'])
    
    cores = funcoes_auxiliares.get_cores_graficos()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_cat['Categoria'],
        y=df_cat['Quantidade'],
        marker_color=cores[:len(df_cat)]
    ))
    fig.update_layout(title='Comentários por Categoria', height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Lista de comentários
    st.markdown("### 📝 Comentários Recentes")
    
    for com in todos_comentarios[:20]:
        icon = {"positivo": "✅", "neutro": "➖", "negativo": "❌"}
        st.write(f"{icon[com['polaridade']]} **{com['categoria']}** - {com['influenciador']}")
        st.caption(com['texto'][:200])
        st.markdown("---")


def render_tab_glossario():
    """Tab Glossário de Métricas"""
    
    st.subheader("📖 Glossário de Métricas")
    
    with st.expander("📊 MÉTRICAS BÁSICAS", expanded=True):
        st.markdown("""
        **Views** - Número total de visualizações do conteúdo
        
        **Alcance** - Número de contas únicas que viram o conteúdo
        
        **Impressões** - Número total de vezes que o conteúdo foi exibido
        
        **Interações** - Soma de curtidas + comentários + compartilhamentos + saves
        
        **Taxa de Engajamento** - (Interações / Views) × 100
        
        **Taxa de Alcance** - (Alcance / Seguidores) × 100
        """)
    
    with st.expander("🏷️ CLASSIFICAÇÃO DE INFLUENCIADORES"):
        st.markdown("""
        **Nano** - Menos de 10K seguidores (alta proximidade)
        
        **Micro** - 10K a 100K seguidores (bom custo-benefício)
        
        **Mid** - 100K a 500K seguidores (alcance significativo)
        
        **Macro** - 500K a 1M seguidores (grande alcance)
        
        **Mega** - Mais de 1M seguidores (celebridades)
        """)
    
    with st.expander("🎯 AIR SCORE"):
        st.markdown("""
        **O que é?** - Métrica proprietária AIR de 0 a 100
        
        **Como é calculado:**
        - 40 pontos: Taxa de Engajamento
        - 30 pontos: Alcance
        - 15 pontos: Conversões
        - 15 pontos: Saves
        
        **Interpretação:**
        - 0-40: Performance baixa
        - 41-60: Performance média
        - 61-80: Performance boa
        - 81-100: Performance excelente
        """)
