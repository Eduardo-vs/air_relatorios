"""
Modulo: Exportacao de Relatorios em PDF
Gera PDF identico ao relatorio do site com graficos CSS
"""

import io
import base64
from datetime import datetime
import re
import pandas as pd
import json

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from utils import data_manager, funcoes_auxiliares


def gerar_pdf_relatorio(campanha_id: int, incluir_paginas: list = None) -> bytes:
    """Gera PDF completo do relatorio"""
    
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
    
    # Coletar todos os dados
    influenciadores = data_manager.get_influenciadores_campanha(campanha_id)
    
    todos_posts = []
    dados_por_influ = []
    dados_por_formato = {}
    dados_por_classif = {}
    
    for inf_camp in influenciadores:
        inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
        if not inf:
            continue
        
        posts = inf_camp.get('posts', [])
        classif = inf.get('classificacao', 'Outro')
        
        inf_impressoes = 0
        inf_alcance = 0
        inf_interacoes = 0
        inf_curtidas = 0
        inf_comentarios = 0
        inf_saves = 0
        inf_compartilhamentos = 0
        
        for post in posts:
            imp = (post.get('views', 0) or 0) + (post.get('impressoes', 0) or 0)
            alc = post.get('alcance', 0) or 0
            inter = post.get('interacoes', 0) or 0
            curt = post.get('curtidas', 0) or 0
            
            coments = post.get('comentarios', 0)
            if isinstance(coments, list):
                coments = len(coments)
            coments = coments or 0
            
            saves = post.get('saves', 0) or 0
            compart = post.get('compartilhamentos', 0) or 0
            
            formato = post.get('formato', 'Outro')
            
            # Agregar por formato
            if formato not in dados_por_formato:
                dados_por_formato[formato] = {'impressoes': 0, 'alcance': 0, 'interacoes': 0, 'posts': 0}
            dados_por_formato[formato]['impressoes'] += imp
            dados_por_formato[formato]['alcance'] += alc
            dados_por_formato[formato]['interacoes'] += inter
            dados_por_formato[formato]['posts'] += 1
            
            # Agregar por classificacao
            if classif not in dados_por_classif:
                dados_por_classif[classif] = {'impressoes': 0, 'alcance': 0, 'interacoes': 0, 'posts': 0, 'influenciadores': set()}
            dados_por_classif[classif]['impressoes'] += imp
            dados_por_classif[classif]['alcance'] += alc
            dados_por_classif[classif]['interacoes'] += inter
            dados_por_classif[classif]['posts'] += 1
            dados_por_classif[classif]['influenciadores'].add(inf['id'])
            
            # Totais do influenciador
            inf_impressoes += imp
            inf_alcance += alc
            inf_interacoes += inter
            inf_curtidas += curt
            inf_comentarios += coments
            inf_saves += saves
            inf_compartilhamentos += compart
            
            # Posts para tabela
            todos_posts.append({
                'influenciador': inf.get('nome', ''),
                'usuario': inf.get('usuario', ''),
                'formato': formato,
                'data': post.get('data_publicacao', ''),
                'impressoes': imp,
                'alcance': alc,
                'interacoes': inter,
                'curtidas': curt,
                'comentarios': coments,
                'saves': saves,
                'compartilhamentos': compart,
                'taxa': (inter / imp * 100) if imp > 0 else 0
            })
        
        # Dados do influenciador
        dados_por_influ.append({
            'nome': inf.get('nome', ''),
            'usuario': inf.get('usuario', ''),
            'classificacao': classif,
            'seguidores': inf.get('seguidores', 0) or 0,
            'posts': len(posts),
            'impressoes': inf_impressoes,
            'alcance': inf_alcance,
            'interacoes': inf_interacoes,
            'curtidas': inf_curtidas,
            'comentarios': inf_comentarios,
            'saves': inf_saves,
            'compartilhamentos': inf_compartilhamentos,
            'taxa': (inf_interacoes / inf_impressoes * 100) if inf_impressoes > 0 else 0
        })
    
    # Gerar HTML
    html = gerar_html_completo(
        campanha=campanha,
        cliente=cliente,
        metricas=metricas,
        primary_color=primary_color,
        todos_posts=todos_posts,
        dados_por_influ=dados_por_influ,
        dados_por_formato=dados_por_formato,
        dados_por_classif=dados_por_classif,
        incluir_paginas=incluir_paginas
    )
    
    # Converter para PDF
    pdf_bytes = HTML(string=html).write_pdf()
    
    return pdf_bytes


def gerar_html_completo(campanha, cliente, metricas, primary_color, 
                        todos_posts, dados_por_influ, dados_por_formato, 
                        dados_por_classif, incluir_paginas=None):
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
    
    # Pagina 1: Big Numbers
    if 'big_numbers' in paginas:
        html += gerar_pag_big_numbers(campanha, metricas, primary_color, dados_por_formato, dados_por_classif)
    
    # Pagina 2: Analise por Classificacao
    if 'analise_geral' in paginas:
        html += gerar_pag_analise(campanha, primary_color, dados_por_formato, dados_por_classif)
    
    # Pagina 3: KPIs por Influenciador
    if 'kpis_influenciador' in paginas:
        html += gerar_pag_kpis_influenciadores(campanha, primary_color, dados_por_influ)
    
    # Pagina 4: Top Posts
    if 'top_posts' in paginas:
        html += gerar_pag_top_posts(campanha, primary_color, todos_posts)
    
    # Pagina 5: Lista de Influenciadores
    if 'lista_influenciadores' in paginas:
        html += gerar_pag_lista_influenciadores(campanha, primary_color, dados_por_influ)
    
    # Footer
    html += f"""
        <div class="footer">
            Relatorio gerado por <strong>AIR</strong> em {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
    </body>
    </html>
    """
    
    return html


def get_css(primary_color):
    """Retorna CSS completo do relatorio"""
    return f"""
    @page {{
        size: A4;
        margin: 1cm;
    }}
    
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 9pt;
        line-height: 1.4;
        color: #1f2937;
        background: #fff;
    }}
    
    .header {{
        text-align: center;
        padding: 20px 0;
        border-bottom: 4px solid {primary_color};
        margin-bottom: 20px;
    }}
    
    .header h1 {{
        color: {primary_color};
        font-size: 24pt;
        margin-bottom: 5px;
    }}
    
    .header .subtitle {{
        color: #6b7280;
        font-size: 11pt;
    }}
    
    .page-break {{ page-break-before: always; padding-top: 15px; }}
    
    .section {{
        margin-bottom: 25px;
    }}
    
    .section-title {{
        color: {primary_color};
        font-size: 14pt;
        font-weight: 700;
        border-bottom: 2px solid {primary_color};
        padding-bottom: 8px;
        margin-bottom: 15px;
    }}
    
    .subsection-title {{
        font-size: 11pt;
        font-weight: 600;
        color: #374151;
        margin: 20px 0 10px 0;
    }}
    
    /* Big Number Principal */
    .big-number-card {{
        background: linear-gradient(135deg, {primary_color} 0%, #a78bfa 100%);
        color: white;
        padding: 30px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 20px;
    }}
    
    .big-number-card .value {{
        font-size: 48pt;
        font-weight: 800;
        line-height: 1;
    }}
    
    .big-number-card .label {{
        font-size: 10pt;
        opacity: 0.9;
        text-transform: uppercase;
        margin-top: 5px;
    }}
    
    /* Grid de Metricas */
    .metrics-grid {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 20px;
    }}
    
    .metric-card {{
        flex: 1;
        min-width: 90px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
    }}
    
    .metric-card .value {{
        font-size: 16pt;
        font-weight: 700;
        color: {primary_color};
    }}
    
    .metric-card .label {{
        font-size: 7pt;
        color: #64748b;
        text-transform: uppercase;
        margin-top: 3px;
    }}
    
    /* Graficos CSS */
    .charts-container {{
        display: flex;
        gap: 20px;
        margin-bottom: 20px;
    }}
    
    .chart-box {{
        flex: 1;
        background: #f8fafc;
        border-radius: 10px;
        padding: 15px;
    }}
    
    .chart-title {{
        font-size: 9pt;
        font-weight: 600;
        color: #374151;
        margin-bottom: 12px;
        text-align: center;
    }}
    
    /* Barras Horizontais CSS */
    .bar-chart {{
        margin: 10px 0;
    }}
    
    .bar-row {{
        display: flex;
        align-items: center;
        margin-bottom: 8px;
    }}
    
    .bar-label {{
        width: 80px;
        font-size: 8pt;
        color: #374151;
        text-align: right;
        padding-right: 10px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    
    .bar-container {{
        flex: 1;
        background: #e5e7eb;
        border-radius: 4px;
        height: 22px;
        overflow: hidden;
    }}
    
    .bar-fill {{
        height: 100%;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 8px;
        min-width: 40px;
    }}
    
    .bar-value {{
        font-size: 8pt;
        font-weight: 600;
        color: white;
    }}
    
    /* Barras Verticais CSS */
    .vertical-bars {{
        display: flex;
        justify-content: space-around;
        align-items: flex-end;
        height: 150px;
        padding: 10px 0;
        border-bottom: 1px solid #e5e7eb;
    }}
    
    .vertical-bar-item {{
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 60px;
    }}
    
    .vertical-bar {{
        width: 40px;
        border-radius: 4px 4px 0 0;
        display: flex;
        align-items: flex-start;
        justify-content: center;
        padding-top: 5px;
    }}
    
    .vertical-bar-value {{
        font-size: 7pt;
        font-weight: 600;
        color: white;
    }}
    
    .vertical-bar-label {{
        font-size: 7pt;
        color: #6b7280;
        margin-top: 5px;
        text-align: center;
    }}
    
    /* Insights */
    .insights-grid {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }}
    
    .insight-card {{
        flex: 1;
        min-width: 45%;
        background: #f0fdf4;
        border-left: 4px solid #22c55e;
        padding: 12px;
        border-radius: 0 8px 8px 0;
    }}
    
    .insight-card.alerta {{ background: #fffbeb; border-color: #f59e0b; }}
    .insight-card.destaque {{ background: #eff6ff; border-color: #3b82f6; }}
    .insight-card.info {{ background: #f5f3ff; border-color: {primary_color}; }}
    .insight-card.critico {{ background: #fef2f2; border-color: #ef4444; }}
    
    .insight-title {{
        font-weight: 600;
        font-size: 9pt;
        margin-bottom: 5px;
        color: #1f2937;
    }}
    
    .insight-text {{
        font-size: 8pt;
        color: #374151;
        line-height: 1.4;
    }}
    
    /* Tabelas */
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 8pt;
        margin-top: 10px;
    }}
    
    th {{
        background: {primary_color};
        color: white;
        padding: 10px 8px;
        text-align: left;
        font-size: 7pt;
        text-transform: uppercase;
        font-weight: 600;
    }}
    
    td {{
        padding: 8px;
        border-bottom: 1px solid #e5e7eb;
    }}
    
    tr:nth-child(even) {{
        background: #f8fafc;
    }}
    
    .text-right {{ text-align: right; }}
    .text-center {{ text-align: center; }}
    
    /* Footer */
    .footer {{
        text-align: center;
        color: #9ca3af;
        font-size: 8pt;
        padding: 20px 0;
        margin-top: 30px;
        border-top: 1px solid #e5e7eb;
    }}
    
    /* Cores das classificacoes */
    .color-nano {{ background-color: #22c55e; }}
    .color-micro {{ background-color: #3b82f6; }}
    .color-inter1 {{ background-color: #8b5cf6; }}
    .color-inter2 {{ background-color: #a855f7; }}
    .color-macro {{ background-color: #f97316; }}
    .color-mega1 {{ background-color: #ef4444; }}
    .color-mega2 {{ background-color: #dc2626; }}
    .color-default {{ background-color: {primary_color}; }}
    """


def formatar_numero(valor):
    """Formata numero para exibicao"""
    if valor >= 1000000:
        return f"{valor/1000000:.1f}M"
    elif valor >= 1000:
        return f"{valor/1000:.0f}K"
    return str(int(valor))


def get_cor_classificacao(classif):
    """Retorna cor CSS para classificacao"""
    cores = {
        'Nano': '#22c55e',
        'Micro': '#3b82f6',
        'Inter 1': '#8b5cf6',
        'Inter 2': '#a855f7',
        'Macro': '#f97316',
        'Mega 1': '#ef4444',
        'Mega 2': '#dc2626',
        'Super Mega': '#991b1b'
    }
    return cores.get(classif, '#7c3aed')


def gerar_barra_horizontal(label, valor, max_valor, cor='#7c3aed'):
    """Gera HTML de barra horizontal"""
    pct = (valor / max_valor * 100) if max_valor > 0 else 0
    pct = max(pct, 5)  # Minimo 5% para visibilidade
    
    return f"""
    <div class="bar-row">
        <div class="bar-label">{label}</div>
        <div class="bar-container">
            <div class="bar-fill" style="width: {pct}%; background: {cor};">
                <span class="bar-value">{formatar_numero(valor)}</span>
            </div>
        </div>
    </div>
    """


def gerar_barras_verticais(dados, cor='#7c3aed'):
    """Gera HTML de barras verticais"""
    if not dados:
        return "<p>Sem dados</p>"
    
    max_val = max(d['valor'] for d in dados) if dados else 1
    
    html = '<div class="vertical-bars">'
    for d in dados:
        pct = (d['valor'] / max_val * 100) if max_val > 0 else 0
        pct = max(pct, 5)
        altura = max(int(pct * 1.3), 20)  # Altura em pixels
        
        html += f"""
        <div class="vertical-bar-item">
            <div class="vertical-bar" style="height: {altura}px; background: {d.get('cor', cor)};">
                <span class="vertical-bar-value">{formatar_numero(d['valor'])}</span>
            </div>
            <div class="vertical-bar-label">{d['label']}</div>
        </div>
        """
    html += '</div>'
    
    return html


def gerar_pag_big_numbers(campanha, metricas, primary_color, dados_por_formato, dados_por_classif):
    """Gera pagina Big Numbers"""
    
    html = f"""
    <div class="section">
        <div class="section-title">Resumo da Campanha</div>
        
        <div class="big-number-card">
            <div class="value">{metricas['engajamento_efetivo']:.2f}%</div>
            <div class="label">Taxa de Engajamento Efetivo</div>
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
                <div class="value">{formatar_numero(metricas['total_views'] + metricas['total_impressoes'])}</div>
                <div class="label">Impressoes</div>
            </div>
            <div class="metric-card">
                <div class="value">{formatar_numero(metricas['total_alcance'])}</div>
                <div class="label">Alcance</div>
            </div>
            <div class="metric-card">
                <div class="value">{formatar_numero(metricas['total_interacoes'])}</div>
                <div class="label">Interacoes</div>
            </div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="value">{formatar_numero(metricas['total_curtidas'])}</div>
                <div class="label">Curtidas</div>
            </div>
            <div class="metric-card">
                <div class="value">{formatar_numero(metricas['total_comentarios'])}</div>
                <div class="label">Comentarios</div>
            </div>
            <div class="metric-card">
                <div class="value">{formatar_numero(metricas.get('total_compartilhamentos', 0))}</div>
                <div class="label">Compartilh.</div>
            </div>
            <div class="metric-card">
                <div class="value">{formatar_numero(metricas.get('total_saves', 0))}</div>
                <div class="label">Saves</div>
            </div>
            <div class="metric-card">
                <div class="value">{metricas['taxa_alcance']:.1f}%</div>
                <div class="label">Taxa Alcance</div>
            </div>
        </div>
        
        <div class="subsection-title">Graficos</div>
        <div class="charts-container">
    """
    
    # Grafico 1: Por Formato
    html += '<div class="chart-box"><div class="chart-title">Impressoes por Formato</div>'
    
    if dados_por_formato:
        max_val = max(d['impressoes'] for d in dados_por_formato.values()) if dados_por_formato else 1
        dados_barras = []
        for fmt, dados in sorted(dados_por_formato.items(), key=lambda x: x[1]['impressoes'], reverse=True):
            dados_barras.append({'label': fmt, 'valor': dados['impressoes']})
        
        html += gerar_barras_verticais(dados_barras, primary_color)
    else:
        html += '<p style="text-align: center; color: #6b7280;">Sem dados</p>'
    
    html += '</div>'
    
    # Grafico 2: Por Classificacao
    html += '<div class="chart-box"><div class="chart-title">Impressoes por Classificacao</div>'
    
    if dados_por_classif:
        dados_barras = []
        for classif, dados in sorted(dados_por_classif.items(), key=lambda x: x[1]['impressoes'], reverse=True):
            dados_barras.append({
                'label': classif,
                'valor': dados['impressoes'],
                'cor': get_cor_classificacao(classif)
            })
        
        html += gerar_barras_verticais(dados_barras)
    else:
        html += '<p style="text-align: center; color: #6b7280;">Sem dados</p>'
    
    html += '</div></div>'
    
    # Insights
    insights = data_manager.get_insights_campanha(campanha['id'], 'big_numbers')
    if insights:
        html += '<div class="subsection-title">Insights</div><div class="insights-grid">'
        for insight in insights[:4]:
            tipo = insight.get('tipo', 'info')
            titulo = insight.get('titulo', '')
            texto = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', insight.get('texto', ''))
            html += f'<div class="insight-card {tipo}"><div class="insight-title">{titulo}</div><div class="insight-text">{texto}</div></div>'
        html += '</div>'
    
    html += '</div>'
    return html


def gerar_pag_analise(campanha, primary_color, dados_por_formato, dados_por_classif):
    """Gera pagina de analise"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">Analise por Classificacao</div>
        <div class="charts-container">
    """
    
    # Grafico: Taxa de Engajamento por Classificacao
    html += '<div class="chart-box"><div class="chart-title">Taxa de Engajamento por Classificacao</div><div class="bar-chart">'
    
    if dados_por_classif:
        dados_ordenados = []
        for classif, dados in dados_por_classif.items():
            taxa = (dados['interacoes'] / dados['impressoes'] * 100) if dados['impressoes'] > 0 else 0
            dados_ordenados.append((classif, taxa, dados['impressoes']))
        
        dados_ordenados.sort(key=lambda x: x[1], reverse=True)
        max_taxa = max(d[1] for d in dados_ordenados) if dados_ordenados else 1
        
        for classif, taxa, imp in dados_ordenados:
            html += gerar_barra_horizontal(classif, taxa, max_taxa, get_cor_classificacao(classif))
    
    html += '</div></div>'
    
    # Grafico: Impressoes por Formato
    html += '<div class="chart-box"><div class="chart-title">Impressoes por Formato</div><div class="bar-chart">'
    
    if dados_por_formato:
        dados_ordenados = sorted(dados_por_formato.items(), key=lambda x: x[1]['impressoes'], reverse=True)
        max_imp = dados_ordenados[0][1]['impressoes'] if dados_ordenados else 1
        
        for fmt, dados in dados_ordenados:
            html += gerar_barra_horizontal(fmt, dados['impressoes'], max_imp, primary_color)
    
    html += '</div></div></div>'
    
    # Tabela de resumo
    html += """
    <div class="subsection-title">Resumo por Classificacao</div>
    <table>
        <tr>
            <th>Classificacao</th>
            <th class="text-right">Posts</th>
            <th class="text-right">Impressoes</th>
            <th class="text-right">Alcance</th>
            <th class="text-right">Interacoes</th>
            <th class="text-right">Taxa Eng.</th>
        </tr>
    """
    
    for classif, dados in sorted(dados_por_classif.items(), key=lambda x: x[1]['impressoes'], reverse=True):
        taxa = (dados['interacoes'] / dados['impressoes'] * 100) if dados['impressoes'] > 0 else 0
        html += f"""
        <tr>
            <td>{classif}</td>
            <td class="text-right">{dados['posts']}</td>
            <td class="text-right">{formatar_numero(dados['impressoes'])}</td>
            <td class="text-right">{formatar_numero(dados['alcance'])}</td>
            <td class="text-right">{formatar_numero(dados['interacoes'])}</td>
            <td class="text-right">{taxa:.2f}%</td>
        </tr>
        """
    
    html += '</table>'
    
    # Insights
    insights = data_manager.get_insights_campanha(campanha['id'], 'analise_geral')
    if insights:
        html += '<div class="subsection-title">Insights</div><div class="insights-grid">'
        for insight in insights[:4]:
            tipo = insight.get('tipo', 'info')
            titulo = insight.get('titulo', '')
            texto = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', insight.get('texto', ''))
            html += f'<div class="insight-card {tipo}"><div class="insight-title">{titulo}</div><div class="insight-text">{texto}</div></div>'
        html += '</div>'
    
    html += '</div>'
    return html


def gerar_pag_kpis_influenciadores(campanha, primary_color, dados_por_influ):
    """Gera pagina de KPIs por influenciador"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">KPIs por Influenciador</div>
    """
    
    # Top 15 por impressoes
    top15 = sorted(dados_por_influ, key=lambda x: x['impressoes'], reverse=True)[:15]
    
    if top15:
        # Grafico de barras horizontais
        html += '<div class="chart-box"><div class="chart-title">Top 15 Influenciadores por Impressoes</div><div class="bar-chart">'
        
        max_imp = top15[0]['impressoes'] if top15 else 1
        
        for inf in top15:
            cor = get_cor_classificacao(inf['classificacao'])
            html += gerar_barra_horizontal(inf['nome'][:15], inf['impressoes'], max_imp, cor)
        
        html += '</div></div>'
    
    # Tabela detalhada
    html += """
    <div class="subsection-title">Detalhamento</div>
    <table>
        <tr>
            <th>Influenciador</th>
            <th class="text-center">Classe</th>
            <th class="text-right">Seguidores</th>
            <th class="text-center">Posts</th>
            <th class="text-right">Impressoes</th>
            <th class="text-right">Alcance</th>
            <th class="text-right">Interacoes</th>
            <th class="text-right">Taxa</th>
        </tr>
    """
    
    for inf in top15:
        html += f"""
        <tr>
            <td>{inf['nome']}</td>
            <td class="text-center">{inf['classificacao']}</td>
            <td class="text-right">{formatar_numero(inf['seguidores'])}</td>
            <td class="text-center">{inf['posts']}</td>
            <td class="text-right">{formatar_numero(inf['impressoes'])}</td>
            <td class="text-right">{formatar_numero(inf['alcance'])}</td>
            <td class="text-right">{formatar_numero(inf['interacoes'])}</td>
            <td class="text-right">{inf['taxa']:.2f}%</td>
        </tr>
        """
    
    html += '</table>'
    
    # Insights
    insights = data_manager.get_insights_campanha(campanha['id'], 'kpis_influenciador')
    if insights:
        html += '<div class="subsection-title">Insights</div><div class="insights-grid">'
        for insight in insights[:4]:
            tipo = insight.get('tipo', 'info')
            titulo = insight.get('titulo', '')
            texto = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', insight.get('texto', ''))
            html += f'<div class="insight-card {tipo}"><div class="insight-title">{titulo}</div><div class="insight-text">{texto}</div></div>'
        html += '</div>'
    
    html += '</div>'
    return html


def gerar_pag_top_posts(campanha, primary_color, todos_posts):
    """Gera pagina de top posts"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">Top Posts</div>
    """
    
    # Top 20 por impressoes
    top20 = sorted(todos_posts, key=lambda x: x['impressoes'], reverse=True)[:20]
    
    html += """
    <table>
        <tr>
            <th>Influenciador</th>
            <th>Formato</th>
            <th class="text-center">Data</th>
            <th class="text-right">Impressoes</th>
            <th class="text-right">Alcance</th>
            <th class="text-right">Interacoes</th>
            <th class="text-right">Taxa</th>
        </tr>
    """
    
    for post in top20:
        html += f"""
        <tr>
            <td>{post['influenciador']}</td>
            <td>{post['formato']}</td>
            <td class="text-center">{post['data']}</td>
            <td class="text-right">{formatar_numero(post['impressoes'])}</td>
            <td class="text-right">{formatar_numero(post['alcance'])}</td>
            <td class="text-right">{formatar_numero(post['interacoes'])}</td>
            <td class="text-right">{post['taxa']:.2f}%</td>
        </tr>
        """
    
    html += '</table>'
    
    # Insights
    insights = data_manager.get_insights_campanha(campanha['id'], 'top_performance')
    if insights:
        html += '<div class="subsection-title">Insights</div><div class="insights-grid">'
        for insight in insights[:4]:
            tipo = insight.get('tipo', 'info')
            titulo = insight.get('titulo', '')
            texto = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', insight.get('texto', ''))
            html += f'<div class="insight-card {tipo}"><div class="insight-title">{titulo}</div><div class="insight-text">{texto}</div></div>'
        html += '</div>'
    
    html += '</div>'
    return html


def gerar_pag_lista_influenciadores(campanha, primary_color, dados_por_influ):
    """Gera pagina com lista completa de influenciadores"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">Lista Completa de Influenciadores</div>
        <table>
            <tr>
                <th>Influenciador</th>
                <th>Usuario</th>
                <th class="text-center">Classe</th>
                <th class="text-right">Seguidores</th>
                <th class="text-center">Posts</th>
                <th class="text-right">Impressoes</th>
                <th class="text-right">Alcance</th>
                <th class="text-right">Interacoes</th>
                <th class="text-right">Taxa</th>
            </tr>
    """
    
    for inf in sorted(dados_por_influ, key=lambda x: x['impressoes'], reverse=True):
        html += f"""
        <tr>
            <td>{inf['nome']}</td>
            <td>@{inf['usuario']}</td>
            <td class="text-center">{inf['classificacao']}</td>
            <td class="text-right">{formatar_numero(inf['seguidores'])}</td>
            <td class="text-center">{inf['posts']}</td>
            <td class="text-right">{formatar_numero(inf['impressoes'])}</td>
            <td class="text-right">{formatar_numero(inf['alcance'])}</td>
            <td class="text-right">{formatar_numero(inf['interacoes'])}</td>
            <td class="text-right">{inf['taxa']:.2f}%</td>
        </tr>
        """
    
    html += '</table></div>'
    return html
