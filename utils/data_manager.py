"""
Utils - Data Manager
Gerenciamento de dados e session state
"""

import streamlit as st
from datetime import datetime, timedelta
from utils.funcoes_auxiliares import classificar_influenciador

# ========================================
# INICIALIZAÇÃO
# ========================================

def inicializar_session_state():
    """Inicializa todas as variáveis do session state"""
    if 'campanhas' not in st.session_state:
        st.session_state.campanhas = []
    if 'clientes' not in st.session_state:
        st.session_state.clientes = []
    if 'influenciadores_base' not in st.session_state:
        st.session_state.influenciadores_base = []
    if 'campanha_atual_id' not in st.session_state:
        st.session_state.campanha_atual_id = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    if 'primary_color' not in st.session_state:
        st.session_state.primary_color = '#7c3aed'
    if 'secondary_color' not in st.session_state:
        st.session_state.secondary_color = '#fb923c'
    
    # Filtros globais
    if 'filtro_cliente_id' not in st.session_state:
        st.session_state.filtro_cliente_id = None
    if 'filtro_campanha_id' not in st.session_state:
        st.session_state.filtro_campanha_id = None
    if 'filtro_data_inicio' not in st.session_state:
        st.session_state.filtro_data_inicio = datetime.now() - timedelta(days=90)
    if 'filtro_data_fim' not in st.session_state:
        st.session_state.filtro_data_fim = datetime.now()

# ========================================
# FILTROS GLOBAIS
# ========================================

def renderizar_filtros_globais():
    """Renderiza os filtros globais de cliente, campanha e data"""
    with st.expander("🔍 Filtros Globais", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            opcoes_clientes = ["Todos os Clientes"] + [c['nome'] for c in st.session_state.clientes]
            cliente_sel = st.selectbox(
                "Cliente",
                opcoes_clientes,
                index=0 if not st.session_state.filtro_cliente_id else 
                      next((i+1 for i, c in enumerate(st.session_state.clientes) 
                           if c['id'] == st.session_state.filtro_cliente_id), 0),
                key="filtro_cliente_global"
            )
            
            if cliente_sel == "Todos os Clientes":
                st.session_state.filtro_cliente_id = None
            else:
                cliente_obj = next((c for c in st.session_state.clientes if c['nome'] == cliente_sel), None)
                st.session_state.filtro_cliente_id = cliente_obj['id'] if cliente_obj else None
        
        with col2:
            # Filtrar campanhas pelo cliente selecionado
            if st.session_state.filtro_cliente_id:
                campanhas_filtradas = [c for c in st.session_state.campanhas 
                                       if c['cliente_id'] == st.session_state.filtro_cliente_id]
            else:
                campanhas_filtradas = st.session_state.campanhas
            
            opcoes_campanhas = ["Todas as Campanhas"] + [c['nome'] for c in campanhas_filtradas]
            campanha_sel = st.selectbox(
                "Campanha",
                opcoes_campanhas,
                index=0,
                key="filtro_campanha_global"
            )
            
            if campanha_sel == "Todas as Campanhas":
                st.session_state.filtro_campanha_id = None
            else:
                camp_obj = next((c for c in campanhas_filtradas if c['nome'] == campanha_sel), None)
                st.session_state.filtro_campanha_id = camp_obj['id'] if camp_obj else None
        
        with col3:
            st.session_state.filtro_data_inicio = st.date_input(
                "Data Início",
                value=st.session_state.filtro_data_inicio,
                key="filtro_data_ini"
            )
        
        with col4:
            st.session_state.filtro_data_fim = st.date_input(
                "Data Fim",
                value=st.session_state.filtro_data_fim,
                key="filtro_data_f"
            )


def get_campanhas_filtradas():
    """Retorna campanhas baseado nos filtros globais"""
    campanhas = st.session_state.campanhas
    
    if st.session_state.filtro_cliente_id:
        campanhas = [c for c in campanhas if c['cliente_id'] == st.session_state.filtro_cliente_id]
    
    if st.session_state.filtro_campanha_id:
        campanhas = [c for c in campanhas if c['id'] == st.session_state.filtro_campanha_id]
    
    # Filtrar por data
    campanhas_filtradas = []
    for camp in campanhas:
        try:
            data_inicio = datetime.strptime(camp['data_inicio'], '%d/%m/%Y').date()
            data_fim = datetime.strptime(camp['data_fim'], '%d/%m/%Y').date()
            
            filtro_ini = st.session_state.filtro_data_inicio
            filtro_fim = st.session_state.filtro_data_fim
            
            if isinstance(filtro_ini, datetime):
                filtro_ini = filtro_ini.date()
            if isinstance(filtro_fim, datetime):
                filtro_fim = filtro_fim.date()
            
            # Campanha está no período se há interseção
            if data_inicio <= filtro_fim and data_fim >= filtro_ini:
                campanhas_filtradas.append(camp)
        except:
            campanhas_filtradas.append(camp)
    
    return campanhas_filtradas

# ========================================
# CLIENTES
# ========================================

def criar_cliente(dados):
    """Cria novo cliente"""
    cliente = {
        'id': len(st.session_state.clientes) + 1,
        'nome': dados['nome'],
        'cnpj': dados.get('cnpj', ''),
        'contato': dados.get('contato', ''),
        'email': dados.get('email', ''),
        'tipo': dados.get('tipo', 'normal'),  # normal (não mais AON por cliente)
        'created_at': datetime.now().isoformat()
    }
    st.session_state.clientes.append(cliente)
    return cliente

def get_cliente(cliente_id):
    """Busca cliente por ID"""
    for cli in st.session_state.clientes:
        if cli['id'] == cliente_id:
            return cli
    return None

# ========================================
# INFLUENCIADORES
# ========================================

def criar_influenciador_base(dados):
    """Cria influenciador na base geral"""
    influencer = {
        'id': len(st.session_state.influenciadores_base) + 1,
        'profile_id': dados.get('profile_id', ''),
        'nome': dados['nome'],
        'usuario': dados['usuario'],
        'redes_sociais': dados['redes_sociais'],
        'base_seguidores': dados['base_seguidores'],
        'seguidores_num': dados.get('seguidores_num', 0),
        'perfil_link': dados.get('perfil_link', ''),
        'taxa_engajamento': dados.get('taxa_engajamento', 0),
        'cidade': dados.get('cidade', ''),
        'endereco': dados.get('endereco', ''),
        'foto': dados.get('foto', ''),
        'score': dados.get('score', 0),
        'means': dados.get('means', {}),
        'hashtags': dados.get('hashtags', []),
        'classificacao': classificar_influenciador(dados['base_seguidores']),
        'created_at': datetime.now().isoformat()
    }
    st.session_state.influenciadores_base.append(influencer)
    return influencer


def criar_influenciador_da_api(api_data):
    """Cria influenciador a partir dos dados da API"""
    from utils.api_client import processar_dados_influenciador
    
    dados = processar_dados_influenciador(api_data)
    if dados:
        return criar_influenciador_base(dados)
    return None

# ========================================
# CAMPANHAS
# ========================================

def criar_campanha(dados):
    """Cria nova campanha"""
    campanha = {
        'id': len(st.session_state.campanhas) + 1,
        'nome': dados['nome'],
        'cliente_id': dados['cliente_id'],
        'cliente_nome': dados['cliente_nome'],
        'objetivo': dados['objetivo'],
        'data_inicio': dados['data_inicio'],
        'data_fim': dados['data_fim'],
        'tipo_dados': dados.get('tipo_dados', 'estatico'),
        'is_aon': dados.get('is_aon', False),  # AON agora é por campanha
        'metricas_selecionadas': dados.get('metricas_selecionadas', {
            'views': True,
            'alcance': True,
            'interacoes': True,
            'impressoes': True,
            'curtidas': True,
            'comentarios': True,
            'compartilhamentos': True,
            'saves': True,
            'clique_link': False,
            'cupom_conversoes': False
        }),
        'status': 'ativa',
        'influenciadores': [],
        'notas': '',  # Campo para escrita livre
        'created_at': datetime.now().isoformat()
    }
    st.session_state.campanhas.append(campanha)
    return campanha

def get_campanha(campanha_id):
    """Busca campanha por ID"""
    for camp in st.session_state.campanhas:
        if camp['id'] == campanha_id:
            return camp
    return None

def adicionar_influenciador_campanha(campanha_id, influencer_base_id):
    """Adiciona influenciador da base à campanha"""
    campanha = get_campanha(campanha_id)
    inf_base = next((i for i in st.session_state.influenciadores_base if i['id'] == influencer_base_id), None)
    
    if campanha and inf_base:
        influencer = {
            'id': len(campanha['influenciadores']) + 1,
            'base_id': inf_base['id'],
            'profile_id': inf_base.get('profile_id', ''),
            'nome': inf_base['nome'],
            'usuario': inf_base['usuario'],
            'redes_sociais': inf_base['redes_sociais'],
            'base_seguidores': inf_base['base_seguidores'],
            'seguidores_num': inf_base.get('seguidores_num', 0),
            'perfil_link': inf_base['perfil_link'],
            'taxa_engajamento': inf_base['taxa_engajamento'],
            'cidade': inf_base['cidade'],
            'foto': inf_base.get('foto', ''),
            'classificacao': inf_base['classificacao'],
            'posts': []
        }
        campanha['influenciadores'].append(influencer)
        return True
    return False

def get_influenciador(campanha_id, influencer_id):
    """Busca influenciador dentro de uma campanha"""
    campanha = get_campanha(campanha_id)
    if campanha:
        for inf in campanha['influenciadores']:
            if inf['id'] == influencer_id:
                return inf
    return None

# ========================================
# POSTS
# ========================================

def adicionar_post(campanha_id, influencer_id, dados):
    """Adiciona post a um influenciador"""
    influencer = get_influenciador(campanha_id, influencer_id)
    if influencer:
        post = {
            'id': len(influencer['posts']) + 1,
            'formato': dados['formato'],
            'plataforma': dados['plataforma'],
            'data_publicacao': dados['data_publicacao'],
            'link_post': dados.get('link_post', ''),
            'metricas': {
                'views': dados.get('views', 0),
                'alcance': dados.get('alcance', 0),
                'interacoes': dados.get('interacoes', 0),
                'impressoes': dados.get('impressoes', 0),
                'curtidas': dados.get('curtidas', 0),
                'comentarios_qtd': dados.get('comentarios_qtd', 0),
                'compartilhamentos': dados.get('compartilhamentos', 0),
                'saves': dados.get('saves', 0),
                'clique_link': dados.get('clique_link', 0),
                'cupom_conversoes': dados.get('cupom_conversoes', 0),
                'cupom_codigo': dados.get('cupom_codigo', '')
            },
            'imagens': dados.get('imagens', []),
            'comentarios': []
        }
        influencer['posts'].append(post)
        return True
    return False

# ========================================
# MÉTRICAS
# ========================================

def calcular_metricas_campanha(campanha):
    """Calcula todas as métricas de uma campanha"""
    total_views = 0
    total_alcance = 0
    total_interacoes = 0
    total_impressoes = 0
    total_posts = 0
    total_saves = 0
    total_compartilhamentos = 0
    total_conversoes_cupom = 0
    total_curtidas = 0
    total_comentarios = 0
    total_cliques_link = 0
    total_seguidores = 0
    total_influenciadores = len(campanha['influenciadores'])
    
    for inf in campanha['influenciadores']:
        total_seguidores += inf.get('seguidores_num', 0)
        
        for post in inf['posts']:
            m = post['metricas']
            total_views += m['views']
            total_alcance += m.get('alcance', 0)
            total_interacoes += m['interacoes']
            total_impressoes += m.get('impressoes', 0)
            total_saves += m['saves']
            total_compartilhamentos += m['compartilhamentos']
            total_conversoes_cupom += m.get('cupom_conversoes', 0)
            total_curtidas += m.get('curtidas', 0)
            total_comentarios += m.get('comentarios_qtd', 0)
            total_cliques_link += m.get('clique_link', 0)
            total_posts += 1
    
    eng_efetivo = (total_interacoes / total_views * 100) if total_views > 0 else 0
    taxa_alcance = (total_alcance / total_seguidores * 100) if total_seguidores > 0 else 0
    
    return {
        'total_views': total_views,
        'total_alcance': total_alcance,
        'total_interacoes': total_interacoes,
        'total_impressoes': total_impressoes,
        'total_posts': total_posts,
        'total_saves': total_saves,
        'total_compartilhamentos': total_compartilhamentos,
        'total_conversoes_cupom': total_conversoes_cupom,
        'total_curtidas': total_curtidas,
        'total_comentarios': total_comentarios,
        'total_cliques_link': total_cliques_link,
        'total_influenciadores': total_influenciadores,
        'total_seguidores': total_seguidores,
        'engajamento_efetivo': round(eng_efetivo, 2),
        'taxa_alcance': round(taxa_alcance, 2)
    }


def calcular_metricas_por_cliente(cliente_id):
    """Calcula métricas agregadas por cliente"""
    campanhas_cliente = [c for c in st.session_state.campanhas if c['cliente_id'] == cliente_id]
    
    totais = {
        'total_campanhas': len(campanhas_cliente),
        'total_views': 0,
        'total_alcance': 0,
        'total_interacoes': 0,
        'total_posts': 0,
        'total_influenciadores': 0,
        'total_seguidores': 0
    }
    
    influenciadores_unicos = set()
    
    for camp in campanhas_cliente:
        metricas = calcular_metricas_campanha(camp)
        totais['total_views'] += metricas['total_views']
        totais['total_alcance'] += metricas['total_alcance']
        totais['total_interacoes'] += metricas['total_interacoes']
        totais['total_posts'] += metricas['total_posts']
        totais['total_seguidores'] += metricas['total_seguidores']
        
        for inf in camp['influenciadores']:
            influenciadores_unicos.add(inf.get('base_id', inf['id']))
    
    totais['total_influenciadores'] = len(influenciadores_unicos)
    
    return totais
