"""
Página: Influenciadores
Gerenciamento da base de influenciadores com integração API
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import data_manager, funcoes_auxiliares, api_client

def render():
    """Renderiza página de Influenciadores"""
    
    st.markdown('<p class="main-header">👤 Base de Influenciadores</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Gerencie influenciadores com integração à API</p>', unsafe_allow_html=True)
    
    # Tabs principais
    tab1, tab2, tab3 = st.tabs(["📋 Lista", "➕ Adicionar via API", "📊 Ranking & Métricas"])
    
    # ========================================
    # TAB 1: LISTA DE INFLUENCIADORES
    # ========================================
    with tab1:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("➕ Cadastro Manual", use_container_width=True):
                st.session_state.show_new_inf = True
        
        # FORMULÁRIO MANUAL
        if st.session_state.get('show_new_inf', False):
            with st.form("form_inf"):
                st.subheader("Cadastrar Influenciador Manualmente")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    nome = st.text_input("Nome *")
                    usuario = st.text_input("Usuário (@) *")
                    base = st.text_input("Seguidores *", placeholder="Ex: 50K, 1.2M")
                    perfil_link = st.text_input("Link Perfil")
                
                with col2:
                    st.markdown("**Redes Sociais**")
                    instagram = st.checkbox("Instagram", value=True)
                    tiktok = st.checkbox("TikTok")
                    youtube = st.checkbox("YouTube")
                    twitter = st.checkbox("Twitter/X")
                    
                    taxa_eng = st.number_input("Taxa Eng. (%)", min_value=0.0, max_value=100.0, value=0.0)
                
                with col3:
                    cidade = st.text_input("Cidade")
                    endereco = st.text_area("Endereço", height=100)
                
                redes = []
                if instagram: redes.append("Instagram")
                if tiktok: redes.append("TikTok")
                if youtube: redes.append("YouTube")
                if twitter: redes.append("Twitter/X")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Salvar", use_container_width=True):
                        if nome and usuario and redes and base:
                            data_manager.criar_influenciador_base({
                                'nome': nome,
                                'usuario': usuario,
                                'redes_sociais': redes,
                                'base_seguidores': base,
                                'perfil_link': perfil_link,
                                'taxa_engajamento': taxa_eng,
                                'cidade': cidade,
                                'endereco': endereco
                            })
                            st.session_state.show_new_inf = False
                            st.success("✅ Influenciador cadastrado!")
                            st.rerun()
                        else:
                            st.error("❌ Preencha os campos obrigatórios")
                
                with col2:
                    if st.form_submit_button("❌ Cancelar", use_container_width=True):
                        st.session_state.show_new_inf = False
                        st.rerun()
        
        st.markdown("---")
        
        # FILTROS E LISTA
        if st.session_state.influenciadores_base:
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_rede = st.multiselect("Filtrar por rede", 
                                            ["Instagram", "TikTok", "YouTube", "Twitter/X"])
            with col2:
                filtro_classe = st.multiselect("Filtrar por classificação",
                                              ["Nano", "Micro", "Mid", "Macro", "Mega"])
            with col3:
                busca_nome = st.text_input("🔍 Buscar por nome")
            
            st.markdown("---")
            
            # Lista
            for inf in st.session_state.influenciadores_base:
                # Aplicar filtros
                if filtro_rede and not any(r in inf['redes_sociais'] for r in filtro_rede):
                    continue
                if filtro_classe and inf['classificacao'] not in filtro_classe:
                    continue
                if busca_nome and busca_nome.lower() not in inf['nome'].lower():
                    continue
                
                with st.expander(f"👤 {inf['nome']} ({inf['usuario']}) - {inf['classificacao']}"):
                    col1, col2, col3 = st.columns([1, 2, 2])
                    
                    with col1:
                        if inf.get('foto'):
                            st.image(inf['foto'], width=80)
                        else:
                            st.markdown("📷 Sem foto")
                    
                    with col2:
                        st.write(f"**Redes:** {', '.join(inf['redes_sociais'])}")
                        st.write(f"**Seguidores:** {inf['base_seguidores']}")
                        st.write(f"**Classificação:** {inf['classificacao']}")
                    
                    with col3:
                        st.write(f"**Taxa Eng.:** {inf['taxa_engajamento']}%")
                        st.write(f"**Cidade:** {inf.get('cidade', '-')}")
                        if inf.get('perfil_link'):
                            st.markdown(f"[🔗 Ver Perfil]({inf['perfil_link']})")
        else:
            st.info("📋 Nenhum influenciador na base")
    
    # ========================================
    # TAB 2: ADICIONAR VIA API
    # ========================================
    with tab2:
        st.subheader("🔌 Buscar Influenciadores via API")
        st.markdown("Adicione múltiplos influenciadores de uma vez buscando na API.")
        
        # Inicializar lista de usernames na session
        if 'api_usernames' not in st.session_state:
            st.session_state.api_usernames = []
        
        st.markdown("### ➕ Adicionar Perfis para Buscar")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            novo_username = st.text_input("Username (sem @)", key="novo_user")
        
        with col2:
            nova_rede = st.selectbox("Rede Social", ["instagram", "tiktok", "youtube"], key="nova_rede")
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Adicionar à Lista", use_container_width=True):
                if novo_username:
                    st.session_state.api_usernames.append({
                        'username': novo_username.replace("@", "").strip(),
                        'network': nova_rede
                    })
                    st.success(f"✅ Adicionado: @{novo_username} ({nova_rede})")
                    st.rerun()
        
        # Mostrar lista atual
        if st.session_state.api_usernames:
            st.markdown("### 📋 Perfis na Fila")
            
            for idx, item in enumerate(st.session_state.api_usernames):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"@{item['username']} ({item['network']})")
                with col3:
                    if st.button("🗑️", key=f"remove_{idx}"):
                        st.session_state.api_usernames.pop(idx)
                        st.rerun()
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Buscar Todos na API", type="primary", use_container_width=True):
                    with st.spinner("Buscando perfis na API..."):
                        resultados = api_client.buscar_profiles_batch(st.session_state.api_usernames)
                        
                        for res in resultados:
                            if res['result'].get('success'):
                                # Processar e adicionar
                                dados = api_client.processar_dados_influenciador(res['result'])
                                if dados:
                                    data_manager.criar_influenciador_base(dados)
                                    st.success(f"✅ {res['username']} adicionado com sucesso!")
                            else:
                                st.error(f"❌ Erro ao buscar {res['username']}: {res['result'].get('error', 'Erro desconhecido')}")
                        
                        st.session_state.api_usernames = []
                        st.rerun()
            
            with col2:
                if st.button("🗑️ Limpar Lista", use_container_width=True):
                    st.session_state.api_usernames = []
                    st.rerun()
        
        # Busca individual rápida
        st.markdown("---")
        st.markdown("### 🚀 Busca Rápida Individual")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            busca_rapida = st.text_input("Username", key="busca_rap")
        
        with col2:
            rede_rapida = st.selectbox("Rede", ["instagram", "tiktok", "youtube"], key="rede_rap")
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔍 Buscar", use_container_width=True, key="btn_busca_rap"):
                if busca_rapida:
                    with st.spinner("Buscando..."):
                        resultado = api_client.buscar_profile_id(busca_rapida, rede_rapida)
                        
                        if resultado.get('success'):
                            st.success("✅ Perfil encontrado!")
                            
                            # Mostrar preview
                            dados = api_client.processar_dados_influenciador(resultado)
                            if dados:
                                col1, col2 = st.columns([1, 3])
                                with col1:
                                    if dados.get('foto'):
                                        st.image(dados['foto'], width=100)
                                with col2:
                                    st.write(f"**{dados['nome']}** ({dados['usuario']})")
                                    st.write(f"Seguidores: {dados['base_seguidores']}")
                                    st.write(f"Taxa Eng.: {dados['taxa_engajamento']}%")
                                
                                if st.button("➕ Adicionar à Base", key="add_rapido"):
                                    data_manager.criar_influenciador_base(dados)
                                    st.success("✅ Adicionado!")
                                    st.rerun()
                        else:
                            st.error(f"❌ Erro: {resultado.get('error', 'Perfil não encontrado')}")
    
    # ========================================
    # TAB 3: RANKING E MÉTRICAS
    # ========================================
    with tab3:
        st.subheader("📊 Ranking de Métricas e Desempenho")
        
        if not st.session_state.influenciadores_base:
            st.info("📋 Adicione influenciadores para ver o ranking")
            return
        
        # Calcular métricas de desempenho
        dados_ranking = []
        
        for inf in st.session_state.influenciadores_base:
            # Buscar posts em todas as campanhas
            total_views = 0
            total_int = 0
            total_posts = 0
            
            for camp in st.session_state.campanhas:
                for inf_camp in camp['influenciadores']:
                    if inf_camp.get('base_id') == inf['id']:
                        for post in inf_camp['posts']:
                            total_views += post['metricas']['views']
                            total_int += post['metricas']['interacoes']
                            total_posts += 1
            
            taxa_eng = (total_int / total_views * 100) if total_views > 0 else 0
            
            dados_ranking.append({
                'Influenciador': inf['nome'],
                'Usuario': inf['usuario'],
                'Classificação': inf['classificacao'],
                'Seguidores': inf.get('seguidores_num', 0),
                'Taxa Eng. Perfil': inf['taxa_engajamento'],
                'Views Totais': total_views,
                'Interações': total_int,
                'Taxa Eng. Real': round(taxa_eng, 2),
                'Total Posts': total_posts,
                'Foto': inf.get('foto', '')
            })
        
        df_ranking = pd.DataFrame(dados_ranking)
        
        # Selector de métrica para ordenação
        col1, col2 = st.columns(2)
        
        with col1:
            metrica_ordem = st.selectbox(
                "Ordenar por:",
                ['Seguidores', 'Views Totais', 'Taxa Eng. Real', 'Total Posts', 'Interações']
            )
        
        with col2:
            ordem = st.radio("Ordem:", ['Maior para Menor', 'Menor para Maior'], horizontal=True)
        
        ascending = ordem == 'Menor para Maior'
        df_sorted = df_ranking.sort_values(metrica_ordem, ascending=ascending)
        
        st.markdown("---")
        
        # Top 5 Ranking
        st.markdown("### 🏆 Top 5")
        
        cores = funcoes_auxiliares.get_cores_graficos()
        
        for idx, (_, row) in enumerate(df_sorted.head(5).iterrows()):
            col1, col2, col3, col4, col5, col6 = st.columns([0.5, 1, 2, 1, 1, 1])
            
            with col1:
                medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
                st.markdown(f"### {medals[idx]}")
            
            with col2:
                if row['Foto']:
                    st.image(row['Foto'], width=50)
            
            with col3:
                st.write(f"**{row['Influenciador']}**")
                st.caption(row['Usuario'])
            
            with col4:
                st.metric("Seguidores", funcoes_auxiliares.formatar_numero(row['Seguidores']))
            
            with col5:
                st.metric("Views", funcoes_auxiliares.formatar_numero(row['Views Totais']))
            
            with col6:
                st.metric("Taxa Eng.", f"{row['Taxa Eng. Real']}%")
        
        st.markdown("---")
        
        # Gráfico por Classificação
        st.markdown("### 📊 Desempenho por Classificação")
        
        df_class = df_ranking.groupby('Classificação').agg({
            'Seguidores': 'sum',
            'Views Totais': 'sum',
            'Taxa Eng. Real': 'mean',
            'Influenciador': 'count'
        }).reset_index()
        df_class.columns = ['Classificação', 'Seguidores', 'Views', 'Taxa Eng. Média', 'Qtd Influs']
        
        # Ordenar classificação
        ordem_class = ['Nano', 'Micro', 'Mid', 'Macro', 'Mega']
        df_class['ordem'] = df_class['Classificação'].apply(lambda x: ordem_class.index(x) if x in ordem_class else 99)
        df_class = df_class.sort_values('ordem')
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = go.Figure()
            
            fig1.add_trace(go.Bar(
                x=df_class['Classificação'],
                y=df_class['Views'],
                name='Views Totais',
                marker_color=cores[0]
            ))
            
            fig1.add_trace(go.Scatter(
                x=df_class['Classificação'],
                y=df_class['Taxa Eng. Média'],
                name='Taxa Eng. Média (%)',
                mode='lines+markers',
                yaxis='y2',
                line=dict(color=cores[1], width=3),
                marker=dict(size=10)
            ))
            
            fig1.update_layout(
                title='Views e Engajamento por Classificação',
                yaxis=dict(title='Views'),
                yaxis2=dict(title='Taxa Eng. (%)', overlaying='y', side='right'),
                height=400,
                legend=dict(orientation='h', yanchor='bottom', y=1.02)
            )
            
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.pie(
                df_class, 
                values='Qtd Influs', 
                names='Classificação',
                title='Distribuição de Influenciadores',
                color_discrete_sequence=cores
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("---")
        
        # Tabela completa
        st.markdown("### 📋 Tabela Completa")
        
        df_display = df_sorted[['Influenciador', 'Usuario', 'Classificação', 'Seguidores', 
                                'Views Totais', 'Taxa Eng. Real', 'Total Posts']]
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
