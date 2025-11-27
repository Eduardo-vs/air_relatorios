"""
Data Manager - Gerenciamento de dados com suporte a banco de dados e session_state
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

# Tentar importar banco de dados (pode nao estar disponivel em todos os ambientes)
try:
    from utils.database import get_db, Cliente, Influenciador, Campanha, CampanhaInfluenciador, Post, Comentario
    DB_AVAILABLE = True
except:
    DB_AVAILABLE = False

# ========================================
# INICIALIZACAO
# ========================================

def inicializar_session_state():
    """Inicializa todas as variaveis do session state"""
    if 'clientes' not in st.session_state:
        st.session_state.clientes = []
    if 'influenciadores' not in st.session_state:
        st.session_state.influenciadores = []
    if 'campanhas' not in st.session_state:
        st.session_state.campanhas = []
    if 'campanha_atual_id' not in st.session_state:
        st.session_state.campanha_atual_id = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    if 'primary_color' not in st.session_state:
        st.session_state.primary_color = '#7c3aed'
    if 'secondary_color' not in st.session_state:
        st.session_state.secondary_color = '#fb923c'
    
    # Modo de relatorio
    if 'modo_relatorio' not in st.session_state:
        st.session_state.modo_relatorio = 'campanha'
    if 'relatorio_cliente_id' not in st.session_state:
        st.session_state.relatorio_cliente_id = None
    if 'relatorio_campanhas_ids' not in st.session_state:
        st.session_state.relatorio_campanhas_ids = []


def classificar_influenciador(seguidores: int) -> str:
    """Classifica influenciador por numero de seguidores"""
    if seguidores < 10000:
        return 'Nano'
    elif seguidores < 100000:
        return 'Micro'
    elif seguidores < 500000:
        return 'Mid'
    elif seguidores < 1000000:
        return 'Macro'
    else:
        return 'Mega'


# ========================================
# CLIENTES
# ========================================

def criar_cliente(dados: Dict) -> Dict:
    """Cria novo cliente"""
    cliente = {
        'id': len(st.session_state.clientes) + 1,
        'nome': dados['nome'],
        'cnpj': dados.get('cnpj', ''),
        'contato': dados.get('contato', ''),
        'email': dados.get('email', ''),
        'is_aon': dados.get('is_aon', False),
        'created_at': datetime.now().isoformat()
    }
    st.session_state.clientes.append(cliente)
    return cliente


def get_cliente(cliente_id: int) -> Optional[Dict]:
    """Busca cliente por ID"""
    for cli in st.session_state.clientes:
        if cli['id'] == cliente_id:
            return cli
    return None


def get_clientes() -> List[Dict]:
    """Retorna todos os clientes"""
    return st.session_state.clientes


def atualizar_cliente(cliente_id: int, dados: Dict) -> bool:
    """Atualiza dados de um cliente"""
    for i, cli in enumerate(st.session_state.clientes):
        if cli['id'] == cliente_id:
            for key, value in dados.items():
                if key != 'id':
                    st.session_state.clientes[i][key] = value
            return True
    return False


def excluir_cliente(cliente_id: int) -> bool:
    """Exclui um cliente"""
    st.session_state.clientes = [c for c in st.session_state.clientes if c['id'] != cliente_id]
    return True


# ========================================
# INFLUENCIADORES
# ========================================

def criar_influenciador(dados: Dict) -> Dict:
    """Cria influenciador na base (dados da API ou manual)"""
    influenciador = {
        'id': len(st.session_state.influenciadores) + 1,
        'profile_id': dados.get('profile_id', ''),
        'nome': dados.get('nome', ''),
        'usuario': dados.get('usuario', ''),
        'network': dados.get('network', 'instagram'),
        'seguidores': dados.get('seguidores', 0),
        'foto': dados.get('foto', ''),
        'bio': dados.get('bio', ''),
        'engagement_rate': dados.get('engagement_rate', 0),
        'air_score': dados.get('air_score', 0),
        'reach_rate': dados.get('reach_rate', 0),
        'means': dados.get('means', {}),
        'hashtags': dados.get('hashtags', []),
        'classificacao': classificar_influenciador(dados.get('seguidores', 0)),
        'total_posts': dados.get('total_posts', 0),
        'total_likes': dados.get('total_likes', 0),
        'total_views': dados.get('total_views', 0),
        'total_comments': dados.get('total_comments', 0),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    st.session_state.influenciadores.append(influenciador)
    return influenciador


def get_influenciador(influenciador_id: int) -> Optional[Dict]:
    """Busca influenciador por ID"""
    for inf in st.session_state.influenciadores:
        if inf['id'] == influenciador_id:
            return inf
    return None


def get_influenciador_por_profile_id(profile_id: str) -> Optional[Dict]:
    """Busca influenciador por profile_id da API"""
    for inf in st.session_state.influenciadores:
        if inf.get('profile_id') == profile_id:
            return inf
    return None


def atualizar_influenciador(influenciador_id: int, dados: Dict) -> bool:
    """Atualiza dados de um influenciador"""
    for i, inf in enumerate(st.session_state.influenciadores):
        if inf['id'] == influenciador_id:
            for key, value in dados.items():
                if key != 'id':
                    st.session_state.influenciadores[i][key] = value
            st.session_state.influenciadores[i]['updated_at'] = datetime.now().isoformat()
            st.session_state.influenciadores[i]['classificacao'] = classificar_influenciador(
                dados.get('seguidores', inf.get('seguidores', 0))
            )
            return True
    return False


def get_influenciadores() -> List[Dict]:
    """Retorna todos os influenciadores"""
    return st.session_state.influenciadores


def excluir_influenciador(influenciador_id: int) -> bool:
    """Exclui um influenciador"""
    st.session_state.influenciadores = [i for i in st.session_state.influenciadores if i['id'] != influenciador_id]
    return True


def calcular_classificacao(seguidores: int) -> str:
    """Alias para classificar_influenciador"""
    return classificar_influenciador(seguidores)


# ========================================
# CAMPANHAS
# ========================================

def criar_campanha(dados: Dict) -> Dict:
    """Cria nova campanha"""
    campanha = {
        'id': len(st.session_state.campanhas) + 1,
        'nome': dados['nome'],
        'cliente_id': dados['cliente_id'],
        'cliente_nome': dados.get('cliente_nome', ''),
        'objetivo': dados.get('objetivo', ''),
        'data_inicio': dados['data_inicio'],
        'data_fim': dados['data_fim'],
        'tipo_dados': dados.get('tipo_dados', 'estatico'),
        'is_aon': dados.get('is_aon', False),
        'status': dados.get('status', 'ativa'),
        'metricas_selecionadas': dados.get('metricas_selecionadas', {
            'views': True, 'alcance': True, 'interacoes': True, 'impressoes': True,
            'curtidas': True, 'comentarios': True, 'compartilhamentos': True, 'saves': True,
            'clique_link': False, 'cupom_conversoes': False
        }),
        'insights_config': dados.get('insights_config', {
            'mostrar_engajamento': True, 'mostrar_alcance': True, 'mostrar_conversao': True,
            'mostrar_saves': True, 'mostrar_comparativo_formato': True, 'mostrar_top_influenciadores': True,
            'insights_personalizados': []
        }),
        'categorias_comentarios': dados.get('categorias_comentarios', [
            'Elogio ao Produto', 'Intencao de Compra', 'Conexao Emocional', 'Duvida', 'Critica', 'Geral'
        ]),
        'notas': '',
        'influenciadores': [],  # Lista de {influenciador_id, snapshot_dados, posts}
        'created_at': datetime.now().isoformat()
    }
    st.session_state.campanhas.append(campanha)
    return campanha


def get_campanha(campanha_id: int) -> Optional[Dict]:
    """Busca campanha por ID"""
    for camp in st.session_state.campanhas:
        if camp['id'] == campanha_id:
            return camp
    return None


def atualizar_campanha(campanha_id: int, dados: Dict) -> bool:
    """Atualiza dados de uma campanha"""
    for i, camp in enumerate(st.session_state.campanhas):
        if camp['id'] == campanha_id:
            for key, value in dados.items():
                if key != 'id':
                    st.session_state.campanhas[i][key] = value
            return True
    return False


def get_campanhas() -> List[Dict]:
    """Retorna todas as campanhas"""
    return st.session_state.campanhas


def excluir_campanha(campanha_id: int) -> bool:
    """Exclui uma campanha"""
    st.session_state.campanhas = [c for c in st.session_state.campanhas if c['id'] != campanha_id]
    if st.session_state.campanha_atual_id == campanha_id:
        st.session_state.campanha_atual_id = None
    return True


def get_campanhas_por_cliente(cliente_id: int) -> List[Dict]:
    """Retorna campanhas de um cliente"""
    return [c for c in st.session_state.campanhas if c['cliente_id'] == cliente_id]


# ========================================
# INFLUENCIADORES NA CAMPANHA
# ========================================

def adicionar_influenciador_campanha(campanha_id: int, influenciador_id: int) -> bool:
    """Adiciona influenciador a uma campanha com snapshot dos dados"""
    campanha = get_campanha(campanha_id)
    influenciador = get_influenciador(influenciador_id)
    
    if not campanha or not influenciador:
        return False
    
    # Verificar se ja existe
    for inf in campanha['influenciadores']:
        if inf['influenciador_id'] == influenciador_id:
            return False
    
    # Criar snapshot dos dados (para campanhas estaticas)
    snapshot = {
        'seguidores': influenciador['seguidores'],
        'engagement_rate': influenciador['engagement_rate'],
        'air_score': influenciador['air_score'],
        'classificacao': influenciador['classificacao']
    }
    
    campanha['influenciadores'].append({
        'id': len(campanha['influenciadores']) + 1,
        'influenciador_id': influenciador_id,
        'snapshot_dados': snapshot,
        'posts': []
    })
    
    return True


def remover_influenciador_campanha(campanha_id: int, influenciador_id: int) -> bool:
    """Remove influenciador de uma campanha"""
    campanha = get_campanha(campanha_id)
    if not campanha:
        return False
    
    campanha['influenciadores'] = [
        inf for inf in campanha['influenciadores'] 
        if inf['influenciador_id'] != influenciador_id
    ]
    return True


def get_influenciadores_campanha(campanha_id: int) -> List[Dict]:
    """Retorna influenciadores de uma campanha com dados completos"""
    campanha = get_campanha(campanha_id)
    if not campanha:
        return []
    
    resultado = []
    for camp_inf in campanha['influenciadores']:
        inf = get_influenciador(camp_inf['influenciador_id'])
        if inf:
            # Usar dados do snapshot para campanhas estaticas
            if campanha['tipo_dados'] == 'estatico':
                dados = {**inf, **camp_inf['snapshot_dados']}
            else:
                dados = inf.copy()
            
            dados['campanha_influenciador_id'] = camp_inf['id']
            dados['posts'] = camp_inf['posts']
            resultado.append(dados)
    
    return resultado


# ========================================
# POSTS
# ========================================

def adicionar_post(campanha_id: int, influenciador_id: int, dados: Dict) -> bool:
    """Adiciona post a um influenciador na campanha"""
    campanha = get_campanha(campanha_id)
    if not campanha:
        return False
    
    for inf in campanha['influenciadores']:
        if inf['influenciador_id'] == influenciador_id:
            post = {
                'id': len(inf['posts']) + 1,
                'formato': dados['formato'],
                'plataforma': dados['plataforma'],
                'data_publicacao': dados['data_publicacao'],
                'link_post': dados.get('link_post', ''),
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
                'cupom_codigo': dados.get('cupom_codigo', ''),
                'custo': dados.get('custo', 0),
                'imagens': dados.get('imagens', []),
                'comentarios': []
            }
            inf['posts'].append(post)
            return True
    return False


def atualizar_post(campanha_id: int, influenciador_id: int, post_id: int, dados: Dict) -> bool:
    """Atualiza um post"""
    campanha = get_campanha(campanha_id)
    if not campanha:
        return False
    
    for inf in campanha['influenciadores']:
        if inf['influenciador_id'] == influenciador_id:
            for i, post in enumerate(inf['posts']):
                if post['id'] == post_id:
                    for key, value in dados.items():
                        if key != 'id':
                            inf['posts'][i][key] = value
                    return True
    return False


def remover_post(campanha_id: int, influenciador_id: int, post_id: int) -> bool:
    """Remove um post"""
    campanha = get_campanha(campanha_id)
    if not campanha:
        return False
    
    for inf in campanha['influenciadores']:
        if inf['influenciador_id'] == influenciador_id:
            inf['posts'] = [p for p in inf['posts'] if p['id'] != post_id]
            return True
    return False


# ========================================
# COMENTARIOS
# ========================================

def adicionar_comentario(campanha_id: int, influenciador_id: int, post_id: int, dados: Dict) -> bool:
    """Adiciona comentario a um post"""
    campanha = get_campanha(campanha_id)
    if not campanha:
        return False
    
    for inf in campanha['influenciadores']:
        if inf['influenciador_id'] == influenciador_id:
            for post in inf['posts']:
                if post['id'] == post_id:
                    comentario = {
                        'id': len(post['comentarios']) + 1,
                        'texto': dados['texto'],
                        'autor': dados.get('autor', ''),
                        'data': dados.get('data', ''),
                        'polaridade': dados.get('polaridade', 'neutro'),
                        'categoria': dados.get('categoria', 'Geral'),
                        'aderente_campanha': dados.get('aderente_campanha', False)
                    }
                    post['comentarios'].append(comentario)
                    return True
    return False


# ========================================
# METRICAS E CALCULOS
# ========================================

def calcular_metricas_campanha(campanha: Dict) -> Dict:
    """Calcula todas as metricas de uma campanha"""
    totais = {
        'total_influenciadores': len(campanha['influenciadores']),
        'total_posts': 0,
        'total_views': 0,
        'total_alcance': 0,
        'total_interacoes': 0,
        'total_impressoes': 0,
        'total_curtidas': 0,
        'total_comentarios': 0,
        'total_compartilhamentos': 0,
        'total_saves': 0,
        'total_cliques_link': 0,
        'total_conversoes_cupom': 0,
        'total_custo': 0,
        'total_seguidores': 0,
        'engajamento_efetivo': 0,
        'taxa_alcance': 0,
        'custo_por_view': 0,
        'custo_por_engajamento': 0
    }
    
    for camp_inf in campanha['influenciadores']:
        inf = get_influenciador(camp_inf['influenciador_id'])
        if inf:
            if campanha['tipo_dados'] == 'estatico':
                totais['total_seguidores'] += camp_inf['snapshot_dados'].get('seguidores', 0)
            else:
                totais['total_seguidores'] += inf.get('seguidores', 0)
        
        for post in camp_inf['posts']:
            totais['total_posts'] += 1
            totais['total_views'] += post.get('views', 0)
            totais['total_alcance'] += post.get('alcance', 0)
            totais['total_interacoes'] += post.get('interacoes', 0)
            totais['total_impressoes'] += post.get('impressoes', 0)
            totais['total_curtidas'] += post.get('curtidas', 0)
            totais['total_comentarios'] += post.get('comentarios_qtd', 0)
            totais['total_compartilhamentos'] += post.get('compartilhamentos', 0)
            totais['total_saves'] += post.get('saves', 0)
            totais['total_cliques_link'] += post.get('clique_link', 0)
            totais['total_conversoes_cupom'] += post.get('cupom_conversoes', 0)
            totais['total_custo'] += post.get('custo', 0)
    
    # Calcular taxas
    if totais['total_views'] > 0:
        totais['engajamento_efetivo'] = round(totais['total_interacoes'] / totais['total_views'] * 100, 2)
        totais['custo_por_view'] = round(totais['total_custo'] / totais['total_views'], 4) if totais['total_custo'] > 0 else 0
    
    if totais['total_seguidores'] > 0:
        totais['taxa_alcance'] = round(totais['total_alcance'] / totais['total_seguidores'] * 100, 2)
    
    if totais['total_interacoes'] > 0 and totais['total_custo'] > 0:
        totais['custo_por_engajamento'] = round(totais['total_custo'] / totais['total_interacoes'], 4)
    
    return totais


def calcular_metricas_multiplas_campanhas(campanhas_list: List[Dict]) -> Dict:
    """Calcula metricas agregadas de multiplas campanhas"""
    totais = {
        'total_campanhas': len(campanhas_list),
        'total_influenciadores': 0,
        'total_posts': 0,
        'total_views': 0,
        'total_alcance': 0,
        'total_interacoes': 0,
        'total_impressoes': 0,
        'total_curtidas': 0,
        'total_comentarios': 0,
        'total_compartilhamentos': 0,
        'total_saves': 0,
        'total_cliques_link': 0,
        'total_conversoes_cupom': 0,
        'total_custo': 0,
        'total_seguidores': 0,
        'engajamento_efetivo': 0,
        'taxa_alcance': 0
    }
    
    influenciadores_unicos = set()
    
    for camp in campanhas_list:
        metricas = calcular_metricas_campanha(camp)
        for key in totais:
            if key.startswith('total_') and key != 'total_campanhas' and key != 'total_influenciadores':
                totais[key] += metricas.get(key, 0)
        
        for inf in camp['influenciadores']:
            influenciadores_unicos.add(inf['influenciador_id'])
    
    totais['total_influenciadores'] = len(influenciadores_unicos)
    
    # Calcular taxas agregadas
    if totais['total_views'] > 0:
        totais['engajamento_efetivo'] = round(totais['total_interacoes'] / totais['total_views'] * 100, 2)
    if totais['total_seguidores'] > 0:
        totais['taxa_alcance'] = round(totais['total_alcance'] / totais['total_seguidores'] * 100, 2)
    
    return totais


def calcular_metricas_por_cliente(cliente_id: int) -> Dict:
    """Calcula metricas agregadas por cliente"""
    campanhas_cliente = get_campanhas_por_cliente(cliente_id)
    metricas = calcular_metricas_multiplas_campanhas(campanhas_cliente)
    metricas['total_campanhas'] = len(campanhas_cliente)
    return metricas
