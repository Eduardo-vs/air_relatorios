"""
Relatório Completo da Campanha
TODAS as funcionalidades de análise em 11 tabs
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import random
from collections import Counter
from utils import data_manager, funcoes_auxiliares

def render():
    """Renderiza relatório completo da campanha"""
    
    campanha = data_manager.get_campanha(st.session_state.campanha_atual_id)
    
    if not campanha:
        st.error("Campanha não encontrada")
        return
    
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f'<p class="main-header">{campanha["nome"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="subtitle">{campanha["cliente_nome"]}</p>', unsafe_allow_html=True)
    with col2:
        if st.button("← Voltar", use_container_width=True):
            st.session_state.campanha_atual_id = None
            st.rerun()
    
    # Verificar se cliente é AON
    cliente = data_manager.get_cliente(campanha['cliente_id'])
    is_aon = cliente and cliente.get('tipo') == 'aon'
    
    # Criar tabs baseado no tipo de cliente
    if is_aon:
        tabs_names = [
            "⚙️ Configuração", 
            "👥 Influenciadores", 
            "📊 Big Numbers",
            "📈 Gráficos Dinâmicos AON",
            "📉 KPIs Dinâmicos",
            "⭐ Top Influenciadores",
            "🎬 Top Conteúdo",
            "📋 Análise Detalhada",
            "💬 Visão Comentários",
            "☁️ Nuvem de Palavras",
            "📚 Glossário"
        ]
    else:
        tabs_names = [
            "⚙️ Configuração", 
            "👥 Influenciadores", 
            "📊 Big Numbers",
            "📉 KPIs Dinâmicos",
            "⭐ Top Influenciadores",
            "🎬 Top Conteúdo",
            "📋 Análise Detalhada",
            "💬 Visão Comentários",
            "☁️ Nuvem de Palavras",
            "📚 Glossário"
        ]
    
    tabs = st.tabs(tabs_names)
    
    # ============================================
    # TAB 1: CONFIGURAÇÃO
    # ============================================
    with tabs[0]:
        render_tab_configuracao(campanha)
    
    # ============================================
    # TAB 2: INFLUENCIADORES
    # ============================================
    with tabs[1]:
        render_tab_influenciadores(campanha)
    
    # ============================================
    # TAB 3: BIG NUMBERS
    # ============================================
    with tabs[2]:
        render_tab_big_numbers(campanha)
    
    # ============================================
    # TAB 4: GRÁFICOS DINÂMICOS AON (se aplicável)
    # ============================================
    if is_aon:
        with tabs[3]:
            render_tab_graficos_dinamicos_aon(campanha)
        next_tab_index = 4
    else:
        next_tab_index = 3
    
    # ============================================
    # TAB: KPIs DINÂMICOS
    # ============================================
    with tabs[next_tab_index]:
        render_tab_kpis_dinamicos(campanha)
    
    # ============================================
    # TAB: TOP INFLUENCIADORES
    # ============================================
    with tabs[next_tab_index + 1]:
        render_tab_top_influenciadores(campanha)
    
    # ============================================
    # TAB: TOP CONTEÚDO
    # ============================================
    with tabs[next_tab_index + 2]:
        render_tab_top_conteudo(campanha)
    
    # ============================================
    # TAB: ANÁLISE DETALHADA
    # ============================================
    with tabs[next_tab_index + 3]:
        render_tab_analise_detalhada(campanha)
    
    # ============================================
    # TAB: VISÃO COMENTÁRIOS
    # ============================================
    with tabs[next_tab_index + 4]:
        render_tab_visao_comentarios(campanha)
    
    # ============================================
    # TAB: NUVEM DE PALAVRAS
    # ============================================
    with tabs[next_tab_index + 5]:
        render_tab_nuvem_palavras(campanha)
    
    # ============================================
    # TAB: GLOSSÁRIO
    # ============================================
    with tabs[next_tab_index + 6]:
        render_tab_glossario()


# ============================================
# FUNÇÕES DE RENDERIZAÇÃO DAS TABS
# ============================================

def render_tab_configuracao(campanha):
    """Tab 1: Configuração da Campanha"""
    
    st.subheader("Informações da Campanha")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Nome", value=campanha['nome'], disabled=True)
        st.text_input("Cliente", value=campanha['cliente_nome'], disabled=True)
        st.text_input("Período", 
                     value=f"{funcoes_auxiliares.formatar_data_br(campanha['data_inicio'])} - {funcoes_auxiliares.formatar_data_br(campanha['data_fim'])}", 
                     disabled=True)
        st.text_area("Objetivo", value=campanha['objetivo'], disabled=True, height=100)
    
    with col2:
        st.text_input("Tipo", value=campanha.get('tipo_dados', 'estático').title(), disabled=True)
        st.text_input("Status", value=campanha['status'].title(), disabled=True)
        
        # AIR Score destacado
        air_score = funcoes_auxiliares.calcular_air_score(campanha)
        st.markdown(f"""
        <div class='air-score-card'>
            <div class='air-score-number'>{air_score}</div>
            <div class='air-score-label'>AIR SCORE</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("📊 Métricas Selecionadas")
    
    metricas_sel = campanha.get('metricas_selecionadas', {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.write("✅ Views" if metricas_sel.get('views') else "❌ Views")
        st.write("✅ Interações" if metricas_sel.get('interacoes') else "❌ Interações")
    with col2:
        st.write("✅ Curtidas" if metricas_sel.get('curtidas') else "❌ Curtidas")
        st.write("✅ Comentários" if metricas_sel.get('comentarios') else "❌ Comentários")
    with col3:
        st.write("✅ Compartilhamentos" if metricas_sel.get('compartilhamentos') else "❌ Compartilhamentos")
        st.write("✅ Saves" if metricas_sel.get('saves') else "❌ Saves")
    with col4:
        st.write("✅ Cliques Link" if metricas_sel.get('clique_link') else "❌ Cliques Link")
        st.write("✅ Conversões Cupom" if metricas_sel.get('cupom_conversoes') else "❌ Conversões Cupom")


def render_tab_influenciadores(campanha):
    """Tab 2: Gerenciamento de Influenciadores e Posts"""
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Influenciadores da Campanha")
    with col2:
        if st.button("+ Adicionar Influenciador", use_container_width=True):
            st.session_state.show_add_inf_camp = True
    
    # Form para adicionar influenciador
    if st.session_state.get('show_add_inf_camp', False):
        if st.session_state.influenciadores_base:
            opcoes_inf = [f"{i['nome']} ({i['usuario']}) - {i['classificacao']}" 
                         for i in st.session_state.influenciadores_base]
            inf_sel = st.selectbox("Selecione o influenciador", opcoes_inf)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Adicionar à Campanha", use_container_width=True):
                    nome_sel = inf_sel.split(" (")[0]
                    inf_obj = next((i for i in st.session_state.influenciadores_base 
                                  if i['nome'] == nome_sel), None)
                    if inf_obj:
                        data_manager.adicionar_influenciador_campanha(campanha['id'], inf_obj['id'])
                        st.session_state.show_add_inf_camp = False
                        st.success("✅ Influenciador adicionado!")
                        st.rerun()
            with col2:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_add_inf_camp = False
                    st.rerun()
        else:
            st.warning("⚠️ Cadastre influenciadores na base primeiro")
            if st.button("Ir para Influenciadores"):
                st.session_state.current_page = 'Influenciadores'
                st.rerun()
    
    st.markdown("---")
    
    # Lista de influenciadores
    if not campanha['influenciadores']:
        st.info("📭 Nenhum influenciador adicionado ainda")
        return
    
    for inf in campanha['influenciadores']:
        with st.expander(f"⭐ {inf['nome']} - {len(inf['posts'])} posts - {inf['classificacao']}"):
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**Redes:** {', '.join(inf['redes_sociais'])}")
                st.write(f"**Cidade:** {inf.get('cidade', '-')}")
            
            with col2:
                st.write(f"**Seguidores:** {inf['base_seguidores']}")
                st.write(f"**Taxa Eng.:** {inf['taxa_engajamento']}%")
            
            with col3:
                if st.button("+ Adicionar Post", key=f"add_post_{inf['id']}", use_container_width=True):
                    st.session_state.current_influencer_id = inf['id']
                    st.session_state.show_add_post = True
            
            # Form para adicionar post
            if (st.session_state.get('show_add_post', False) and 
                st.session_state.get('current_influencer_id') == inf['id']):
                
                render_form_post(campanha, inf)
            
            # Lista de posts
            if inf['posts']:
                st.markdown("---")
                st.markdown("**📱 Posts Publicados:**")
                
                for post in inf['posts']:
                    render_post_item(campanha, inf, post)


def render_form_post(campanha, inf):
    """Renderiza formulário de adicionar post"""
    
    with st.form(f"form_post_{inf['id']}"):
        st.markdown("##### 📝 Novo Post")
        
        col1, col2, col3 = st.columns(3)
        
        metricas_camp = campanha.get('metricas_selecionadas', {})
        
        with col1:
            formato = st.selectbox("Formato *", 
                                  ["Reels", "Stories", "Carrossel", "Feed", "TikTok", "YouTube"])
            plataforma = st.selectbox("Plataforma *", inf['redes_sociais'])
            data_pub = st.date_input("Data *", value=datetime.now())
            link_post = st.text_input("Link do Post", placeholder="https://...")
        
        with col2:
            views = st.number_input("Views *", min_value=0, value=0) if metricas_camp.get('views', True) else 0
            interacoes = st.number_input("Interações *", min_value=0, value=0) if metricas_camp.get('interacoes', True) else 0
            curtidas = st.number_input("Curtidas", min_value=0, value=0) if metricas_camp.get('curtidas', True) else 0
            comentarios = st.number_input("Comentários", min_value=0, value=0) if metricas_camp.get('comentarios', True) else 0
        
        with col3:
            compartilhamentos = st.number_input("Compartilh.", min_value=0, value=0) if metricas_camp.get('compartilhamentos', True) else 0
            saves = st.number_input("Saves", min_value=0, value=0) if metricas_camp.get('saves', True) else 0
            
            # Clique em link só para Stories
            if formato == "Stories" and metricas_camp.get('clique_link', False):
                clique_link = st.number_input("Cliques Link", min_value=0, value=0)
            else:
                clique_link = 0
            
            # Cupom opcional
            cupom_codigo = ""
            cupom_conversoes = 0
            if metricas_camp.get('cupom_conversoes', False):
                cupom_codigo = st.text_input("Código Cupom", placeholder="PROMO10")
                if cupom_codigo:
                    cupom_conversoes = st.number_input("Conversões", min_value=0, value=0)
        
        st.markdown("**📷 Imagens/Vídeos do Post**")
        imagens_upload = st.file_uploader(
            "Upload de mídias (prints, fotos, vídeos)",
            type=['png', 'jpg', 'jpeg', 'mp4', 'gif'],
            accept_multiple_files=True,
            key=f"upload_{inf['id']}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("✅ Salvar Post", use_container_width=True):
                imagens_b64 = []
                if imagens_upload:
                    for img_file in imagens_upload:
                        img_bytes = img_file.read()
                        imagens_b64.append(base64.b64encode(img_bytes).decode())
                
                data_manager.adicionar_post(campanha['id'], inf['id'], {
                    'formato': formato,
                    'plataforma': plataforma,
                    'data_publicacao': data_pub.strftime('%d/%m/%Y'),
                    'link_post': link_post,
                    'views': views,
                    'interacoes': interacoes,
                    'curtidas': curtidas,
                    'comentarios_qtd': comentarios,
                    'compartilhamentos': compartilhamentos,
                    'saves': saves,
                    'clique_link': clique_link,
                    'cupom_codigo': cupom_codigo,
                    'cupom_conversoes': cupom_conversoes,
                    'imagens': imagens_b64
                })
                st.session_state.show_add_post = False
                st.success("✅ Post adicionado com sucesso!")
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                st.session_state.show_add_post = False
                st.rerun()


def render_post_item(campanha, inf, post):
    """Renderiza item de post na lista"""
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.write(f"**{post['formato']}** ({post['plataforma']})")
        st.caption(post['data_publicacao'])
    
    with col2:
        st.write(f"👁️ {post['metricas']['views']:,}")
    
    with col3:
        st.write(f"💬 {post['metricas']['interacoes']:,}")
    
    with col4:
        if st.button("Ver Detalhes", key=f"view_{post['id']}_{inf['id']}", use_container_width=True):
            st.session_state.view_post_id = post['id']
            st.session_state.view_influencer_id = inf['id']
    
    # Detalhes do post
    if (st.session_state.get('view_post_id') == post['id'] and 
        st.session_state.get('view_influencer_id') == inf['id']):
        
        st.markdown("---")
        render_post_detalhes(campanha, inf, post)


def render_post_detalhes(campanha, inf, post):
    """Renderiza detalhes completos do post"""
    
    st.markdown("#### 📊 Detalhes Completos do Post")
    
    # Imagens
    if post['imagens']:
        st.markdown("**📷 Mídias do Post:**")
        cols_img = st.columns(min(len(post['imagens']), 4))
        for idx, img_b64 in enumerate(post['imagens']):
            with cols_img[idx % 4]:
                try:
                    img_bytes = base64.b64decode(img_b64)
                    st.image(img_bytes, use_container_width=True)
                except:
                    st.caption("Erro ao carregar mídia")
    
    st.markdown("**📈 Métricas Completas:**")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Views", f"{post['metricas']['views']:,}")
    with col2:
        st.metric("Curtidas", f"{post['metricas']['curtidas']:,}")
    with col3:
        st.metric("Comentários", f"{post['metricas']['comentarios_qtd']:,}")
    with col4:
        st.metric("Compartilh.", f"{post['metricas']['compartilhamentos']:,}")
    with col5:
        st.metric("Saves", f"{post['metricas']['saves']:,}")
    
    if post['metricas'].get('clique_link', 0) > 0:
        st.metric("🔗 Cliques em Link", f"{post['metricas']['clique_link']:,}")
    
    if post['metricas'].get('cupom_codigo'):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**🎟️ Cupom:** {post['metricas']['cupom_codigo']}")
        with col2:
            st.metric("Conversões", f"{post['metricas']['cupom_conversoes']:,}")
    
    if post['link_post']:
        st.markdown(f"**🔗 Link:** [{post['link_post']}]({post['link_post']})")
    
    st.markdown("---")
    
    # Adicionar comentários
    st.markdown("### 💬 Gerenciar Comentários para Análise")
    
    with st.form(f"form_comentario_{post['id']}_{inf['id']}"):
        texto_comentario = st.text_area(
            "Cole comentários das redes sociais aqui",
            placeholder="Exemplo: 'Adorei! Esse produto é o melhor!'",
            height=100
        )
        
        if st.form_submit_button("🤖 Adicionar e Analisar com IA"):
            if texto_comentario:
                analise = funcoes_auxiliares.analisar_sentimento_comentario(texto_comentario)
                comentario = {
                    'texto': texto_comentario,
                    'polaridade': analise['polaridade'],
                    'categoria': analise['categoria']
                }
                post['comentarios'].append(comentario)
                st.success(f"✅ Comentário analisado! **{analise['categoria']}** ({analise['polaridade']})")
                st.rerun()
            else:
                st.error("Digite um comentário")
    
    # Mostrar comentários classificados
    if post['comentarios']:
        st.markdown("**🤖 Comentários Classificados pela IA:**")
        
        positivos = len([c for c in post['comentarios'] if c['polaridade'] == 'positivo'])
        neutros = len([c for c in post['comentarios'] if c['polaridade'] == 'neutro'])
        negativos = len([c for c in post['comentarios'] if c['polaridade'] == 'negativo'])
        total_com = len(post['comentarios'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🟢 Positivos", f"{positivos}/{total_com}", 
                     f"{positivos/total_com*100:.1f}%" if total_com > 0 else "0%")
        with col2:
            st.metric("🟡 Neutros", f"{neutros}/{total_com}",
                     f"{neutros/total_com*100:.1f}%" if total_com > 0 else "0%")
        with col3:
            st.metric("🔴 Negativos", f"{negativos}/{total_com}",
                     f"{negativos/total_com*100:.1f}%" if total_com > 0 else "0%")
        
        st.markdown("**Últimos comentários:**")
        for com in post['comentarios'][:5]:
            cor = {"positivo": "🟢", "neutro": "🟡", "negativo": "🔴"}
            st.write(f"{cor[com['polaridade']]} **{com['categoria']}**: {com['texto'][:100]}...")
    else:
        st.info("💡 Adicione comentários para análise de sentimento automática")


def render_tab_big_numbers(campanha):
    """Tab 3: Big Numbers e Insights"""
    
    st.subheader("📊 Big Numbers - Visão Geral")
    
    metricas = data_manager.calcular_metricas_campanha(campanha)
    air_score = funcoes_auxiliares.calcular_air_score(campanha)
    
    # AIR Score destacado
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown(f"""
        <div class='air-score-card'>
            <div class='air-score-number'>{air_score}</div>
            <div class='air-score-label'>AIR SCORE</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📱 Posts", metricas['total_posts'])
        with col2:
            st.metric("👁️ Views", f"{metricas['total_views']:,}")
        with col3:
            st.metric("💬 Interações", f"{metricas['total_interacoes']:,}")
        with col4:
            st.metric("📈 Eng. Efetivo", f"{metricas['engajamento_efetivo']}%")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("❤️ Curtidas", f"{metricas['total_curtidas']:,}")
        with col2:
            st.metric("💭 Comentários", f"{metricas['total_comentarios']:,}")
        with col3:
            st.metric("💾 Saves", f"{metricas['total_saves']:,}")
        with col4:
            if metricas['total_conversoes_cupom'] > 0:
                st.metric("🎟️ Conversões", f"{metricas['total_conversoes_cupom']:,}")
            else:
                st.metric("🔄 Compartilh.", f"{metricas['total_compartilhamentos']:,}")
    
    st.markdown("---")
    
    if metricas['total_posts'] == 0:
        st.info("📭 Adicione posts aos influenciadores para ver análises")
        return
    
    # GRÁFICOS DE PERFORMANCE
    st.subheader("📈 Performance por Formato")
    
    dados_formato = []
    for inf in campanha['influenciadores']:
        for post in inf['posts']:
            dados_formato.append({
                'Formato': post['formato'],
                'Views': post['metricas']['views'],
                'Interações': post['metricas']['interacoes'],
                'Saves': post['metricas']['saves']
            })
    
    if dados_formato:
        df_formato = pd.DataFrame(dados_formato)
        df_formato_agg = df_formato.groupby('Formato').sum().reset_index()
        df_formato_agg['Engajamento %'] = (df_formato_agg['Interações'] / df_formato_agg['Views'] * 100).round(2)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(df_formato_agg, x='Formato', y='Views',
                        title='Views por Formato de Conteúdo',
                        color='Views',
                        color_continuous_scale='Purples')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig2 = px.pie(df_formato_agg, values='Interações', names='Formato',
                         title='Distribuição de Interações por Formato')
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    
    # DESEMPENHO POR CLASSIFICAÇÃO
    st.subheader("⭐ Performance por Tamanho de Influenciador")
    
    dados_class = []
    for inf in campanha['influenciadores']:
        for post in inf['posts']:
            eng_post = (post['metricas']['interacoes'] / post['metricas']['views'] * 100) if post['metricas']['views'] > 0 else 0
            dados_class.append({
                'Classificação': inf['classificacao'],
                'Views': post['metricas']['views'],
                'Interações': post['metricas']['interacoes'],
                'Engajamento': eng_post
            })
    
    if dados_class:
        df_class = pd.DataFrame(dados_class)
        df_class_agg = df_class.groupby('Classificação').agg({
            'Views': 'sum',
            'Interações': 'sum',
            'Engajamento': 'mean'
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(df_class_agg, x='Classificação', y='Views',
                        title='Views por Classificação de Influenciador',
                        color='Views',
                        color_continuous_scale='Viridis',
                        category_orders={'Classificação': ['Nano', 'Micro', 'Mid', 'Macro', 'Mega']})
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig2 = px.bar(df_class_agg, x='Classificação', y='Engajamento',
                         title='Taxa de Engajamento Média por Classificação (%)',
                         color='Engajamento',
                         color_continuous_scale='Blues',
                         category_orders={'Classificação': ['Nano', 'Micro', 'Mid', 'Macro', 'Mega']})
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
    
    st.markdown("---")
    
    # INSIGHTS AUTOMÁTICOS
    st.subheader("💡 Insights Automáticos Gerados")
    
    # Melhor formato
    if dados_formato:
        melhor_formato = df_formato_agg.loc[df_formato_agg['Views'].idxmax()]
        st.success(f"📱 **Formato Mais Efetivo:** {melhor_formato['Formato']} gerou {melhor_formato['Views']:,} views e {melhor_formato['Interações']:,} interações")
    
    # Melhor classificação
    if dados_class:
        melhor_class = df_class_agg.loc[df_class_agg['Engajamento'].idxmax()]
        st.info(f"⭐ **Melhor Performance:** Influenciadores **{melhor_class['Classificação']}** têm taxa média de engajamento de {melhor_class['Engajamento']:.2f}%")
    
    # Engajamento geral
    if metricas['engajamento_efetivo'] > 5:
        st.success(f"📈 **Engajamento Excelente:** Taxa de {metricas['engajamento_efetivo']}% está acima da referência de mercado (3-5%)")
    elif metricas['engajamento_efetivo'] > 3:
        st.info(f"📊 **Engajamento Adequado:** Taxa de {metricas['engajamento_efetivo']}% está dentro da referência de mercado")
    else:
        st.warning(f"⚠️ **Atenção:** Taxa de {metricas['engajamento_efetivo']}% está abaixo da referência. Considere ajustar a estratégia")
    
    # Saves
    if metricas['total_saves'] > 0:
        taxa_saves = (metricas['total_saves'] / metricas['total_views'] * 100)
        if taxa_saves > 2:
            st.success(f"💾 **Alto Valor Percebido:** {metricas['total_saves']:,} saves ({taxa_saves:.2f}% dos views). Conteúdo está sendo guardado para referência!")
    
    # Conversões
    if metricas['total_conversoes_cupom'] > 0:
        st.success(f"🎟️ **ROI Rastreável:** {metricas['total_conversoes_cupom']} conversões via cupom. Impacto mensurável!")


def render_tab_graficos_dinamicos_aon(campanha):
    """Tab 4 (AON): Gráficos Dinâmicos com Evolução Temporal"""
    
    st.subheader("📈 Gráficos Dinâmicos - Evolução Temporal")
    st.caption("🌟 Funcionalidade exclusiva para clientes AON")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if campanha['influenciadores']:
            influs_opcoes = ["Todos"] + [inf['nome'] for inf in campanha['influenciadores']]
            filtro_influ = st.selectbox("Influenciador", influs_opcoes)
        else:
            filtro_influ = "Todos"
    
    with col2:
        data_inicio_filtro = st.date_input("Período: De", value=datetime.now() - timedelta(days=30))
    
    with col3:
        data_fim_filtro = st.date_input("Até", value=datetime.now())
    
    st.markdown("---")
    
    # Coletar dados temporais
    if not campanha['influenciadores'] or not any(inf['posts'] for inf in campanha['influenciadores']):
        st.info("📭 Adicione posts com datas para visualizar evolução temporal")
        return
    
    dados_tempo = []
    
    for inf in campanha['influenciadores']:
        if filtro_influ != "Todos" and inf['nome'] != filtro_influ:
            continue
        
        for post in inf['posts']:
            try:
                data_post = datetime.strptime(post['data_publicacao'], '%d/%m/%Y')
                
                # Filtrar por período
                if data_inicio_filtro <= data_post.date() <= data_fim_filtro.date():
                    dados_tempo.append({
                        'Data': data_post,
                        'Views': post['metricas']['views'],
                        'Interações': post['metricas']['interacoes'],
                        'Saves': post['metricas']['saves'],
                        'Engajamento': (post['metricas']['interacoes'] / post['metricas']['views'] * 100) if post['metricas']['views'] > 0 else 0,
                        'Influenciador': inf['nome'],
                        'Formato': post['formato']
                    })
            except:
                pass
    
    if not dados_tempo:
        st.warning("⚠️ Nenhum post no período selecionado")
        return
    
    df_tempo = pd.DataFrame(dados_tempo)
    df_tempo = df_tempo.sort_values('Data')
    
    # Gráfico 1: Evolução de Views
    st.subheader("📊 Evolução de Views ao Longo do Tempo")
    fig1 = px.line(df_tempo, x='Data', y='Views',
                  markers=True,
                  color='Influenciador' if filtro_influ == "Todos" else None,
                  title='Views por Data de Publicação')
    fig1.update_layout(height=400)
    st.plotly_chart(fig1, use_container_width=True)
    
    # Gráficos lado a lado
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💬 Interações por Data")
        fig2 = px.bar(df_tempo, x='Data', y='Interações',
                     color='Influenciador' if filtro_influ == "Todos" else None,
                     title='Interações Acumuladas')
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        st.subheader("📈 Taxa de Engajamento")
        fig3 = px.scatter(df_tempo, x='Views', y='Interações',
                         size='Saves',
                         color='Influenciador' if filtro_influ == "Todos" else None,
                         hover_data=['Formato', 'Engajamento'],
                         title='Relação Views x Interações')
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)
    
    # Gráfico de formato ao longo do tempo
    st.subheader("📱 Performance por Formato no Período")
    df_formato_tempo = df_tempo.groupby(['Data', 'Formato']).agg({
        'Views': 'sum',
        'Interações': 'sum'
    }).reset_index()
    
    fig4 = px.area(df_formato_tempo, x='Data', y='Views',
                   color='Formato',
                   title='Views por Formato ao Longo do Tempo')
    fig4.update_layout(height=400)
    st.plotly_chart(fig4, use_container_width=True)
    
    # Estatísticas do período
    st.markdown("---")
    st.subheader("📊 Estatísticas do Período Selecionado")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Posts", len(df_tempo))
    with col2:
        st.metric("Views Totais", f"{df_tempo['Views'].sum():,}")
    with col3:
        st.metric("Interações Totais", f"{df_tempo['Interações'].sum():,}")
    with col4:
        st.metric("Eng. Médio", f"{df_tempo['Engajamento'].mean():.2f}%")


def render_tab_kpis_dinamicos(campanha):
    """Tab: KPIs Dinâmicos por Influenciador"""
    
    st.subheader("📉 KPIs Dinâmicos por Influenciador")
    st.caption("Visualize diferentes métricas e compare até 30 influenciadores")
    
    # Seletores de métricas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎯 KPIs de Awareness:**")
        kpi_awareness = st.radio("", ["Views", "Alcance Único (Estimado)"], key="kpi_aw")
        
        st.markdown("**📈 KPIs de Engajamento:**")
        kpi_engajamento = st.radio("", ["Interações Totais", "Taxa de Engajamento (%)"], key="kpi_eng")
    
    with col2:
        st.markdown("**💰 Taxas de Eficiência:**")
        taxa_eficiencia = st.radio("", ["CPM (Custo por Mil)", "Custo por Interação"], key="taxa_ef")
        
        st.markdown("**🔗 Métricas de Tráfego:**")
        taxa_trafego = st.radio("", ["Cliques em Link", "Taxa de Cliques (CTR %)"], key="taxa_tr")
    
    st.markdown("---")
    
    if not campanha['influenciadores'] or not any(inf['posts'] for inf in campanha['influenciadores']):
        st.info("📭 Adicione posts para visualizar KPIs")
        return
    
    # Preparar dados (limitado a 30 influenciadores)
    dados_influs = []
    
    for inf in campanha['influenciadores'][:30]:
        if not inf['posts']:
            continue
        
        total_views = sum([p['metricas']['views'] for p in inf['posts']])
        total_int = sum([p['metricas']['interacoes'] for p in inf['posts']])
        total_cliques = sum([p['metricas'].get('clique_link', 0) for p in inf['posts']])
        
        alcance_unico = int(total_views * 0.75)  # Estimado
        taxa_eng = (total_int / total_views * 100) if total_views > 0 else 0
        taxa_ctr = (total_cliques / total_views * 100) if total_views > 0 else 0
        
        # Simular custos
        custo_estimado = random.randint(500, 5000)
        cpm = (custo_estimado / total_views * 1000) if total_views > 0 else 0
        custo_int = (custo_estimado / total_int) if total_int > 0 else 0
        
        dados_influs.append({
            'Influenciador': inf['nome'],
            'Views': total_views,
            'Alcance Único (Estimado)': alcance_unico,
            'Interações Totais': total_int,
            'Taxa de Engajamento (%)': round(taxa_eng, 2),
            'CPM (Custo por Mil)': round(cpm, 2),
            'Custo por Interação': round(custo_int, 2),
            'Cliques em Link': total_cliques,
            'Taxa de Cliques (CTR %)': round(taxa_ctr, 2)
        })
    
    if not dados_influs:
        st.warning("Nenhum dado disponível")
        return
    
    df_influs = pd.DataFrame(dados_influs)
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # KPI Awareness
        fig1 = px.bar(df_influs, x='Influenciador', y=kpi_awareness,
                     title=f'{kpi_awareness} por Influenciador',
                     color=kpi_awareness,
                     color_continuous_scale='Blues')
        fig1.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)
        
        # Taxa Eficiência
        fig3 = px.bar(df_influs, x='Influenciador', y=taxa_eficiencia,
                     title=f'{taxa_eficiencia} por Influenciador',
                     color=taxa_eficiencia,
                     color_continuous_scale='Reds')
        fig3.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        # KPI Engajamento
        fig2 = px.bar(df_influs, x='Influenciador', y=kpi_engajamento,
                     title=f'{kpi_engajamento} por Influenciador',
                     color=kpi_engajamento,
                     color_continuous_scale='Greens')
        fig2.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Taxa Tráfego
        fig4 = px.bar(df_influs, x='Influenciador', y=taxa_trafego,
                     title=f'{taxa_trafego} por Influenciador',
                     color=taxa_trafego,
                     color_continuous_scale='Purples')
        fig4.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig4, use_container_width=True)


def render_tab_top_influenciadores(campanha):
    """Tab: Top Influenciadores"""
    
    st.subheader("⭐ Top Influenciadores - Ranking de Performance")
    
    if not campanha['influenciadores'] or not any(inf['posts'] for inf in campanha['influenciadores']):
        st.info("📭 Adicione posts para ver o ranking")
        return
    
    # Calcular métricas por influenciador
    dados_top = []
    
    for inf in campanha['influenciadores']:
        if not inf['posts']:
            continue
        
        total_views = sum([p['metricas']['views'] for p in inf['posts']])
        total_int = sum([p['metricas']['interacoes'] for p in inf['posts']])
        taxa_eng = (total_int / total_views * 100) if total_views > 0 else 0
        
        dados_top.append({
            'Influenciador': inf['nome'],
            'Classificação': inf['classificacao'],
            'Alcance': total_views,
            'Engajamento': total_int,
            'Taxa Eng. %': round(taxa_eng, 2),
            'Posts': len(inf['posts'])
        })
    
    df_top = pd.DataFrame(dados_top)
    
    # Gráfico de bolhas
    st.markdown("### 💫 Mapa de Performance: Alcance vs Engajamento")
    
    fig = px.scatter(df_top, x='Alcance', y='Engajamento',
                    size='Posts', color='Classificação',
                    hover_data=['Taxa Eng. %'],
                    text='Influenciador',
                    title='Posicionamento de Influenciadores',
                    size_max=60)
    fig.update_traces(textposition='top center')
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Top 5 Rankings
    st.subheader("🏆 Top 5 Rankings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**👁️ Top 5 em Alcance:**")
        top_views = df_top.nlargest(5, 'Alcance')[['Influenciador', 'Alcance']]
        for idx, row in top_views.iterrows():
            st.write(f"**{row['Influenciador']}**: {row['Alcance']:,}")
    
    with col2:
        st.markdown("**📈 Top 5 em Engajamento:**")
        top_eng = df_top.nlargest(5, 'Taxa Eng. %')[['Influenciador', 'Taxa Eng. %']]
        for idx, row in top_eng.iterrows():
            st.write(f"**{row['Influenciador']}**: {row['Taxa Eng. %']}%")
    
    with col3:
        st.markdown("**🔥 Mais Ativos:**")
        top_posts = df_top.nlargest(5, 'Posts')[['Influenciador', 'Posts']]
        for idx, row in top_posts.iterrows():
            st.write(f"**{row['Influenciador']}**: {row['Posts']} posts")
    
    st.markdown("---")
    
    # Tabela completa
    st.subheader("📊 Tabela Completa de Performance")
    df_top_sorted = df_top.sort_values('Engajamento', ascending=False)
    st.dataframe(df_top_sorted, use_container_width=True, hide_index=True)


def render_tab_top_conteudo(campanha):
    """Tab: Top Conteúdo com Análise Criativa"""
    
    st.subheader("🎬 Top Conteúdo - Melhores Posts da Campanha")
    
    if not campanha['influenciadores'] or not any(inf['posts'] for inf in campanha['influenciadores']):
        st.info("📭 Adicione posts para ver o top conteúdo")
        return
    
    # Coletar todos os posts
    todos_posts = []
    
    for inf in campanha['influenciadores']:
        for post in inf['posts']:
            taxa_eng = (post['metricas']['interacoes'] / post['metricas']['views'] * 100) if post['metricas']['views'] > 0 else 0
            
            todos_posts.append({
                'influenciador': inf['nome'],
                'classificacao': inf['classificacao'],
                'formato': post['formato'],
                'plataforma': post['plataforma'],
                'views': post['metricas']['views'],
                'engajamento': post['metricas']['interacoes'],
                'saves': post['metricas']['saves'],
                'taxa_eng': taxa_eng,
                'imagens': post['imagens'],
                'link': post.get('link_post', ''),
                'data': post['data_publicacao']
            })
    
    # Ordenar por engajamento
    todos_posts.sort(key=lambda x: x['engajamento'], reverse=True)
    
    # Top 10
    st.markdown("### 🏆 Top 10 Posts por Engajamento")
    
    for idx, post in enumerate(todos_posts[:10], 1):
        with st.expander(f"#{idx} - {post['influenciador']} - {post['formato']} ({post['views']:,} views)"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Mostrar mídia se disponível
                if post['imagens']:
                    try:
                        img_bytes = base64.b64decode(post['imagens'][0])
                        st.image(img_bytes, use_container_width=True, caption="Post")
                    except:
                        st.info("📷 Mídia indisponível")
                else:
                    st.info("📷 Sem mídia")
            
            with col2:
                st.write(f"**Influenciador:** {post['influenciador']} ({post['classificacao']})")
                st.write(f"**Formato:** {post['formato']} ({post['plataforma']})")
                st.write(f"**Data:** {post['data']}")
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Views", f"{post['views']:,}")
                with col_b:
                    st.metric("Engajamento", f"{post['engajamento']:,}")
                with col_c:
                    st.metric("Taxa Eng.", f"{post['taxa_eng']:.2f}%")
                
                if post['link']:
                    st.markdown(f"[🔗 Ver Post Original]({post['link']})")
                
                # ANÁLISE CRIATIVA
                st.markdown("**💡 Análise Criativa Automática:**")
                
                analise_criativa = []
                
                if post['formato'] == 'Reels':
                    analise_criativa.append("✅ **Formato Reels** é excelente para alcance orgânico e viralização")
                elif post['formato'] == 'Stories':
                    analise_criativa.append("✅ **Stories** geram proximidade e urgência com a audiência")
                elif post['formato'] == 'Carrossel':
                    analise_criativa.append("✅ **Carrosséis** têm alto tempo de permanência no conteúdo")
                
                if post['taxa_eng'] > 5:
                    analise_criativa.append("🔥 **Taxa de engajamento excepcional!** Acima de 5%")
                elif post['taxa_eng'] > 3:
                    analise_criativa.append("✅ Taxa de engajamento saudável (acima de 3%)")
                
                if post['saves'] > post['views'] * 0.02:
                    analise_criativa.append("💾 **Alto valor percebido**: Taxa de saves acima de 2%")
                
                if post['classificacao'] in ['Nano', 'Micro']:
                    analise_criativa.append(f"⭐ Influenciador **{post['classificacao']}** com engajamento autêntico")
                
                for analise in analise_criativa:
                    st.write(analise)
                
                st.success("💡 **Recomendação**: Replicar estilo criativo e abordagem deste post")


def render_tab_analise_detalhada(campanha):
    """Tab: Análise Detalhada por Influenciador"""
    
    st.subheader("📋 Análise Detalhada de Performance")
    
    if not campanha['influenciadores'] or not any(inf['posts'] for inf in campanha['influenciadores']):
        st.info("📭 Adicione posts para ver análises detalhadas")
        return
    
    # Calcular métricas completas
    analise_influs = []
    
    for inf in campanha['influenciadores']:
        if not inf['posts']:
            continue
        
        total_views = sum([p['metricas']['views'] for p in inf['posts']])
        total_int = sum([p['metricas']['interacoes'] for p in inf['posts']])
        total_saves = sum([p['metricas']['saves'] for p in inf['posts']])
        total_curtidas = sum([p['metricas']['curtidas'] for p in inf['posts']])
        total_comentarios = sum([p['metricas']['comentarios_qtd'] for p in inf['posts']])
        total_posts = len(inf['posts'])
        
        media_views = total_views / total_posts
        media_int = total_int / total_posts
        taxa_eng = (total_int / total_views * 100) if total_views > 0 else 0
        
        analise_influs.append({
            'Influenciador': inf['nome'],
            'Classificação': inf['classificacao'],
            'Total Posts': total_posts,
            'Total Views': total_views,
            'Total Interações': total_int,
            'Total Curtidas': total_curtidas,
            'Total Comentários': total_comentarios,
            'Total Saves': total_saves,
            'Média Views/Post': int(media_views),
            'Média Int/Post': int(media_int),
            'Taxa Eng. (%)': round(taxa_eng, 2)
        })
    
    df_analise = pd.DataFrame(analise_influs)
    df_analise = df_analise.sort_values('Taxa Eng. (%)', ascending=False)
    
    # Tabela completa
    st.markdown("### 📊 Tabela Completa de Performance")
    st.dataframe(df_analise, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Rankings por métrica
    st.subheader("🏆 Rankings por Métrica")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**👁️ Top 5 em Views Totais:**")
        top = df_analise.nlargest(5, 'Total Views')
        for _, row in top.iterrows():
            st.write(f"{row['Influenciador']}: **{row['Total Views']:,}**")
    
    with col2:
        st.markdown("**📈 Top 5 em Taxa de Engajamento:**")
        top = df_analise.nlargest(5, 'Taxa Eng. (%)')
        for _, row in top.iterrows():
            st.write(f"{row['Influenciador']}: **{row['Taxa Eng. (%)']:.2f}%**")
    
    with col3:
        st.markdown("**💾 Top 5 em Saves:**")
        top = df_analise.nlargest(5, 'Total Saves')
        for _, row in top.iterrows():
            st.write(f"{row['Influenciador']}: **{row['Total Saves']:,}**")
    
    st.markdown("---")
    
    # Melhor por classificação
    st.subheader("⭐ Melhor Desempenho por Classificação")
    
    for classe in df_analise['Classificação'].unique():
        df_classe = df_analise[df_analise['Classificação'] == classe]
        if not df_classe.empty:
            melhor = df_classe.loc[df_classe['Taxa Eng. (%)'].idxmax()]
            
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{classe}**: {melhor['Influenciador']}")
            with col2:
                st.write(f"Taxa Eng.: {melhor['Taxa Eng. (%)']:.2f}%")
            with col3:
                st.write(f"{melhor['Total Posts']} posts")


def render_tab_visao_comentarios(campanha):
    """Tab: Visão de Comentários com Análise de Sentimento"""
    
    st.subheader("💬 Análise de Comentários por IA")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        visao = st.radio("Visão:", ["Campanha Geral", "Por Influenciador", "Por Post"])
    
    with col2:
        filtro_polaridade = st.multiselect("Polaridade:", ["positivo", "neutro", "negativo"])
    
    with col3:
        filtro_categoria = st.multiselect("Categoria:", 
                                         ["Elogio ao Produto", "Conexão Emocional", 
                                          "Intenção de Compra", "Dúvida", "Crítica", "Geral"])
    
    st.markdown("---")
    
    # Coletar comentários
    todos_comentarios = []
    
    for inf in campanha['influenciadores']:
        for post in inf['posts']:
            for com in post.get('comentarios', []):
                # Aplicar filtros
                if filtro_polaridade and com['polaridade'] not in filtro_polaridade:
                    continue
                if filtro_categoria and com['categoria'] not in filtro_categoria:
                    continue
                
                todos_comentarios.append({
                    'influenciador': inf['nome'],
                    'post': f"{post['formato']} - {post['data_publicacao']}",
                    'texto': com['texto'],
                    'polaridade': com['polaridade'],
                    'categoria': com['categoria']
                })
    
    if not todos_comentarios:
        st.info("💬 Nenhum comentário classificado ainda")
        
        with st.expander("💡 Como usar esta funcionalidade"):
            st.markdown("""
            **Passo a passo:**
            
            1. Vá até a aba **Influenciadores**
            2. Abra um influenciador e clique em **Ver Detalhes** de um post
            3. Role até a seção **Gerenciar Comentários**
            4. Cole comentários reais das redes sociais
            5. Clique em **Adicionar e Analisar com IA**
            6. A IA classificará automaticamente
            7. Volte aqui para ver análises completas
            
            **A IA classifica em:**
            - 🟢 **Positivo**: Elogios, satisfação
            - 🟡 **Neutro**: Perguntas, informações
            - 🔴 **Negativo**: Críticas, insatisfação
            
            **Categorias:**
            - Elogio ao Produto
            - Conexão Emocional (nostalgia)
            - Intenção de Compra
            - Dúvida
            - Crítica
            """)
        return
    
    # Estatísticas gerais
    total_com = len(todos_comentarios)
    positivos = len([c for c in todos_comentarios if c['polaridade'] == 'positivo'])
    neutros = len([c for c in todos_comentarios if c['polaridade'] == 'neutro'])
    negativos = len([c for c in todos_comentarios if c['polaridade'] == 'negativo'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Comentários", total_com)
    with col2:
        st.metric("🟢 Positivos", positivos, f"{positivos/total_com*100:.1f}%")
    with col3:
        st.metric("🟡 Neutros", neutros, f"{neutros/total_com*100:.1f}%")
    with col4:
        st.metric("🔴 Negativos", negativos, f"{negativos/total_com*100:.1f}%")
    
    st.markdown("---")
    
    # Distribuição por categoria
    st.subheader("📊 Distribuição por Categoria")
    
    categorias_count = Counter([c['categoria'] for c in todos_comentarios])
    df_cat = pd.DataFrame(categorias_count.items(), columns=['Categoria', 'Quantidade'])
    
    fig = px.bar(df_cat, x='Categoria', y='Quantidade',
                title='Comentários por Categoria',
                color='Quantidade',
                color_continuous_scale='Viridis')
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Mostrar comentários baseado na visão
    if visao == "Campanha Geral":
        st.subheader("📝 Comentários Aderentes à Campanha")
        
        for com in todos_comentarios[:20]:
            cor = {"positivo": "🟢", "neutro": "🟡", "negativo": "🔴"}
            st.write(f"{cor[com['polaridade']]} **{com['categoria']}** - {com['influenciador']}")
            st.caption(com['texto'])
            st.markdown("---")
    
    elif visao == "Por Influenciador":
        # Agrupar por influenciador
        influs_com = {}
        for com in todos_comentarios:
            if com['influenciador'] not in influs_com:
                influs_com[com['influenciador']] = []
            influs_com[com['influenciador']].append(com)
        
        for influ_nome, comentarios in influs_com.items():
            with st.expander(f"👤 {influ_nome} ({len(comentarios)} comentários)"):
                pos = len([c for c in comentarios if c['polaridade'] == 'positivo'])
                neu = len([c for c in comentarios if c['polaridade'] == 'neutro'])
                neg = len([c for c in comentarios if c['polaridade'] == 'negativo'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Positivos", f"{pos} ({pos/len(comentarios)*100:.0f}%)")
                with col2:
                    st.metric("Neutros", f"{neu} ({neu/len(comentarios)*100:.0f}%)")
                with col3:
                    st.metric("Negativos", f"{neg} ({neg/len(comentarios)*100:.0f}%)")
                
                for com in comentarios[:10]:
                    cor = {"positivo": "🟢", "neutro": "🟡", "negativo": "🔴"}
                    st.write(f"{cor[com['polaridade']]} **{com['categoria']}**: {com['texto'][:100]}...")
    
    elif visao == "Por Post":
        # Agrupar por post
        posts_com = {}
        for com in todos_comentarios:
            key = f"{com['influenciador']} - {com['post']}"
            if key not in posts_com:
                posts_com[key] = []
            posts_com[key].append(com)
        
        for post_key, comentarios in posts_com.items():
            with st.expander(f"📱 {post_key} ({len(comentarios)} comentários)"):
                for com in comentarios[:5]:
                    cor = {"positivo": "🟢", "neutro": "🟡", "negativo": "🔴"}
                    st.write(f"{cor[com['polaridade']]} **{com['categoria']}**: {com['texto'][:150]}...")
                    st.markdown("---")


def render_tab_nuvem_palavras(campanha):
    """Tab: Nuvem de Palavras e Principais Assuntos"""
    
    st.subheader("☁️ Nuvem de Palavras e Análise de Assuntos")
    
    # Coletar comentários
    todos_comentarios = []
    for inf in campanha['influenciadores']:
        for post in inf['posts']:
            todos_comentarios.extend(post.get('comentarios', []))
    
    if not todos_comentarios:
        st.info("💬 Adicione comentários aos posts para gerar a nuvem de palavras")
        
        with st.expander("💡 Como funciona"):
            st.markdown("""
            A **Nuvem de Palavras** analisa automaticamente todos os comentários e:
            
            1. 🔍 **Extrai palavras-chave** mais mencionadas
            2. ☁️ **Gera visualização** com tamanho proporcional
            3. 📊 **Identifica assuntos** principais
            4. 💬 **Destaca comentários** relevantes
            
            **Para usar:**
            - Adicione comentários aos posts
            - A IA classificará automaticamente
            - Volte aqui para ver os insights
            """)
        return
    
    # Extrair palavras-chave
    palavras_chave = funcoes_auxiliares.extrair_palavras_chave(todos_comentarios)
    
    if not palavras_chave:
        st.warning("Não foi possível extrair palavras-chave")
        return
    
    # Top 20 palavras
    st.markdown("### 🔤 Palavras Mais Mencionadas")
    
    df_palavras = pd.DataFrame(palavras_chave[:20], columns=['Palavra', 'Frequência'])
    
    fig = px.bar(df_palavras, x='Palavra', y='Frequência',
                title='Top 20 Palavras nos Comentários',
                color='Frequência',
                color_continuous_scale='Viridis')
    fig.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Nuvem visual (simulada com HTML)
    st.markdown("### ☁️ Nuvem de Palavras")
    
    palavras_html = ""
    for palavra, freq in palavras_chave[:30]:
        tamanho = min(12 + (freq / 2), 40)
        cor_r = random.randint(100, 200)
        cor_g = random.randint(50, 150)
        cor_b = random.randint(150, 250)
        palavras_html += f"<span style='font-size: {tamanho}px; margin: 10px; color: rgb({cor_r},{cor_g},{cor_b}); font-weight: 600;'>{palavra}</span> "
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                padding: 3rem; border-radius: 16px; text-align: center; 
                line-height: 3; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        {palavras_html}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Principais assuntos por categoria
    st.markdown("### 📌 Principais Assuntos Identificados")
    
    categorias = Counter([c['categoria'] for c in todos_comentarios])
    
    for categoria, qtd in categorias.most_common():
        with st.expander(f"📂 {categoria} ({qtd} menções)"):
            comentarios_cat = [c for c in todos_comentarios if c['categoria'] == categoria]
            
            st.markdown("**Exemplos de comentários:**")
            for com in comentarios_cat[:5]:
                cor = {"positivo": "🟢", "neutro": "🟡", "negativo": "🔴"}
                st.write(f"{cor[com['polaridade']]} _{com['texto'][:120]}..._")
            
            # Palavras específicas
            palavras_cat = funcoes_auxiliares.extrair_palavras_chave(comentarios_cat)
            if palavras_cat:
                st.markdown("**Palavras-chave desta categoria:**")
                palavras_str = ", ".join([f"**{p[0]}** ({p[1]}x)" for p in palavras_cat[:10]])
                st.markdown(palavras_str)
    
    st.markdown("---")
    
    # Comentários em destaque
    st.markdown("### 📸 Comentários em Destaque")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**💚 Mais Positivos:**")
        positivos = [c for c in todos_comentarios if c['polaridade'] == 'positivo']
        for com in positivos[:3]:
            st.markdown(f"""
            <div style='background: #dcfce7; padding: 1rem; border-radius: 8px; 
                        margin-bottom: 0.5rem; border-left: 4px solid #22c55e;'>
                <strong>{com['categoria']}</strong><br>
                <em>"{com['texto'][:100]}..."</em>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("**💛 Intenção de Compra:**")
        compra = [c for c in todos_comentarios if c['categoria'] == 'Intenção de Compra']
        if compra:
            for com in compra[:3]:
                st.markdown(f"""
                <div style='background: #fef3c7; padding: 1rem; border-radius: 8px; 
                            margin-bottom: 0.5rem; border-left: 4px solid #f59e0b;'>
                    <strong>{com['categoria']}</strong><br>
                    <em>"{com['texto'][:100]}..."</em>
                </div>
                """, unsafe_allow_html=True)
        else:
            emocional = [c for c in todos_comentarios if c['categoria'] == 'Conexão Emocional']
            for com in emocional[:3]:
                st.markdown(f"""
                <div style='background: #fef3c7; padding: 1rem; border-radius: 8px; 
                            margin-bottom: 0.5rem; border-left: 4px solid #f59e0b;'>
                    <strong>{com['categoria']}</strong><br>
                    <em>"{com['texto'][:100]}..."</em>
                </div>
                """, unsafe_allow_html=True)


def render_tab_glossario():
    """Tab: Glossário Completo de Métricas"""
    
    st.subheader("📚 Glossário de Métricas e Termos")
    
    st.markdown("""
    Este glossário explica todos os termos e métricas utilizados no sistema AIR.
    """)
    
    st.markdown("---")
    
    # Métricas Básicas
    with st.expander("📊 MÉTRICAS BÁSICAS", expanded=True):
        st.markdown("""
        **Views (Visualizações)**
        - Número total de vezes que o conteúdo foi visualizado
        - Inclui visualizações repetidas do mesmo usuário
        - Métrica principal de alcance
        
        **Interações**
        - Soma de todas as ações: curtidas + comentários + compartilhamentos + saves
        - Indica o nível de engajamento geral
        
        **Curtidas (Likes)**
        - Número de curtidas/corações no post
        - Forma mais simples de engajamento
        
        **Comentários**
        - Número de comentários recebidos
        - Indica engajamento profundo e conversação
        
        **Compartilhamentos**
        - Quantas vezes o conteúdo foi compartilhado
        - Indica viralização e relevância
        
        **Saves (Salvamentos)**
        - Quantas vezes usuários salvaram o conteúdo
        - Indica alto valor percebido
        - Conteúdo considerado útil
        
        **Cliques em Link**
        - Específico para Stories
        - Indica interesse em saber mais
        - Direcionamento para conversão
        """)
    
    # Métricas Calculadas
    with st.expander("🧮 MÉTRICAS CALCULADAS"):
        st.markdown("""
        **Taxa de Engajamento (Engajamento Efetivo)**
        - Fórmula: (Interações / Views) × 100
        - Mostra % de pessoas que interagiram
        - Benchmark: 3-5% é bom, >5% é excelente
        
        **Taxa de Cliques (CTR)**
        - Fórmula: (Cliques / Views) × 100
        - Específico para Stories com link
        - Benchmark: >2% é bom
        
        **CPM (Custo Por Mil)**
        - Fórmula: (Investimento / Views) × 1000
        - Custo para alcançar 1000 pessoas
        - Quanto menor, mais eficiente
        
        **Custo por Interação**
        - Fórmula: Investimento / Interações
        - Quanto custa cada engajamento
        - Métrica de ROI
        
        **Taxa de Saves**
        - Fórmula: (Saves / Views) × 100
        - >2% indica conteúdo de referência
        """)
    
    # AIR Score
    with st.expander("⭐ AIR SCORE"):
        st.markdown("""
        **O que é o AIR Score?**
        - Métrica proprietária da AIR (0-100)
        - Avalia performance geral da campanha
        
        **Como é calculado:**
        - 40 pontos: Taxa de Engajamento
        - 30 pontos: Alcance (Views)
        - 15 pontos: Conversões (Cupom)
        - 15 pontos: Saves (Valor Percebido)
        
        **Interpretação:**
        - 0-40: Performance baixa
        - 41-60: Performance média
        - 61-80: Performance boa
        - 81-100: Performance excelente
        """)
    
    # Classificação de Influenciadores
    with st.expander("👥 CLASSIFICAÇÃO DE INFLUENCIADORES"):
        st.markdown("""
        **Nano (< 10K seguidores)**
        - Alta proximidade com audiência
        - Taxa de engajamento: 5-10%
        - Ótimo para nichos específicos
        
        **Micro (10K - 100K)**
        - Bom equilíbrio alcance/engajamento
        - Taxa de engajamento: 3-7%
        - Excelente custo-benefício
        
        **Mid (100K - 500K)**
        - Alcance significativo
        - Taxa de engajamento: 2-5%
        - Boa visibilidade de marca
        
        **Macro (500K - 1M)**
        - Grande alcance
        - Taxa de engajamento: 1-3%
        - Investimento elevado
        
        **Mega (> 1M)**
        - Alcance massivo
        - Taxa de engajamento: 0.5-2%
        - Celebridades e grandes influenciadores
        """)
    
    # Formatos
    with st.expander("📱 FORMATOS DE CONTEÚDO"):
        st.markdown("""
        **Reels (Instagram/TikTok)**
        - Vídeos curtos (15-90s)
        - Alto potencial de viralização
        - Priorizado pelos algoritmos
        
        **Stories**
        - Conteúdo efêmero (24h)
        - Alta proximidade
        - Único formato com swipe-up/link
        
        **Carrossel**
        - Múltiplas imagens/vídeos
        - Alto tempo de permanência
        - Bom para tutoriais
        
        **Feed**
        - Post tradicional de imagem
        - Permanente no perfil
        - Conteúdo evergreen
        
        **YouTube**
        - Vídeos longos
        - Conteúdo aprofundado
        - SEO e descoberta a longo prazo
        """)
    
    # Análise de Sentimento
    with st.expander("🤖 ANÁLISE DE SENTIMENTO (IA)"):
        st.markdown("""
        **Polaridade:**
        
        🟢 **Positivo** - Comentários favoráveis, elogios
        🟡 **Neutro** - Perguntas, informações
        🔴 **Negativo** - Críticas, insatisfação
        
        **Categorias:**
        
        **Elogio ao Produto** - Comentários positivos sobre qualidade
        **Conexão Emocional** - Nostalgia, memórias afetivas
        **Intenção de Compra** - "Quero comprar", "Onde encontro?"
        **Dúvida** - Perguntas sobre preço, disponibilidade
        **Crítica** - Feedback negativo, pontos de melhoria
        **Geral** - Comentários diversos
        """)
    
    # Termos Técnicos
    with st.expander("🔤 TERMOS TÉCNICOS"):
        st.markdown("""
        **Awareness (Conscientização)**
        - Métrica de conhecimento da marca
        - Medida principalmente por alcance
        
        **Engajamento**
        - Interação ativa do usuário
        - Indica interesse e conexão
        
        **Conversão**
        - Ação final desejada (compra, cadastro)
        - Último estágio do funil
        
        **ROI (Return on Investment)**
        - Retorno sobre investimento
        - Compara ganhos vs custos
        
        **KPI (Key Performance Indicator)**
        - Indicadores-chave de performance
        - Variam conforme objetivo
        
        **Benchmark**
        - Referência de mercado
        - Padrão para comparação
        """)
    
    st.markdown("---")
    
    st.markdown(f"""
    <div style='background: #f9fafb; padding: 1.5rem; border-radius: 12px; 
                border-left: 4px solid {st.session_state.primary_color};'>
        <strong>💡 Dica:</strong> Use este glossário como referência ao analisar campanhas. 
        Entender as métricas é essencial para tomar decisões estratégicas informadas.
    </div>
    """, unsafe_allow_html=True)

