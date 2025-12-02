"""
Data Manager - Gerenciamento de dados com SQLite local
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional
import json
import sqlite3
import os

# Caminho do banco de dados
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'air_relatorios.db')


def parse_data_flexivel(data_str: str) -> datetime:
    """Parseia data em varios formatos possiveis"""
    if not data_str:
        return datetime.now()
    
    formatos = [
        '%Y-%m-%d',      # 2025-12-02
        '%d/%m/%Y',      # 02/12/2025
        '%d-%m-%Y',      # 02-12-2025
        '%Y/%m/%d',      # 2025/12/02
        '%d.%m.%Y',      # 02.12.2025
    ]
    
    for fmt in formatos:
        try:
            return datetime.strptime(data_str, fmt)
        except ValueError:
            continue
    
    # Se nenhum formato funcionar, retorna data atual
    return datetime.now()


def get_connection():
    """Retorna conexao SQLite"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa as tabelas do banco de dados"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela de clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj TEXT,
            contato TEXT,
            email TEXT,
            classificacao_cliente TEXT DEFAULT 'padrao',
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
            nicho TEXT,
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
            estimativa_alcance INTEGER DEFAULT 0,
            estimativa_impressoes INTEGER DEFAULT 0,
            investimento_total REAL DEFAULT 0,
            created_at TEXT
        )
    ''')
    
    # Tabela de configuracoes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT UNIQUE NOT NULL,
            valor TEXT
        )
    ''')
    
    conn.commit()
    conn.close()


# ========================================
# INICIALIZACAO
# ========================================

def inicializar_session_state():
    """Inicializa variaveis do session state"""
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


def get_faixas_classificacao() -> Dict:
    """Retorna faixas de classificacao de influenciadores"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracoes WHERE chave = 'faixas_classificacao'")
    row = cursor.fetchone()
    conn.close()
    
    if row and row['valor']:
        try:
            return json.loads(row['valor'])
        except:
            pass
    
    # Valores padrao conforme tabela AIR
    return {
        'nano': {'min': 1000, 'max': 10000},
        'micro': {'min': 10000, 'max': 50000},
        'inter1': {'min': 50000, 'max': 250000},
        'inter2': {'min': 250000, 'max': 500000},
        'macro': {'min': 500000, 'max': 1000000},
        'mega1': {'min': 1000000, 'max': 5000000},
        'mega2': {'min': 5000000, 'max': 10000000},
        'supermega': {'min': 10000000, 'max': 999999999}
    }


def salvar_faixas_classificacao(faixas: Dict) -> bool:
    """Salva faixas de classificacao"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO configuracoes (chave, valor)
        VALUES ('faixas_classificacao', ?)
    ''', (json.dumps(faixas),))
    conn.commit()
    conn.close()
    return True


def classificar_influenciador(seguidores: int) -> str:
    """Classifica influenciador por numero de seguidores usando faixas configuradas"""
    faixas = get_faixas_classificacao()
    
    if seguidores < faixas['nano']['max']:
        return 'Nano'
    elif seguidores < faixas['micro']['max']:
        return 'Micro'
    elif seguidores < faixas['inter1']['max']:
        return 'Inter 1'
    elif seguidores < faixas['inter2']['max']:
        return 'Inter 2'
    elif seguidores < faixas['macro']['max']:
        return 'Macro'
    elif seguidores < faixas['mega1']['max']:
        return 'Mega 1'
    elif seguidores < faixas['mega2']['max']:
        return 'Mega 2'
    else:
        return 'Super Mega'


def calcular_classificacao(seguidores: int) -> str:
    """Alias para classificar_influenciador"""
    return classificar_influenciador(seguidores)


# ========================================
# CLIENTES
# ========================================

def criar_cliente(dados: Dict) -> Dict:
    """Cria novo cliente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO clientes (nome, cnpj, contato, email, classificacao_cliente, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        dados['nome'],
        dados.get('cnpj', ''),
        dados.get('contato', ''),
        dados.get('email', ''),
        dados.get('classificacao_cliente', 'padrao'),
        datetime.now().isoformat()
    ))
    
    cliente_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {'id': cliente_id, **dados}


def get_cliente(cliente_id: int) -> Optional[Dict]:
    """Busca cliente por ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_clientes() -> List[Dict]:
    """Retorna todos os clientes"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes ORDER BY nome")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def atualizar_cliente(cliente_id: int, dados: Dict) -> bool:
    """Atualiza dados de um cliente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE clientes SET nome = ?, cnpj = ?, contato = ?, email = ?, classificacao_cliente = ?
        WHERE id = ?
    ''', (
        dados.get('nome', ''),
        dados.get('cnpj', ''),
        dados.get('contato', ''),
        dados.get('email', ''),
        dados.get('classificacao_cliente', 'padrao'),
        cliente_id
    ))
    
    conn.commit()
    conn.close()
    return True


def excluir_cliente(cliente_id: int) -> bool:
    """Exclui um cliente"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()
    return True


# ========================================
# INFLUENCIADORES
# ========================================

def criar_influenciador(dados: Dict) -> Dict:
    """Cria influenciador na base"""
    conn = get_connection()
    cursor = conn.cursor()
    
    classificacao = classificar_influenciador(dados.get('seguidores', 0))
    now = datetime.now().isoformat()
    
    means_json = json.dumps(dados.get('means', {})) if dados.get('means') else '{}'
    hashtags_json = json.dumps(dados.get('hashtags', [])) if dados.get('hashtags') else '[]'
    
    cursor.execute('''
        INSERT INTO influenciadores (
            profile_id, nome, usuario, network, seguidores, foto, bio,
            engagement_rate, air_score, reach_rate, means, hashtags,
            classificacao, nicho, total_posts, total_likes, total_views,
            total_comments, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        means_json,
        hashtags_json,
        classificacao,
        dados.get('nicho', ''),
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


def get_influenciador(inf_id: int) -> Optional[Dict]:
    """Busca influenciador por ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM influenciadores WHERE id = ?", (inf_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        inf = dict(row)
        if inf.get('means'):
            try:
                inf['means'] = json.loads(inf['means'])
            except:
                inf['means'] = {}
        if inf.get('hashtags'):
            try:
                inf['hashtags'] = json.loads(inf['hashtags'])
            except:
                inf['hashtags'] = []
        return inf
    return None


def get_influenciador_por_usuario(usuario: str) -> Optional[Dict]:
    """Busca influenciador por username"""
    conn = get_connection()
    cursor = conn.cursor()
    
    usuario_limpo = usuario.replace('@', '').strip().lower()
    cursor.execute("SELECT * FROM influenciadores WHERE LOWER(usuario) = ?", (usuario_limpo,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        inf = dict(row)
        if inf.get('means'):
            try:
                inf['means'] = json.loads(inf['means'])
            except:
                inf['means'] = {}
        if inf.get('hashtags'):
            try:
                inf['hashtags'] = json.loads(inf['hashtags'])
            except:
                inf['hashtags'] = []
        return inf
    return None


def get_influenciadores() -> List[Dict]:
    """Retorna todos os influenciadores"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM influenciadores ORDER BY nome")
    rows = cursor.fetchall()
    conn.close()
    
    influenciadores = []
    for row in rows:
        inf = dict(row)
        if inf.get('means'):
            try:
                inf['means'] = json.loads(inf['means'])
            except:
                inf['means'] = {}
        if inf.get('hashtags'):
            try:
                inf['hashtags'] = json.loads(inf['hashtags'])
            except:
                inf['hashtags'] = []
        influenciadores.append(inf)
    
    return influenciadores


def atualizar_influenciador(inf_id: int, dados: Dict) -> bool:
    """Atualiza dados de um influenciador"""
    conn = get_connection()
    cursor = conn.cursor()
    
    classificacao = classificar_influenciador(dados.get('seguidores', 0))
    now = datetime.now().isoformat()
    
    means_json = json.dumps(dados.get('means', {})) if dados.get('means') else '{}'
    hashtags_json = json.dumps(dados.get('hashtags', [])) if dados.get('hashtags') else '[]'
    
    cursor.execute('''
        UPDATE influenciadores SET
            profile_id = ?, nome = ?, usuario = ?, network = ?, seguidores = ?,
            foto = ?, bio = ?, engagement_rate = ?, air_score = ?, reach_rate = ?,
            means = ?, hashtags = ?, classificacao = ?, nicho = ?,
            total_posts = ?, total_likes = ?, total_views = ?, total_comments = ?,
            updated_at = ?
        WHERE id = ?
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
        means_json,
        hashtags_json,
        classificacao,
        dados.get('nicho', ''),
        dados.get('total_posts', 0),
        dados.get('total_likes', 0),
        dados.get('total_views', 0),
        dados.get('total_comments', 0),
        now,
        inf_id
    ))
    
    conn.commit()
    conn.close()
    return True


def excluir_influenciador(inf_id: int) -> bool:
    """Exclui um influenciador"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM influenciadores WHERE id = ?", (inf_id,))
    conn.commit()
    conn.close()
    return True


# ========================================
# CAMPANHAS
# ========================================

def criar_campanha(dados: Dict) -> Dict:
    """Cria nova campanha"""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    metricas_json = json.dumps(dados.get('metricas_selecionadas', []))
    insights_json = json.dumps(dados.get('insights_config', {}))
    categorias_json = json.dumps(dados.get('categorias_comentarios', []))
    influenciadores_json = json.dumps(dados.get('influenciadores', []))
    
    cursor.execute('''
        INSERT INTO campanhas (
            nome, cliente_id, cliente_nome, objetivo, data_inicio, data_fim,
            tipo_dados, is_aon, status, metricas_selecionadas, insights_config,
            categorias_comentarios, notas, influenciadores, estimativa_alcance,
            estimativa_impressoes, investimento_total, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        dados.get('nome', ''),
        dados.get('cliente_id'),
        dados.get('cliente_nome', ''),
        dados.get('objetivo', ''),
        dados.get('data_inicio', ''),
        dados.get('data_fim', ''),
        dados.get('tipo_dados', 'estatico'),
        1 if dados.get('is_aon') else 0,
        dados.get('status', 'ativa'),
        metricas_json,
        insights_json,
        categorias_json,
        dados.get('notas', ''),
        influenciadores_json,
        dados.get('estimativa_alcance', 0),
        dados.get('estimativa_impressoes', 0),
        dados.get('investimento_total', 0),
        now
    ))
    
    camp_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {'id': camp_id, **dados}


def get_campanha(camp_id: int) -> Optional[Dict]:
    """Busca campanha por ID"""
    if not camp_id:
        return None
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campanhas WHERE id = ?", (camp_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        camp = dict(row)
        # Parse JSON fields
        for field in ['metricas_selecionadas', 'insights_config', 'categorias_comentarios', 'influenciadores']:
            if camp.get(field):
                try:
                    camp[field] = json.loads(camp[field])
                except:
                    camp[field] = [] if field != 'insights_config' else {}
        camp['is_aon'] = bool(camp.get('is_aon'))
        return camp
    return None


def get_campanhas() -> List[Dict]:
    """Retorna todas as campanhas"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campanhas ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    campanhas = []
    for row in rows:
        camp = dict(row)
        for field in ['metricas_selecionadas', 'insights_config', 'categorias_comentarios', 'influenciadores']:
            if camp.get(field):
                try:
                    camp[field] = json.loads(camp[field])
                except:
                    camp[field] = [] if field != 'insights_config' else {}
        camp['is_aon'] = bool(camp.get('is_aon'))
        campanhas.append(camp)
    
    return campanhas


def get_campanhas_por_cliente(cliente_id: int) -> List[Dict]:
    """Retorna campanhas de um cliente"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campanhas WHERE cliente_id = ? ORDER BY created_at DESC", (cliente_id,))
    rows = cursor.fetchall()
    conn.close()
    
    campanhas = []
    for row in rows:
        camp = dict(row)
        if camp.get('influenciadores'):
            try:
                camp['influenciadores'] = json.loads(camp['influenciadores'])
            except:
                camp['influenciadores'] = []
        camp['is_aon'] = bool(camp.get('is_aon'))
        campanhas.append(camp)
    
    return campanhas


def atualizar_campanha(camp_id: int, dados: Dict) -> bool:
    """Atualiza dados de uma campanha"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Buscar campanha atual para merge
    campanha_atual = get_campanha(camp_id)
    if not campanha_atual:
        return False
    
    # Merge dados
    for key, value in dados.items():
        campanha_atual[key] = value
    
    metricas_json = json.dumps(campanha_atual.get('metricas_selecionadas', []))
    insights_json = json.dumps(campanha_atual.get('insights_config', {}))
    categorias_json = json.dumps(campanha_atual.get('categorias_comentarios', []))
    influenciadores_json = json.dumps(campanha_atual.get('influenciadores', []))
    
    cursor.execute('''
        UPDATE campanhas SET
            nome = ?, cliente_id = ?, cliente_nome = ?, objetivo = ?,
            data_inicio = ?, data_fim = ?, tipo_dados = ?, is_aon = ?,
            status = ?, metricas_selecionadas = ?, insights_config = ?,
            categorias_comentarios = ?, notas = ?, influenciadores = ?,
            estimativa_alcance = ?, estimativa_impressoes = ?, investimento_total = ?
        WHERE id = ?
    ''', (
        campanha_atual.get('nome', ''),
        campanha_atual.get('cliente_id'),
        campanha_atual.get('cliente_nome', ''),
        campanha_atual.get('objetivo', ''),
        campanha_atual.get('data_inicio', ''),
        campanha_atual.get('data_fim', ''),
        campanha_atual.get('tipo_dados', 'estatico'),
        1 if campanha_atual.get('is_aon') else 0,
        campanha_atual.get('status', 'ativa'),
        metricas_json,
        insights_json,
        categorias_json,
        campanha_atual.get('notas', ''),
        influenciadores_json,
        campanha_atual.get('estimativa_alcance', 0),
        campanha_atual.get('estimativa_impressoes', 0),
        campanha_atual.get('investimento_total', 0),
        camp_id
    ))
    
    conn.commit()
    conn.close()
    return True


def excluir_campanha(camp_id: int) -> bool:
    """Exclui uma campanha"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM campanhas WHERE id = ?", (camp_id,))
    conn.commit()
    conn.close()
    return True


# ========================================
# INFLUENCIADORES NA CAMPANHA
# ========================================

def adicionar_influenciador_campanha(camp_id: int, inf_id: int, custo: float = 0) -> bool:
    """Adiciona influenciador a uma campanha com custo"""
    campanha = get_campanha(camp_id)
    if not campanha:
        return False
    
    influenciador = get_influenciador(inf_id)
    if not influenciador:
        return False
    
    influenciadores = campanha.get('influenciadores', [])
    
    # Verificar se ja existe
    for inf in influenciadores:
        if inf.get('influenciador_id') == inf_id:
            return False
    
    # Adicionar com custo
    novo_inf = {
        'influenciador_id': inf_id,
        'nome': influenciador.get('nome', ''),
        'usuario': influenciador.get('usuario', ''),
        'foto': influenciador.get('foto', ''),
        'seguidores': influenciador.get('seguidores', 0),
        'custo': custo,  # Custo atrelado ao influenciador na campanha
        'posts': []
    }
    
    influenciadores.append(novo_inf)
    
    campanha['influenciadores'] = influenciadores
    return atualizar_campanha(camp_id, campanha)


def atualizar_custo_influenciador_campanha(camp_id: int, inf_id: int, custo: float) -> bool:
    """Atualiza custo de um influenciador na campanha"""
    campanha = get_campanha(camp_id)
    if not campanha:
        return False
    
    influenciadores = campanha.get('influenciadores', [])
    
    for i, inf in enumerate(influenciadores):
        if inf.get('influenciador_id') == inf_id:
            influenciadores[i]['custo'] = custo
            break
    
    campanha['influenciadores'] = influenciadores
    return atualizar_campanha(camp_id, campanha)


def remover_influenciador_campanha(camp_id: int, inf_id: int) -> bool:
    """Remove influenciador de uma campanha"""
    campanha = get_campanha(camp_id)
    if not campanha:
        return False
    
    influenciadores = campanha.get('influenciadores', [])
    influenciadores = [inf for inf in influenciadores if inf.get('influenciador_id') != inf_id]
    
    campanha['influenciadores'] = influenciadores
    return atualizar_campanha(camp_id, campanha)


def get_influenciador_campanha(camp_id: int, inf_id: int) -> Optional[Dict]:
    """Retorna dados de um influenciador especifico na campanha"""
    campanha = get_campanha(camp_id)
    if not campanha:
        return None
    
    for inf in campanha.get('influenciadores', []):
        if inf.get('influenciador_id') == inf_id:
            return inf
    
    return None


def get_influenciadores_campanha(camp_id: int) -> List[Dict]:
    """Retorna lista de influenciadores da campanha com dados completos"""
    campanha = get_campanha(camp_id)
    if not campanha:
        return []
    
    resultado = []
    
    for inf_camp in campanha.get('influenciadores', []):
        inf_id = inf_camp.get('influenciador_id')
        inf = get_influenciador(inf_id)
        
        if inf:
            # Mesclar dados do influenciador com dados da campanha
            inf_completo = {
                'id': inf_id,
                'nome': inf.get('nome', inf_camp.get('nome', '')),
                'usuario': inf.get('usuario', inf_camp.get('usuario', '')),
                'foto': inf.get('foto', inf_camp.get('foto', '')),
                'network': inf.get('network', 'instagram'),
                'seguidores': inf.get('seguidores', inf_camp.get('seguidores', 0)),
                'engagement_rate': inf.get('engagement_rate', 0),
                'air_score': inf.get('air_score', 0),
                'classificacao': inf.get('classificacao', 'Desconhecido'),
                'nicho': inf.get('nicho', ''),
                'profile_id': inf.get('profile_id', ''),
                # Dados especificos da campanha
                'custo_campanha': inf_camp.get('custo', 0),
                'posts': inf_camp.get('posts', []),
                'snapshot_dados': inf_camp.get('snapshot_dados', {})
            }
            resultado.append(inf_completo)
    
    return resultado


# ========================================
# POSTS
# ========================================

def adicionar_post(camp_id: int, inf_id: int, post_data: Dict) -> bool:
    """Adiciona post a um influenciador na campanha"""
    campanha = get_campanha(camp_id)
    if not campanha:
        return False
    
    influenciadores = campanha.get('influenciadores', [])
    
    for i, inf in enumerate(influenciadores):
        if inf.get('influenciador_id') == inf_id:
            if 'posts' not in inf:
                inf['posts'] = []
            
            # Gerar ID para o post
            post_data['id'] = len(inf['posts']) + 1
            post_data['created_at'] = datetime.now().isoformat()
            
            inf['posts'].append(post_data)
            influenciadores[i] = inf
            break
    
    campanha['influenciadores'] = influenciadores
    return atualizar_campanha(camp_id, campanha)


def atualizar_post(camp_id: int, inf_id: int, post_id: int, post_data: Dict) -> bool:
    """Atualiza um post existente"""
    campanha = get_campanha(camp_id)
    if not campanha:
        return False
    
    influenciadores = campanha.get('influenciadores', [])
    
    for i, inf in enumerate(influenciadores):
        if inf.get('influenciador_id') == inf_id:
            posts = inf.get('posts', [])
            for j, post in enumerate(posts):
                if post.get('id') == post_id:
                    post_data['id'] = post_id
                    post_data['updated_at'] = datetime.now().isoformat()
                    posts[j] = post_data
                    break
            inf['posts'] = posts
            influenciadores[i] = inf
            break
    
    campanha['influenciadores'] = influenciadores
    return atualizar_campanha(camp_id, campanha)


def excluir_post(camp_id: int, inf_id: int, post_id: int) -> bool:
    """Exclui um post"""
    campanha = get_campanha(camp_id)
    if not campanha:
        return False
    
    influenciadores = campanha.get('influenciadores', [])
    
    for i, inf in enumerate(influenciadores):
        if inf.get('influenciador_id') == inf_id:
            posts = inf.get('posts', [])
            posts = [p for p in posts if p.get('id') != post_id]
            inf['posts'] = posts
            influenciadores[i] = inf
            break
    
    campanha['influenciadores'] = influenciadores
    return atualizar_campanha(camp_id, campanha)


def get_posts_influenciador(camp_id: int, inf_id: int) -> List[Dict]:
    """Retorna todos os posts de um influenciador na campanha"""
    inf_camp = get_influenciador_campanha(camp_id, inf_id)
    if inf_camp:
        return inf_camp.get('posts', [])
    return []


# ========================================
# METRICAS
# ========================================

def calcular_metricas_campanha(campanha: Dict) -> Dict:
    """Calcula metricas agregadas de uma campanha"""
    
    total_influenciadores = 0
    total_seguidores = 0
    total_posts = 0
    total_views = 0
    total_alcance = 0
    total_interacoes = 0
    total_impressoes = 0
    total_curtidas = 0
    total_comentarios = 0
    total_compartilhamentos = 0
    total_saves = 0
    total_cliques_link = 0
    total_conversoes = 0
    total_custo = 0
    
    influenciadores = campanha.get('influenciadores', [])
    total_influenciadores = len(influenciadores)
    
    for inf_camp in influenciadores:
        inf = get_influenciador(inf_camp.get('influenciador_id'))
        if inf:
            total_seguidores += inf.get('seguidores', 0)
        
        # Custo do influenciador na campanha
        total_custo += inf_camp.get('custo', 0)
        
        posts = inf_camp.get('posts', [])
        total_posts += len(posts)
        
        for post in posts:
            total_views += post.get('views', 0) or 0
            total_alcance += post.get('alcance', 0) or 0
            total_interacoes += post.get('interacoes', 0) or 0
            total_impressoes += post.get('impressoes', 0) or 0
            total_curtidas += post.get('curtidas', 0) or 0
            # comentarios pode ser lista de objetos ou numero
            comentarios = post.get('comentarios', 0)
            if isinstance(comentarios, list):
                total_comentarios += len(comentarios)
            elif isinstance(comentarios, int):
                total_comentarios += comentarios
            # comentarios_qtd e o campo numerico
            total_comentarios += post.get('comentarios_qtd', 0) or 0
            total_compartilhamentos += post.get('compartilhamentos', 0) or 0
            total_saves += post.get('saves', 0) or 0
            total_cliques_link += post.get('cliques_link', 0) or 0
            total_cliques_link += post.get('clique_link', 0) or 0
            total_conversoes += post.get('conversoes', 0) or 0
            total_conversoes += post.get('cupom_conversoes', 0) or 0
    
    engajamento_efetivo = 0
    taxa_alcance = 0
    
    if total_views > 0:
        engajamento_efetivo = round((total_interacoes / total_views) * 100, 2)
    
    if total_seguidores > 0:
        taxa_alcance = round((total_alcance / total_seguidores) * 100, 2)
    
    return {
        'total_influenciadores': total_influenciadores,
        'total_seguidores': total_seguidores,
        'total_posts': total_posts,
        'total_views': total_views,
        'total_alcance': total_alcance,
        'total_interacoes': total_interacoes,
        'total_impressoes': total_impressoes,
        'total_curtidas': total_curtidas,
        'total_comentarios': total_comentarios,
        'total_compartilhamentos': total_compartilhamentos,
        'total_saves': total_saves,
        'total_cliques_link': total_cliques_link,
        'total_conversoes': total_conversoes,
        'total_custo': total_custo,
        'engajamento_efetivo': engajamento_efetivo,
        'taxa_alcance': taxa_alcance
    }


def calcular_metricas_por_cliente(cliente_id: int) -> Dict:
    """Calcula metricas agregadas de todas as campanhas de um cliente"""
    campanhas = get_campanhas_por_cliente(cliente_id)
    
    if not campanhas:
        return {
            'total_campanhas': 0,
            'total_influenciadores': 0,
            'total_posts': 0,
            'total_views': 0,
            'total_alcance': 0,
            'total_interacoes': 0,
            'engajamento_efetivo': 0
        }
    
    metricas = calcular_metricas_multiplas_campanhas(campanhas)
    metricas['total_campanhas'] = len(campanhas)
    return metricas


def calcular_metricas_multiplas_campanhas(campanhas: List[Dict]) -> Dict:
    """Calcula metricas agregadas de multiplas campanhas"""
    
    total_influenciadores = 0
    total_seguidores = 0
    total_posts = 0
    total_views = 0
    total_alcance = 0
    total_interacoes = 0
    total_impressoes = 0
    total_curtidas = 0
    total_comentarios = 0
    total_compartilhamentos = 0
    total_saves = 0
    total_cliques_link = 0
    total_conversoes = 0
    total_custo = 0
    
    influenciadores_ids = set()
    
    for campanha in campanhas:
        influenciadores = campanha.get('influenciadores', [])
        
        for inf_camp in influenciadores:
            inf_id = inf_camp.get('influenciador_id')
            if inf_id not in influenciadores_ids:
                influenciadores_ids.add(inf_id)
                inf = get_influenciador(inf_id)
                if inf:
                    total_seguidores += inf.get('seguidores', 0)
            
            # Custo do influenciador na campanha
            total_custo += inf_camp.get('custo', 0)
            
            posts = inf_camp.get('posts', [])
            total_posts += len(posts)
            
            for post in posts:
                total_views += post.get('views', 0) or 0
                total_alcance += post.get('alcance', 0) or 0
                total_interacoes += post.get('interacoes', 0) or 0
                total_impressoes += post.get('impressoes', 0) or 0
                total_curtidas += post.get('curtidas', 0) or 0
                # comentarios pode ser lista de objetos ou numero
                comentarios = post.get('comentarios', 0)
                if isinstance(comentarios, list):
                    total_comentarios += len(comentarios)
                elif isinstance(comentarios, int):
                    total_comentarios += comentarios
                total_comentarios += post.get('comentarios_qtd', 0) or 0
                total_compartilhamentos += post.get('compartilhamentos', 0) or 0
                total_saves += post.get('saves', 0) or 0
                total_cliques_link += post.get('cliques_link', 0) or 0
                total_cliques_link += post.get('clique_link', 0) or 0
                total_conversoes += post.get('conversoes', 0) or 0
                total_conversoes += post.get('cupom_conversoes', 0) or 0
    
    total_influenciadores = len(influenciadores_ids)
    
    engajamento_efetivo = 0
    taxa_alcance = 0
    
    if total_views > 0:
        engajamento_efetivo = round((total_interacoes / total_views) * 100, 2)
    
    if total_seguidores > 0:
        taxa_alcance = round((total_alcance / total_seguidores) * 100, 2)
    
    return {
        'total_influenciadores': total_influenciadores,
        'total_seguidores': total_seguidores,
        'total_posts': total_posts,
        'total_views': total_views,
        'total_alcance': total_alcance,
        'total_interacoes': total_interacoes,
        'total_impressoes': total_impressoes,
        'total_curtidas': total_curtidas,
        'total_comentarios': total_comentarios,
        'total_compartilhamentos': total_compartilhamentos,
        'total_saves': total_saves,
        'total_cliques_link': total_cliques_link,
        'total_conversoes': total_conversoes,
        'total_custo': total_custo,
        'engajamento_efetivo': engajamento_efetivo,
        'taxa_alcance': taxa_alcance
    }


def calcular_metricas_influenciador_campanha(campanha: Dict, inf_id: int) -> Dict:
    """Calcula metricas de um influenciador especifico na campanha"""
    
    inf_camp = None
    for inf in campanha.get('influenciadores', []):
        if inf.get('influenciador_id') == inf_id:
            inf_camp = inf
            break
    
    if not inf_camp:
        return {}
    
    inf = get_influenciador(inf_id)
    seguidores = inf.get('seguidores', 0) if inf else 0
    
    total_posts = 0
    total_views = 0
    total_alcance = 0
    total_interacoes = 0
    total_impressoes = 0
    total_curtidas = 0
    total_comentarios = 0
    total_compartilhamentos = 0
    total_saves = 0
    total_cliques_link = 0
    total_conversoes = 0
    
    # Custo do influenciador na campanha
    total_custo = inf_camp.get('custo', 0)
    
    posts = inf_camp.get('posts', [])
    total_posts = len(posts)
    
    for post in posts:
        total_views += post.get('views', 0) or 0
        total_alcance += post.get('alcance', 0) or 0
        total_interacoes += post.get('interacoes', 0) or 0
        total_impressoes += post.get('impressoes', 0) or 0
        total_curtidas += post.get('curtidas', 0) or 0
        # comentarios pode ser lista de objetos ou numero
        comentarios = post.get('comentarios', 0)
        if isinstance(comentarios, list):
            total_comentarios += len(comentarios)
        elif isinstance(comentarios, int):
            total_comentarios += comentarios
        total_comentarios += post.get('comentarios_qtd', 0) or 0
        total_compartilhamentos += post.get('compartilhamentos', 0) or 0
        total_saves += post.get('saves', 0) or 0
        total_cliques_link += post.get('cliques_link', 0) or 0
        total_cliques_link += post.get('clique_link', 0) or 0
        total_conversoes += post.get('conversoes', 0) or 0
        total_conversoes += post.get('cupom_conversoes', 0) or 0
    
    engajamento_efetivo = 0
    taxa_alcance = 0
    
    if total_views > 0:
        engajamento_efetivo = round((total_interacoes / total_views) * 100, 2)
    
    if seguidores > 0:
        taxa_alcance = round((total_alcance / seguidores) * 100, 2)
    
    return {
        'seguidores': seguidores,
        'total_posts': total_posts,
        'total_views': total_views,
        'total_alcance': total_alcance,
        'total_interacoes': total_interacoes,
        'total_impressoes': total_impressoes,
        'total_curtidas': total_curtidas,
        'total_comentarios': total_comentarios,
        'total_compartilhamentos': total_compartilhamentos,
        'total_saves': total_saves,
        'total_cliques_link': total_cliques_link,
        'total_conversoes': total_conversoes,
        'total_custo': total_custo,
        'engajamento_efetivo': engajamento_efetivo,
        'taxa_alcance': taxa_alcance
    }


# ========================================
# CONFIGURACOES
# ========================================

def get_configuracoes() -> Dict:
    """Retorna configuracoes do sistema"""
    return {
        'primary_color': st.session_state.get('primary_color', '#7c3aed'),
        'secondary_color': st.session_state.get('secondary_color', '#fb923c'),
        'logo': st.session_state.get('logo_url', ''),
        'nome_empresa': st.session_state.get('nome_empresa', 'AIR Relatorios')
    }


def salvar_configuracoes(config: Dict) -> bool:
    """Salva configuracoes do sistema"""
    if 'primary_color' in config:
        st.session_state.primary_color = config['primary_color']
    if 'secondary_color' in config:
        st.session_state.secondary_color = config['secondary_color']
    if 'logo' in config:
        st.session_state.logo_url = config['logo']
    if 'nome_empresa' in config:
        st.session_state.nome_empresa = config['nome_empresa']
    return True


# ========================================
# ESTATISTICAS DASHBOARD
# ========================================

def get_estatisticas_dashboard() -> Dict:
    """Retorna estatisticas para o dashboard"""
    clientes = get_clientes()
    influenciadores = get_influenciadores()
    campanhas = get_campanhas()
    
    campanhas_ativas = [c for c in campanhas if c.get('status') == 'ativa']
    
    total_posts = 0
    total_alcance = 0
    
    for camp in campanhas:
        for inf in camp.get('influenciadores', []):
            posts = inf.get('posts', [])
            total_posts += len(posts)
            for post in posts:
                total_alcance += post.get('alcance', 0)
    
    return {
        'total_clientes': len(clientes),
        'total_influenciadores': len(influenciadores),
        'total_campanhas': len(campanhas),
        'campanhas_ativas': len(campanhas_ativas),
        'total_posts': total_posts,
        'total_alcance': total_alcance
    }


# ========================================
# EXPORTACAO CSV BALIZADORES
# ========================================

def exportar_balizadores_csv(campanha: Dict) -> str:
    """Exporta dados agregados por influenciador para CSV com colunas por rede"""
    import io
    import csv
    
    output = io.StringIO()
    
    # Colunas do CSV
    colunas = [
        'Influenciador', 'Usuario', 'Classificacao', 'Nicho',
        # Instagram
        'IG_Base_Seguidores', 'IG_Feed_Impressoes', 'IG_Feed_Alcance',
        'IG_Reels_Impressoes', 'IG_Reels_Alcance', 'IG_Stories_Impressoes', 'IG_Stories_Alcance',
        'IG_Interacoes_Total', 'IG_Engaj_Efetivo',
        # TikTok
        'TK_Base_Seguidores', 'TK_Visualizacoes', 'TK_Alcance', 'TK_Engaj_Total', 'TK_Engaj_Efetivo',
        # YouTube
        'YT_Base_Inscritos', 'YT_Visualizacoes', 'YT_Alcance'
    ]
    
    writer = csv.DictWriter(output, fieldnames=colunas)
    writer.writeheader()
    
    for inf_camp in campanha.get('influenciadores', []):
        inf = get_influenciador(inf_camp.get('influenciador_id'))
        if not inf:
            continue
        
        # Agregar metricas por formato/rede
        metricas = {
            'ig_feed_imp': 0, 'ig_feed_alc': 0,
            'ig_reels_imp': 0, 'ig_reels_alc': 0,
            'ig_stories_imp': 0, 'ig_stories_alc': 0,
            'ig_interacoes': 0, 'ig_views': 0,
            'tk_views': 0, 'tk_alc': 0, 'tk_inter': 0,
            'yt_views': 0, 'yt_alc': 0
        }
        
        for post in inf_camp.get('posts', []):
            formato = post.get('formato', '').lower()
            rede = post.get('rede', inf.get('network', 'instagram')).lower()
            
            if rede == 'instagram' or rede == '':
                if 'feed' in formato or formato == 'post':
                    metricas['ig_feed_imp'] += post.get('impressoes', 0)
                    metricas['ig_feed_alc'] += post.get('alcance', 0)
                elif 'reel' in formato:
                    metricas['ig_reels_imp'] += post.get('impressoes', 0)
                    metricas['ig_reels_alc'] += post.get('alcance', 0)
                elif 'stor' in formato:
                    metricas['ig_stories_imp'] += post.get('impressoes', 0)
                    metricas['ig_stories_alc'] += post.get('alcance', 0)
                else:
                    # Outros formatos IG
                    metricas['ig_reels_imp'] += post.get('impressoes', 0)
                    metricas['ig_reels_alc'] += post.get('alcance', 0)
                
                metricas['ig_interacoes'] += post.get('interacoes', 0)
                metricas['ig_views'] += post.get('views', 0)
            
            elif rede == 'tiktok':
                metricas['tk_views'] += post.get('views', 0)
                metricas['tk_alc'] += post.get('alcance', 0)
                metricas['tk_inter'] += post.get('interacoes', 0)
            
            elif rede == 'youtube':
                metricas['yt_views'] += post.get('views', 0)
                metricas['yt_alc'] += post.get('alcance', 0)
        
        # Calcular engajamento efetivo
        ig_eng_efetivo = round((metricas['ig_interacoes'] / metricas['ig_views'] * 100), 2) if metricas['ig_views'] > 0 else 0
        tk_eng_total = round((metricas['tk_inter'] / inf.get('seguidores', 1) * 100), 2) if inf.get('seguidores', 0) > 0 else 0
        tk_eng_efetivo = round((metricas['tk_inter'] / metricas['tk_alc'] * 100), 2) if metricas['tk_alc'] > 0 else 0
        
        row = {
            'Influenciador': inf.get('nome', ''),
            'Usuario': inf.get('usuario', ''),
            'Classificacao': inf.get('classificacao', ''),
            'Nicho': inf.get('nicho', ''),
            # Instagram
            'IG_Base_Seguidores': inf.get('seguidores', 0) if inf.get('network') == 'instagram' else 0,
            'IG_Feed_Impressoes': metricas['ig_feed_imp'],
            'IG_Feed_Alcance': metricas['ig_feed_alc'],
            'IG_Reels_Impressoes': metricas['ig_reels_imp'],
            'IG_Reels_Alcance': metricas['ig_reels_alc'],
            'IG_Stories_Impressoes': metricas['ig_stories_imp'],
            'IG_Stories_Alcance': metricas['ig_stories_alc'],
            'IG_Interacoes_Total': metricas['ig_interacoes'],
            'IG_Engaj_Efetivo': ig_eng_efetivo,
            # TikTok
            'TK_Base_Seguidores': inf.get('seguidores', 0) if inf.get('network') == 'tiktok' else 0,
            'TK_Visualizacoes': metricas['tk_views'],
            'TK_Alcance': metricas['tk_alc'],
            'TK_Engaj_Total': tk_eng_total,
            'TK_Engaj_Efetivo': tk_eng_efetivo,
            # YouTube
            'YT_Base_Inscritos': inf.get('seguidores', 0) if inf.get('network') == 'youtube' else 0,
            'YT_Visualizacoes': metricas['yt_views'],
            'YT_Alcance': metricas['yt_alc']
        }
        
        writer.writerow(row)
    
    return output.getvalue()
