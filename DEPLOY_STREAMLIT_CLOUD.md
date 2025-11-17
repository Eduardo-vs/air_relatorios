# 🚀 Guia de Deploy no Streamlit Cloud

## ❌ Problema: "No module named pages"

Este erro acontece porque o Streamlit Cloud tem algumas particularidades. Aqui está a solução completa:

---

## ✅ SOLUÇÃO 1: Estrutura de Arquivos Correta

Certifique-se de que sua estrutura está assim:

```
air_relatorios/
├── app.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── utils/
│   ├── __init__.py          ✅ IMPORTANTE
│   ├── funcoes_auxiliares.py
│   └── data_manager.py
└── pages/
    ├── __init__.py           ✅ IMPORTANTE
    ├── dashboard.py
    ├── clientes.py
    ├── influenciadores.py
    ├── campanhas.py
    ├── configuracoes.py
    └── campanha/
        ├── __init__.py       ✅ IMPORTANTE
        └── relatorio_completo.py
```

---

## ✅ SOLUÇÃO 2: Arquivos __init__.py

Todos os arquivos `__init__.py` já foram criados corretamente no ZIP.

### Conteúdo do `utils/__init__.py`:
```python
from utils import funcoes_auxiliares
from utils import data_manager

__all__ = ['funcoes_auxiliares', 'data_manager']
```

### Conteúdo do `pages/__init__.py`:
```python
from pages import dashboard
from pages import clientes
from pages import influenciadores
from pages import campanhas
from pages import configuracoes

__all__ = ['dashboard', 'clientes', 'influenciadores', 'campanhas', 'configuracoes']
```

### Conteúdo do `pages/campanha/__init__.py`:
```python
from pages.campanha import relatorio_completo

__all__ = ['relatorio_completo']
```

---

## ✅ SOLUÇÃO 3: requirements.txt

Certifique-se de que o arquivo `requirements.txt` existe e contém:

```txt
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.17.0
fpdf>=1.7.2
```

---

## ✅ SOLUÇÃO 4: Passo a Passo no Streamlit Cloud

### 1️⃣ Preparar o Repositório

**Opção A: GitHub**
```bash
# Na sua máquina local
cd air_relatorios
git init
git add .
git commit -m "Initial commit - AIR Relatórios v4.0"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/air-relatorios.git
git push -u origin main
```

**Opção B: Upload direto**
- Extraia o ZIP
- Faça upload dos arquivos diretamente no GitHub/GitLab

### 2️⃣ Deploy no Streamlit Cloud

1. Acesse: https://share.streamlit.io/
2. Clique em "New app"
3. Conecte seu repositório GitHub
4. Configure:
   - **Repository**: seu-usuario/air-relatorios
   - **Branch**: main
   - **Main file path**: app.py
5. Clique em "Deploy!"

### 3️⃣ Aguarde o Deploy
- O Streamlit Cloud irá:
  - Instalar dependências do requirements.txt
  - Executar o app.py
  - Disponibilizar a URL

---

## ✅ SOLUÇÃO 5: Se Ainda Assim Não Funcionar

Se o erro persistir, use esta versão alternativa do `app.py`:

### Substitua o início do app.py por:

```python
import streamlit as st
from datetime import datetime
import json
import sys
import os

# Adicionar diretório ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Imports com tratamento de erro
try:
    import pages.dashboard as dashboard
    import pages.clientes as clientes
    import pages.influenciadores as influenciadores
    import pages.campanhas as campanhas
    import pages.configuracoes as configuracoes
    import pages.campanha.relatorio_completo as relatorio_completo
    import utils.funcoes_auxiliares as funcoes_auxiliares
    import utils.data_manager as data_manager
except ImportError as e:
    st.error(f"❌ Erro ao importar módulos: {e}")
    st.info("Verifique se todos os arquivos __init__.py existem")
    st.stop()

# ... resto do código continua igual
```

---

## ✅ SOLUÇÃO 6: Teste Local Antes de Deploy

Antes de fazer deploy, teste localmente:

```bash
# 1. Extrair o ZIP
unzip air_relatorios_v4_COMPLETO.zip
cd air_relatorios

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar localmente
streamlit run app.py

# 4. Se funcionar local, deve funcionar no Cloud
```

---

## ✅ SOLUÇÃO 7: Verificar Logs no Streamlit Cloud

Se o erro aparecer no deploy:

1. No Streamlit Cloud, clique em "Manage app"
2. Veja os logs em tempo real
3. Procure por mensagens de erro específicas
4. Copie o erro exato e me envie

---

## 🆘 SOLUÇÃO ALTERNATIVA: Arquivo Único

Se NADA funcionar, posso criar uma versão em arquivo único (sem módulos):

```
air_relatorios_single/
└── app.py  (um único arquivo com tudo)
```

Esta versão é mais simples para deploy mas menos organizada.

**Quer que eu crie essa versão?**

---

## 📋 Checklist de Verificação

Antes de fazer deploy, verifique:

- [ ] Todos os arquivos `__init__.py` existem
- [ ] `requirements.txt` existe e está correto
- [ ] Estrutura de pastas está correta
- [ ] Funciona localmente com `streamlit run app.py`
- [ ] Repositório GitHub está atualizado
- [ ] Branch correta selecionada no Streamlit Cloud

---

## 💡 Dicas Adicionais

1. **Cache do Streamlit Cloud**: Às vezes precisa limpar o cache
   - No Streamlit Cloud: Manage app → Reboot app

2. **Versões do Python**: O Streamlit Cloud usa Python 3.9+
   - Certifique-se de que seu código é compatível

3. **Arquivos grandes**: Se tiver uploads grandes
   - Configure `.gitignore` para não enviar arquivos temporários

---

## 🎯 Resultado Esperado

Após seguir estes passos, seu app deve:
- ✅ Fazer deploy sem erros
- ✅ Carregar todas as páginas
- ✅ Funcionar completamente
- ✅ Estar acessível via URL pública

---

**Precisa de ajuda com algum passo específico?**
