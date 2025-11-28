"""
Funcoes Auxiliares - Formatacao, cores e CSS
"""

import streamlit as st
from datetime import datetime
import re
from collections import Counter

# ========================================
# FORMATACAO
# ========================================

def formatar_numero(num):
    """Formata numero com separador de milhares"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.0f}K"
    return f"{num:,}".replace(",", ".")


def formatar_data_br(data_str):
    """Converte para dd/mm/yyyy"""
    try:
        if isinstance(data_str, str):
            if '/' in data_str and len(data_str) == 10:
                return data_str
            data = datetime.fromisoformat(data_str)
            return data.strftime('%d/%m/%Y')
        elif isinstance(data_str, datetime):
            return data_str.strftime('%d/%m/%Y')
        else:
            return str(data_str)
    except:
        return data_str


def get_text_color(hex_color):
    """Retorna preto ou branco baseado na luminosidade"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    luminosidade = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return '#000000' if luminosidade > 0.5 else '#ffffff'


# ========================================
# CORES PARA GRAFICOS
# ========================================

def get_cores_graficos():
    """Paleta de cores vibrantes para graficos"""
    return [
        '#7c3aed',  # Roxo principal
        '#f97316',  # Laranja vibrante
        '#10b981',  # Verde esmeralda
        '#3b82f6',  # Azul
        '#ef4444',  # Vermelho
        '#8b5cf6',  # Roxo claro
        '#06b6d4',  # Cyan
        '#f59e0b',  # Amarelo
        '#6366f1',  # Indigo
        '#ec4899',  # Pink
    ]


# ========================================
# ANALISE DE SENTIMENTO
# ========================================

def analisar_sentimento(texto: str, categorias: list = None) -> dict:
    """
    Analisa sentimento de um comentario
    Categorias podem ser personalizadas por campanha
    """
    if categorias is None:
        categorias = ['Elogio ao Produto', 'Intencao de Compra', 'Conexao Emocional', 'Duvida', 'Critica', 'Geral']
    
    texto_lower = texto.lower()
    
    # Palavras-chave para cada categoria
    keywords = {
        'Intencao de Compra': ['comprar', 'quero', 'vou comprar', 'onde compro', 'preciso', 'vou pegar', 'link'],
        'Conexao Emocional': ['nostalgia', 'lembra', 'memoria', 'infancia', 'saudade', 'antigamente', 'emocao'],
        'Duvida': ['preco', 'quanto', 'valor', 'custa', 'como', 'onde', 'quando'],
        'Elogio ao Produto': ['amo', 'adoro', 'melhor', 'top', 'incrivel', 'perfeito', 'maravilhoso', 'excelente', 'amei', 'demais'],
        'Critica': ['ruim', 'pessimo', 'horrivel', 'nao gostei', 'chato', 'fraco', 'caro', 'terrivel', 'decepcionante']
    }
    
    # Palavras positivas e negativas para polaridade
    positivas = ['amo', 'adoro', 'melhor', 'top', 'incrivel', 'perfeito', 'maravilhoso', 'excelente', 'amei', 'demais', 'lindo', 'otimo']
    negativas = ['ruim', 'pessimo', 'horrivel', 'nao gostei', 'chato', 'fraco', 'caro', 'terrivel', 'decepcionante', 'pior']
    
    # Determinar categoria
    categoria = 'Geral'
    for cat, words in keywords.items():
        if cat in categorias and any(word in texto_lower for word in words):
            categoria = cat
            break
    
    # Determinar polaridade
    if any(word in texto_lower for word in negativas):
        polaridade = 'negativo'
    elif any(word in texto_lower for word in positivas):
        polaridade = 'positivo'
    else:
        polaridade = 'neutro'
    
    return {
        'polaridade': polaridade,
        'categoria': categoria
    }


def extrair_palavras_chave(comentarios: list) -> list:
    """Extrai palavras-chave para nuvem de palavras"""
    stop_words = ['o', 'a', 'de', 'da', 'do', 'em', 'para', 'com', 'e', 'que', 'um', 'uma', 
                  'os', 'as', 'dos', 'das', 'no', 'na', 'se', 'por', 'mais', 'muito', 'eu', 'voce',
                  'sao', 'esse', 'essa', 'isso', 'ele', 'ela', 'seu', 'sua', 'meu', 'minha',
                  'foi', 'vai', 'ter', 'tem', 'tinha', 'esta', 'este', 'nos', 'nao', 'sim']
    
    palavras = []
    for comentario in comentarios:
        texto = comentario.get('texto', '').lower()
        texto_limpo = re.sub(r'[^\w\s]', '', texto)
        palavras_texto = [p for p in texto_limpo.split() if len(p) > 3 and p not in stop_words]
        palavras.extend(palavras_texto)
    
    return Counter(palavras).most_common(50)


def exportar_campanha_csv(campanha: dict, influenciadores_data: list) -> str:
    """Exporta dados da campanha para CSV"""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow([
        'Influenciador', 'Usuario', 'Rede', 'Classificacao', 'Seguidores',
        'Formato', 'Data', 'Link', 'Views', 'Alcance', 'Interacoes', 
        'Impressoes', 'Curtidas', 'Comentarios', 'Compartilhamentos', 
        'Saves', 'Cliques Link', 'Conversoes', 'Custo'
    ])
    
    # Dados
    for inf_data in influenciadores_data:
        for post in inf_data.get('posts', []):
            writer.writerow([
                inf_data.get('nome', ''),
                inf_data.get('usuario', ''),
                inf_data.get('network', ''),
                inf_data.get('classificacao', ''),
                inf_data.get('seguidores', 0),
                post.get('formato', ''),
                post.get('data_publicacao', ''),
                post.get('link_post', ''),
                post.get('views', 0),
                post.get('alcance', 0),
                post.get('interacoes', 0),
                post.get('impressoes', 0),
                post.get('curtidas', 0),
                post.get('comentarios_qtd', 0),
                post.get('compartilhamentos', 0),
                post.get('saves', 0),
                post.get('clique_link', 0),
                post.get('cupom_conversoes', 0),
                post.get('custo', 0)
            ])
    
    return output.getvalue()


# ========================================
# CSS GLOBAL
# ========================================

def aplicar_css_global(primary_color, secondary_color):
    """Aplica CSS global do sistema"""
    
    text_color_primary = get_text_color(primary_color)
    text_color_secondary = get_text_color(secondary_color)
    
    st.markdown(f"""
    <style>
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        .main {{
            background-color: #ffffff;
            padding-top: 0 !important;
        }}
        
        .block-container {{
            padding-top: 0.5rem !important;
            max-width: 100%;
        }}
        
        .top-nav-logo {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .top-nav-logo h1 {{
            font-size: clamp(1.2rem, 3vw, 1.8rem);
            font-weight: 700;
            margin: 0;
            color: #1a1a1a;
            white-space: nowrap;
        }}
        
        .top-nav-logo p {{
            font-size: clamp(0.6rem, 1.2vw, 0.8rem);
            margin: 0;
            color: #6b7280;
            border-left: 2px solid #e5e7eb;
            padding-left: 1rem;
            white-space: nowrap;
        }}
        
        /* BOTOES DE NAVEGACAO - FUNDO TRANSPARENTE */
        [data-testid="stHorizontalBlock"]:first-of-type .stButton > button {{
            background: transparent !important;
            border: none !important;
            color: {primary_color} !important;
            font-weight: 600 !important;
            padding: 0.5rem 1rem !important;
            position: relative;
            box-shadow: none !important;
        }}
        
        [data-testid="stHorizontalBlock"]:first-of-type .stButton > button:hover {{
            background: transparent !important;
            transform: scale(1.05);
            color: {primary_color} !important;
            border-bottom: 3px solid {primary_color} !important;
        }}
        
        [data-testid="stHorizontalBlock"]:first-of-type .stButton > button:focus {{
            background: transparent !important;
            box-shadow: none !important;
        }}
        
        /* Botoes gerais */
        .stButton > button {{
            background-color: {primary_color};
            color: {text_color_primary};
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.5rem;
            font-weight: 500;
            transition: all 0.2s ease;
            font-size: clamp(0.7rem, 1.2vw, 0.9rem);
            white-space: nowrap;
        }}
        
        .stButton > button:hover {{
            opacity: 0.9;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        [data-testid="stSidebar"] {{
            background: #f9fafb;
            border-right: 1px solid #e5e7eb;
        }}
        
        /* Texto adaptavel - nao quebra linha */
        .main-header {{
            font-size: clamp(1.2rem, 3vw, 2rem);
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 0.5rem;
            border-bottom: 3px solid {primary_color};
            padding-bottom: 0.5rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .subtitle {{
            font-size: clamp(0.7rem, 1.5vw, 0.95rem);
            color: #6b7280;
            margin-bottom: 2rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background: #f9fafb;
            padding: 0.5rem;
            border-radius: 12px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background-color: transparent;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            color: #6b7280;
            font-weight: 500;
            font-size: clamp(0.7rem, 1.2vw, 0.9rem);
            white-space: nowrap;
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: {primary_color};
            color: {text_color_primary};
        }}
        
        /* AIR SCORE CARD */
        .air-score-card {{
            background: linear-gradient(135deg, {primary_color}, {secondary_color});
            color: white;
            padding: 1.5rem;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
            grid-row: span 2;
        }}
        
        .air-score-number {{
            font-size: clamp(2rem, 4vw, 3rem);
            font-weight: 700;
            margin: 0;
            white-space: nowrap;
        }}
        
        .air-score-label {{
            font-size: clamp(0.7rem, 1.2vw, 0.9rem);
            opacity: 0.9;
            margin-top: 0.5rem;
            white-space: nowrap;
        }}
        
        /* CARDS DE METRICAS */
        .card-metric {{
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
        }}
        
        .card-metric-value {{
            font-size: clamp(1.2rem, 2.5vw, 1.8rem);
            font-weight: 700;
            color: {primary_color};
            white-space: nowrap;
        }}
        
        .card-metric-label {{
            font-size: clamp(0.6rem, 1vw, 0.8rem);
            color: #6b7280;
            margin-top: 0.25rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        /* Metricas Streamlit */
        [data-testid="stMetricValue"] {{
            font-size: clamp(1rem, 2vw, 1.5rem) !important;
            white-space: nowrap;
        }}
        
        [data-testid="stMetricLabel"] {{
            font-size: clamp(0.6rem, 1vw, 0.8rem) !important;
            white-space: nowrap;
        }}
        
        /* Janela de posts com scroll */
        .posts-scroll-container {{
            max-height: 400px;
            overflow-y: auto;
            padding-right: 10px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1rem;
            background: #fafafa;
        }}
        
        .posts-selecionados-container {{
            max-height: 400px;
            overflow-y: auto;
            padding: 1rem;
            border: 1px solid {primary_color};
            border-radius: 8px;
            background: rgba(124, 58, 237, 0.05);
        }}
        
        /* Tabelas */
        .stDataFrame {{
            font-size: clamp(0.7rem, 1.2vw, 0.9rem);
        }}
    </style>
    """, unsafe_allow_html=True)
