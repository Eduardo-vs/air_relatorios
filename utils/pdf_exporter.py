"""
PDF Exporter para Relatorios AIR
Gera PDFs extraiveis com todas as informacoes do relatorio web
Inclui graficos como imagens e tabelas divididas em no maximo 6 colunas
"""

import io
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

# WeasyPrint para geracao de PDF
from weasyprint import HTML, CSS

# Plotly para graficos
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from utils import data_manager, funcoes_auxiliares


def calcular_impressoes_post(post: Dict) -> int:
    """Calcula impressoes de um post combinando views e impressoes."""
    views = post.get('views', 0) or 0
    impressoes = post.get('impressoes', 0) or 0
    return views + impressoes


def coletar_dados_influenciadores(campanhas_list: List[Dict]) -> List[Dict]:
    """Coleta dados por influenciador."""
    dados_inf = {}
    
    for camp in campanhas_list:
        for camp_inf in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(camp_inf.get('influenciador_id'))
            if not inf:
                continue
            inf_id = inf['id']
            if inf_id not in dados_inf:
                dados_inf[inf_id] = {
                    'id': inf_id, 
                    'nome': inf['nome'], 
                    'usuario': inf['usuario'], 
                    'foto': inf.get('foto', ''), 
                    'classificacao': inf.get('classificacao', 'Desconhecido'), 
                    'seguidores': inf.get('seguidores', 0), 
                    'network': inf.get('network', 'instagram'),
                    'categoria': inf.get('categoria', ''),
                    'impressoes': 0, 
                    'alcance': 0, 
                    'alcance_total': 0,
                    'interacoes': 0,
                    'curtidas': 0,
                    'custo': 0, 
                    'posts': 0,
                    '_stories_datas': set()
                }
            dados_inf[inf_id]['custo'] += camp_inf.get('custo', 0)
            
            for post in camp_inf.get('posts', []):
                formato = post.get('formato', 'Outro')
                data_post = post.get('data_publicacao', '')
                imp = calcular_impressoes_post(post)
                
                dados_inf[inf_id]['impressoes'] += imp
                post_alcance = post.get('alcance', 0) or 0
                dados_inf[inf_id]['alcance'] = max(dados_inf[inf_id]['alcance'], post_alcance)
                dados_inf[inf_id]['alcance_total'] += post_alcance
                dados_inf[inf_id]['interacoes'] += post.get('interacoes', 0) or 0
                dados_inf[inf_id]['curtidas'] += post.get('curtidas', 0) or 0
                
                if formato == 'Stories':
                    if data_post and data_post not in dados_inf[inf_id]['_stories_datas']:
                        dados_inf[inf_id]['_stories_datas'].add(data_post)
                        dados_inf[inf_id]['posts'] += 1
                    elif not data_post:
                        dados_inf[inf_id]['posts'] += 1
                else:
                    dados_inf[inf_id]['posts'] += 1
    
    resultado = []
    for inf_id, d in dados_inf.items():
        d.pop('_stories_datas', None)
        d['taxa_eng'] = round((d['interacoes'] / d['impressoes'] * 100), 2) if d['impressoes'] > 0 else 0
        d['taxa_alcance'] = round((d['alcance'] / d['seguidores'] * 100), 2) if d['seguidores'] > 0 else 0
        d['interacoes_qualif'] = max(0, d['interacoes'] - d['curtidas'])
        resultado.append(d)
    return resultado


def calcular_metricas_gerais(campanhas_list: List[Dict]) -> Dict:
    """Calcula metricas gerais das campanhas."""
    metricas = {
        'total_influenciadores': 0,
        'total_seguidores': 0,
        'total_posts': 0,
        'total_views': 0,
        'total_impressoes': 0,
        'total_alcance': 0,
        'total_interacoes': 0,
        'total_curtidas': 0,
        'total_comentarios': 0,
        'total_compartilhamentos': 0,
        'total_saves': 0,
        'taxa_alcance': 0,
        'engajamento_efetivo': 0
    }
    
    influenciadores_unicos = set()
    
    for camp in campanhas_list:
        for inf_camp in camp.get('influenciadores', []):
            inf_id = inf_camp.get('influenciador_id')
            if inf_id not in influenciadores_unicos:
                influenciadores_unicos.add(inf_id)
                inf = data_manager.get_influenciador(inf_id)
                if inf:
                    metricas['total_seguidores'] += inf.get('seguidores', 0)
            
            for post in inf_camp.get('posts', []):
                metricas['total_posts'] += 1
                metricas['total_views'] += post.get('views', 0) or 0
                metricas['total_impressoes'] += post.get('impressoes', 0) or 0
                metricas['total_alcance'] += post.get('alcance', 0) or 0
                metricas['total_interacoes'] += post.get('interacoes', 0) or 0
                metricas['total_curtidas'] += post.get('curtidas', 0) or 0
                
                comentarios = post.get('comentarios', 0)
                if isinstance(comentarios, list):
                    metricas['total_comentarios'] += len(comentarios)
                else:
                    metricas['total_comentarios'] += comentarios or 0
                
                metricas['total_compartilhamentos'] += post.get('compartilhamentos', 0) or 0
                metricas['total_saves'] += post.get('saves', 0) or 0
    
    metricas['total_influenciadores'] = len(influenciadores_unicos)
    
    if metricas['total_seguidores'] > 0:
        metricas['taxa_alcance'] = (metricas['total_alcance'] / metricas['total_seguidores'] * 100)
    
    total_imp = metricas['total_impressoes'] + metricas['total_views']
    if total_imp > 0:
        metricas['engajamento_efetivo'] = (metricas['total_interacoes'] / total_imp * 100)
    
    return metricas


def gerar_grafico_barras_formato(campanhas_list: List[Dict], kpi: str = "Impressoes") -> Optional[str]:
    """Gera grafico de barras empilhadas por formato/classificacao e retorna como base64."""
    todos_influs_camp = []
    for camp in campanhas_list:
        for inf_camp in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
            if inf:
                todos_influs_camp.append({'inf': inf, 'posts': inf_camp.get('posts', [])})
    
    dados_grafico = []
    for inf_data in todos_influs_camp:
        inf = inf_data['inf']
        classif = inf.get('classificacao', 'Desconhecido')
        
        for post in inf_data['posts']:
            formato = post.get('formato', post.get('type', 'Outro'))
            if formato:
                formato = formato.capitalize()
            
            valor = 0
            if kpi == "Impressoes":
                valor = calcular_impressoes_post(post)
            elif kpi == "Alcance":
                valor = post.get('alcance', 0) or 0
            elif kpi == "Interacoes":
                valor = post.get('interacoes', 0) or 0
            
            dados_grafico.append({
                'Formato': formato,
                'Classificacao': classif,
                'Valor': valor
            })
    
    if not dados_grafico:
        return None
    
    df = pd.DataFrame(dados_grafico)
    df_agg = df.groupby(['Formato', 'Classificacao'])['Valor'].sum().reset_index()
    
    df_total = df_agg.groupby('Formato')['Valor'].sum().reset_index()
    df_total.columns = ['Formato', 'Total']
    df_agg = df_agg.merge(df_total, on='Formato')
    df_agg['Percentual'] = (df_agg['Valor'] / df_agg['Total'] * 100).round(1)
    
    cores_classif = {
        'Nano': '#22c55e', 'Micro': '#3b82f6', 'Inter 1': '#8b5cf6',
        'Inter 2': '#a855f7', 'Macro': '#f97316', 'Mega 1': '#ef4444',
        'Mega 2': '#dc2626', 'Super Mega': '#991b1b', 'Mid': '#8b5cf6',
        'Mega': '#ef4444', 'Desconhecido': '#9ca3af'
    }
    
    fig = px.bar(
        df_agg, x='Formato', y='Percentual', color='Classificacao',
        color_discrete_map=cores_classif, barmode='stack',
        text=df_agg['Percentual'].apply(lambda x: f"{x:.0f}%")
    )
    fig.update_traces(textposition='inside')
    fig.update_layout(
        height=400, width=600,
        xaxis_title="", yaxis_title=f"{kpi} (%)",
        legend_title="Classificacao",
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    img_bytes = pio.to_image(fig, format='png', scale=2)
    return base64.b64encode(img_bytes).decode('utf-8')


def gerar_grafico_radar_classificacao(campanhas_list: List[Dict]) -> Optional[str]:
    """Gera grafico de radar por classificacao e retorna como base64."""
    todos_influs_camp = []
    classificacoes = set()
    
    for camp in campanhas_list:
        for inf_camp in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
            if inf:
                todos_influs_camp.append({'inf': inf, 'posts': inf_camp.get('posts', [])})
                classificacoes.add(inf.get('classificacao', 'Desconhecido'))
    
    classificacoes = sorted(list(classificacoes)) if classificacoes else ['Desconhecido']
    dados_classif = {c: 0 for c in classificacoes}
    
    for inf_data in todos_influs_camp:
        inf = inf_data['inf']
        classif = inf.get('classificacao', 'Desconhecido')
        for post in inf_data['posts']:
            dados_classif[classif] += post.get('interacoes', 0) or 0
    
    if not any(v > 0 for v in dados_classif.values()):
        return None
    
    categorias = list(dados_classif.keys())
    valores = list(dados_classif.values())
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valores + [valores[0]],
        theta=categorias + [categorias[0]],
        fill='toself',
        fillcolor='rgba(124, 58, 237, 0.3)',
        line=dict(color='#7c3aed', width=2),
        name='Interacoes'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=False,
        height=400, width=500,
        margin=dict(l=60, r=60, t=40, b=40)
    )
    
    img_bytes = pio.to_image(fig, format='png', scale=2)
    return base64.b64encode(img_bytes).decode('utf-8')


def gerar_grafico_barras_influenciadores(campanhas_list: List[Dict], kpi: str = "Impressoes", top_n: int = 15) -> Optional[str]:
    """Gera grafico de barras dos top influenciadores."""
    dados = coletar_dados_influenciadores(campanhas_list)
    if not dados:
        return None
    
    df = pd.DataFrame(dados)
    
    kpi_map = {'Seguidores': 'seguidores', 'Impressoes': 'impressoes', 'Alcance': 'alcance_total', 
               'Interacoes': 'interacoes'}
    campo = kpi_map.get(kpi, 'impressoes')
    
    df = df.sort_values(campo, ascending=False).head(top_n)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['nome'],
        y=df[campo],
        marker_color='#7c3aed',
        text=[funcoes_auxiliares.formatar_numero(v) for v in df[campo]],
        textposition='outside'
    ))
    fig.update_layout(
        height=400, width=800,
        xaxis_title="", yaxis_title=kpi,
        xaxis_tickangle=-45,
        margin=dict(l=40, r=40, t=40, b=100)
    )
    
    img_bytes = pio.to_image(fig, format='png', scale=2)
    return base64.b64encode(img_bytes).decode('utf-8')


def gerar_grafico_linha_taxa(campanhas_list: List[Dict], top_n: int = 15) -> Optional[str]:
    """Gera grafico de linha com taxa de engajamento."""
    dados = coletar_dados_influenciadores(campanhas_list)
    if not dados:
        return None
    
    df = pd.DataFrame(dados)
    df = df.sort_values('impressoes', ascending=False).head(top_n)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['nome'],
        y=df['taxa_eng'],
        mode='lines+markers+text',
        line=dict(color='#fb923c', width=3),
        marker=dict(size=10),
        text=[f"{v:.1f}%" for v in df['taxa_eng']],
        textposition='top center',
        name='Taxa Eng. %'
    ))
    fig.update_layout(
        height=350, width=800,
        xaxis_title="", yaxis_title="Taxa Engajamento (%)",
        xaxis_tickangle=-45,
        margin=dict(l=40, r=40, t=40, b=100)
    )
    
    img_bytes = pio.to_image(fig, format='png', scale=2)
    return base64.b64encode(img_bytes).decode('utf-8')


def gerar_grafico_dispersao(campanhas_list: List[Dict]) -> Optional[str]:
    """Gera grafico de dispersao Engajamento vs Alcance."""
    dados = coletar_dados_influenciadores(campanhas_list)
    if not dados:
        return None
    
    df = pd.DataFrame(dados)
    if df.empty:
        return None
    
    # Cores por classificacao
    cores_classif = {
        'Nano': '#22c55e', 'Micro': '#3b82f6', 'Inter 1': '#8b5cf6',
        'Inter 2': '#a855f7', 'Macro': '#f97316', 'Mega 1': '#ef4444',
        'Mega 2': '#dc2626', 'Super Mega': '#991b1b', 'Mid': '#8b5cf6',
        'Mega': '#ef4444', 'Desconhecido': '#9ca3af'
    }
    
    fig = px.scatter(
        df, 
        x='taxa_alcance', 
        y='taxa_eng', 
        size='impressoes',
        color='classificacao',
        hover_name='nome',
        text='nome',
        labels={'taxa_alcance': 'Taxa de Alcance (%)', 'taxa_eng': 'Taxa de Engajamento (%)'},
        color_discrete_map=cores_classif
    )
    fig.update_traces(textposition='top center', textfont_size=8)
    fig.update_layout(
        height=450, width=700,
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
    )
    
    img_bytes = pio.to_image(fig, format='png', scale=2)
    return base64.b64encode(img_bytes).decode('utf-8')


def gerar_grafico_eficiencia_gasto(campanhas_list: List[Dict], metrica: str = "CPM") -> Optional[str]:
    """Gera grafico de eficiencia de gasto (CPM, CPE, etc)."""
    dados = coletar_dados_influenciadores(campanhas_list)
    if not dados:
        return None
    
    df = pd.DataFrame(dados)
    df = df[df['custo'] > 0].copy()
    
    if df.empty:
        return None
    
    if metrica == "CPM":
        df['valor'] = (df['custo'] / df['impressoes'] * 1000).round(2).fillna(0)
    elif metrica == "CPE":
        df['valor'] = (df['custo'] / df['interacoes']).round(2).fillna(0)
    else:
        df['valor'] = (df['custo'] / df['impressoes']).round(4).fillna(0)
    
    df = df[df['valor'] > 0].sort_values('valor', ascending=True).head(15)
    
    if df.empty:
        return None
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['valor'],
        y=df['nome'],
        orientation='h',
        marker_color='#7c3aed',
        text=[f"R$ {v:.2f}" for v in df['valor']],
        textposition='outside'
    ))
    fig.update_layout(
        height=max(300, len(df) * 30),
        width=600,
        title=f'{metrica} por Influenciador (R$)',
        xaxis_title=f'{metrica} (R$)',
        yaxis_title='',
        margin=dict(l=120, r=60, t=50, b=40)
    )
    
    img_bytes = pio.to_image(fig, format='png', scale=2)
    return base64.b64encode(img_bytes).decode('utf-8')


def gerar_grafico_barras_combo(campanhas_list: List[Dict], kpi_barra: str = "Impressoes", kpi_linha: str = "Taxa Eng. Efetivo", top_n: int = 15) -> Optional[str]:
    """Gera grafico combo barras + linha por influenciador."""
    dados = coletar_dados_influenciadores(campanhas_list)
    if not dados:
        return None
    
    df = pd.DataFrame(dados)
    
    kpi_map = {'Seguidores': 'seguidores', 'Impressoes': 'impressoes', 'Alcance': 'alcance_total', 'Interacoes': 'interacoes'}
    campo_barra = kpi_map.get(kpi_barra, 'impressoes')
    
    df = df.sort_values(campo_barra, ascending=False).head(top_n)
    
    fig = go.Figure()
    
    # Barras
    fig.add_trace(go.Bar(
        x=df['nome'],
        y=df[campo_barra],
        name=kpi_barra,
        marker_color='#7c3aed',
        text=[funcoes_auxiliares.formatar_numero(v) for v in df[campo_barra]],
        textposition='outside'
    ))
    
    # Linha
    if kpi_linha == "Taxa Eng. Efetivo":
        y_linha = df['taxa_eng']
    elif kpi_linha == "Taxa Alcance":
        y_linha = df['taxa_alcance']
    else:
        y_linha = df['taxa_eng']
    
    fig.add_trace(go.Scatter(
        x=df['nome'],
        y=y_linha,
        mode='lines+markers+text',
        name=kpi_linha,
        text=[f"{v:.1f}%" for v in y_linha],
        textposition='top center',
        yaxis='y2',
        line=dict(color='#fb923c', width=2),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        height=450, width=800,
        xaxis=dict(title='', tickangle=-45),
        yaxis=dict(title=kpi_barra),
        yaxis2=dict(title=kpi_linha, overlaying='y', side='right'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        margin=dict(l=60, r=60, t=60, b=120)
    )
    
    img_bytes = pio.to_image(fig, format='png', scale=2)
    return base64.b64encode(img_bytes).decode('utf-8')


def gerar_grafico_formato_kpi(campanhas_list: List[Dict], kpi1: str = "Impressoes", kpi2: str = "Taxa Eng. Efetivo") -> Optional[str]:
    """Gera grafico de barras + linha por formato."""
    todos_posts = []
    todos_influs_camp = []
    
    for camp in campanhas_list:
        for inf_camp in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
            if inf:
                todos_influs_camp.append({'inf': inf, 'posts': inf_camp.get('posts', [])})
    
    dados_formato = {}
    for inf_data in todos_influs_camp:
        for post in inf_data['posts']:
            formato = post.get('formato', 'Outro')
            if formato:
                formato = formato.capitalize()
            if formato not in dados_formato:
                dados_formato[formato] = {'impressoes': 0, 'alcance': 0, 'interacoes': 0, 'curtidas': 0}
            
            dados_formato[formato]['impressoes'] += calcular_impressoes_post(post)
            dados_formato[formato]['alcance'] += post.get('alcance', 0) or 0
            dados_formato[formato]['interacoes'] += post.get('interacoes', 0) or 0
            dados_formato[formato]['curtidas'] += post.get('curtidas', 0) or 0
    
    if not dados_formato:
        return None
    
    df = pd.DataFrame([
        {'formato': k, **v} for k, v in dados_formato.items()
    ])
    
    # Calcular taxas
    df['taxa_eng'] = (df['interacoes'] / df['impressoes'] * 100).round(2).fillna(0)
    
    kpi_map = {'Impressoes': 'impressoes', 'Alcance': 'alcance', 'Interacoes': 'interacoes'}
    campo1 = kpi_map.get(kpi1, 'impressoes')
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['formato'],
        y=df[campo1],
        name=kpi1,
        marker_color='#7c3aed',
        text=[funcoes_auxiliares.formatar_numero(v) for v in df[campo1]],
        textposition='outside'
    ))
    
    if kpi2 == "Taxa Eng. Efetivo":
        y2 = df['taxa_eng']
    else:
        y2 = df['taxa_eng']
    
    fig.add_trace(go.Scatter(
        x=df['formato'],
        y=y2,
        mode='lines+markers',
        name=kpi2,
        yaxis='y2',
        line=dict(color='#fb923c', width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        height=400, width=600,
        yaxis=dict(title=kpi1),
        yaxis2=dict(title=kpi2, overlaying='y', side='right'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        margin=dict(l=60, r=60, t=60, b=40)
    )
    
    img_bytes = pio.to_image(fig, format='png', scale=2)
    return base64.b64encode(img_bytes).decode('utf-8')


def gerar_grafico_classificacao_kpi(campanhas_list: List[Dict], kpi1: str = "Impressoes", kpi2: str = "Taxa Eng. Efetivo") -> Optional[str]:
    """Gera grafico de barras + linha por classificacao."""
    todos_influs_camp = []
    
    for camp in campanhas_list:
        for inf_camp in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
            if inf:
                todos_influs_camp.append({'inf': inf, 'posts': inf_camp.get('posts', [])})
    
    dados_classif = {}
    for inf_data in todos_influs_camp:
        classif = inf_data['inf'].get('classificacao', 'Desconhecido')
        if classif not in dados_classif:
            dados_classif[classif] = {'impressoes': 0, 'alcance': 0, 'interacoes': 0}
        
        for post in inf_data['posts']:
            dados_classif[classif]['impressoes'] += calcular_impressoes_post(post)
            dados_classif[classif]['alcance'] += post.get('alcance', 0) or 0
            dados_classif[classif]['interacoes'] += post.get('interacoes', 0) or 0
    
    if not dados_classif:
        return None
    
    df = pd.DataFrame([
        {'classificacao': k, **v} for k, v in dados_classif.items()
    ])
    
    df['taxa_eng'] = (df['interacoes'] / df['impressoes'] * 100).round(2).fillna(0)
    
    kpi_map = {'Impressoes': 'impressoes', 'Alcance': 'alcance', 'Interacoes': 'interacoes'}
    campo1 = kpi_map.get(kpi1, 'impressoes')
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['classificacao'],
        y=df[campo1],
        name=kpi1,
        marker_color='#7c3aed',
        text=[funcoes_auxiliares.formatar_numero(v) for v in df[campo1]],
        textposition='outside'
    ))
    
    if kpi2 == "Taxa Eng. Efetivo":
        y2 = df['taxa_eng']
    else:
        y2 = df['taxa_eng']
    
    fig.add_trace(go.Scatter(
        x=df['classificacao'],
        y=y2,
        mode='lines+markers',
        name=kpi2,
        yaxis='y2',
        line=dict(color='#fb923c', width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        height=400, width=600,
        yaxis=dict(title=kpi1),
        yaxis2=dict(title=kpi2, overlaying='y', side='right'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        margin=dict(l=60, r=60, t=60, b=40)
    )
    
    img_bytes = pio.to_image(fig, format='png', scale=2)
    return base64.b64encode(img_bytes).decode('utf-8')


def dividir_tabela_html(df: pd.DataFrame, max_cols: int = 6, col_identificadora: str = None) -> List[str]:
    """
    Divide um DataFrame em multiplas tabelas HTML com no maximo max_cols colunas.
    A primeira coluna (col_identificadora) e repetida em todas as tabelas.
    
    Args:
        df: DataFrame a ser dividido
        max_cols: Numero maximo de colunas por tabela (default 6)
        col_identificadora: Nome da coluna a repetir (default: primeira coluna)
    
    Returns:
        Lista de strings HTML com as tabelas
    """
    if col_identificadora is None:
        col_identificadora = df.columns[0]
    
    todas_colunas = list(df.columns)
    outras_colunas = [c for c in todas_colunas if c != col_identificadora]
    
    # Se cabe em uma tabela, retorna direto
    if len(todas_colunas) <= max_cols:
        return [df.to_html(index=False, classes='tabela-dados', border=0)]
    
    # Dividir em grupos de (max_cols - 1) colunas (pois 1 e a identificadora)
    colunas_por_tabela = max_cols - 1
    tabelas_html = []
    
    for i in range(0, len(outras_colunas), colunas_por_tabela):
        colunas_grupo = outras_colunas[i:i + colunas_por_tabela]
        colunas_tabela = [col_identificadora] + colunas_grupo
        df_parte = df[colunas_tabela]
        
        html = df_parte.to_html(index=False, classes='tabela-dados', border=0)
        tabelas_html.append(html)
    
    return tabelas_html


def render_big_numbers_html(campanhas_list: List[Dict], metricas: Dict, config_kpis: Dict) -> str:
    """Renderiza secao Big Numbers como HTML."""
    
    # Estimativas
    estimativa_alcance = 0
    estimativa_impressoes = 0
    if len(campanhas_list) == 1:
        estimativa_alcance = campanhas_list[0].get('estimativa_alcance', 0) or 0
        estimativa_impressoes = campanhas_list[0].get('estimativa_impressoes', 0) or 0
    
    realizado_imp = metricas['total_impressoes'] + metricas['total_views']
    realizado_alc = metricas['total_alcance']
    
    pct_dif_imp = ((realizado_imp - estimativa_impressoes) / estimativa_impressoes * 100) if estimativa_impressoes > 0 else 0
    pct_dif_alc = ((realizado_alc - estimativa_alcance) / estimativa_alcance * 100) if estimativa_alcance > 0 else 0
    
    taxa_eng_total = (metricas['total_interacoes'] / metricas['total_seguidores'] * 100) if metricas['total_seguidores'] > 0 else 0
    
    # AIR Score medio
    todos_influs = []
    for camp in campanhas_list:
        for inf_camp in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
            if inf:
                todos_influs.append(inf)
    
    air_score_medio = sum(i.get('air_score', 0) for i in todos_influs) / len(todos_influs) if todos_influs else 0
    
    # Cards HTML
    def card_html(titulo, valor, cor="#f9fafb"):
        return f'''
        <div class="card" style="background: {cor};">
            <div class="card-titulo">{titulo}</div>
            <div class="card-valor">{valor}</div>
        </div>
        '''
    
    cor_pct_imp = "#dcfce7" if pct_dif_imp >= 0 else "#fee2e2"
    cor_pct_alc = "#dcfce7" if pct_dif_alc >= 0 else "#fee2e2"
    
    html = '''
    <div class="secao">
        <h2>Metricas Principais</h2>
        <div class="cards-grid">
    '''
    
    # Linha 1
    html += card_html("Q. INFLUS", metricas['total_influenciadores'])
    html += card_html("T. SEGUIDORES", funcoes_auxiliares.formatar_numero(metricas['total_seguidores']))
    html += card_html("T. IMPRESSOES", funcoes_auxiliares.formatar_numero(realizado_imp))
    html += card_html("T. ALCANCE", funcoes_auxiliares.formatar_numero(realizado_alc))
    html += card_html("TX. ALCANCE", f"{metricas['taxa_alcance']:.2f}%")
    html += card_html("T. INTERACOES", funcoes_auxiliares.formatar_numero(metricas['total_interacoes']))
    html += card_html("T. LIKES", funcoes_auxiliares.formatar_numero(metricas['total_curtidas']))
    html += card_html("T. SALVOS", funcoes_auxiliares.formatar_numero(metricas['total_saves']))
    
    # Linha 2
    html += card_html("Q. CONTEUDO", metricas['total_posts'])
    html += card_html("TX. ENG. TOTAL", f"{taxa_eng_total:.2f}%")
    html += card_html("EST. IMPR. %", f"{pct_dif_imp:+.1f}%", cor_pct_imp)
    html += card_html("EST. ALC. %", f"{pct_dif_alc:+.1f}%", cor_pct_alc)
    html += card_html("ENGAJ. EFETIVO", f"{metricas['engajamento_efetivo']:.2f}%")
    html += card_html("AIR SCORE", funcoes_auxiliares.formatar_air_score(air_score_medio))
    html += card_html("T. COMENTARIOS", funcoes_auxiliares.formatar_numero(metricas['total_comentarios']))
    html += card_html("T. COMPARTILH.", funcoes_auxiliares.formatar_numero(metricas['total_compartilhamentos']))
    
    html += '</div>'
    
    # Graficos - Linha 1
    kpi_barras = config_kpis.get('big_numbers', {}).get('barras', 'Impressoes')
    kpi_radar = config_kpis.get('big_numbers', {}).get('classificacao', 'Impressoes')
    
    html += '<h3>Graficos</h3><div class="graficos-container">'
    
    img_barras = gerar_grafico_barras_formato(campanhas_list, kpi_barras)
    if img_barras:
        html += f'''
        <div class="grafico">
            <h4>KPI por Formato ({kpi_barras})</h4>
            <img src="data:image/png;base64,{img_barras}" alt="Grafico de Barras"/>
        </div>
        '''
    
    img_radar = gerar_grafico_radar_classificacao(campanhas_list)
    if img_radar:
        html += f'''
        <div class="grafico">
            <h4>Distribuicao por Classificacao</h4>
            <img src="data:image/png;base64,{img_radar}" alt="Grafico Radar"/>
        </div>
        '''
    
    html += '</div>'
    
    # Graficos - Linha 2 (KPI por Formato e Classificacao)
    html += '<div class="graficos-container" style="margin-top: 20px;">'
    
    img_formato = gerar_grafico_formato_kpi(campanhas_list, kpi_barras, "Taxa Eng. Efetivo")
    if img_formato:
        html += f'''
        <div class="grafico">
            <h4>{kpi_barras} por Formato</h4>
            <img src="data:image/png;base64,{img_formato}" alt="Grafico Formato"/>
        </div>
        '''
    
    img_classif = gerar_grafico_classificacao_kpi(campanhas_list, kpi_barras, "Taxa Eng. Efetivo")
    if img_classif:
        html += f'''
        <div class="grafico">
            <h4>{kpi_barras} por Classificacao</h4>
            <img src="data:image/png;base64,{img_classif}" alt="Grafico Classificacao"/>
        </div>
        '''
    
    html += '</div>'
    
    html += '</div>'
    return html


def render_kpis_influenciador_html(campanhas_list: List[Dict], config_kpis: Dict) -> str:
    """Renderiza secao KPIs por Influenciador como HTML."""
    
    dados = coletar_dados_influenciadores(campanhas_list)
    if not dados:
        return '<div class="secao"><h2>KPIs por Influenciador</h2><p>Nenhum dado disponivel</p></div>'
    
    html = '<div class="secao"><h2>KPIs por Influenciador (Top 15)</h2>'
    
    # Graficos
    kpi_barras = config_kpis.get('kpis_influenciador', {}).get('barras', 'Impressoes')
    
    # Grafico 1: Combo Barras + Linha
    img_combo = gerar_grafico_barras_combo(campanhas_list, kpi_barras, "Taxa Eng. Efetivo", 15)
    if img_combo:
        html += f'''
        <div class="grafico-full">
            <h3>Performance Geral - {kpi_barras} + Taxa Engajamento</h3>
            <img src="data:image/png;base64,{img_combo}" alt="Grafico Combo"/>
        </div>
        '''
    
    # Grafico 2: Eficiencia de Gasto (CPM)
    img_cpm = gerar_grafico_eficiencia_gasto(campanhas_list, "CPM")
    if img_cpm:
        html += f'''
        <div class="grafico-full">
            <h3>Eficiencia de Gasto - CPM</h3>
            <img src="data:image/png;base64,{img_cpm}" alt="Grafico CPM"/>
        </div>
        '''
    
    # Grafico antigo de barras (backup)
    img_barras = gerar_grafico_barras_influenciadores(campanhas_list, kpi_barras, 15)
    if img_barras:
        html += f'''
        <div class="grafico-full">
            <h3>Performance por Influenciador - {kpi_barras}</h3>
            <img src="data:image/png;base64,{img_barras}" alt="Grafico de Barras Influenciadores"/>
        </div>
        '''
    
    img_linha = gerar_grafico_linha_taxa(campanhas_list, 15)
    if img_linha:
        html += f'''
        <div class="grafico-full">
            <h3>Taxa de Engajamento por Influenciador</h3>
            <img src="data:image/png;base64,{img_linha}" alt="Grafico de Linha Taxa"/>
        </div>
        '''
    
    # Tabela resumo
    df = pd.DataFrame(dados)
    df = df.sort_values('impressoes', ascending=False).head(15)
    
    df_exibir = df[['nome', 'classificacao', 'seguidores', 'posts', 'impressoes', 'alcance_total', 'interacoes', 'taxa_eng']].copy()
    df_exibir.columns = ['Nome', 'Classe', 'Seguidores', 'Posts', 'Impressoes', 'Alcance', 'Interacoes', 'Tx Eng %']
    
    for col in ['Seguidores', 'Impressoes', 'Alcance', 'Interacoes']:
        df_exibir[col] = df_exibir[col].apply(lambda x: f"{x:,.0f}".replace(",", "."))
    df_exibir['Tx Eng %'] = df_exibir['Tx Eng %'].apply(lambda x: f"{x:.2f}")
    
    html += '<h3>Tabela Resumo</h3>'
    tabelas = dividir_tabela_html(df_exibir, max_cols=6, col_identificadora='Nome')
    for i, tabela in enumerate(tabelas):
        if len(tabelas) > 1:
            html += f'<p class="tabela-parte">Parte {i+1} de {len(tabelas)}</p>'
        html += tabela
    
    html += '</div>'
    return html


def render_top_performance_html(campanhas_list: List[Dict], config_kpis: Dict) -> str:
    """Renderiza secao Top Performance como HTML."""
    
    # Coletar top 3 conteudos
    top_conteudos = {}
    if len(campanhas_list) == 1:
        top_conteudos = campanhas_list[0].get('top_conteudos', {}) or {}
    
    html = '<div class="secao"><h2>Top Performance</h2>'
    
    # Top 3 destacados (novo formato com campos individuais)
    tem_tops = any(top_conteudos.get(f'top{i}_post_id') for i in range(1, 4))
    
    if tem_tops:
        html += '<h3>Top 3 Conteudos Destacados</h3><div class="top3-container">'
        
        for i in range(1, 4):
            post_id = top_conteudos.get(f'top{i}_post_id')
            if post_id:
                usuario = top_conteudos.get(f'top{i}_usuario', '')
                formato = top_conteudos.get(f'top{i}_formato', 'Post')
                curtidas = top_conteudos.get(f'top{i}_curtidas', 0) or 0
                comentarios = top_conteudos.get(f'top{i}_comentarios', 0) or 0
                interacoes = top_conteudos.get(f'top{i}_interacoes', 0) or 0
                descricao = top_conteudos.get(f'top{i}_descricao', '')
                
                desc_curta = descricao[:60] + '...' if len(descricao) > 60 else descricao
                
                html += f'''
                <div class="top-card">
                    <div class="top-posicao">#{i}</div>
                    <div class="top-info">
                        <strong>@{usuario}</strong><br/>
                        <span class="top-formato">{formato}</span><br/>
                        <span>Curtidas: {funcoes_auxiliares.formatar_numero(curtidas)}</span><br/>
                        <span>Coment.: {funcoes_auxiliares.formatar_numero(comentarios)}</span><br/>
                        <span>Interacoes: {funcoes_auxiliares.formatar_numero(interacoes)}</span>
                    </div>
                </div>
                '''
        
        html += '</div>'
    
    # Grafico de Dispersao
    img_dispersao = gerar_grafico_dispersao(campanhas_list)
    if img_dispersao:
        html += f'''
        <div class="grafico-full" style="margin-top: 20px;">
            <h3>Dispersao: Engajamento vs Alcance</h3>
            <img src="data:image/png;base64,{img_dispersao}" alt="Grafico de Dispersao"/>
        </div>
        '''
    
    # Lista de top posts
    todos_posts = []
    for camp in campanhas_list:
        for inf_camp in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
            for post in inf_camp.get('posts', []):
                post_data = post.copy()
                post_data['influenciador_nome'] = inf['nome'] if inf else 'Desconhecido'
                post_data['impressoes_total'] = calcular_impressoes_post(post)
                todos_posts.append(post_data)
    
    if todos_posts:
        ordenar_por = config_kpis.get('top_performance', {}).get('ordenar_posts', 'Impressoes')
        campo_ord = 'impressoes_total' if ordenar_por == 'Impressoes' else 'interacoes'
        
        df = pd.DataFrame(todos_posts)
        df = df.sort_values(campo_ord, ascending=False).head(20)
        
        df_exibir = df[['influenciador_nome', 'formato', 'impressoes_total', 'alcance', 'interacoes', 'curtidas', 'data_publicacao']].copy()
        df_exibir.columns = ['Influenciador', 'Formato', 'Impressoes', 'Alcance', 'Interacoes', 'Curtidas', 'Data']
        
        for col in ['Impressoes', 'Alcance', 'Interacoes', 'Curtidas']:
            df_exibir[col] = df_exibir[col].apply(lambda x: f"{x:,.0f}".replace(",", ".") if pd.notna(x) else "0")
        
        html += '<h3>Lista de Top Performance</h3>'
        tabelas = dividir_tabela_html(df_exibir, max_cols=6, col_identificadora='Influenciador')
        for i, tabela in enumerate(tabelas):
            if len(tabelas) > 1:
                html += f'<p class="tabela-parte">Parte {i+1} de {len(tabelas)}</p>'
            html += tabela
    
    html += '</div>'
    return html


def render_lista_influenciadores_html(campanhas_list: List[Dict]) -> str:
    """Renderiza secao Lista de Influenciadores como HTML."""
    
    dados = coletar_dados_influenciadores(campanhas_list)
    if not dados:
        return '<div class="secao"><h2>Lista de Influenciadores</h2><p>Nenhum influenciador</p></div>'
    
    df = pd.DataFrame(dados)
    df = df.sort_values('impressoes', ascending=False)
    
    # Verificar colunas personalizadas
    dados_custom = {}
    col_custom1_nome = None
    col_custom2_nome = None
    tem_dados_custom = False
    
    for camp in campanhas_list:
        config_cols = camp.get('colunas_personalizadas', {})
        if config_cols.get('col1_nome'):
            col_custom1_nome = config_cols['col1_nome']
        if config_cols.get('col2_nome'):
            col_custom2_nome = config_cols['col2_nome']
        
        for inf_camp in camp.get('influenciadores', []):
            inf_id = inf_camp.get('influenciador_id')
            col1_val = inf_camp.get('dado_custom1', '')
            col2_val = inf_camp.get('dado_custom2', '')
            
            if col1_val or col2_val:
                tem_dados_custom = True
            
            dados_custom[inf_id] = {'col1': col1_val, 'col2': col2_val}
    
    # Montar colunas
    colunas_base = ['nome', 'usuario', 'classificacao', 'seguidores', 'posts', 'impressoes', 'alcance_total', 'interacoes', 'custo', 'taxa_eng']
    nomes_base = ['Nome', 'Usuario', 'Classe', 'Seguidores', 'Posts', 'Impressoes', 'Alcance', 'Interacoes', 'Invest.', 'Tx Eng %']
    
    if tem_dados_custom:
        df['col_custom1'] = df['id'].apply(lambda x: dados_custom.get(x, {}).get('col1', ''))
        df['col_custom2'] = df['id'].apply(lambda x: dados_custom.get(x, {}).get('col2', ''))
        
        if col_custom1_nome:
            colunas_base.append('col_custom1')
            nomes_base.append(col_custom1_nome)
        if col_custom2_nome:
            colunas_base.append('col_custom2')
            nomes_base.append(col_custom2_nome)
    
    df_exibir = df[colunas_base].copy()
    df_exibir.columns = nomes_base
    
    for col in ['Seguidores', 'Impressoes', 'Alcance', 'Interacoes', 'Invest.']:
        if col in df_exibir.columns:
            df_exibir[col] = df_exibir[col].apply(lambda x: f"{x:,.0f}".replace(",", "."))
    if 'Tx Eng %' in df_exibir.columns:
        df_exibir['Tx Eng %'] = df_exibir['Tx Eng %'].apply(lambda x: f"{x:.2f}")
    
    html = '<div class="secao"><h2>Lista de Influenciadores</h2>'
    
    tabelas = dividir_tabela_html(df_exibir, max_cols=6, col_identificadora='Nome')
    for i, tabela in enumerate(tabelas):
        if len(tabelas) > 1:
            html += f'<p class="tabela-parte">Parte {i+1} de {len(tabelas)}</p>'
        html += tabela
    
    html += '</div>'
    return html


def render_stories_detalhado_html(campanhas_list: List[Dict]) -> str:
    """Renderiza secao de Stories Detalhado como HTML."""
    
    # Coletar todos os stories
    stories_data = []
    
    for camp in campanhas_list:
        for inf_camp in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
            nome_inf = inf['nome'] if inf else 'Desconhecido'
            
            for post in inf_camp.get('posts', []):
                if post.get('formato', '').lower() == 'stories':
                    stories_data.append({
                        'influenciador': nome_inf,
                        'data': post.get('data_publicacao', ''),
                        'views': post.get('views', 0) or 0,
                        'alcance': post.get('alcance', 0) or 0,
                        'impressoes': calcular_impressoes_post(post),
                        'interacoes': post.get('interacoes', 0) or 0,
                        'clique_link': post.get('clique_link', 0) or 0,
                        'respostas': post.get('respostas', 0) or 0,
                        'compartilhamentos': post.get('compartilhamentos', 0) or 0
                    })
    
    if not stories_data:
        return '<div class="secao"><h2>Stories Detalhado</h2><p>Nenhum story encontrado</p></div>'
    
    html = '<div class="secao"><h2>Stories Detalhado</h2>'
    html += f'<p>Total de stories: {len(stories_data)}</p>'
    
    # Agrupar por influenciador
    df = pd.DataFrame(stories_data)
    
    # Resumo por influenciador
    df_resumo = df.groupby('influenciador').agg({
        'views': 'sum',
        'alcance': 'max',
        'impressoes': 'sum',
        'interacoes': 'sum',
        'clique_link': 'sum',
        'data': 'count'
    }).reset_index()
    df_resumo.columns = ['Influenciador', 'Views', 'Alcance', 'Impressoes', 'Interacoes', 'Cliques Link', 'Qtd Stories']
    df_resumo = df_resumo.sort_values('Impressoes', ascending=False)
    
    # Formatar numeros
    for col in ['Views', 'Alcance', 'Impressoes', 'Interacoes', 'Cliques Link']:
        df_resumo[col] = df_resumo[col].apply(lambda x: f"{x:,.0f}".replace(",", "."))
    
    html += '<h3>Resumo por Influenciador</h3>'
    tabelas = dividir_tabela_html(df_resumo, max_cols=6, col_identificadora='Influenciador')
    for i, tabela in enumerate(tabelas):
        if len(tabelas) > 1:
            html += f'<p class="tabela-parte">Parte {i+1} de {len(tabelas)}</p>'
        html += tabela
    
    # Tabela detalhada (top 50)
    df_det = df.sort_values('impressoes', ascending=False).head(50)
    df_det_exibir = df_det[['influenciador', 'data', 'views', 'alcance', 'interacoes', 'clique_link']].copy()
    df_det_exibir.columns = ['Influenciador', 'Data', 'Views', 'Alcance', 'Interacoes', 'Cliques']
    
    for col in ['Views', 'Alcance', 'Interacoes', 'Cliques']:
        df_det_exibir[col] = df_det_exibir[col].apply(lambda x: f"{x:,.0f}".replace(",", "."))
    
    html += '<h3>Stories Individuais (Top 50)</h3>'
    tabelas = dividir_tabela_html(df_det_exibir, max_cols=6, col_identificadora='Influenciador')
    for i, tabela in enumerate(tabelas):
        if len(tabelas) > 1:
            html += f'<p class="tabela-parte">Parte {i+1} de {len(tabelas)}</p>'
        html += tabela
    
    html += '</div>'
    return html


def render_comentarios_html(campanhas_list: List[Dict]) -> str:
    """Renderiza secao de comentarios como HTML."""
    
    todos_comentarios = []
    for camp in campanhas_list:
        for inf_camp in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
            nome_inf = inf['nome'] if inf else 'Desconhecido'
            
            for post in inf_camp.get('posts', []):
                comentarios = post.get('comentarios', [])
                if isinstance(comentarios, list):
                    for com in comentarios:
                        if isinstance(com, dict):
                            todos_comentarios.append({
                                'influenciador': nome_inf,
                                'autor': com.get('autor', com.get('usuario', 'Anonimo')),
                                'texto': com.get('texto', com.get('comentario', '')),
                                'data': com.get('data', '')
                            })
    
    if not todos_comentarios:
        return '<div class="secao"><h2>Comentarios</h2><p>Nenhum comentario extraido</p></div>'
    
    html = '<div class="secao"><h2>Comentarios</h2>'
    html += f'<p>Total de comentarios: {len(todos_comentarios)}</p>'
    
    # Mostrar ate 100 comentarios
    for com in todos_comentarios[:100]:
        html += f'''
        <div class="comentario">
            <div class="com-header">
                <strong>{com['autor']}</strong> em post de <em>{com['influenciador']}</em>
            </div>
            <div class="com-texto">{com['texto']}</div>
        </div>
        '''
    
    if len(todos_comentarios) > 100:
        html += f'<p class="aviso">... e mais {len(todos_comentarios) - 100} comentarios</p>'
    
    html += '</div>'
    return html


def render_glossario_html() -> str:
    """Renderiza glossario como HTML."""
    
    termos = [
        ("Impressoes", "Numero total de vezes que o conteudo foi exibido (views + impressoes)"),
        ("Alcance", "Numero de contas unicas que viram o conteudo"),
        ("Interacoes", "Soma de curtidas, comentarios, compartilhamentos e salvamentos"),
        ("Taxa de Engajamento", "Porcentagem de interacoes em relacao as impressoes"),
        ("Taxa de Alcance", "Porcentagem de alcance em relacao aos seguidores"),
        ("Engajamento Efetivo", "Taxa de interacoes sobre impressoes totais"),
        ("AIR Score", "Indice de performance do influenciador calculado pelo AIR"),
        ("Interacoes Qualificadas", "Interacoes excluindo curtidas (comentarios + compartilhamentos + salvamentos)"),
        ("Classificacao", "Categoria do influenciador por numero de seguidores (Nano, Micro, Mid, Macro, Mega)")
    ]
    
    html = '<div class="secao"><h2>Glossario</h2><div class="glossario">'
    
    for termo, definicao in termos:
        html += f'''
        <div class="termo">
            <strong>{termo}:</strong> {definicao}
        </div>
        '''
    
    html += '</div></div>'
    return html


def gerar_pdf_relatorio(campanha_id: int, paginas: List[str], config_kpis: Dict) -> bytes:
    """
    Gera PDF do relatorio.
    
    Args:
        campanha_id: ID da campanha
        paginas: Lista de paginas a incluir ['big_numbers', 'kpis_influenciador', 'top_performance', 
                 'lista_influenciadores', 'comentarios', 'glossario']
        config_kpis: Configuracoes de KPIs para graficos
    
    Returns:
        bytes do PDF gerado
    """
    
    # Carregar campanha
    campanha = data_manager.get_campanha(campanha_id)
    if not campanha:
        raise ValueError("Campanha nao encontrada")
    
    campanhas_list = [campanha]
    metricas = calcular_metricas_gerais(campanhas_list)
    
    # CSS do documento
    css = '''
    @page {
        size: A4;
        margin: 1.5cm;
    }
    
    body {
        font-family: Arial, Helvetica, sans-serif;
        font-size: 10pt;
        line-height: 1.4;
        color: #1f2937;
    }
    
    .header {
        text-align: center;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 2px solid #7c3aed;
    }
    
    .header h1 {
        color: #7c3aed;
        margin: 0;
        font-size: 18pt;
    }
    
    .header .subtitle {
        color: #6b7280;
        font-size: 10pt;
        margin-top: 5px;
    }
    
    .secao {
        margin-bottom: 25px;
        page-break-inside: avoid;
    }
    
    .secao h2 {
        color: #7c3aed;
        font-size: 14pt;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 5px;
        margin-bottom: 15px;
    }
    
    .secao h3 {
        color: #374151;
        font-size: 11pt;
        margin: 15px 0 10px 0;
    }
    
    .cards-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        margin-bottom: 15px;
    }
    
    .card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 8px;
        text-align: center;
    }
    
    .card-titulo {
        font-size: 7pt;
        color: #6b7280;
        margin-bottom: 3px;
    }
    
    .card-valor {
        font-size: 11pt;
        font-weight: bold;
        color: #1f2937;
    }
    
    .graficos-container {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        justify-content: center;
    }
    
    .grafico, .grafico-full {
        text-align: center;
        margin: 10px 0;
    }
    
    .grafico img {
        max-width: 280px;
        height: auto;
    }
    
    .grafico-full img {
        max-width: 100%;
        height: auto;
    }
    
    .grafico h4, .grafico-full h3 {
        font-size: 9pt;
        color: #374151;
        margin-bottom: 8px;
    }
    
    .tabela-dados {
        width: 100%;
        border-collapse: collapse;
        font-size: 8pt;
        margin: 10px 0;
    }
    
    .tabela-dados th {
        background: #7c3aed;
        color: white;
        padding: 6px 4px;
        text-align: left;
        font-weight: bold;
    }
    
    .tabela-dados td {
        padding: 5px 4px;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .tabela-dados tr:nth-child(even) {
        background: #f9fafb;
    }
    
    .tabela-parte {
        font-size: 8pt;
        color: #6b7280;
        font-style: italic;
        margin: 10px 0 5px 0;
    }
    
    .top3-container {
        display: flex;
        gap: 15px;
        justify-content: center;
        margin: 15px 0;
    }
    
    .top-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 12px;
        width: 150px;
        text-align: center;
    }
    
    .top-posicao {
        font-size: 18pt;
        font-weight: bold;
        color: #7c3aed;
    }
    
    .top-info {
        font-size: 8pt;
        margin-top: 8px;
    }
    
    .top-formato {
        background: #e5e7eb;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 7pt;
    }
    
    .comentario {
        background: #f9fafb;
        border-left: 3px solid #7c3aed;
        padding: 8px 12px;
        margin: 8px 0;
        font-size: 8pt;
    }
    
    .com-header {
        color: #6b7280;
        margin-bottom: 4px;
    }
    
    .com-texto {
        color: #1f2937;
    }
    
    .glossario .termo {
        padding: 6px 0;
        border-bottom: 1px solid #e5e7eb;
        font-size: 9pt;
    }
    
    .aviso {
        color: #6b7280;
        font-style: italic;
        font-size: 8pt;
    }
    '''
    
    # Montar HTML
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Relatorio {campanha['nome']}</title>
    </head>
    <body>
        <div class="header">
            <h1>{campanha['nome']}</h1>
            <div class="subtitle">
                Cliente: {campanha.get('cliente_nome', 'N/A')} | 
                Periodo: {campanha.get('data_inicio', '')} a {campanha.get('data_fim', '')} |
                Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </div>
        </div>
    '''
    
    # Adicionar paginas selecionadas
    if 'big_numbers' in paginas:
        html += render_big_numbers_html(campanhas_list, metricas, config_kpis)
    
    if 'kpis_influenciador' in paginas:
        html += render_kpis_influenciador_html(campanhas_list, config_kpis)
    
    if 'top_performance' in paginas:
        html += render_top_performance_html(campanhas_list, config_kpis)
    
    if 'lista_influenciadores' in paginas:
        html += render_lista_influenciadores_html(campanhas_list)
    
    if 'stories_detalhado' in paginas:
        html += render_stories_detalhado_html(campanhas_list)
    
    if 'comentarios' in paginas:
        html += render_comentarios_html(campanhas_list)
    
    if 'glossario' in paginas:
        html += render_glossario_html()
    
    html += '''
    </body>
    </html>
    '''
    
    # Gerar PDF
    pdf_bytes = HTML(string=html).write_pdf(stylesheets=[CSS(string=css)])
    
    return pdf_bytes
