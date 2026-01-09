"""
Data Manager - Gerenciamento de dados com SQLite local ou PostgreSQL
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import sqlite3
import os
import time

# Verificar se tem DATABASE_URL para PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL', '')

# Se tiver secrets do Streamlit, usar
try:
    if hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
        DATABASE_URL = st.secrets['DATABASE_URL']
except:
    pass

# Caminho do banco SQLite (fallback)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'air_relatorios.db')

# Flag para indicar se estamos usando PostgreSQL
USING_POSTGRES = 'postgresql' in DATABASE_URL.lower() or 'postgres' in DATABASE_URL.lower()


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
    
    return datetime.now()


def get_connection():
    """Retorna conexao com banco de dados"""
    if USING_POSTGRES:
        # Usar session_state para manter conexao durante a sessao
        if 'db_conn' not in st.session_state or st.session_state.db_conn is None:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            st.session_state.db_conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        
        # Verificar se conexao ainda esta valida
        try:
            cur = st.session_state.db_conn.cursor()
            cur.execute('SELECT 1')
            cur.fetchone()
            return st.session_state.db_conn
        except:
            # Reconectar
            import psycopg2
            from psycopg2.extras import RealDictCursor
            try:
                st.session_state.db_conn.close()
            except:
                pass
            st.session_state.db_conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            return st.session_state.db_conn
    else:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn


def invalidar_cache():
    """Invalida cache de dados para forcar reload"""
    if '_cache_clientes' in st.session_state:
        del st.session_state._cache_clientes
    if '_cache_influenciadores' in st.session_state:
        del st.session_state._cache_influenciadores
    if '_cache_campanhas' in st.session_state:
        del st.session_state._cache_campanhas


def diagnostico_db():
    """Mostra diagnostico de conexao com banco"""
    st.subheader("🔍 Diagnostico de Banco de Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Tipo:** {'PostgreSQL' if USING_POSTGRES else 'SQLite'}")
        if USING_POSTGRES:
            try:
                host = DATABASE_URL.split('@')[1].split('/')[0]
                st.write(f"**Host:** {host}")
            except:
                st.write("**Host:** (não identificado)")
    
    with col2:
        if st.button("🧪 Testar Conexao Atual"):
            tempos = []
            
            for i in range(5):
                start = time.time()
                try:
                    if USING_POSTGRES:
                        import psycopg2
                        from psycopg2.extras import RealDictCursor
                        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
                        cursor = conn.cursor()
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                        conn.close()
                    else:
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                        conn.close()
                    
                    elapsed = time.time() - start
                    tempos.append(elapsed)
                    st.write(f"Teste {i+1}: {elapsed:.3f}s ✅")
                except Exception as e:
                    st.write(f"Teste {i+1}: ERRO - {e}")
            
            if tempos:
                media = sum(tempos) / len(tempos)
                st.success(f"**Media: {media:.3f}s** | Min: {min(tempos):.3f}s | Max: {max(tempos):.3f}s")
                
                if media > 0.5:
                    st.warning("⚠️ Conexao lenta! Servidor do banco esta longe do Streamlit Cloud.")
                elif media > 0.2:
                    st.info("ℹ️ Conexao moderada.")
                else:
                    st.success("✅ Conexao rapida!")
    
    # Teste de URL customizada
    st.markdown("---")
    st.subheader("🧪 Testar Outra URL")
    st.caption("Use para comparar diferentes provedores/regioes")
    
    test_url = st.text_input("DATABASE_URL para testar:", type="password", key="test_db_url")
    
    if st.button("Testar URL", disabled=not test_url):
        if test_url:
            tempos = []
            try:
                host = test_url.split('@')[1].split('/')[0]
                st.write(f"**Testando:** {host}")
            except:
                pass
            
            for i in range(3):
                start = time.time()
                try:
                    import psycopg2
                    from psycopg2.extras import RealDictCursor
                    conn = psycopg2.connect(test_url, cursor_factory=RealDictCursor)
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    conn.close()
                    
                    elapsed = time.time() - start
                    tempos.append(elapsed)
                    st.write(f"Teste {i+1}: {elapsed:.3f}s ✅")
                except Exception as e:
                    st.error(f"Teste {i+1}: ERRO - {e}")
            
            if tempos:
                media = sum(tempos) / len(tempos)
                if media < 0.2:
                    st.success(f"🚀 **Excelente! Media: {media:.3f}s** - Use esta URL!")
                elif media < 0.5:
                    st.success(f"✅ **Boa! Media: {media:.3f}s**")
                else:
                    st.warning(f"⚠️ **Lenta: Media: {media:.3f}s** - Tente outra regiao")


def execute_query(query: str, params: tuple = (), fetch: bool = False):
    """Executa query adaptando para PostgreSQL ou SQLite"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Adaptar query para PostgreSQL (usa %s ao inves de ?)
    if USING_POSTGRES:
        query = query.replace('?', '%s')
        query = query.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
    
    try:
        cursor.execute(query, params)
        
        if fetch:
            result = cursor.fetchall()
            if not USING_POSTGRES:
                conn.close()
            return result
        else:
            conn.commit()
            
            # Pegar ultimo ID inserido
            if 'INSERT' in query.upper():
                if USING_POSTGRES:
                    cursor.execute("SELECT lastval()")
                    last_id = cursor.fetchone()
                    return last_id[0] if last_id else None
                else:
                    last_id = cursor.lastrowid
                    conn.close()
                    return last_id
            
            if not USING_POSTGRES:
                conn.close()
            return True
    except Exception as e:
        if not USING_POSTGRES:
            conn.close()
        raise e


def execute_sql(query: str, params: tuple = ()):
    """Executa SQL adaptando placeholders"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if USING_POSTGRES:
        query = query.replace('?', '%s')
    
    cursor.execute(query, params)
    return cursor, conn


def execute_insert(query: str, params: tuple = ()):
    """Executa INSERT e retorna o ID inserido"""
    cursor, conn = execute_sql(query, params)
    conn.commit()
    
    if USING_POSTGRES:
        cursor.execute("SELECT lastval()")
        result = cursor.fetchone()
        if result:
            last_id = result.get('lastval') if isinstance(result, dict) else result[0]
        else:
            last_id = None
        # Nao fechar - conexao fica em session_state
    else:
        last_id = cursor.lastrowid
        conn.close()
    
    return last_id


def execute_select(query: str, params: tuple = ()):
    """Executa SELECT e retorna todas as linhas"""
    cursor, conn = execute_sql(query, params)
    rows = cursor.fetchall()
    if not USING_POSTGRES:
        conn.close()
    return rows


def execute_select_one(query: str, params: tuple = ()):
    """Executa SELECT e retorna uma linha"""
    cursor, conn = execute_sql(query, params)
    row = cursor.fetchone()
    if not USING_POSTGRES:
        conn.close()
    return row


def execute_update(query: str, params: tuple = ()):
    """Executa UPDATE/DELETE"""
    cursor, conn = execute_sql(query, params)
    conn.commit()
    if not USING_POSTGRES:
        conn.close()
    return True


def init_db():
    """Inicializa as tabelas do banco de dados"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Definir tipo de primary key baseado no banco
    if USING_POSTGRES:
        pk_type = "SERIAL PRIMARY KEY"
        int_type = "INTEGER"
        text_type = "TEXT"
        real_type = "REAL"
    else:
        pk_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
        int_type = "INTEGER"
        text_type = "TEXT"
        real_type = "REAL"
    
    # Tabela de clientes
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS clientes (
            id {pk_type},
            nome {text_type} NOT NULL,
            cnpj {text_type},
            contato {text_type},
            email {text_type},
            classificacao_cliente {text_type} DEFAULT 'padrao',
            created_at {text_type}
        )
    ''')
    
    # Tabela de influenciadores
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS influenciadores (
            id {pk_type},
            profile_id {text_type},
            nome {text_type} NOT NULL,
            usuario {text_type} NOT NULL,
            network {text_type},
            seguidores {int_type} DEFAULT 0,
            foto {text_type},
            bio {text_type},
            engagement_rate {real_type} DEFAULT 0,
            air_score {real_type} DEFAULT 0,
            reach_rate {real_type} DEFAULT 0,
            means {text_type},
            hashtags {text_type},
            classificacao {text_type},
            nicho {text_type},
            total_posts {int_type} DEFAULT 0,
            total_likes {int_type} DEFAULT 0,
            total_views {int_type} DEFAULT 0,
            total_comments {int_type} DEFAULT 0,
            vinculo_id {int_type},
            created_at {text_type},
            updated_at {text_type}
        )
    ''')
    
    # Tabela de campanhas
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS campanhas (
            id {pk_type},
            nome {text_type} NOT NULL,
            cliente_id {int_type},
            cliente_nome {text_type},
            objetivo {text_type},
            data_inicio {text_type},
            data_fim {text_type},
            tipo_dados {text_type} DEFAULT 'estatico',
            is_aon {int_type} DEFAULT 0,
            status {text_type} DEFAULT 'ativa',
            metricas_selecionadas {text_type},
            insights_config {text_type},
            categorias_comentarios {text_type},
            notas {text_type},
            influenciadores {text_type},
            estimativa_alcance {int_type} DEFAULT 0,
            estimativa_impressoes {int_type} DEFAULT 0,
            investimento_total {real_type} DEFAULT 0,
            created_at {text_type}
        )
    ''')
    
    # Tabela de configuracoes
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS configuracoes (
            id {pk_type},
            chave {text_type} UNIQUE NOT NULL,
            valor {text_type}
        )
    ''')
    
    # Tabela de insights de campanha
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS insights_campanha (
            id {pk_type},
            campanha_id {int_type} NOT NULL,
            pagina {text_type} NOT NULL,
            tipo {text_type} DEFAULT 'info',
            icone {text_type} DEFAULT '💡',
            titulo {text_type} NOT NULL,
            texto {text_type} NOT NULL,
            fonte {text_type} DEFAULT 'ia',
            ordem {int_type} DEFAULT 0,
            ativo {int_type} DEFAULT 1,
            created_at {text_type},
            updated_at {text_type}
        )
    ''')
    
    # Tabela de historico de insights (para manter versoes anteriores)
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS insights_historico (
            id {pk_type},
            campanha_id {int_type} NOT NULL,
            pagina {text_type} NOT NULL,
            insights_json {text_type},
            created_at {text_type}
        )
    ''')
    
    # Tabela de tokens para compartilhamento de relatorios
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS tokens_compartilhamento (
            id {pk_type},
            token {text_type} UNIQUE NOT NULL,
            campanha_id {int_type} NOT NULL,
            cliente_id {int_type},
            titulo {text_type},
            paginas_permitidas {text_type},
            expira_em {text_type},
            visualizacoes {int_type} DEFAULT 0,
            max_visualizacoes {int_type},
            ativo {int_type} DEFAULT 1,
            created_at {text_type},
            updated_at {text_type}
        )
    ''')
    
    # Tabela de comentarios extraidos e classificados
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS comentarios_posts (
            id {pk_type},
            campanha_id {int_type} NOT NULL,
            influenciador_id {int_type},
            post_url {text_type},
            post_shortcode {text_type},
            comment_id {text_type},
            usuario {text_type},
            texto {text_type},
            data_comentario {text_type},
            likes {int_type} DEFAULT 0,
            categoria {text_type},
            sentimento {text_type},
            confianca {real_type} DEFAULT 0,
            justificativa {text_type},
            classificado {int_type} DEFAULT 0,
            created_at {text_type}
        )
    ''')
    
    conn.commit()
    
    # Só fecha conexão se for SQLite (PostgreSQL usa conexão compartilhada)
    if not USING_POSTGRES:
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
        # Carregar cor salva do banco
        cor_salva = get_configuracao('primary_color')
        st.session_state.primary_color = cor_salva if cor_salva else '#7c3aed'
    if 'modo_relatorio' not in st.session_state:
        st.session_state.modo_relatorio = 'campanha'
    if 'relatorio_cliente_id' not in st.session_state:
        st.session_state.relatorio_cliente_id = None
    if 'relatorio_campanhas_ids' not in st.session_state:
        st.session_state.relatorio_campanhas_ids = []


def get_configuracao(chave: str) -> str:
    """Retorna valor de uma configuracao"""
    try:
        row = execute_select_one("SELECT valor FROM configuracoes WHERE chave = ?", (chave,))
        return row.get('valor') if row else None
    except:
        return None


def salvar_configuracao(chave: str, valor: str) -> bool:
    """Salva uma configuracao no banco"""
    try:
        # Verificar se ja existe
        existente = get_configuracao(chave)
        if existente is not None:
            execute_update("UPDATE configuracoes SET valor = ? WHERE chave = ?", (valor, chave))
        else:
            execute_insert("INSERT INTO configuracoes (chave, valor) VALUES (?, ?)", (chave, valor))
        return True
    except:
        return False


def get_faixas_classificacao() -> Dict:
    """Retorna faixas de classificacao de influenciadores"""
    row = execute_select_one("SELECT valor FROM configuracoes WHERE chave = 'faixas_classificacao'")
    
    if row and row.get('valor'):
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
    if USING_POSTGRES:
        cursor, conn = execute_sql('''
            INSERT INTO configuracoes (chave, valor)
            VALUES (?, ?)
            ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor
        ''', ('faixas_classificacao', json.dumps(faixas)))
        conn.commit()
        # Nao fechar - conexao fica em session_state
    else:
        cursor, conn = execute_sql('''
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
    invalidar_cache()
    cliente_id = execute_insert('''
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
    
    return {'id': cliente_id, **dados}


def get_cliente(cliente_id: int) -> Optional[Dict]:
    """Busca cliente por ID"""
    row = execute_select_one("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
    
    if row:
        return dict(row)
    return None


def get_clientes() -> List[Dict]:
    """Retorna todos os clientes (com cache)"""
    # Cache por sessao
    if '_cache_clientes' in st.session_state:
        return st.session_state._cache_clientes
    
    rows = execute_select("SELECT * FROM clientes ORDER BY nome")
    result = [dict(row) for row in rows]
    st.session_state._cache_clientes = result
    return result


def atualizar_cliente(cliente_id: int, dados: Dict) -> bool:
    """Atualiza dados de um cliente"""
    invalidar_cache()
    execute_update('''
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
    return True


def excluir_cliente(cliente_id: int) -> bool:
    """Exclui um cliente"""
    invalidar_cache()
    execute_update("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    return True


# ========================================
# INFLUENCIADORES
# ========================================

def criar_influenciador(dados: Dict) -> Dict:
    """Cria influenciador na base"""
    invalidar_cache()
    classificacao = classificar_influenciador(dados.get('seguidores', 0))
    now = datetime.now().isoformat()
    
    means_json = json.dumps(dados.get('means', {})) if dados.get('means') else '{}'
    hashtags_json = json.dumps(dados.get('hashtags', [])) if dados.get('hashtags') else '[]'
    
    inf_id = execute_insert('''
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
    
    return {'id': inf_id, 'classificacao': classificacao, **dados}


def get_influenciador(inf_id: int) -> Optional[Dict]:
    """Busca influenciador por ID"""
    row = execute_select_one("SELECT * FROM influenciadores WHERE id = ?", (inf_id,))
    
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
    usuario_limpo = usuario.replace('@', '').strip().lower()
    row = execute_select_one("SELECT * FROM influenciadores WHERE LOWER(usuario) = ?", (usuario_limpo,))
    
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
    """Retorna todos os influenciadores (com cache)"""
    # Cache por sessao
    if '_cache_influenciadores' in st.session_state:
        return st.session_state._cache_influenciadores
    
    rows = execute_select("SELECT * FROM influenciadores ORDER BY nome")
    
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
    
    st.session_state._cache_influenciadores = influenciadores
    return influenciadores


def atualizar_influenciador(inf_id: int, dados: Dict) -> bool:
    """Atualiza dados de um influenciador"""
    invalidar_cache()
    classificacao = classificar_influenciador(dados.get('seguidores', 0))
    now = datetime.now().isoformat()
    
    means_json = json.dumps(dados.get('means', {})) if dados.get('means') else '{}'
    hashtags_json = json.dumps(dados.get('hashtags', [])) if dados.get('hashtags') else '[]'
    
    execute_update('''
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
    return True


def excluir_influenciador(inf_id: int) -> bool:
    """Exclui um influenciador"""
    invalidar_cache()
    execute_update("DELETE FROM influenciadores WHERE id = ?", (inf_id,))
    return True


# ========================================
# CAMPANHAS
# ========================================

def criar_campanha(dados: Dict) -> Dict:
    """Cria nova campanha"""
    invalidar_cache()
    now = datetime.now().isoformat()
    
    metricas_json = json.dumps(dados.get('metricas_selecionadas', []))
    insights_json = json.dumps(dados.get('insights_config', {}))
    categorias_json = json.dumps(dados.get('categorias_comentarios', []))
    influenciadores_json = json.dumps(dados.get('influenciadores', []))
    
    camp_id = execute_insert('''
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
    
    return {'id': camp_id, **dados}


def get_campanha(camp_id: int) -> Optional[Dict]:
    """Busca campanha por ID"""
    if not camp_id:
        return None
    
    row = execute_select_one("SELECT * FROM campanhas WHERE id = ?", (camp_id,))
    
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
    """Retorna todas as campanhas (com cache)"""
    # Cache por sessao
    if '_cache_campanhas' in st.session_state:
        return st.session_state._cache_campanhas
    
    rows = execute_select("SELECT * FROM campanhas ORDER BY created_at DESC")
    
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
    
    st.session_state._cache_campanhas = campanhas
    return campanhas


def get_campanhas_por_cliente(cliente_id: int) -> List[Dict]:
    """Retorna campanhas de um cliente"""
    rows = execute_select("SELECT * FROM campanhas WHERE cliente_id = ? ORDER BY created_at DESC", (cliente_id,))
    
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
    invalidar_cache()
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
    
    execute_update('''
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
    return True


def excluir_campanha(camp_id: int) -> bool:
    """Exclui uma campanha"""
    invalidar_cache()
    execute_update("DELETE FROM campanhas WHERE id = ?", (camp_id,))
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


def atualizar_post_campanha(camp_id: int, inf_id: int, post_idx: int, post_data: Dict) -> bool:
    """Atualiza um post existente pelo indice"""
    campanha = get_campanha(camp_id)
    if not campanha:
        return False
    
    influenciadores = campanha.get('influenciadores', [])
    
    for i, inf in enumerate(influenciadores):
        if inf.get('influenciador_id') == inf_id:
            posts = inf.get('posts', [])
            if 0 <= post_idx < len(posts):
                post_data['updated_at'] = datetime.now().isoformat()
                posts[post_idx] = post_data
                inf['posts'] = posts
                influenciadores[i] = inf
            break
    
    campanha['influenciadores'] = influenciadores
    return atualizar_campanha(camp_id, campanha)


def remover_post_campanha(camp_id: int, inf_id: int, post_idx: int) -> bool:
    """Remove um post pelo indice"""
    campanha = get_campanha(camp_id)
    if not campanha:
        return False
    
    influenciadores = campanha.get('influenciadores', [])
    
    for i, inf in enumerate(influenciadores):
        if inf.get('influenciador_id') == inf_id:
            posts = inf.get('posts', [])
            if 0 <= post_idx < len(posts):
                posts.pop(post_idx)
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


# ========================================
# GESTAO DE INSIGHTS
# ========================================

def get_insights_campanha(campanha_id: int, pagina: str = None, apenas_ativos: bool = True) -> List[Dict]:
    """Retorna insights de uma campanha, opcionalmente filtrados por página"""
    if pagina:
        if apenas_ativos:
            query = "SELECT * FROM insights_campanha WHERE campanha_id = ? AND pagina = ? AND ativo = 1 ORDER BY ordem, created_at DESC"
            rows = execute_select(query, (campanha_id, pagina))
        else:
            query = "SELECT * FROM insights_campanha WHERE campanha_id = ? AND pagina = ? ORDER BY ordem, created_at DESC"
            rows = execute_select(query, (campanha_id, pagina))
    else:
        if apenas_ativos:
            query = "SELECT * FROM insights_campanha WHERE campanha_id = ? AND ativo = 1 ORDER BY pagina, ordem, created_at DESC"
            rows = execute_select(query, (campanha_id,))
        else:
            query = "SELECT * FROM insights_campanha WHERE campanha_id = ? ORDER BY pagina, ordem, created_at DESC"
            rows = execute_select(query, (campanha_id,))
    
    return [dict(row) for row in rows] if rows else []


def adicionar_insight(campanha_id: int, pagina: str, insight: Dict, fonte: str = 'ia') -> int:
    """Adiciona um novo insight à campanha"""
    now = datetime.now().isoformat()
    
    # Pegar a maior ordem atual para essa página
    rows = execute_select(
        "SELECT MAX(ordem) as max_ordem FROM insights_campanha WHERE campanha_id = ? AND pagina = ?",
        (campanha_id, pagina)
    )
    max_ordem = rows[0]['max_ordem'] if rows and rows[0]['max_ordem'] else 0
    
    query = '''
        INSERT INTO insights_campanha 
        (campanha_id, pagina, tipo, icone, titulo, texto, fonte, ordem, ativo, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
    '''
    
    insight_id = execute_insert(query, (
        campanha_id,
        pagina,
        insight.get('tipo', 'info'),
        insight.get('icone', '💡'),
        insight.get('titulo', 'Insight'),
        insight.get('texto', ''),
        fonte,
        max_ordem + 1,
        now,
        now
    ))
    
    invalidar_cache()
    return insight_id


def adicionar_insights_lote(campanha_id: int, pagina: str, insights: List[Dict], fonte: str = 'ia') -> List[int]:
    """Adiciona múltiplos insights de uma vez"""
    ids = []
    for insight in insights:
        insight_id = adicionar_insight(campanha_id, pagina, insight, fonte)
        ids.append(insight_id)
    return ids


def atualizar_insight(insight_id: int, dados: Dict) -> bool:
    """Atualiza um insight existente"""
    now = datetime.now().isoformat()
    
    campos = []
    valores = []
    
    for campo in ['tipo', 'icone', 'titulo', 'texto', 'ordem', 'ativo']:
        if campo in dados:
            campos.append(f"{campo} = ?")
            valores.append(dados[campo])
    
    if not campos:
        return False
    
    campos.append("updated_at = ?")
    valores.append(now)
    valores.append(insight_id)
    
    query = f"UPDATE insights_campanha SET {', '.join(campos)} WHERE id = ?"
    execute_update(query, tuple(valores))
    invalidar_cache()
    return True


def excluir_insight(insight_id: int, soft_delete: bool = True) -> bool:
    """Exclui um insight (soft delete por padrão)"""
    if soft_delete:
        return atualizar_insight(insight_id, {'ativo': 0})
    else:
        execute_update("DELETE FROM insights_campanha WHERE id = ?", (insight_id,))
        invalidar_cache()
        return True


def reordenar_insights(campanha_id: int, pagina: str, ordem_ids: List[int]) -> bool:
    """Reordena insights de uma página"""
    for idx, insight_id in enumerate(ordem_ids):
        execute_update(
            "UPDATE insights_campanha SET ordem = ? WHERE id = ? AND campanha_id = ?",
            (idx + 1, insight_id, campanha_id)
        )
    invalidar_cache()
    return True


def salvar_historico_insights(campanha_id: int, pagina: str) -> int:
    """Salva o estado atual dos insights no histórico antes de atualizar"""
    insights = get_insights_campanha(campanha_id, pagina, apenas_ativos=True)
    
    if not insights:
        return None
    
    now = datetime.now().isoformat()
    query = '''
        INSERT INTO insights_historico (campanha_id, pagina, insights_json, created_at)
        VALUES (?, ?, ?, ?)
    '''
    
    historico_id = execute_insert(query, (
        campanha_id,
        pagina,
        json.dumps(insights, ensure_ascii=False),
        now
    ))
    
    return historico_id


def get_historico_insights(campanha_id: int, pagina: str = None, limit: int = 10) -> List[Dict]:
    """Retorna histórico de insights de uma campanha"""
    if pagina:
        query = "SELECT * FROM insights_historico WHERE campanha_id = ? AND pagina = ? ORDER BY created_at DESC LIMIT ?"
        rows = execute_select(query, (campanha_id, pagina, limit))
    else:
        query = "SELECT * FROM insights_historico WHERE campanha_id = ? ORDER BY created_at DESC LIMIT ?"
        rows = execute_select(query, (campanha_id, limit))
    
    result = []
    for row in rows:
        item = dict(row)
        try:
            item['insights'] = json.loads(item.get('insights_json', '[]'))
        except:
            item['insights'] = []
        result.append(item)
    
    return result


def restaurar_insights_historico(historico_id: int) -> bool:
    """Restaura insights de um ponto do histórico"""
    row = execute_select_one("SELECT * FROM insights_historico WHERE id = ?", (historico_id,))
    
    if not row:
        return False
    
    campanha_id = row['campanha_id']
    pagina = row['pagina']
    
    try:
        insights = json.loads(row.get('insights_json', '[]'))
    except:
        return False
    
    # Desativar insights atuais dessa página
    execute_update(
        "UPDATE insights_campanha SET ativo = 0 WHERE campanha_id = ? AND pagina = ?",
        (campanha_id, pagina)
    )
    
    # Adicionar insights do histórico
    for insight in insights:
        adicionar_insight(campanha_id, pagina, insight, fonte='historico')
    
    invalidar_cache()
    return True


def limpar_insights_pagina(campanha_id: int, pagina: str, salvar_historico: bool = True) -> bool:
    """Limpa todos os insights de uma página (desativa)"""
    if salvar_historico:
        salvar_historico_insights(campanha_id, pagina)
    
    execute_update(
        "UPDATE insights_campanha SET ativo = 0 WHERE campanha_id = ? AND pagina = ?",
        (campanha_id, pagina)
    )
    invalidar_cache()
    return True


def atualizar_insights_ia(campanha_id: int, pagina: str, novos_insights: List[Dict]) -> bool:
    """
    Atualiza insights gerados por IA:
    1. Salva histórico
    2. Desativa insights IA antigos
    3. Mantém insights manuais
    4. Adiciona novos insights IA
    """
    # Salvar histórico
    salvar_historico_insights(campanha_id, pagina)
    
    # Desativar apenas insights de IA (manter manuais)
    execute_update(
        "UPDATE insights_campanha SET ativo = 0 WHERE campanha_id = ? AND pagina = ? AND fonte = 'ia'",
        (campanha_id, pagina)
    )
    
    # Adicionar novos insights
    for insight in novos_insights:
        adicionar_insight(campanha_id, pagina, insight, fonte='ia')
    
    invalidar_cache()
    return True


# ========================================
# COMENTARIOS - CRUD
# ========================================

def salvar_comentarios(campanha_id: int, post_url: str, comentarios: List[Dict], 
                       influenciador_id: int = None, post_shortcode: str = None) -> int:
    """
    Salva comentarios extraidos no banco
    
    Returns:
        Quantidade de comentarios salvos
    """
    count = 0
    now = datetime.now().isoformat()
    
    for comentario in comentarios:
        try:
            execute_insert(
                """INSERT INTO comentarios_posts 
                   (campanha_id, influenciador_id, post_url, post_shortcode, comment_id,
                    usuario, texto, data_comentario, likes, categoria, sentimento,
                    confianca, justificativa, classificado, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    campanha_id,
                    influenciador_id,
                    post_url,
                    post_shortcode or '',
                    comentario.get('id', ''),
                    comentario.get('usuario', ''),
                    comentario.get('texto', ''),
                    comentario.get('data', ''),
                    comentario.get('likes', 0),
                    comentario.get('categoria', ''),
                    comentario.get('sentimento', ''),
                    comentario.get('confianca', 0),
                    comentario.get('justificativa', ''),
                    1 if comentario.get('categoria') else 0,
                    now
                )
            )
            count += 1
        except Exception as e:
            print(f"Erro ao salvar comentario: {e}")
    
    invalidar_cache()
    return count


def get_comentarios_campanha(campanha_id: int, apenas_classificados: bool = False) -> List[Dict]:
    """Retorna todos os comentarios de uma campanha"""
    if apenas_classificados:
        rows = execute_select(
            "SELECT * FROM comentarios_posts WHERE campanha_id = ? AND classificado = 1 ORDER BY created_at DESC",
            (campanha_id,)
        )
    else:
        rows = execute_select(
            "SELECT * FROM comentarios_posts WHERE campanha_id = ? ORDER BY created_at DESC",
            (campanha_id,)
        )
    return rows


def get_comentarios_post(post_url: str) -> List[Dict]:
    """Retorna comentarios de um post especifico"""
    rows = execute_select(
        "SELECT * FROM comentarios_posts WHERE post_url = ? ORDER BY data_comentario DESC",
        (post_url,)
    )
    return rows


def get_estatisticas_comentarios(campanha_id: int) -> Dict:
    """Retorna estatisticas dos comentarios de uma campanha"""
    comentarios = get_comentarios_campanha(campanha_id, apenas_classificados=True)
    
    if not comentarios:
        return {
            'total': 0,
            'classificados': 0,
            'por_categoria': {},
            'por_sentimento': {}
        }
    
    total = len(comentarios)
    
    # Contagem por categoria
    por_categoria = {}
    for c in comentarios:
        cat = c.get('categoria', 'Nao Classificado')
        por_categoria[cat] = por_categoria.get(cat, 0) + 1
    
    # Contagem por sentimento
    por_sentimento = {'positivo': 0, 'neutro': 0, 'negativo': 0}
    for c in comentarios:
        sent = c.get('sentimento', 'neutro')
        if sent in por_sentimento:
            por_sentimento[sent] += 1
    
    return {
        'total': total,
        'classificados': total,
        'por_categoria': {
            cat: {'quantidade': qtd, 'percentual': round(qtd / total * 100, 1)}
            for cat, qtd in por_categoria.items()
        },
        'por_sentimento': {
            sent: {'quantidade': qtd, 'percentual': round(qtd / total * 100, 1)}
            for sent, qtd in por_sentimento.items()
        }
    }


def atualizar_classificacao_comentario(comment_id: int, classificacao: Dict) -> bool:
    """Atualiza a classificacao de um comentario"""
    execute_update(
        """UPDATE comentarios_posts 
           SET categoria = ?, sentimento = ?, confianca = ?, justificativa = ?, classificado = 1
           WHERE id = ?""",
        (
            classificacao.get('categoria', ''),
            classificacao.get('sentimento', 'neutro'),
            classificacao.get('confianca', 0),
            classificacao.get('justificativa', ''),
            comment_id
        )
    )
    invalidar_cache()
    return True


def excluir_comentarios_post(post_url: str) -> bool:
    """Exclui todos os comentarios de um post"""
    execute_update(
        "DELETE FROM comentarios_posts WHERE post_url = ?",
        (post_url,)
    )
    invalidar_cache()
    return True


def excluir_comentarios_campanha(campanha_id: int) -> bool:
    """Exclui todos os comentarios de uma campanha"""
    execute_update(
        "DELETE FROM comentarios_posts WHERE campanha_id = ?",
        (campanha_id,)
    )
    invalidar_cache()
    return True


# ========================================
# TOKENS DE COMPARTILHAMENTO
# ========================================

def gerar_token_compartilhamento(
    campanha_id: int, 
    cliente_id: int = None,
    titulo: str = None,
    paginas_permitidas: List[str] = None,
    dias_expiracao: int = 30,
    max_visualizacoes: int = None
) -> Dict:
    """
    Gera um token unico para compartilhar relatorio
    
    Args:
        campanha_id: ID da campanha
        cliente_id: ID do cliente (opcional)
        titulo: Titulo personalizado do link
        paginas_permitidas: Lista de paginas que podem ser visualizadas
        dias_expiracao: Dias ate expirar (0 = sem expiracao)
        max_visualizacoes: Maximo de visualizacoes (None = ilimitado)
    
    Returns:
        Dict com token e informacoes
    """
    import secrets
    
    # Gerar token unico
    token = secrets.token_urlsafe(16)
    
    now = datetime.now()
    expira_em = None
    if dias_expiracao > 0:
        expira_em = (now + timedelta(days=dias_expiracao)).isoformat()
    
    paginas_json = json.dumps(paginas_permitidas) if paginas_permitidas else None
    
    token_id = execute_insert(
        """INSERT INTO tokens_compartilhamento 
           (token, campanha_id, cliente_id, titulo, paginas_permitidas, 
            expira_em, max_visualizacoes, ativo, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
        (token, campanha_id, cliente_id, titulo, paginas_json, 
         expira_em, max_visualizacoes, now.isoformat(), now.isoformat())
    )
    
    return {
        'id': token_id,
        'token': token,
        'campanha_id': campanha_id,
        'expira_em': expira_em,
        'max_visualizacoes': max_visualizacoes
    }


def validar_token(token: str) -> Optional[Dict]:
    """
    Valida um token e retorna informacoes se valido
    
    Returns:
        Dict com informacoes do token ou None se invalido/expirado
    """
    row = execute_select_one(
        "SELECT * FROM tokens_compartilhamento WHERE token = ? AND ativo = 1",
        (token,)
    )
    
    if not row:
        return None
    
    token_info = dict(row)
    
    # Verificar expiracao
    if token_info.get('expira_em'):
        expira = datetime.fromisoformat(token_info['expira_em'])
        if datetime.now() > expira:
            return None
    
    # Verificar max visualizacoes
    if token_info.get('max_visualizacoes'):
        if token_info.get('visualizacoes', 0) >= token_info['max_visualizacoes']:
            return None
    
    # Parse paginas permitidas
    if token_info.get('paginas_permitidas'):
        try:
            token_info['paginas_permitidas'] = json.loads(token_info['paginas_permitidas'])
        except:
            token_info['paginas_permitidas'] = None
    
    return token_info


def registrar_visualizacao_token(token: str) -> bool:
    """Incrementa contador de visualizacoes do token"""
    execute_update(
        "UPDATE tokens_compartilhamento SET visualizacoes = visualizacoes + 1, updated_at = ? WHERE token = ?",
        (datetime.now().isoformat(), token)
    )
    return True


def get_tokens_campanha(campanha_id: int) -> List[Dict]:
    """Retorna todos os tokens de uma campanha"""
    rows = execute_select(
        "SELECT * FROM tokens_compartilhamento WHERE campanha_id = ? ORDER BY created_at DESC",
        (campanha_id,)
    )
    return [dict(row) for row in rows]


def desativar_token(token_id: int) -> bool:
    """Desativa um token"""
    execute_update(
        "UPDATE tokens_compartilhamento SET ativo = 0, updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), token_id)
    )
    return True


def excluir_token(token_id: int) -> bool:
    """Exclui um token"""
    execute_update(
        "DELETE FROM tokens_compartilhamento WHERE id = ?",
        (token_id,)
    )
    return True
