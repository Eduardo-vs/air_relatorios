"""
Utils - Data Manager
Gerenciamento de dados e session state
"""

import streamlit as st
from datetime import datetime
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
        'tipo': dados.get('tipo', 'normal'),  # normal ou aon
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
        'nome': dados['nome'],
        'usuario': dados['usuario'],
        'redes_sociais': dados['redes_sociais'],
        'base_seguidores': dados['base_seguidores'],
        'perfil_link': dados.get('perfil_link', ''),
        'taxa_engajamento': dados.get('taxa_engajamento', 0),
        'cidade': dados.get('cidade', ''),
        'endereco': dados.get('endereco', ''),
        'classificacao': classificar_influenciador(dados['base_seguidores']),
        'created_at': datetime.now().isoformat()
    }
    st.session_state.influenciadores_base.append(influencer)
    return influencer

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
        'metricas_selecionadas': dados.get('metricas_selecionadas', {
            'views': True,
            'interacoes': True,
            'curtidas': True,
            'comentarios': True,
            'compartilhamentos': True,
            'saves': True,
            'clique_link': False,
            'cupom_conversoes': False
        }),
        'status': 'ativa',
        'influenciadores': [],
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
            'nome': inf_base['nome'],
            'usuario': inf_base['usuario'],
            'redes_sociais': inf_base['redes_sociais'],
            'base_seguidores': inf_base['base_seguidores'],
            'perfil_link': inf_base['perfil_link'],
            'taxa_engajamento': inf_base['taxa_engajamento'],
            'cidade': inf_base['cidade'],
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
                'interacoes': dados.get('interacoes', 0),
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
    total_interacoes = 0
    total_posts = 0
    total_saves = 0
    total_compartilhamentos = 0
    total_conversoes_cupom = 0
    total_curtidas = 0
    total_comentarios = 0
    total_cliques_link = 0
    
    for inf in campanha['influenciadores']:
        for post in inf['posts']:
            m = post['metricas']
            total_views += m['views']
            total_interacoes += m['interacoes']
            total_saves += m['saves']
            total_compartilhamentos += m['compartilhamentos']
            total_conversoes_cupom += m.get('cupom_conversoes', 0)
            total_curtidas += m.get('curtidas', 0)
            total_comentarios += m.get('comentarios_qtd', 0)
            total_cliques_link += m.get('clique_link', 0)
            total_posts += 1
    
    eng_efetivo = (total_interacoes / total_views * 100) if total_views > 0 else 0
    
    return {
        'total_views': total_views,
        'total_interacoes': total_interacoes,
        'total_posts': total_posts,
        'total_saves': total_saves,
        'total_compartilhamentos': total_compartilhamentos,
        'total_conversoes_cupom': total_conversoes_cupom,
        'total_curtidas': total_curtidas,
        'total_comentarios': total_comentarios,
        'total_cliques_link': total_cliques_link,
        'engajamento_efetivo': round(eng_efetivo, 2)
    }
