"""
Pagina: Relatorios v5.0
Relatorio completo reformulado conforme especificacoes AIR
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import Counter
import base64
from utils import data_manager, funcoes_auxiliares

def render():
    """Renderiza relatorio"""
    
    modo = st.session_state.get('modo_relatorio', 'campanha')
    
    if modo == 'campanha':
        campanha = data_manager.get_campanha(st.session_state.campanha_atual_id)
        if not campanha:
            st.warning("Selecione uma campanha")
            return
        render_relatorio([campanha])
    else:
        # Relatorio por cliente
        cliente_id = st.session_state.get('relatorio_cliente_id')
        campanhas_ids = st.session_state.get('relatorio_campanhas_ids', [])
        
        if not cliente_id:
            st.warning("Selecione um cliente")
            return
        
        cliente = data_manager.get_cliente(cliente_id)
        campanhas_cliente = data_manager.get_campanhas_por_cliente(cliente_id)
        
        if campanhas_ids:
            campanhas_filtradas = [c for c in campanhas_cliente if c['id'] in campanhas_ids]
        else:
            campanhas_filtradas = campanhas_cliente
        
        render_relatorio(campanhas_filtradas, cliente)


def render_relatorio(campanhas_list, cliente=None):
    """Renderiza o relatorio completo"""
    
    if not campanhas_list:
        st.warning("Nenhuma campanha selecionada")
        return
    
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        if len(campanhas_list) == 1:
            camp = campanhas_list[0]
            aon = "[AON]" if camp.get('is_aon') else ""
            st.markdown(f'<p class="main-header">Relatorio: {camp["nome"]} {aon}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="subtitle">{camp.get("cliente_nome", "")} | {funcoes_auxiliares.formatar_data_br(camp["data_inicio"])} - {funcoes_auxiliares.formatar_data_br(camp["data_fim"])}</p>', unsafe_allow_html=True)
        else:
            st.markdown(f'<p class="main-header">Relatorio: {cliente["nome"]}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="subtitle">{len(campanhas_list)} campanhas selecionadas</p>', unsafe_allow_html=True)
    
    with col2:
        if st.button("<- Voltar", use_container_width=True):
            if len(campanhas_list) == 1:
                st.session_state.current_page = 'Central'
            else:
                st.session_state.current_page = 'Clientes'
            st.rerun()
    
    # Verificar se tem AON
    has_aon = any(c.get('is_aon') for c in campanhas_list)
    
    # Calcular metricas
    metricas = data_manager.calcular_metricas_multiplas_campanhas(campanhas_list)
    cores = funcoes_auxiliares.get_cores_graficos()
    
    # Definir tabs
    if has_aon:
        tabs = st.tabs([
            "1. Big Numbers",
            "2. Analise Geral", 
            "3. Visao AON",
            "4. KPIs por Influ",
            "5. Top Performance",
            "6. Lista Influs",
            "Comentarios",
            "Glossario"
        ])
    else:
        tabs = st.tabs([
            "1. Big Numbers",
            "2. Analise Geral",
            "3. KPIs por Influ",
            "4. Top Performance",
            "5. Lista Influs",
            "Comentarios",
            "Glossario"
        ])
    
    tab_idx = 0
    
    # TAB 1: BIG NUMBERS
    with tabs[tab_idx]:
        render_pag1_big_numbers(campanhas_list, metricas, cores)
    tab_idx += 1
    
    # TAB 2: ANALISE GERAL
    with tabs[tab_idx]:
        render_pag2_analise_geral(campanhas_list, metricas, cores)
    tab_idx += 1
    
    # TAB 3: VISAO AON (se aplicavel)
    if has_aon:
        with tabs[tab_idx]:
            render_pag3_visao_aon(campanhas_list, metricas, cores, cliente)
        tab_idx += 1
    
    # TAB 4: KPIs por Influenciador
    with tabs[tab_idx]:
        render_pag4_kpis_influenciador(campanhas_list, cores)
    tab_idx += 1
    
    # TAB 5: Top Performance
    with tabs[tab_idx]:
        render_pag5_top_performance(campanhas_list, cores)
    tab_idx += 1
    
    # TAB 6: Lista Influenciadores
    with tabs[tab_idx]:
        render_pag6_lista_influenciadores(campanhas_list, cores)
    tab_idx += 1
    
    # TAB 7: Comentarios
    with tabs[tab_idx]:
        render_comentarios(campanhas_list, cores)
    tab_idx += 1
    
    # TAB 8: Glossario
    with tabs[tab_idx]:
        render_glossario()


def render_pag1_big_numbers(campanhas_list, metricas, cores):
    """Pagina 1 - Big Numbers reformulado"""
    
    primary_color = st.session_state.get('primary_color', '#7c3aed')
    secondary_color = st.session_state.get('secondary_color', '#fb923c')
    
    st.subheader("Metricas Gerais")
    
    # Pegar estimativas da campanha
    estimativa_alcance = 0
    estimativa_impressoes = 0
    if len(campanhas_list) == 1:
        estimativa_alcance = campanhas_list[0].get('estimativa_alcance', 0)
        estimativa_impressoes = campanhas_list[0].get('estimativa_impressoes', 0)
    
    # Calcular AIR Score medio
    todos_influs = []
    for camp in campanhas_list:
        for inf_camp in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
            if inf:
                todos_influs.append(inf)
    
    air_score_medio = 0
    if todos_influs:
        air_score_medio = sum(i.get('air_score', 0) for i in todos_influs) / len(todos_influs)
    
    # Layout: AIR Score | Estimativas | Metricas principais
    col_score, col_est1, col_est2, col_metrics = st.columns([1.2, 1.5, 1.5, 3])
    
    with col_score:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {primary_color}, {secondary_color});
            color: white;
            padding: 1.5rem;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
            height: 180px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <div style="font-size: 3rem; font-weight: 700;">{air_score_medio:.1f}</div>
            <div style="font-size: 0.9rem; opacity: 0.9; margin-top: 0.5rem;">AIR SCORE</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_est1:
        realizado_alcance = metricas['total_alcance']
        pct_alcance = (realizado_alcance / estimativa_alcance * 100) if estimativa_alcance > 0 else 0
        cor_pct = "#10b981" if pct_alcance >= 100 else ("#f59e0b" if pct_alcance >= 70 else "#ef4444")
        
        st.markdown(f"""
        <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1rem; text-align: center; height: 180px;">
            <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.5rem;">ALCANCE</div>
            <div style="font-size: 1.8rem; font-weight: 700; color: {primary_color};">{funcoes_auxiliares.formatar_numero(realizado_alcance)}</div>
            <div style="font-size: 0.7rem; color: #9ca3af; margin: 0.5rem 0;">Meta: {funcoes_auxiliares.formatar_numero(estimativa_alcance)}</div>
            <div style="font-size: 1.5rem; font-weight: 600; color: {cor_pct};">{pct_alcance:.0f}%</div>
            <div style="font-size: 0.65rem; color: #9ca3af;">da estimativa</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_est2:
        realizado_imp = metricas['total_impressoes'] + metricas['total_views']
        pct_imp = (realizado_imp / estimativa_impressoes * 100) if estimativa_impressoes > 0 else 0
        cor_pct2 = "#10b981" if pct_imp >= 100 else ("#f59e0b" if pct_imp >= 70 else "#ef4444")
        
        st.markdown(f"""
        <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1rem; text-align: center; height: 180px;">
            <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.5rem;">IMPRESSOES + VIEWS</div>
            <div style="font-size: 1.8rem; font-weight: 700; color: {primary_color};">{funcoes_auxiliares.formatar_numero(realizado_imp)}</div>
            <div style="font-size: 0.7rem; color: #9ca3af; margin: 0.5rem 0;">Meta: {funcoes_auxiliares.formatar_numero(estimativa_impressoes)}</div>
            <div style="font-size: 1.5rem; font-weight: 600; color: {cor_pct2};">{pct_imp:.0f}%</div>
            <div style="font-size: 0.65rem; color: #9ca3af;">da estimativa</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_metrics:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Influenciadores", metricas['total_influenciadores'])
            st.metric("Seguidores", funcoes_auxiliares.formatar_numero(metricas['total_seguidores']))
        with col2:
            st.metric("Posts", metricas['total_posts'])
            st.metric("Interacoes", funcoes_auxiliares.formatar_numero(metricas['total_interacoes']))
        with col3:
            st.metric("Views", funcoes_auxiliares.formatar_numero(metricas['total_views']))
            st.metric("Impressoes", funcoes_auxiliares.formatar_numero(metricas['total_impressoes']))
    
    st.markdown("---")
    
    # TAXAS
    st.subheader("Taxas de Performance")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        filtro_taxa = st.selectbox("Selecione a taxa:", ["Todas", "Engajamento Efetivo", "Engajamento Geral", "Taxa de Alcance"], key="filtro_taxa_pag1")
    
    taxa_eng_efetivo = metricas['engajamento_efetivo']
    taxa_eng_geral = (metricas['total_interacoes'] / metricas['total_seguidores'] * 100) if metricas['total_seguidores'] > 0 else 0
    taxa_alcance = metricas['taxa_alcance']
    
    with col2:
        if filtro_taxa == "Todas":
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Eng. Efetivo", f"{taxa_eng_efetivo:.2f}%")
            with col_b:
                st.metric("Eng. Geral", f"{taxa_eng_geral:.2f}%")
            with col_c:
                st.metric("Taxa Alcance", f"{taxa_alcance:.2f}%")
        elif filtro_taxa == "Engajamento Efetivo":
            st.metric("Engajamento Efetivo", f"{taxa_eng_efetivo:.2f}%")
        elif filtro_taxa == "Engajamento Geral":
            st.metric("Engajamento Geral", f"{taxa_eng_geral:.2f}%")
        else:
            st.metric("Taxa de Alcance", f"{taxa_alcance:.2f}%")
    
    st.markdown("---")
    
    # GRAFICOS
    st.subheader("Analise por Tier e Formato")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        kpi_selecionado = st.selectbox("KPI:", ["Seguidores", "Impressoes", "Alcance", "Interacoes", "Views"], key="kpi_pag1")
    
    with col2:
        filtro_formato = st.selectbox("Formato:", ["Todos", "Reels", "Feed", "Stories", "TikTok", "YouTube", "Carrossel"], key="formato_pag1")
    
    dados_tier = coletar_dados_por_tier(campanhas_list, kpi_selecionado.lower(), filtro_formato)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Distribuicao por Tier (%)**")
        if dados_tier:
            df = pd.DataFrame(dados_tier)
            df_agg = df.groupby('tier')['valor'].sum().reset_index()
            total = df_agg['valor'].sum()
            df_agg['percentual'] = (df_agg['valor'] / total * 100).round(1) if total > 0 else 0
            
            ordem_tier = ['Nano', 'Micro', 'Mid', 'Macro', 'Mega']
            df_agg['ordem'] = df_agg['tier'].apply(lambda x: ordem_tier.index(x) if x in ordem_tier else 99)
            df_agg = df_agg.sort_values('ordem')
            
            fig = go.Figure()
            cores_tier = {'Nano': cores[0], 'Micro': cores[1], 'Mid': cores[2], 'Macro': cores[3], 'Mega': cores[4]}
            
            for _, row in df_agg.iterrows():
                fig.add_trace(go.Bar(
                    y=[kpi_selecionado],
                    x=[row['percentual']],
                    name=f"{row['tier']} ({row['percentual']:.1f}%)",
                    orientation='h',
                    marker_color=cores_tier.get(row['tier'], cores[5]),
                    text=f"{row['tier']}: {row['percentual']:.1f}%",
                    textposition='inside'
                ))
            
            fig.update_layout(barmode='stack', height=200, showlegend=True, legend=dict(orientation='h', yanchor='bottom', y=1.02), xaxis=dict(title='Percentual (%)', range=[0, 100]), yaxis=dict(visible=False))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados")
    
    with col2:
        st.markdown("**Performance por Formato (Taxas)**")
        dados_radar = coletar_dados_radar_formato(campanhas_list)
        
        if dados_radar:
            df_radar = pd.DataFrame(dados_radar)
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=df_radar['taxa_alcance'].tolist() + [df_radar['taxa_alcance'].iloc[0]],
                theta=df_radar['formato'].tolist() + [df_radar['formato'].iloc[0]],
                fill='toself', name='Taxa Alcance',
                fillcolor='rgba(124, 58, 237, 0.2)', line=dict(color=cores[0], width=2)
            ))
            fig.add_trace(go.Scatterpolar(
                r=df_radar['taxa_eng'].tolist() + [df_radar['taxa_eng'].iloc[0]],
                theta=df_radar['formato'].tolist() + [df_radar['formato'].iloc[0]],
                fill='toself', name='Eng. Efetivo',
                fillcolor='rgba(249, 115, 22, 0.2)', line=dict(color=cores[1], width=2)
            ))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True)), height=350, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados")
    
    st.markdown("---")
    st.subheader("Notas")
    
    if len(campanhas_list) == 1:
        notas = st.text_area("Notas:", value=campanhas_list[0].get('notas', ''), height=100, placeholder="Insights...")
        if st.button("Salvar Notas", key="salvar_notas_pag1"):
            data_manager.atualizar_campanha(campanhas_list[0]['id'], {'notas': notas})
            st.success("Notas salvas!")


def render_pag2_analise_geral(campanhas_list, metricas, cores):
    """Pagina 2 - Analise Geral"""
    
    st.subheader("Analise de Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Grafico 1: Comparativo por Formato**")
        kpi1 = st.selectbox("KPI Barras:", ["Views", "Alcance", "Interacoes", "Impressoes"], key="kpi1_pag2")
        kpi2 = st.selectbox("KPI Linha:", ["Taxa Eng. Efetivo", "Taxa Alcance", "Interacoes", "Views"], key="kpi2_pag2")
        
        dados = coletar_dados_formato(campanhas_list)
        if dados:
            df = pd.DataFrame(dados)
            kpi_map = {'Views': 'views', 'Alcance': 'alcance', 'Interacoes': 'interacoes', 'Impressoes': 'impressoes'}
            campo1 = kpi_map.get(kpi1, 'views')
            
            df_agg = df.groupby('formato').agg({'views': 'sum', 'alcance': 'sum', 'interacoes': 'sum', 'impressoes': 'sum'}).reset_index()
            df_agg['taxa_eng'] = (df_agg['interacoes'] / df_agg['views'] * 100).round(2).fillna(0)
            df_agg['taxa_alcance'] = (df_agg['alcance'] / metricas['total_seguidores'] * 100).round(2) if metricas['total_seguidores'] > 0 else 0
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_agg['formato'], y=df_agg[campo1], name=kpi1, marker_color=cores[0], text=[funcoes_auxiliares.formatar_numero(v) for v in df_agg[campo1]], textposition='outside'))
            
            if kpi2 == "Taxa Eng. Efetivo":
                y2 = df_agg['taxa_eng']
            elif kpi2 == "Taxa Alcance":
                y2 = df_agg['taxa_alcance']
            else:
                y2 = df_agg[kpi_map.get(kpi2, 'interacoes')]
            
            fig.add_trace(go.Scatter(x=df_agg['formato'], y=y2, name=kpi2, mode='lines+markers', yaxis='y2', line=dict(color=cores[1], width=3), marker=dict(size=10)))
            fig.update_layout(yaxis=dict(title=kpi1), yaxis2=dict(title=kpi2, overlaying='y', side='right'), height=400, legend=dict(orientation='h', yanchor='bottom', y=1.02))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Grafico 2: Desempenho por Classificacao**")
        kpi3 = st.selectbox("KPI Barras:", ["Views", "Alcance", "Interacoes", "Impressoes"], key="kpi3_pag2")
        kpi4 = st.selectbox("KPI Linha:", ["Qtd Influenciadores", "Taxa Eng. Media", "Posts"], key="kpi4_pag2")
        
        dados_class = coletar_dados_classificacao_completo(campanhas_list)
        if dados_class:
            df = pd.DataFrame(dados_class)
            kpi_map = {'Views': 'views', 'Alcance': 'alcance', 'Interacoes': 'interacoes', 'Impressoes': 'impressoes'}
            campo3 = kpi_map.get(kpi3, 'views')
            
            df_agg = df.groupby('classificacao').agg({'views': 'sum', 'alcance': 'sum', 'interacoes': 'sum', 'impressoes': 'sum', 'influenciador': 'nunique', 'post_id': 'count'}).reset_index()
            df_agg.columns = ['classificacao', 'views', 'alcance', 'interacoes', 'impressoes', 'qtd_influs', 'posts']
            df_agg['taxa_eng_media'] = (df_agg['interacoes'] / df_agg['views'] * 100).round(2).fillna(0)
            
            ordem = ['Nano', 'Micro', 'Mid', 'Macro', 'Mega']
            df_agg['ordem'] = df_agg['classificacao'].apply(lambda x: ordem.index(x) if x in ordem else 99)
            df_agg = df_agg.sort_values('ordem')
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_agg['classificacao'], y=df_agg[campo3], name=kpi3, marker_color=cores[2], text=[funcoes_auxiliares.formatar_numero(v) for v in df_agg[campo3]], textposition='outside'))
            
            if kpi4 == "Qtd Influenciadores":
                y4 = df_agg['qtd_influs']
            elif kpi4 == "Taxa Eng. Media":
                y4 = df_agg['taxa_eng_media']
            else:
                y4 = df_agg['posts']
            
            fig.add_trace(go.Scatter(x=df_agg['classificacao'], y=y4, name=kpi4, mode='lines+markers', yaxis='y2', line=dict(color=cores[3], width=3), marker=dict(size=10)))
            fig.update_layout(yaxis=dict(title=kpi3), yaxis2=dict(title=kpi4, overlaying='y', side='right'), height=400, legend=dict(orientation='h', yanchor='bottom', y=1.02))
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Insights")
    col1, col2 = st.columns(2)
    with col1:
        if metricas['engajamento_efetivo'] > 5:
            st.success(f"Engajamento Excelente: {metricas['engajamento_efetivo']:.2f}%")
        elif metricas['engajamento_efetivo'] > 3:
            st.info(f"Engajamento Adequado: {metricas['engajamento_efetivo']:.2f}%")
        else:
            st.warning(f"Engajamento Baixo: {metricas['engajamento_efetivo']:.2f}%")
    with col2:
        if metricas['taxa_alcance'] > 50:
            st.success(f"Alcance Alto: {metricas['taxa_alcance']:.2f}%")
        elif metricas['taxa_alcance'] > 20:
            st.info(f"Alcance Bom: {metricas['taxa_alcance']:.2f}%")


def render_pag3_visao_aon(campanhas_list, metricas, cores, cliente=None):
    """Pagina 3 - Visao AON"""
    
    st.subheader("Visao AON - Evolucao Temporal")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filtro_metrica = st.selectbox("Metrica:", ["Impressoes", "Alcance", "Interacoes"], key="aon_metrica")
    with col2:
        filtro_taxa = st.selectbox("Taxa:", ["Taxa Eng. Efetivo", "Taxa Alcance"], key="aon_taxa")
    with col3:
        data_ini = st.date_input("De:", value=datetime.now() - timedelta(days=90), key="aon_di")
    with col4:
        data_fim = st.date_input("Ate:", value=datetime.now(), key="aon_df")
    
    st.markdown("---")
    
    dados_tempo = coletar_dados_temporais(campanhas_list, data_ini, data_fim)
    
    if not dados_tempo:
        st.warning("Nenhum post no periodo")
        return
    
    df = pd.DataFrame(dados_tempo)
    df['mes'] = pd.to_datetime(df['data']).dt.to_period('M').astype(str)
    
    metrica_map = {'Impressoes': 'impressoes', 'Alcance': 'alcance', 'Interacoes': 'interacoes'}
    campo = metrica_map.get(filtro_metrica, 'impressoes')
    
    df_tempo = df.groupby('data').agg({campo: 'sum', 'views': 'sum', 'alcance': 'sum', 'interacoes': 'sum', 'seguidores': 'sum'}).reset_index()
    df_tempo = df_tempo.sort_values('data')
    df_tempo['taxa_eng'] = (df_tempo['interacoes'] / df_tempo['views'] * 100).round(2).fillna(0)
    df_tempo['taxa_alcance'] = (df_tempo['alcance'] / df_tempo['seguidores'] * 100).round(2).fillna(0)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_tempo['data'], y=df_tempo[campo], name=filtro_metrica, marker_color=cores[0]))
    
    taxa_campo = 'taxa_eng' if filtro_taxa == "Taxa Eng. Efetivo" else 'taxa_alcance'
    fig.add_trace(go.Scatter(x=df_tempo['data'], y=df_tempo[taxa_campo], name=filtro_taxa, mode='lines+markers', yaxis='y2', line=dict(color=cores[1], width=3), marker=dict(size=8)))
    
    fig.update_layout(title=f'Evolucao de {filtro_metrica}', yaxis=dict(title=filtro_metrica), yaxis2=dict(title=filtro_taxa, overlaying='y', side='right'), height=450, legend=dict(orientation='h', yanchor='bottom', y=1.02))
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Resumo Mensal")
    
    df_mensal = df.groupby('mes').agg({'influenciador': 'nunique', 'seguidores': lambda x: x.drop_duplicates().sum(), 'views': 'sum', 'alcance': 'sum', 'interacoes': 'sum', 'impressoes': 'sum'}).reset_index()
    df_mensal.columns = ['Mes', 'Qtd Influs', 'Seguidores', 'Views', 'Alcance', 'Interacoes', 'Impressoes']
    st.dataframe(df_mensal, use_container_width=True, hide_index=True)


def render_pag4_kpis_influenciador(campanhas_list, cores):
    """Pagina 4 - KPIs por Influenciador (Top 15)"""
    
    st.subheader("KPIs por Influenciador (Top 15)")
    
    dados_inf = coletar_dados_influenciadores(campanhas_list)
    
    if not dados_inf:
        st.info("Nenhum dado disponivel")
        return
    
    df = pd.DataFrame(dados_inf)
    df = df.sort_values('views', ascending=False).head(15)
    
    st.markdown("### Grafico 1: Performance Geral")
    
    col1, col2 = st.columns(2)
    with col1:
        kpi_barra = st.selectbox("KPI Barras:", ["Seguidores", "Impressoes", "Alcance", "Interacoes"], key="kpi_barra_pag4")
    with col2:
        kpi_linha = st.selectbox("KPI Linha:", ["Taxa Eng. Efetivo", "Taxa Alcance", "Engajamento Total"], key="kpi_linha_pag4")
    
    kpi_map = {'Seguidores': 'seguidores', 'Impressoes': 'impressoes', 'Alcance': 'alcance', 'Interacoes': 'interacoes'}
    campo_barra = kpi_map.get(kpi_barra, 'seguidores')
    
    df_sorted = df.sort_values(campo_barra, ascending=True)
    
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=df_sorted[campo_barra], y=df_sorted['nome'], orientation='h', name=kpi_barra, marker_color=cores[0], text=[funcoes_auxiliares.formatar_numero(v) for v in df_sorted[campo_barra]], textposition='outside'))
    
    if kpi_linha == "Taxa Eng. Efetivo":
        y_linha = df_sorted['taxa_eng']
    elif kpi_linha == "Taxa Alcance":
        y_linha = df_sorted['taxa_alcance']
    else:
        y_linha = df_sorted['taxa_eng_geral']
    
    fig1.add_trace(go.Scatter(x=y_linha, y=df_sorted['nome'], mode='lines+markers', name=kpi_linha, xaxis='x2', line=dict(color=cores[1], width=2), marker=dict(size=8)))
    fig1.update_layout(xaxis=dict(title=kpi_barra, side='bottom'), xaxis2=dict(title=kpi_linha, overlaying='x', side='top'), height=max(400, len(df_sorted) * 30), legend=dict(orientation='h', yanchor='bottom', y=1.02))
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("### Grafico 2: Eficiencia de Gasto")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        metrica_custo = st.selectbox("Metrica:", ["CPM", "CPE", "CPI", "CPV"], key="custo_pag4")
        investimento = st.number_input("Investimento (R$):", min_value=0.0, value=float(sum([d.get('custo', 0) for d in dados_inf])), step=100.0, key="invest_pag4")
    
    with col2:
        df_custo = df.copy()
        if metrica_custo == "CPM":
            df_custo['metrica'] = (df_custo['custo'] / df_custo['views'] * 1000).round(2).fillna(0)
        elif metrica_custo == "CPE":
            df_custo['metrica'] = (df_custo['custo'] / df_custo['interacoes']).round(2).fillna(0)
        elif metrica_custo == "CPI":
            df_custo['metrica'] = (df_custo['custo'] / df_custo['impressoes']).round(4).fillna(0)
        else:
            df_custo['metrica'] = (df_custo['custo'] / df_custo['views']).round(4).fillna(0)
        
        df_custo = df_custo[df_custo['metrica'] > 0].sort_values('metrica', ascending=False)
        
        if not df_custo.empty:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=df_custo['metrica'], y=df_custo['nome'], orientation='h', marker_color=cores[4], text=[f"R$ {v:.2f}" for v in df_custo['metrica']], textposition='outside'))
            fig2.update_layout(title=f'{metrica_custo} (R$)', height=max(300, len(df_custo) * 25))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Adicione custos aos posts")
    
    st.markdown("### Grafico 3: Trafego")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        tipo_trafego = st.selectbox("Tipo:", ["Cliques Link", "Ambos"], key="trafego_pag4")
    
    with col2:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=df['cliques_link'], y=df['nome'], orientation='h', name='Cliques Link', marker_color=cores[5]))
        
        for i, row in df.iterrows():
            fig3.add_annotation(x=0, y=row['nome'], text=f"({funcoes_auxiliares.formatar_numero(row['seguidores'])} seg)", showarrow=False, xanchor='right', xshift=-10, font=dict(size=9, color='gray'))
        
        fig3.update_layout(title='Trafego por Influenciador', height=max(300, len(df) * 25))
        st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Insights")
    
    if len(campanhas_list) == 1:
        insights_texto = st.text_area("Insights:", value=campanhas_list[0].get('insights_config', {}).get('insights_influenciadores', ''), height=100, key="insights_pag4")
        if st.button("Salvar Insights", key="salvar_insights_pag4"):
            insights_config = campanhas_list[0].get('insights_config', {})
            insights_config['insights_influenciadores'] = insights_texto
            data_manager.atualizar_campanha(campanhas_list[0]['id'], {'insights_config': insights_config})
            st.success("Insights salvos!")


def render_pag5_top_performance(campanhas_list, cores):
    """Pagina 5 - Top Performance"""
    
    st.subheader("Top Performance")
    
    dados_influs = coletar_dados_influenciadores(campanhas_list)
    
    if not dados_influs:
        st.info("Nenhum dado")
        return
    
    df = pd.DataFrame(dados_influs)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        metrica_ordenar = st.selectbox("Ordenar:", ["EMV (Custo)", "Interacoes", "Taxa Eng. Efetivo", "Views", "Alcance"], key="ordenar_pag5")
    with col2:
        filtro_class = st.multiselect("Classificacao:", ["Nano", "Micro", "Mid", "Macro", "Mega"], key="class_pag5")
    with col3:
        qtd = st.slider("Quantidade:", 5, 30, 15, key="qtd_pag5")
    
    if filtro_class:
        df = df[df['classificacao'].isin(filtro_class)]
    
    ordem_map = {"EMV (Custo)": "custo", "Interacoes": "interacoes", "Taxa Eng. Efetivo": "taxa_eng", "Views": "views", "Alcance": "alcance"}
    df = df.sort_values(ordem_map.get(metrica_ordenar, 'interacoes'), ascending=False).head(qtd)
    
    if len(df) > 0:
        st.markdown("### Dispersao: Engajamento vs Alcance")
        
        fig = px.scatter(df, x='taxa_alcance', y='taxa_eng', size='views', color='classificacao', hover_name='nome', text='nome', labels={'taxa_alcance': 'Taxa de Alcance (%)', 'taxa_eng': 'Taxa de Engajamento (%)'}, color_discrete_sequence=cores)
        fig.update_traces(textposition='top center', textfont_size=9)
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Lista")
    
    for _, row in df.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([0.5, 2, 1.2, 1.2, 1.2, 1.2])
        with col1:
            if row.get('foto'):
                st.image(row['foto'], width=40)
        with col2:
            st.write(f"**{row['nome']}**")
            st.caption(f"@{row['usuario']} | {row['classificacao']}")
        with col3:
            st.metric("EMV", f"R$ {row.get('custo', 0):,.0f}")
        with col4:
            st.metric("Interacoes", funcoes_auxiliares.formatar_numero(row['interacoes']))
        with col5:
            st.metric("Taxa Eng.", f"{row['taxa_eng']:.2f}%")
        with col6:
            st.metric("Views", funcoes_auxiliares.formatar_numero(row['views']))
        st.markdown("---")


def render_pag6_lista_influenciadores(campanhas_list, cores):
    """Pagina 6 - Lista completa"""
    
    st.subheader("Lista de Influenciadores")
    
    col1, col2 = st.columns(2)
    with col1:
        filtro_class = st.multiselect("Classificacao:", ["Nano", "Micro", "Mid", "Macro", "Mega"], key="class_pag6")
    with col2:
        ordenar = st.selectbox("Ordenar:", ["Views", "Alcance", "Interacoes", "Taxa Eng."], key="ord_pag6")
    
    dados = coletar_dados_influenciadores(campanhas_list)
    
    if not dados:
        st.info("Nenhum influenciador")
        return
    
    df = pd.DataFrame(dados)
    
    if filtro_class:
        df = df[df['classificacao'].isin(filtro_class)]
    
    ordem_map = {"Views": "views", "Alcance": "alcance", "Interacoes": "interacoes", "Taxa Eng.": "taxa_eng"}
    df = df.sort_values(ordem_map.get(ordenar, 'views'), ascending=False)
    
    st.dataframe(df[['nome', 'usuario', 'classificacao', 'seguidores', 'posts', 'views', 'alcance', 'interacoes', 'taxa_eng', 'taxa_alcance']].rename(columns={'nome': 'Nome', 'usuario': 'Usuario', 'classificacao': 'Classe', 'seguidores': 'Seguidores', 'posts': 'Posts', 'views': 'Views', 'alcance': 'Alcance', 'interacoes': 'Interacoes', 'taxa_eng': 'Taxa Eng. %', 'taxa_alcance': 'Taxa Alc. %'}), use_container_width=True, hide_index=True)


# ========================================
# FUNCOES AUXILIARES
# ========================================

def coletar_dados_por_tier(campanhas_list, kpi, filtro_formato):
    dados = []
    for camp in campanhas_list:
        for camp_inf in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(camp_inf.get('influenciador_id'))
            if not inf:
                continue
            tier = camp_inf.get('snapshot_dados', {}).get('classificacao', inf.get('classificacao', 'Desconhecido'))
            for post in camp_inf.get('posts', []):
                if filtro_formato != "Todos" and post.get('formato') != filtro_formato:
                    continue
                valor = post.get(kpi, 0)
                if kpi == 'seguidores':
                    valor = inf.get('seguidores', 0)
                if valor > 0:
                    dados.append({'tier': tier, 'valor': valor})
    return dados


def coletar_dados_radar_formato(campanhas_list):
    dados_formato = {}
    for camp in campanhas_list:
        for camp_inf in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(camp_inf.get('influenciador_id'))
            seguidores = inf.get('seguidores', 1) if inf else 1
            for post in camp_inf.get('posts', []):
                formato = post.get('formato', 'Outro')
                if formato not in dados_formato:
                    dados_formato[formato] = {'views': 0, 'alcance': 0, 'interacoes': 0, 'seguidores': 0}
                dados_formato[formato]['views'] += post.get('views', 0)
                dados_formato[formato]['alcance'] += post.get('alcance', 0)
                dados_formato[formato]['interacoes'] += post.get('interacoes', 0)
                dados_formato[formato]['seguidores'] += seguidores
    resultado = []
    for formato, vals in dados_formato.items():
        taxa_eng = (vals['interacoes'] / vals['views'] * 100) if vals['views'] > 0 else 0
        taxa_alcance = (vals['alcance'] / vals['seguidores'] * 100) if vals['seguidores'] > 0 else 0
        resultado.append({'formato': formato, 'taxa_eng': round(taxa_eng, 2), 'taxa_alcance': round(taxa_alcance, 2)})
    return resultado


def coletar_dados_formato(campanhas_list):
    dados = []
    for camp in campanhas_list:
        for camp_inf in camp.get('influenciadores', []):
            for post in camp_inf.get('posts', []):
                dados.append({'formato': post.get('formato', 'Outro'), 'views': post.get('views', 0), 'alcance': post.get('alcance', 0), 'interacoes': post.get('interacoes', 0), 'impressoes': post.get('impressoes', 0)})
    return dados


def coletar_dados_classificacao_completo(campanhas_list):
    dados = []
    for camp in campanhas_list:
        for camp_inf in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(camp_inf.get('influenciador_id'))
            if not inf:
                continue
            classificacao = camp_inf.get('snapshot_dados', {}).get('classificacao', inf.get('classificacao', 'Desconhecido'))
            for post in camp_inf.get('posts', []):
                dados.append({'classificacao': classificacao, 'influenciador': inf['nome'], 'post_id': post.get('id', 0), 'views': post.get('views', 0), 'alcance': post.get('alcance', 0), 'interacoes': post.get('interacoes', 0), 'impressoes': post.get('impressoes', 0)})
    return dados


def coletar_dados_temporais(campanhas_list, data_ini, data_fim):
    dados = []
    for camp in campanhas_list:
        for camp_inf in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(camp_inf.get('influenciador_id'))
            if not inf:
                continue
            seguidores = inf.get('seguidores', 0)
            for post in camp_inf.get('posts', []):
                try:
                    data_post = datetime.strptime(post.get('data_publicacao', ''), '%d/%m/%Y')
                    if data_ini <= data_post.date() <= data_fim:
                        dados.append({'data': data_post, 'influenciador': inf['nome'], 'seguidores': seguidores, 'views': post.get('views', 0), 'alcance': post.get('alcance', 0), 'interacoes': post.get('interacoes', 0), 'impressoes': post.get('impressoes', 0)})
                except:
                    pass
    return dados


def coletar_dados_influenciadores(campanhas_list):
    dados_inf = {}
    for camp in campanhas_list:
        for camp_inf in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(camp_inf.get('influenciador_id'))
            if not inf:
                continue
            inf_id = inf['id']
            if inf_id not in dados_inf:
                dados_inf[inf_id] = {'id': inf_id, 'nome': inf['nome'], 'usuario': inf['usuario'], 'foto': inf.get('foto', ''), 'classificacao': inf.get('classificacao', 'Desconhecido'), 'seguidores': inf.get('seguidores', 0), 'views': 0, 'alcance': 0, 'interacoes': 0, 'impressoes': 0, 'custo': 0, 'cliques_link': 0, 'posts': 0}
            for post in camp_inf.get('posts', []):
                dados_inf[inf_id]['views'] += post.get('views', 0)
                dados_inf[inf_id]['alcance'] += post.get('alcance', 0)
                dados_inf[inf_id]['interacoes'] += post.get('interacoes', 0)
                dados_inf[inf_id]['impressoes'] += post.get('impressoes', 0)
                dados_inf[inf_id]['custo'] += post.get('custo', 0)
                dados_inf[inf_id]['cliques_link'] += post.get('clique_link', 0)
                dados_inf[inf_id]['posts'] += 1
    resultado = []
    for inf_id, d in dados_inf.items():
        d['taxa_eng'] = round((d['interacoes'] / d['views'] * 100), 2) if d['views'] > 0 else 0
        d['taxa_alcance'] = round((d['alcance'] / d['seguidores'] * 100), 2) if d['seguidores'] > 0 else 0
        d['taxa_eng_geral'] = round((d['interacoes'] / d['seguidores'] * 100), 2) if d['seguidores'] > 0 else 0
        resultado.append(d)
    return resultado


def render_comentarios(campanhas_list, cores):
    st.subheader("Analise de Comentarios")
    comentarios = []
    for camp in campanhas_list:
        for camp_inf in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(camp_inf.get('influenciador_id'))
            for post in camp_inf.get('posts', []):
                for com in post.get('comentarios', []):
                    comentarios.append({'influenciador': inf['nome'] if inf else 'Desconhecido', 'texto': com.get('texto', ''), 'polaridade': com.get('polaridade', 'neutro'), 'categoria': com.get('categoria', 'Geral')})
    if not comentarios:
        st.info("Nenhum comentario")
        return
    total = len(comentarios)
    positivos = len([c for c in comentarios if c['polaridade'] == 'positivo'])
    neutros = len([c for c in comentarios if c['polaridade'] == 'neutro'])
    negativos = len([c for c in comentarios if c['polaridade'] == 'negativo'])
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Positivos", f"{positivos} ({positivos/total*100:.0f}%)")
    with col3:
        st.metric("Neutros", f"{neutros} ({neutros/total*100:.0f}%)")
    with col4:
        st.metric("Negativos", f"{negativos} ({negativos/total*100:.0f}%)")
    categorias_count = Counter([c['categoria'] for c in comentarios])
    df_cat = pd.DataFrame(categorias_count.items(), columns=['Categoria', 'Quantidade'])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_cat['Categoria'], y=df_cat['Quantidade'], marker_color=cores[:len(df_cat)]))
    fig.update_layout(title='Comentarios por Categoria', height=350)
    st.plotly_chart(fig, use_container_width=True)


def render_glossario():
    st.subheader("AIR Glossary")
    glossario = {
        "AIRSCORE": "Metrica institucional da AIR que avalia a qualidade do engajamento de um perfil.",
        "INTERACOES": "Curtidas, comentarios, salvamentos, compartilhamentos, cliques no link, cliques em @'s e #'s, dm's e reacoes.",
        "ADERENCIA": "Percentual de comentarios relacionados a marca/produtos/publicidade.",
        "ALCANCE": "Numero aproximado de usuarios unicos alcancados.",
        "ENGAJAMENTO GERAL": "Interacoes dividido pelo total de seguidores.",
        "ENGAJAMENTO EFETIVO": "Interacoes dividido pelo alcance.",
        "TAXA DE ALCANCE": "Percentual da base de seguidores alcancada.",
        "IMPRESSOES": "Total de vezes que os conteudos foram exibidos.",
        "Nano": "< 10K seguidores", "Micro": "10K - 100K", "Mid": "100K - 500K", "Macro": "500K - 1M", "Mega": "> 1M"
    }
    for termo, definicao in glossario.items():
        with st.expander(termo):
            st.write(definicao)
