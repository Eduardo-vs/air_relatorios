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
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("Importar CSV", use_container_width=True):
            st.session_state.show_import_csv = True
    with col3:
        if st.button("+ Nova Campanha", type="primary", use_container_width=True):
            st.session_state.show_new_campaign = True
            st.session_state.edit_campanha_id = None
    
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
                
                di_val = datetime.strptime(camp_edit['data_inicio'], '%d/%m/%Y') if camp_edit else datetime.now()
                df_val = datetime.strptime(camp_edit['data_fim'], '%d/%m/%Y') if camp_edit else datetime.now() + timedelta(days=30)
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
            metricas_cfg = camp_edit.get('metricas_selecionadas', {}) if camp_edit else {}
            
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


def render_importar_csv():
    """Modal para importar campanha via CSV"""
    
    st.subheader("Importar Campanha via CSV")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Cancelar", use_container_width=True):
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
