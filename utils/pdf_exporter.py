"""
Modulo: Exportacao de Relatorios em PDF
Gera PDF identico ao relatorio do site com graficos Plotly
"""

import io
import base64
from datetime import datetime
import re
import pandas as pd

# Plotly para graficos
import plotly.express as px
import plotly.graph_objects as go

# WeasyPrint para conversao HTML -> PDF
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

# Kaleido para exportar graficos
try:
    import kaleido
    KALEIDO_AVAILABLE = True
except ImportError:
    KALEIDO_AVAILABLE = False

from utils import data_manager, funcoes_auxiliares


def fig_to_base64(fig, width=700, height=400):
    """Converte figura Plotly para base64 PNG"""
    try:
        img_bytes = fig.to_image(format='png', width=width, height=height, scale=2)
        b64 = base64.b64encode(img_bytes).decode()
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        print(f"Erro ao converter grafico: {e}")
        return None


def gerar_pdf_relatorio(campanha_id: int, incluir_paginas: list = None) -> bytes:
    """
    Gera PDF do relatorio identico ao site
    """
    if not WEASYPRINT_AVAILABLE:
        raise ImportError("WeasyPrint nao instalado")
    
    campanha = data_manager.get_campanha(campanha_id)
    if not campanha:
        raise ValueError("Campanha nao encontrada")
    
    cliente = None
    if campanha.get('cliente_id'):
        cliente = data_manager.get_cliente(campanha['cliente_id'])
    
    metricas = data_manager.calcular_metricas_campanha(campanha)
    primary_color = '#7c3aed'
    
    try:
        cfg = data_manager.get_configuracao('primary_color')
        if cfg:
            primary_color = cfg
    except:
        pass
    
    # Coletar dados
    influenciadores = data_manager.get_influenciadores_campanha(campanha_id)
    todos_posts = []
    dados_influs = []
    
    for inf in influenciadores:
        posts = inf.get('posts', [])
        for post in posts:
            post['influenciador_nome'] = inf.get('nome', '')
            post['classificacao'] = inf.get('classificacao', 'Outro')
            todos_posts.append(post)
        
        # Calcular metricas do influenciador
        imp = sum((p.get('views', 0) or 0) + (p.get('impressoes', 0) or 0) for p in posts)
        inter = sum(p.get('interacoes', 0) or 0 for p in posts)
        alcance = sum(p.get('alcance', 0) or 0 for p in posts)
        
        dados_influs.append({
            'nome': inf.get('nome', ''),
            'usuario': inf.get('usuario', ''),
            'classificacao': inf.get('classificacao', '-'),
            'seguidores': inf.get('seguidores', 0),
            'posts': len(posts),
            'impressoes': imp,
            'alcance': alcance,
            'interacoes': inter,
            'taxa': (inter / imp * 100) if imp > 0 else 0
        })
    
    # Gerar HTML
    html = gerar_html_completo(
        campanha, cliente, metricas, primary_color,
        influenciadores, todos_posts, dados_influs,
        incluir_paginas
    )
    
    # Converter para PDF
    pdf_bytes = HTML(string=html).write_pdf()
    
    return pdf_bytes


def gerar_html_completo(campanha, cliente, metricas, primary_color, 
                        influenciadores, todos_posts, dados_influs, incluir_paginas=None):
    """Gera HTML completo do relatorio"""
    
    paginas_default = ['big_numbers', 'analise_geral', 'kpis_influenciador', 'top_posts', 'lista_influenciadores']
    paginas = incluir_paginas or paginas_default
    
    css = get_css(primary_color)
    
    nome_cliente = cliente['nome'] if cliente else ''
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Relatorio - {campanha['nome']}</title>
        <style>{css}</style>
    </head>
    <body>
        <div class="header">
            <h1>{campanha['nome']}</h1>
            <div class="subtitle">{nome_cliente} | {campanha.get('data_inicio', '')} a {campanha.get('data_fim', '')}</div>
        </div>
    """
    
    if 'big_numbers' in paginas:
        html += gerar_pag_big_numbers(campanha, metricas, primary_color, todos_posts, dados_influs)
    
    if 'analise_geral' in paginas:
        html += gerar_pag_analise(campanha, metricas, primary_color, todos_posts, dados_influs)
    
    if 'kpis_influenciador' in paginas:
        html += gerar_pag_kpis_influenciadores(campanha, primary_color, dados_influs)
    
    if 'top_posts' in paginas:
        html += gerar_pag_top_posts(campanha, primary_color, todos_posts)
    
    if 'lista_influenciadores' in paginas:
        html += gerar_pag_lista_influenciadores(campanha, primary_color, dados_influs)
    
    html += f"""
        <div class="footer">
            Relatorio gerado por <strong>AIR</strong> em {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
    </body>
    </html>
    """
    
    return html


def get_css(primary_color):
    """Retorna CSS do relatorio"""
    return f"""
    @page {{
        size: A4;
        margin: 1.2cm;
    }}
    
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 9pt;
        line-height: 1.4;
        color: #1f2937;
    }}
    
    .header {{
        text-align: center;
        padding: 15px 0;
        border-bottom: 3px solid {primary_color};
        margin-bottom: 20px;
    }}
    
    .header h1 {{
        color: {primary_color};
        font-size: 20pt;
        margin-bottom: 5px;
    }}
    
    .header .subtitle {{
        color: #6b7280;
        font-size: 10pt;
    }}
    
    .page-break {{ page-break-before: always; }}
    
    .section {{
        margin-bottom: 20px;
    }}
    
    .section-title {{
        color: {primary_color};
        font-size: 12pt;
        font-weight: 700;
        border-bottom: 2px solid {primary_color};
        padding-bottom: 5px;
        margin-bottom: 12px;
    }}
    
    .subsection-title {{
        font-size: 10pt;
        font-weight: 600;
        color: #374151;
        margin: 15px 0 8px 0;
    }}
    
    /* Cards de metricas */
    .metrics-grid {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 15px;
    }}
    
    .metric-card {{
        flex: 1;
        min-width: 80px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }}
    
    .metric-card .value {{
        font-size: 14pt;
        font-weight: 700;
        color: {primary_color};
    }}
    
    .metric-card .label {{
        font-size: 7pt;
        color: #64748b;
        text-transform: uppercase;
    }}
    
    .big-metric {{
        background: linear-gradient(135deg, {primary_color}, #a78bfa);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 15px;
    }}
    
    .big-metric .value {{
        font-size: 32pt;
        font-weight: 800;
    }}
    
    .big-metric .label {{
        font-size: 9pt;
        opacity: 0.9;
    }}
    
    /* Graficos */
    .chart-container {{
        text-align: center;
        margin: 10px 0;
    }}
    
    .chart-container img {{
        max-width: 100%;
        height: auto;
    }}
    
    .charts-row {{
        display: flex;
        gap: 15px;
        margin-bottom: 15px;
    }}
    
    .charts-row > div {{
        flex: 1;
    }}
    
    /* Insights */
    .insight-card {{
        background: #f0fdf4;
        border-left: 4px solid #22c55e;
        padding: 10px 12px;
        margin-bottom: 8px;
        border-radius: 0 6px 6px 0;
    }}
    
    .insight-card.alerta {{ background: #fffbeb; border-color: #f59e0b; }}
    .insight-card.destaque {{ background: #eff6ff; border-color: #3b82f6; }}
    .insight-card.info {{ background: #f5f3ff; border-color: {primary_color}; }}
    .insight-card.critico {{ background: #fef2f2; border-color: #ef4444; }}
    
    .insight-title {{ font-weight: 600; font-size: 9pt; margin-bottom: 3px; }}
    .insight-text {{ font-size: 8pt; color: #374151; }}
    
    /* Tabelas */
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 8pt;
        margin-top: 8px;
    }}
    
    th {{
        background: {primary_color};
        color: white;
        padding: 8px 6px;
        text-align: left;
        font-size: 7pt;
        text-transform: uppercase;
    }}
    
    td {{
        padding: 7px 6px;
        border-bottom: 1px solid #e5e7eb;
    }}
    
    tr:nth-child(even) {{ background: #f8fafc; }}
    
    .text-right {{ text-align: right; }}
    .text-center {{ text-align: center; }}
    
    .footer {{
        text-align: center;
        color: #9ca3af;
        font-size: 8pt;
        padding-top: 15px;
        margin-top: 20px;
        border-top: 1px solid #e5e7eb;
    }}
    """


def gerar_pag_big_numbers(campanha, metricas, primary_color, todos_posts, dados_influs):
    """Gera pagina Big Numbers com graficos"""
    
    html = f"""
    <div class="section">
        <div class="section-title">Resumo da Campanha</div>
        
        <div class="big-metric">
            <div class="value">{metricas['engajamento_efetivo']:.2f}%</div>
            <div class="label">TAXA DE ENGAJAMENTO EFETIVO</div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="value">{metricas['total_influenciadores']}</div>
                <div class="label">Influenciadores</div>
            </div>
            <div class="metric-card">
                <div class="value">{metricas['total_posts']}</div>
                <div class="label">Posts</div>
            </div>
            <div class="metric-card">
                <div class="value">{funcoes_auxiliares.formatar_numero(metricas['total_views'] + metricas['total_impressoes'])}</div>
                <div class="label">Impressoes</div>
            </div>
            <div class="metric-card">
                <div class="value">{funcoes_auxiliares.formatar_numero(metricas['total_alcance'])}</div>
                <div class="label">Alcance</div>
            </div>
            <div class="metric-card">
                <div class="value">{funcoes_auxiliares.formatar_numero(metricas['total_interacoes'])}</div>
                <div class="label">Interacoes</div>
            </div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="value">{funcoes_auxiliares.formatar_numero(metricas['total_curtidas'])}</div>
                <div class="label">Curtidas</div>
            </div>
            <div class="metric-card">
                <div class="value">{funcoes_auxiliares.formatar_numero(metricas['total_comentarios'])}</div>
                <div class="label">Comentarios</div>
            </div>
            <div class="metric-card">
                <div class="value">{funcoes_auxiliares.formatar_numero(metricas.get('total_compartilhamentos', 0))}</div>
                <div class="label">Compartilh.</div>
            </div>
            <div class="metric-card">
                <div class="value">{funcoes_auxiliares.formatar_numero(metricas.get('total_saves', 0))}</div>
                <div class="label">Saves</div>
            </div>
            <div class="metric-card">
                <div class="value">{metricas['taxa_alcance']:.1f}%</div>
                <div class="label">Taxa Alcance</div>
            </div>
        </div>
    """
    
    # Graficos
    html += '<div class="subsection-title">Graficos</div>'
    html += '<div class="charts-row">'
    
    # Grafico 1: KPI por Formato (barras empilhadas por classificacao)
    dados_formato = []
    for post in todos_posts:
        formato = post.get('formato', 'Outro')
        classif = post.get('classificacao', 'Outro')
        imp = (post.get('views', 0) or 0) + (post.get('impressoes', 0) or 0)
        dados_formato.append({'Formato': formato, 'Classificacao': classif, 'Impressoes': imp})
    
    if dados_formato:
        df_formato = pd.DataFrame(dados_formato)
        df_agg = df_formato.groupby(['Formato', 'Classificacao'])['Impressoes'].sum().reset_index()
        
        fig1 = px.bar(
            df_agg, x='Formato', y='Impressoes', color='Classificacao',
            title='Impressoes por Formato',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig1.update_layout(
            height=300, margin=dict(t=40, b=40, l=40, r=40),
            legend=dict(orientation='h', y=-0.2),
            font=dict(size=10)
        )
        
        img1 = fig_to_base64(fig1, 350, 300)
        if img1:
            html += f'<div><img src="{img1}" /></div>'
    
    # Grafico 2: Taxa por Formato (linha)
    dados_taxa = []
    for post in todos_posts:
        formato = post.get('formato', 'Outro')
        imp = (post.get('views', 0) or 0) + (post.get('impressoes', 0) or 0)
        inter = post.get('interacoes', 0) or 0
        dados_taxa.append({'Formato': formato, 'Impressoes': imp, 'Interacoes': inter})
    
    if dados_taxa:
        df_taxa = pd.DataFrame(dados_taxa)
        df_taxa_agg = df_taxa.groupby('Formato').agg({'Impressoes': 'sum', 'Interacoes': 'sum'}).reset_index()
        df_taxa_agg['Taxa'] = (df_taxa_agg['Interacoes'] / df_taxa_agg['Impressoes'] * 100).round(2)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=df_taxa_agg['Formato'], y=df_taxa_agg['Impressoes'], name='Impressoes', marker_color=primary_color))
        fig2.add_trace(go.Scatter(x=df_taxa_agg['Formato'], y=df_taxa_agg['Taxa'], name='Taxa Eng.', yaxis='y2', mode='lines+markers', marker_color='#f97316'))
        
        fig2.update_layout(
            title='Performance por Formato',
            yaxis=dict(title='Impressoes'),
            yaxis2=dict(title='Taxa %', overlaying='y', side='right'),
            height=300, margin=dict(t=40, b=40, l=40, r=40),
            legend=dict(orientation='h', y=-0.2),
            font=dict(size=10)
        )
        
        img2 = fig_to_base64(fig2, 350, 300)
        if img2:
            html += f'<div><img src="{img2}" /></div>'
    
    html += '</div>'
    
    # Insights
    insights = data_manager.get_insights_campanha(campanha['id'], 'big_numbers')
    if insights:
        html += '<div class="subsection-title">Insights</div>'
        for insight in insights[:4]:
            tipo = insight.get('tipo', 'info')
            titulo = insight.get('titulo', '')
            texto = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', insight.get('texto', ''))
            html += f'<div class="insight-card {tipo}"><div class="insight-title">{titulo}</div><div class="insight-text">{texto}</div></div>'
    
    html += '</div>'
    return html


def gerar_pag_analise(campanha, metricas, primary_color, todos_posts, dados_influs):
    """Gera pagina de analise com graficos por classificacao"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">Analise por Classificacao</div>
    """
    
    # Agregar por classificacao
    dados_class = {}
    for post in todos_posts:
        classif = post.get('classificacao', 'Outro')
        if classif not in dados_class:
            dados_class[classif] = {'impressoes': 0, 'alcance': 0, 'interacoes': 0, 'posts': 0}
        dados_class[classif]['impressoes'] += (post.get('views', 0) or 0) + (post.get('impressoes', 0) or 0)
        dados_class[classif]['alcance'] += post.get('alcance', 0) or 0
        dados_class[classif]['interacoes'] += post.get('interacoes', 0) or 0
        dados_class[classif]['posts'] += 1
    
    html += '<div class="charts-row">'
    
    # Grafico pizza de impressoes
    if dados_class:
        labels = list(dados_class.keys())
        values = [dados_class[c]['impressoes'] for c in labels]
        
        fig1 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4)])
        fig1.update_layout(title='Impressoes por Classificacao', height=280, margin=dict(t=40, b=20, l=20, r=20), font=dict(size=9))
        
        img1 = fig_to_base64(fig1, 340, 280)
        if img1:
            html += f'<div><img src="{img1}" /></div>'
    
    # Grafico barras de taxa
    if dados_class:
        df_class = pd.DataFrame([
            {'Classificacao': k, 'Taxa': (v['interacoes']/v['impressoes']*100) if v['impressoes'] > 0 else 0}
            for k, v in dados_class.items()
        ])
        df_class = df_class.sort_values('Taxa', ascending=True)
        
        fig2 = px.bar(df_class, x='Taxa', y='Classificacao', orientation='h', title='Taxa de Engajamento')
        fig2.update_traces(marker_color=primary_color)
        fig2.update_layout(height=280, margin=dict(t=40, b=20, l=80, r=20), font=dict(size=9))
        
        img2 = fig_to_base64(fig2, 340, 280)
        if img2:
            html += f'<div><img src="{img2}" /></div>'
    
    html += '</div>'
    
    # Tabela resumo
    html += """
    <div class="subsection-title">Resumo por Classificacao</div>
    <table>
        <tr><th>Classificacao</th><th class="text-right">Posts</th><th class="text-right">Impressoes</th><th class="text-right">Alcance</th><th class="text-right">Interacoes</th><th class="text-right">Taxa Eng.</th></tr>
    """
    
    for classif, dados in sorted(dados_class.items(), key=lambda x: x[1]['impressoes'], reverse=True):
        taxa = (dados['interacoes'] / dados['impressoes'] * 100) if dados['impressoes'] > 0 else 0
        html += f"""
        <tr>
            <td>{classif}</td>
            <td class="text-right">{dados['posts']}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(dados['impressoes'])}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(dados['alcance'])}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(dados['interacoes'])}</td>
            <td class="text-right">{taxa:.2f}%</td>
        </tr>
        """
    
    html += '</table></div>'
    return html


def gerar_pag_kpis_influenciadores(campanha, primary_color, dados_influs):
    """Gera pagina de KPIs por influenciador"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">KPIs por Influenciador</div>
    """
    
    # Top 15 por impressoes
    top15 = sorted(dados_influs, key=lambda x: x['impressoes'], reverse=True)[:15]
    
    if top15:
        df = pd.DataFrame(top15)
        
        # Grafico barras horizontais
        fig = px.bar(df, x='impressoes', y='nome', orientation='h', title='Top 15 Influenciadores')
        fig.update_traces(marker_color=primary_color)
        fig.update_layout(height=400, margin=dict(t=40, b=20, l=120, r=20), yaxis=dict(autorange='reversed'), font=dict(size=9))
        
        img = fig_to_base64(fig, 700, 400)
        if img:
            html += f'<div class="chart-container"><img src="{img}" /></div>'
    
    # Tabela
    html += """
    <table>
        <tr><th>Influenciador</th><th class="text-center">Classe</th><th class="text-right">Seguidores</th><th class="text-center">Posts</th><th class="text-right">Impressoes</th><th class="text-right">Interacoes</th><th class="text-right">Taxa</th></tr>
    """
    
    for d in top15:
        html += f"""
        <tr>
            <td>{d['nome']}</td>
            <td class="text-center">{d['classificacao']}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(d['seguidores'])}</td>
            <td class="text-center">{d['posts']}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(d['impressoes'])}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(d['interacoes'])}</td>
            <td class="text-right">{d['taxa']:.2f}%</td>
        </tr>
        """
    
    html += '</table>'
    
    # Insights
    insights = data_manager.get_insights_campanha(campanha['id'], 'kpis_influenciador')
    if insights:
        html += '<div class="subsection-title">Insights</div>'
        for insight in insights[:3]:
            tipo = insight.get('tipo', 'info')
            titulo = insight.get('titulo', '')
            texto = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', insight.get('texto', ''))
            html += f'<div class="insight-card {tipo}"><div class="insight-title">{titulo}</div><div class="insight-text">{texto}</div></div>'
    
    html += '</div>'
    return html


def gerar_pag_top_posts(campanha, primary_color, todos_posts):
    """Gera pagina de top posts"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">Top Posts</div>
    """
    
    # Ordenar posts
    posts_ordenados = sorted(todos_posts, key=lambda x: (x.get('views', 0) or 0) + (x.get('impressoes', 0) or 0), reverse=True)[:20]
    
    html += """
    <table>
        <tr><th>Influenciador</th><th>Formato</th><th class="text-center">Data</th><th class="text-right">Impressoes</th><th class="text-right">Alcance</th><th class="text-right">Interacoes</th><th class="text-right">Taxa</th></tr>
    """
    
    for post in posts_ordenados:
        imp = (post.get('views', 0) or 0) + (post.get('impressoes', 0) or 0)
        inter = post.get('interacoes', 0) or 0
        taxa = (inter / imp * 100) if imp > 0 else 0
        
        html += f"""
        <tr>
            <td>{post.get('influenciador_nome', '-')}</td>
            <td>{post.get('formato', '-')}</td>
            <td class="text-center">{post.get('data_publicacao', '-')}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(imp)}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(post.get('alcance', 0) or 0)}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(inter)}</td>
            <td class="text-right">{taxa:.2f}%</td>
        </tr>
        """
    
    html += '</table>'
    
    # Insights
    insights = data_manager.get_insights_campanha(campanha['id'], 'top_performance')
    if insights:
        html += '<div class="subsection-title">Insights</div>'
        for insight in insights[:3]:
            tipo = insight.get('tipo', 'info')
            titulo = insight.get('titulo', '')
            texto = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', insight.get('texto', ''))
            html += f'<div class="insight-card {tipo}"><div class="insight-title">{titulo}</div><div class="insight-text">{texto}</div></div>'
    
    html += '</div>'
    return html


def gerar_pag_lista_influenciadores(campanha, primary_color, dados_influs):
    """Gera pagina com lista completa de influenciadores"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">Lista Completa de Influenciadores</div>
        <table>
            <tr><th>Influenciador</th><th>Usuario</th><th class="text-center">Classe</th><th class="text-right">Seguidores</th><th class="text-center">Posts</th><th class="text-right">Impressoes</th><th class="text-right">Alcance</th><th class="text-right">Interacoes</th><th class="text-right">Taxa</th></tr>
    """
    
    for d in sorted(dados_influs, key=lambda x: x['impressoes'], reverse=True):
        html += f"""
        <tr>
            <td>{d['nome']}</td>
            <td>@{d['usuario']}</td>
            <td class="text-center">{d['classificacao']}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(d['seguidores'])}</td>
            <td class="text-center">{d['posts']}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(d['impressoes'])}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(d['alcance'])}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(d['interacoes'])}</td>
            <td class="text-right">{d['taxa']:.2f}%</td>
        </tr>
        """
    
    html += '</table></div>'
    return html
