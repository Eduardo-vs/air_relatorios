"""
Pagina: Ajustes
"""

import streamlit as st
import json
from datetime import datetime
from utils import funcoes_auxiliares, data_manager
from pages import auth

def render():
    st.markdown('<p class="main-header">Ajustes</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Personalize o sistema</p>', unsafe_allow_html=True)
    
    # Verificar se usuario e admin para mostrar aba Usuarios
    usuario = st.session_state.get('usuario_logado', {})
    is_admin = usuario.get('role') == 'admin'
    
    if is_admin:
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Aparencia", "Classificacao de Influenciadores", "Colunas Dinamicas", "Sistema", "Usuarios"])
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["Aparencia", "Classificacao de Influenciadores", "Colunas Dinamicas", "Sistema"])
    
    with tab1:
        render_aparencia()
    
    with tab2:
        render_faixas_classificacao()
    
    with tab3:
        render_colunas_dinamicas()
    
    with tab4:
        render_sistema()
    
    if is_admin:
        with tab5:
            auth.render_gerenciar_usuarios()


def render_aparencia():
    """Configuracoes de cores e aparencia"""
    st.subheader("Cores do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nova_primary = st.color_picker("Cor Principal", value=st.session_state.primary_color)
        
        if st.button("Aplicar Cor", use_container_width=True):
            st.session_state.primary_color = nova_primary
            # Salvar no banco para persistir
            data_manager.salvar_configuracao('primary_color', nova_primary)
            st.success("Cor aplicada e salva!")
            st.rerun()
    
    with col2:
        st.markdown("**Preview:**")
        st.markdown(f"""
        <div style='background: {nova_primary}; color: white; padding: 1rem; 
                    border-radius: 8px; text-align: center; margin-bottom: 1rem;'>
            Botao Principal
        </div>
        <div style='background: {nova_primary}; opacity: 0.7; color: white; padding: 1rem; 
                    border-radius: 8px; text-align: center;'>
            Variacao
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Nano
            st.markdown("---")
            st.markdown("**Nano**")
            nano_max = st.number_input(
                "Limite maximo",
                min_value=1000,
                max_value=50000,
                value=faixas.get('nano', {}).get('max', 10000),
                step=1000,
                key="nano_max"
            )
            st.caption(f"Faixa: 1K - {nano_max:,}")
            
            # Micro
            st.markdown("---")
            st.markdown("**Micro**")
            micro_max = st.number_input(
                "Limite maximo",
                min_value=nano_max,
                max_value=100000,
                value=max(faixas.get('micro', {}).get('max', 50000), nano_max),
                step=5000,
                key="micro_max"
            )
            st.caption(f"Faixa: {nano_max:,} - {micro_max:,}")
            
            # Inter 1
            st.markdown("---")
            st.markdown("**Inter 1**")
            inter1_max = st.number_input(
                "Limite maximo",
                min_value=micro_max,
                max_value=500000,
                value=max(faixas.get('inter1', {}).get('max', 250000), micro_max),
                step=10000,
                key="inter1_max"
            )
            st.caption(f"Faixa: {micro_max:,} - {inter1_max:,}")
            
            # Inter 2
            st.markdown("---")
            st.markdown("**Inter 2**")
            inter2_max = st.number_input(
                "Limite maximo",
                min_value=inter1_max,
                max_value=1000000,
                value=max(faixas.get('inter2', {}).get('max', 500000), inter1_max),
                step=50000,
                key="inter2_max"
            )
            st.caption(f"Faixa: {inter1_max:,} - {inter2_max:,}")
        
        with col2:
            # Macro
            st.markdown("---")
            st.markdown("**Macro**")
            macro_max = st.number_input(
                "Limite maximo",
                min_value=inter2_max,
                max_value=5000000,
                value=max(faixas.get('macro', {}).get('max', 1000000), inter2_max),
                step=100000,
                key="macro_max"
            )
            st.caption(f"Faixa: {inter2_max:,} - {macro_max:,}")
            
            # Mega 1
            st.markdown("---")
            st.markdown("**Mega 1**")
            mega1_max = st.number_input(
                "Limite maximo",
                min_value=macro_max,
                max_value=10000000,
                value=max(faixas.get('mega1', {}).get('max', 5000000), macro_max),
                step=500000,
                key="mega1_max"
            )
            st.caption(f"Faixa: {macro_max:,} - {mega1_max:,}")
            
            # Mega 2
            st.markdown("---")
            st.markdown("**Mega 2**")
            mega2_max = st.number_input(
                "Limite maximo",
                min_value=mega1_max,
                max_value=50000000,
                value=max(faixas.get('mega2', {}).get('max', 10000000), mega1_max),
                step=1000000,
                key="mega2_max"
            )
            st.caption(f"Faixa: {mega1_max:,} - {mega2_max:,}")
            
            # Super Mega
            st.markdown("---")
            st.markdown("**Super Mega**")
            st.info(f"Acima de {mega2_max:,} seguidores")
        
        st.markdown("---")
        
        if st.form_submit_button("Salvar Faixas", type="primary", use_container_width=True):
            novas_faixas = {
                'nano': {'min': 1000, 'max': nano_max},
                'micro': {'min': nano_max, 'max': micro_max},
                'inter1': {'min': micro_max, 'max': inter1_max},
                'inter2': {'min': inter1_max, 'max': inter2_max},
                'macro': {'min': inter2_max, 'max': macro_max},
                'mega1': {'min': macro_max, 'max': mega1_max},
                'mega2': {'min': mega1_max, 'max': mega2_max},
                'supermega': {'min': mega2_max, 'max': 999999999}
            }
            
            data_manager.salvar_faixas_classificacao(novas_faixas)
            st.success("Faixas salvas!")
            st.rerun()
    
    # Visualizacao das faixas atuais
    st.markdown("---")
    st.markdown("### Resumo das Faixas Atuais")
    
    faixas_atuais = data_manager.get_faixas_classificacao()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style='background: #22c55e; color: white; padding: 0.8rem; border-radius: 8px; text-align: center; margin-bottom: 0.5rem;'>
            <strong>Nano</strong><br>
            <small>1K - {max:,}</small>
        </div>
        """.format(max=faixas_atuais['nano']['max']), unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background: #3b82f6; color: white; padding: 0.8rem; border-radius: 8px; text-align: center;'>
            <strong>Micro</strong><br>
            <small>{min:,} - {max:,}</small>
        </div>
        """.format(min=faixas_atuais['micro']['min'], max=faixas_atuais['micro']['max']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: #8b5cf6; color: white; padding: 0.8rem; border-radius: 8px; text-align: center; margin-bottom: 0.5rem;'>
            <strong>Inter 1</strong><br>
            <small>{min:,} - {max:,}</small>
        </div>
        """.format(min=faixas_atuais['inter1']['min'], max=faixas_atuais['inter1']['max']), unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background: #a855f7; color: white; padding: 0.8rem; border-radius: 8px; text-align: center;'>
            <strong>Inter 2</strong><br>
            <small>{min:,} - {max:,}</small>
        </div>
        """.format(min=faixas_atuais['inter2']['min'], max=faixas_atuais['inter2']['max']), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background: #f97316; color: white; padding: 0.8rem; border-radius: 8px; text-align: center; margin-bottom: 0.5rem;'>
            <strong>Macro</strong><br>
            <small>{min:,} - {max:,}</small>
        </div>
        """.format(min=faixas_atuais['macro']['min'], max=faixas_atuais['macro']['max']), unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background: #ef4444; color: white; padding: 0.8rem; border-radius: 8px; text-align: center;'>
            <strong>Mega 1</strong><br>
            <small>{min:,} - {max:,}</small>
        </div>
        """.format(min=faixas_atuais['mega1']['min'], max=faixas_atuais['mega1']['max']), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style='background: #dc2626; color: white; padding: 0.8rem; border-radius: 8px; text-align: center; margin-bottom: 0.5rem;'>
            <strong>Mega 2</strong><br>
            <small>{min:,} - {max:,}</small>
        </div>
        """.format(min=faixas_atuais['mega2']['min'], max=faixas_atuais['mega2']['max']), unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background: #991b1b; color: white; padding: 0.8rem; border-radius: 8px; text-align: center;'>
            <strong>Super Mega</strong><br>
            <small>{min:,}+</small>
        </div>
        """.format(min=faixas_atuais['supermega']['min']), unsafe_allow_html=True)


def render_sistema():
    """Estatisticas e backup do sistema"""
    
    # Diagnostico de banco de dados
    data_manager.diagnostico_db()
    
    st.markdown("---")
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
                'version': '5.1'
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


def render_colunas_dinamicas():
    """Gerenciar colunas dinamicas para categorizar influenciadores"""
    
    st.subheader("Colunas Dinamicas")
    st.caption("Crie colunas personalizadas para categorizar influenciadores (ex: Tipo de Cabelo, Faixa Etaria, Tom de Pele)")
    
    # Buscar colunas existentes
    colunas = data_manager.get_colunas_dinamicas()
    
    # Criar nova coluna
    st.markdown("---")
    st.markdown("**Criar Nova Coluna**")
    
    with st.form("form_nova_coluna"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome_coluna = st.text_input("Nome da Coluna", placeholder="Ex: Tipo de Cabelo")
        with col2:
            descricao_coluna = st.text_input("Descricao (opcional)", placeholder="Ex: Classificacao por tipo de cabelo")
        
        opcoes_coluna = st.text_input(
            "Opcoes (separadas por virgula)", 
            placeholder="Ex: Liso, Ondulado, Cacheado, Crespo",
            help="Deixe vazio para permitir texto livre"
        )
        
        if st.form_submit_button("Criar Coluna", type="primary"):
            if nome_coluna:
                opcoes_lista = [o.strip() for o in opcoes_coluna.split(',') if o.strip()] if opcoes_coluna else []
                coluna_id = data_manager.criar_coluna_dinamica(nome_coluna, descricao_coluna, opcoes_lista)
                if coluna_id:
                    st.success(f"Coluna '{nome_coluna}' criada!")
                    st.rerun()
                else:
                    st.error("Erro ao criar coluna")
            else:
                st.warning("Informe o nome da coluna")
    
    # Listar colunas existentes
    if colunas:
        st.markdown("---")
        st.markdown(f"**Colunas Cadastradas ({len(colunas)})**")
        
        for col in colunas:
            with st.expander(f"{col['nome']}", expanded=False):
                st.caption(col.get('descricao', '') or 'Sem descricao')
                
                # Mostrar opcoes
                opcoes = col.get('opcoes', [])
                if opcoes:
                    st.markdown(f"**Opcoes:** {', '.join(opcoes)}")
                else:
                    st.caption("Texto livre (sem opcoes pre-definidas)")
                
                # Valores em uso
                valores_usados = data_manager.get_valores_unicos_coluna(col['id'])
                if valores_usados:
                    st.markdown(f"**Valores em uso:** {', '.join(valores_usados[:10])}" + ("..." if len(valores_usados) > 10 else ""))
                
                # Editar
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Editar", key=f"edit_col_{col['id']}"):
                        st.session_state[f"editing_col_{col['id']}"] = True
                        st.rerun()
                with col2:
                    if st.button(f"Excluir", key=f"del_col_{col['id']}"):
                        data_manager.excluir_coluna_dinamica(col['id'])
                        st.success("Coluna excluida!")
                        st.rerun()
                
                # Form de edicao
                if st.session_state.get(f"editing_col_{col['id']}"):
                    with st.form(f"form_edit_col_{col['id']}"):
                        novo_nome = st.text_input("Nome", value=col['nome'])
                        nova_desc = st.text_input("Descricao", value=col.get('descricao', ''))
                        novas_opcoes = st.text_input(
                            "Opcoes (separadas por virgula)", 
                            value=', '.join(opcoes) if opcoes else ''
                        )
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.form_submit_button("Salvar", type="primary"):
                                opcoes_lista = [o.strip() for o in novas_opcoes.split(',') if o.strip()] if novas_opcoes else []
                                data_manager.atualizar_coluna_dinamica(col['id'], {
                                    'nome': novo_nome,
                                    'descricao': nova_desc,
                                    'opcoes': opcoes_lista
                                })
                                st.session_state[f"editing_col_{col['id']}"] = False
                                st.success("Coluna atualizada!")
                                st.rerun()
                        with col_b:
                            if st.form_submit_button("Cancelar"):
                                st.session_state[f"editing_col_{col['id']}"] = False
                                st.rerun()
    else:
        st.info("Nenhuma coluna dinamica cadastrada. Crie a primeira acima!")
