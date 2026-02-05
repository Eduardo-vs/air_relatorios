"""
Pagina: Relatorio Publico (Compartilhavel)
Usa EXATAMENTE o mesmo codigo do relatorio normal
"""

import streamlit as st
from utils import data_manager, funcoes_auxiliares

# Importar funcoes do relatorio principal
from pages.relatorios import (
    render_pag1_big_numbers,
    render_pag3_visao_aon,
    render_pag4_kpis_influenciador,
    render_pag5_top_performance,
    render_pag6_lista_influenciadores,
    render_comentarios,
    render_glossario
)


def render_publico(token: str):
    """Renderiza relatorio publico usando o mesmo codigo do relatorio normal"""
    
    # Validar token
    token_info = data_manager.validar_token(token)
    
    if not token_info:
        st.error("Link invalido ou expirado")
        st.info("Este link de compartilhamento nao existe, ja expirou ou atingiu o limite de visualizacoes.")
        return
    
    # Registrar visualizacao
    data_manager.registrar_visualizacao_token(token)
    
    # Buscar campanha
    campanha_id = token_info['campanha_id']
    campanha = data_manager.get_campanha(campanha_id)
    
    if not campanha:
        st.error("Campanha nao encontrada")
        return
    
    # Buscar cliente
    cliente = None
    if campanha.get('cliente_id'):
        cliente = data_manager.get_cliente(campanha['cliente_id'])
    
    # Cores
    primary_color = st.session_state.get('primary_color', '#7c3aed')
    
    # Header
    titulo_relatorio = token_info.get('titulo') or campanha['nome']
    nome_cliente = cliente['nome'] if cliente else ''
    
    st.markdown(f"""
    <div style='text-align: center; padding: 1.5rem 0; border-bottom: 3px solid {primary_color}; margin-bottom: 1rem;'>
        <h1 style='color: {primary_color}; margin: 0; font-size: 1.8rem;'>{titulo_relatorio}</h1>
        <p style='color: #6b7280; margin-top: 0.5rem;'>
            {nome_cliente} | {campanha.get('data_inicio', '')} - {campanha.get('data_fim', '')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botoes de download CSV
    influenciadores_data = data_manager.get_influenciadores_campanha(campanha['id'])
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        csv_data = funcoes_auxiliares.exportar_campanha_csv(campanha, influenciadores_data)
        st.download_button(
            "CSV Conteudo",
            data=csv_data,
            file_name=f"{campanha['nome']}_conteudo.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col3:
        csv_balizadores = funcoes_auxiliares.exportar_csv_balizadores(campanha, influenciadores_data)
        st.download_button(
            "CSV Balizadores",
            data=csv_balizadores,
            file_name=f"{campanha['nome']}_balizadores.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Lista de campanhas (para compatibilidade com funcoes do relatorio)
    campanhas_list = [campanha]
    
    # Calcular metricas
    metricas = data_manager.calcular_metricas_multiplas_campanhas(campanhas_list)
    cores = funcoes_auxiliares.get_cores_graficos()
    
    # Verificar se tem AON
    has_aon = any(c.get('is_aon') for c in campanhas_list)
    
    # Definir tabs - IDENTICAS ao relatorio normal
    if has_aon:
        tabs = st.tabs([
            "1. Big Numbers",
            "2. Visao AON",
            "3. KPIs por Influ",
            "4. Top Performance",
            "5. Lista Influs",
            "Comentarios",
            "Glossario"
        ])
    else:
        tabs = st.tabs([
            "1. Big Numbers",
            "2. KPIs por Influ",
            "3. Top Performance",
            "4. Lista Influs",
            "Comentarios",
            "Glossario"
        ])
    
    tab_idx = 0
    
    # TAB 1: BIG NUMBERS
    with tabs[tab_idx]:
        try:
            render_pag1_big_numbers(campanhas_list, metricas, cores)
        except Exception as e:
            st.error(f"Erro ao carregar: {e}")
    tab_idx += 1
    
    # TAB 2: VISAO AON (se aplicavel)
    if has_aon:
        with tabs[tab_idx]:
            try:
                render_pag3_visao_aon(campanhas_list, metricas, cores, cliente)
            except Exception as e:
                st.error(f"Erro ao carregar: {e}")
        tab_idx += 1
    
    # TAB 3: KPIs por Influenciador
    with tabs[tab_idx]:
        try:
            render_pag4_kpis_influenciador(campanhas_list, cores)
        except Exception as e:
            st.error(f"Erro ao carregar: {e}")
    tab_idx += 1
    
    # TAB 4: Top Performance
    with tabs[tab_idx]:
        try:
            render_pag5_top_performance(campanhas_list, cores)
        except Exception as e:
            st.error(f"Erro ao carregar: {e}")
    tab_idx += 1
    
    # TAB 5: Lista Influenciadores
    with tabs[tab_idx]:
        try:
            render_pag6_lista_influenciadores(campanhas_list, cores)
        except Exception as e:
            st.error(f"Erro ao carregar: {e}")
    tab_idx += 1
    
    # TAB 6: Comentarios
    with tabs[tab_idx]:
        try:
            render_comentarios(campanhas_list, cores)
        except Exception as e:
            st.error(f"Erro ao carregar: {e}")
    tab_idx += 1
    
    # TAB 7: Glossario
    with tabs[tab_idx]:
        try:
            render_glossario()
        except Exception as e:
            st.error(f"Erro ao carregar: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #9ca3af; padding: 1rem 0; font-size: 0.8rem;'>
        Relatorio gerado por <strong>AIR</strong> | Visualizacao #{token_info.get('visualizacoes', 0) + 1}
    </div>
    """, unsafe_allow_html=True)
