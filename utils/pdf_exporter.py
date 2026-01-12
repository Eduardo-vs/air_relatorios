"""
Modulo: Exportacao de Relatorios em PDF
Gera PDF estatico com graficos e mesma estetica do relatorio online
"""

import io
import base64
from datetime import datetime
import re
import plotly.graph_objects as go
import plotly.io as pio

# WeasyPrint para conversao HTML -> PDF
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from utils import data_manager, funcoes_auxiliares


def fig_to_base64(fig, width=800, height=400):
    """Converte figura Plotly para base64 PNG"""
    img_bytes = pio.to_image(fig, format='png', width=width, height=height, scale=2)
    b64 = base64.b64encode(img_bytes).decode()
    return f"data:image/png;base64,{b64}"


def gerar_pdf_relatorio(campanha_id: int, incluir_paginas: list = None) -> bytes:
    """
    Gera PDF do relatorio da campanha com graficos
    
    Args:
        campanha_id: ID da campanha
        incluir_paginas: Lista de paginas a incluir (None = todas)
    
    Returns:
        bytes do PDF gerado
    """
    if not WEASYPRINT_AVAILABLE:
        raise ImportError("WeasyPrint nao instalado. Execute: pip install weasyprint")
    
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
    
    # Gerar HTML
    html_content = gerar_html_relatorio(campanha, cliente, metricas, primary_color, incluir_paginas)
    
    # Converter para PDF
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    return pdf_bytes


def gerar_html_relatorio(campanha, cliente, metricas, primary_color, incluir_paginas=None):
    """Gera HTML completo do relatorio com graficos"""
    
    paginas_default = ['big_numbers', 'analise_geral', 'influenciadores', 'top_posts']
    paginas = incluir_paginas or paginas_default
    
    # CSS do relatorio
    css = f"""
    @page {{
        size: A4;
        margin: 1.5cm;
    }}
    
    * {{
        box-sizing: border-box;
    }}
    
    body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 11pt;
        line-height: 1.5;
        color: #1a1a1a;
        margin: 0;
        padding: 0;
    }}
    
    .header {{
        text-align: center;
        padding: 20px 0;
        border-bottom: 3px solid {primary_color};
        margin-bottom: 30px;
    }}
    
    .header h1 {{
        color: {primary_color};
        margin: 0 0 10px 0;
        font-size: 24pt;
    }}
    
    .header .subtitle {{
        color: #6b7280;
        font-size: 11pt;
    }}
    
    .section {{
        margin-bottom: 30px;
        page-break-inside: avoid;
    }}
    
    .section-title {{
        color: {primary_color};
        font-size: 14pt;
        font-weight: 600;
        border-bottom: 2px solid {primary_color};
        padding-bottom: 5px;
        margin-bottom: 15px;
    }}
    
    .metrics-grid {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 20px;
    }}
    
    .metric-card {{
        background: #f9fafb;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        flex: 1;
        min-width: 100px;
        border: 1px solid #e5e7eb;
    }}
    
    .metric-value {{
        font-size: 16pt;
        font-weight: 700;
        color: {primary_color};
    }}
    
    .metric-label {{
        font-size: 8pt;
        color: #6b7280;
        text-transform: uppercase;
    }}
    
    .big-metric {{
        background: {primary_color};
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
    }}
    
    .big-metric .value {{
        font-size: 36pt;
        font-weight: 700;
    }}
    
    .big-metric .label {{
        font-size: 10pt;
        opacity: 0.9;
    }}
    
    .insight-box {{
        background: #f5f3ff;
        border-left: 4px solid {primary_color};
        padding: 12px 15px;
        margin-bottom: 10px;
        border-radius: 0 8px 8px 0;
    }}
    
    .insight-box.destaque {{ background: #eff6ff; border-color: #3b82f6; }}
    .insight-box.sucesso {{ background: #ecfdf5; border-color: #10b981; }}
    .insight-box.alerta {{ background: #fffbeb; border-color: #f59e0b; }}
    .insight-box.critico {{ background: #fef2f2; border-color: #ef4444; }}
    
    .insight-title {{
        font-weight: 600;
        margin-bottom: 5px;
    }}
    
    .insight-text {{
        font-size: 10pt;
        color: #374151;
    }}
    
    .chart-container {{
        text-align: center;
        margin: 20px 0;
    }}
    
    .chart-container img {{
        max-width: 100%;
        height: auto;
    }}
    
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-size: 9pt;
    }}
    
    th, td {{
        padding: 8px 10px;
        text-align: left;
        border-bottom: 1px solid #e5e7eb;
    }}
    
    th {{
        background: {primary_color};
        color: white;
        font-weight: 600;
    }}
    
    td {{
        font-size: 9pt;
    }}
    
    tr:nth-child(even) {{
        background: #f9fafb;
    }}
    
    .footer {{
        text-align: center;
        color: #9ca3af;
        font-size: 9pt;
        margin-top: 30px;
        padding-top: 20px;
        border-top: 1px solid #e5e7eb;
    }}
    
    .page-break {{
        page-break-before: always;
    }}
    
    .two-col {{
        display: flex;
        gap: 20px;
    }}
    
    .two-col > div {{
        flex: 1;
    }}
    """
    
    # Header
    nome_cliente = cliente['nome'] if cliente else ''
    data_inicio = campanha.get('data_inicio', '')
    data_fim = campanha.get('data_fim', '')
    
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
            <div class="subtitle">
                {nome_cliente} | {data_inicio} - {data_fim}
            </div>
        </div>
    """
    
    # Big Numbers
    if 'big_numbers' in paginas:
        html += gerar_secao_big_numbers(metricas, campanha, primary_color)
    
    # Analise Geral com Graficos
    if 'analise_geral' in paginas:
        html += gerar_secao_analise_graficos(campanha, metricas, primary_color)
    
    # Influenciadores
    if 'influenciadores' in paginas:
        html += gerar_secao_influenciadores(campanha, primary_color)
    
    # Top Posts
    if 'top_posts' in paginas:
        html += gerar_secao_top_posts(campanha)
    
    # Footer
    html += f"""
        <div class="footer">
            Relatorio gerado por <strong>AIR</strong> em {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
    </body>
    </html>
    """
    
    return html


def gerar_secao_big_numbers(metricas, campanha, primary_color):
    """Gera secao de Big Numbers"""
    
    # Taxa de engajamento destacada
    html = f"""
    <div class="section">
        <div class="section-title">Resumo da Campanha</div>
        
        <div class="big-metric">
            <div class="value">{metricas['engajamento_efetivo']:.2f}%</div>
            <div class="label">TAXA DE ENGAJAMENTO EFETIVO</div>
        </div>
        
        <div class="metrics-grid">
    """
    
    cards = [
        ("Influenciadores", str(metricas['total_influenciadores'])),
        ("Posts", str(metricas['total_posts'])),
        ("Impressoes", funcoes_auxiliares.formatar_numero(metricas['total_views'] + metricas['total_impressoes'])),
        ("Alcance", funcoes_auxiliares.formatar_numero(metricas['total_alcance'])),
    ]
    
    for label, value in cards:
        html += f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
        """
    
    html += "</div><div class='metrics-grid'>"
    
    cards2 = [
        ("Interacoes", funcoes_auxiliares.formatar_numero(metricas['total_interacoes'])),
        ("Curtidas", funcoes_auxiliares.formatar_numero(metricas['total_curtidas'])),
        ("Comentarios", funcoes_auxiliares.formatar_numero(metricas['total_comentarios'])),
        ("Taxa Alcance", f"{metricas['taxa_alcance']:.2f}%"),
    ]
    
    for label, value in cards2:
        html += f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
        """
    
    html += "</div>"
    
    # Investimento se houver
    if metricas.get('total_custo', 0) > 0:
        custo = metricas['total_custo']
        cpm = (custo / (metricas['total_views'] + metricas['total_impressoes']) * 1000) if (metricas['total_views'] + metricas['total_impressoes']) > 0 else 0
        cpe = (custo / metricas['total_interacoes']) if metricas['total_interacoes'] > 0 else 0
        
        html += f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">R$ {custo:,.0f}</div>
                <div class="metric-label">Investimento</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">R$ {cpm:,.2f}</div>
                <div class="metric-label">CPM</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">R$ {cpe:,.2f}</div>
                <div class="metric-label">CPE</div>
            </div>
        </div>
        """.replace(",", ".")
    
    # Insights
    insights = data_manager.get_insights_campanha(campanha['id'], 'big_numbers')
    
    if insights:
        html += '<div class="section-title" style="margin-top: 20px;">Insights</div>'
        
        for insight in insights[:5]:
            tipo = insight.get('tipo', 'info')
            icone = insight.get('icone', '💡')
            titulo = insight.get('titulo', '')
            texto = insight.get('texto', '')
            
            texto_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', texto)
            
            html += f"""
            <div class="insight-box {tipo}">
                <div class="insight-title">{icone} {titulo}</div>
                <div class="insight-text">{texto_html}</div>
            </div>
            """
    
    html += "</div>"
    return html


def gerar_secao_analise_graficos(campanha, metricas, primary_color):
    """Gera secao de analise com graficos"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">Analise de Performance</div>
    """
    
    # Coletar dados por formato
    formatos = {}
    classificacoes = {}
    
    for inf_camp in campanha.get('influenciadores', []):
        inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
        classe = inf.get('classificacao', 'Desconhecido') if inf else 'Desconhecido'
        
        if classe not in classificacoes:
            classificacoes[classe] = {'impressoes': 0, 'interacoes': 0, 'qtd': 0}
        classificacoes[classe]['qtd'] += 1
        
        for post in inf_camp.get('posts', []):
            formato = post.get('formato', 'Outro')
            if formato not in formatos:
                formatos[formato] = {'impressoes': 0, 'alcance': 0, 'interacoes': 0}
            
            imp = post.get('views', 0) + post.get('impressoes', 0)
            formatos[formato]['impressoes'] += imp
            formatos[formato]['alcance'] += post.get('alcance', 0)
            formatos[formato]['interacoes'] += post.get('interacoes', 0)
            classificacoes[classe]['impressoes'] += imp
            classificacoes[classe]['interacoes'] += post.get('interacoes', 0)
    
    # Grafico por Formato
    if formatos:
        try:
            fig = go.Figure()
            
            nomes = list(formatos.keys())
            valores = [formatos[f]['impressoes'] for f in nomes]
            
            fig.add_trace(go.Bar(
                x=nomes,
                y=valores,
                marker_color=primary_color,
                text=[funcoes_auxiliares.formatar_numero(v) for v in valores],
                textposition='outside'
            ))
            
            fig.update_layout(
                title='Impressoes por Formato',
                showlegend=False,
                height=350,
                margin=dict(t=50, b=50, l=50, r=50),
                plot_bgcolor='white'
            )
            
            img_b64 = fig_to_base64(fig, width=700, height=350)
            html += f'<div class="chart-container"><img src="{img_b64}" /></div>'
        except Exception as e:
            # Se falhar o grafico, mostrar tabela
            html += """
            <h3 style="font-size: 12pt;">Por Formato</h3>
            <table>
                <tr><th>Formato</th><th>Impressoes</th><th>Alcance</th><th>Interacoes</th></tr>
            """
            for formato, dados in sorted(formatos.items(), key=lambda x: x[1]['impressoes'], reverse=True):
                html += f"""
                <tr>
                    <td>{formato}</td>
                    <td>{funcoes_auxiliares.formatar_numero(dados['impressoes'])}</td>
                    <td>{funcoes_auxiliares.formatar_numero(dados['alcance'])}</td>
                    <td>{funcoes_auxiliares.formatar_numero(dados['interacoes'])}</td>
                </tr>
                """
            html += "</table>"
    
    # Grafico por Classificacao
    if classificacoes:
        try:
            fig2 = go.Figure()
            
            ordem = ['Nano', 'Micro', 'Mid', 'Macro', 'Mega']
            nomes_ord = [c for c in ordem if c in classificacoes]
            valores_ord = [classificacoes[c]['impressoes'] for c in nomes_ord]
            
            cores = ['#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe', '#ede9fe']
            
            fig2.add_trace(go.Bar(
                x=nomes_ord,
                y=valores_ord,
                marker_color=cores[:len(nomes_ord)],
                text=[funcoes_auxiliares.formatar_numero(v) for v in valores_ord],
                textposition='outside'
            ))
            
            fig2.update_layout(
                title='Impressoes por Classificacao',
                showlegend=False,
                height=350,
                margin=dict(t=50, b=50, l=50, r=50),
                plot_bgcolor='white'
            )
            
            img_b64_2 = fig_to_base64(fig2, width=700, height=350)
            html += f'<div class="chart-container"><img src="{img_b64_2}" /></div>'
        except:
            pass
    
    # Tabela resumo
    html += """
    <h3 style="font-size: 12pt; margin-top: 20px;">Resumo por Classificacao</h3>
    <table>
        <tr><th>Classificacao</th><th>Qtd Influs</th><th>Impressoes</th><th>Interacoes</th><th>Taxa Eng.</th></tr>
    """
    
    ordem = ['Nano', 'Micro', 'Mid', 'Macro', 'Mega']
    for classe in ordem:
        if classe in classificacoes:
            dados = classificacoes[classe]
            taxa = (dados['interacoes'] / dados['impressoes'] * 100) if dados['impressoes'] > 0 else 0
            html += f"""
            <tr>
                <td>{classe}</td>
                <td>{dados['qtd']}</td>
                <td>{funcoes_auxiliares.formatar_numero(dados['impressoes'])}</td>
                <td>{funcoes_auxiliares.formatar_numero(dados['interacoes'])}</td>
                <td>{taxa:.2f}%</td>
            </tr>
            """
    
    html += "</table></div>"
    return html


def gerar_secao_influenciadores(campanha, primary_color):
    """Gera secao com lista de influenciadores e grafico"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">Influenciadores</div>
    """
    
    dados_inf = []
    for inf_camp in campanha.get('influenciadores', []):
        inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
        if not inf:
            continue
        
        impressoes = 0
        interacoes = 0
        posts = inf_camp.get('posts', [])
        
        for post in posts:
            impressoes += post.get('views', 0) + post.get('impressoes', 0)
            interacoes += post.get('interacoes', 0)
        
        taxa = (interacoes / impressoes * 100) if impressoes > 0 else 0
        
        dados_inf.append({
            'nome': inf['nome'],
            'classe': inf.get('classificacao', '-'),
            'seguidores': inf.get('seguidores', 0),
            'posts': len(posts),
            'impressoes': impressoes,
            'interacoes': interacoes,
            'taxa': taxa
        })
    
    # Ordenar por impressoes
    dados_inf.sort(key=lambda x: x['impressoes'], reverse=True)
    
    # Grafico top 10
    if dados_inf:
        try:
            top10 = dados_inf[:10]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=[d['nome'] for d in top10],
                x=[d['impressoes'] for d in top10],
                orientation='h',
                marker_color=primary_color,
                text=[funcoes_auxiliares.formatar_numero(d['impressoes']) for d in top10],
                textposition='outside'
            ))
            
            fig.update_layout(
                title='Top 10 Influenciadores por Impressoes',
                height=400,
                margin=dict(t=50, b=30, l=150, r=80),
                yaxis=dict(autorange='reversed'),
                plot_bgcolor='white'
            )
            
            img_b64 = fig_to_base64(fig, width=700, height=400)
            html += f'<div class="chart-container"><img src="{img_b64}" /></div>'
        except:
            pass
    
    # Tabela
    html += """
    <table>
        <tr>
            <th>Nome</th>
            <th>Classe</th>
            <th>Seguidores</th>
            <th>Posts</th>
            <th>Impressoes</th>
            <th>Interacoes</th>
            <th>Taxa Eng.</th>
        </tr>
    """
    
    for d in dados_inf:
        html += f"""
        <tr>
            <td>{d['nome']}</td>
            <td>{d['classe']}</td>
            <td>{funcoes_auxiliares.formatar_numero(d['seguidores'])}</td>
            <td>{d['posts']}</td>
            <td>{funcoes_auxiliares.formatar_numero(d['impressoes'])}</td>
            <td>{funcoes_auxiliares.formatar_numero(d['interacoes'])}</td>
            <td>{d['taxa']:.2f}%</td>
        </tr>
        """
    
    html += "</table></div>"
    return html


def gerar_secao_top_posts(campanha):
    """Gera secao com top posts"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">Top Posts</div>
        <table>
            <tr>
                <th>Influenciador</th>
                <th>Formato</th>
                <th>Data</th>
                <th>Impressoes</th>
                <th>Alcance</th>
                <th>Interacoes</th>
                <th>Taxa Eng.</th>
            </tr>
    """
    
    posts = []
    for inf_camp in campanha.get('influenciadores', []):
        inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
        if not inf:
            continue
        
        for post in inf_camp.get('posts', []):
            imp = post.get('views', 0) + post.get('impressoes', 0)
            inter = post.get('interacoes', 0)
            taxa = (inter / imp * 100) if imp > 0 else 0
            
            posts.append({
                'influenciador': inf['nome'],
                'formato': post.get('formato', '-'),
                'data': post.get('data_publicacao', '-'),
                'impressoes': imp,
                'alcance': post.get('alcance', 0),
                'interacoes': inter,
                'taxa': taxa
            })
    
    # Ordenar por impressoes e pegar top 15
    posts.sort(key=lambda x: x['impressoes'], reverse=True)
    
    for post in posts[:15]:
        html += f"""
        <tr>
            <td>{post['influenciador']}</td>
            <td>{post['formato']}</td>
            <td>{post['data']}</td>
            <td>{funcoes_auxiliares.formatar_numero(post['impressoes'])}</td>
            <td>{funcoes_auxiliares.formatar_numero(post['alcance'])}</td>
            <td>{funcoes_auxiliares.formatar_numero(post['interacoes'])}</td>
            <td>{post['taxa']:.2f}%</td>
        </tr>
        """
    
    html += "</table></div>"
    return html


def get_pdf_download_link(pdf_bytes: bytes, filename: str = "relatorio.pdf") -> str:
    """Gera link de download para o PDF"""
    b64 = base64.b64encode(pdf_bytes).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📥 Baixar PDF</a>'
