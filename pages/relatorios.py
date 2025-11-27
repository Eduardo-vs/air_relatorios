"""
Pagina: Relatorios
Relatorio completo com 8 paginas
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
    is_cliente_aon = cliente and cliente.get('is_aon', False) if cliente else has_aon
    
    # Calcular metricas
    metricas = data_manager.calcular_metricas_multiplas_campanhas(campanhas_list)
    cores = funcoes_auxiliares.get_cores_graficos()
    
    # Definir tabs baseado em AON
    if is_cliente_aon:
        tabs = st.tabs([
            "1. Big Numbers",
            "2. Pagina Principal",
            "3. Visao AON",
            "4. KPIs por Influenciador",
            "5. Top Performance",
            "6. Lista Influenciadores",
            "7. Comentarios",
            "8. Nuvem de Palavras",
            "9. Glossario"
        ])
        tab_offset = 0
    else:
        tabs = st.tabs([
            "1. Big Numbers",
            "2. Pagina Principal",
            "3. KPIs por Influenciador",
            "4. Top Performance",
            "5. Lista Influenciadores",
            "6. Comentarios",
            "7. Nuvem de Palavras",
            "8. Glossario"
        ])
        tab_offset = -1
    
    # TAB 1: BIG NUMBERS
    with tabs[0]:
        render_big_numbers(campanhas_list, metricas, cores)
    
    # TAB 2: PAGINA PRINCIPAL
    with tabs[1]:
        render_pagina_principal(campanhas_list, metricas, cores)
    
    # TAB 3: VISAO AON (se aplicavel)
    if is_cliente_aon:
        with tabs[2]:
            render_visao_aon(campanhas_list, metricas, cores, cliente)
    
    # TAB 4 (ou 3): KPIs por Influenciador
    with tabs[3 + tab_offset]:
        render_kpis_influenciador(campanhas_list, cores)
    
    # TAB 5 (ou 4): Top Performance
    with tabs[4 + tab_offset]:
        render_top_performance(campanhas_list, cores)
    
    # TAB 6 (ou 5): Lista Influenciadores
    with tabs[5 + tab_offset]:
        render_lista_influenciadores(campanhas_list, cores)
    
    # TAB 7 (ou 6): Comentarios
    with tabs[6 + tab_offset]:
        render_comentarios(campanhas_list, cores)
    
    # TAB 8 (ou 7): Nuvem de Palavras
    with tabs[7 + tab_offset]:
        render_nuvem_palavras(campanhas_list, cores)
    
    # TAB 9 (ou 8): Glossario
    with tabs[8 + tab_offset]:
        render_glossario()


# ========================================
# TAB 1: BIG NUMBERS
# ========================================

def render_big_numbers(campanhas_list, metricas, cores):
    """Pagina 1 - Big Numbers"""
    
    st.subheader("Metricas Gerais")
    
    # Filtro de metrica principal
    col1, col2 = st.columns([2, 3])
    with col1:
        metrica_filtro = st.selectbox(
            "Metrica principal:",
            ["Views", "Alcance", "Interacoes", "Impressoes"],
            key="bn_metrica"
        )
    
    st.markdown("---")
    
    # Big Numbers em grid
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="card-metric">
            <div class="card-metric-value">{metricas['total_influenciadores']}</div>
            <div class="card-metric-label">Influenciadores</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="card-metric">
            <div class="card-metric-value">{funcoes_auxiliares.formatar_numero(metricas['total_seguidores'])}</div>
            <div class="card-metric-label">Seguidores</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="card-metric">
            <div class="card-metric-value">{funcoes_auxiliares.formatar_numero(metricas['total_alcance'])}</div>
            <div class="card-metric-label">Alcance</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="card-metric">
            <div class="card-metric-value">{funcoes_auxiliares.formatar_numero(metricas['total_views'])}</div>
            <div class="card-metric-label">Views</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="card-metric">
            <div class="card-metric-value">{funcoes_auxiliares.formatar_numero(metricas['total_interacoes'])}</div>
            <div class="card-metric-label">Interacoes</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div class="card-metric">
            <div class="card-metric-value">{metricas['total_posts']}</div>
            <div class="card-metric-label">Posts</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Segunda linha
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Impressoes", funcoes_auxiliares.formatar_numero(metricas['total_impressoes']))
    with col2:
        st.metric("Curtidas", funcoes_auxiliares.formatar_numero(metricas['total_curtidas']))
    with col3:
        st.metric("Comentarios", funcoes_auxiliares.formatar_numero(metricas['total_comentarios']))
    with col4:
        st.metric("Saves", funcoes_auxiliares.formatar_numero(metricas['total_saves']))
    with col5:
        st.metric("Taxa Eng.", f"{metricas['engajamento_efetivo']}%")
    with col6:
        st.metric("Taxa Alcance", f"{metricas['taxa_alcance']}%")
    
    st.markdown("---")
    
    # Graficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribuicao por formato - grafico de barras com percentual
        st.markdown("**Distribuicao por Formato (%)**")
        
        dados_formato = coletar_dados_formato(campanhas_list)
        if dados_formato:
            df = pd.DataFrame(dados_formato)
            
            metrica_map = {
                "Views": "views", "Alcance": "alcance",
                "Interacoes": "interacoes", "Impressoes": "impressoes"
            }
            campo = metrica_map.get(metrica_filtro, 'views')
            
            df_agg = df.groupby('formato')[campo].sum().reset_index()
            total = df_agg[campo].sum()
            df_agg['percentual'] = (df_agg[campo] / total * 100).round(1)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_agg['formato'],
                y=df_agg['percentual'],
                text=[f"{p}%" for p in df_agg['percentual']],
                textposition='outside',
                marker_color=cores[:len(df_agg)]
            ))
            fig.update_layout(
                yaxis_title='Percentual (%)',
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Grafico Radar - Performance por tamanho de influenciador
        st.markdown("**Performance por Tamanho de Influenciador**")
        
        dados_class = coletar_dados_classificacao(campanhas_list, metrica_filtro.lower())
        
        if dados_class:
            df_class = pd.DataFrame(dados_class)
            df_agg = df_class.groupby('classificacao')['valor'].sum().reset_index()
            
            # Ordenar
            ordem = ['Nano', 'Micro', 'Mid', 'Macro', 'Mega']
            df_agg['ordem'] = df_agg['classificacao'].apply(lambda x: ordem.index(x) if x in ordem else 99)
            df_agg = df_agg.sort_values('ordem')
            
            # Normalizar para radar
            max_val = df_agg['valor'].max()
            df_agg['normalizado'] = df_agg['valor'] / max_val * 100 if max_val > 0 else 0
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=df_agg['normalizado'].tolist() + [df_agg['normalizado'].iloc[0]],
                theta=df_agg['classificacao'].tolist() + [df_agg['classificacao'].iloc[0]],
                fill='toself',
                fillcolor='rgba(124, 58, 237, 0.3)',
                line=dict(color=cores[0], width=2),
                name=metrica_filtro
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)


# ========================================
# TAB 2: PAGINA PRINCIPAL
# ========================================

def render_pagina_principal(campanhas_list, metricas, cores):
    """Pagina 2 - Graficos e Insights"""
    
    st.subheader("Analise de Performance")
    
    # Graficos de comparacao de formato
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Comparacao de Formato (Barra + Linha)**")
        
        dados_formato = coletar_dados_formato(campanhas_list)
        if dados_formato:
            df = pd.DataFrame(dados_formato)
            df_agg = df.groupby('formato').agg({
                'views': 'sum',
                'interacoes': 'sum'
            }).reset_index()
            
            fig = go.Figure()
            
            # Barras - Views
            fig.add_trace(go.Bar(
                x=df_agg['formato'],
                y=df_agg['views'],
                name='Views',
                marker_color=cores[0],
                text=[funcoes_auxiliares.formatar_numero(v) for v in df_agg['views']],
                textposition='outside'
            ))
            
            # Linha - Interacoes
            fig.add_trace(go.Scatter(
                x=df_agg['formato'],
                y=df_agg['interacoes'],
                name='Interacoes',
                mode='lines+markers',
                yaxis='y2',
                line=dict(color=cores[1], width=3),
                marker=dict(size=10)
            ))
            
            fig.update_layout(
                yaxis=dict(title='Views'),
                yaxis2=dict(title='Interacoes', overlaying='y', side='right'),
                height=400,
                legend=dict(orientation='h', yanchor='bottom', y=1.02)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Desempenho por Classificacao (Barra + Linha)**")
        
        dados_class = coletar_dados_classificacao_completo(campanhas_list)
        if dados_class:
            df = pd.DataFrame(dados_class)
            df_agg = df.groupby('classificacao').agg({
                'views': 'sum',
                'interacoes': 'sum',
                'influenciador': 'nunique'
            }).reset_index()
            df_agg.columns = ['classificacao', 'views', 'interacoes', 'qtd_influs']
            
            # Ordenar
            ordem = ['Nano', 'Micro', 'Mid', 'Macro', 'Mega']
            df_agg['ordem'] = df_agg['classificacao'].apply(lambda x: ordem.index(x) if x in ordem else 99)
            df_agg = df_agg.sort_values('ordem')
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=df_agg['classificacao'],
                y=df_agg['views'],
                name='Views',
                marker_color=cores[2],
                text=[funcoes_auxiliares.formatar_numero(v) for v in df_agg['views']],
                textposition='outside'
            ))
            
            fig.add_trace(go.Scatter(
                x=df_agg['classificacao'],
                y=df_agg['qtd_influs'],
                name='Qtd Influs',
                mode='lines+markers',
                yaxis='y2',
                line=dict(color=cores[3], width=3),
                marker=dict(size=10)
            ))
            
            fig.update_layout(
                yaxis=dict(title='Views'),
                yaxis2=dict(title='Qtd Influenciadores', overlaying='y', side='right'),
                height=400,
                legend=dict(orientation='h', yanchor='bottom', y=1.02)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Insights
    st.subheader("Insights")
    
    # Verificar config de insights
    insights_config = campanhas_list[0].get('insights_config', {}) if len(campanhas_list) == 1 else {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        if insights_config.get('mostrar_engajamento', True):
            if metricas['engajamento_efetivo'] > 5:
                st.success(f"[ENGAJAMENTO EXCELENTE] Taxa de {metricas['engajamento_efetivo']}% esta acima da referencia de mercado (3-5%)")
            elif metricas['engajamento_efetivo'] > 3:
                st.info(f"[ENGAJAMENTO ADEQUADO] Taxa de {metricas['engajamento_efetivo']}% esta dentro da referencia")
            else:
                st.warning(f"[ATENCAO] Taxa de {metricas['engajamento_efetivo']}% abaixo da referencia")
        
        if insights_config.get('mostrar_saves', True) and metricas['total_saves'] > 0:
            taxa_saves = (metricas['total_saves'] / metricas['total_views'] * 100) if metricas['total_views'] > 0 else 0
            if taxa_saves > 2:
                st.success(f"[ALTO VALOR] {metricas['total_saves']:,} saves ({taxa_saves:.2f}% dos views)")
    
    with col2:
        if insights_config.get('mostrar_alcance', True):
            if metricas['taxa_alcance'] > 50:
                st.success(f"[ALCANCE ALTO] Taxa de {metricas['taxa_alcance']}% da base de seguidores")
            elif metricas['taxa_alcance'] > 20:
                st.info(f"[ALCANCE BOM] Taxa de {metricas['taxa_alcance']}% da base")
        
        if insights_config.get('mostrar_conversao', True) and metricas['total_conversoes_cupom'] > 0:
            st.success(f"[CONVERSAO] {metricas['total_conversoes_cupom']} conversoes via cupom")
    
    # Insights personalizados
    insights_personalizados = insights_config.get('insights_personalizados', [])
    if insights_personalizados:
        st.markdown("---")
        st.markdown("**Observacoes:**")
        for insight in insights_personalizados:
            st.write(f"- {insight}")
    
    st.markdown("---")
    
    # Campo de escrita livre
    st.subheader("Notas e Observacoes")
    
    if len(campanhas_list) == 1:
        notas = st.text_area(
            "Adicione suas notas:",
            value=campanhas_list[0].get('notas', ''),
            height=150,
            placeholder="Digite aqui suas observacoes, insights adicionais, conclusoes..."
        )
        
        if st.button("Salvar Notas"):
            data_manager.atualizar_campanha(campanhas_list[0]['id'], {'notas': notas})
            st.success("Notas salvas!")
    else:
        st.text_area(
            "Notas (modo visualizacao):",
            value="Para editar notas, acesse o relatorio de cada campanha individualmente.",
            height=100,
            disabled=True
        )


def coletar_dados_formato(campanhas_list):
    """Coleta dados agregados por formato"""
    dados = []
    for camp in campanhas_list:
        for camp_inf in camp['influenciadores']:
            for post in camp_inf['posts']:
                dados.append({
                    'formato': post['formato'],
                    'views': post.get('views', 0),
                    'alcance': post.get('alcance', 0),
                    'interacoes': post.get('interacoes', 0),
                    'impressoes': post.get('impressoes', 0)
                })
    return dados


def coletar_dados_classificacao(campanhas_list, metrica):
    """Coleta dados por classificacao de influenciador"""
    dados = []
    for camp in campanhas_list:
        for camp_inf in camp['influenciadores']:
            inf = data_manager.get_influenciador(camp_inf['influenciador_id'])
            if not inf:
                continue
            
            classificacao = camp_inf['snapshot_dados'].get('classificacao', inf.get('classificacao', 'Desconhecido'))
            
            total = 0
            for post in camp_inf['posts']:
                if metrica == 'views':
                    total += post.get('views', 0)
                elif metrica == 'alcance':
                    total += post.get('alcance', 0)
                elif metrica == 'interacoes':
                    total += post.get('interacoes', 0)
                elif metrica == 'impressoes':
                    total += post.get('impressoes', 0)
            
            if total > 0:
                dados.append({'classificacao': classificacao, 'valor': total})
    
    return dados


def coletar_dados_classificacao_completo(campanhas_list):
    """Coleta dados completos por classificacao"""
    dados = []
    for camp in campanhas_list:
        for camp_inf in camp['influenciadores']:
            inf = data_manager.get_influenciador(camp_inf['influenciador_id'])
            if not inf:
                continue
            
            classificacao = camp_inf['snapshot_dados'].get('classificacao', inf.get('classificacao', 'Desconhecido'))
            
            for post in camp_inf['posts']:
                dados.append({
                    'classificacao': classificacao,
                    'influenciador': inf['nome'],
                    'views': post.get('views', 0),
                    'interacoes': post.get('interacoes', 0)
                })
    
    return dados


# ========================================
# TAB 3: VISAO AON (Clientes AON)
# ========================================

def render_visao_aon(campanhas_list, metricas, cores, cliente=None):
    """Pagina 3 - Visao especial para clientes AON"""
    
    st.subheader("Visao AON - Evolucao Temporal")
    
    # Filtros
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Lista de influenciadores
        todos_influs = []
        for camp in campanhas_list:
            for camp_inf in camp['influenciadores']:
                inf = data_manager.get_influenciador(camp_inf['influenciador_id'])
                if inf and inf['nome'] not in todos_influs:
                    todos_influs.append(inf['nome'])
        
        filtro_influ = st.selectbox("Influenciador", ["Todos"] + todos_influs)
    
    with col2:
        data_ini = st.date_input("De:", value=datetime.now() - timedelta(days=30), key="aon_di")
    
    with col3:
        data_fim = st.date_input("Ate:", value=datetime.now(), key="aon_df")
    
    with col4:
        kpi = st.selectbox("KPI", ["Views", "Alcance", "Interacoes", "Impressoes"])
    
    st.markdown("---")
    
    # Coletar dados temporais
    dados_tempo = []
    
    for camp in campanhas_list:
        for camp_inf in camp['influenciadores']:
            inf = data_manager.get_influenciador(camp_inf['influenciador_id'])
            if not inf:
                continue
            
            if filtro_influ != "Todos" and inf['nome'] != filtro_influ:
                continue
            
            for post in camp_inf['posts']:
                try:
                    data_post = datetime.strptime(post['data_publicacao'], '%d/%m/%Y')
                    
                    if data_ini <= data_post.date() <= data_fim:
                        kpi_map = {
                            'Views': post.get('views', 0),
                            'Alcance': post.get('alcance', 0),
                            'Interacoes': post.get('interacoes', 0),
                            'Impressoes': post.get('impressoes', 0)
                        }
                        
                        dados_tempo.append({
                            'data': data_post,
                            'mes': data_post.strftime('%Y-%m'),
                            'valor': kpi_map[kpi],
                            'influenciador': inf['nome'],
                            'campanha': camp['nome']
                        })
                except:
                    pass
    
    if not dados_tempo:
        st.warning("Nenhum post no periodo selecionado")
        return
    
    df = pd.DataFrame(dados_tempo)
    
    # Grafico de evolucao (barra + linha)
    df_tempo = df.groupby('data')['valor'].sum().reset_index()
    df_tempo = df_tempo.sort_values('data')
    df_tempo['acumulado'] = df_tempo['valor'].cumsum()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_tempo['data'],
        y=df_tempo['valor'],
        name=f'{kpi} Diario',
        marker_color=cores[0]
    ))
    
    fig.add_trace(go.Scatter(
        x=df_tempo['data'],
        y=df_tempo['acumulado'],
        name='Acumulado',
        mode='lines+markers',
        yaxis='y2',
        line=dict(color=cores[1], width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=f'Evolucao de {kpi}',
        yaxis=dict(title=f'{kpi} Diario'),
        yaxis2=dict(title='Acumulado', overlaying='y', side='right'),
        height=450,
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Visao de empresa (para cliente AON)
    if cliente or len(campanhas_list) > 1:
        st.subheader("Visao Geral - Empresa")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Campanhas por mes
            df_mes = df.groupby('mes').agg({
                'valor': 'sum',
                'campanha': 'nunique',
                'influenciador': 'nunique'
            }).reset_index()
            df_mes.columns = ['Mes', kpi, 'Campanhas', 'Influenciadores']
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_mes['Mes'],
                y=df_mes['Campanhas'],
                name='Campanhas',
                marker_color=cores[2]
            ))
            fig.update_layout(title='Campanhas por Mes', height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Influs por mes
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_mes['Mes'],
                y=df_mes['Influenciadores'],
                name='Influenciadores',
                marker_color=cores[3]
            ))
            fig.update_layout(title='Influenciadores por Mes', height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabela geralzao
        st.markdown("**Resumo Mensal**")
        st.dataframe(df_mes, use_container_width=True, hide_index=True)
        
        # Destaque
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Influenciador Destaque:**")
            df_inf = df.groupby('influenciador')['valor'].sum().reset_index()
            if not df_inf.empty:
                top_inf = df_inf.loc[df_inf['valor'].idxmax()]
                st.success(f"{top_inf['influenciador']} - {funcoes_auxiliares.formatar_numero(int(top_inf['valor']))} {kpi}")
        
        with col2:
            st.markdown("**Melhor Campanha:**")
            df_camp = df.groupby('campanha')['valor'].sum().reset_index()
            if not df_camp.empty:
                top_camp = df_camp.loc[df_camp['valor'].idxmax()]
                st.success(f"{top_camp['campanha']} - {funcoes_auxiliares.formatar_numero(int(top_camp['valor']))} {kpi}")


# ========================================
# TAB 4: KPIs POR INFLUENCIADOR
# ========================================

def render_kpis_influenciador(campanhas_list, cores):
    """Pagina 4 - KPIs dinamicos por influenciador"""
    
    st.subheader("KPIs por Influenciador")
    
    # Seletor de tipo de grafico
    tipo = st.radio(
        "Tipo de Metrica:",
        ["Awareness (Views/Alcance)", "Engajamento (Interacoes)", 
         "Eficiencia de Gasto (CPV/CPE)", "Trafego (Cliques/Conversoes)"],
        horizontal=True
    )
    
    st.markdown("---")
    
    # Coletar dados por influenciador
    dados_inf = {}
    
    for camp in campanhas_list:
        for camp_inf in camp['influenciadores']:
            inf = data_manager.get_influenciador(camp_inf['influenciador_id'])
            if not inf:
                continue
            
            nome = inf['nome']
            if nome not in dados_inf:
                dados_inf[nome] = {
                    'views': 0, 'alcance': 0, 'interacoes': 0,
                    'custo': 0, 'cliques': 0, 'conversoes': 0,
                    'seguidores': camp_inf['snapshot_dados'].get('seguidores', inf.get('seguidores', 0))
                }
            
            for post in camp_inf['posts']:
                dados_inf[nome]['views'] += post.get('views', 0)
                dados_inf[nome]['alcance'] += post.get('alcance', 0)
                dados_inf[nome]['interacoes'] += post.get('interacoes', 0)
                dados_inf[nome]['custo'] += post.get('custo', 0)
                dados_inf[nome]['cliques'] += post.get('clique_link', 0)
                dados_inf[nome]['conversoes'] += post.get('cupom_conversoes', 0)
    
    if not dados_inf:
        st.info("Nenhum dado disponivel")
        return
    
    # Limitar a 30 influenciadores
    df = pd.DataFrame([
        {'influenciador': k, **v} for k, v in dados_inf.items()
    ])
    
    # Calcular metricas derivadas
    df['taxa_eng'] = (df['interacoes'] / df['views'] * 100).round(2).fillna(0)
    df['taxa_alcance'] = (df['alcance'] / df['seguidores'] * 100).round(2).fillna(0)
    df['cpv'] = (df['custo'] / df['views']).round(4).fillna(0)
    df['cpe'] = (df['custo'] / df['interacoes']).round(4).fillna(0)
    
    # Ordenar e limitar
    df = df.head(30)
    
    # Criar grafico baseado na selecao
    fig = go.Figure()
    
    if "Awareness" in tipo:
        df = df.sort_values('views', ascending=True)
        
        fig.add_trace(go.Bar(
            x=df['views'],
            y=df['influenciador'],
            orientation='h',
            name='Views',
            marker_color=cores[0],
            text=[funcoes_auxiliares.formatar_numero(v) for v in df['views']],
            textposition='outside'
        ))
        
        fig.add_trace(go.Bar(
            x=df['alcance'],
            y=df['influenciador'],
            orientation='h',
            name='Alcance',
            marker_color=cores[1]
        ))
        
        fig.update_layout(title='Awareness: Views e Alcance por Influenciador', barmode='group')
    
    elif "Engajamento" in tipo:
        df = df.sort_values('taxa_eng', ascending=True)
        
        fig.add_trace(go.Bar(
            x=df['taxa_eng'],
            y=df['influenciador'],
            orientation='h',
            name='Taxa Engajamento %',
            marker_color=cores[2],
            text=[f"{v}%" for v in df['taxa_eng']],
            textposition='outside'
        ))
        
        fig.update_layout(title='Engajamento: Taxa de Engajamento por Influenciador')
    
    elif "Eficiencia" in tipo:
        df = df[df['cpv'] > 0].sort_values('cpv', ascending=False)
        
        fig.add_trace(go.Bar(
            x=df['cpv'],
            y=df['influenciador'],
            orientation='h',
            name='CPV (R$)',
            marker_color=cores[4],
            text=[f"R${v:.4f}" for v in df['cpv']],
            textposition='outside'
        ))
        
        fig.update_layout(title='Eficiencia: Custo por View (CPV)')
    
    else:  # Trafego
        df = df.sort_values('cliques', ascending=True)
        
        fig.add_trace(go.Bar(
            x=df['cliques'],
            y=df['influenciador'],
            orientation='h',
            name='Cliques',
            marker_color=cores[5],
            text=[funcoes_auxiliares.formatar_numero(v) for v in df['cliques']],
            textposition='outside'
        ))
        
        fig.add_trace(go.Bar(
            x=df['conversoes'],
            y=df['influenciador'],
            orientation='h',
            name='Conversoes',
            marker_color=cores[6]
        ))
        
        fig.update_layout(title='Trafego: Cliques e Conversoes por Influenciador', barmode='group')
    
    fig.update_layout(height=max(400, len(df) * 25), showlegend=True)
    st.plotly_chart(fig, use_container_width=True)


# ========================================
# TAB 5: TOP PERFORMANCE
# ========================================

def render_top_performance(campanhas_list, cores):
    """Pagina 5 - Top influenciadores e conteudo"""
    
    st.subheader("Top Performance")
    
    col1, col2 = st.columns(2)
    
    # Coletar dados
    dados_influs = {}
    dados_posts = []
    
    for camp in campanhas_list:
        for camp_inf in camp['influenciadores']:
            inf = data_manager.get_influenciador(camp_inf['influenciador_id'])
            if not inf:
                continue
            
            nome = inf['nome']
            seguidores = camp_inf['snapshot_dados'].get('seguidores', inf.get('seguidores', 1))
            
            if nome not in dados_influs:
                dados_influs[nome] = {
                    'foto': inf.get('foto', ''),
                    'seguidores': seguidores,
                    'views': 0, 'alcance': 0, 'interacoes': 0
                }
            
            for post in camp_inf['posts']:
                views = post.get('views', 0)
                alcance = post.get('alcance', 0)
                interacoes = post.get('interacoes', 0)
                
                dados_influs[nome]['views'] += views
                dados_influs[nome]['alcance'] += alcance
                dados_influs[nome]['interacoes'] += interacoes
                
                taxa_eng = (interacoes / views * 100) if views > 0 else 0
                taxa_alcance = (alcance / seguidores * 100) if seguidores > 0 else 0
                
                dados_posts.append({
                    'influenciador': nome,
                    'formato': post['formato'],
                    'data': post['data_publicacao'],
                    'views': views,
                    'alcance': alcance,
                    'interacoes': interacoes,
                    'taxa_eng': round(taxa_eng, 2),
                    'taxa_alcance': round(taxa_alcance, 2),
                    'link': post.get('link_post', ''),
                    'imagens': post.get('imagens', [])
                })
    
    with col1:
        st.markdown("**Top Influenciadores (Engajamento vs Alcance)**")
        
        # Preparar dados para scatter
        df_inf = pd.DataFrame([
            {
                'nome': k,
                'taxa_eng': (v['interacoes'] / v['views'] * 100) if v['views'] > 0 else 0,
                'taxa_alcance': (v['alcance'] / v['seguidores'] * 100) if v['seguidores'] > 0 else 0,
                'views': v['views']
            }
            for k, v in dados_influs.items()
        ])
        
        if not df_inf.empty:
            fig = px.scatter(
                df_inf,
                x='taxa_alcance',
                y='taxa_eng',
                size='views',
                hover_name='nome',
                color_discrete_sequence=[cores[0]],
                labels={'taxa_alcance': 'Taxa de Alcance (%)', 'taxa_eng': 'Taxa de Engajamento (%)'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Selecao de Metrica para Top Conteudo**")
        
        metrica_top = st.selectbox(
            "Ordenar por:",
            ["Taxa de Engajamento", "Taxa de Alcance", "Views", "Interacoes"],
            key="top_content_metric"
        )
        
        qtd = st.slider("Quantidade:", 5, 20, 10, key="top_content_qty")
    
    st.markdown("---")
    st.subheader("Top Conteudo")
    
    if not dados_posts:
        st.info("Nenhum post cadastrado")
        return
    
    # Ordenar
    ordem_map = {
        "Taxa de Engajamento": "taxa_eng",
        "Taxa de Alcance": "taxa_alcance",
        "Views": "views",
        "Interacoes": "interacoes"
    }
    campo = ordem_map.get(metrica_top, 'views')
    dados_posts.sort(key=lambda x: x[campo], reverse=True)
    
    # Grid de cards
    for idx, post in enumerate(dados_posts[:qtd], 1):
        col1, col2, col3, col4, col5 = st.columns([0.5, 1.2, 2, 1.5, 1.5])
        
        with col1:
            posicao = ['1o', '2o', '3o'] + [f'{i}o' for i in range(4, 21)]
            st.markdown(f"### {posicao[idx-1]}")
        
        with col2:
            if post['imagens']:
                try:
                    img = post['imagens'][0]
                    if img.startswith('http'):
                        st.image(img, width=80)
                    else:
                        st.image(base64.b64decode(img), width=80)
                except:
                    st.write("-")
            else:
                st.write("-")
        
        with col3:
            st.write(f"**{post['influenciador']}**")
            st.caption(f"{post['formato']} | {post['data']}")
            if post['link']:
                st.markdown(f"[Ver Post]({post['link']})")
        
        with col4:
            st.metric("Taxa Eng.", f"{post['taxa_eng']}%")
            st.caption(f"Views: {funcoes_auxiliares.formatar_numero(post['views'])}")
        
        with col5:
            st.metric("Taxa Alcance", f"{post['taxa_alcance']}%")
            st.caption(f"Interacoes: {funcoes_auxiliares.formatar_numero(post['interacoes'])}")
        
        st.markdown("---")


# ========================================
# TAB 6: LISTA INFLUENCIADORES
# ========================================

def render_lista_influenciadores(campanhas_list, cores):
    """Pagina 6 - Lista completa de influenciadores com KPIs"""
    
    st.subheader("Lista de Influenciadores")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filtro_class = st.multiselect("Filtrar por classificacao:", ["Nano", "Micro", "Mid", "Macro", "Mega"])
    with col2:
        ordenar_por = st.selectbox("Ordenar por:", ["Views", "Alcance", "Interacoes", "Taxa Eng."])
    
    st.markdown("---")
    
    # Coletar dados
    dados = []
    
    for camp in campanhas_list:
        for camp_inf in camp['influenciadores']:
            inf = data_manager.get_influenciador(camp_inf['influenciador_id'])
            if not inf:
                continue
            
            classificacao = camp_inf['snapshot_dados'].get('classificacao', inf.get('classificacao', 'Desconhecido'))
            
            if filtro_class and classificacao not in filtro_class:
                continue
            
            seguidores = camp_inf['snapshot_dados'].get('seguidores', inf.get('seguidores', 0))
            
            totais = {'views': 0, 'alcance': 0, 'interacoes': 0, 'impressoes': 0}
            for post in camp_inf['posts']:
                totais['views'] += post.get('views', 0)
                totais['alcance'] += post.get('alcance', 0)
                totais['interacoes'] += post.get('interacoes', 0)
                totais['impressoes'] += post.get('impressoes', 0)
            
            taxa_eng = (totais['interacoes'] / totais['views'] * 100) if totais['views'] > 0 else 0
            taxa_alc = (totais['alcance'] / seguidores * 100) if seguidores > 0 else 0
            
            dados.append({
                'foto': inf.get('foto', ''),
                'nome': inf['nome'],
                'usuario': inf['usuario'],
                'classificacao': classificacao,
                'seguidores': seguidores,
                'posts': len(camp_inf['posts']),
                'views': totais['views'],
                'alcance': totais['alcance'],
                'interacoes': totais['interacoes'],
                'taxa_eng': round(taxa_eng, 2),
                'taxa_alc': round(taxa_alc, 2)
            })
    
    if not dados:
        st.info("Nenhum influenciador encontrado")
        return
    
    # Ordenar
    ordem_map = {"Views": "views", "Alcance": "alcance", "Interacoes": "interacoes", "Taxa Eng.": "taxa_eng"}
    dados.sort(key=lambda x: x[ordem_map.get(ordenar_por, 'views')], reverse=True)
    
    # Exibir
    for d in dados:
        col1, col2, col3, col4, col5, col6, col7 = st.columns([0.8, 2, 1, 1, 1, 1, 1])
        
        with col1:
            if d['foto']:
                st.image(d['foto'], width=50)
        
        with col2:
            st.write(f"**{d['nome']}**")
            st.caption(f"@{d['usuario']}")
        
        with col3:
            st.caption("Classe")
            st.write(d['classificacao'])
        
        with col4:
            st.caption("Posts")
            st.write(d['posts'])
        
        with col5:
            st.caption("Views")
            st.write(funcoes_auxiliares.formatar_numero(d['views']))
        
        with col6:
            st.caption("Taxa Eng.")
            st.write(f"{d['taxa_eng']}%")
        
        with col7:
            st.caption("Taxa Alc.")
            st.write(f"{d['taxa_alc']}%")
        
        st.markdown("---")


# ========================================
# TAB 7: COMENTARIOS
# ========================================

def render_comentarios(campanhas_list, cores):
    """Pagina 7 - Analise de comentarios"""
    
    st.subheader("Analise de Comentarios")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Influenciadores
        todos_influs = ["Todos"]
        for camp in campanhas_list:
            for camp_inf in camp['influenciadores']:
                inf = data_manager.get_influenciador(camp_inf['influenciador_id'])
                if inf and inf['nome'] not in todos_influs:
                    todos_influs.append(inf['nome'])
        filtro_inf = st.selectbox("Influenciador:", todos_influs, key="com_inf")
    
    with col2:
        filtro_polaridade = st.selectbox("Polaridade:", ["Todos", "positivo", "neutro", "negativo"])
    
    with col3:
        if len(campanhas_list) > 1:
            filtro_camp = st.selectbox("Campanha:", ["Todos"] + [c['nome'] for c in campanhas_list])
        else:
            filtro_camp = "Todos"
    
    st.markdown("---")
    
    # Coletar comentarios
    comentarios = []
    
    for camp in campanhas_list:
        if filtro_camp != "Todos" and camp['nome'] != filtro_camp:
            continue
        
        for camp_inf in camp['influenciadores']:
            inf = data_manager.get_influenciador(camp_inf['influenciador_id'])
            if not inf:
                continue
            
            if filtro_inf != "Todos" and inf['nome'] != filtro_inf:
                continue
            
            for post in camp_inf['posts']:
                for com in post.get('comentarios', []):
                    if filtro_polaridade != "Todos" and com['polaridade'] != filtro_polaridade:
                        continue
                    
                    comentarios.append({
                        'campanha': camp['nome'],
                        'influenciador': inf['nome'],
                        'post': f"{post['formato']} - {post['data_publicacao']}",
                        'texto': com['texto'],
                        'polaridade': com['polaridade'],
                        'categoria': com['categoria'],
                        'aderente': com.get('aderente_campanha', False)
                    })
    
    if not comentarios:
        st.info("Nenhum comentario cadastrado")
        return
    
    # Estatisticas
    total = len(comentarios)
    positivos = len([c for c in comentarios if c['polaridade'] == 'positivo'])
    neutros = len([c for c in comentarios if c['polaridade'] == 'neutro'])
    negativos = len([c for c in comentarios if c['polaridade'] == 'negativo'])
    aderentes = len([c for c in comentarios if c['aderente']])
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Positivos", f"{positivos} ({positivos/total*100:.0f}%)")
    with col3:
        st.metric("Neutros", f"{neutros} ({neutros/total*100:.0f}%)")
    with col4:
        st.metric("Negativos", f"{negativos} ({negativos/total*100:.0f}%)")
    with col5:
        st.metric("Aderentes", f"{aderentes} ({aderentes/total*100:.0f}%)")
    
    st.markdown("---")
    
    # Grafico por categoria
    categorias_count = Counter([c['categoria'] for c in comentarios])
    df_cat = pd.DataFrame(categorias_count.items(), columns=['Categoria', 'Quantidade'])
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_cat['Categoria'],
        y=df_cat['Quantidade'],
        marker_color=cores[:len(df_cat)]
    ))
    fig.update_layout(title='Comentarios por Categoria', height=350)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("**Lista de Comentarios**")
    
    for com in comentarios[:30]:
        icon = {"positivo": "[+]", "neutro": "[~]", "negativo": "[-]"}
        aderente = "[ADERENTE]" if com['aderente'] else ""
        
        st.write(f"{icon[com['polaridade']]} **{com['categoria']}** {aderente}")
        st.caption(f"{com['influenciador']} | {com['post']}")
        st.write(com['texto'][:300])
        st.markdown("---")


# ========================================
# TAB 8: NUVEM DE PALAVRAS
# ========================================

def render_nuvem_palavras(campanhas_list, cores):
    """Pagina 8 - Nuvem de palavras e prints de comentarios"""
    
    st.subheader("Nuvem de Palavras e Principais Assuntos")
    
    # Coletar comentarios
    comentarios = []
    for camp in campanhas_list:
        for camp_inf in camp['influenciadores']:
            for post in camp_inf['posts']:
                for com in post.get('comentarios', []):
                    comentarios.append(com)
    
    if not comentarios:
        st.info("Nenhum comentario cadastrado para gerar nuvem de palavras")
        return
    
    # Extrair palavras-chave
    palavras = funcoes_auxiliares.extrair_palavras_chave(comentarios)
    
    if palavras:
        # Exibir como barras (alternativa a nuvem)
        df_palavras = pd.DataFrame(palavras, columns=['Palavra', 'Frequencia'])
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_palavras['Frequencia'][:20],
            y=df_palavras['Palavra'][:20],
            orientation='h',
            marker_color=cores[0]
        ))
        fig.update_layout(
            title='Palavras Mais Frequentes nos Comentarios',
            height=500,
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Principais Assuntos")
    
    # Agrupar por categoria
    categorias = {}
    for com in comentarios:
        cat = com['categoria']
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(com)
    
    for cat, coms in categorias.items():
        with st.expander(f"{cat} ({len(coms)} comentarios)"):
            for c in coms[:5]:
                st.write(f"- {c['texto'][:200]}")
    
    st.markdown("---")
    st.subheader("Print de Comentarios Destacados")
    st.caption("Comentarios positivos e com intencao de compra")
    
    destacados = [c for c in comentarios if c['polaridade'] == 'positivo' or c['categoria'] == 'Intencao de Compra']
    
    for com in destacados[:10]:
        st.markdown(f"""
        <div style="background: #f0fdf4; border-left: 4px solid {cores[2]}; padding: 1rem; margin: 0.5rem 0; border-radius: 0 8px 8px 0;">
            <strong>{com['categoria']}</strong><br>
            "{com['texto'][:250]}"
        </div>
        """, unsafe_allow_html=True)


# ========================================
# TAB 9: GLOSSARIO
# ========================================

def render_glossario():
    """Pagina 9 - Glossario de termos"""
    
    st.subheader("Glossario de Metricas e Termos")
    
    glossario = {
        "Views": "Numero total de visualizacoes do conteudo",
        "Alcance": "Numero de contas unicas que viram o conteudo",
        "Impressoes": "Numero total de vezes que o conteudo foi exibido (inclui repeticoes)",
        "Interacoes": "Soma de curtidas, comentarios, compartilhamentos e saves",
        "Taxa de Engajamento": "(Interacoes / Views) x 100 - Mede o nivel de envolvimento do publico",
        "Taxa de Alcance": "(Alcance / Seguidores) x 100 - Mede a penetracao do conteudo na base",
        "AIR Score": "Score proprietario de performance geral (0-100)",
        "CPV (Custo por View)": "Custo total / Views - Quanto custa cada visualizacao",
        "CPE (Custo por Engajamento)": "Custo total / Interacoes - Quanto custa cada interacao",
        "Saves": "Quantidade de vezes que o conteudo foi salvo pelo usuario",
        "Classificacao de Influenciador": "Nano (<10K), Micro (10K-100K), Mid (100K-500K), Macro (500K-1M), Mega (>1M)",
        "Campanha AON": "Campanha com monitoramento continuo e graficos de evolucao temporal",
        "Campanha Estatica": "Dados congelados no momento da adicao do influenciador",
        "Campanha Dinamica": "Dados atualizados via API periodicamente",
        "Comentario Aderente": "Comentario relacionado ao objetivo da campanha"
    }
    
    for termo, definicao in glossario.items():
        with st.expander(termo):
            st.write(definicao)
