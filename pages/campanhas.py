"""
Pagina: Campanhas
"""

import streamlit as st
from datetime import datetime, timedelta
from utils import data_manager, funcoes_auxiliares
import pandas as pd
import io

def render():
    st.markdown('<p class="main-header">Campanhas</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Gerencie suas campanhas</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])
    with col2:
        if st.button("Importar do AIR", use_container_width=True):
            st.session_state.show_import_air = True
    with col3:
        if st.button("📄 Importar CSV", use_container_width=True):
            st.session_state.show_import_csv = True
    with col4:
        if st.button("+ Nova Campanha", type="primary", use_container_width=True):
            st.session_state.show_new_campaign = True
            st.session_state.edit_campanha_id = None
    
    # Modal importar do AIR
    if st.session_state.get('show_import_air', False):
        render_importar_air()
        return
    
    # Modal importar CSV
    if st.session_state.get('show_import_csv', False):
        render_importar_csv()
        return
    
    # Form nova/editar campanha
    if st.session_state.get('show_new_campaign', False) or st.session_state.get('edit_campanha_id'):
        edit_id = st.session_state.get('edit_campanha_id')
        camp_edit = data_manager.get_campanha(edit_id) if edit_id else None
        
        with st.form("form_campanha"):
            st.subheader("Editar Campanha" if camp_edit else "Criar Campanha")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome da Campanha *", value=camp_edit['nome'] if camp_edit else "")
                
                clientes = data_manager.get_clientes()
                if clientes:
                    opcoes = {c['nome']: c for c in clientes}
                    cliente_atual = camp_edit.get('cliente_nome', '') if camp_edit else None
                    idx = list(opcoes.keys()).index(cliente_atual) if cliente_atual in opcoes else 0
                    cliente_sel = st.selectbox("Cliente *", list(opcoes.keys()), index=idx)
                    cliente_obj = opcoes.get(cliente_sel)
                else:
                    st.warning("Cadastre um cliente primeiro")
                    cliente_obj = None
                
                def parse_data(data_str, default=None):
                    """Parse data em varios formatos"""
                    if not data_str:
                        return default or datetime.now()
                    for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d']:
                        try:
                            return datetime.strptime(data_str, fmt)
                        except:
                            continue
                    return default or datetime.now()
                
                di_val = parse_data(camp_edit.get('data_inicio'), datetime.now()) if camp_edit else datetime.now()
                df_val = parse_data(camp_edit.get('data_fim'), datetime.now() + timedelta(days=30)) if camp_edit else datetime.now() + timedelta(days=30)
                data_inicio = st.date_input("Data Inicio", value=di_val)
                data_fim = st.date_input("Data Fim", value=df_val)
            
            with col2:
                tipo_idx = 0 if camp_edit and camp_edit.get('tipo_dados') == 'estatico' else 1
                tipo_dados = st.selectbox("Tipo de Dados", ["estatico", "dinamico"], index=tipo_idx if camp_edit else 0,
                                         help="Estatico: dados congelados | Dinamico: atualiza via API")
                is_aon = st.checkbox("Campanha AON", value=camp_edit.get('is_aon', False) if camp_edit else False,
                                    help="Habilita graficos de evolucao temporal")
                objetivo = st.text_area("Objetivo", value=camp_edit.get('objetivo', '') if camp_edit else "", height=100)
            
            st.markdown("**Metricas a Coletar:**")
            metricas_cfg = (camp_edit.get('metricas_selecionadas') or {}) if camp_edit else {}
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                views = st.checkbox("Views", value=metricas_cfg.get('views', True))
                alcance = st.checkbox("Alcance", value=metricas_cfg.get('alcance', True))
            with col2:
                interacoes = st.checkbox("Interacoes", value=metricas_cfg.get('interacoes', True))
                impressoes = st.checkbox("Impressoes", value=metricas_cfg.get('impressoes', True))
            with col3:
                curtidas = st.checkbox("Curtidas", value=metricas_cfg.get('curtidas', True))
                comentarios = st.checkbox("Comentarios", value=metricas_cfg.get('comentarios', True))
            with col4:
                compartilhamentos = st.checkbox("Compartilhamentos", value=metricas_cfg.get('compartilhamentos', True))
                saves = st.checkbox("Saves", value=metricas_cfg.get('saves', True))
            
            col1, col2 = st.columns(2)
            with col1:
                clique_link = st.checkbox("Cliques Link (Stories)", value=metricas_cfg.get('clique_link', False))
            with col2:
                cupom = st.checkbox("Conversoes Cupom", value=metricas_cfg.get('cupom_conversoes', False))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.form_submit_button("Salvar", use_container_width=True):
                    if nome and cliente_obj:
                        dados = {
                            'nome': nome,
                            'cliente_id': cliente_obj['id'],
                            'cliente_nome': cliente_obj['nome'],
                            'objetivo': objetivo,
                            'data_inicio': data_inicio.strftime('%d/%m/%Y'),
                            'data_fim': data_fim.strftime('%d/%m/%Y'),
                            'tipo_dados': tipo_dados,
                            'is_aon': is_aon,
                            'metricas_selecionadas': {
                                'views': views, 'alcance': alcance, 'interacoes': interacoes,
                                'impressoes': impressoes, 'curtidas': curtidas, 'comentarios': comentarios,
                                'compartilhamentos': compartilhamentos, 'saves': saves,
                                'clique_link': clique_link, 'cupom_conversoes': cupom
                            }
                        }
                        if camp_edit:
                            data_manager.atualizar_campanha(edit_id, dados)
                            st.success("Campanha atualizada!")
                        else:
                            data_manager.criar_campanha(dados)
                            st.success("Campanha criada!")
                        st.session_state.show_new_campaign = False
                        st.session_state.edit_campanha_id = None
                        st.rerun()
                    else:
                        st.error("Preencha os campos obrigatorios")
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.show_new_campaign = False
                    st.session_state.edit_campanha_id = None
                    st.rerun()
            with col3:
                if camp_edit:
                    if st.form_submit_button("Excluir", use_container_width=True):
                        data_manager.excluir_campanha(edit_id)
                        st.session_state.edit_campanha_id = None
                        st.success("Campanha excluida!")
                        st.rerun()
    
    st.markdown("---")
    
    # Filtro
    col1, col2 = st.columns(2)
    with col1:
        clientes = data_manager.get_clientes()
        opcoes_cli = ["Todos"] + [c['nome'] for c in clientes]
        filtro_cli = st.selectbox("Filtrar por Cliente", opcoes_cli)
    
    campanhas = data_manager.get_campanhas()
    
    if filtro_cli != "Todos":
        cliente_obj = next((c for c in clientes if c['nome'] == filtro_cli), None)
        if cliente_obj:
            campanhas = [c for c in campanhas if c['cliente_id'] == cliente_obj['id']]
    
    # Lista
    if campanhas:
        for camp in campanhas:
            metricas = data_manager.calcular_metricas_campanha(camp)
            aon = "[AON]" if camp.get('is_aon') else ""
            
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2.5, 0.8, 0.8, 1, 1.2, 1.2, 0.8])
            
            with col1:
                st.write(f"**{camp['nome']}** {aon}")
                st.caption(f"{camp.get('cliente_nome', '')} | {funcoes_auxiliares.formatar_data_br(camp['data_inicio'])}")
            with col2:
                st.metric("Influs", metricas['total_influenciadores'])
            with col3:
                st.metric("Posts", metricas['total_posts'])
            with col4:
                st.metric("Views", funcoes_auxiliares.formatar_numero(metricas['total_views']))
            with col5:
                if st.button("Central da Campanha", key=f"ctrl_{camp['id']}"):
                    st.session_state.campanha_atual_id = camp['id']
                    st.session_state.current_page = 'Central'
                    st.rerun()
            with col6:
                if st.button("Relatorio", key=f"rel_{camp['id']}"):
                    st.session_state.campanha_atual_id = camp['id']
                    st.session_state.modo_relatorio = 'campanha'
                    st.session_state.current_page = 'Relatorios'
                    st.rerun()
            with col7:
                if st.button("Editar", key=f"edit_{camp['id']}"):
                    st.session_state.edit_campanha_id = camp['id']
                    st.session_state.show_new_campaign = False
                    st.rerun()
            
            st.markdown("---")
    else:
        st.info("Nenhuma campanha encontrada")


def render_importar_air():
    """Modal para importar campanha do AIR via link"""
    import requests
    import re
    import time
    from utils import api_client
    
    st.subheader("Importar Campanha do AIR")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Cancelar", use_container_width=True, key="btn_cancelar_import_air"):
            st.session_state.show_import_air = False
            st.session_state.air_import_data = None
            st.rerun()
    
    st.markdown("---")
    
    # Endpoint do AIR
    AIR_ENDPOINT = "https://n8n.air.com.vc/webhook/d90a066a-3a26-42d5-8c7b-ac8f0afbe1a6"
    
    st.markdown("""
    **Como usar:**
    1. Cole o link da campanha do AIR (ex: `https://app.air.com.vc/campanhas/vzquYDxr4eTfouviAIZvg7AZSnjn5TlQs92AEGwc1Oo`)
    2. O sistema vai extrair os influenciadores e posts automaticamente
    3. Posts com as hashtags da campanha serão vinculados
    """)
    
    link_air = st.text_input(
        "Link da Campanha AIR:",
        placeholder="https://app.air.com.vc/campanhas/vzquYDxr4eTfouviAIZvg7AZSnjn5TlQs92AEGwc1Oo",
        key="air_link_input"
    )
    
    # Extrair código do link
    def extrair_codigo_air(link):
        """Extrai o código da campanha do link do AIR"""
        # Padrões possíveis
        patterns = [
            r'campanhas/([A-Za-z0-9_-]+)',
            r'campaign/([A-Za-z0-9_-]+)',
            r'/([A-Za-z0-9_-]{30,})'  # Código longo no final
        ]
        for pattern in patterns:
            match = re.search(pattern, link)
            if match:
                return match.group(1)
        # Se não encontrou padrão, assume que é o código direto
        if len(link) > 20 and '/' not in link:
            return link
        return None
    
    if link_air:
        codigo = extrair_codigo_air(link_air)
        if codigo:
            st.caption(f"Código extraído: `{codigo}`")
        else:
            st.error("Não foi possível extrair o código do link. Verifique o formato.")
    
    # Cliente (mostrar antes de buscar)
    clientes = data_manager.get_clientes()
    if clientes:
        opcoes_clientes = ["Selecione..."] + [c['nome'] for c in clientes]
        cliente_sel = st.selectbox("Cliente:", opcoes_clientes)
    else:
        cliente_sel = None
        st.caption("Nenhum cliente cadastrado")
    
    if st.button("Buscar Dados da Campanha", type="primary", disabled=not link_air):
        if not link_air:
            st.error("Cole o link da campanha")
        else:
            codigo = extrair_codigo_air(link_air)
            if not codigo:
                st.error("Link inválido")
            else:
                with st.spinner("Buscando dados da campanha no AIR..."):
                    try:
                        # Chamar endpoint do AIR
                        response = requests.get(f"{AIR_ENDPOINT}?code={codigo}", timeout=30)
                        
                        if response.status_code == 200:
                            dados = response.json()
                            
                            # Debug: mostrar resposta raw
                            with st.expander("Debug: Resposta do servidor"):
                                st.json(dados)
                            
                            # O retorno pode ser uma lista ou objeto
                            if isinstance(dados, list) and len(dados) > 0:
                                dados = dados[0]
                            
                            # Verificar se tem dados válidos
                            # Campos podem ser: title/name, profiles_in_campaign/influencers, hashtags
                            tem_dados = (
                                dados.get('success') or 
                                dados.get('profiles_in_campaign') or
                                dados.get('influencers') or 
                                dados.get('title') or
                                dados.get('name') or 
                                dados.get('hashtags')
                            )
                            
                            if tem_dados:
                                # Pegar nome (pode ser 'title' ou 'name')
                                nome_camp = dados.get('title') or dados.get('name', 'Campanha AIR')
                                
                                # Pegar influenciadores (pode ser 'profiles_in_campaign' ou 'influencers')
                                inf_ids = dados.get('profiles_in_campaign') or dados.get('influencers', [])
                                
                                # Pegar hashtags
                                hashtags = dados.get('hashtags', [])
                                
                                # Pegar datas se existirem
                                start_date = dados.get('start_date', '')
                                end_date = dados.get('end_date', '')
                                
                                # Pegar menções
                                mentions = dados.get('mentions', [])
                                
                                st.session_state.air_import_data = {
                                    'codigo': codigo,
                                    'nome': nome_camp,
                                    'hashtags': hashtags,
                                    'mentions': mentions,
                                    'influenciadores_ids': inf_ids,
                                    'start_date': start_date,
                                    'end_date': end_date,
                                    'cliente': cliente_sel if cliente_sel != "Selecione..." else None
                                }
                                st.success(f"Campanha '{nome_camp}' encontrada! {len(inf_ids)} influenciadores")
                                st.rerun()
                            else:
                                st.error("Campanha não encontrada ou resposta inválida")
                                st.caption(f"Resposta: {str(dados)[:500]}")
                        else:
                            st.error(f"Erro ao buscar campanha: {response.status_code}")
                    except requests.exceptions.Timeout:
                        st.error("Timeout - o servidor demorou para responder")
                    except Exception as e:
                        st.error(f"Erro: {str(e)}")
    
    # Mostrar dados encontrados
    air_data = st.session_state.get('air_import_data')
    
    if air_data:
        st.markdown("---")
        st.markdown("### Dados da Campanha")
        
        # Permitir editar o nome
        nome_editado = st.text_input(
            "Nome da Campanha:", 
            value=air_data.get('nome', 'Campanha AIR'),
            key="air_nome_editado"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Influenciadores", len(air_data.get('influenciadores_ids', [])))
        with col2:
            st.metric("Hashtags", len(air_data.get('hashtags', [])))
        with col3:
            st.metric("Mencoes", len(air_data.get('mentions', [])))
        
        # Mostrar datas
        start_date = air_data.get('start_date', '')
        end_date = air_data.get('end_date', '')
        if start_date or end_date:
            try:
                start_fmt = datetime.fromisoformat(start_date.replace('Z', '')).strftime('%d/%m/%Y') if start_date else 'N/A'
                end_fmt = datetime.fromisoformat(end_date.replace('Z', '')).strftime('%d/%m/%Y') if end_date else 'N/A'
                st.caption(f"Periodo: {start_fmt} ate {end_fmt}")
            except:
                pass
        
        # Mostrar hashtags
        hashtags = air_data.get('hashtags', [])
        if hashtags:
            st.markdown("**Hashtags da campanha:**")
            st.caption(" ".join(hashtags[:15]))
        
        # Mostrar mencoes
        mentions = air_data.get('mentions', [])
        if mentions:
            st.markdown("**Mencoes:**")
            st.caption(" ".join(mentions))
        
        st.markdown("---")
        
        # Opcoes de importacao
        st.markdown("### Opcoes de Importacao")
        
        col1, col2 = st.columns(2)
        with col1:
            limite_posts = st.number_input("Limite de posts por influenciador:", min_value=5, max_value=100, value=20)
        with col2:
            criar_ausentes = st.checkbox("Cadastrar influenciadores ausentes", value=True,
                                        help="Se o influenciador nao existir na base, busca na API e cadastra")
        
        st.markdown("---")
        
        # Estado para controlar o fluxo
        if 'air_posts_preview' not in st.session_state:
            st.session_state.air_posts_preview = None
        if 'air_influenciadores_preview' not in st.session_state:
            st.session_state.air_influenciadores_preview = None
        
        # Botao para buscar posts (etapa 1)
        if st.session_state.air_posts_preview is None:
            if st.button("Buscar Posts", type="primary", use_container_width=True):
                # Limpar debug anterior
                st.session_state.debug_api_responses = []
                air_data['nome'] = nome_editado
                buscar_posts_preview(air_data, criar_ausentes, limite_posts)
        
        # Se ja buscou, mostrar preview e botoes de acao
        else:
            preview = st.session_state.air_posts_preview
            influenciadores = st.session_state.air_influenciadores_preview or []
            
            st.markdown("### Preview dos Posts Encontrados")
            
            # Resumo geral
            total_posts = sum(len(inf.get('posts', [])) for inf in influenciadores)
            total_inf = len(influenciadores)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Influenciadores encontrados", total_inf)
            with col2:
                st.metric("Posts encontrados", total_posts)
            
            # Mostrar detalhes por influenciador
            if influenciadores:
                with st.expander(f"Ver detalhes ({total_inf} influenciadores, {total_posts} posts)", expanded=True):
                    for inf in influenciadores:
                        posts = inf.get('posts', [])
                        nome = inf.get('nome', 'Desconhecido')
                        usuario = inf.get('usuario', '')
                        
                        st.markdown(f"**{nome}** (@{usuario}) - {len(posts)} posts")
                        
                        if posts:
                            # Mostrar primeiros 3 posts como exemplo
                            for i, post in enumerate(posts[:3]):
                                formato = post.get('formato', 'Feed')
                                data_pub = post.get('data_publicacao', '')
                                views = post.get('views', 0)
                                alcance = post.get('alcance', 0)
                                interacoes = post.get('interacoes', 0)
                                st.caption(f"  - {formato} ({data_pub}) | Views: {views:,} | Alcance: {alcance:,} | Interacoes: {interacoes:,}")
                            
                            if len(posts) > 3:
                                st.caption(f"  ... e mais {len(posts) - 3} posts")
                        else:
                            st.caption("  Nenhum post encontrado")
                        
                        st.markdown("---")
            
            # Avisos se houver
            if preview.get('erros'):
                with st.expander(f"Avisos ({len(preview['erros'])})"):
                    for erro in preview['erros']:
                        st.warning(erro)
            
            # DEBUG: Mostrar respostas da API
            if st.session_state.get('debug_api_responses'):
                with st.expander("DEBUG: Respostas da API (clique para ver)", expanded=True):
                    import json
                    for i, debug_info in enumerate(st.session_state.debug_api_responses):
                        st.markdown(f"### {i+1}. {debug_info['influenciador']}")
                        st.markdown(f"**Profile ID:** `{debug_info['profile_id']}`")
                        
                        st.markdown("**Parametros enviados:**")
                        st.json(debug_info['parametros'])
                        
                        resposta = debug_info['resposta_completa']
                        if isinstance(resposta, dict):
                            st.markdown("**Resumo da resposta:**")
                            st.write(f"- success: {resposta.get('success')}")
                            st.write(f"- error: {resposta.get('error')}")
                            st.write(f"- total_encontrados: {resposta.get('total_encontrados')}")
                            st.write(f"- qtd posts processados: {len(resposta.get('posts', []))}")
                            
                            # Mostrar debug das chamadas a API
                            if resposta.get('api_debug'):
                                st.markdown("**Chamadas a API:**")
                                for call in resposta['api_debug']:
                                    st.json(call)
                            
                            # Mostrar dados brutos se existirem
                            if resposta.get('raw_data'):
                                st.markdown("**Raw data da API (primeiros itens):**")
                                st.json(resposta.get('raw_data', []))
                            else:
                                st.warning("Nenhum raw_data retornado")
                            
                            # Mostrar posts processados
                            if resposta.get('posts'):
                                st.markdown("**Posts processados (primeiros 2):**")
                                st.json(resposta['posts'][:2])
                            else:
                                st.warning("Nenhum post processado")
                        else:
                            st.write(f"Tipo de resposta: {type(resposta)}")
                            st.write(resposta)
                        st.markdown("---")
            
            st.markdown("---")
            
            # Botoes de acao
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Criar Campanha", type="primary", use_container_width=True):
                    air_data['nome'] = nome_editado
                    criar_campanha_do_air_com_preview(air_data, influenciadores)
            
            with col2:
                if st.button("Cancelar", use_container_width=True, key="btn_cancelar_preview_air"):
                    st.session_state.air_posts_preview = None
                    st.session_state.air_influenciadores_preview = None
                    st.rerun()


def buscar_posts_preview(air_data, criar_ausentes=True, limite_posts=20):
    """Busca posts para preview antes de criar a campanha"""
    from utils import api_client
    
    progress = st.progress(0)
    status = st.empty()
    
    hashtags = air_data.get('hashtags', [])
    mentions = air_data.get('mentions', [])
    inf_ids_air = air_data.get('influenciadores_ids', [])
    
    # Datas do AIR
    start_date_str = air_data.get('start_date', '')
    end_date_str = air_data.get('end_date', '')
    
    # Converter datas para formato da API
    api_start_date = None
    api_end_date = None
    
    if start_date_str:
        try:
            dt = datetime.fromisoformat(start_date_str.replace('Z', ''))
            api_start_date = dt.strftime('%Y-%m-%d')
        except:
            pass
    
    if end_date_str:
        try:
            dt = datetime.fromisoformat(end_date_str.replace('Z', ''))
            api_end_date = dt.strftime('%Y-%m-%d')
        except:
            pass
    
    # Se nao tem datas, usar periodo padrao
    if not api_start_date:
        api_start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if not api_end_date:
        api_end_date = datetime.now().strftime('%Y-%m-%d')
    
    influenciadores_preview = []
    erros = []
    total = len(inf_ids_air)
    
    for idx, inf_id_air in enumerate(inf_ids_air):
        progress.progress((idx + 1) / total)
        status.text(f"Buscando influenciador {idx + 1}/{total}...")
        
        # Buscar influenciador na base local pelo profile_id
        inf_local = data_manager.buscar_influenciador_por_profile_id(inf_id_air)
        
        if not inf_local:
            if criar_ausentes:
                # Buscar na API
                status.text(f"Buscando dados do influenciador {idx + 1}/{total} na API...")
                resultado = api_client.buscar_por_profile_id(inf_id_air)
                
                if resultado.get('success') and resultado.get('data'):
                    dados_api = resultado['data']
                    inf_local = {
                        'id': None,  # Sera criado depois
                        'nome': dados_api.get('nome', 'Influenciador AIR'),
                        'usuario': dados_api.get('usuario', f'air_{inf_id_air[:8]}'),
                        'profile_id': inf_id_air,
                        'network': dados_api.get('network', 'instagram'),
                        'seguidores': dados_api.get('seguidores', 0),
                        'novo': True,  # Flag para indicar que precisa criar
                        'dados_completos': dados_api
                    }
                else:
                    # Criar com dados minimos
                    inf_local = {
                        'id': None,
                        'nome': 'Influenciador AIR',
                        'usuario': f'air_{inf_id_air[:8]}',
                        'profile_id': inf_id_air,
                        'network': 'instagram',
                        'seguidores': 0,
                        'novo': True,
                        'dados_completos': None
                    }
                    erros.append(f"Nao foi possivel buscar dados de {inf_id_air[:12]}...")
            else:
                erros.append(f"Influenciador {inf_id_air[:12]}... nao encontrado na base")
                continue
        else:
            inf_local['novo'] = False
            inf_local['dados_completos'] = None
        
        # Buscar posts
        status.text(f"Buscando posts de {inf_local.get('nome', '')}...")
        
        posts_resultado = api_client.buscar_posts_influenciador(
            inf_local.get('profile_id') or inf_id_air,
            limite=limite_posts,
            hashtags=hashtags,
            mentions=mentions,
            start_date=api_start_date,
            end_date=api_end_date
        )
        
        # DEBUG: Salvar resposta da API para visualizacao
        if 'debug_api_responses' not in st.session_state:
            st.session_state.debug_api_responses = []
        
        st.session_state.debug_api_responses.append({
            'influenciador': inf_local.get('nome', ''),
            'profile_id': inf_local.get('profile_id') or inf_id_air,
            'parametros': {
                'limite': limite_posts,
                'hashtags': hashtags,
                'mentions': mentions,
                'start_date': api_start_date,
                'end_date': api_end_date
            },
            'resposta_completa': posts_resultado
        })
        
        posts = []
        if posts_resultado.get('success') and posts_resultado.get('posts'):
            posts = posts_resultado['posts']
        elif posts_resultado.get('error'):
            erros.append(f"Erro ao buscar posts de {inf_local.get('nome', '')}: {posts_resultado['error'][:50]}")
        
        inf_local['posts'] = posts
        influenciadores_preview.append(inf_local)
    
    progress.empty()
    status.empty()
    
    # Salvar no session_state
    st.session_state.air_posts_preview = {
        'erros': erros,
        'total_influenciadores': len(influenciadores_preview),
        'total_posts': sum(len(inf.get('posts', [])) for inf in influenciadores_preview)
    }
    st.session_state.air_influenciadores_preview = influenciadores_preview
    
    st.rerun()


def criar_campanha_do_air_com_preview(air_data, influenciadores_preview):
    """Cria a campanha usando os dados ja buscados no preview"""
    
    progress = st.progress(0)
    status = st.empty()
    
    nome_campanha = air_data.get('nome', 'Campanha AIR')
    cliente_nome = air_data.get('cliente')
    
    # Datas do AIR
    start_date_str = air_data.get('start_date', '')
    end_date_str = air_data.get('end_date', '')
    
    # Converter datas
    try:
        if start_date_str:
            start_dt = datetime.fromisoformat(start_date_str.replace('Z', ''))
            data_inicio = start_dt.strftime('%d/%m/%Y')
        else:
            data_inicio = datetime.now().strftime('%d/%m/%Y')
    except:
        data_inicio = datetime.now().strftime('%d/%m/%Y')
    
    try:
        if end_date_str:
            end_dt = datetime.fromisoformat(end_date_str.replace('Z', ''))
            data_fim = end_dt.strftime('%d/%m/%Y')
        else:
            data_fim = (datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y')
    except:
        data_fim = (datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y')
    
    status.text("Criando campanha...")
    
    # Buscar cliente
    cliente_id = None
    if cliente_nome:
        clientes = data_manager.get_clientes()
        for c in clientes:
            if c['nome'] == cliente_nome:
                cliente_id = c['id']
                break
    
    # Criar campanha
    campanha = data_manager.criar_campanha({
        'nome': nome_campanha,
        'cliente_id': cliente_id,
        'cliente_nome': cliente_nome,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'objetivo': f"Importado do AIR",
        'status': 'ativa'
    })
    
    campanha_id = campanha['id']
    
    influenciadores_adicionados = 0
    posts_adicionados = 0
    erros = []
    
    total = len(influenciadores_preview)
    
    for idx, inf_data in enumerate(influenciadores_preview):
        progress.progress((idx + 1) / total)
        
        # Se e novo, criar primeiro
        if inf_data.get('novo'):
            status.text(f"Cadastrando {inf_data.get('nome', '')}...")
            
            dados_criar = inf_data.get('dados_completos') or {
                'nome': inf_data.get('nome', 'Influenciador AIR'),
                'usuario': inf_data.get('usuario', ''),
                'profile_id': inf_data.get('profile_id', ''),
                'network': inf_data.get('network', 'instagram'),
                'seguidores': inf_data.get('seguidores', 0)
            }
            
            inf_local = data_manager.criar_influenciador(dados_criar)
            inf_id = inf_local['id']
        else:
            inf_id = inf_data['id']
        
        # Adicionar a campanha
        try:
            status.text(f"Adicionando {inf_data.get('nome', '')} a campanha...")
            data_manager.adicionar_influenciador_campanha(campanha_id, inf_id)
            influenciadores_adicionados += 1
        except Exception as e:
            erros.append(f"Erro ao adicionar {inf_data.get('nome', '')}: {str(e)}")
            continue
        
        # Adicionar posts
        posts = inf_data.get('posts', [])
        if posts:
            status.text(f"Salvando {len(posts)} posts de {inf_data.get('nome', '')}...")
            
            for post_api in posts:
                post_data = {
                    'formato': post_api.get('formato') or post_api.get('type', 'Feed'),
                    'plataforma': 'Instagram',
                    'data_publicacao': post_api.get('data_publicacao') or post_api.get('date', ''),
                    'link': post_api.get('link') or post_api.get('permalink', ''),
                    'views': post_api.get('views', 0) or 0,
                    'alcance': post_api.get('alcance') or post_api.get('reach', 0) or 0,
                    'interacoes': post_api.get('interacoes') or post_api.get('engagement', 0) or 0,
                    'impressoes': post_api.get('impressoes') or post_api.get('impressions', 0) or 0,
                    'curtidas': post_api.get('curtidas') or post_api.get('likes', 0) or 0,
                    'comentarios_qtd': post_api.get('comentarios_qtd') or post_api.get('comments', 0) or 0,
                    'compartilhamentos': post_api.get('compartilhamentos') or post_api.get('shares', 0) or 0,
                    'saves': post_api.get('saves', 0) or 0,
                    'imagens': [post_api.get('thumbnail', '')] if post_api.get('thumbnail') else []
                }
                
                try:
                    data_manager.adicionar_post(campanha_id, inf_id, post_data)
                    posts_adicionados += 1
                except Exception as pe:
                    erros.append(f"Erro ao salvar post: {str(pe)[:50]}")
    
    progress.empty()
    status.empty()
    
    # Limpar session state
    st.session_state.air_posts_preview = None
    st.session_state.air_influenciadores_preview = None
    st.session_state.air_data = None
    
    # Mostrar resultado
    st.success(f"""
    Campanha criada com sucesso!
    
    - Nome: {nome_campanha}
    - Influenciadores: {influenciadores_adicionados} adicionados
    - Posts: {posts_adicionados} vinculados
    """)
    
    if erros:
        with st.expander(f"{len(erros)} avisos/erros"):
            for erro in erros:
                st.warning(erro)
    
    # Botao para ir para a central
    if st.button("Ir para Central da Campanha", type="primary"):
        st.session_state.campanha_selecionada = campanha_id
        st.session_state.pagina = 'central_campanha'
        st.rerun()


def render_importar_csv():
    """Modal para importar campanha via CSV"""
    
    st.subheader("Importar Campanha via CSV")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Cancelar", use_container_width=True, key="btn_cancelar_import_csv"):
            st.session_state.show_import_csv = False
            st.rerun()
    
    st.markdown("---")
    
    # Modelo CSV
    st.markdown("**Modelo do CSV:**")
    st.caption("O CSV deve ter as seguintes colunas (separadas por ; ou ,)")
    
    modelo_csv = """influenciador;usuario;rede;seguidores;formato;data_publicacao;curtidas;comentarios;salvamentos;compartilhamentos;views;impressoes;alcance;link
Maria Silva;@mariasilva;instagram;150000;Reels;01/12/2024;5000;200;150;80;50000;60000;40000;https://instagram.com/p/xxx
Maria Silva;@mariasilva;instagram;150000;Stories;01/12/2024;0;0;0;0;25000;25000;20000;
Joao Santos;@joaosantos;tiktok;80000;Video;02/12/2024;3000;100;50;200;100000;100000;0;https://tiktok.com/@joaosantos/video/xxx"""
    
    st.code(modelo_csv, language='csv')
    
    # Download modelo
    st.download_button(
        "Baixar Modelo CSV",
        data=modelo_csv,
        file_name="modelo_campanha.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    
    # Upload CSV
    st.markdown("**Upload do CSV:**")
    
    uploaded_file = st.file_uploader("Selecione o arquivo CSV", type=['csv'])
    
    if uploaded_file:
        try:
            # Tentar ler com diferentes separadores
            content = uploaded_file.read().decode('utf-8')
            
            if ';' in content:
                df = pd.read_csv(io.StringIO(content), sep=';')
            else:
                df = pd.read_csv(io.StringIO(content), sep=',')
            
            st.success(f"Arquivo carregado: {len(df)} linhas")
            
            # Preview
            st.dataframe(df.head(10), use_container_width=True)
            
            st.markdown("---")
            
            # Configuracao da campanha
            st.markdown("**Configurar Campanha:**")
            
            col1, col2 = st.columns(2)
            with col1:
                nome_campanha = st.text_input("Nome da Campanha *", value="Campanha Importada")
                
                clientes = data_manager.get_clientes()
                if clientes:
                    cliente_sel = st.selectbox("Cliente *", [c['nome'] for c in clientes])
                    cliente_obj = next((c for c in clientes if c['nome'] == cliente_sel), None)
                else:
                    st.warning("Cadastre um cliente primeiro")
                    cliente_obj = None
            
            with col2:
                is_aon = st.checkbox("Campanha AON")
                tipo_dados = st.selectbox("Tipo de Dados", ["estatico", "dinamico"])
            
            if st.button("Importar Campanha", type="primary", use_container_width=True):
                if nome_campanha and cliente_obj:
                    # Criar campanha
                    campanha_dados = {
                        'nome': nome_campanha,
                        'cliente_id': cliente_obj['id'],
                        'cliente_nome': cliente_obj['nome'],
                        'data_inicio': datetime.now().strftime('%d/%m/%Y'),
                        'data_fim': (datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y'),
                        'tipo_dados': tipo_dados,
                        'is_aon': is_aon,
                        'objetivo': 'Importado via CSV',
                        'metricas_selecionadas': {
                            'curtidas': True, 'comentarios': True, 'salvamentos': True,
                            'compartilhamentos': True, 'views': True, 'impressoes': True,
                            'alcance': True, 'clique_link': True, 'cliques_arroba': True
                        }
                    }
                    
                    nova_campanha = data_manager.criar_campanha(campanha_dados)
                    camp_id = nova_campanha['id']
                    
                    # Processar influenciadores e posts
                    influenciadores_processados = {}
                    posts_adicionados = 0
                    
                    for _, row in df.iterrows():
                        usuario = str(row.get('usuario', '')).replace('@', '').strip()
                        nome_inf = str(row.get('influenciador', usuario))
                        
                        if not usuario:
                            continue
                        
                        # Verificar se influenciador ja existe
                        inf_existente = data_manager.get_influenciador_por_usuario(usuario)
                        
                        if inf_existente:
                            inf_id = inf_existente['id']
                        else:
                            # Criar influenciador
                            novo_inf = data_manager.criar_influenciador({
                                'nome': nome_inf,
                                'usuario': usuario,
                                'network': str(row.get('rede', 'instagram')).lower(),
                                'seguidores': int(row.get('seguidores', 0)) if pd.notna(row.get('seguidores')) else 0
                            })
                            inf_id = novo_inf['id']
                        
                        # Adicionar influenciador a campanha se ainda nao esta
                        if inf_id not in influenciadores_processados:
                            data_manager.adicionar_influenciador_campanha(camp_id, inf_id)
                            influenciadores_processados[inf_id] = True
                        
                        # Criar post
                        post_data = {
                            'formato': str(row.get('formato', 'Reels')),
                            'data_publicacao': str(row.get('data_publicacao', datetime.now().strftime('%d/%m/%Y'))),
                            'curtidas': int(row.get('curtidas', 0)) if pd.notna(row.get('curtidas')) else 0,
                            'comentarios': int(row.get('comentarios', 0)) if pd.notna(row.get('comentarios')) else 0,
                            'salvamentos': int(row.get('salvamentos', 0)) if pd.notna(row.get('salvamentos')) else 0,
                            'compartilhamentos': int(row.get('compartilhamentos', 0)) if pd.notna(row.get('compartilhamentos')) else 0,
                            'views': int(row.get('views', 0)) if pd.notna(row.get('views')) else 0,
                            'impressoes': int(row.get('impressoes', 0)) if pd.notna(row.get('impressoes')) else 0,
                            'alcance': int(row.get('alcance', 0)) if pd.notna(row.get('alcance')) else 0,
                            'link': str(row.get('link', '')) if pd.notna(row.get('link')) else ''
                        }
                        
                        # Calcular interacoes
                        post_data['interacoes'] = (
                            post_data['curtidas'] + 
                            post_data['comentarios'] + 
                            post_data['salvamentos'] + 
                            post_data['compartilhamentos']
                        )
                        
                        data_manager.adicionar_post(camp_id, inf_id, post_data)
                        posts_adicionados += 1
                    
                    st.success(f"Campanha importada com sucesso!")
                    st.info(f"{len(influenciadores_processados)} influenciadores | {posts_adicionados} posts")
                    
                    st.session_state.show_import_csv = False
                    st.session_state.campanha_atual_id = camp_id
                    st.rerun()
                else:
                    st.error("Preencha nome e cliente")
        
        except Exception as e:
            st.error(f"Erro ao processar CSV: {str(e)}")
