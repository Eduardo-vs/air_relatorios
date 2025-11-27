"""
Utils - Funções Auxiliares
Todas as funções de apoio do sistema
"""

import streamlit as st
from datetime import datetime
from collections import Counter
import re

# ========================================
# FUNÇÕES DE FORMATAÇÃO
# ========================================

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

def formatar_numero(num):
    """Formata número com separador de milhares"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.0f}K"
    return str(num)

def get_text_color(hex_color):
    """Retorna preto ou branco baseado na luminosidade da cor"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    luminosidade = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return '#000000' if luminosidade > 0.5 else '#ffffff'

# ========================================
# CLASSIFICAÇÃO E ANÁLISE
# ========================================

def classificar_influenciador(seguidores_str):
    """Classifica influenciador por tamanho"""
    try:
        seguidores_str = str(seguidores_str).upper().replace(' ', '')
        
        if 'K' in seguidores_str:
            num = float(seguidores_str.replace('K', '')) * 1000
        elif 'M' in seguidores_str:
            num = float(seguidores_str.replace('M', '')) * 1000000
        else:
            num = float(seguidores_str)
        
        if num < 10000:
            return 'Nano'
        elif num < 100000:
            return 'Micro'
        elif num < 500000:
            return 'Mid'
        elif num < 1000000:
            return 'Macro'
        else:
            return 'Mega'
    except:
        return 'Desconhecido'

def calcular_air_score(campanha):
    """Calcula o AIR Score da campanha (0-100)"""
    from utils.data_manager import calcular_metricas_campanha
    
    metricas = calcular_metricas_campanha(campanha)
    
    if metricas['total_posts'] == 0:
        return 0
    
    # Componentes do score
    score_engajamento = min(metricas['engajamento_efetivo'] * 10, 40)  # Até 40 pontos
    score_alcance = min((metricas['total_views'] / 100000) * 20, 30)  # Até 30 pontos
    score_conversao = min(metricas['total_conversoes_cupom'] / 10, 15)  # Até 15 pontos
    score_saves = min((metricas['total_saves'] / metricas['total_views']) * 1000, 15) if metricas['total_views'] > 0 else 0  # Até 15 pontos
    
    score_total = score_engajamento + score_alcance + score_conversao + score_saves
    
    return min(round(score_total, 1), 100)

# ========================================
# CORES PARA GRÁFICOS
# ========================================

def get_cores_graficos():
    """Retorna paleta de cores mais vibrantes para gráficos"""
    return [
        '#7c3aed',  # Roxo principal
        '#fb923c',  # Laranja
        '#22c55e',  # Verde
        '#3b82f6',  # Azul
        '#f43f5e',  # Rosa/Vermelho
        '#a855f7',  # Roxo claro
        '#14b8a6',  # Teal
        '#eab308',  # Amarelo
        '#6366f1',  # Indigo
        '#ec4899',  # Pink
    ]

def get_color_scale_vibrante():
    """Retorna escala de cores vibrante"""
    return [
        [0, '#7c3aed'],
        [0.5, '#a855f7'],
        [1, '#fb923c']
    ]

# ========================================
# ANÁLISE DE SENTIMENTO (IA)
# ========================================

def analisar_sentimento_comentario(texto):
    """Simula análise de sentimento com IA"""
    texto_lower = texto.lower()
    
    # Palavras positivas
    positivas = ['amo', 'adoro', 'melhor', 'top', 'incrível', 'perfeito', 'maravilhoso', 
                 'excelente', 'bom', 'legal', 'nostalgia', 'comprar', 'quero', 'vou comprar',
                 'amei', 'demais', 'show', 'fantástico', 'adorei']
    
    # Palavras negativas
    negativas = ['ruim', 'péssimo', 'horrível', 'não gostei', 'chato', 'fraco', 'caro',
                 'terrível', 'decepção', 'pior']
    
    # Categorias
    if any(palavra in texto_lower for palavra in ['comprar', 'quero', 'vou comprar', 'onde compro', 'preciso', 'vou pegar']):
        categoria = 'Intenção de Compra'
        polaridade = 'positivo'
    elif any(palavra in texto_lower for palavra in ['nostalgia', 'lembra', 'memória', 'infância', 'saudade', 'antigamente']):
        categoria = 'Conexão Emocional'
        polaridade = 'positivo'
    elif any(palavra in texto_lower for palavra in ['preço', 'quanto', 'valor', 'custa', 'valor']):
        categoria = 'Dúvida'
        polaridade = 'neutro'
    elif any(palavra in texto_lower for palavra in positivas):
        categoria = 'Elogio ao Produto'
        polaridade = 'positivo'
    elif any(palavra in texto_lower for palavra in negativas):
        categoria = 'Crítica'
        polaridade = 'negativo'
    else:
        categoria = 'Geral'
        polaridade = 'neutro'
    
    return {
        'polaridade': polaridade,
        'categoria': categoria
    }

def extrair_palavras_chave(comentarios):
    """Extrai palavras-chave dos comentários para nuvem de palavras"""
    stop_words = ['o', 'a', 'de', 'da', 'do', 'em', 'para', 'com', 'e', 'que', 'é', 'um', 'uma', 
                  'os', 'as', 'dos', 'das', 'no', 'na', 'se', 'por', 'mais', 'muito', 'eu', 'você',
                  'são', 'esse', 'essa', 'isso', 'ele', 'ela', 'seu', 'sua', 'meu', 'minha']
    
    palavras = []
    for comentario in comentarios:
        texto = comentario['texto'].lower()
        # Remove pontuação e quebra em palavras
        texto_limpo = re.sub(r'[^\w\s]', '', texto)
        palavras_texto = [p for p in texto_limpo.split() if len(p) > 3 and p not in stop_words]
        palavras.extend(palavras_texto)
    
    return Counter(palavras).most_common(30)

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
        
        /* Navegação Top */
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
        
        /* Botões */
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
            background-color: #6b7280;
            color: white;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: #f9fafb;
            border-right: 1px solid #e5e7eb;
        }}
        
        .sidebar-campaign-card {{
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 0.75rem;
            margin-bottom: 1rem;
            font-size: 0.85rem;
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
            transition: all 0.2s;
        }}
        
        .stTabs [data-baseweb="tab"]:hover {{
            background-color: #e5e7eb;
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: {primary_color};
            color: {text_color_primary};
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .air-score-card {{
            background: linear-gradient(135deg, {primary_color}, {secondary_color});
            color: white;
            padding: 2rem;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        }}
        
        .air-score-number {{
            font-size: 4rem;
            font-weight: 700;
            margin: 0;
        }}
        
        .air-score-label {{
            font-size: 1rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }}
        
        /* Cards de métricas */
        .metric-card {{
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {primary_color};
        }}
        
        .metric-label {{
            font-size: 0.85rem;
            color: #6b7280;
            margin-top: 0.5rem;
        }}
        
        /* Influenciador card */
        .influencer-card {{
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 1rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }}
        
        .influencer-photo {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            object-fit: cover;
        }}
        
        /* Notas/Campo de escrita */
        .notes-area {{
            background: #fefce8;
            border: 1px solid #fef08a;
            border-radius: 12px;
            padding: 1rem;
        }}
    </style>
    """, unsafe_allow_html=True)
