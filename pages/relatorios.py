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
from typing import List, Dict
import base64
import requests
import json
import time
from utils import data_manager, funcoes_auxiliares

# ========================================
# INSIGHTS POR IA - COM PERSISTENCIA
# ========================================

WEBHOOK_IA_URL = "https://n8n.air.com.vc/webhook/e19fe530-62b6-44af-b6d1-3aeed59cfe0b"

def buscar_insights_ia(pagina: str, dados: dict, campanha_id: int) -> List[dict]:
    """
    Busca insights da IA via webhook
    Retorna lista de insights ou None em caso de erro
    """
    try:
        payload = {
            "pagina": pagina,
            "campanha_id": campanha_id,
            "dados": dados,
            "timestamp": datetime.now().isoformat()
        }
        
        # Timeout alto e retries
        for tentativa in range(3):
            try:
                response = requests.post(
                    WEBHOOK_IA_URL,
                    json=payload,
                    timeout=120,  # 2 minutos de timeout
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    resultado = response.json()
                    return resultado.get('insights', [])
                else:
                    if tentativa < 2:
                        time.sleep(2)
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                if tentativa < 2:
                    time.sleep(2)
                    continue
                return None
            except requests.exceptions.RequestException:
                if tentativa < 2:
                    time.sleep(2)
                    continue
                return None
                
    except Exception:
        return None


def render_secao_insights(pagina: str, dados: dict, campanha_id: int):
    """
    Renderiza seção completa de insights com:
    - Insights salvos do banco (ativos e inativos)
    - Botão para gerar novos insights via IA
    - Edição/exclusão de insights
    - Adição manual de insights
    """
    st.markdown("---")
    st.markdown("### 💡 Insights da Campanha")
    
    # Controle de estado para geração de insights
    status_key = f"ia_status_{campanha_id}_{pagina}"
    error_key = f"ia_error_{campanha_id}_{pagina}"
    
    # Botões de ação
    col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1, 1, 1])
    
    with col1:
        # Filtro para mostrar inativos
        mostrar_inativos = st.checkbox("Mostrar excluídos", key=f"show_inativos_{pagina}_{campanha_id}")
    
    with col2:
        if st.button("🤖 Gerar com IA", key=f"btn_gerar_ia_{pagina}_{campanha_id}", help="Gerar novos insights usando IA"):
            st.session_state[status_key] = 'pending'
            st.rerun()
    
    with col3:
        if st.button("➕ Adicionar", key=f"btn_add_insight_{pagina}_{campanha_id}", help="Adicionar insight manualmente"):
            st.session_state[f'adding_insight_{pagina}_{campanha_id}'] = True
            st.rerun()
    
    with col4:
        if st.button("📜 Histórico", key=f"btn_hist_{pagina}_{campanha_id}", help="Ver histórico de insights"):
            st.session_state[f'show_historico_{pagina}_{campanha_id}'] = not st.session_state.get(f'show_historico_{pagina}_{campanha_id}', False)
            st.rerun()
    
    with col5:
        # Botão para expandir/colapsar todos
        if st.button("📝 Editar Todos", key=f"btn_edit_all_{pagina}_{campanha_id}", help="Expandir modo de edição"):
            st.session_state[f'edit_mode_{pagina}_{campanha_id}'] = not st.session_state.get(f'edit_mode_{pagina}_{campanha_id}', False)
            st.rerun()
    
    # Processar geração de insights IA
    status = st.session_state.get(status_key, 'idle')
    
    if status == 'pending':
        with st.spinner("🤖 Analisando dados com IA... Isso pode levar alguns segundos."):
            novos_insights = buscar_insights_ia(pagina, dados, campanha_id)
            
            if novos_insights:
                # Salvar no banco (mantém manuais, substitui IA)
                data_manager.atualizar_insights_ia(campanha_id, pagina, novos_insights)
                st.session_state[status_key] = 'done'
                st.success(f"✅ {len(novos_insights)} insights gerados com sucesso!")
                time.sleep(1)
                st.rerun()
            else:
                st.session_state[status_key] = 'error'
                st.session_state[error_key] = "Não foi possível gerar insights. Tente novamente."
                st.rerun()
    
    elif status == 'error':
        erro = st.session_state.get(error_key, 'Erro desconhecido')
        st.warning(f"⚠️ {erro}")
        st.session_state[status_key] = 'idle'
    
    # Formulário para adicionar insight manual
    if st.session_state.get(f'adding_insight_{pagina}_{campanha_id}', False):
        render_form_adicionar_insight(pagina, campanha_id)
    
    # Mostrar histórico
    if st.session_state.get(f'show_historico_{pagina}_{campanha_id}', False):
        render_historico_insights(pagina, campanha_id)
    
    # Buscar insights salvos do banco (ativos ou todos)
    insights = data_manager.get_insights_campanha(campanha_id, pagina, apenas_ativos=not mostrar_inativos)
    
    if not insights:
        st.info("Nenhum insight cadastrado ainda. Clique em '🤖 Gerar com IA' ou '➕ Adicionar' para começar.")
        return
    
    # Modo de edição
    edit_mode = st.session_state.get(f'edit_mode_{pagina}_{campanha_id}', False)
    
    # Separar insights por fonte
    insights_ia = [i for i in insights if i.get('fonte') == 'ia']
    insights_manuais = [i for i in insights if i.get('fonte') != 'ia']
    
    # Renderizar insights IA
    if insights_ia:
        st.markdown("**Insights Automáticos (IA):**")
        render_lista_insights(insights_ia, pagina, campanha_id, editavel=True)
    
    # Renderizar insights manuais
    if insights_manuais:
        st.markdown("**Insights Manuais:**")
        render_lista_insights(insights_manuais, pagina, campanha_id, editavel=True)


def render_lista_insights(insights: List[dict], pagina: str, campanha_id: int, editavel: bool = True):
    """Renderiza lista de insights com opções de edição"""
    cols_per_row = 2
    
    for i in range(0, len(insights), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(insights):
                insight = insights[i + j]
                with col:
                    render_card_insight_editavel(insight, pagina, campanha_id, editavel)


def render_card_insight_editavel(insight: dict, pagina: str, campanha_id: int, editavel: bool = True):
    """Renderiza um card de insight com opções de edição"""
    insight_id = insight.get('id')
    tipo = insight.get('tipo', 'info')
    titulo = insight.get('titulo', 'Insight')
    texto = insight.get('texto', '')
    icone = insight.get('icone', '💡')
    fonte = insight.get('fonte', 'ia')
    ativo = insight.get('ativo', 1)
    created_at = insight.get('created_at', '')
    updated_at = insight.get('updated_at', '')
    
    # Formatar data
    data_criacao = ''
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00')) if 'T' in created_at else datetime.strptime(created_at[:19], '%Y-%m-%d %H:%M:%S')
            data_criacao = dt.strftime('%d/%m/%Y %H:%M')
        except:
            data_criacao = created_at[:16] if len(created_at) > 16 else created_at
    
    cores = {
        'sucesso': '#dcfce7',
        'alerta': '#fef3c7',
        'info': '#dbeafe',
        'destaque': '#f3e8ff',
        'critico': '#fee2e2'
    }
    
    cor_fundo = cores.get(tipo, '#f3f4f6')
    
    # Se inativo, deixar mais transparente
    if not ativo:
        cor_fundo = '#e5e7eb'
    
    # Verificar se está em modo de edição
    editing_key = f'editing_insight_{insight_id}'
    
    if st.session_state.get(editing_key, False):
        # Modo de edição
        with st.container():
            st.markdown(f"**Editando Insight #{insight_id}**")
            st.caption(f"📅 Criado em: {data_criacao}")
            
            col1, col2 = st.columns(2)
            with col1:
                novo_tipo = st.selectbox("Tipo:", ['sucesso', 'alerta', 'info', 'destaque', 'critico'], 
                                        index=['sucesso', 'alerta', 'info', 'destaque', 'critico'].index(tipo) if tipo in ['sucesso', 'alerta', 'info', 'destaque', 'critico'] else 2,
                                        key=f"edit_tipo_{insight_id}")
            with col2:
                novo_icone = st.text_input("Ícone:", value=icone, key=f"edit_icone_{insight_id}")
            
            novo_titulo = st.text_input("Título:", value=titulo, key=f"edit_titulo_{insight_id}")
            novo_texto = st.text_area("Texto:", value=texto, height=100, key=f"edit_texto_{insight_id}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar", key=f"save_insight_{insight_id}"):
                    data_manager.atualizar_insight(insight_id, {
                        'tipo': novo_tipo,
                        'icone': novo_icone,
                        'titulo': novo_titulo,
                        'texto': novo_texto
                    })
                    st.session_state[editing_key] = False
                    st.rerun()
            with col2:
                if st.button("❌ Cancelar", key=f"cancel_insight_{insight_id}"):
                    st.session_state[editing_key] = False
                    st.rerun()
    else:
        # Modo de visualização
        fonte_badge = "🤖" if fonte == 'ia' else "✍️"
        status_badge = "" if ativo else "🚫 "
        opacity = "1" if ativo else "0.6"
        
        st.markdown(f"""
        <div style="background: {cor_fundo}; border-radius: 12px; padding: 1rem; margin-bottom: 0.5rem; position: relative; opacity: {opacity};">
            <div style="position: absolute; top: 0.5rem; right: 0.5rem; font-size: 0.7rem; opacity: 0.6;">{fonte_badge}</div>
            <div style="font-size: 1.2rem; margin-bottom: 0.3rem;">{status_badge}{icone} <strong>{titulo}</strong></div>
            <div style="font-size: 0.9rem; color: #374151; margin-bottom: 0.5rem;">{texto}</div>
            <div style="font-size: 0.7rem; color: #6b7280;">📅 {data_criacao}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if editavel:
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✏️ Editar", key=f"btn_edit_{insight_id}", help="Editar insight"):
                    st.session_state[editing_key] = True
                    st.rerun()
            with col2:
                if ativo:
                    if st.button("🗑️ Excluir", key=f"btn_del_{insight_id}", help="Excluir insight"):
                        data_manager.excluir_insight(insight_id)
                        st.rerun()
                else:
                    if st.button("♻️ Restaurar", key=f"btn_restore_{insight_id}", help="Restaurar insight"):
                        data_manager.atualizar_insight(insight_id, {'ativo': 1})
                        st.rerun()
            with col3:
                if not ativo:
                    if st.button("🗑️ Apagar", key=f"btn_delete_perm_{insight_id}", help="Apagar permanentemente"):
                        data_manager.excluir_insight(insight_id, soft_delete=False)
                        st.rerun()


def render_form_adicionar_insight(pagina: str, campanha_id: int):
    """Formulário para adicionar insight manualmente"""
    st.markdown("---")
    st.markdown("**➕ Adicionar Insight Manual**")
    
    with st.form(key=f"form_add_insight_{pagina}_{campanha_id}"):
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox("Tipo:", ['sucesso', 'alerta', 'info', 'destaque', 'critico'])
        with col2:
            icone = st.text_input("Ícone:", value='💡')
        
        titulo = st.text_input("Título:", placeholder="Ex: Meta de Impressões Superada")
        texto = st.text_area("Texto:", placeholder="Descrição detalhada do insight...", height=100)
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Salvar Insight")
        with col2:
            cancelled = st.form_submit_button("❌ Cancelar")
        
        if submitted and titulo and texto:
            data_manager.adicionar_insight(campanha_id, pagina, {
                'tipo': tipo,
                'icone': icone,
                'titulo': titulo,
                'texto': texto
            }, fonte='manual')
            st.session_state[f'adding_insight_{pagina}_{campanha_id}'] = False
            st.success("✅ Insight adicionado!")
            time.sleep(0.5)
            st.rerun()
        
        if cancelled:
            st.session_state[f'adding_insight_{pagina}_{campanha_id}'] = False
            st.rerun()


def render_historico_insights(pagina: str, campanha_id: int):
    """Mostra histórico de insights com opção de restaurar"""
    st.markdown("---")
    st.markdown("**📜 Histórico de Insights**")
    
    historico = data_manager.get_historico_insights(campanha_id, pagina, limit=5)
    
    if not historico:
        st.info("Nenhum histórico disponível.")
        return
    
    for item in historico:
        created_at = item.get('created_at', '')[:16].replace('T', ' ')
        qtd_insights = len(item.get('insights', []))
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"📅 {created_at} - {qtd_insights} insights")
        with col2:
            with st.expander("Ver"):
                for ins in item.get('insights', []):
                    st.write(f"{ins.get('icone', '💡')} **{ins.get('titulo', '')}**")
                    st.caption(ins.get('texto', '')[:100] + "...")
        with col3:
            if st.button("🔄 Restaurar", key=f"restore_{item['id']}"):
                data_manager.restaurar_insights_historico(item['id'])
                st.success("✅ Insights restaurados!")
                time.sleep(0.5)
                st.rerun()


def render_card_insight(insight: dict):
    """
    Renderiza um card de insight simples (sem edição)
    Mantido para compatibilidade
    """
    tipo = insight.get('tipo', 'info')
    titulo = insight.get('titulo', 'Insight')
    texto = insight.get('texto', '')
    icone = insight.get('icone', '💡')
    
    cores = {
        'sucesso': '#dcfce7',
        'alerta': '#fef3c7',
        'info': '#dbeafe',
        'destaque': '#f3e8ff',
        'critico': '#fee2e2'
    }
    
    cor_fundo = cores.get(tipo, '#f3f4f6')
    
    st.markdown(f"""
    <div style="background: {cor_fundo}; border-radius: 12px; padding: 1rem; margin-bottom: 0.5rem;">
        <div style="font-size: 1.2rem; margin-bottom: 0.3rem;">{icone} <strong>{titulo}</strong></div>
        <div style="font-size: 0.9rem; color: #374151;">{texto}</div>
    </div>
    """, unsafe_allow_html=True)


def preparar_dados_pagina(pagina: str, campanhas_list: list, metricas: dict = None) -> dict:
    """
    Prepara os dados de uma página para enviar à IA
    """
    dados = {
        "pagina": pagina,
        "campanhas": [],
        "metricas_gerais": metricas or {},
        "influenciadores": [],
        "posts": []
    }
    
    for camp in campanhas_list:
        dados["campanhas"].append({
            "id": camp.get('id'),
            "nome": camp.get('nome'),
            "cliente": camp.get('cliente_nome'),
            "data_inicio": camp.get('data_inicio'),
            "data_fim": camp.get('data_fim'),
            "is_aon": camp.get('is_aon', False),
            "estimativa_alcance": camp.get('estimativa_alcance', 0),
            "estimativa_impressoes": camp.get('estimativa_impressoes', 0),
            "investimento_total": camp.get('investimento_total', 0)
        })
        
        for inf_camp in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
            if inf:
                inf_dados = {
                    "nome": inf.get('nome'),
                    "usuario": inf.get('usuario'),
                    "classificacao": inf.get('classificacao'),
                    "seguidores": inf.get('seguidores', 0),
                    "air_score": inf.get('air_score', 0),
                    "custo": inf_camp.get('custo', 0),
                    "posts": []
                }
                
                for post in inf_camp.get('posts', []):
                    post_dados = {
                        "formato": post.get('formato'),
                        "plataforma": post.get('plataforma'),
                        "data": post.get('data_publicacao'),
                        "impressoes": post.get('views', 0) + post.get('impressoes', 0),
                        "alcance": post.get('alcance', 0),
                        "interacoes": post.get('interacoes', 0),
                        "curtidas": post.get('curtidas', 0),
                        "comentarios": post.get('comentarios', 0) if isinstance(post.get('comentarios'), int) else len(post.get('comentarios', [])),
                        "compartilhamentos": post.get('compartilhamentos', 0),
                        "saves": post.get('saves', 0)
                    }
                    inf_dados["posts"].append(post_dados)
                    dados["posts"].append(post_dados)
                
                dados["influenciadores"].append(inf_dados)
    
    return dados

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
            "2. Visao AON",
            "3. KPIs por Influ",
            "4. Top Performance",
            "5. Lista Influs",
            "Comentarios",
            "Glossario"
        ])
    else:
        tabs = st.tabs([
            "1. Big Numbers",
            "2. KPIs por Influ",
            "3. Top Performance",
            "4. Lista Influs",
            "Comentarios",
            "Glossario"
        ])
    
    tab_idx = 0
    
    # TAB 1: BIG NUMBERS
    with tabs[tab_idx]:
        render_pag1_big_numbers(campanhas_list, metricas, cores)
    tab_idx += 1
    
    # TAB 2: VISAO AON (se aplicavel)
    if has_aon:
        with tabs[tab_idx]:
            render_pag3_visao_aon(campanhas_list, metricas, cores, cliente)
        tab_idx += 1
    
    # TAB 3: KPIs por Influenciador
    with tabs[tab_idx]:
        render_pag4_kpis_influenciador(campanhas_list, cores)
    tab_idx += 1
    
    # TAB 4: Top Performance
    with tabs[tab_idx]:
        render_pag5_top_performance(campanhas_list, cores)
    tab_idx += 1
    
    # TAB 5: Lista Influenciadores
    with tabs[tab_idx]:
        render_pag6_lista_influenciadores(campanhas_list, cores)
    tab_idx += 1
    
    # TAB 6: Comentarios
    with tabs[tab_idx]:
        render_comentarios(campanhas_list, cores)
    tab_idx += 1
    
    # TAB 7: Glossario
    with tabs[tab_idx]:
        render_glossario()


def render_pag1_big_numbers(campanhas_list, metricas, cores):
    """Pagina 1 - Big Numbers conforme layout especificado"""
    
    primary_color = st.session_state.get('primary_color', '#7c3aed')
    secondary_color = st.session_state.get('secondary_color', '#fb923c')
    
    # Pegar estimativas da campanha
    estimativa_alcance = 0
    estimativa_impressoes = 0
    if len(campanhas_list) == 1:
        estimativa_alcance = campanhas_list[0].get('estimativa_alcance', 0)
        estimativa_impressoes = campanhas_list[0].get('estimativa_impressoes', 0)
    
    # Calcular diferencas de estimativa
    realizado_alcance = metricas['total_alcance']
    realizado_imp = metricas['total_impressoes'] + metricas['total_views']
    
    pct_dif_alcance = ((realizado_alcance - estimativa_alcance) / estimativa_alcance * 100) if estimativa_alcance > 0 else 0
    pct_dif_imp = ((realizado_imp - estimativa_impressoes) / estimativa_impressoes * 100) if estimativa_impressoes > 0 else 0
    
    # Calcular taxas
    taxa_eng_total = (metricas['total_interacoes'] / metricas['total_seguidores'] * 100) if metricas['total_seguidores'] > 0 else 0
    taxa_alcance = metricas['taxa_alcance']
    engaj_efetivo = metricas['engajamento_efetivo']
    
    # Calcular AIR Score medio
    todos_influs = []
    todos_influs_camp = []  # Para manter relacao inf -> posts
    for camp in campanhas_list:
        for inf_camp in camp.get('influenciadores', []):
            inf = data_manager.get_influenciador(inf_camp.get('influenciador_id'))
            if inf:
                todos_influs.append(inf)
                todos_influs_camp.append({'inf': inf, 'posts': inf_camp.get('posts', [])})
    
    air_score_medio = 0
    if todos_influs:
        air_score_medio = sum(i.get('air_score', 0) for i in todos_influs) / len(todos_influs)
    
    # Coletar todos os posts para metricas
    todos_posts = []
    for camp in campanhas_list:
        for inf_camp in camp.get('influenciadores', []):
            todos_posts.extend(inf_camp.get('posts', []))
    
    # ========== LINHA 1 - CARDS BONITOS ==========
    st.markdown("### Metricas Principais")
    
    def render_card(titulo, valor, cor_fundo="#f9fafb"):
        return f"""
        <div style="background: {cor_fundo}; border: 1px solid #e5e7eb; border-radius: 12px; 
                    padding: 1rem; text-align: center; height: 90px;">
            <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.3rem;">{titulo}</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #1f2937;">{valor}</div>
        </div>
        """
    
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    
    with col1:
        st.markdown(render_card("Q. INFLUS", metricas['total_influenciadores']), unsafe_allow_html=True)
    with col2:
        st.markdown(render_card("T. SEGUIDORES", funcoes_auxiliares.formatar_numero(metricas['total_seguidores'])), unsafe_allow_html=True)
    with col3:
        st.markdown(render_card("T. IMPRESSOES", funcoes_auxiliares.formatar_numero(realizado_imp)), unsafe_allow_html=True)
    with col4:
        st.markdown(render_card("T. ALCANCE", funcoes_auxiliares.formatar_numero(realizado_alcance)), unsafe_allow_html=True)
    with col5:
        st.markdown(render_card("TX. ALCANCE", f"{taxa_alcance:.2f}%"), unsafe_allow_html=True)
    with col6:
        st.markdown(render_card("T. INTERACOES", funcoes_auxiliares.formatar_numero(metricas['total_interacoes'])), unsafe_allow_html=True)
    with col7:
        st.markdown(render_card("T. LIKES", funcoes_auxiliares.formatar_numero(metricas['total_curtidas'])), unsafe_allow_html=True)
    with col8:
        st.markdown(render_card("T. SALVOS", funcoes_auxiliares.formatar_numero(metricas['total_saves'])), unsafe_allow_html=True)
    
    st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
    
    # ========== LINHA 2 - CARDS BONITOS ==========
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    
    cor_pct_imp = "#dcfce7" if pct_dif_imp >= 0 else "#fee2e2"
    cor_pct_alc = "#dcfce7" if pct_dif_alcance >= 0 else "#fee2e2"
    
    with col1:
        st.markdown(render_card("Q. CONTEUDO", metricas['total_posts']), unsafe_allow_html=True)
    with col2:
        st.markdown(render_card("TX. ENG. TOTAL", f"{taxa_eng_total:.2f}%"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_card("EST. IMPR. %", f"{pct_dif_imp:+.1f}%", cor_pct_imp), unsafe_allow_html=True)
    with col4:
        st.markdown(render_card("EST. ALC. %", f"{pct_dif_alcance:+.1f}%", cor_pct_alc), unsafe_allow_html=True)
    with col5:
        st.markdown(render_card("ENGAJ. EFETIVO", f"{engaj_efetivo:.2f}%"), unsafe_allow_html=True)
    with col6:
        st.markdown(render_card("AIR SCORE", funcoes_auxiliares.formatar_air_score(air_score_medio)), unsafe_allow_html=True)
    with col7:
        st.markdown(render_card("T. COMENTARIOS", funcoes_auxiliares.formatar_numero(metricas['total_comentarios'])), unsafe_allow_html=True)
    with col8:
        st.markdown(render_card("T. COMPARTILH.", funcoes_auxiliares.formatar_numero(metricas['total_compartilhamentos'])), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========== GRAFICOS ==========
    st.markdown("### Graficos")
    
    # Coletar formatos unicos da campanha
    formatos_campanha = set()
    for post in todos_posts:
        formato = post.get('formato', post.get('type', 'Outro'))
        if formato:
            formatos_campanha.add(formato.capitalize())
    formatos_campanha = sorted(list(formatos_campanha)) if formatos_campanha else ['Reels', 'Feed', 'Stories']
    
    # Coletar classificacoes unicas
    classificacoes = set()
    for inf in todos_influs:
        classificacoes.add(inf.get('classificacao', 'Desconhecido'))
    classificacoes = sorted(list(classificacoes)) if classificacoes else ['Nano', 'Micro', 'Inter 1', 'Inter 2', 'Macro', 'Mega 1', 'Mega 2', 'Super Mega']
    
    col_grafico1, col_grafico2 = st.columns(2)
    
    # ========== GRAFICO DE BARRAS EMPILHADAS ==========
    with col_grafico1:
        st.markdown("**KPI por Formato (por Classificacao)**")
        
        kpi_barra = st.selectbox(
            "KPI:",
            ["Impressoes", "Alcance", "Interacoes", "Impressoes", "Likes", "Comentarios", "Saves"],
            key="kpi_barra_pag1"
        )
        
        # Agregar dados por formato E por classificacao
        dados_grafico = []
        
        for inf_data in todos_influs_camp:
            inf = inf_data['inf']
            classif = inf.get('classificacao', 'Desconhecido')
            
            for post in inf_data['posts']:
                formato = post.get('formato', post.get('type', 'Outro')).capitalize()
                
                valor = 0
                if kpi_barra == "Impressoes":
                    valor = post.get('impressoes', 0) or 0
                elif kpi_barra == "Alcance":
                    valor = post.get('alcance', 0) or 0
                elif kpi_barra == "Interacoes":
                    valor = post.get('interacoes', 0) or 0
                elif kpi_barra == "Impressoes":
                    valor = post.get('views', 0) or 0
                elif kpi_barra == "Likes":
                    valor = post.get('curtidas', 0) or 0
                elif kpi_barra == "Comentarios":
                    comentarios = post.get('comentarios', 0)
                    if isinstance(comentarios, list):
                        valor = len(comentarios)
                    else:
                        valor = comentarios or 0
                elif kpi_barra == "Saves":
                    valor = post.get('saves', 0) or 0
                
                dados_grafico.append({
                    'Formato': formato,
                    'Classificacao': classif,
                    'Valor': valor
                })
        
        if dados_grafico:
            df_barras = pd.DataFrame(dados_grafico)
            df_agg = df_barras.groupby(['Formato', 'Classificacao'])['Valor'].sum().reset_index()
            
            # Cores para classificacoes
            cores_classif = {
                'Nano': '#22c55e',
                'Micro': '#3b82f6', 
                'Inter 1': '#8b5cf6',
                'Inter 2': '#a855f7',
                'Macro': '#f97316',
                'Mega 1': '#ef4444',
                'Mega 2': '#dc2626',
                'Super Mega': '#991b1b',
                'Desconhecido': '#9ca3af'
            }
            
            fig_barras = px.bar(
                df_agg,
                x='Formato',
                y='Valor',
                color='Classificacao',
                color_discrete_map=cores_classif,
                barmode='stack'
            )
            fig_barras.update_layout(
                height=350,
                xaxis_title="",
                yaxis_title=kpi_barra,
                legend_title="Classificacao",
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
            )
            st.plotly_chart(fig_barras, use_container_width=True)
        else:
            st.info("Sem dados para exibir")
    
    # ========== GRAFICO DE RADAR ==========
    with col_grafico2:
        st.markdown("**Distribuicao por Classificacao**")
        
        filtro_formato_radar = st.selectbox(
            "Formato:",
            ["Todos"] + formatos_campanha,
            key="formato_radar_pag1"
        )
        
        # Agregar dados por classificacao
        dados_classif = {c: 0 for c in classificacoes}
        
        for inf_data in todos_influs_camp:
            inf = inf_data['inf']
            classif = inf.get('classificacao', 'Desconhecido')
            
            for post in inf_data['posts']:
                formato_post = post.get('formato', post.get('type', '')).capitalize()
                
                if filtro_formato_radar != "Todos" and formato_post != filtro_formato_radar:
                    continue
                
                # Contar interacoes por classificacao
                dados_classif[classif] += post.get('interacoes', 0) or 0
        
        if any(v > 0 for v in dados_classif.values()):
            categorias = list(dados_classif.keys())
            valores = list(dados_classif.values())
            
            fig_radar = go.Figure()
            
            fig_radar.add_trace(go.Scatterpolar(
                r=valores + [valores[0]],
                theta=categorias + [categorias[0]],
                fill='toself',
                fillcolor=f'rgba(124, 58, 237, 0.3)',
                line=dict(color=primary_color, width=2),
                name='Interacoes'
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True)
                ),
                showlegend=False,
                height=350
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("Sem dados para exibir")
    
    # ========== INSIGHTS ==========
    st.markdown("---")
    st.subheader("Insights")
    
    # Insights automaticos
    st.markdown("**Analise Automatica:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if engaj_efetivo > 5:
            st.success(f"✅ **Engajamento Excelente**: {engaj_efetivo:.2f}%")
        elif engaj_efetivo > 3:
            st.info(f"ℹ️ **Engajamento Adequado**: {engaj_efetivo:.2f}%")
        else:
            st.warning(f"⚠️ **Engajamento Baixo**: {engaj_efetivo:.2f}%")
    
    with col2:
        if taxa_alcance > 50:
            st.success(f"✅ **Alcance Alto**: {taxa_alcance:.2f}%")
        elif taxa_alcance > 20:
            st.info(f"ℹ️ **Alcance Bom**: {taxa_alcance:.2f}%")
        else:
            st.warning(f"⚠️ **Alcance Baixo**: {taxa_alcance:.2f}%")
    
    with col3:
        if pct_dif_imp >= 0:
            st.success(f"✅ **Meta de Impressoes**: Superada em {pct_dif_imp:.1f}%")
        else:
            st.warning(f"⚠️ **Meta de Impressoes**: Abaixo em {abs(pct_dif_imp):.1f}%")
    
    # Insights manuais
    st.markdown("---")
    st.markdown("**Insights Manuais:**")
    
    if len(campanhas_list) == 1:
        insights_config = campanhas_list[0].get('insights_config', {})
        insights_manuais = insights_config.get('insights_campanha', '')
        
        novo_insight = st.text_area(
            "Adicione suas observacoes sobre a campanha:", 
            value=insights_manuais, 
            height=100, 
            key="insights_manual_pag1"
        )
        
        if st.button("Salvar Insights", key="salvar_insights_pag1"):
            insights_config['insights_campanha'] = novo_insight
            data_manager.atualizar_campanha(campanhas_list[0]['id'], {'insights_config': insights_config})
            st.success("Insights salvos!")
            st.rerun()
    else:
        st.caption("Insights manuais disponiveis apenas para relatorio de campanha unica")
    
    # Insights por IA
    if len(campanhas_list) == 1:
        dados_ia = preparar_dados_pagina("big_numbers", campanhas_list, metricas)
        dados_ia["metricas_gerais"] = {
            "total_influenciadores": metricas['total_influenciadores'],
            "total_seguidores": metricas['total_seguidores'],
            "total_impressoes": metricas['total_impressoes'] + metricas['total_views'],
            "total_alcance": metricas['total_alcance'],
            "total_interacoes": metricas['total_interacoes'],
            "engajamento_efetivo": engaj_efetivo,
            "taxa_alcance": taxa_alcance,
            "pct_meta_impressoes": pct_dif_imp,
            "pct_meta_alcance": pct_dif_alcance,
            "air_score_medio": air_score_medio
        }
        render_secao_insights("big_numbers", dados_ia, campanhas_list[0]['id'])


def render_pag2_analise_geral(campanhas_list, metricas, cores):
    """Pagina 2 - Analise Geral"""
    
    st.subheader("Analise de Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Grafico 1: Comparativo por Formato**")
        kpi1 = st.selectbox("KPI Barras:", ["Impressoes", "Alcance", "Interacoes", "Impressoes"], key="kpi1_pag2")
        kpi2 = st.selectbox("KPI Linha:", ["Taxa Eng. Efetivo", "Taxa Alcance", "Interacoes", "Impressoes"], key="kpi2_pag2")
        
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
        kpi3 = st.selectbox("KPI Barras:", ["Impressoes", "Alcance", "Interacoes", "Impressoes"], key="kpi3_pag2")
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
    fig.add_trace(go.Bar(
        x=df_tempo['data'], 
        y=df_tempo[campo], 
        name=filtro_metrica, 
        marker_color=cores[0],
        text=[funcoes_auxiliares.formatar_numero(v) for v in df_tempo[campo]],
        textposition='outside',
        width=0.5  # Barras mais finas
    ))
    
    taxa_campo = 'taxa_eng' if filtro_taxa == "Taxa Eng. Efetivo" else 'taxa_alcance'
    fig.add_trace(go.Scatter(
        x=df_tempo['data'], 
        y=df_tempo[taxa_campo], 
        name=filtro_taxa, 
        mode='lines+markers+text',
        text=[f"{v:.1f}%" for v in df_tempo[taxa_campo]],
        textposition='top center',
        yaxis='y2', 
        line=dict(color=cores[1], width=3), 
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=f'Evolucao de {filtro_metrica}', 
        yaxis=dict(title=filtro_metrica), 
        yaxis2=dict(title=filtro_taxa, overlaying='y', side='right'), 
        height=450, 
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        bargap=0.3  # Espacamento entre barras
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Resumo Mensal")
    
    df_mensal = df.groupby('mes').agg({'influenciador': 'nunique', 'seguidores': lambda x: x.drop_duplicates().sum(), 'views': 'sum', 'alcance': 'sum', 'interacoes': 'sum', 'impressoes': 'sum'}).reset_index()
    df_mensal.columns = ['Mes', 'Qtd Influs', 'Seguidores', 'Views', 'Alcance', 'Interacoes', 'Impressoes']
    
    # Formatar numeros com ponto nas centenas
    df_mensal_fmt = df_mensal.copy()
    for col in ['Seguidores', 'Views', 'Alcance', 'Interacoes', 'Impressoes']:
        df_mensal_fmt[col] = df_mensal_fmt[col].apply(lambda x: f"{x:,.0f}".replace(",", "."))
    
    st.dataframe(df_mensal_fmt, use_container_width=True, hide_index=True)
    
    # Insights por IA
    if len(campanhas_list) == 1:
        dados_ia = preparar_dados_pagina("visao_aon", campanhas_list)
        dados_ia["resumo_mensal"] = df_mensal.to_dict('records') if not df_mensal.empty else []
        dados_ia["evolucao_temporal"] = df_tempo.to_dict('records') if not df_tempo.empty else []
        render_secao_insights("visao_aon", dados_ia, campanhas_list[0]['id'])


def render_pag4_kpis_influenciador(campanhas_list, cores):
    """Pagina 4 - KPIs por Influenciador (Top 15)"""
    
    st.subheader("KPIs por Influenciador (Top 15)")
    
    dados_inf = coletar_dados_influenciadores(campanhas_list)
    
    if not dados_inf:
        st.info("Nenhum dado disponivel")
        return
    
    df = pd.DataFrame(dados_inf)
    df = df.sort_values('impressoes', ascending=False).head(15)
    
    st.markdown("### Grafico 1: Performance Geral")
    
    col1, col2 = st.columns(2)
    with col1:
        kpi_barra = st.selectbox("KPI Barras:", ["Seguidores", "Impressoes", "Alcance", "Interacoes"], key="kpi_barra_pag4")
    with col2:
        kpi_linha = st.selectbox("KPI Linha:", ["Taxa Eng. Efetivo", "Taxa Alcance", "Taxa Visualizacao", "Engajamento Total"], key="kpi_linha_pag4")
    
    kpi_map = {'Seguidores': 'seguidores', 'Impressoes': 'impressoes', 'Alcance': 'alcance', 'Interacoes': 'interacoes'}
    campo_barra = kpi_map.get(kpi_barra, 'seguidores')
    
    # Calcular taxa de visualizacao (impressoes / seguidores)
    df['taxa_views'] = (df['impressoes'] / df['seguidores'] * 100).round(2).fillna(0)
    
    df_sorted = df.sort_values(campo_barra, ascending=False)
    
    fig1 = go.Figure()
    # Barras VERTICAIS
    fig1.add_trace(go.Bar(
        x=df_sorted['nome'], 
        y=df_sorted[campo_barra], 
        name=kpi_barra, 
        marker_color=cores[0], 
        text=[funcoes_auxiliares.formatar_numero(v) for v in df_sorted[campo_barra]], 
        textposition='outside'
    ))
    
    if kpi_linha == "Taxa Eng. Efetivo":
        y_linha = df_sorted['taxa_eng']
    elif kpi_linha == "Taxa Alcance":
        y_linha = df_sorted['taxa_alcance']
    elif kpi_linha == "Taxa Visualizacao":
        y_linha = df_sorted['taxa_views']
    else:
        y_linha = df_sorted['taxa_eng_geral']
    
    fig1.add_trace(go.Scatter(
        x=df_sorted['nome'], 
        y=y_linha, 
        mode='lines+markers+text', 
        name=kpi_linha, 
        text=[f"{v:.1f}%" for v in y_linha],
        textposition='top center',
        yaxis='y2', 
        line=dict(color=cores[1], width=2), 
        marker=dict(size=8)
    ))
    fig1.update_layout(
        xaxis=dict(title='Influenciador', tickangle=-45), 
        yaxis=dict(title=kpi_barra), 
        yaxis2=dict(title=kpi_linha, overlaying='y', side='right'), 
        height=500, 
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        bargap=0.5  # Barras mais finas
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("### Grafico 2: Eficiencia de Gasto")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        metrica_custo = st.selectbox("Metrica:", ["CPM", "CPE", "CPI", "CPV"], key="custo_pag4")
        investimento = st.number_input("Investimento (R$):", min_value=0.0, value=float(sum([d.get('custo', 0) for d in dados_inf])), step=100.0, key="invest_pag4")
    
    with col2:
        df_custo = df.copy()
        if metrica_custo == "CPM":
            df_custo['metrica'] = (df_custo['custo'] / df_custo['impressoes'] * 1000).round(2).fillna(0)
        elif metrica_custo == "CPE":
            df_custo['metrica'] = (df_custo['custo'] / df_custo['interacoes']).round(2).fillna(0)
        elif metrica_custo == "CPI":
            df_custo['metrica'] = (df_custo['custo'] / df_custo['impressoes']).round(4).fillna(0)
        else:  # CPV
            df_custo['metrica'] = (df_custo['custo'] / df_custo['impressoes']).round(4).fillna(0)
        
        df_custo = df_custo[df_custo['metrica'] > 0].sort_values('metrica', ascending=False)
        
        if not df_custo.empty:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=df_custo['metrica'], y=df_custo['nome'], orientation='h', marker_color=cores[4], text=[f"R$ {v:.2f}" for v in df_custo['metrica']], textposition='outside'))
            fig2.update_layout(title=f'{metrica_custo} (R$)', height=max(300, len(df_custo) * 25), bargap=0.5)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Adicione custos aos posts")
    
    st.markdown("### Grafico 3: Trafego")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        tipo_trafego = st.selectbox("Tipo:", ["Cliques Link", "Cliques @", "Ambos"], key="trafego_pag4")
    
    with col2:
        fig3 = go.Figure()
        
        if tipo_trafego == "Cliques Link":
            fig3.add_trace(go.Bar(
                x=df['cliques_link'], 
                y=df['nome'], 
                orientation='h', 
                name='Cliques Link', 
                marker_color=cores[5],
                text=[funcoes_auxiliares.formatar_numero(v) for v in df['cliques_link']],
                textposition='outside'
            ))
        elif tipo_trafego == "Cliques @":
            fig3.add_trace(go.Bar(
                x=df['cliques_arroba'], 
                y=df['nome'], 
                orientation='h', 
                name='Cliques @', 
                marker_color=cores[3],
                text=[funcoes_auxiliares.formatar_numero(v) for v in df['cliques_arroba']],
                textposition='outside'
            ))
        else:
            # Ambos
            fig3.add_trace(go.Bar(
                x=df['cliques_link'], 
                y=df['nome'], 
                orientation='h', 
                name='Cliques Link', 
                marker_color=cores[5],
                text=[funcoes_auxiliares.formatar_numero(v) for v in df['cliques_link']],
                textposition='outside'
            ))
            fig3.add_trace(go.Bar(
                x=df['cliques_arroba'], 
                y=df['nome'], 
                orientation='h', 
                name='Cliques @', 
                marker_color=cores[3],
                text=[funcoes_auxiliares.formatar_numero(v) for v in df['cliques_arroba']],
                textposition='outside'
            ))
        
        for i, row in df.iterrows():
            fig3.add_annotation(x=0, y=row['nome'], text=f"({funcoes_auxiliares.formatar_numero(row['seguidores'])} seg)", showarrow=False, xanchor='right', xshift=-10, font=dict(size=9, color='gray'))
        
        fig3.update_layout(title='Trafego por Influenciador', height=max(300, len(df) * 25), barmode='group', bargap=0.5)
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
        
        # Insights por IA
        dados_ia = preparar_dados_pagina("kpis_influenciador", campanhas_list)
        dados_ia["top_15_influenciadores"] = dados_inf[:15] if len(dados_inf) > 15 else dados_inf
        render_secao_insights("kpis_influenciador", dados_ia, campanhas_list[0]['id'])


def render_pag5_top_performance(campanhas_list, cores):
    """Pagina 5 - Top Performance"""
    
    st.subheader("Top Performance")
    
    dados_influs = coletar_dados_influenciadores(campanhas_list)
    
    if not dados_influs:
        st.info("Nenhum dado")
        return
    
    df = pd.DataFrame(dados_influs)
    
    # Grafico de dispersao primeiro (sem filtros)
    if len(df) > 0:
        st.markdown("### Dispersao: Engajamento vs Alcance")
        
        fig = px.scatter(df, x='taxa_alcance', y='taxa_eng', size='impressoes', color='classificacao', hover_name='nome', text='nome', labels={'taxa_alcance': 'Taxa de Alcance (%)', 'taxa_eng': 'Taxa de Engajamento (%)'}, color_discrete_sequence=cores)
        fig.update_traces(textposition='top center', textfont_size=9)
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Filtros acima da lista
    st.markdown("### Lista de Top Performance")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        metrica_ordenar = st.selectbox("Ordenar:", ["Investimento (Custo)", "Interacoes", "Taxa Eng. Efetivo", "Impressoes", "Alcance"], key="ordenar_pag5")
    with col2:
        filtro_class = st.multiselect("Classificacao:", ["Nano", "Micro", "Mid", "Macro", "Mega"], key="class_pag5")
    with col3:
        qtd = st.slider("Quantidade:", 5, 30, 15, key="qtd_pag5")
    
    df_filtrado = df.copy()
    
    if filtro_class:
        df_filtrado = df_filtrado[df_filtrado['classificacao'].isin(filtro_class)]
    
    ordem_map = {"Investimento (Custo)": "custo", "Interacoes": "interacoes", "Taxa Eng. Efetivo": "taxa_eng", "Impressoes": "impressoes", "Alcance": "alcance"}
    df_filtrado = df_filtrado.sort_values(ordem_map.get(metrica_ordenar, 'interacoes'), ascending=False).head(qtd)
    
    for _, row in df_filtrado.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([0.5, 2, 1.2, 1.2, 1.2, 1.2])
        with col1:
            if row.get('foto'):
                st.image(row['foto'], width=40)
        with col2:
            st.write(f"**{row['nome']}**")
            st.caption(f"@{row['usuario']} | {row['classificacao']}")
        with col3:
            st.metric("Investimento", f"R$ {row.get('custo', 0):,.0f}".replace(",", "."))
        with col4:
            st.metric("Interacoes", funcoes_auxiliares.formatar_numero(row['interacoes']))
        with col5:
            st.metric("Taxa Eng.", f"{row['taxa_eng']:.2f}%")
        with col6:
            st.metric("Impressoes", funcoes_auxiliares.formatar_numero(row['impressoes']))
        st.markdown("---")
    
    # Insights por IA
    if len(campanhas_list) == 1:
        dados_ia = preparar_dados_pagina("top_performance", campanhas_list)
        dados_ia["top_performance"] = df_filtrado.to_dict('records') if not df_filtrado.empty else []
        render_secao_insights("top_performance", dados_ia, campanhas_list[0]['id'])


def render_pag6_lista_influenciadores(campanhas_list, cores):
    """Pagina 6 - Lista completa"""
    
    st.subheader("Lista de Influenciadores")
    
    col1, col2 = st.columns(2)
    with col1:
        filtro_class = st.multiselect("Classificacao:", ["Nano", "Micro", "Mid", "Macro", "Mega"], key="class_pag6")
    with col2:
        ordenar = st.selectbox("Ordenar:", ["Impressoes", "Alcance", "Interacoes", "Taxa Eng.", "Investimento"], key="ord_pag6")
    
    dados = coletar_dados_influenciadores(campanhas_list)
    
    if not dados:
        st.info("Nenhum influenciador")
        return
    
    df = pd.DataFrame(dados)
    
    if filtro_class:
        df = df[df['classificacao'].isin(filtro_class)]
    
    ordem_map = {"Impressoes": "impressoes", "Alcance": "alcance", "Interacoes": "interacoes", "Taxa Eng.": "taxa_eng", "Investimento": "custo"}
    df = df.sort_values(ordem_map.get(ordenar, 'impressoes'), ascending=False)
    
    # Preparar dataframe para exibicao com formatacao
    df_exibir = df[['nome', 'usuario', 'classificacao', 'seguidores', 'posts', 'impressoes', 'alcance', 'interacoes', 'custo', 'taxa_eng', 'taxa_alcance']].copy()
    df_exibir.columns = ['Nome', 'Usuario', 'Classe', 'Seguidores', 'Posts', 'Impressoes', 'Alcance', 'Interacoes', 'Investimento (R$)', 'Taxa Eng. %', 'Taxa Alc. %']
    
    # Formatar numeros com ponto nas centenas
    for col in ['Seguidores', 'Impressoes', 'Alcance', 'Interacoes']:
        df_exibir[col] = df_exibir[col].apply(lambda x: f"{x:,.0f}".replace(",", "."))
    
    df_exibir['Investimento (R$)'] = df_exibir['Investimento (R$)'].apply(lambda x: f"{x:,.0f}".replace(",", "."))
    df_exibir['Taxa Eng. %'] = df_exibir['Taxa Eng. %'].apply(lambda x: f"{x:.2f}")
    df_exibir['Taxa Alc. %'] = df_exibir['Taxa Alc. %'].apply(lambda x: f"{x:.2f}")
    
    st.dataframe(df_exibir, use_container_width=True, hide_index=True)


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
                dados_inf[inf_id] = {'id': inf_id, 'nome': inf['nome'], 'usuario': inf['usuario'], 'foto': inf.get('foto', ''), 'classificacao': inf.get('classificacao', 'Desconhecido'), 'seguidores': inf.get('seguidores', 0), 'impressoes': 0, 'alcance': 0, 'interacoes': 0, 'custo': 0, 'cliques_link': 0, 'cliques_arroba': 0, 'posts': 0}
            dados_inf[inf_id]['custo'] += camp_inf.get('custo', 0)  # Custo por influenciador
            for post in camp_inf.get('posts', []):
                # Impressoes = views + impressoes (combinados)
                dados_inf[inf_id]['impressoes'] += post.get('views', 0) + post.get('impressoes', 0)
                dados_inf[inf_id]['alcance'] += post.get('alcance', 0)
                dados_inf[inf_id]['interacoes'] += post.get('interacoes', 0)
                dados_inf[inf_id]['cliques_link'] += post.get('clique_link', 0)
                dados_inf[inf_id]['cliques_arroba'] += post.get('clique_arroba', 0) or post.get('cliques_arroba', 0) or 0
                dados_inf[inf_id]['posts'] += 1
    resultado = []
    for inf_id, d in dados_inf.items():
        d['taxa_eng'] = round((d['interacoes'] / d['impressoes'] * 100), 2) if d['impressoes'] > 0 else 0
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
