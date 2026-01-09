"""
Modulo: Exportacao de Relatorios em PDF
Gera PDF estatico com mesma estetica do relatorio online
"""

import io
import base64
from datetime import datetime
import re

# WeasyPrint para conversao HTML -> PDF
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from utils import data_manager, funcoes_auxiliares


def gerar_pdf_relatorio(campanha_id: int, incluir_paginas: list = None) -> bytes:
    """
    Gera PDF do relatorio da campanha
    
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
    
    # Gerar HTML
    html_content = gerar_html_relatorio(campanha, cliente, metricas, primary_color, incluir_paginas)
    
    # Converter para PDF
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    return pdf_bytes


def gerar_html_relatorio(campanha, cliente, metricas, primary_color, incluir_paginas=None):
    """Gera HTML completo do relatorio"""
    
    paginas_default = ['big_numbers', 'analise_geral', 'influenciadores', 'top_posts']
    paginas = incluir_paginas or paginas_default
    
    # CSS do relatorio
    css = f"""
    @page {{
        size: A4;
        margin: 1.5cm;
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
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
        margin-bottom: 20px;
    }}
    
    .metric-card {{
        background: #f9fafb;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }}
    
    .metric-value {{
        font-size: 18pt;
        font-weight: 700;
        color: {primary_color};
    }}
    
    .metric-label {{
        font-size: 9pt;
        color: #6b7280;
        text-transform: uppercase;
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
    
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
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
        font-size: 9pt;
    }}
    
    td {{
        font-size: 10pt;
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
    
    # Analise Geral
    if 'analise_geral' in paginas:
        html += gerar_secao_analise(campanha, metricas)
    
    # Influenciadores
    if 'influenciadores' in paginas:
        html += gerar_secao_influenciadores(campanha)
    
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
    
    html = """
    <div class="section">
        <div class="section-title">Resumo da Campanha</div>
        <div class="metrics-grid">
    """
    
    cards = [
        ("Influenciadores", str(metricas['total_influenciadores'])),
        ("Posts", str(metricas['total_posts'])),
        ("Impressoes", funcoes_auxiliares.formatar_numero(metricas['total_views'] + metricas['total_impressoes'])),
        ("Alcance", funcoes_auxiliares.formatar_numero(metricas['total_alcance'])),
        ("Interacoes", funcoes_auxiliares.formatar_numero(metricas['total_interacoes'])),
        ("Taxa Engajamento", f"{metricas['engajamento_efetivo']:.2f}%"),
        ("Taxa Alcance", f"{metricas['taxa_alcance']:.2f}%"),
        ("Investimento", f"R$ {metricas.get('total_custo', 0):,.0f}".replace(",", ".") if metricas.get('total_custo', 0) > 0 else "-")
    ]
    
    for label, value in cards:
        html += f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
        """
    
    html += "</div>"
    
    # Insights
    insights = data_manager.get_insights_campanha(campanha['id'], 'big_numbers')
    
    if insights:
        html += '<div class="section-title" style="margin-top: 20px;">Insights</div>'
        
        for insight in insights[:5]:  # Limitar a 5 insights
            tipo = insight.get('tipo', 'info')
            icone = insight.get('icone', '💡')
            titulo = insight.get('titulo', '')
            texto = insight.get('texto', '')
            
            # Converter markdown para HTML
            texto_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', texto)
            
            html += f"""
            <div class="insight-box {tipo}">
                <div class="insight-title">{icone} {titulo}</div>
                <div class="insight-text">{texto_html}</div>
            </div>
            """
    
    html += "</div>"
    return html


def gerar_secao_analise(campanha, metricas):
    """Gera secao de analise por formato e classificacao"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">Analise de Performance</div>
    """
    
    # Por Formato
    formatos = {}
    for inf_camp in campanha.get('influenciadores', []):
        for post in inf_camp.get('posts', []):
            formato = post.get('formato', 'Outro')
            if formato not in formatos:
                formatos[formato] = {'impressoes': 0, 'alcance': 0, 'interacoes': 0}
            formatos[formato]['impressoes'] += post.get('views', 0) + post.get('impressoes', 0)
            formatos[formato]['alcance'] += post.get('alcance', 0)
            formatos[formato]['interacoes'] += post.get('interacoes', 0)
    
    if formatos:
        html += """
        <h3 style="font-size: 12pt; margin-top: 20px;">Por Formato</h3>
        <table>
            <tr>
                <th>Formato</th>
                <th>Impressoes</th>
                <th>Alcance</th>
                <th>Interacoes</th>
                <th>Taxa Eng.</th>
            </tr>
        """
        
        for formato, dados in sorted(formatos.items(), key=lambda x: x[1]['impressoes'], reverse=True):
            taxa = (dados['interacoes'] / dados['impressoes'] * 100) if dados['impressoes'] > 0 else 0
            html += f"""
            <tr>
                <td>{formato}</td>
                <td>{funcoes_auxiliares.formatar_numero(dados['impressoes'])}</td>
                <td>{funcoes_auxiliares.formatar_numero(dados['alcance'])}</td>
                <td>{funcoes_auxiliares.formatar_numero(dados['interacoes'])}</td>
                <td>{taxa:.2f}%</td>
            </tr>
            """
        
        html += "</table>"
    
    # Por Classificacao
    classificacoes = {}
    for inf_camp in campanha.get('influenciadores', []):
        inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
        if not inf:
            continue
        classe = inf.get('classificacao', 'Desconhecido')
        if classe not in classificacoes:
            classificacoes[classe] = {'impressoes': 0, 'alcance': 0, 'interacoes': 0, 'qtd': 0}
        classificacoes[classe]['qtd'] += 1
        for post in inf_camp.get('posts', []):
            classificacoes[classe]['impressoes'] += post.get('views', 0) + post.get('impressoes', 0)
            classificacoes[classe]['alcance'] += post.get('alcance', 0)
            classificacoes[classe]['interacoes'] += post.get('interacoes', 0)
    
    if classificacoes:
        html += """
        <h3 style="font-size: 12pt; margin-top: 20px;">Por Classificacao</h3>
        <table>
            <tr>
                <th>Classificacao</th>
                <th>Qtd</th>
                <th>Impressoes</th>
                <th>Alcance</th>
                <th>Interacoes</th>
            </tr>
        """
        
        ordem = ['Nano', 'Micro', 'Mid', 'Macro', 'Mega']
        for classe in ordem:
            if classe in classificacoes:
                dados = classificacoes[classe]
                html += f"""
                <tr>
                    <td>{classe}</td>
                    <td>{dados['qtd']}</td>
                    <td>{funcoes_auxiliares.formatar_numero(dados['impressoes'])}</td>
                    <td>{funcoes_auxiliares.formatar_numero(dados['alcance'])}</td>
                    <td>{funcoes_auxiliares.formatar_numero(dados['interacoes'])}</td>
                </tr>
                """
        
        html += "</table>"
    
    html += "</div>"
    return html


def gerar_secao_influenciadores(campanha):
    """Gera secao com lista de influenciadores"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">Influenciadores</div>
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
            </tr>
    """
    
    posts = []
    for inf_camp in campanha.get('influenciadores', []):
        inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
        if not inf:
            continue
        
        for post in inf_camp.get('posts', []):
            posts.append({
                'influenciador': inf['nome'],
                'formato': post.get('formato', '-'),
                'data': post.get('data_publicacao', '-'),
                'impressoes': post.get('views', 0) + post.get('impressoes', 0),
                'alcance': post.get('alcance', 0),
                'interacoes': post.get('interacoes', 0)
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
        </tr>
        """
    
    html += "</table></div>"
    return html


def get_pdf_download_link(pdf_bytes: bytes, filename: str = "relatorio.pdf") -> str:
    """Gera link de download para o PDF"""
    b64 = base64.b64encode(pdf_bytes).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📥 Baixar PDF</a>'
