# Scouting Dashboard | Botafogo-SP

Dashboard de scouting profissional com visualizações estilo Wyscout.

## 🚀 Deploy no Streamlit Cloud (Gratuito)

### Passo 1: Criar repositório no GitHub

1. Acesse [github.com](https://github.com) e faça login
2. Clique em **"New repository"** (botão verde)
3. Nome: `scouting-dashboard`
4. Deixe como **Public**
5. Clique em **"Create repository"**

### Passo 2: Upload dos arquivos

No repositório criado:

1. Clique em **"uploading an existing file"**
2. Arraste os arquivos:
   - `app.py`
   - `requirements.txt`
   - `Banco_de_Dados___Jogadores-2.xlsx` (opcional - pode carregar depois)
3. Clique em **"Commit changes"**

### Passo 3: Deploy no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Faça login com sua conta GitHub
3. Clique em **"New app"**
4. Selecione:
   - **Repository:** `seu-usuario/scouting-dashboard`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. Clique em **"Deploy!"**

⏱️ Aguarde 2-3 minutos. Seu dashboard estará online em:
```
https://seu-usuario-scouting-dashboard.streamlit.app
```

---

## 🖥️ Rodar Localmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar
streamlit run app.py
```

---

## 📊 Funcionalidades

- **Perfil Individual:** Radar de atributos + percentis estilo Wyscout
- **Comparativo:** Scatter plot + comparação entre jogadores
- **Dados Físicos:** Métricas SkillCorner com radar de rankings
- **Base de Dados:** Visualização e exportação CSV

---

## 🎨 Personalização

As cores podem ser ajustadas no dicionário `COLORS` no início do `app.py`:

```python
COLORS = {
    'accent': '#dc2626',      # Cor principal (vermelho)
    'elite': '#22c55e',       # Verde (P90+)
    'above_avg': '#eab308',   # Amarelo (P65-89)
    'average': '#f97316',     # Laranja (P36-64)
    'below_avg': '#ef4444',   # Vermelho (P0-35)
}
```

---

## 📁 Estrutura

```
scouting-dashboard/
├── app.py                              # Aplicação principal
├── requirements.txt                    # Dependências
├── Banco_de_Dados___Jogadores-2.xlsx   # Dados (opcional)
└── README.md                           # Instruções
```

---

**Desenvolvido para Botafogo SA Ribeirão Preto**
