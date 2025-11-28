"""
Data Manager - Gerenciamento de dados com SQLite persistente
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional
import json
import sqlite3
import os

# Caminho do banco de dados
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'air_relatorios.db')


def get_db_connection():
    """Retorna conexao com o banco SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa as tabelas do banco de dados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj TEXT,
            contato TEXT,
            email TEXT,
            created_at TEXT
        )
    ''')
    
    # Tabela de influenciadores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS influenciadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT,
            nome TEXT NOT NULL,
            usuario TEXT NOT NULL,
            network TEXT,
            seguidores INTEGER DEFAULT 0,
            foto TEXT,
            bio TEXT,
            engagement_rate REAL DEFAULT 0,
            air_score REAL DEFAULT 0,
            reach_rate REAL DEFAULT 0,
            means TEXT,
            hashtags TEXT,
            classificacao TEXT,
            total_posts INTEGER DEFAULT 0,
            total_likes INTEGER DEFAULT 0,
            total_views INTEGER DEFAULT 0,
            total_comments INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Tabela de campanhas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campanhas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cliente_id INTEGER,
            cliente_nome TEXT,
            objetivo TEXT,
            data_inicio TEXT,
            data_fim TEXT,
            tipo_dados TEXT DEFAULT 'estatico',
            is_aon INTEGER DEFAULT 0,
            status TEXT DEFAULT 'ativa',
            metricas_selecionadas TEXT,
            insights_config TEXT,
            categorias_comentarios TEXT,
            notas TEXT,
            influenciadores TEXT,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()


# Inicializa o banco ao importar o modulo
init_db()


# ========================================
# INICIALIZACAO
# ========================================

def inicializar_session_state():
    """Inicializa variaveis do session state (apenas UI, nao dados)"""
    if 'campanha_atual_id' not in st.session_state:
        st.session_state.campanha_atual_id = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    if 'primary_color' not in st.session_state:
        st.session_state.primary_color = '#7c3aed'
    if 'secondary_color' not in st.session_state:
        st.session_state.secondary_color = '#fb923c'
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


def calcular_classificacao(seguidores: int) -> str:
    """Alias para classificar_influenciador"""
    return classificar_influenciador(seguidores)


# ========================================
# CLIENTES
# ========================================

def criar_cliente(dados: Dict) -> Dict:
    """Cria novo cliente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO clientes (nome, cnpj, contato, email, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        dados['nome'],
        dados.get('cnpj', ''),
        dados.get('contato', ''),
        dados.get('email', ''),
        datetime.now().isoformat()
    ))
    
    cliente_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {'id': cliente_id, **dados}


def get_cliente(cliente_id: int) -> Optional[Dict]:
    """Busca cliente por ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM clientes WHERE id = ?', (cliente_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_clientes() -> List[Dict]:
    """Retorna todos os clientes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM clientes ORDER BY nome')
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def atualizar_cliente(cliente_id: int, dados: Dict) -> bool:
    """Atualiza dados de um cliente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE clientes SET nome=?, cnpj=?, contato=?, email=? WHERE id=?
    ''', (
        dados.get('nome', ''),
        dados.get('cnpj', ''),
        dados.get('contato', ''),
        dados.get('email', ''),
        cliente_id
    ))
    
    conn.commit()
    conn.close()
    return True


def excluir_cliente(cliente_id: int) -> bool:
    """Exclui um cliente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
    
    conn.commit()
    conn.close()
    return True


# ========================================
# INFLUENCIADORES
# ========================================

def criar_influenciador(dados: Dict) -> Dict:
    """Cria influenciador na base"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    classificacao = classificar_influenciador(dados.get('seguidores', 0))
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO influenciadores (
            profile_id, nome, usuario, network, seguidores, foto, bio,
            engagement_rate, air_score, reach_rate, means, hashtags,
            classificacao, total_posts, total_likes, total_views, total_comments,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        dados.get('profile_id', ''),
        dados.get('nome', ''),
        dados.get('usuario', ''),
        dados.get('network', 'instagram'),
        dados.get('seguidores', 0),
        dados.get('foto', ''),
        dados.get('bio', ''),
        dados.get('engagement_rate', 0),
        dados.get('air_score', 0),
        dados.get('reach_rate', 0),
        json.dumps(dados.get('means', {})),
        json.dumps(dados.get('hashtags', [])),
        classificacao,
        dados.get('total_posts', 0),
        dados.get('total_likes', 0),
        dados.get('total_views', 0),
        dados.get('total_comments', 0),
        now,
        now
    ))
    
    inf_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {'id': inf_id, 'classificacao': classificacao, **dados}


def get_influenciador(influenciador_id: int) -> Optional[Dict]:
    """Busca influenciador por ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM influenciadores WHERE id = ?', (influenciador_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        inf = dict(row)
        inf['means'] = json.loads(inf['means']) if inf['means'] else {}
        inf['hashtags'] = json.loads(inf['hashtags']) if inf['hashtags'] else []
        return inf
    return None


def get_influenciador_por_profile_id(profile_id: str) -> Optional[Dict]:
    """Busca influenciador por profile_id da API"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM influenciadores WHERE profile_id = ?', (profile_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        inf = dict(row)
        inf['means'] = json.loads(inf['means']) if inf['means'] else {}
        inf['hashtags'] = json.loads(inf['hashtags']) if inf['hashtags'] else []
        return inf
    return None


def atualizar_influenciador(influenciador_id: int, dados: Dict) -> bool:
    """Atualiza dados de um influenciador"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    classificacao = classificar_influenciador(dados.get('seguidores', 0))
    
    cursor.execute('''
        UPDATE influenciadores SET
            profile_id=?, nome=?, usuario=?, network=?, seguidores=?, foto=?, bio=?,
            engagement_rate=?, air_score=?, reach_rate=?, means=?, hashtags=?,
            classificacao=?, total_posts=?, total_likes=?, total_views=?, total_comments=?,
            updated_at=?
        WHERE id=?
    ''', (
        dados.get('profile_id', ''),
        dados.get('nome', ''),
        dados.get('usuario', ''),
        dados.get('network', 'instagram'),
        dados.get('seguidores', 0),
        dados.get('foto', ''),
        dados.get('bio', ''),
        dados.get('engagement_rate', 0),
        dados.get('air_score', 0),
        dados.get('reach_rate', 0),
        json.dumps(dados.get('means', {})),
        json.dumps(dados.get('hashtags', [])),
        classificacao,
        dados.get('total_posts', 0),
        dados.get('total_likes', 0),
        dados.get('total_views', 0),
        dados.get('total_comments', 0),
        datetime.now().isoformat(),
        influenciador_id
    ))
    
    conn.commit()
    conn.close()
    return True


def get_influenciadores() -> List[Dict]:
    """Retorna todos os influenciadores"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM influenciadores ORDER BY nome')
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        inf = dict(row)
        inf['means'] = json.loads(inf['means']) if inf['means'] else {}
        inf['hashtags'] = json.loads(inf['hashtags']) if inf['hashtags'] else []
        result.append(inf)
    
    return result


def excluir_influenciador(influenciador_id: int) -> bool:
    """Exclui um influenciador"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM influenciadores WHERE id = ?', (influenciador_id,))
    
    conn.commit()
    conn.close()
    return True


# ========================================
# CAMPANHAS
# ========================================

def criar_campanha(dados: Dict) -> Dict:
    """Cria nova campanha"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    metricas_default = {
        'views': True, 'alcance': True, 'interacoes': True, 'impressoes': True,
        'curtidas': True, 'comentarios': True, 'compartilhamentos': True, 'saves': True,
        'clique_link': False, 'cupom_conversoes': False
    }
    
    insights_default = {
        'mostrar_engajamento': True, 'mostrar_alcance': True, 'mostrar_conversao': True,
        'mostrar_saves': True, 'mostrar_comparativo_formato': True, 'mostrar_top_influenciadores': True,
        'insights_personalizados': []
    }
    
    categorias_default = ['Elogio ao Produto', 'Intencao de Compra', 'Conexao Emocional', 'Duvida', 'Critica', 'Geral']
    
    cursor.execute('''
        INSERT INTO campanhas (
            nome, cliente_id, cliente_nome, objetivo, data_inicio, data_fim,
            tipo_dados, is_aon, status, metricas_selecionadas, insights_config,
            categorias_comentarios, notas, influenciadores, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        dados['nome'],
        dados['cliente_id'],
        dados.get('cliente_nome', ''),
        dados.get('objetivo', ''),
        dados['data_inicio'],
        dados['data_fim'],
        dados.get('tipo_dados', 'estatico'),
        1 if dados.get('is_aon', False) else 0,
        dados.get('status', 'ativa'),
        json.dumps(dados.get('metricas_selecionadas', metricas_default)),
        json.dumps(dados.get('insights_config', insights_default)),
        json.dumps(dados.get('categorias_comentarios', categorias_default)),
        '',
        json.dumps([]),
        datetime.now().isoformat()
    ))
    
    camp_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {'id': camp_id, **dados, 'influenciadores': []}


def get_campanha(campanha_id: int) -> Optional[Dict]:
    """Busca campanha por ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM campanhas WHERE id = ?', (campanha_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        camp = dict(row)
        camp['is_aon'] = bool(camp['is_aon'])
        camp['metricas_selecionadas'] = json.loads(camp['metricas_selecionadas']) if camp['metricas_selecionadas'] else {}
        camp['insights_config'] = json.loads(camp['insights_config']) if camp['insights_config'] else {}
        camp['categorias_comentarios'] = json.loads(camp['categorias_comentarios']) if camp['categorias_comentarios'] else []
        camp['influenciadores'] = json.loads(camp['influenciadores']) if camp['influenciadores'] else []
        return camp
    return None


def atualizar_campanha(campanha_id: int, dados: Dict) -> bool:
    """Atualiza dados de uma campanha"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Buscar campanha atual para mesclar dados
    camp_atual = get_campanha(campanha_id)
    if not camp_atual:
        conn.close()
        return False
    
    # Mesclar dados
    for key, value in dados.items():
        camp_atual[key] = value
    
    cursor.execute('''
        UPDATE campanhas SET
            nome=?, cliente_id=?, cliente_nome=?, objetivo=?, data_inicio=?, data_fim=?,
            tipo_dados=?, is_aon=?, status=?, metricas_selecionadas=?, insights_config=?,
            categorias_comentarios=?, notas=?, influenciadores=?
        WHERE id=?
    ''', (
        camp_atual['nome'],
        camp_atual['cliente_id'],
        camp_atual.get('cliente_nome', ''),
        camp_atual.get('objetivo', ''),
        camp_atual['data_inicio'],
        camp_atual['data_fim'],
        camp_atual.get('tipo_dados', 'estatico'),
        1 if camp_atual.get('is_aon', False) else 0,
        camp_atual.get('status', 'ativa'),
        json.dumps(camp_atual.get('metricas_selecionadas', {})),
        json.dumps(camp_atual.get('insights_config', {})),
        json.dumps(camp_atual.get('categorias_comentarios', [])),
        camp_atual.get('notas', ''),
        json.dumps(camp_atual.get('influenciadores', [])),
        campanha_id
    ))
    
    conn.commit()
    conn.close()
    return True


def get_campanhas() -> List[Dict]:
    """Retorna todas as campanhas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM campanhas ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        camp = dict(row)
        camp['is_aon'] = bool(camp['is_aon'])
        camp['metricas_selecionadas'] = json.loads(camp['metricas_selecionadas']) if camp['metricas_selecionadas'] else {}
        camp['insights_config'] = json.loads(camp['insights_config']) if camp['insights_config'] else {}
        camp['categorias_comentarios'] = json.loads(camp['categorias_comentarios']) if camp['categorias_comentarios'] else []
        camp['influenciadores'] = json.loads(camp['influenciadores']) if camp['influenciadores'] else []
        result.append(camp)
    
    return result


def excluir_campanha(campanha_id: int) -> bool:
    """Exclui uma campanha"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM campanhas WHERE id = ?', (campanha_id,))
    
    conn.commit()
    conn.close()
    
    if st.session_state.get('campanha_atual_id') == campanha_id:
        st.session_state.campanha_atual_id = None
    
    return True


def get_campanhas_por_cliente(cliente_id: int) -> List[Dict]:
    """Retorna campanhas de um cliente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM campanhas WHERE cliente_id = ? ORDER BY id DESC', (cliente_id,))
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        camp = dict(row)
        camp['is_aon'] = bool(camp['is_aon'])
        camp['metricas_selecionadas'] = json.loads(camp['metricas_selecionadas']) if camp['metricas_selecionadas'] else {}
        camp['insights_config'] = json.loads(camp['insights_config']) if camp['insights_config'] else {}
        camp['categorias_comentarios'] = json.loads(camp['categorias_comentarios']) if camp['categorias_comentarios'] else []
        camp['influenciadores'] = json.loads(camp['influenciadores']) if camp['influenciadores'] else []
        result.append(camp)
    
    return result


# ========================================
# INFLUENCIADORES NA CAMPANHA
# ========================================

def adicionar_influenciador_campanha(campanha_id: int, influenciador_id: int) -> bool:
    """Adiciona influenciador a uma campanha"""
    campanha = get_campanha(campanha_id)
    if not campanha:
        return False
    
    influenciador = get_influenciador(influenciador_id)
    if not influenciador:
        return False
    
    # Verificar se ja existe
    for inf in campanha['influenciadores']:
        if inf['influenciador_id'] == influenciador_id:
            return False
    
    # Criar snapshot
    snapshot = {
        'seguidores': influenciador.get('seguidores', 0),
        'engagement_rate': influenciador.get('engagement_rate', 0),
        'air_score': influenciador.get('air_score', 0),
        'classificacao': influenciador.get('classificacao', '')
    }
    
    campanha['influenciadores'].append({
        'influenciador_id': influenciador_id,
        'snapshot_dados': snapshot,
        'posts': []
    })
    
    atualizar_campanha(campanha_id, {'influenciadores': campanha['influenciadores']})
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
    
    atualizar_campanha(campanha_id, {'influenciadores': campanha['influenciadores']})
    return True


def get_influenciadores_campanha(campanha_id: int) -> List[Dict]:
    """Retorna influenciadores de uma campanha com dados completos"""
    campanha = get_campanha(campanha_id)
    if not campanha:
        return []
    
    resultado = []
    for camp_inf in campanha['influenciadores']:
        influenciador = get_influenciador(camp_inf['influenciador_id'])
        if influenciador:
            resultado.append({
                **influenciador,
                'snapshot_dados': camp_inf['snapshot_dados'],
                'posts': camp_inf['posts']
            })
    
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
            atualizar_campanha(campanha_id, {'influenciadores': campanha['influenciadores']})
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
                    atualizar_campanha(campanha_id, {'influenciadores': campanha['influenciadores']})
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
            atualizar_campanha(campanha_id, {'influenciadores': campanha['influenciadores']})
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
                    atualizar_campanha(campanha_id, {'influenciadores': campanha['influenciadores']})
                    return True
    return False


# ========================================
# METRICAS E CALCULOS
# ========================================

def calcular_metricas_campanha(campanha: Dict) -> Dict:
    """Calcula todas as metricas de uma campanha"""
    totais = {
        'total_influenciadores': len(campanha.get('influenciadores', [])),
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
    
    for camp_inf in campanha.get('influenciadores', []):
        inf = get_influenciador(camp_inf['influenciador_id'])
        if inf:
            if campanha.get('tipo_dados') == 'estatico':
                totais['total_seguidores'] += camp_inf.get('snapshot_dados', {}).get('seguidores', 0)
            else:
                totais['total_seguidores'] += inf.get('seguidores', 0)
        
        for post in camp_inf.get('posts', []):
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
        
        for inf in camp.get('influenciadores', []):
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
