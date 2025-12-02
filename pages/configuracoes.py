"""
Pagina: Configuracoes
"""

import streamlit as st
import json
from datetime import datetime
from utils import funcoes_auxiliares, data_manager

def render():
    st.markdown('<p class="main-header">Configuracoes</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Personalize o sistema</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Aparencia", "Classificacao de Influenciadores", "Banco de Dados", "Sistema"])
    
    with tab1:
        render_aparencia()
    
    with tab2:
        render_faixas_classificacao()
    
    with tab3:
        render_banco_dados()
    
    with tab4:
        render_sistema()


def render_aparencia():
    """Configuracoes de cores e aparencia"""
    st.subheader("Cores do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nova_primary = st.color_picker("Cor Principal", value=st.session_state.primary_color)
        nova_secondary = st.color_picker("Cor Secundaria", value=st.session_state.secondary_color)
        
        if st.button("Aplicar Cores", use_container_width=True):
            st.session_state.primary_color = nova_primary
            st.session_state.secondary_color = nova_secondary
            st.success("Cores aplicadas!")
            st.rerun()
    
    with col2:
        st.markdown("**Preview:**")
        st.markdown(f"""
        <div style='background: {nova_primary}; color: white; padding: 1rem; 
                    border-radius: 8px; text-align: center; margin-bottom: 1rem;'>
            Botao Principal
        </div>
        <div style='background: {nova_secondary}; color: white; padding: 1rem; 
                    border-radius: 8px; text-align: center;'>
            Elemento Secundario
        </div>
        """, unsafe_allow_html=True)


def render_faixas_classificacao():
    """Configurar faixas de classificacao de influenciadores"""
    st.subheader("Faixas de Classificacao de Influenciadores")
    st.caption("Configure os limites de seguidores para cada classificacao")
    
    # Obter faixas atuais
    faixas = data_manager.get_faixas_classificacao()
    
    with st.form("form_faixas"):
        st.markdown("**Defina o limite maximo de seguidores para cada faixa:**")
        st.caption("Os influenciadores serao classificados automaticamente com base nestas faixas")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Nano
            st.markdown("---")
            st.markdown("### 🟢 Nano")
            nano_max = st.number_input(
                "Limite maximo de seguidores",
                min_value=1000,
                max_value=100000,
                value=faixas.get('nano', {}).get('max', 10000),
                step=1000,
                key="nano_max",
                help="Influenciadores com ate este numero de seguidores serao classificados como Nano"
            )
            st.caption(f"Faixa: 0 - {nano_max:,} seguidores")
            
            # Micro
            st.markdown("---")
            st.markdown("### 🔵 Micro")
            micro_max = st.number_input(
                "Limite maximo de seguidores",
                min_value=nano_max + 1,
                max_value=500000,
                value=max(faixas.get('micro', {}).get('max', 100000), nano_max + 1),
                step=10000,
                key="micro_max",
                help="Influenciadores entre Nano e este numero serao classificados como Micro"
            )
            st.caption(f"Faixa: {nano_max:,} - {micro_max:,} seguidores")
            
            # Mid
            st.markdown("---")
            st.markdown("### 🟣 Mid")
            mid_max = st.number_input(
                "Limite maximo de seguidores",
                min_value=micro_max + 1,
                max_value=2000000,
                value=max(faixas.get('mid', {}).get('max', 500000), micro_max + 1),
                step=50000,
                key="mid_max",
                help="Influenciadores entre Micro e este numero serao classificados como Mid"
            )
            st.caption(f"Faixa: {micro_max:,} - {mid_max:,} seguidores")
            
            # Macro
            st.markdown("---")
            st.markdown("### 🟠 Macro")
            macro_max = st.number_input(
                "Limite maximo de seguidores",
                min_value=mid_max + 1,
                max_value=10000000,
                value=max(faixas.get('macro', {}).get('max', 1000000), mid_max + 1),
                step=100000,
                key="macro_max",
                help="Influenciadores entre Mid e este numero serao classificados como Macro"
            )
            st.caption(f"Faixa: {mid_max:,} - {macro_max:,} seguidores")
            
            # Mega
            st.markdown("---")
            st.markdown("### 🔴 Mega")
            st.info(f"Influenciadores com mais de {macro_max:,} seguidores serao classificados como Mega")
        
        st.markdown("---")
        
        if st.form_submit_button("Salvar Faixas", type="primary", use_container_width=True):
            novas_faixas = {
                'nano': {'min': 0, 'max': nano_max},
                'micro': {'min': nano_max, 'max': micro_max},
                'mid': {'min': micro_max, 'max': mid_max},
                'macro': {'min': mid_max, 'max': macro_max},
                'mega': {'min': macro_max, 'max': 999999999}
            }
            
            data_manager.salvar_faixas_classificacao(novas_faixas)
            st.success("Faixas salvas com sucesso!")
            st.rerun()
    
    # Visualizacao das faixas atuais
    st.markdown("---")
    st.markdown("### Resumo das Faixas Atuais")
    
    faixas_atuais = data_manager.get_faixas_classificacao()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown("""
        <div style='background: #22c55e; color: white; padding: 1rem; border-radius: 8px; text-align: center;'>
            <strong>Nano</strong><br>
            0 - {nano:,}
        </div>
        """.format(nano=faixas_atuais['nano']['max']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: #3b82f6; color: white; padding: 1rem; border-radius: 8px; text-align: center;'>
            <strong>Micro</strong><br>
            {min:,} - {max:,}
        </div>
        """.format(min=faixas_atuais['micro']['min'], max=faixas_atuais['micro']['max']), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background: #8b5cf6; color: white; padding: 1rem; border-radius: 8px; text-align: center;'>
            <strong>Mid</strong><br>
            {min:,} - {max:,}
        </div>
        """.format(min=faixas_atuais['mid']['min'], max=faixas_atuais['mid']['max']), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style='background: #f97316; color: white; padding: 1rem; border-radius: 8px; text-align: center;'>
            <strong>Macro</strong><br>
            {min:,} - {max:,}
        </div>
        """.format(min=faixas_atuais['macro']['min'], max=faixas_atuais['macro']['max']), unsafe_allow_html=True)
    
    with col5:
        st.markdown("""
        <div style='background: #ef4444; color: white; padding: 1rem; border-radius: 8px; text-align: center;'>
            <strong>Mega</strong><br>
            {min:,}+
        </div>
        """.format(min=faixas_atuais['mega']['min']), unsafe_allow_html=True)


def render_banco_dados():
    """Configuracao de banco de dados"""
    st.subheader("Configuracao de Banco de Dados")
    
    st.markdown("""
    ### Como funciona?
    
    O sistema usa **SQLite** por padrao, salvando os dados em um arquivo local.
    Os dados sao persistidos automaticamente.
    
    ---
    
    ### Opcao alternativa: PostgreSQL (para producao em nuvem)
    
    **Sites gratuitos para testar PostgreSQL:**
    
    1. **Neon** (https://neon.tech) - 500MB gratis, mais rapido
    2. **Supabase** (https://supabase.com) - 500MB gratis
    3. **Railway** (https://railway.app) - $5/mes de credito gratis
    
    **Como configurar (exemplo Neon):**
    
    1. Crie uma conta em https://neon.tech
    2. Crie um novo projeto
    3. Copie a connection string
    4. Configure a variavel de ambiente:
       ```
       DATABASE_URL=postgresql://user:pass@host/database
       ```
    
    **No Streamlit Cloud:**
    - Va em Settings > Secrets
    - Adicione: `DATABASE_URL = "sua_connection_string"`
    """)
    
    st.markdown("---")
    st.markdown("**Status atual:**")
    
    import os
    db_url = os.getenv('DATABASE_URL', '')
    
    if 'postgresql' in db_url.lower():
        st.success("Conectado ao PostgreSQL")
        st.code(db_url[:50] + "..." if len(db_url) > 50 else db_url)
    elif 'sqlite' in db_url.lower():
        st.info("Usando SQLite (dados persistidos localmente)")
        st.code(db_url)
    else:
        st.info("Usando SQLite local (dados persistidos em data/air_relatorios.db)")


def render_sistema():
    """Estatisticas e backup do sistema"""
    st.subheader("Estatisticas do Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Clientes", len(data_manager.get_clientes()))
        st.metric("Campanhas", len(data_manager.get_campanhas()))
    
    with col2:
        st.metric("Influenciadores", len(data_manager.get_influenciadores()))
        total_posts = 0
        for c in data_manager.get_campanhas():
            for inf in c.get('influenciadores', []):
                total_posts += len(inf.get('posts', []))
        st.metric("Posts", total_posts)
    
    with col3:
        aon = len([c for c in data_manager.get_campanhas() if c.get('is_aon')])
        st.metric("Campanhas AON", aon)
    
    st.markdown("---")
    st.subheader("Backup e Restauracao")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Exportar Backup (JSON)", use_container_width=True):
            backup = {
                'clientes': data_manager.get_clientes(),
                'influenciadores': data_manager.get_influenciadores(),
                'campanhas': data_manager.get_campanhas(),
                'faixas_classificacao': data_manager.get_faixas_classificacao(),
                'export_date': datetime.now().isoformat(),
                'version': '5.0'
            }
            
            json_data = json.dumps(backup, indent=2, ensure_ascii=False).encode('utf-8')
            st.download_button(
                "Download Backup",
                data=json_data,
                file_name=f"air_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        uploaded = st.file_uploader("Importar Backup", type=['json'])
        if uploaded:
            try:
                backup = json.loads(uploaded.read().decode('utf-8'))
                st.info(f"Backup de {backup.get('export_date', 'data desconhecida')} - Versao {backup.get('version', '?')}")
                
                if st.button("Restaurar", type="primary"):
                    # Restaurar dados
                    for cliente in backup.get('clientes', []):
                        data_manager.criar_cliente(cliente)
                    
                    for inf in backup.get('influenciadores', []):
                        data_manager.criar_influenciador(inf)
                    
                    for camp in backup.get('campanhas', []):
                        data_manager.criar_campanha(camp)
                    
                    if backup.get('faixas_classificacao'):
                        data_manager.salvar_faixas_classificacao(backup['faixas_classificacao'])
                    
                    st.success("Backup restaurado!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao ler backup: {e}")
    
    st.markdown("---")
    st.subheader("Limpar Dados")
    
    st.warning("Cuidado! Esta acao ira apagar todos os dados.")
    
    if st.button("Limpar Todos os Dados", type="secondary"):
        st.session_state.confirmar_limpeza = True
    
    if st.session_state.get('confirmar_limpeza'):
        st.error("Tem certeza? Esta acao nao pode ser desfeita!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sim, limpar tudo", type="primary"):
                # Limpar banco
                conn = data_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM campanhas")
                cursor.execute("DELETE FROM influenciadores")
                cursor.execute("DELETE FROM clientes")
                conn.commit()
                conn.close()
                
                st.session_state.confirmar_limpeza = False
                st.success("Dados limpos!")
                st.rerun()
        with col2:
            if st.button("Cancelar"):
                st.session_state.confirmar_limpeza = False
                st.rerun()
