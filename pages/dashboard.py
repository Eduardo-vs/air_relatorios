"""
Página: Dashboard
Visão geral do sistema com evolução temporal
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
from utils import funcoes_auxiliares, data_manager

def render():
    """Renderiza página do Dashboard"""
    
    st.markdown('<p class="main-header">📊 Dashboard Geral</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Visão panorâmica do sistema</p>', unsafe_allow_html=True)
    
    # Filtros globais
    data_manager.renderizar_filtros_globais()
    
    st.markdown("---")
    
    # Big Numbers
    campanhas_filtradas = data_manager.get_campanhas_filtradas()
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        campanhas_ativas = len([c for c in campanhas_filtradas if c['status'] == 'ativa'])
        st.metric("🎯 Campanhas", campanhas_ativas)
    
    with col2:
        st.metric("👥 Clientes", len(st.session_state.clientes))
    
    with col3:
        total_influs = sum([len(c['influenciadores']) for c in campanhas_filtradas])
        st.metric("👤 Influenciadores", total_influs)
    
    with col4:
        total_posts = sum([len(inf['posts']) for c in campanhas_filtradas for inf in c['influenciadores']])
        st.metric("📱 Posts", total_posts)
    
    with col5:
        total_views = sum([sum([p['metricas']['views'] for p in inf['posts']]) 
                          for c in campanhas_filtradas for inf in c['influenciadores']])
        st.metric("👁️ Views", f"{total_views:,}")
    
    with col6:
        total_seguidores = sum([inf.get('seguidores_num', 0) for c in campanhas_filtradas for inf in c['influenciadores']])
        st.metric("📈 Seguidores", funcoes_auxiliares.formatar_numero(total_seguidores))
    
    st.markdown("---")
    
    if not campanhas_filtradas:
        st.info("📊 Crie campanhas para ver análises detalhadas")
        return
    
    # ========================================
    # RELATÓRIO POR CLIENTE
    # ========================================
    st.subheader("📋 Relatório por Cliente")
    
    for cliente in st.session_state.clientes:
        metricas_cliente = data_manager.calcular_metricas_por_cliente(cliente['id'])
        
        if metricas_cliente['total_campanhas'] > 0:
            with st.expander(f"🏢 {cliente['nome']} - {metricas_cliente['total_campanhas']} campanhas"):
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Campanhas", metricas_cliente['total_campanhas'])
                with col2:
                    st.metric("Influenciadores", metricas_cliente['total_influenciadores'])
                with col3:
                    st.metric("Posts", metricas_cliente['total_posts'])
                with col4:
                    st.metric("Views", f"{metricas_cliente['total_views']:,}")
                with col5:
                    st.metric("Alcance", f"{metricas_cliente['total_alcance']:,}")
    
    st.markdown("---")
    
    # ========================================
    # VISÃO POR MÊS
    # ========================================
    st.subheader("📈 Evolução Mensal")
    
    # Simular dados mensais (em produção viria do banco)
    meses_dados = []
    for i in range(6):
        mes = (datetime.now() - timedelta(days=30*i)).strftime('%m/%Y')
        campanhas_mes = random.randint(1, max(len(campanhas_filtradas), 1))
        influs_mes = random.randint(5, 30)
        posts_mes = random.randint(10, 100)
        views_mes = random.randint(50000, 500000)
        
        meses_dados.append({
            'Mês': mes,
            'Campanhas': campanhas_mes,
            'Influenciadores': influs_mes,
            'Posts': posts_mes,
            'Views': views_mes
        })
    
    meses_dados.reverse()
    df_meses = pd.DataFrame(meses_dados)
    
    cores = funcoes_auxiliares.get_cores_graficos()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico combinado barra + linha
        fig1 = go.Figure()
        
        fig1.add_trace(go.Bar(
            x=df_meses['Mês'],
            y=df_meses['Campanhas'],
            name='Campanhas',
            marker_color=cores[0]
        ))
        
        fig1.add_trace(go.Scatter(
            x=df_meses['Mês'],
            y=df_meses['Influenciadores'],
            name='Influenciadores',
            mode='lines+markers',
            yaxis='y2',
            line=dict(color=cores[1], width=3),
            marker=dict(size=8)
        ))
        
        fig1.update_layout(
            title='Campanhas e Influenciadores por Mês',
            yaxis=dict(title='Campanhas'),
            yaxis2=dict(title='Influenciadores', overlaying='y', side='right'),
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Gráfico combinado barra + linha para views e posts
        fig2 = go.Figure()
        
        fig2.add_trace(go.Bar(
            x=df_meses['Mês'],
            y=df_meses['Views'],
            name='Views',
            marker_color=cores[2]
        ))
        
        fig2.add_trace(go.Scatter(
            x=df_meses['Mês'],
            y=df_meses['Posts'],
            name='Posts',
            mode='lines+markers',
            yaxis='y2',
            line=dict(color=cores[3], width=3),
            marker=dict(size=8)
        ))
        
        fig2.update_layout(
            title='Views e Posts por Mês',
            yaxis=dict(title='Views'),
            yaxis2=dict(title='Posts', overlaying='y', side='right'),
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================
    # TABELA RESUMO MENSAL
    # ========================================
    st.subheader("📊 Resumo Mensal Detalhado (Geralzão)")
    st.dataframe(df_meses, use_container_width=True, hide_index=True)
    
    # Totais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Campanhas", df_meses['Campanhas'].sum())
    with col2:
        st.metric("Total Influenciadores", df_meses['Influenciadores'].sum())
    with col3:
        st.metric("Total Posts", df_meses['Posts'].sum())
    with col4:
        st.metric("Total Views", f"{df_meses['Views'].sum():,}")
    
    st.markdown("---")
    
    # ========================================
    # DESTAQUES DO MÊS
    # ========================================
    st.subheader("⭐ Destaques do Mês")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🏆 Campanha Destaque**")
        if campanhas_filtradas:
            melhor_campanha = max(campanhas_filtradas, 
                                 key=lambda c: data_manager.calcular_metricas_campanha(c)['total_views'])
            metricas_melhor = data_manager.calcular_metricas_campanha(melhor_campanha)
            st.write(f"**{melhor_campanha['nome']}**")
            st.caption(f"{metricas_melhor['total_views']:,} views")
            air_score = funcoes_auxiliares.calcular_air_score(melhor_campanha)
            st.metric("AIR Score", air_score)
    
    with col2:
        st.markdown("**🌟 Influenciador Destaque**")
        todos_influs = []
        for camp in campanhas_filtradas:
            for inf in camp['influenciadores']:
                total_views_inf = sum([p['metricas']['views'] for p in inf['posts']])
                todos_influs.append({
                    'nome': inf['nome'],
                    'views': total_views_inf,
                    'classificacao': inf['classificacao'],
                    'foto': inf.get('foto', '')
                })
        
        if todos_influs:
            melhor_inf = max(todos_influs, key=lambda x: x['views'])
            if melhor_inf.get('foto'):
                st.image(melhor_inf['foto'], width=60)
            st.write(f"**{melhor_inf['nome']}**")
            st.caption(f"{melhor_inf['views']:,} views")
            st.caption(f"Classificação: {melhor_inf['classificacao']}")
    
    with col3:
        st.markdown("**📱 Post Destaque**")
        todos_posts = []
        for camp in campanhas_filtradas:
            for inf in camp['influenciadores']:
                for post in inf['posts']:
                    todos_posts.append({
                        'formato': post['formato'],
                        'views': post['metricas']['views'],
                        'engajamento': post['metricas']['interacoes'],
                        'link': post.get('link_post', '')
                    })
        
        if todos_posts:
            melhor_post = max(todos_posts, key=lambda x: x['views'])
            st.write(f"**{melhor_post['formato']}**")
            st.caption(f"{melhor_post['views']:,} views")
            st.caption(f"{melhor_post['engajamento']:,} interações")
            if melhor_post.get('link'):
                st.markdown(f"[🔗 Ver post]({melhor_post['link']})")
    
    st.markdown("---")
    
    # ========================================
    # INSIGHTS GERAIS
    # ========================================
    st.subheader("💡 Insights do Sistema")
    
    # Calcular médias
    if campanhas_filtradas:
        todas_metricas = [data_manager.calcular_metricas_campanha(c) for c in campanhas_filtradas]
        media_posts = sum([m['total_posts'] for m in todas_metricas]) / len(todas_metricas) if todas_metricas else 0
        media_eng = sum([m['engajamento_efetivo'] for m in todas_metricas]) / len(todas_metricas) if todas_metricas else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"📊 **Média de Posts por Campanha:** {media_posts:.0f} posts")
            st.info(f"📈 **Taxa Média de Engajamento:** {media_eng:.2f}%")
        
        with col2:
            # Classificação mais usada
            todas_class = []
            for camp in campanhas_filtradas:
                for inf in camp['influenciadores']:
                    todas_class.append(inf['classificacao'])
            
            if todas_class:
                from collections import Counter
                mais_comum = Counter(todas_class).most_common(1)[0]
                st.success(f"👤 **Classificação Mais Usada:** {mais_comum[0]} ({mais_comum[1]} influenciadores)")
            
            # Total de conversões
            total_conversoes = sum([m['total_conversoes_cupom'] for m in todas_metricas])
            if total_conversoes > 0:
                st.success(f"🎯 **Total de Conversões Rastreadas:** {total_conversoes}")
