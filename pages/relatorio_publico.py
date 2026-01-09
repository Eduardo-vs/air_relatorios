"""
Pagina: Relatorio Publico (Compartilhavel)
Visualizacao de relatorio sem necessidade de login
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import json
import re

from utils import data_manager, funcoes_auxiliares


def render_publico(token: str):
    """Renderiza relatorio publico baseado no token"""
    
    # Validar token
    token_info = data_manager.validar_token(token)
    
    if not token_info:
        st.error("Link invalido ou expirado")
        st.info("Este link de compartilhamento nao existe, ja expirou ou atingiu o limite de visualizacoes.")
        return
    
    # Registrar visualizacao
    data_manager.registrar_visualizacao_token(token)
    
    # Buscar campanha
    campanha_id = token_info['campanha_id']
    campanha = data_manager.get_campanha(campanha_id)
    
    if not campanha:
        st.error("Campanha nao encontrada")
        return
    
    # Buscar cliente
    cliente = None
    if campanha.get('cliente_id'):
        cliente = data_manager.get_cliente(campanha['cliente_id'])
    
    # Calcular metricas
    metricas = data_manager.calcular_metricas_campanha(campanha)
    
    # Cores
    primary_color = st.session_state.get('primary_color', '#7c3aed')
    cores = funcoes_auxiliares.get_cores_graficos()
    
    # Header
    titulo_relatorio = token_info.get('titulo') or campanha['nome']
    
    st.markdown(f"""
    <div style='text-align: center; padding: 2rem 0; border-bottom: 3px solid {primary_color};'>
        <h1 style='color: #1a1a1a; margin: 0;'>{titulo_relatorio}</h1>
        <p style='color: #6b7280; margin-top: 0.5rem;'>
            {cliente['nome'] if cliente else ''} | 
            {campanha.get('data_inicio', '')} - {campanha.get('data_fim', '')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Paginas permitidas
    paginas_permitidas = token_info.get('paginas_permitidas')
    
    # Tabs de navegacao
    tabs_disponiveis = []
    tabs_nomes = []
    
    paginas_config = {
        'big_numbers': 'Resumo',
        'analise_geral': 'Analise',
        'kpis_influenciador': 'Influenciadores',
        'top_performance': 'Top Posts',
        'lista_influenciadores': 'Lista Completa'
    }
    
    for key, nome in paginas_config.items():
        if paginas_permitidas is None or key in paginas_permitidas:
            tabs_disponiveis.append(key)
            tabs_nomes.append(nome)
    
    if not tabs_disponiveis:
        tabs_disponiveis = list(paginas_config.keys())
        tabs_nomes = list(paginas_config.values())
    
    tabs = st.tabs(tabs_nomes)
    
    campanhas_list = [campanha]
    
    for idx, tab_key in enumerate(tabs_disponiveis):
        with tabs[idx]:
            if tab_key == 'big_numbers':
                render_big_numbers_publico(metricas, campanha, primary_color)
            elif tab_key == 'analise_geral':
                render_analise_publico(campanhas_list, metricas, cores)
            elif tab_key == 'kpis_influenciador':
                render_kpis_influenciador_publico(campanhas_list, cores)
            elif tab_key == 'top_performance':
                render_top_posts_publico(campanhas_list, cores, metricas)
            elif tab_key == 'lista_influenciadores':
                render_lista_publico(campanhas_list)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #9ca3af; padding: 1rem 0; font-size: 0.8rem;'>
        Relatorio gerado por <strong>AIR</strong> | Visualizacao #{token_info.get('visualizacoes', 0) + 1}
    </div>
    """, unsafe_allow_html=True)


def render_big_numbers_publico(metricas, campanha, primary_color):
    """Big Numbers para visualizacao publica"""
    
    st.subheader("Resumo da Campanha")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Influenciadores", metricas['total_influenciadores'])
    with col2:
        st.metric("Posts", metricas['total_posts'])
    with col3:
        st.metric("Impressoes", funcoes_auxiliares.formatar_numero(metricas['total_views'] + metricas['total_impressoes']))
    with col4:
        st.metric("Alcance", funcoes_auxiliares.formatar_numero(metricas['total_alcance']))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Interacoes", funcoes_auxiliares.formatar_numero(metricas['total_interacoes']))
    with col2:
        st.metric("Taxa Engajamento", f"{metricas['engajamento_efetivo']:.2f}%")
    with col3:
        st.metric("Taxa Alcance", f"{metricas['taxa_alcance']:.2f}%")
    with col4:
        if metricas.get('total_custo', 0) > 0:
            st.metric("Investimento", f"R$ {metricas['total_custo']:,.0f}".replace(",", "."))
        else:
            st.metric("Cliques Link", funcoes_auxiliares.formatar_numero(metricas.get('total_cliques_link', 0)))
    
    # Insights da IA
    st.markdown("---")
    st.subheader("Insights")
    
    insights = data_manager.get_insights_campanha(campanha['id'], 'big_numbers')
    
    if insights:
        for insight in insights:
            tipo = insight.get('tipo', 'info')
            icone = insight.get('icone', '💡')
            titulo = insight.get('titulo', '')
            texto = insight.get('texto', '')
            
            # Converter markdown para HTML
            texto_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', texto)
            
            cor_fundo = {
                'destaque': '#eff6ff',
                'sucesso': '#ecfdf5',
                'alerta': '#fffbeb',
                'critico': '#fef2f2',
                'info': '#f5f3ff'
            }.get(tipo, '#f5f3ff')
            
            st.markdown(f"""
            <div style='background: {cor_fundo}; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                <strong>{icone} {titulo}</strong>
                <p style='margin: 0.5rem 0 0 0; color: #374151;'>{texto_html}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhum insight disponivel")


def render_analise_publico(campanhas_list, metricas, cores):
    """Analise geral para visualizacao publica"""
    
    st.subheader("Analise de Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Por Formato**")
        dados = coletar_dados_formato_publico(campanhas_list)
        if dados:
            df = pd.DataFrame(dados)
            df_agg = df.groupby('formato').agg({
                'views': 'sum', 
                'alcance': 'sum', 
                'interacoes': 'sum', 
                'impressoes': 'sum'
            }).reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_agg['formato'], 
                y=df_agg['impressoes'], 
                name='Impressoes', 
                marker_color=cores[0],
                text=[funcoes_auxiliares.formatar_numero(v) for v in df_agg['impressoes']],
                textposition='outside'
            ))
            fig.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Por Classificacao**")
        dados_class = coletar_dados_classificacao_publico(campanhas_list)
        if dados_class:
            df = pd.DataFrame(dados_class)
            df_agg = df.groupby('classificacao').agg({
                'impressoes': 'sum',
                'interacoes': 'sum'
            }).reset_index()
            
            ordem = ['Nano', 'Micro', 'Mid', 'Macro', 'Mega']
            df_agg['ordem'] = df_agg['classificacao'].apply(lambda x: ordem.index(x) if x in ordem else 99)
            df_agg = df_agg.sort_values('ordem')
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_agg['classificacao'], 
                y=df_agg['impressoes'], 
                name='Impressoes', 
                marker_color=cores[2],
                text=[funcoes_auxiliares.formatar_numero(v) for v in df_agg['impressoes']],
                textposition='outside'
            ))
            fig.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)


def render_kpis_influenciador_publico(campanhas_list, cores):
    """KPIs por influenciador para visualizacao publica"""
    
    st.subheader("Performance por Influenciador")
    
    dados = coletar_dados_influenciadores_publico(campanhas_list)
    
    if not dados:
        st.info("Sem dados de influenciadores")
        return
    
    df = pd.DataFrame(dados)
    df = df.sort_values('impressoes', ascending=False).head(10)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df['nome'],
        x=df['impressoes'],
        orientation='h',
        marker_color=cores[0],
        text=[funcoes_auxiliares.formatar_numero(v) for v in df['impressoes']],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Top 10 Influenciadores por Impressoes',
        height=400,
        yaxis=dict(autorange='reversed')
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_top_posts_publico(campanhas_list, cores, metricas):
    """Top posts para visualizacao publica"""
    
    st.subheader("Top Posts")
    
    posts = []
    for camp in campanhas_list:
        for inf_camp in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
            if not inf:
                continue
            for post in inf_camp.get('posts', []):
                posts.append({
                    'influenciador': inf['nome'],
                    'formato': post.get('formato', ''),
                    'data': post.get('data_publicacao', ''),
                    'impressoes': post.get('views', 0) + post.get('impressoes', 0),
                    'alcance': post.get('alcance', 0),
                    'interacoes': post.get('interacoes', 0)
                })
    
    if not posts:
        st.info("Sem posts")
        return
    
    df = pd.DataFrame(posts)
    df = df.sort_values('impressoes', ascending=False).head(10)
    
    for _, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.write(f"**{row['influenciador']}** - {row['formato']}")
            st.caption(row['data'])
        with col2:
            st.metric("Impressoes", funcoes_auxiliares.formatar_numero(row['impressoes']))
        with col3:
            st.metric("Alcance", funcoes_auxiliares.formatar_numero(row['alcance']))
        with col4:
            st.metric("Interacoes", funcoes_auxiliares.formatar_numero(row['interacoes']))
        st.markdown("---")


def render_lista_publico(campanhas_list):
    """Lista de influenciadores para visualizacao publica"""
    
    st.subheader("Lista de Influenciadores")
    
    dados = coletar_dados_influenciadores_publico(campanhas_list)
    
    if not dados:
        st.info("Sem influenciadores")
        return
    
    df = pd.DataFrame(dados)
    df = df.sort_values('impressoes', ascending=False)
    
    df_exibir = df[['nome', 'classificacao', 'seguidores', 'posts', 'impressoes', 'alcance', 'interacoes', 'taxa_eng']].copy()
    df_exibir.columns = ['Nome', 'Classe', 'Seguidores', 'Posts', 'Impressoes', 'Alcance', 'Interacoes', 'Taxa Eng. %']
    
    for col in ['Seguidores', 'Impressoes', 'Alcance', 'Interacoes']:
        df_exibir[col] = df_exibir[col].apply(lambda x: f"{x:,.0f}".replace(",", "."))
    
    df_exibir['Taxa Eng. %'] = df_exibir['Taxa Eng. %'].apply(lambda x: f"{x:.2f}")
    
    st.dataframe(df_exibir, use_container_width=True, hide_index=True)


# Funcoes auxiliares de coleta
def coletar_dados_formato_publico(campanhas_list):
    dados = []
    for camp in campanhas_list:
        for camp_inf in camp.get('influenciadores', []):
            for post in camp_inf.get('posts', []):
                dados.append({
                    'formato': post.get('formato', 'Outro'), 
                    'views': post.get('views', 0), 
                    'alcance': post.get('alcance', 0), 
                    'interacoes': post.get('interacoes', 0), 
                    'impressoes': post.get('impressoes', 0) + post.get('views', 0)
                })
    return dados


def coletar_dados_classificacao_publico(campanhas_list):
    dados = []
    for camp in campanhas_list:
        for camp_inf in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(camp_inf.get('influenciador_id'))
            if not inf:
                continue
            classificacao = inf.get('classificacao', 'Desconhecido')
            for post in camp_inf.get('posts', []):
                dados.append({
                    'classificacao': classificacao,
                    'impressoes': post.get('impressoes', 0) + post.get('views', 0),
                    'interacoes': post.get('interacoes', 0)
                })
    return dados


def coletar_dados_influenciadores_publico(campanhas_list):
    dados_inf = {}
    for camp in campanhas_list:
        for camp_inf in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(camp_inf.get('influenciador_id'))
            if not inf:
                continue
            inf_id = inf['id']
            if inf_id not in dados_inf:
                dados_inf[inf_id] = {
                    'nome': inf['nome'],
                    'classificacao': inf.get('classificacao', 'Desconhecido'),
                    'seguidores': inf.get('seguidores', 0),
                    'impressoes': 0,
                    'alcance': 0,
                    'interacoes': 0,
                    'posts': 0
                }
            for post in camp_inf.get('posts', []):
                dados_inf[inf_id]['impressoes'] += post.get('views', 0) + post.get('impressoes', 0)
                dados_inf[inf_id]['alcance'] += post.get('alcance', 0)
                dados_inf[inf_id]['interacoes'] += post.get('interacoes', 0)
                dados_inf[inf_id]['posts'] += 1
    
    resultado = []
    for d in dados_inf.values():
        d['taxa_eng'] = round((d['interacoes'] / d['impressoes'] * 100), 2) if d['impressoes'] > 0 else 0
        resultado.append(d)
    
    return resultado
