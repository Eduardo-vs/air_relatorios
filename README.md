# 📊 AIR Relatórios v4.1 - Sistema Completo

## 🚀 Novidades da Versão 4.1

### Integração com API
- **Busca de Perfis via API**: Endpoint para buscar ID do perfil
- **Dados Completos do Perfil**: Endpoint para dados detalhados
- **Inserção em Lote**: Adicione múltiplos influenciadores de uma vez

### Melhorias Solicitadas

#### 📊 Relatório - Página 1 (Big Numbers)
- ✅ Total de influenciadores adicionado
- ✅ Total de seguidores adicionado
- ✅ Alcance adicionado
- ✅ Filtro por Views/Alcance/Interações/Impressões
- ✅ Gráfico de barras com percentual por formato (removido pizza)
- ✅ Gráfico RADAR para performance por tamanho de influenciador
- ✅ Campo de notas/escrita livre

#### 📈 Relatório - Página 2 (Gráficos AON)
- ✅ Gráficos combinados com barra + linha
- ✅ Cores mais vibrantes nos gráficos

#### 🏆 Relatório - Página 3 (Top Conteúdo)
- ✅ Tabela melhorada com foto e link do conteúdo
- ✅ Ordenação por Taxa de Engajamento e Taxa de Alcance
- ✅ Visualização de mídias dos posts

#### 👤 Relatório - Página 4 (Influenciadores)
- ✅ Ranking de métricas
- ✅ Desempenho por classificação
- ✅ Gráficos combinados barra + linha

#### 🔧 Outras Melhorias
- ✅ **AON por Campanha**: Agora é configurado por campanha, não mais por cliente
- ✅ **Filtros Globais**: Cliente, campanha e janela de data em todas as páginas
- ✅ **Relatório por Cliente**: Métricas agrupadas por cliente
- ✅ Novas métricas: Alcance e Impressões

## 📁 Estrutura do Projeto

```
air_relatorios/
├── app.py                          # Arquivo principal
├── requirements.txt                # Dependências
├── .gitignore
├── .streamlit/
│   └── config.toml                 # Configurações do Streamlit
├── utils/
│   ├── __init__.py
│   ├── api_client.py               # 🆕 Cliente API para endpoints
│   ├── data_manager.py             # Gerenciamento de dados
│   └── funcoes_auxiliares.py       # Funções auxiliares
└── pages/
    ├── __init__.py
    ├── dashboard.py                # Dashboard geral
    ├── clientes.py                 # Gestão de clientes
    ├── influenciadores.py          # 🔄 Com integração API
    ├── campanhas.py                # 🔄 Com AON por campanha
    ├── configuracoes.py            # Configurações
    └── campanha/
        ├── __init__.py
        └── relatorio_completo.py   # 🔄 Relatório completo melhorado
```

## 🔌 Endpoints da API

### 1. Buscar ID do Perfil
```
GET https://n8n.air.com.vc/webhook/2e7956e8-2f15-497d-9a10-efb21038d5e5
Query: username=casaldr_ofc&network=instagram
```

### 2. Buscar Dados Completos
```
POST https://n8n.air.com.vc/webhook-test/5246e807-0d6a-44aa-935a-88a26d831428
Body: {"profiles": ["profile_id_1", "profile_id_2"]}
```

## 🎯 Como Usar a Integração com API

1. Vá para **Influenciadores** → **Adicionar via API**
2. Digite o username (sem @) e selecione a rede
3. Adicione à lista ou faça busca rápida
4. Clique em **Buscar Todos na API**
5. Os influenciadores serão adicionados automaticamente à base

## 📊 Métricas Disponíveis

### Básicas
- Views, Alcance, Impressões
- Interações, Curtidas, Comentários
- Compartilhamentos, Saves

### Calculadas
- Taxa de Engajamento (%)
- Taxa de Alcance (%)
- AIR Score (0-100)

### Condicionais
- Cliques em Link (só Stories)
- Conversões de Cupom

## 🔷 Campanhas AON

Campanhas marcadas como **AON** têm acesso a:
- 📈 Gráficos de evolução temporal
- 🔍 Filtros avançados de período
- 📊 Análise por influenciador ao longo do tempo
- 📉 Dados acumulados e diários

## 🚀 Como Executar

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar
streamlit run app.py
```

## 📦 Dependências

```
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.17.0
fpdf>=1.7.2
requests>=2.31.0
Pillow>=10.0.0
```

## 🔄 Changelog v4.1

### Adicionado
- Integração com endpoints da API para busca de perfis
- Inserção em lote de influenciadores
- Métricas de Alcance e Impressões
- Gráfico Radar para performance por classificação
- Campo de notas/observações nas campanhas
- AON configurável por campanha
- Filtros globais de cliente, campanha e data
- Relatório agrupado por cliente

### Melhorado
- Gráficos com cores mais vibrantes
- Gráficos combinados (barra + linha)
- Tabela de top conteúdo com fotos e links
- Ranking de métricas na página de influenciadores
- Performance por classificação

### Removido
- Gráfico de pizza de distribuição (substituído por barras com %)
- AON por cliente (agora é por campanha)

---

**Versão:** 4.1
**Última atualização:** 2025
