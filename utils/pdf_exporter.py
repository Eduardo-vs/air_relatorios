"""
Modulo: Exportacao de Relatorios em PDF
Gera PDF completo com KPIs configuraveis
"""

import io
import base64
from datetime import datetime
import re
import json

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from utils import data_manager, funcoes_auxiliares


def formatar_numero(valor):
    if valor is None:
        return "0"
    if valor >= 1000000:
        return f"{valor/1000000:.1f}M"
    elif valor >= 1000:
        return f"{valor/1000:.1f}K"
    return str(int(valor))


def get_cor_classificacao(classif):
    cores = {
        'Nano': '#22c55e', 'Micro': '#3b82f6', 'Inter 1': '#8b5cf6',
        'Inter 2': '#a855f7', 'Macro': '#f97316', 'Mega 1': '#ef4444',
        'Mega 2': '#dc2626', 'Super Mega': '#991b1b', 'Mid': '#8b5cf6', 'Mega': '#ef4444'
    }
    return cores.get(classif, '#7c3aed')


def gerar_barra_horizontal(label, valor, max_valor, total=None, cor='#7c3aed'):
    pct = (valor / max_valor * 100) if max_valor > 0 else 0
    pct = max(pct, 5)
    pct_total = f'<span class="bar-pct">({valor/total*100:.1f}%)</span>' if total and total > 0 else ""
    return f'''<div class="bar-row"><div class="bar-label">{label}</div><div class="bar-container"><div class="bar-fill" style="width:{pct}%;background:{cor};"><span class="bar-value">{formatar_numero(valor)}</span>{pct_total}</div></div></div>'''


def gerar_barras_verticais(dados, total=None):
    if not dados:
        return '<p style="text-align:center;color:#9ca3af;">Sem dados</p>'
    max_val = max(d['valor'] for d in dados) if dados else 1
    html = '<div class="vertical-chart">'
    for d in dados:
        pct_altura = max((d['valor'] / max_val * 100) if max_val > 0 else 0, 8)
        altura = max(int(pct_altura * 1.4), 25)
        pct_total = f'<span class="v-bar-pct">{d["valor"]/total*100:.1f}%</span>' if total and total > 0 else ""
        html += f'''<div class="v-bar-item"><div class="v-bar" style="height:{altura}px;background:{d.get('cor','#7c3aed')};"><span class="v-bar-value">{formatar_numero(d['valor'])}</span>{pct_total}</div><div class="v-bar-label">{d['label']}</div></div>'''
    html += '</div>'
    return html


def gerar_insights_html(campanha_id, pagina):
    insights = data_manager.get_insights_campanha(campanha_id, pagina, apenas_ativos=True)
    if not insights:
        return ""
    html = '<div class="insights-section"><div class="subsection-title">Insights</div><div class="insights-grid">'
    for insight in insights[:6]:
        tipo = insight.get('tipo', 'info')
        titulo = insight.get('titulo', '')
        texto = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', insight.get('texto', ''))
        html += f'<div class="insight-card {tipo}"><div class="insight-title">{titulo}</div><div class="insight-text">{texto}</div></div>'
    html += '</div></div>'
    return html


def get_css(primary_color):
    return f'''
    @page {{ size: A4; margin: 1.5cm; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 9pt; line-height: 1.5; color: #1f2937; background: #fff; }}
    .header {{ text-align: center; padding: 25px 0; border-bottom: 4px solid {primary_color}; margin-bottom: 25px; }}
    .header h1 {{ color: {primary_color}; font-size: 26pt; margin-bottom: 8px; }}
    .header .subtitle {{ color: #6b7280; font-size: 12pt; }}
    .page-break {{ page-break-before: always; padding-top: 20px; }}
    .section {{ margin-bottom: 30px; }}
    .section-title {{ color: {primary_color}; font-size: 16pt; font-weight: 700; border-bottom: 3px solid {primary_color}; padding-bottom: 10px; margin-bottom: 20px; }}
    .subsection-title {{ font-size: 12pt; font-weight: 600; color: #374151; margin: 25px 0 15px 0; padding-bottom: 5px; border-bottom: 1px solid #e5e7eb; }}
    .big-number-card {{ background: linear-gradient(135deg, {primary_color} 0%, #a78bfa 100%); color: white; padding: 35px; border-radius: 16px; text-align: center; margin-bottom: 25px; }}
    .big-number-card .value {{ font-size: 52pt; font-weight: 800; line-height: 1; }}
    .big-number-card .label {{ font-size: 11pt; opacity: 0.9; text-transform: uppercase; margin-top: 8px; letter-spacing: 1px; }}
    .metrics-grid {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 25px; }}
    .metric-card {{ flex: 1; min-width: 100px; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; text-align: center; }}
    .metric-card .value {{ font-size: 18pt; font-weight: 700; color: {primary_color}; }}
    .metric-card .label {{ font-size: 7pt; color: #64748b; text-transform: uppercase; margin-top: 4px; }}
    .charts-row {{ display: flex; gap: 20px; margin-bottom: 25px; }}
    .chart-box {{ flex: 1; background: #f8fafc; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; }}
    .chart-title {{ font-size: 10pt; font-weight: 600; color: #374151; margin-bottom: 15px; text-align: center; }}
    .bar-chart {{ margin: 10px 0; }}
    .bar-row {{ display: flex; align-items: center; margin-bottom: 10px; }}
    .bar-label {{ width: 100px; font-size: 8pt; color: #374151; text-align: right; padding-right: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .bar-container {{ flex: 1; background: #e5e7eb; border-radius: 6px; height: 26px; overflow: hidden; }}
    .bar-fill {{ height: 100%; border-radius: 6px; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; min-width: 50px; }}
    .bar-value {{ font-size: 8pt; font-weight: 600; color: white; }}
    .bar-pct {{ font-size: 7pt; color: rgba(255,255,255,0.8); margin-left: 5px; }}
    .vertical-chart {{ display: flex; justify-content: space-around; align-items: flex-end; height: 180px; padding: 15px 10px; border-bottom: 2px solid #e5e7eb; margin-bottom: 10px; }}
    .v-bar-item {{ display: flex; flex-direction: column; align-items: center; flex: 1; max-width: 80px; }}
    .v-bar {{ width: 50px; border-radius: 6px 6px 0 0; display: flex; flex-direction: column; align-items: center; justify-content: flex-start; padding-top: 5px; min-height: 25px; }}
    .v-bar-value {{ font-size: 8pt; font-weight: 700; color: white; text-shadow: 0 1px 2px rgba(0,0,0,0.2); }}
    .v-bar-pct {{ font-size: 7pt; color: rgba(255,255,255,0.9); }}
    .v-bar-label {{ font-size: 8pt; color: #6b7280; margin-top: 8px; text-align: center; max-width: 70px; word-wrap: break-word; }}
    .insights-section {{ margin-top: 25px; }}
    .insights-grid {{ display: flex; flex-wrap: wrap; gap: 12px; }}
    .insight-card {{ flex: 1; min-width: 45%; background: #f0fdf4; border-left: 4px solid #22c55e; padding: 15px; border-radius: 0 10px 10px 0; }}
    .insight-card.alerta {{ background: #fffbeb; border-color: #f59e0b; }}
    .insight-card.destaque {{ background: #eff6ff; border-color: #3b82f6; }}
    .insight-card.info {{ background: #f5f3ff; border-color: {primary_color}; }}
    .insight-card.critico {{ background: #fef2f2; border-color: #ef4444; }}
    .insight-title {{ font-weight: 600; font-size: 10pt; margin-bottom: 6px; color: #1f2937; }}
    .insight-text {{ font-size: 8pt; color: #374151; line-height: 1.5; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 8pt; margin-top: 15px; }}
    th {{ background: {primary_color}; color: white; padding: 12px 10px; text-align: left; font-size: 8pt; text-transform: uppercase; font-weight: 600; }}
    td {{ padding: 10px; border-bottom: 1px solid #e5e7eb; }}
    tr:nth-child(even) {{ background: #f8fafc; }}
    .text-right {{ text-align: right; }}
    .text-center {{ text-align: center; }}
    .font-bold {{ font-weight: 600; }}
    .influ-card {{ display: flex; align-items: center; padding: 12px; border-bottom: 1px solid #e5e7eb; gap: 15px; }}
    .influ-avatar {{ width: 40px; height: 40px; background: {primary_color}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 14pt; }}
    .influ-info {{ flex: 1; }}
    .influ-name {{ font-weight: 600; font-size: 10pt; }}
    .influ-meta {{ font-size: 8pt; color: #6b7280; }}
    .influ-metrics {{ display: flex; gap: 20px; }}
    .influ-metric {{ text-align: center; }}
    .influ-metric-value {{ font-weight: 600; font-size: 10pt; color: {primary_color}; }}
    .influ-metric-label {{ font-size: 7pt; color: #6b7280; text-transform: uppercase; }}
    .comment-card {{ background: #f8fafc; border-radius: 10px; padding: 15px; margin-bottom: 12px; border-left: 3px solid {primary_color}; }}
    .comment-header {{ display: flex; justify-content: space-between; margin-bottom: 8px; }}
    .comment-author {{ font-weight: 600; color: {primary_color}; }}
    .comment-date {{ font-size: 8pt; color: #9ca3af; }}
    .comment-text {{ font-size: 9pt; color: #374151; line-height: 1.6; }}
    .glossary-item {{ margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e5e7eb; }}
    .glossary-term {{ font-weight: 600; color: {primary_color}; font-size: 10pt; margin-bottom: 4px; }}
    .glossary-def {{ font-size: 9pt; color: #4b5563; line-height: 1.5; }}
    .footer {{ text-align: center; color: #9ca3af; font-size: 8pt; padding: 25px 0; margin-top: 40px; border-top: 1px solid #e5e7eb; }}
    '''


def get_valor_kpi(dados, kpi_nome):
    """Retorna o valor do KPI selecionado"""
    kpi_map = {
        'Impressoes': 'impressoes',
        'Alcance': 'alcance',
        'Interacoes': 'interacoes',
        'Interacoes Qualificadas': 'interacoes_qualif',
        'Seguidores': 'seguidores',
        'Custo': 'custo',
        'Taxa Eng. Efetivo': 'taxa_eng',
        'Taxa Alcance': 'taxa_alcance',
        'Taxa de Interacoes Qualificadas': 'taxa_interacoes_qualif',
        'Taxa Eng.': 'taxa'
    }
    campo = kpi_map.get(kpi_nome, 'impressoes')
    
    # Calcular interacoes qualificadas se necessario
    if campo == 'interacoes_qualif':
        return max(0, dados.get('interacoes', 0) - dados.get('curtidas', 0))
    if campo == 'taxa_interacoes_qualif':
        inter = dados.get('interacoes', 0)
        curt = dados.get('curtidas', 0)
        return ((inter - curt) / inter * 100) if inter > 0 else 0
    
    return dados.get(campo, 0)


def gerar_pdf_relatorio(campanha_id: int, incluir_paginas: list = None, config_kpis: dict = None) -> bytes:
    """Gera PDF completo do relatorio com KPIs configuraveis"""
    
    if not WEASYPRINT_AVAILABLE:
        raise ImportError("WeasyPrint nao instalado")
    
    campanha = data_manager.get_campanha(campanha_id)
    if not campanha:
        raise ValueError("Campanha nao encontrada")
    
    cliente = None
    if campanha.get('cliente_id'):
        cliente = data_manager.get_cliente(campanha['cliente_id'])
    
    metricas = data_manager.calcular_metricas_campanha(campanha)
    
    # Config padrao de KPIs
    if config_kpis is None:
        config_kpis = {
            'big_numbers': {'barras': 'Impressoes', 'classificacao': 'Impressoes'},
            'kpis_influenciador': {'barras': 'Impressoes', 'linha': 'Taxa Eng. Efetivo'},
            'top_performance': {'ordenar_ranking': 'Interacoes', 'ordenar_posts': 'Impressoes'}
        }
    
    primary_color = '#7c3aed'
    try:
        cfg = data_manager.get_configuracao('primary_color')
        if cfg:
            primary_color = cfg
    except:
        pass
    
    # Coletar dados
    todos_posts = []
    dados_por_influ = []
    dados_por_formato = {}
    dados_por_classif = {}
    
    for inf_camp in campanha.get('influenciadores', []):
        inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
        
        nome_inf = inf.get('nome', '') if inf else inf_camp.get('nome', 'Desconhecido')
        usuario_inf = inf.get('usuario', '') if inf else inf_camp.get('usuario', '')
        classif = inf.get('classificacao', 'Outro') if inf else 'Outro'
        seguidores = inf.get('seguidores', 0) if inf else inf_camp.get('seguidores', 0)
        custo = inf_camp.get('custo', 0) or 0
        
        posts = inf_camp.get('posts', [])
        
        inf_impressoes = inf_alcance = inf_interacoes = inf_curtidas = 0
        inf_comentarios = inf_saves = inf_compartilhamentos = 0
        
        for post in posts:
            views = post.get('views', 0) or 0
            imp_post = post.get('impressoes', 0) or 0
            imp = views + imp_post
            alc = post.get('alcance', 0) or 0
            inter = post.get('interacoes', 0) or 0
            curt = post.get('curtidas', 0) or 0
            coments = post.get('comentarios', 0)
            if isinstance(coments, list):
                coments = len(coments)
            coments = (coments or 0) + (post.get('comentarios_qtd', 0) or 0)
            saves = post.get('saves', 0) or 0
            compart = post.get('compartilhamentos', 0) or 0
            formato = post.get('formato', 'Outro') or 'Outro'
            
            # Por formato
            if formato not in dados_por_formato:
                dados_por_formato[formato] = {'impressoes': 0, 'alcance': 0, 'interacoes': 0, 'curtidas': 0, 'posts': 0}
            dados_por_formato[formato]['impressoes'] += imp
            dados_por_formato[formato]['alcance'] += alc
            dados_por_formato[formato]['interacoes'] += inter
            dados_por_formato[formato]['curtidas'] += curt
            dados_por_formato[formato]['posts'] += 1
            
            # Por classificacao
            if classif not in dados_por_classif:
                dados_por_classif[classif] = {'impressoes': 0, 'alcance': 0, 'interacoes': 0, 'curtidas': 0, 'posts': 0}
            dados_por_classif[classif]['impressoes'] += imp
            dados_por_classif[classif]['alcance'] += alc
            dados_por_classif[classif]['interacoes'] += inter
            dados_por_classif[classif]['curtidas'] += curt
            dados_por_classif[classif]['posts'] += 1
            
            inf_impressoes += imp
            inf_alcance += alc
            inf_interacoes += inter
            inf_curtidas += curt
            inf_comentarios += coments
            inf_saves += saves
            inf_compartilhamentos += compart
            
            todos_posts.append({
                'influenciador': nome_inf, 'usuario': usuario_inf, 'classificacao': classif,
                'formato': formato, 'data': post.get('data_publicacao', ''),
                'impressoes': imp, 'alcance': alc, 'interacoes': inter, 'curtidas': curt,
                'comentarios': coments, 'saves': saves, 'compartilhamentos': compart,
                'taxa': (inter / imp * 100) if imp > 0 else 0
            })
        
        if len(posts) > 0 or inf_impressoes > 0:
            taxa_eng = (inf_interacoes / inf_impressoes * 100) if inf_impressoes > 0 else 0
            taxa_alcance = (inf_alcance / seguidores * 100) if seguidores > 0 else 0
            taxa_interacoes_qualif = ((inf_interacoes - inf_curtidas) / inf_interacoes * 100) if inf_interacoes > 0 else 0
            dados_por_influ.append({
                'nome': nome_inf, 'usuario': usuario_inf, 'classificacao': classif,
                'seguidores': seguidores or 0, 'custo': custo, 'posts': len(posts),
                'impressoes': inf_impressoes, 'alcance': inf_alcance, 'interacoes': inf_interacoes,
                'curtidas': inf_curtidas, 'comentarios': inf_comentarios, 'saves': inf_saves,
                'compartilhamentos': inf_compartilhamentos, 'taxa_eng': taxa_eng, 'taxa_alcance': taxa_alcance,
                'interacoes_qualif': max(0, inf_interacoes - inf_curtidas),
                'taxa_interacoes_qualif': taxa_interacoes_qualif
            })
    
    comentarios = data_manager.get_comentarios_campanha(campanha_id)
    
    # Gerar HTML
    paginas = incluir_paginas or ['big_numbers', 'kpis_influenciador', 'top_performance', 'lista_influenciadores', 'comentarios', 'glossario']
    css = get_css(primary_color)
    nome_cliente = cliente['nome'] if cliente else ''
    data_inicio = funcoes_auxiliares.formatar_data_br(campanha.get('data_inicio', ''))
    data_fim = funcoes_auxiliares.formatar_data_br(campanha.get('data_fim', ''))
    
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Relatorio - {campanha['nome']}</title><style>{css}</style></head><body>
    <div class="header"><h1>{campanha['nome']}</h1><div class="subtitle">{nome_cliente} | {data_inicio} a {data_fim}</div></div>'''
    
    # ========== BIG NUMBERS ==========
    if 'big_numbers' in paginas:
        kpi_barras = config_kpis.get('big_numbers', {}).get('barras', 'Impressoes')
        kpi_classif = config_kpis.get('big_numbers', {}).get('classificacao', 'Impressoes')
        
        total_impressoes = metricas['total_views'] + metricas['total_impressoes']
        html += f'''<div class="section"><div class="section-title">Big Numbers</div>
        <div class="big-number-card"><div class="value">{metricas['engajamento_efetivo']:.2f}%</div><div class="label">Taxa de Engajamento Efetivo</div></div>
        <div class="metrics-grid">
            <div class="metric-card"><div class="value">{metricas['total_influenciadores']}</div><div class="label">Influenciadores</div></div>
            <div class="metric-card"><div class="value">{metricas['total_posts']}</div><div class="label">Posts</div></div>
            <div class="metric-card"><div class="value">{formatar_numero(total_impressoes)}</div><div class="label">Impressoes</div></div>
            <div class="metric-card"><div class="value">{formatar_numero(metricas['total_alcance'])}</div><div class="label">Alcance</div></div>
            <div class="metric-card"><div class="value">{formatar_numero(metricas['total_interacoes'])}</div><div class="label">Interacoes</div></div>
        </div>
        <div class="metrics-grid">
            <div class="metric-card"><div class="value">{formatar_numero(metricas['total_curtidas'])}</div><div class="label">Curtidas</div></div>
            <div class="metric-card"><div class="value">{formatar_numero(metricas['total_comentarios'])}</div><div class="label">Comentarios</div></div>
            <div class="metric-card"><div class="value">{formatar_numero(metricas.get('total_compartilhamentos', 0))}</div><div class="label">Compartilh.</div></div>
            <div class="metric-card"><div class="value">{formatar_numero(metricas.get('total_saves', 0))}</div><div class="label">Saves</div></div>
            <div class="metric-card"><div class="value">{metricas['taxa_alcance']:.1f}%</div><div class="label">Taxa Alcance</div></div>
        </div>
        <div class="subsection-title">Graficos</div><div class="charts-row">'''
        
        # Grafico formato com KPI selecionado
        html += f'<div class="chart-box"><div class="chart-title">{kpi_barras} por Formato</div>'
        if dados_por_formato:
            dados_barras = []
            for f, d in dados_por_formato.items():
                valor = get_valor_kpi(d, kpi_barras)
                dados_barras.append({'label': f, 'valor': valor, 'cor': primary_color})
            dados_barras.sort(key=lambda x: x['valor'], reverse=True)
            total_fmt = sum(d['valor'] for d in dados_barras)
            html += gerar_barras_verticais(dados_barras, total_fmt)
        else:
            html += '<p style="text-align:center;color:#9ca3af;">Sem dados</p>'
        html += '</div>'
        
        # Grafico classificacao com KPI selecionado
        html += f'<div class="chart-box"><div class="chart-title">{kpi_classif} por Classificacao</div>'
        if dados_por_classif:
            dados_barras = []
            for c, d in dados_por_classif.items():
                valor = get_valor_kpi(d, kpi_classif)
                dados_barras.append({'label': c, 'valor': valor, 'cor': get_cor_classificacao(c)})
            dados_barras.sort(key=lambda x: x['valor'], reverse=True)
            total_class = sum(d['valor'] for d in dados_barras)
            html += gerar_barras_verticais(dados_barras, total_class)
        else:
            html += '<p style="text-align:center;color:#9ca3af;">Sem dados</p>'
        html += '</div></div>'
        html += gerar_insights_html(campanha['id'], 'big_numbers')
        html += '</div>'
    
    # ========== KPIs POR INFLUENCIADOR ==========
    if 'kpis_influenciador' in paginas:
        kpi_barras = config_kpis.get('kpis_influenciador', {}).get('barras', 'Impressoes')
        kpi_linha = config_kpis.get('kpis_influenciador', {}).get('linha', 'Taxa Eng. Efetivo')
        
        html += f'<div class="section page-break"><div class="section-title">KPIs por Influenciador</div>'
        
        # Ordenar por KPI selecionado
        kpi_campo_map = {'Impressoes': 'impressoes', 'Alcance': 'alcance', 'Interacoes': 'interacoes', 'Seguidores': 'seguidores'}
        campo_ordem = kpi_campo_map.get(kpi_barras, 'impressoes')
        top15 = sorted(dados_por_influ, key=lambda x: x.get(campo_ordem, 0), reverse=True)[:15]
        
        if top15:
            html += f'<div class="subsection-title">Top 15 por {kpi_barras}</div><div class="chart-box"><div class="bar-chart">'
            max_val = top15[0].get(campo_ordem, 1) if top15 else 1
            total_val = sum(i.get(campo_ordem, 0) for i in top15)
            for inf in top15:
                valor = inf.get(campo_ordem, 0)
                html += gerar_barra_horizontal(inf['nome'][:18], valor, max_val, total_val, get_cor_classificacao(inf['classificacao']))
            html += '</div></div>'
            
            # Grafico secundario com KPI linha
            kpi_linha_campo = {'Taxa Eng. Efetivo': 'taxa_eng', 'Taxa Alcance': 'taxa_alcance', 'Taxa de Interacoes Qualificadas': 'taxa_interacoes_qualif'}
            campo_linha = kpi_linha_campo.get(kpi_linha, 'taxa_eng')
            
            html += f'<div class="subsection-title">{kpi_linha} por Influenciador</div><div class="chart-box"><div class="bar-chart">'
            top15_linha = sorted(top15, key=lambda x: x.get(campo_linha, 0), reverse=True)
            max_linha = top15_linha[0].get(campo_linha, 1) if top15_linha else 1
            for inf in top15_linha:
                valor = inf.get(campo_linha, 0)
                pct = max((valor / max_linha * 100) if max_linha > 0 else 0, 5)
                html += f'<div class="bar-row"><div class="bar-label">{inf["nome"][:18]}</div><div class="bar-container"><div class="bar-fill" style="width:{pct}%;background:{get_cor_classificacao(inf["classificacao"])};"><span class="bar-value">{valor:.2f}%</span></div></div></div>'
            html += '</div></div>'
        
        html += '''<div class="subsection-title">Detalhamento</div><table><tr><th>Influenciador</th><th class="text-center">Classe</th><th class="text-right">Seguidores</th><th class="text-center">Posts</th><th class="text-right">Impressoes</th><th class="text-right">Alcance</th><th class="text-right">Interacoes</th><th class="text-right">Taxa</th></tr>'''
        for inf in top15:
            html += f'<tr><td class="font-bold">{inf["nome"]}</td><td class="text-center">{inf["classificacao"]}</td><td class="text-right">{formatar_numero(inf["seguidores"])}</td><td class="text-center">{inf["posts"]}</td><td class="text-right">{formatar_numero(inf["impressoes"])}</td><td class="text-right">{formatar_numero(inf["alcance"])}</td><td class="text-right">{formatar_numero(inf["interacoes"])}</td><td class="text-right">{inf["taxa_eng"]:.2f}%</td></tr>'
        html += '</table>'
        html += gerar_insights_html(campanha['id'], 'kpis_influenciador')
        html += '</div>'
    
    # ========== TOP PERFORMANCE ==========
    if 'top_performance' in paginas:
        kpi_ranking = config_kpis.get('top_performance', {}).get('ordenar_ranking', 'Interacoes')
        kpi_posts = config_kpis.get('top_performance', {}).get('ordenar_posts', 'Impressoes')
        
        html += '<div class="section page-break"><div class="section-title">Top Performance</div>'
        
        # Ordenar ranking pelo KPI selecionado
        ranking_map = {'Interacoes': 'interacoes', 'Impressoes': 'impressoes', 'Alcance': 'alcance', 'Taxa Eng. Efetivo': 'taxa_eng', 'Custo': 'custo'}
        campo_ranking = ranking_map.get(kpi_ranking, 'interacoes')
        top20 = sorted(dados_por_influ, key=lambda x: x.get(campo_ranking, 0), reverse=True)[:20]
        
        if top20:
            html += f'<div class="subsection-title">Ranking por {kpi_ranking}</div>'
            for i, inf in enumerate(top20, 1):
                inicial = inf['nome'][0].upper() if inf['nome'] else '?'
                custo_fmt = f"R$ {inf.get('custo', 0):,.0f}".replace(",", ".")
                valor_destaque = inf.get(campo_ranking, 0)
                if campo_ranking == 'taxa_eng':
                    valor_fmt = f"{valor_destaque:.2f}%"
                elif campo_ranking == 'custo':
                    valor_fmt = custo_fmt
                else:
                    valor_fmt = formatar_numero(valor_destaque)
                html += f'''<div class="influ-card"><div style="font-size:14pt;font-weight:600;color:#6b7280;width:30px;">#{i}</div><div class="influ-avatar">{inicial}</div><div class="influ-info"><div class="influ-name">{inf['nome']}</div><div class="influ-meta">@{inf['usuario']} | {inf['classificacao']} | {formatar_numero(inf['seguidores'])} seg</div></div><div class="influ-metrics"><div class="influ-metric"><div class="influ-metric-value">{custo_fmt}</div><div class="influ-metric-label">Invest.</div></div><div class="influ-metric"><div class="influ-metric-value">{formatar_numero(inf['interacoes'])}</div><div class="influ-metric-label">Interacoes</div></div><div class="influ-metric"><div class="influ-metric-value">{inf['taxa_eng']:.2f}%</div><div class="influ-metric-label">Taxa</div></div><div class="influ-metric"><div class="influ-metric-value">{formatar_numero(inf['impressoes'])}</div><div class="influ-metric-label">Impressoes</div></div></div></div>'''
        
        # Ordenar posts pelo KPI selecionado
        posts_map = {'Impressoes': 'impressoes', 'Alcance': 'alcance', 'Interacoes': 'interacoes', 'Taxa Eng.': 'taxa'}
        campo_posts = posts_map.get(kpi_posts, 'impressoes')
        top_posts = sorted(todos_posts, key=lambda x: x.get(campo_posts, 0), reverse=True)[:15]
        
        if top_posts:
            html += f'''<div class="subsection-title">Top Posts por {kpi_posts}</div><table><tr><th>Influenciador</th><th>Formato</th><th class="text-center">Data</th><th class="text-right">Impressoes</th><th class="text-right">Alcance</th><th class="text-right">Interacoes</th><th class="text-right">Taxa</th></tr>'''
            for p in top_posts:
                html += f'<tr><td class="font-bold">{p["influenciador"]}</td><td>{p["formato"]}</td><td class="text-center">{p["data"]}</td><td class="text-right">{formatar_numero(p["impressoes"])}</td><td class="text-right">{formatar_numero(p["alcance"])}</td><td class="text-right">{formatar_numero(p["interacoes"])}</td><td class="text-right">{p["taxa"]:.2f}%</td></tr>'
            html += '</table>'
        html += gerar_insights_html(campanha['id'], 'top_performance')
        html += '</div>'
    
    # ========== LISTA INFLUENCIADORES ==========
    if 'lista_influenciadores' in paginas:
        html += '''<div class="section page-break"><div class="section-title">Lista de Influenciadores</div><table><tr><th>Influenciador</th><th>Usuario</th><th class="text-center">Classe</th><th class="text-right">Seguidores</th><th class="text-right">Custo</th><th class="text-center">Posts</th><th class="text-right">Impressoes</th><th class="text-right">Alcance</th><th class="text-right">Interacoes</th><th class="text-right">Taxa</th></tr>'''
        for inf in sorted(dados_por_influ, key=lambda x: x['impressoes'], reverse=True):
            custo_fmt = f"R$ {inf.get('custo', 0):,.0f}".replace(",", ".")
            html += f'<tr><td class="font-bold">{inf["nome"]}</td><td>@{inf["usuario"]}</td><td class="text-center">{inf["classificacao"]}</td><td class="text-right">{formatar_numero(inf["seguidores"])}</td><td class="text-right">{custo_fmt}</td><td class="text-center">{inf["posts"]}</td><td class="text-right">{formatar_numero(inf["impressoes"])}</td><td class="text-right">{formatar_numero(inf["alcance"])}</td><td class="text-right">{formatar_numero(inf["interacoes"])}</td><td class="text-right">{inf["taxa_eng"]:.2f}%</td></tr>'
        html += '</table></div>'
    
    # ========== COMENTARIOS ==========
    if 'comentarios' in paginas:
        html += '<div class="section page-break"><div class="section-title">Comentarios</div>'
        if comentarios:
            for com in comentarios:
                data_str = com.get('created_at', '')
                if data_str:
                    try:
                        dt = datetime.fromisoformat(data_str.replace('Z', ''))
                        data_str = dt.strftime('%d/%m/%Y %H:%M')
                    except:
                        pass
                html += f'<div class="comment-card"><div class="comment-header"><span class="comment-author">{com.get("autor", "Autor")}</span><span class="comment-date">{data_str}</span></div><div class="comment-text">{com.get("texto", "")}</div></div>'
        else:
            html += '<p style="text-align:center;color:#9ca3af;padding:30px;">Nenhum comentario registrado</p>'
        html += '</div>'
    
    # ========== GLOSSARIO ==========
    if 'glossario' in paginas:
        glossario = [
            ("Impressoes", "Numero total de vezes que o conteudo foi exibido"),
            ("Alcance", "Numero de contas unicas que visualizaram o conteudo"),
            ("Interacoes", "Soma de curtidas, comentarios, compartilhamentos e saves"),
            ("Interacoes Qualificadas", "Interacoes excluindo curtidas (comentarios + compartilhamentos + saves)"),
            ("Taxa de Engajamento Efetivo", "Interacoes / Impressoes x 100"),
            ("Taxa de Alcance", "Alcance / Seguidores x 100"),
            ("Taxa de Interacoes Qualificadas", "(Interacoes - Curtidas) / Interacoes x 100"),
            ("Classificacao", "Categoria do influenciador baseada no numero de seguidores"),
        ]
        html += '<div class="section page-break"><div class="section-title">Glossario</div>'
        for termo, definicao in glossario:
            html += f'<div class="glossary-item"><div class="glossary-term">{termo}</div><div class="glossary-def">{definicao}</div></div>'
        html += '</div>'
    
    html += f'<div class="footer">Relatorio gerado por <strong>AIR</strong> em {datetime.now().strftime("%d/%m/%Y %H:%M")}</div></body></html>'
    
    return HTML(string=html).write_pdf()
