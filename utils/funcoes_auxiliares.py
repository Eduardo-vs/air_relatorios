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
            font-size: 1.8rem;
            font-weight: 700;
            margin: 0;
            color: #1a1a1a;
        }}
        
        .top-nav-logo p {{
            font-size: 0.8rem;
            margin: 0;
            color: #6b7280;
            border-left: 2px solid #e5e7eb;
            padding-left: 1rem;
        }}
        
        .stButton>button {{
            background-color: {primary_color};
            color: {text_color_primary};
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.5rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }}
        
        .stButton>button:hover {{
            opacity: 0.9;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        [data-testid="stSidebar"] {{
            background: #f9fafb;
            border-right: 1px solid #e5e7eb;
        }}
        
        .main-header {{
            font-size: 2rem;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 0.5rem;
            border-bottom: 3px solid {primary_color};
            padding-bottom: 0.5rem;
        }}
        
        .subtitle {{
            font-size: 0.95rem;
            color: #6b7280;
            margin-bottom: 2rem;
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
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: {primary_color};
            color: {text_color_primary};
        }}
        
        .air-score-card {{
            background: linear-gradient(135deg, {primary_color}, {secondary_color});
            color: white;
            padding: 1.5rem;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        }}
        
        .air-score-number {{
            font-size: 3rem;
            font-weight: 700;
            margin: 0;
        }}
        
        .air-score-label {{
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }}
        
        .card-metric {{
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
        }}
        
        .card-metric-value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: {primary_color};
        }}
        
        .card-metric-label {{
            font-size: 0.8rem;
            color: #6b7280;
            margin-top: 0.25rem;
        }}
    </style>
    """, unsafe_allow_html=True)
