"""
Database - Modelos e conexao com banco de dados
Suporta PostgreSQL (producao) e SQLite (desenvolvimento)
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

# Configuracao do banco
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///air_relatorios.db')

# Para desenvolvimento local com SQLite
if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========================================
# MODELOS
# ========================================

class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    cnpj = Column(String(20))
    contato = Column(String(255))
    email = Column(String(255))
    is_aon = Column(Boolean, default=False)  # Cliente AON tem visao especial
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    campanhas = relationship("Campanha", back_populates="cliente")


class Influenciador(Base):
    """Influenciador na base geral (dados da API)"""
    __tablename__ = "influenciadores"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(String(100), unique=True, index=True)  # ID da API para atualizacoes
    nome = Column(String(255), nullable=False)
    usuario = Column(String(100), nullable=False)
    network = Column(String(50), default='instagram')  # instagram, tiktok, youtube
    
    # Dados da API
    seguidores = Column(Integer, default=0)
    foto = Column(Text)  # URL da foto
    bio = Column(Text)
    engagement_rate = Column(Float, default=0)
    air_score = Column(Float, default=0)  # Score retornado pela API
    
    # Counters da API
    total_posts = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    total_comments = Column(Integer, default=0)
    
    # Metricas adicionais
    reach_rate = Column(Float, default=0)
    means = Column(JSON, default={})  # Medias de metricas
    hashtags = Column(JSON, default=[])  # Hashtags mais usadas
    
    # Classificacao
    classificacao = Column(String(20))  # Nano, Micro, Mid, Macro, Mega
    
    # Controle
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    campanhas_influenciadores = relationship("CampanhaInfluenciador", back_populates="influenciador")


class Campanha(Base):
    __tablename__ = "campanhas"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    objetivo = Column(Text)
    data_inicio = Column(String(20))
    data_fim = Column(String(20))
    
    # Configuracoes
    tipo_dados = Column(String(20), default='estatico')  # estatico ou dinamico
    is_aon = Column(Boolean, default=False)
    status = Column(String(20), default='ativa')
    
    # Metricas selecionadas para a campanha
    metricas_selecionadas = Column(JSON, default={
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
    })
    
    # Configuracao de insights do relatorio
    insights_config = Column(JSON, default={
        'mostrar_engajamento': True,
        'mostrar_alcance': True,
        'mostrar_conversao': True,
        'mostrar_saves': True,
        'mostrar_comparativo_formato': True,
        'mostrar_top_influenciadores': True,
        'insights_personalizados': []
    })
    
    # Configuracao de categorias para IA classificar comentarios
    categorias_comentarios = Column(JSON, default=[
        'Elogio ao Produto',
        'Intencao de Compra',
        'Conexao Emocional',
        'Duvida',
        'Critica',
        'Geral'
    ])
    
    # Notas e observacoes
    notas = Column(Text, default='')
    
    # Controle
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="campanhas")
    influenciadores = relationship("CampanhaInfluenciador", back_populates="campanha")


class CampanhaInfluenciador(Base):
    """Relacionamento entre Campanha e Influenciador com dados especificos"""
    __tablename__ = "campanha_influenciadores"
    
    id = Column(Integer, primary_key=True, index=True)
    campanha_id = Column(Integer, ForeignKey("campanhas.id"))
    influenciador_id = Column(Integer, ForeignKey("influenciadores.id"))
    
    # Snapshot dos dados do influenciador no momento da adicao (para campanhas estaticas)
    snapshot_dados = Column(JSON, default={})
    
    # Controle
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    campanha = relationship("Campanha", back_populates="influenciadores")
    influenciador = relationship("Influenciador", back_populates="campanhas_influenciadores")
    posts = relationship("Post", back_populates="campanha_influenciador")


class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    campanha_influenciador_id = Column(Integer, ForeignKey("campanha_influenciadores.id"))
    
    # Dados do post
    formato = Column(String(50))  # Reels, Stories, Carrossel, Feed, TikTok, YouTube
    plataforma = Column(String(50))
    data_publicacao = Column(String(20))
    link_post = Column(Text)
    
    # Metricas
    views = Column(Integer, default=0)
    alcance = Column(Integer, default=0)
    interacoes = Column(Integer, default=0)
    impressoes = Column(Integer, default=0)
    curtidas = Column(Integer, default=0)
    comentarios_qtd = Column(Integer, default=0)
    compartilhamentos = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    clique_link = Column(Integer, default=0)
    cupom_conversoes = Column(Integer, default=0)
    cupom_codigo = Column(String(50))
    
    # Custo (para calculo de eficiencia)
    custo = Column(Float, default=0)
    
    # Imagens (base64 ou URLs)
    imagens = Column(JSON, default=[])
    
    # Controle
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    campanha_influenciador = relationship("CampanhaInfluenciador", back_populates="posts")
    comentarios = relationship("Comentario", back_populates="post")


class Comentario(Base):
    __tablename__ = "comentarios"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    
    # Dados do comentario
    texto = Column(Text, nullable=False)
    autor = Column(String(255))
    data = Column(String(50))
    
    # Classificacao da IA
    polaridade = Column(String(20))  # positivo, neutro, negativo
    categoria = Column(String(100))  # Baseado nas categorias configuradas na campanha
    aderente_campanha = Column(Boolean, default=False)  # Se e aderente ao objetivo
    
    # Controle
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    post = relationship("Post", back_populates="comentarios")


# ========================================
# FUNCOES DE BANCO
# ========================================

def criar_tabelas():
    """Cria todas as tabelas no banco"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Retorna sessao do banco"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Nao fechar aqui, fechar no finally do chamador


# Criar tabelas ao importar
criar_tabelas()
