"""
UI Components - Sistema de Design Moderno
Componentes reutilizaveis com modais, botoes e estilos consistentes
"""

import streamlit as st
from typing import Optional, Callable
import uuid


def inject_modern_styles():
    """Injeta estilos CSS modernos globais"""
    st.markdown("""
    <style>
    /* ========== FONTE GLOBAL ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* ========== REDUCAO DE FONTES ========== */
    .stApp {
        font-size: 13px !important;
    }
    
    h1 {
        font-size: 1.75rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }
    
    h2 {
        font-size: 1.35rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
    }
    
    h3 {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
    }
    
    p, span, div, label {
        font-size: 13px !important;
        line-height: 1.5 !important;
    }
    
    small, .caption, [data-testid="stCaptionContainer"] {
        font-size: 11px !important;
        color: #6b7280 !important;
    }
    
    /* ========== BOTOES MODERNOS ========== */
    .stButton > button {
        font-family: 'Inter', sans-serif !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        padding: 0.45rem 0.9rem !important;
        border-radius: 8px !important;
        border: 1px solid transparent !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        min-height: 36px !important;
        background: #f8f9fa !important;
        color: #374151 !important;
    }
    
    .stButton > button:hover {
        background: rgba(124, 58, 237, 0.08) !important;
        border-color: rgba(124, 58, 237, 0.3) !important;
        color: #7c3aed !important;
        transform: translateY(-1px) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Botao primario */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
        color: white !important;
        border: none !important;
    }
    
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3) !important;
        color: white !important;
    }
    
    /* ========== INPUTS MODERNOS ========== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        font-family: 'Inter', sans-serif !important;
        font-size: 13px !important;
        border-radius: 8px !important;
        border: 1px solid #e5e7eb !important;
        padding: 0.5rem 0.75rem !important;
        transition: all 0.2s ease !important;
        background: white !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1) !important;
        outline: none !important;
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        font-size: 13px !important;
    }
    
    .stSelectbox [data-baseweb="select"] > div {
        border-radius: 8px !important;
        border-color: #e5e7eb !important;
        background: white !important;
    }
    
    /* ========== LABELS ========== */
    .stTextInput > label,
    .stNumberInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stMultiSelect > label,
    .stCheckbox > label,
    .stDateInput > label {
        font-size: 12px !important;
        font-weight: 500 !important;
        color: #4b5563 !important;
        margin-bottom: 4px !important;
    }
    
    /* ========== CHECKBOXES ========== */
    .stCheckbox > label > span {
        font-size: 13px !important;
    }
    
    /* ========== TABS MODERNAS ========== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0 !important;
        background: #f3f4f6 !important;
        border-radius: 10px !important;
        padding: 4px !important;
        border: none !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        padding: 8px 16px !important;
        border-radius: 8px !important;
        color: #6b7280 !important;
        background: transparent !important;
        border: none !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #7c3aed !important;
        background: rgba(124, 58, 237, 0.05) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #7c3aed !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
    }
    
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }
    
    /* ========== DATAFRAMES ========== */
    .stDataFrame {
        font-size: 12px !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }
    
    /* ========== METRICS ========== */
    [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #6b7280 !important;
    }
    
    /* ========== EXPANDERS ========== */
    .streamlit-expanderHeader {
        font-size: 13px !important;
        font-weight: 500 !important;
        background: #f9fafb !important;
        border-radius: 8px !important;
        border: 1px solid #e5e7eb !important;
        padding: 0.75rem 1rem !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: #f3f4f6 !important;
        border-color: #d1d5db !important;
    }
    
    .streamlit-expanderContent {
        border: 1px solid #e5e7eb !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        padding: 1rem !important;
    }
    
    /* ========== FORMS ========== */
    [data-testid="stForm"] {
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        background: #fafafa !important;
    }
    
    /* ========== DIVIDERS ========== */
    hr {
        border: none !important;
        border-top: 1px solid #e5e7eb !important;
        margin: 1rem 0 !important;
    }
    
    /* ========== ALERTAS ========== */
    .stAlert {
        border-radius: 10px !important;
        font-size: 13px !important;
        border: none !important;
    }
    
    /* ========== DOWNLOAD BUTTON ========== */
    .stDownloadButton > button {
        font-size: 12px !important;
        padding: 0.45rem 0.9rem !important;
        border-radius: 8px !important;
        background: #f8f9fa !important;
        border: 1px solid #e5e7eb !important;
        color: #374151 !important;
    }
    
    .stDownloadButton > button:hover {
        background: rgba(124, 58, 237, 0.08) !important;
        border-color: rgba(124, 58, 237, 0.3) !important;
        color: #7c3aed !important;
    }
    
    /* ========== BADGES ========== */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.2rem 0.6rem;
        font-size: 10px;
        font-weight: 500;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    
    .badge-purple { background: rgba(124, 58, 237, 0.1); color: #7c3aed; }
    .badge-green { background: rgba(34, 197, 94, 0.1); color: #16a34a; }
    .badge-orange { background: rgba(249, 115, 22, 0.1); color: #ea580c; }
    .badge-red { background: rgba(239, 68, 68, 0.1); color: #dc2626; }
    .badge-blue { background: rgba(59, 130, 246, 0.1); color: #2563eb; }
    .badge-gray { background: rgba(107, 114, 128, 0.1); color: #4b5563; }
    
    /* ========== CARDS MODERNOS ========== */
    .modern-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1rem;
        transition: all 0.2s ease;
    }
    
    .modern-card:hover {
        border-color: #d1d5db;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* ========== EMPTY STATE ========== */
    .empty-state {
        text-align: center;
        padding: 2.5rem 2rem;
        color: #6b7280;
    }
    
    .empty-state-icon {
        font-size: 2.5rem;
        margin-bottom: 0.75rem;
        opacity: 0.5;
    }
    
    .empty-state-title {
        font-size: 14px;
        font-weight: 500;
        color: #374151;
        margin-bottom: 0.4rem;
    }
    
    .empty-state-text {
        font-size: 12px;
        color: #6b7280;
    }
    
    /* ========== CUSTOM HEADER ========== */
    .main-header {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: #111827 !important;
        margin: 0 !important;
        letter-spacing: -0.02em !important;
    }
    
    .subtitle {
        font-size: 12px !important;
        color: #6b7280 !important;
        margin: 0.25rem 0 0 0 !important;
    }
    
    /* ========== ITEM LISTS ========== */
    .item-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 0.875rem 1rem;
        margin-bottom: 0.5rem;
        transition: all 0.15s ease;
    }
    
    .item-card:hover {
        background: #f3f4f6;
        border-color: #d1d5db;
    }
    
    /* ========== SCROLLBAR ========== */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a1a1a1;
    }
    
    /* ========== RESPONSIVE ========== */
    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab"] {
            padding: 6px 10px !important;
            font-size: 11px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def open_modal(modal_id: str):
    """Abre um modal pelo ID"""
    st.session_state[f'modal_{modal_id}_open'] = True


def close_modal(modal_id: str):
    """Fecha um modal pelo ID"""
    st.session_state[f'modal_{modal_id}_open'] = False


def is_modal_open(modal_id: str) -> bool:
    """Verifica se um modal esta aberto"""
    return st.session_state.get(f'modal_{modal_id}_open', False)


def render_modal_trigger(label: str, modal_id: str, icon: str = "", button_type: str = "secondary", key: str = None, full_width: bool = False):
    """Renderiza um botao que abre um modal"""
    btn_key = key or f"btn_open_{modal_id}_{uuid.uuid4().hex[:6]}"
    display_label = f"{icon} {label}".strip() if icon else label
    is_primary = button_type == "primary"
    
    if st.button(display_label, key=btn_key, type="primary" if is_primary else "secondary", use_container_width=full_width):
        open_modal(modal_id)
        st.rerun()


def render_empty_state(icon: str, title: str, description: str):
    """Renderiza estado vazio com icone e mensagem"""
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-text">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def render_badge(text: str, color: str = "gray"):
    """Renderiza badge colorido - retorna HTML"""
    return f'<span class="badge badge-{color}">{text}</span>'
