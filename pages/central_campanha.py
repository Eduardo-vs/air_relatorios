"""
Pagina: Central da Campanha
Gerenciamento de influenciadores, posts e configuracoes da campanha
"""

import streamlit as st
from datetime import datetime
import base64
from utils import data_manager, funcoes_auxiliares

def render():
    """Renderiza central de controle da campanha"""
    
    campanha = data_manager.get_campanha(st.session_state.campanha_atual_id)
    
    if not campanha:
        st.warning("Selecione uma campanha na barra lateral")
        return
    
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        aon_badge = "[AON]" if campanha.get('is_aon') else ""
        st.markdown(f'<p class="main-header">Central: {campanha["nome"]} {aon_badge}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="subtitle">{campanha.get("cliente_nome", "")} | {funcoes_auxiliares.formatar_data_br(campanha["data_inicio"])} - {funcoes_auxiliares.formatar_data_br(campanha["data_fim"])}</p>', unsafe_allow_html=True)
    with col2:
        if st.button("Ver Relatorio", type="primary", use_container_width=True):
            st.session_state.modo_relatorio = 'campanha'
            st.session_state.current_page = 'Relatorios'
            st.rerun()
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Influenciadores e Posts",
        "Configuracoes da Campanha",
        "Configurar Insights",
        "Categorias de Comentarios"
    ])
    
    # ========================================
    # TAB 1: INFLUENCIADORES E POSTS
    # ========================================
    with tab1:
        render_influenciadores_posts(campanha)
    
    # ========================================
    # TAB 2: CONFIGURACOES DA CAMPANHA
    # ========================================
    with tab2:
        render_configuracoes_campanha(campanha)
    
    # ========================================
    # TAB 3: CONFIGURAR INSIGHTS
    # ========================================
    with tab3:
        render_configurar_insights(campanha)
    
    # ========================================
    # TAB 4: CATEGORIAS DE COMENTARIOS
    # ========================================
    with tab4:
        render_categorias_comentarios(campanha)


def render_influenciadores_posts(campanha):
    """Gerencia influenciadores e posts da campanha"""
    
    st.subheader("Influenciadores da Campanha")
    
    # Botao para adicionar influenciador
    if st.button("+ Adicionar Influenciador", use_container_width=False):
        st.session_state.show_add_inf_to_campaign = True
    
    # Modal de adicionar
    if st.session_state.get('show_add_inf_to_campaign', False):
        render_modal_add_influenciador(campanha)
    
    st.markdown("---")
    
    # Lista de influenciadores da campanha
    influenciadores = data_manager.get_influenciadores_campanha(campanha['id'])
    
    if not influenciadores:
        st.info("Nenhum influenciador adicionado a campanha")
        return
    
    for inf in influenciadores:
        with st.expander(f"{inf['nome']} (@{inf['usuario']}) - {inf['classificacao']} - {len(inf['posts'])} posts"):
            col1, col2, col3 = st.columns([1, 2, 2])
            
            with col1:
                if inf.get('foto'):
                    st.image(inf['foto'], width=80)
            
            with col2:
                st.write(f"**Seguidores:** {funcoes_auxiliares.formatar_numero(inf['seguidores'])}")
                st.write(f"**AIR Score:** {inf['air_score']}")
                st.write(f"**Taxa Eng.:** {inf['engagement_rate']:.2f}%")
            
            with col3:
                st.write(f"**Rede:** {inf['network'].title()}")
                st.write(f"**Classificacao:** {inf['classificacao']}")
                
                if campanha['tipo_dados'] == 'estatico':
                    st.caption("Dados congelados (campanha estatica)")
            
            st.markdown("---")
            
            # Posts do influenciador
            st.markdown("**Posts:**")
            
            if st.button("+ Adicionar Post", key=f"add_post_{inf['id']}"):
                st.session_state.show_add_post_inf = inf['id']
            
            # Form de adicionar post
            if st.session_state.get('show_add_post_inf') == inf['id']:
                render_form_post(campanha, inf)
            
            # Lista de posts
            if inf['posts']:
                for post in inf['posts']:
                    col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1, 1, 0.5])
                    
                    with col1:
                        st.write(f"**{post['formato']}** ({post['plataforma']})")
                        st.caption(post['data_publicacao'])
                        if post.get('link_post'):
                            st.markdown(f"[Link]({post['link_post']})")
                    
                    with col2:
                        st.caption("Views")
                        st.write(f"{post['views']:,}")
                    
                    with col3:
                        st.caption("Alcance")
                        st.write(f"{post['alcance']:,}")
                    
                    with col4:
                        st.caption("Interacoes")
                        st.write(f"{post['interacoes']:,}")
                    
                    with col5:
                        if post.get('imagens'):
                            try:
                                img_data = post['imagens'][0]
                                if img_data.startswith('http'):
                                    st.image(img_data, width=50)
                                else:
                                    st.image(base64.b64decode(img_data), width=50)
                            except:
                                pass
                    
                    st.markdown("---")
            else:
                st.caption("Nenhum post cadastrado")
            
            # Remover influenciador
            if st.button("Remover da Campanha", key=f"rem_inf_{inf['id']}", type="secondary"):
                data_manager.remover_influenciador_campanha(campanha['id'], inf['id'])
                st.success("Influenciador removido!")
                st.rerun()


def render_modal_add_influenciador(campanha):
    """Modal para adicionar influenciador a campanha"""
    
    with st.container():
        st.markdown("### Adicionar Influenciador")
        
        influenciadores_disponiveis = data_manager.get_influenciadores()
        
        if not influenciadores_disponiveis:
            st.warning("Cadastre influenciadores na base primeiro")
            if st.button("Ir para Influenciadores"):
                st.session_state.current_page = 'Influenciadores'
                st.rerun()
        else:
            # Filtrar os que ja estao na campanha
            ids_na_campanha = [i['influenciador_id'] for i in campanha['influenciadores']]
            disponiveis = [i for i in influenciadores_disponiveis if i['id'] not in ids_na_campanha]
            
            if not disponiveis:
                st.info("Todos os influenciadores da base ja estao na campanha")
            else:
                opcoes = {f"{i['nome']} (@{i['usuario']}) - {i['classificacao']}": i['id'] for i in disponiveis}
                
                selecionado = st.selectbox("Selecione o influenciador:", list(opcoes.keys()))
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Adicionar", type="primary", use_container_width=True):
                        inf_id = opcoes[selecionado]
                        data_manager.adicionar_influenciador_campanha(campanha['id'], inf_id)
                        st.session_state.show_add_inf_to_campaign = False
                        st.success("Influenciador adicionado!")
                        st.rerun()
                with col2:
                    if st.button("Cancelar", use_container_width=True):
                        st.session_state.show_add_inf_to_campaign = False
                        st.rerun()
        
        st.markdown("---")


def render_form_post(campanha, inf):
    """Formulario para adicionar post"""
    
    with st.form(f"form_post_{inf['id']}"):
        st.markdown("##### Novo Post")
        
        metricas_config = campanha.get('metricas_selecionadas', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            formato = st.selectbox("Formato *", ["Reels", "Stories", "Carrossel", "Feed", "TikTok", "YouTube"])
            plataforma = st.selectbox("Plataforma *", [inf['network'].title()])
            data_pub = st.date_input("Data Publicacao *", value=datetime.now())
            link_post = st.text_input("Link do Post", placeholder="https://...")
        
        with col2:
            views = st.number_input("Views", min_value=0, value=0) if metricas_config.get('views', True) else 0
            alcance = st.number_input("Alcance", min_value=0, value=0) if metricas_config.get('alcance', True) else 0
            interacoes = st.number_input("Interacoes", min_value=0, value=0) if metricas_config.get('interacoes', True) else 0
            impressoes = st.number_input("Impressoes", min_value=0, value=0) if metricas_config.get('impressoes', True) else 0
        
        with col3:
            curtidas = st.number_input("Curtidas", min_value=0, value=0) if metricas_config.get('curtidas', True) else 0
            comentarios = st.number_input("Comentarios", min_value=0, value=0) if metricas_config.get('comentarios', True) else 0
            compartilhamentos = st.number_input("Compartilhamentos", min_value=0, value=0) if metricas_config.get('compartilhamentos', True) else 0
            saves = st.number_input("Saves", min_value=0, value=0) if metricas_config.get('saves', True) else 0
        
        # Metricas opcionais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if formato == "Stories" and metricas_config.get('clique_link', False):
                clique_link = st.number_input("Cliques no Link", min_value=0, value=0)
            else:
                clique_link = 0
        
        with col2:
            if metricas_config.get('cupom_conversoes', False):
                cupom_codigo = st.text_input("Codigo do Cupom")
                cupom_conversoes = st.number_input("Conversoes", min_value=0, value=0)
            else:
                cupom_codigo = ""
                cupom_conversoes = 0
        
        with col3:
            custo = st.number_input("Custo (R$)", min_value=0.0, value=0.0, step=0.01)
        
        # Upload de imagens
        st.markdown("**Imagens/Videos do Post**")
        imagens_upload = st.file_uploader(
            "Selecione as midias",
            type=['png', 'jpg', 'jpeg', 'gif', 'mp4'],
            accept_multiple_files=True,
            key=f"upload_post_{inf['id']}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("Salvar Post", use_container_width=True):
                # Processar imagens
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
                    'alcance': alcance,
                    'interacoes': interacoes,
                    'impressoes': impressoes,
                    'curtidas': curtidas,
                    'comentarios_qtd': comentarios,
                    'compartilhamentos': compartilhamentos,
                    'saves': saves,
                    'clique_link': clique_link,
                    'cupom_codigo': cupom_codigo,
                    'cupom_conversoes': cupom_conversoes,
                    'custo': custo,
                    'imagens': imagens_b64
                })
                st.session_state.show_add_post_inf = None
                st.success("Post adicionado!")
                st.rerun()
        
        with col2:
            if st.form_submit_button("Cancelar", use_container_width=True):
                st.session_state.show_add_post_inf = None
                st.rerun()


def render_configuracoes_campanha(campanha):
    """Configuracoes gerais da campanha"""
    
    st.subheader("Configuracoes da Campanha")
    
    with st.form("form_config_campanha"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome da Campanha", value=campanha['nome'])
            objetivo = st.text_area("Objetivo", value=campanha.get('objetivo', ''), height=100)
            data_inicio = st.text_input("Data Inicio", value=campanha['data_inicio'], disabled=True)
        
        with col2:
            tipo_dados = st.selectbox(
                "Tipo de Dados",
                ["estatico", "dinamico"],
                index=0 if campanha.get('tipo_dados') == 'estatico' else 1,
                help="Estatico: usa dados do momento da adicao. Dinamico: atualiza via API"
            )
            is_aon = st.checkbox("Campanha AON", value=campanha.get('is_aon', False))
            data_fim = st.text_input("Data Fim", value=campanha['data_fim'], disabled=True)
            status = st.selectbox("Status", ["ativa", "pausada", "finalizada"],
                                 index=["ativa", "pausada", "finalizada"].index(campanha.get('status', 'ativa')))
        
        st.markdown("---")
        st.markdown("**Metricas a Coletar**")
        
        metricas = campanha.get('metricas_selecionadas', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            views = st.checkbox("Views", value=metricas.get('views', True))
            alcance = st.checkbox("Alcance", value=metricas.get('alcance', True))
        with col2:
            interacoes = st.checkbox("Interacoes", value=metricas.get('interacoes', True))
            impressoes = st.checkbox("Impressoes", value=metricas.get('impressoes', True))
        with col3:
            curtidas = st.checkbox("Curtidas", value=metricas.get('curtidas', True))
            comentarios_check = st.checkbox("Comentarios", value=metricas.get('comentarios', True))
        with col4:
            compartilhamentos = st.checkbox("Compartilhamentos", value=metricas.get('compartilhamentos', True))
            saves = st.checkbox("Saves", value=metricas.get('saves', True))
        
        col1, col2 = st.columns(2)
        with col1:
            clique_link = st.checkbox("Cliques Link (Stories)", value=metricas.get('clique_link', False))
        with col2:
            cupom_conversoes = st.checkbox("Conversoes Cupom", value=metricas.get('cupom_conversoes', False))
        
        st.markdown("---")
        
        notas = st.text_area("Notas e Observacoes", value=campanha.get('notas', ''), height=150,
                            placeholder="Adicione notas, insights manuais, observacoes importantes...")
        
        if st.form_submit_button("Salvar Configuracoes", use_container_width=True):
            data_manager.atualizar_campanha(campanha['id'], {
                'nome': nome,
                'objetivo': objetivo,
                'tipo_dados': tipo_dados,
                'is_aon': is_aon,
                'status': status,
                'notas': notas,
                'metricas_selecionadas': {
                    'views': views, 'alcance': alcance, 'interacoes': interacoes,
                    'impressoes': impressoes, 'curtidas': curtidas, 'comentarios': comentarios_check,
                    'compartilhamentos': compartilhamentos, 'saves': saves,
                    'clique_link': clique_link, 'cupom_conversoes': cupom_conversoes
                }
            })
            st.success("Configuracoes salvas!")
            st.rerun()


def render_configurar_insights(campanha):
    """Configura quais insights aparecem no relatorio"""
    
    st.subheader("Configurar Insights do Relatorio")
    st.caption("Selecione quais insights automaticos devem aparecer no relatorio")
    
    insights = campanha.get('insights_config', {})
    
    with st.form("form_insights"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Insights Automaticos**")
            mostrar_engajamento = st.checkbox("Analise de Engajamento", value=insights.get('mostrar_engajamento', True))
            mostrar_alcance = st.checkbox("Analise de Alcance", value=insights.get('mostrar_alcance', True))
            mostrar_conversao = st.checkbox("Analise de Conversao", value=insights.get('mostrar_conversao', True))
            mostrar_saves = st.checkbox("Analise de Saves", value=insights.get('mostrar_saves', True))
        
        with col2:
            st.markdown("**Secoes do Relatorio**")
            mostrar_comparativo_formato = st.checkbox("Comparativo por Formato", value=insights.get('mostrar_comparativo_formato', True))
            mostrar_top_influenciadores = st.checkbox("Top Influenciadores", value=insights.get('mostrar_top_influenciadores', True))
        
        st.markdown("---")
        st.markdown("**Insights Personalizados**")
        st.caption("Adicione insights manuais que devem aparecer no relatorio")
        
        # Insights existentes
        insights_personalizados = insights.get('insights_personalizados', [])
        
        for idx, insight in enumerate(insights_personalizados):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text_input(f"Insight {idx+1}", value=insight, key=f"insight_{idx}", disabled=True)
        
        # Novo insight
        novo_insight = st.text_input("Novo Insight", placeholder="Digite um insight personalizado...")
        
        if st.form_submit_button("Salvar Configuracao de Insights", use_container_width=True):
            novos_personalizados = insights_personalizados.copy()
            if novo_insight:
                novos_personalizados.append(novo_insight)
            
            data_manager.atualizar_campanha(campanha['id'], {
                'insights_config': {
                    'mostrar_engajamento': mostrar_engajamento,
                    'mostrar_alcance': mostrar_alcance,
                    'mostrar_conversao': mostrar_conversao,
                    'mostrar_saves': mostrar_saves,
                    'mostrar_comparativo_formato': mostrar_comparativo_formato,
                    'mostrar_top_influenciadores': mostrar_top_influenciadores,
                    'insights_personalizados': novos_personalizados
                }
            })
            st.success("Configuracao de insights salva!")
            st.rerun()


def render_categorias_comentarios(campanha):
    """Configura categorias para classificacao de comentarios pela IA"""
    
    st.subheader("Categorias para Classificacao de Comentarios")
    st.caption("Configure as categorias que a IA usara para classificar os comentarios")
    
    categorias = campanha.get('categorias_comentarios', [
        'Elogio ao Produto', 'Intencao de Compra', 'Conexao Emocional', 'Duvida', 'Critica', 'Geral'
    ])
    
    st.markdown("**Categorias Atuais:**")
    
    for idx, cat in enumerate(categorias):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"{idx+1}. {cat}")
        with col2:
            if st.button("X", key=f"rem_cat_{idx}", help="Remover categoria"):
                categorias.pop(idx)
                data_manager.atualizar_campanha(campanha['id'], {'categorias_comentarios': categorias})
                st.rerun()
    
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        nova_categoria = st.text_input("Nova Categoria", placeholder="Ex: Perguntas sobre Preco")
    with col2:
        st.write("")
        st.write("")
        if st.button("Adicionar", use_container_width=True):
            if nova_categoria and nova_categoria not in categorias:
                categorias.append(nova_categoria)
                data_manager.atualizar_campanha(campanha['id'], {'categorias_comentarios': categorias})
                st.success("Categoria adicionada!")
                st.rerun()
    
    st.markdown("---")
    st.info("A IA classificara automaticamente os comentarios nas categorias definidas acima, alem de determinar se sao positivos, neutros ou negativos.")
