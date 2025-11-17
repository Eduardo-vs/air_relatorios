"""
Página: Dashboard
Visão geral do sistema com evolução temporal
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random
from utils import funcoes_auxiliares, data_manager

def render():
    """Renderiza página do Dashboard"""
    
    st.markdown('<p class="main-header">Dashboard Geral</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Visão panorâmica do sistema</p>', unsafe_allow_html=True)
    
    # Big Numbers
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        campanhas_ativas = len([c for c in st.session_state.campanhas if c['status'] == 'ativa'])
        st.metric("Campanhas Ativas", campanhas_ativas)
    
    with col2:
        st.metric("Clientes", len(st.session_state.clientes))
    
    with col3:
        st.metric("Influenciadores", len(st.session_state.influenciadores_base))
    
    with col4:
        total_posts = sum([len(inf['posts']) for c in st.session_state.campanhas for inf in c['influenciadores']])
        st.metric("Posts Totais", total_posts)
    
    with col5:
        total_views = sum([sum([p['metricas']['views'] for p in inf['posts']]) 
                          for c in st.session_state.campanhas for inf in c['influenciadores']])
        st.metric("Views Totais", f"{total_views:,}")
    
    st.markdown("---")
    
    if not st.session_state.campanhas:
        st.info("📊 Crie campanhas para ver análises detalhadas")
        return
    
    # ========================================
    # VISÃO POR MÊS
    # ========================================
    st.subheader("📈 Evolução Mensal")
    
    # Simular dados mensais (em produção viria do banco)
    meses_dados = []
    for i in range(6):
        mes = (datetime.now() - timedelta(days=30*i)).strftime('%m/%Y')
        campanhas_mes = random.randint(1, max(len(st.session_state.campanhas), 1))
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
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.line(df_meses, x='Mês', y='Campanhas', 
                      title='Campanhas por Mês',
                      markers=True)
        fig1.update_traces(line_color=st.session_state.primary_color)
        fig1.update_layout(height=350)
        st.plotly_chart(fig1, use_container_width=True)
        
        fig3 = px.bar(df_meses, x='Mês', y='Influenciadores',
                     title='Influenciadores por Mês',
                     color='Influenciadores',
                     color_continuous_scale='Viridis')
        fig3.update_layout(height=350)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        fig2 = px.bar(df_meses, x='Mês', y='Views',
                     title='Views por Mês',
                     color='Views',
                     color_continuous_scale='Purples')
        fig2.update_layout(height=350)
        st.plotly_chart(fig2, use_container_width=True)
        
        fig4 = px.line(df_meses, x='Mês', y='Posts',
                      title='Posts por Mês',
                      markers=True)
        fig4.update_traces(line_color=st.session_state.secondary_color)
        fig4.update_layout(height=350)
        st.plotly_chart(fig4, use_container_width=True)
    
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
        if st.session_state.campanhas:
            melhor_campanha = max(st.session_state.campanhas, 
                                 key=lambda c: data_manager.calcular_metricas_campanha(c)['total_views'])
            metricas_melhor = data_manager.calcular_metricas_campanha(melhor_campanha)
            st.write(f"**{melhor_campanha['nome']}**")
            st.caption(f"{metricas_melhor['total_views']:,} views")
            air_score = funcoes_auxiliares.calcular_air_score(melhor_campanha)
            st.metric("AIR Score", air_score)
    
    with col2:
        st.markdown("**⭐ Influenciador Destaque**")
        todos_influs = []
        for camp in st.session_state.campanhas:
            for inf in camp['influenciadores']:
                total_views_inf = sum([p['metricas']['views'] for p in inf['posts']])
                todos_influs.append({
                    'nome': inf['nome'],
                    'views': total_views_inf,
                    'classificacao': inf['classificacao']
                })
        
        if todos_influs:
            melhor_inf = max(todos_influs, key=lambda x: x['views'])
            st.write(f"**{melhor_inf['nome']}**")
            st.caption(f"{melhor_inf['views']:,} views")
            st.caption(f"Classificação: {melhor_inf['classificacao']}")
    
    with col3:
        st.markdown("**📱 Post Destaque**")
        todos_posts = []
        for camp in st.session_state.campanhas:
            for inf in camp['influenciadores']:
                for post in inf['posts']:
                    todos_posts.append({
                        'formato': post['formato'],
                        'views': post['metricas']['views'],
                        'engajamento': post['metricas']['interacoes']
                    })
        
        if todos_posts:
            melhor_post = max(todos_posts, key=lambda x: x['views'])
            st.write(f"**{melhor_post['formato']}**")
            st.caption(f"{melhor_post['views']:,} views")
            st.caption(f"{melhor_post['engajamento']:,} interações")
    
    st.markdown("---")
    
    # ========================================
    # INSIGHTS GERAIS
    # ========================================
    st.subheader("💡 Insights do Sistema")
    
    # Calcular médias
    if st.session_state.campanhas:
        todas_metricas = [data_manager.calcular_metricas_campanha(c) for c in st.session_state.campanhas]
        media_posts = sum([m['total_posts'] for m in todas_metricas]) / len(todas_metricas) if todas_metricas else 0
        media_eng = sum([m['engajamento_efetivo'] for m in todas_metricas]) / len(todas_metricas) if todas_metricas else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"📊 **Média de Posts por Campanha:** {media_posts:.0f} posts")
            st.info(f"📈 **Taxa Média de Engajamento:** {media_eng:.2f}%")
        
        with col2:
            # Classificação mais usada
            todas_class = []
            for camp in st.session_state.campanhas:
                for inf in camp['influenciadores']:
                    todas_class.append(inf['classificacao'])
            
            if todas_class:
                from collections import Counter
                mais_comum = Counter(todas_class).most_common(1)[0]
                st.success(f"⭐ **Classificação Mais Usada:** {mais_comum[0]} ({mais_comum[1]} influenciadores)")
            
            # Total de conversões
            total_conversoes = sum([m['total_conversoes_cupom'] for m in todas_metricas])
            if total_conversoes > 0:
                st.success(f"🎟️ **Total de Conversões Rastreadas:** {total_conversoes}")
