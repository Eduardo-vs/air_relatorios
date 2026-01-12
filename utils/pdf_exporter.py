"""
Modulo: Exportacao de Relatorios em PDF
Gera PDF estatico com visual profissional usando barras CSS
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
    """Gera HTML completo do relatorio"""
    
    paginas_default = ['big_numbers', 'analise_geral', 'influenciadores', 'top_posts']
    paginas = incluir_paginas or paginas_default
    
    # CSS do relatorio
    css = f"""
    @page {{
        size: A4;
        margin: 1.5cm;
        @bottom-center {{
            content: "Pagina " counter(page) " de " counter(pages);
            font-size: 9pt;
            color: #9ca3af;
        }}
    }}
    
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    
    body {{
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.4;
        color: #1f2937;
    }}
    
    .header {{
        text-align: center;
        padding: 20px 0 15px 0;
        border-bottom: 4px solid {primary_color};
        margin-bottom: 20px;
    }}
    
    .header h1 {{
        color: {primary_color};
        font-size: 22pt;
        font-weight: 700;
        margin-bottom: 8px;
    }}
    
    .header .subtitle {{
        color: #6b7280;
        font-size: 11pt;
    }}
    
    .section {{
        margin-bottom: 25px;
    }}
    
    .section-title {{
        color: {primary_color};
        font-size: 13pt;
        font-weight: 700;
        padding-bottom: 8px;
        border-bottom: 2px solid {primary_color};
        margin-bottom: 15px;
    }}
    
    /* Big Numbers Grid */
    .big-number-highlight {{
        background: linear-gradient(135deg, {primary_color}, #a78bfa);
        color: white;
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
    }}
    
    .big-number-highlight .value {{
        font-size: 42pt;
        font-weight: 800;
    }}
    
    .big-number-highlight .label {{
        font-size: 11pt;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    .metrics-row {{
        display: flex;
        gap: 12px;
        margin-bottom: 15px;
    }}
    
    .metric-card {{
        flex: 1;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }}
    
    .metric-card .value {{
        font-size: 18pt;
        font-weight: 700;
        color: {primary_color};
    }}
    
    .metric-card .label {{
        font-size: 8pt;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }}
    
    /* Insights */
    .insight-card {{
        background: #f0fdf4;
        border-left: 4px solid #22c55e;
        padding: 12px 15px;
        margin-bottom: 10px;
        border-radius: 0 8px 8px 0;
    }}
    
    .insight-card.alerta {{
        background: #fffbeb;
        border-color: #f59e0b;
    }}
    
    .insight-card.destaque {{
        background: #eff6ff;
        border-color: #3b82f6;
    }}
    
    .insight-card.info {{
        background: #f5f3ff;
        border-color: {primary_color};
    }}
    
    .insight-title {{
        font-weight: 600;
        font-size: 10pt;
        margin-bottom: 4px;
    }}
    
    .insight-text {{
        font-size: 9pt;
        color: #374151;
    }}
    
    /* Graficos em CSS */
    .chart-container {{
        margin: 15px 0;
    }}
    
    .bar-chart {{
        margin: 10px 0;
    }}
    
    .bar-item {{
        display: flex;
        align-items: center;
        margin-bottom: 8px;
    }}
    
    .bar-label {{
        width: 100px;
        font-size: 9pt;
        color: #374151;
        text-align: right;
        padding-right: 10px;
    }}
    
    .bar-container {{
        flex: 1;
        background: #e5e7eb;
        height: 24px;
        border-radius: 4px;
        overflow: hidden;
        position: relative;
    }}
    
    .bar-fill {{
        height: 100%;
        background: linear-gradient(90deg, {primary_color}, #a78bfa);
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 8px;
    }}
    
    .bar-value {{
        font-size: 8pt;
        font-weight: 600;
        color: white;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }}
    
    .bar-value-outside {{
        font-size: 8pt;
        color: #374151;
        margin-left: 8px;
        min-width: 60px;
    }}
    
    /* Tabelas */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 9pt;
    }}
    
    th {{
        background: {primary_color};
        color: white;
        padding: 10px 8px;
        text-align: left;
        font-weight: 600;
        font-size: 8pt;
        text-transform: uppercase;
    }}
    
    td {{
        padding: 10px 8px;
        border-bottom: 1px solid #e5e7eb;
    }}
    
    tr:nth-child(even) {{
        background: #f8fafc;
    }}
    
    tr:hover {{
        background: #f1f5f9;
    }}
    
    .text-right {{
        text-align: right;
    }}
    
    .text-center {{
        text-align: center;
    }}
    
    /* Footer */
    .footer {{
        text-align: center;
        color: #9ca3af;
        font-size: 8pt;
        padding-top: 20px;
        margin-top: 30px;
        border-top: 1px solid #e5e7eb;
    }}
    
    .page-break {{
        page-break-before: always;
    }}
    
    /* Mini bar para tabelas */
    .mini-bar {{
        display: inline-block;
        height: 8px;
        background: {primary_color};
        border-radius: 4px;
        margin-right: 6px;
        vertical-align: middle;
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
                {nome_cliente} &bull; {data_inicio} a {data_fim}
            </div>
        </div>
    """
    
    # Big Numbers
    if 'big_numbers' in paginas:
        html += gerar_secao_big_numbers(metricas, campanha, primary_color)
    
    # Analise Geral
    if 'analise_geral' in paginas:
        html += gerar_secao_analise(campanha, metricas, primary_color)
    
    # Influenciadores
    if 'influenciadores' in paginas:
        html += gerar_secao_influenciadores(campanha, primary_color)
    
    # Top Posts
    if 'top_posts' in paginas:
        html += gerar_secao_top_posts(campanha, primary_color)
    
    # Footer
    html += f"""
        <div class="footer">
            Relatorio gerado automaticamente por <strong>AIR</strong> em {datetime.now().strftime('%d/%m/%Y as %H:%M')}
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
        <div class="section-title">Resumo Executivo</div>
        
        <div class="big-number-highlight">
            <div class="value">{metricas['engajamento_efetivo']:.2f}%</div>
            <div class="label">Taxa de Engajamento Efetivo</div>
        </div>
        
        <div class="metrics-row">
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
        </div>
        
        <div class="metrics-row">
            <div class="metric-card">
                <div class="value">{funcoes_auxiliares.formatar_numero(metricas['total_interacoes'])}</div>
                <div class="label">Interacoes</div>
            </div>
            <div class="metric-card">
                <div class="value">{funcoes_auxiliares.formatar_numero(metricas['total_curtidas'])}</div>
                <div class="label">Curtidas</div>
            </div>
            <div class="metric-card">
                <div class="value">{funcoes_auxiliares.formatar_numero(metricas['total_comentarios'])}</div>
                <div class="label">Comentarios</div>
            </div>
            <div class="metric-card">
                <div class="value">{metricas['taxa_alcance']:.1f}%</div>
                <div class="label">Taxa Alcance</div>
            </div>
        </div>
    """
    
    # Investimento se houver
    if metricas.get('total_custo', 0) > 0:
        custo = metricas['total_custo']
        total_imp = metricas['total_views'] + metricas['total_impressoes']
        cpm = (custo / total_imp * 1000) if total_imp > 0 else 0
        cpe = (custo / metricas['total_interacoes']) if metricas['total_interacoes'] > 0 else 0
        
        html += f"""
        <div class="metrics-row">
            <div class="metric-card">
                <div class="value">R$ {custo:,.0f}</div>
                <div class="label">Investimento</div>
            </div>
            <div class="metric-card">
                <div class="value">R$ {cpm:,.2f}</div>
                <div class="label">CPM</div>
            </div>
            <div class="metric-card">
                <div class="value">R$ {cpe:,.2f}</div>
                <div class="label">CPE</div>
            </div>
            <div class="metric-card">
                <div class="value">&nbsp;</div>
                <div class="label">&nbsp;</div>
            </div>
        </div>
        """.replace(",", ".")
    
    # Insights
    insights = data_manager.get_insights_campanha(campanha['id'], 'big_numbers')
    
    if insights:
        html += '<div class="section-title" style="margin-top: 25px;">Insights</div>'
        
        for insight in insights[:4]:
            tipo = insight.get('tipo', 'info')
            titulo = insight.get('titulo', '')
            texto = insight.get('texto', '')
            texto = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', texto)
            
            html += f"""
            <div class="insight-card {tipo}">
                <div class="insight-title">{titulo}</div>
                <div class="insight-text">{texto}</div>
            </div>
            """
    
    html += "</div>"
    return html


def gerar_secao_analise(campanha, metricas, primary_color):
    """Gera secao de analise com graficos em CSS"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">Analise de Performance</div>
    """
    
    # Coletar dados por formato
    formatos = {}
    classificacoes = {}
    
    for inf_camp in campanha.get('influenciadores', []):
        inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
        classe = inf.get('classificacao', 'Outro') if inf else 'Outro'
        
        if classe not in classificacoes:
            classificacoes[classe] = {'impressoes': 0, 'interacoes': 0, 'qtd': 0}
        classificacoes[classe]['qtd'] += 1
        
        for post in inf_camp.get('posts', []):
            formato = post.get('formato', 'Outro')
            if formato not in formatos:
                formatos[formato] = {'impressoes': 0, 'alcance': 0, 'interacoes': 0}
            
            imp = (post.get('views', 0) or 0) + (post.get('impressoes', 0) or 0)
            formatos[formato]['impressoes'] += imp
            formatos[formato]['alcance'] += post.get('alcance', 0) or 0
            formatos[formato]['interacoes'] += post.get('interacoes', 0) or 0
            classificacoes[classe]['impressoes'] += imp
            classificacoes[classe]['interacoes'] += post.get('interacoes', 0) or 0
    
    # Grafico por Formato (barras CSS)
    if formatos:
        max_imp = max(f['impressoes'] for f in formatos.values()) if formatos else 1
        
        html += """
        <h3 style="font-size: 11pt; margin: 20px 0 10px 0; color: #374151;">Impressoes por Formato</h3>
        <div class="bar-chart">
        """
        
        for formato, dados in sorted(formatos.items(), key=lambda x: x[1]['impressoes'], reverse=True):
            pct = (dados['impressoes'] / max_imp * 100) if max_imp > 0 else 0
            pct = max(pct, 5)  # Minimo 5% para visibilidade
            
            html += f"""
            <div class="bar-item">
                <div class="bar-label">{formato}</div>
                <div class="bar-container">
                    <div class="bar-fill" style="width: {pct}%;">
                        <span class="bar-value">{funcoes_auxiliares.formatar_numero(dados['impressoes'])}</span>
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
        
        # Tabela de formatos
        html += """
        <table style="margin-top: 15px;">
            <tr>
                <th>Formato</th>
                <th class="text-right">Impressoes</th>
                <th class="text-right">Alcance</th>
                <th class="text-right">Interacoes</th>
                <th class="text-right">Taxa Eng.</th>
            </tr>
        """
        
        for formato, dados in sorted(formatos.items(), key=lambda x: x[1]['impressoes'], reverse=True):
            taxa = (dados['interacoes'] / dados['impressoes'] * 100) if dados['impressoes'] > 0 else 0
            html += f"""
            <tr>
                <td>{formato}</td>
                <td class="text-right">{funcoes_auxiliares.formatar_numero(dados['impressoes'])}</td>
                <td class="text-right">{funcoes_auxiliares.formatar_numero(dados['alcance'])}</td>
                <td class="text-right">{funcoes_auxiliares.formatar_numero(dados['interacoes'])}</td>
                <td class="text-right">{taxa:.2f}%</td>
            </tr>
            """
        
        html += "</table>"
    
    # Grafico por Classificacao
    if classificacoes:
        max_imp_class = max(c['impressoes'] for c in classificacoes.values()) if classificacoes else 1
        
        html += """
        <h3 style="font-size: 11pt; margin: 25px 0 10px 0; color: #374151;">Impressoes por Classificacao</h3>
        <div class="bar-chart">
        """
        
        ordem = ['Nano', 'Micro', 'Mid', 'Macro', 'Mega']
        for classe in ordem:
            if classe in classificacoes:
                dados = classificacoes[classe]
                pct = (dados['impressoes'] / max_imp_class * 100) if max_imp_class > 0 else 0
                pct = max(pct, 5)
                
                html += f"""
                <div class="bar-item">
                    <div class="bar-label">{classe}</div>
                    <div class="bar-container">
                        <div class="bar-fill" style="width: {pct}%;">
                            <span class="bar-value">{funcoes_auxiliares.formatar_numero(dados['impressoes'])}</span>
                        </div>
                    </div>
                </div>
                """
        
        html += "</div>"
    
    html += "</div>"
    return html


def gerar_secao_influenciadores(campanha, primary_color):
    """Gera secao com lista de influenciadores"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">Performance por Influenciador</div>
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
            impressoes += (post.get('views', 0) or 0) + (post.get('impressoes', 0) or 0)
            interacoes += post.get('interacoes', 0) or 0
        
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
    
    dados_inf.sort(key=lambda x: x['impressoes'], reverse=True)
    
    # Top 10 em barras
    if dados_inf:
        max_imp = dados_inf[0]['impressoes'] if dados_inf else 1
        
        html += """
        <h3 style="font-size: 11pt; margin: 10px 0; color: #374151;">Top 10 por Impressoes</h3>
        <div class="bar-chart">
        """
        
        for d in dados_inf[:10]:
            pct = (d['impressoes'] / max_imp * 100) if max_imp > 0 else 0
            pct = max(pct, 5)
            
            html += f"""
            <div class="bar-item">
                <div class="bar-label" style="width: 120px;">{d['nome'][:15]}</div>
                <div class="bar-container">
                    <div class="bar-fill" style="width: {pct}%;">
                        <span class="bar-value">{funcoes_auxiliares.formatar_numero(d['impressoes'])}</span>
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
    
    # Tabela completa
    html += """
    <h3 style="font-size: 11pt; margin: 25px 0 10px 0; color: #374151;">Lista Completa</h3>
    <table>
        <tr>
            <th>Influenciador</th>
            <th class="text-center">Classe</th>
            <th class="text-right">Seguidores</th>
            <th class="text-center">Posts</th>
            <th class="text-right">Impressoes</th>
            <th class="text-right">Interacoes</th>
            <th class="text-right">Taxa Eng.</th>
        </tr>
    """
    
    for d in dados_inf:
        html += f"""
        <tr>
            <td>{d['nome']}</td>
            <td class="text-center">{d['classe']}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(d['seguidores'])}</td>
            <td class="text-center">{d['posts']}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(d['impressoes'])}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(d['interacoes'])}</td>
            <td class="text-right">{d['taxa']:.2f}%</td>
        </tr>
        """
    
    html += "</table></div>"
    return html


def gerar_secao_top_posts(campanha, primary_color):
    """Gera secao com top posts"""
    
    html = """
    <div class="section page-break">
        <div class="section-title">Top Posts</div>
        <table>
            <tr>
                <th>Influenciador</th>
                <th>Formato</th>
                <th class="text-center">Data</th>
                <th class="text-right">Impressoes</th>
                <th class="text-right">Alcance</th>
                <th class="text-right">Interacoes</th>
                <th class="text-right">Taxa Eng.</th>
            </tr>
    """
    
    posts = []
    for inf_camp in campanha.get('influenciadores', []):
        inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
        if not inf:
            continue
        
        for post in inf_camp.get('posts', []):
            imp = (post.get('views', 0) or 0) + (post.get('impressoes', 0) or 0)
            inter = post.get('interacoes', 0) or 0
            taxa = (inter / imp * 100) if imp > 0 else 0
            
            posts.append({
                'influenciador': inf['nome'],
                'formato': post.get('formato', '-'),
                'data': post.get('data_publicacao', '-'),
                'impressoes': imp,
                'alcance': post.get('alcance', 0) or 0,
                'interacoes': inter,
                'taxa': taxa
            })
    
    posts.sort(key=lambda x: x['impressoes'], reverse=True)
    
    for post in posts[:20]:
        html += f"""
        <tr>
            <td>{post['influenciador']}</td>
            <td>{post['formato']}</td>
            <td class="text-center">{post['data']}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(post['impressoes'])}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(post['alcance'])}</td>
            <td class="text-right">{funcoes_auxiliares.formatar_numero(post['interacoes'])}</td>
            <td class="text-right">{post['taxa']:.2f}%</td>
        </tr>
        """
    
    html += "</table></div>"
    return html
