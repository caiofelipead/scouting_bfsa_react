import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# ============================================
# CONFIG
# ============================================
st.set_page_config(
    page_title="Scouting Dashboard | Botafogo-SP",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CORES
# ============================================
COLORS = {
    'bg': '#000000',
    'card': '#111118',
    'accent': '#dc2626',
    'text': '#ffffff',
    'text_secondary': '#9ca3af',
    'text_muted': '#6b7280',
    'border': 'rgba(255,255,255,0.1)',
    'elite': '#22c55e',
    'above': '#eab308',
    'average': '#f97316',
    'below': '#ef4444',
}

# ============================================
# CSS
# ============================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* FORÇAR FUNDO PRETO EM TUDO */
    .stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stHeader"], 
    [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
    .block-container, section[data-testid="stSidebar"] > div {{
        background-color: {COLORS['bg']} !important;
    }}
    
    .main {{ font-family: 'Inter', sans-serif; }}
    [data-testid="stSidebar"] {{ background: #0a0a0d !important; }}
    [data-testid="stSidebar"] > div {{ background: #0a0a0d !important; }}
    
    .stTabs [data-baseweb="tab-list"] {{ gap: 0; background: {COLORS['card']}; border-radius: 10px; padding: 4px; }}
    .stTabs [data-baseweb="tab"] {{ background: transparent; color: {COLORS['text_muted']}; font-weight: 500; border-radius: 8px; padding: 8px 16px; }}
    .stTabs [aria-selected="true"] {{ background: {COLORS['accent']} !important; color: white !important; }}
    
    /* Forçar textos brancos */
    h1, h2, h3, h4, h5, h6 {{ font-family: 'Inter', sans-serif; color: #ffffff !important; }}
    p, label {{ color: #ffffff !important; }}
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown p {{ color: #ffffff !important; }}
    [data-testid="stSubheader"] {{ color: #ffffff !important; }}
    
    /* SELECTBOX - CORRIGIDO */
    .stSelectbox label {{ color: #ffffff !important; }}
    .stSelectbox > div > div {{ background-color: {COLORS['card']} !important; }}
    .stSelectbox [data-baseweb="select"] {{ background-color: {COLORS['card']} !important; }}
    .stSelectbox [data-baseweb="select"] > div {{ background-color: {COLORS['card']} !important; color: #ffffff !important; }}
    
    /* Dropdown menu options */
    [data-baseweb="menu"] {{ background-color: {COLORS['card']} !important; }}
    [data-baseweb="menu"] li {{ background-color: {COLORS['card']} !important; color: #ffffff !important; }}
    [data-baseweb="menu"] li:hover {{ background-color: #2a2a35 !important; }}
    [role="listbox"] {{ background-color: {COLORS['card']} !important; }}
    [role="option"] {{ color: #ffffff !important; background-color: {COLORS['card']} !important; }}
    [role="option"]:hover {{ background-color: #2a2a35 !important; }}
    ul[data-testid="stSelectboxVirtualDropdown"] {{ background-color: {COLORS['card']} !important; }}
    ul[data-testid="stSelectboxVirtualDropdown"] li {{ color: #ffffff !important; }}
    
    /* Radio buttons */
    .stRadio label {{ color: #ffffff !important; }}
    .stRadio [data-baseweb="radio"] {{ background-color: {COLORS['card']} !important; }}
    
    /* Text input */
    .stTextInput label {{ color: #ffffff !important; }}
    .stTextInput input {{ background-color: {COLORS['card']} !important; color: #ffffff !important; }}
    
    /* Expander */
    .streamlit-expanderHeader {{ color: #ffffff !important; background: {COLORS['card']} !important; }}
    .streamlit-expanderContent {{ background: {COLORS['card']} !important; }}
    
    /* File uploader */
    [data-testid="stFileUploader"] {{ background: {COLORS['card']}; border-radius: 8px; }}
    [data-testid="stFileUploader"] label {{ color: #ffffff !important; }}
    
    /* Divider */
    hr {{ border-color: rgba(255,255,255,0.1) !important; }}
    
    /* Info/Warning boxes */
    .stAlert {{ background: {COLORS['card']} !important; color: #ffffff !important; }}
    
    /* Caption */
    .stCaption, [data-testid="stCaption"] {{ color: {COLORS['text_muted']} !important; }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# ============================================
# ÍNDICES POR POSIÇÃO
# ============================================

INDICES_CONFIG = {
    'Atacante': {
        'Finalização': ['Golos/90', 'Golos esperados/90', 'Remates/90', 'Remates à baliza, %', 'Toques na área/90'],
        '1x1 Ofensivo': ['Dribles/90', 'Dribles com sucesso, %', 'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %'],
        'Jogo Aéreo': ['Duelos aérios/90', 'Duelos aéreos ganhos, %', 'Golos de cabeça/90'],
        'Movimentação': ['Corridas progressivas/90', 'Receção de passes em profundidade/90', 'Acelerações/90'],
        'Participação': ['Passes recebidos/90', 'Toques na área/90', 'Faltas sofridas/90'],
    },
    'Extremo': {
        'Finalização': ['Golos/90', 'Golos esperados/90', 'Remates/90', 'Toques na área/90'],
        '1x1 Ofensivo': ['Dribles/90', 'Dribles com sucesso, %', 'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %'],
        'Criação': ['Assistências/90', 'Assistências esperadas/90', 'Passes chave/90', 'Cruzamentos/90', 'Cruzamentos certos, %'],
        'Progressão': ['Corridas progressivas/90', 'Passes progressivos/90', 'Acelerações/90'],
        'Cruzamentos': ['Cruzamentos/90', 'Cruzamentos certos, %', 'Cruzamentos para a área de baliza/90'],
    },
    'Meia': {
        'Criação': ['Assistências/90', 'Assistências esperadas/90', 'Passes chave/90', 'Passes inteligentes/90'],
        'Progressão': ['Passes progressivos/90', 'Corridas progressivas/90', 'Passes para terço final/90'],
        'Passe': ['Passes/90', 'Passes certos, %', 'Passes longos/90', 'Passes longos certos, %'],
        'Finalização': ['Golos/90', 'Golos esperados/90', 'Remates/90'],
        'Duelos': ['Duelos/90', 'Duelos ganhos, %', 'Duelos defensivos/90'],
    },
    'Volante': {
        'Recuperação': ['Ações defensivas com êxito/90', 'Interseções/90', 'Duelos defensivos/90', 'Duelos defensivos ganhos, %'],
        'Passe': ['Passes/90', 'Passes certos, %', 'Passes longos/90', 'Passes longos certos, %'],
        'Progressão': ['Passes progressivos/90', 'Passes para terço final/90', 'Corridas progressivas/90'],
        'Duelos': ['Duelos/90', 'Duelos ganhos, %', 'Duelos aérios/90', 'Duelos aéreos ganhos, %'],
        'Disciplina': ['Faltas/90', 'Cartões amarelos/90'],
    },
    'Lateral': {
        'Apoio Ofensivo': ['Cruzamentos/90', 'Cruzamentos certos, %', 'Passes para terço final/90', 'Toques na área/90'],
        'Progressão': ['Corridas progressivas/90', 'Passes progressivos/90', 'Acelerações/90'],
        '1x1 Ofensivo': ['Dribles/90', 'Dribles com sucesso, %', 'Duelos ofensivos/90'],
        'Defesa': ['Duelos defensivos/90', 'Duelos defensivos ganhos, %', 'Interseções/90', 'Cortes/90'],
        'Duelos': ['Duelos/90', 'Duelos ganhos, %'],
    },
    'Zagueiro': {
        'Duelos Defensivos': ['Duelos defensivos/90', 'Duelos defensivos ganhos, %', 'Cortes/90'],
        'Jogo Aéreo': ['Duelos aérios/90', 'Duelos aéreos ganhos, %'],
        'Passe': ['Passes/90', 'Passes certos, %', 'Passes longos/90', 'Passes longos certos, %'],
        'Progressão': ['Passes progressivos/90', 'Passes para terço final/90'],
        'Interceções': ['Interseções/90', 'Remates intercetados/90'],
    },
    'Goleiro': {
        'Defesas': ['Defesas, %', 'Golos sofridos/90', 'Remates sofridos/90'],
        'xG Prevented': ['Golos sofridos esperados/90', 'Golos expectáveis defendidos por 90´'],
        'Jogo Aéreo': ['Duelos aérios/90.1', 'Saídas/90'],
        'Jogo com Pés': ['Passes para trás recebidos pelo guarda-redes/90', 'Passes longos certos, %'],
    },
}

POSICAO_MAP = {
    'CF': 'Atacante', 'SS': 'Atacante',
    'LW': 'Extremo', 'RW': 'Extremo', 'LWF': 'Extremo', 'RWF': 'Extremo', 'LAMF': 'Extremo', 'RAMF': 'Extremo',
    'AMF': 'Meia', 'LCMF': 'Meia', 'RCMF': 'Meia', 'CMF': 'Meia',
    'DMF': 'Volante', 'LDMF': 'Volante', 'RDMF': 'Volante',
    'LB': 'Lateral', 'RB': 'Lateral', 'LWB': 'Lateral', 'RWB': 'Lateral',
    'CB': 'Zagueiro', 'LCB': 'Zagueiro', 'RCB': 'Zagueiro',
    'GK': 'Goleiro',
}

# Times da Série B 2025
SERIE_B_TEAMS = [
    'Amazonas', 'América Mineiro', 'Avaí', 'Botafogo SP', 'Botafogo SP B',
    'Chapecoense', 'CRB', 'Coritiba', 'Coritiba SE', 'Goiás', 
    'Grêmio Novorizontino', 'Novorizontino', 'Operário', 'Operário PR', 
    'Paysandu', 'Ponte Preta', 'Remo', 'Vila Nova', 'Vila Nova GO', 'Volta Redonda'
]

# ============================================
# FUNÇÕES
# ============================================

@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file:
        xlsx = pd.ExcelFile(uploaded_file)
    else:
        xlsx = pd.ExcelFile('Banco_de_Dados___Jogadores-3.xlsx')
    
    analises = pd.read_excel(xlsx, sheet_name='Análises')
    oferecidos = pd.read_excel(xlsx, sheet_name='Oferecidos')
    skillcorner = pd.read_excel(xlsx, sheet_name='SkillCorner')
    wyscout = pd.read_excel(xlsx, sheet_name='WyScout')
    
    return analises, oferecidos, skillcorner, wyscout


def get_posicao_categoria(posicao_str):
    if pd.isna(posicao_str):
        return None
    for pos in str(posicao_str).replace(' ', '').split(','):
        if pos in POSICAO_MAP:
            return POSICAO_MAP[pos]
    return None


def normalize_name(name):
    """Normaliza nome para comparação"""
    if pd.isna(name):
        return ""
    import unicodedata
    name = unicodedata.normalize('NFD', str(name))
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    return name.lower().strip()


def find_skillcorner_player(jogador_name, skillcorner_df):
    """Busca jogador no SkillCorner usando múltiplas estratégias"""
    if pd.isna(jogador_name):
        return None
    
    name = str(jogador_name).strip()
    name_norm = normalize_name(name)
    name_parts = name.split()
    
    # Estratégia 1: Nome exato no player_name
    for idx, row in skillcorner_df.iterrows():
        if normalize_name(row.get('player_name', '')) == name_norm:
            return row
    
    # Estratégia 2: Nome exato no short_name
    if 'short_name' in skillcorner_df.columns:
        for idx, row in skillcorner_df.iterrows():
            if normalize_name(row.get('short_name', '')) == name_norm:
                return row
    
    # Estratégia 3: Buscar por sobrenome no player_name
    if len(name_parts) >= 1:
        sobrenome = name_parts[-1]
        if len(sobrenome) > 3:
            for idx, row in skillcorner_df.iterrows():
                player = str(row.get('player_name', '')).lower()
                if sobrenome.lower() in player:
                    # Verificar se primeiro nome também bate (se tiver)
                    if len(name_parts) >= 2:
                        primeiro = name_parts[0].lower()
                        if primeiro in player:
                            return row
                    else:
                        return row
    
    # Estratégia 4: Buscar partes no short_name
    if 'short_name' in skillcorner_df.columns:
        for part in name_parts:
            if len(part) > 2:
                part_norm = normalize_name(part)
                for idx, row in skillcorner_df.iterrows():
                    short = normalize_name(row.get('short_name', ''))
                    if part_norm in short or short in name_norm:
                        return row
    
    return None


def calculate_percentile(value, series):
    if pd.isna(value):
        return 50
    valid = series.dropna()
    if len(valid) == 0:
        return 50
    return (valid < value).sum() / len(valid) * 100


def calculate_index(player_row, metrics, df_all):
    percentiles = []
    for metric in metrics:
        if metric in player_row.index and metric in df_all.columns:
            val = player_row[metric]
            if pd.notna(val):
                perc = calculate_percentile(val, df_all[metric])
                if 'Faltas/90' in metric or 'Cartões' in metric or 'sofridos' in metric.lower():
                    perc = 100 - perc
                percentiles.append(perc)
    return np.mean(percentiles) if percentiles else 50


def get_color(value):
    if value >= 90:
        return COLORS['elite']
    elif value >= 65:
        return COLORS['above']
    elif value >= 36:
        return COLORS['average']
    return COLORS['below']


def create_legend_html():
    """Cria legenda de cores HTML BEM VISÍVEL"""
    return f"""
    <div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 20px; margin: 25px 0; padding: 18px 24px; background: {COLORS['card']}; border-radius: 12px; border: 2px solid {COLORS['border']};">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 24px; height: 24px; background: {COLORS['elite']}; border-radius: 4px; border: 2px solid white;"></div>
            <span style="color: white; font-size: 14px; font-weight: 600;">Elite (90+)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 24px; height: 24px; background: {COLORS['above']}; border-radius: 4px; border: 2px solid white;"></div>
            <span style="color: white; font-size: 14px; font-weight: 600;">Acima (65-89)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 24px; height: 24px; background: {COLORS['average']}; border-radius: 4px; border: 2px solid white;"></div>
            <span style="color: white; font-size: 14px; font-weight: 600;">Média (36-64)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 24px; height: 24px; background: {COLORS['below']}; border-radius: 4px; border: 2px solid white;"></div>
            <span style="color: white; font-size: 14px; font-weight: 600;">Abaixo (0-35)</span>
        </div>
    </div>
    """


def create_section_title(icon, title):
    """Cria título de seção bem visível com fundo"""
    return f"""
    <div style="display: flex; align-items: center; gap: 12px; margin: 30px 0 20px 0; padding: 12px 16px; background: {COLORS['card']}; border-left: 4px solid {COLORS['accent']}; border-radius: 0 8px 8px 0;">
        <span style="font-size: 22px;">{icon}</span>
        <span style="color: #ffffff; font-size: 18px; font-weight: 700;">{title}</span>
    </div>
    """


def create_wyscout_radar(metrics_dict):
    categories = list(metrics_dict.keys())
    values = list(metrics_dict.values())
    n = len(categories)
    
    if n == 0:
        return go.Figure()
    
    fig = go.Figure()
    
    # Círculos de fundo
    for r in [25, 50, 75, 100]:
        theta = list(range(0, 361, 1))
        fig.add_trace(go.Scatterpolar(
            r=[r] * len(theta), theta=theta, mode='lines',
            line=dict(color='rgba(255,255,255,0.15)', width=1),
            showlegend=False, hoverinfo='skip'
        ))
    
    # Linhas radiais
    for i in range(n):
        angle = i * (360 / n)
        fig.add_trace(go.Scatterpolar(
            r=[0, 105], theta=[angle, angle], mode='lines',
            line=dict(color='rgba(255,255,255,0.15)', width=1),
            showlegend=False, hoverinfo='skip'
        ))
    
    # Setores coloridos
    for i, (cat, val) in enumerate(zip(categories, values)):
        color = get_color(val)
        angle_center = i * (360 / n)
        half_width = (360 / n) / 2 - 2
        
        theta_points = np.linspace(angle_center - half_width, angle_center + half_width, 30)
        r_points = [val] * len(theta_points)
        
        theta_full = [angle_center] + list(theta_points) + [angle_center]
        r_full = [0] + r_points + [0]
        
        fig.add_trace(go.Scatterpolar(
            r=r_full, theta=theta_full, fill='toself',
            fillcolor=color, line=dict(color=color, width=1),
            opacity=0.85, showlegend=False,
            hovertemplate=f'<b>{cat}</b><br>{val:.0f}<extra></extra>'
        ))
    
    # Labels externos - BEM VISÍVEIS
    for i, (cat, val) in enumerate(zip(categories, values)):
        angle = i * (360 / n)
        fig.add_trace(go.Scatterpolar(
            r=[128], theta=[angle], mode='text',
            text=[f"<b>{cat}</b>"], textfont=dict(size=12, color='white'),
            showlegend=False, hoverinfo='skip'
        ))
        if val > 15:
            fig.add_trace(go.Scatterpolar(
                r=[val * 0.5], theta=[angle], mode='text',
                text=[f'<b>{val:.0f}</b>'], textfont=dict(size=14, color='white'),
                showlegend=False, hoverinfo='skip'
            ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 150]),
            angularaxis=dict(visible=False, direction='clockwise'),
            bgcolor=COLORS['bg']
        ),
        paper_bgcolor=COLORS['card'],
        plot_bgcolor=COLORS['bg'],
        margin=dict(l=100, r=100, t=60, b=60),
        height=420,
        showlegend=False
    )
    
    return fig


def create_bar_chart(metrics_dict, title=""):
    categories = list(metrics_dict.keys())
    values = list(metrics_dict.values())
    colors = [get_color(v) for v in values]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=categories, x=values, orientation='h',
        marker=dict(color=colors, line=dict(width=0)),
        text=[f'{v:.0f}' for v in values],
        textposition='inside',
        textfont=dict(color='white', size=14, weight=700),
        hovertemplate='<b>%{y}</b><br>Percentil: %{x:.0f}<extra></extra>'
    ))
    
    for x in [25, 50, 75]:
        fig.add_vline(x=x, line_dash="dot", line_color="rgba(255,255,255,0.3)")
    
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=16, color='white')),
        paper_bgcolor=COLORS['card'],
        plot_bgcolor=COLORS['bg'],
        xaxis=dict(
            range=[0, 100], 
            gridcolor='rgba(255,255,255,0.1)', 
            tickfont=dict(color='white', size=12),
            title=dict(text='<b>Percentil</b>', font=dict(color='white', size=13))
        ),
        yaxis=dict(
            tickfont=dict(color='white', size=13), 
            categoryorder='total ascending'
        ),
        margin=dict(l=180, r=40, t=60, b=60),
        height=max(320, len(categories) * 50 + 120)
    )
    
    return fig


def create_comparison_radar(p1_data, p2_data, p1_name, p2_name):
    categories = list(p1_data.keys())
    vals1 = list(p1_data.values()) + [list(p1_data.values())[0]]
    vals2 = list(p2_data.values()) + [list(p2_data.values())[0]]
    theta = categories + [categories[0]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=vals1, theta=theta, fill='toself',
        fillcolor='rgba(220, 38, 38, 0.3)',
        line=dict(color=COLORS['accent'], width=2),
        name=p1_name
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=vals2, theta=theta, fill='toself',
        fillcolor='rgba(59, 130, 246, 0.3)',
        line=dict(color='#3b82f6', width=2),
        name=p2_name
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(255,255,255,0.15)', tickfont=dict(color='white', size=11)),
            angularaxis=dict(gridcolor='rgba(255,255,255,0.15)', tickfont=dict(color='white', size=12, weight=500)),
            bgcolor=COLORS['bg']
        ),
        paper_bgcolor=COLORS['card'],
        legend=dict(
            orientation='h', yanchor='bottom', y=1.1, xanchor='center', x=0.5, 
            font=dict(color='white', size=14, weight=600),
            bgcolor=COLORS['card'],
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1
        ),
        margin=dict(l=80, r=80, t=100, b=40),
        height=480
    )
    
    return fig


def create_scatter_plot(df, x_col, y_col, highlight=None, title=""):
    df_valid = df.dropna(subset=[x_col, y_col])
    if len(df_valid) == 0:
        return go.Figure()
    
    x_mean, y_mean = df_valid[x_col].mean(), df_valid[y_col].mean()
    x_max, y_max = df_valid[x_col].max() * 1.1, df_valid[y_col].max() * 1.1
    x_min, y_min = df_valid[x_col].min() * 0.9, df_valid[y_col].min() * 0.9
    
    fig = go.Figure()
    
    # Quadrantes
    fig.add_shape(type="rect", x0=x_mean, y0=y_mean, x1=x_max, y1=y_max,
                  fillcolor="rgba(34,197,94,0.15)", line=dict(width=0))
    fig.add_shape(type="rect", x0=x_min, y0=y_min, x1=x_mean, y1=y_mean,
                  fillcolor="rgba(239,68,68,0.15)", line=dict(width=0))
    
    fig.add_hline(y=y_mean, line_dash="dot", line_color="rgba(255,255,255,0.4)")
    fig.add_vline(x=x_mean, line_dash="dot", line_color="rgba(255,255,255,0.4)")
    
    name_col = 'Jogador' if 'Jogador' in df_valid.columns else 'player_name'
    
    fig.add_trace(go.Scatter(
        x=df_valid[x_col], y=df_valid[y_col],
        mode='markers',
        marker=dict(size=7, color='#6b7280', opacity=0.5),
        text=df_valid[name_col],
        hovertemplate='<b>%{text}</b><br>%{x:.2f} | %{y:.2f}<extra></extra>',
        showlegend=False
    ))
    
    if highlight and highlight in df_valid[name_col].values:
        p = df_valid[df_valid[name_col] == highlight].iloc[0]
        fig.add_trace(go.Scatter(
            x=[p[x_col]], y=[p[y_col]],
            mode='markers+text',
            marker=dict(size=16, color=COLORS['accent'], line=dict(width=3, color='white')),
            text=[highlight.split()[0]],
            textposition='top center',
            textfont=dict(color='white', size=13, weight=700),
            showlegend=False
        ))
    
    # Labels MUITO VISÍVEIS
    x_label = x_col.replace('/90', ' /90').replace(', %', ' %')
    y_label = y_col.replace('/90', ' /90').replace(', %', ' %')
    
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=17, color='white')),
        paper_bgcolor=COLORS['card'],
        plot_bgcolor=COLORS['bg'],
        xaxis=dict(
            title=dict(text=f"<b>{x_label}</b>", font=dict(color='white', size=14)),
            gridcolor='rgba(255,255,255,0.1)',
            tickfont=dict(color='white', size=11),
            zeroline=False
        ),
        yaxis=dict(
            title=dict(text=f"<b>{y_label}</b>", font=dict(color='white', size=14)),
            gridcolor='rgba(255,255,255,0.1)',
            tickfont=dict(color='white', size=11),
            zeroline=False
        ),
        margin=dict(l=90, r=40, t=80, b=90),
        height=460
    )
    
    return fig


# ============================================
# MAIN
# ============================================

def main():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 20px 0;">
            <div style="color: #dc2626; font-size: 11px; letter-spacing: 3px; font-weight: 600;">SCOUTING</div>
            <div style="color: white; font-size: 26px; font-weight: 800; letter-spacing: -1px;">BOTAFOGO</div>
            <div style="color: #6b7280; font-size: 10px; letter-spacing: 2px;">RIBEIRÃO PRETO</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        uploaded = st.file_uploader("📂 Carregar Planilha", type=['xlsx'])
        
        try:
            analises, oferecidos, skillcorner, wyscout = load_data(uploaded)
        except:
            st.error("⚠️ Faça upload do Excel")
            return
        
        st.divider()
        st.caption("FILTROS")
        
        posicoes = ['Todas'] + sorted([str(p) for p in analises['Posição'].dropna().unique()])
        posicao = st.selectbox("Posição", posicoes)
        
        df = analises if posicao == 'Todas' else analises[analises['Posição'] == posicao]
        jogadores = sorted([str(j) for j in df['Nome'].dropna().unique()])
        
        if not jogadores:
            st.warning("Nenhum jogador")
            return
        
        jogador = st.selectbox("Jogador", jogadores)
        
        st.divider()
        # Contagem de jogadores com índices SC
        sc_with_idx = skillcorner[skillcorner['Direct striker index'].notna()].shape[0]
        st.caption(f"📊 {len(analises)} análises | 📈 {len(wyscout)} Wyscout")
        st.caption(f"🏃 {len(skillcorner)} SkillCorner ({sc_with_idx} com índices)")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Perfil", "📈 Índices", "📋 Relatório", "🔄 Comparativo", "🗂️ Dados"])
    
    # ===== TAB 1: PERFIL =====
    with tab1:
        if jogador:
            p = df[df['Nome'] == jogador].iloc[0]
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div style="background: {COLORS['card']}; border-radius: 12px; padding: 24px; border: 1px solid {COLORS['border']};">
                    <div style="color: {COLORS['accent']}; font-size: 12px; font-weight: 600; letter-spacing: 1px;">{p['Posição'] or 'JOGADOR'}</div>
                    <div style="color: white; font-size: 32px; font-weight: 800; margin: 4px 0;">{p['Nome']}</div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 16px;">
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Idade</div><div style="color: white; font-size: 14px;">{int(p['Idade']) if pd.notna(p['Idade']) else '-'} anos</div></div>
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Clube</div><div style="color: white; font-size: 14px;">{p['Clube'] or '-'}</div></div>
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Liga</div><div style="color: white; font-size: 14px;">{p['Liga'] or '-'}</div></div>
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Perfil</div><div style="color: white; font-size: 14px;">{p['Perfil'] or '-'}</div></div>
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Contrato</div><div style="color: white; font-size: 14px;">{str(p['Contrato']).split(' ')[0] if pd.notna(p['Contrato']) else '-'}</div></div>
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Modelo</div><div style="color: white; font-size: 14px;">{p['Modelo'] if pd.notna(p.get('Modelo')) else '-'}</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if pd.notna(p['Nota_Desempenho']):
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {COLORS['accent']}, #b91c1c); border-radius: 12px; padding: 20px; text-align: center;">
                        <div style="color: rgba(255,255,255,0.7); font-size: 10px; letter-spacing: 1px;">NOTA GERAL</div>
                        <div style="color: white; font-size: 42px; font-weight: 800;">{p['Nota_Desempenho']:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                if pd.notna(p.get('Link_TM')):
                    st.link_button("🔗 Transfermarkt", p['Link_TM'], use_container_width=True)
            
            # LEGENDA BEM VISÍVEL
            st.markdown(create_legend_html(), unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(create_section_title("📊", "Atributos Qualitativos"), unsafe_allow_html=True)
                attrs = {
                    'Técnica': (p['Técnica'] / 5 * 100) if pd.notna(p['Técnica']) else 50,
                    'Físico': (p['Físico'] / 5 * 100) if pd.notna(p['Físico']) else 50,
                    'Tática': (p['Tática'] / 5 * 100) if pd.notna(p['Tática']) else 50,
                    'Mental': (p['Mental'] / 5 * 100) if pd.notna(p['Mental']) else 50,
                }
                st.plotly_chart(create_wyscout_radar(attrs), use_container_width=True, config={'displayModeBar': False}, key="radar_attrs")
            
            with col2:
                st.markdown(create_section_title("⭐", "Potencial"), unsafe_allow_html=True)
                perc = attrs.copy()
                perc['Potencial'] = (p['Potencial'] / 5 * 100) if pd.notna(p.get('Potencial')) else 50
                st.plotly_chart(create_wyscout_radar(perc), use_container_width=True, config={'displayModeBar': False}, key="radar_potencial")
            
            if pd.notna(p.get('Análise')):
                st.markdown(create_section_title("📝", "Análise Qualitativa"), unsafe_allow_html=True)
                st.markdown(f"""
                <div style="background: {COLORS['card']}; border-left: 4px solid {COLORS['accent']}; border-radius: 0 8px 8px 0; padding: 20px;">
                    <p style="color: {COLORS['text_secondary']}; line-height: 1.8; margin: 0; font-size: 15px;">{p['Análise']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # ===== TAB 2: ÍNDICES =====
    with tab2:
        st.markdown(create_section_title("📈", "Índices Compostos por Posição"), unsafe_allow_html=True)
        
        jogadores_ws = sorted(wyscout['Jogador'].dropna().unique().tolist())
        
        col1, col2 = st.columns([2, 1])
        with col1:
            jogador_ws = st.selectbox("Jogador (Wyscout)", jogadores_ws, key='ws_player')
        with col2:
            categoria = st.selectbox("Categoria de Posição", list(INDICES_CONFIG.keys()), key='cat_indices')
        
        if jogador_ws:
            player_ws = wyscout[wyscout['Jogador'] == jogador_ws].iloc[0]
            
            st.markdown(f"""
            <div style="background: {COLORS['card']}; border-radius: 12px; padding: 16px; margin: 16px 0; border: 1px solid {COLORS['border']};">
                <span style="color: {COLORS['accent']}; font-weight: 600;">{player_ws['Posição']}</span> | 
                <span style="color: white; font-weight: 700; font-size: 18px;">{jogador_ws}</span> | 
                <span style="color: {COLORS['text_secondary']};">{player_ws['Equipa']} • {int(player_ws['Idade']) if pd.notna(player_ws['Idade']) else '-'} anos • {int(player_ws['Minutos jogados:']) if pd.notna(player_ws['Minutos jogados:']) else 0} min</span>
            </div>
            """, unsafe_allow_html=True)
            
            # LEGENDA
            st.markdown(create_legend_html(), unsafe_allow_html=True)
            
            indices = INDICES_CONFIG.get(categoria, {})
            indices_values = {idx_name: calculate_index(player_ws, metrics, wyscout) for idx_name, metrics in indices.items()}
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_wyscout_radar(indices_values), use_container_width=True, config={'displayModeBar': False}, key="radar_indices")
            with col2:
                st.plotly_chart(create_bar_chart(indices_values, "Ranking Percentil"), use_container_width=True, config={'displayModeBar': False}, key="bar_indices")
            
            st.markdown(create_section_title("🔍", "Detalhamento por Índice"), unsafe_allow_html=True)
            
            for idx_name, metrics in indices.items():
                with st.expander(f"📊 {idx_name} — Percentil: {indices_values[idx_name]:.0f}"):
                    cols = st.columns(min(5, len(metrics)))
                    for i, m in enumerate(metrics):
                        if m in player_ws.index:
                            val = player_ws[m]
                            perc = calculate_percentile(val, wyscout[m]) if pd.notna(val) else 50
                            color = get_color(perc)
                            val_fmt = f"{val:.2f}" if pd.notna(val) else "-"
                            with cols[i % len(cols)]:
                                st.markdown(f"""
                                <div style="background: {COLORS['card']}; border-radius: 8px; padding: 12px; text-align: center; border-left: 3px solid {color}; margin-bottom: 8px;">
                                    <div style="color: {COLORS['text_muted']}; font-size: 9px; text-transform: uppercase;">{m.replace('/90', '').replace(', %', '%')[:20]}</div>
                                    <div style="color: white; font-size: 18px; font-weight: 700;">{val_fmt}</div>
                                    <div style="color: {color}; font-size: 10px;">P{perc:.0f}</div>
                                </div>
                                """, unsafe_allow_html=True)
    
    # ===== TAB 3: RELATÓRIO =====
    with tab3:
        st.markdown(create_section_title("📋", "Gráficos de Relatório"), unsafe_allow_html=True)
        
        jogadores_ws = sorted(wyscout['Jogador'].dropna().unique().tolist())
        
        col1, col2 = st.columns([2, 1])
        with col1:
            jogador_rel = st.selectbox("Selecione o Jogador", jogadores_ws, key='rel_player')
        with col2:
            # SELETOR DE POSIÇÃO PARA O RELATÓRIO
            posicao_rel = st.selectbox("Posição para Índices", list(INDICES_CONFIG.keys()), key='pos_rel')
        
        if jogador_rel:
            player_rel = wyscout[wyscout['Jogador'] == jogador_rel].iloc[0]
            
            st.markdown(f"""
            <div style="background: {COLORS['card']}; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 2px solid {COLORS['accent']};">
                <div style="color: {COLORS['accent']}; font-size: 13px; font-weight: 600;">{player_rel['Posição']} → AVALIANDO COMO: {posicao_rel.upper()}</div>
                <div style="color: white; font-size: 30px; font-weight: 800; margin: 8px 0;">{jogador_rel}</div>
                <div style="color: {COLORS['text_secondary']}; font-size: 15px;">
                    {player_rel['Equipa']} • {int(player_rel['Idade']) if pd.notna(player_rel['Idade']) else '-'} anos • 
                    {int(player_rel['Partidas jogadas']) if pd.notna(player_rel['Partidas jogadas']) else 0} jogos • 
                    {int(player_rel['Minutos jogados:']) if pd.notna(player_rel['Minutos jogados:']) else 0} min
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # LEGENDA
            st.markdown(create_legend_html(), unsafe_allow_html=True)
            
            indices = INDICES_CONFIG.get(posicao_rel, INDICES_CONFIG['Meia'])
            indices_values = {idx_name: calculate_index(player_rel, metrics, wyscout) for idx_name, metrics in indices.items()}
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(create_section_title("📊", "Perfil de Índices"), unsafe_allow_html=True)
                st.plotly_chart(create_wyscout_radar(indices_values), use_container_width=True, config={'displayModeBar': False}, key="radar_rel")
            with col2:
                st.markdown(create_section_title("📈", "Rankings"), unsafe_allow_html=True)
                st.plotly_chart(create_bar_chart(indices_values), use_container_width=True, config={'displayModeBar': False}, key="bar_rel")
            
            st.markdown(create_section_title("📍", "Posicionamento vs Liga"), unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if posicao_rel in ['Atacante', 'Extremo']:
                    fig = create_scatter_plot(wyscout, 'Golos esperados/90', 'Assistências esperadas/90', jogador_rel, 'xG vs xA por 90')
                else:
                    fig = create_scatter_plot(wyscout, 'Passes progressivos/90', 'Corridas progressivas/90', jogador_rel, 'Passes Prog. vs Corridas Prog.')
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key="scatter1")
            
            with col2:
                if posicao_rel in ['Zagueiro', 'Volante']:
                    fig = create_scatter_plot(wyscout, 'Duelos defensivos/90', 'Duelos defensivos ganhos, %', jogador_rel, 'Volume vs Eficiência Defensiva')
                else:
                    fig = create_scatter_plot(wyscout, 'Dribles/90', 'Dribles com sucesso, %', jogador_rel, 'Volume vs Eficiência 1x1')
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key="scatter2")
            
            # SkillCorner - DADOS FÍSICOS
            st.markdown(create_section_title("🏃", "Dados Físicos SkillCorner"), unsafe_allow_html=True)
            
            # Criar lista de jogadores SkillCorner para seleção
            sc_players_list = skillcorner['player_name'].dropna().unique().tolist()
            sc_players_list = sorted(sc_players_list)
            
            # Tentar match automático para sugerir
            sc_auto_match = find_skillcorner_player(jogador_rel, skillcorner)
            default_idx = 0
            if sc_auto_match is not None:
                try:
                    default_idx = sc_players_list.index(sc_auto_match['player_name'])
                except ValueError:
                    default_idx = 0
            
            # Selectbox para seleção manual
            col_sc1, col_sc2 = st.columns([3, 1])
            with col_sc1:
                sc_selected_name = st.selectbox(
                    "Selecionar Jogador SkillCorner",
                    sc_players_list,
                    index=default_idx,
                    key='sc_player_select',
                    help="Match automático sugerido. Selecione outro se estiver incorreto."
                )
            with col_sc2:
                if sc_auto_match is not None and sc_selected_name == sc_auto_match['player_name']:
                    st.markdown(f"<br><span style='color: {COLORS['elite']}; font-size: 12px;'>✓ Match automático</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<br><span style='color: {COLORS['above']}; font-size: 12px;'>✎ Seleção manual</span>", unsafe_allow_html=True)
            
            # Buscar jogador selecionado
            sc_player = skillcorner[skillcorner['player_name'] == sc_selected_name].iloc[0] if sc_selected_name else None
            
            if sc_player is not None:
                count_match = sc_player.get('count_match', 0)
                min_per_match = sc_player.get('minutes_per_match', 0)
                try:
                    count_match = int(float(count_match)) if pd.notna(count_match) else 0
                    min_per_match = float(min_per_match) if pd.notna(min_per_match) else 0
                except:
                    count_match = 0
                    min_per_match = 0
                
                st.markdown(f"""
                <div style="background: {COLORS['card']}; border-radius: 8px; padding: 14px; margin-bottom: 20px; border: 1px solid {COLORS['border']};">
                    <span style="color: white; font-weight: 700; font-size: 15px;">{sc_player['player_name']}</span>
                    <span style="color: {COLORS['text_secondary']};"> • {sc_player['team_name']}</span>
                    <span style="color: {COLORS['text_muted']}; font-size: 12px;"> • {count_match} jogos • {min_per_match:.0f} min/jogo</span>
                </div>
                """, unsafe_allow_html=True)
                
                # DADOS FÍSICOS - Todos os jogadores têm
                # O _rank JÁ É o percentil (100 = melhor, 0 = pior)
                # NOTA: sprint_count_per_90 removido pois está corrompido no Excel (parseado como datetime)
                physical_metrics = {
                    'Vel. Máx (km/h)': ('avg_psv99', 'avg_psv99_rank'),
                    'Top 5 Vel (km/h)': ('avg_top_5_psv99', 'avg_top_5_psv99_rank'),
                    'Dist. Total /90': ('distance_per_90', 'distance_per_90_rank'),
                    'Dist. Alta Int /90': ('hi_distance_per_90', 'hi_distance_per_90_rank'),
                    'Dist. Sprint /90': ('sprint_distance_per_90', 'sprint_distance_per_90_rank'),
                    'Ações Alta Int /90': ('hi_count_per_90', 'hi_count_per_90_rank'),
                    'm/min (posse)': ('avg_meters_per_minute_tip', 'avg_meters_per_minute_tip_rank'),
                    'Acel → HSR /90': ('explacceltohsr_count_per_90', 'explacceltohsr_count_per_90_rank'),
                    'Acel → Sprint /90': ('explacceltosprint_count_per_90', 'explacceltosprint_count_per_90_rank'),
                }
                
                # Calcular percentis físicos (rank JÁ É o percentil)
                physical_perc = {}
                physical_vals = {}
                for label, (val_col, rank_col) in physical_metrics.items():
                    try:
                        if val_col in sc_player.index and rank_col in sc_player.index:
                            val = sc_player.get(val_col)
                            rank = sc_player.get(rank_col)
                            
                            # Converter valor para float (pode estar como string)
                            val_float = None
                            if pd.notna(val):
                                # Verificar se não é datetime
                                if hasattr(val, 'year'):  # É datetime
                                    continue
                                try:
                                    val_float = float(str(val).replace(',', '.'))
                                except:
                                    continue
                            
                            # Rank já é o percentil
                            if pd.notna(rank) and val_float is not None:
                                physical_perc[label] = float(rank)
                                physical_vals[label] = val_float
                    except Exception as e:
                        continue  # Pular métricas com erro
                
                if physical_perc:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(create_wyscout_radar(physical_perc), use_container_width=True, config={'displayModeBar': False}, key="radar_sc_phys")
                    with col2:
                        st.plotly_chart(create_bar_chart(physical_perc, "Perfil Físico (Percentil)"), use_container_width=True, config={'displayModeBar': False}, key="bar_sc_phys")
                    
                    # Cards com valores absolutos
                    st.markdown("<br>", unsafe_allow_html=True)
                    cols = st.columns(5)
                    for i, (label, val) in enumerate(physical_vals.items()):
                        perc = physical_perc.get(label, 50)
                        color = get_color(perc)
                        with cols[i % 5]:
                            st.markdown(f"""
                            <div style="background: {COLORS['card']}; border-radius: 8px; padding: 12px; text-align: center; border-left: 3px solid {color}; margin-bottom: 8px;">
                                <div style="color: {COLORS['text_muted']}; font-size: 9px; text-transform: uppercase;">{label}</div>
                                <div style="color: white; font-size: 16px; font-weight: 700;">{val:.1f}</div>
                                <div style="color: {color}; font-size: 10px;">P{perc:.0f}</div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Dados físicos não disponíveis para este jogador")
                
                # ÍNDICES DE ESTILO (só para os 435 que têm)
                sc_indices_raw = {
                    'Direct Striker': ('Direct striker index', 'Direct striker index_rank'),
                    'Link-up Striker': ('Link up striker index', 'Link up striker index_rank'),
                    'Inverted Winger': ('Inverted winger index', 'Inverted winger index_rank'),
                    'Wide Winger': ('Wide winger index', 'Wide winger index_rank'),
                    'Dynamic #8': ('Dynamic number 8 index', 'Dynamic number 8 index_rank'),
                    'Box-to-Box': ('Box to box midfielder index', 'Box to box midfielder index_rank'),
                    'Number 6': ('Number 6 index', 'Number 6 index_rank'),
                    'Intense FB': ('Intense full back index', 'Intense full back index_rank'),
                    'Technical FB': ('Technical full back index', 'Technical full back index_rank'),
                    'Aggressive CB': ('Physical & aggressive defender index', 'Physical & aggressive defender index_rank'),
                    'Ball-Playing CB': ('Ball playing central defender index', 'Ball playing central defender index_rank'),
                }
                
                sc_style_perc = {}
                for label, (val_col, rank_col) in sc_indices_raw.items():
                    if val_col in sc_player.index:
                        rank = sc_player.get(rank_col)
                        if pd.notna(rank):
                            # rank JÁ É o percentil (rank 100 = melhor)
                            try:
                                sc_style_perc[label] = float(rank)
                            except:
                                pass
                
                if sc_style_perc:
                    st.markdown(create_section_title("🎯", "Índices de Estilo de Jogo"), unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(create_wyscout_radar(sc_style_perc), use_container_width=True, config={'displayModeBar': False}, key="radar_sc_style")
                    with col2:
                        st.plotly_chart(create_bar_chart(sc_style_perc, "Índices de Estilo"), use_container_width=True, config={'displayModeBar': False}, key="bar_sc_style")
                else:
                    st.info("ℹ️ Índices de estilo de jogo não disponíveis para este jogador (apenas 435 de 3.298 jogadores têm)")
    
    # ===== TAB 4: COMPARATIVO =====
    with tab4:
        st.markdown(create_section_title("🔄", "Comparar Jogadores"), unsafe_allow_html=True)
        
        jogadores_ws = sorted(wyscout['Jogador'].dropna().unique().tolist())
        
        col1, col2 = st.columns(2)
        with col1:
            j1 = st.selectbox("Jogador 1", jogadores_ws, key='cmp1')
        with col2:
            j2 = st.selectbox("Jogador 2", jogadores_ws, index=min(1, len(jogadores_ws)-1), key='cmp2')
        
        categoria_cmp = st.selectbox("Categoria para comparação", list(INDICES_CONFIG.keys()), key='cat_cmp')
        
        if j1 and j2 and j1 != j2:
            p1 = wyscout[wyscout['Jogador'] == j1].iloc[0]
            p2 = wyscout[wyscout['Jogador'] == j2].iloc[0]
            
            indices = INDICES_CONFIG.get(categoria_cmp, {})
            idx1 = {n: calculate_index(p1, m, wyscout) for n, m in indices.items()}
            idx2 = {n: calculate_index(p2, m, wyscout) for n, m in indices.items()}
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div style="background: rgba(220,38,38,0.2); border: 2px solid {COLORS['accent']}; border-radius: 12px; padding: 16px;">
                    <div style="color: {COLORS['accent']}; font-weight: 600;">{p1['Posição']}</div>
                    <div style="color: white; font-size: 20px; font-weight: 700;">{j1}</div>
                    <div style="color: {COLORS['text_secondary']};">{p1['Equipa']} • {int(p1['Idade']) if pd.notna(p1['Idade']) else '-'} anos</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="background: rgba(59,130,246,0.2); border: 2px solid #3b82f6; border-radius: 12px; padding: 16px;">
                    <div style="color: #3b82f6; font-weight: 600;">{p2['Posição']}</div>
                    <div style="color: white; font-size: 20px; font-weight: 700;">{j2}</div>
                    <div style="color: {COLORS['text_secondary']};">{p2['Equipa']} • {int(p2['Idade']) if pd.notna(p2['Idade']) else '-'} anos</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.plotly_chart(create_comparison_radar(idx1, idx2, j1, j2), use_container_width=True, config={'displayModeBar': False}, key="radar_cmp")
            
            st.markdown(create_section_title("📊", "Tabela Comparativa"), unsafe_allow_html=True)
            
            comparison_data = []
            for idx_name in indices.keys():
                v1, v2 = idx1[idx_name], idx2[idx_name]
                diff = v1 - v2
                comparison_data.append({
                    'Índice': idx_name,
                    j1: f"{v1:.0f}",
                    j2: f"{v2:.0f}",
                    'Diferença': f"+{diff:.0f}" if diff > 0 else f"{diff:.0f}",
                    'Vantagem': '🔴' if diff > 0 else '🔵' if diff < 0 else '='
                })
            
            st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
    
    # ===== TAB 5: DADOS =====
    with tab5:
        st.markdown(create_section_title("🗂️", "Explorar Dados"), unsafe_allow_html=True)
        
        source = st.radio("Fonte de Dados", ['Análises', 'WyScout', 'SkillCorner', 'Oferecidos'], horizontal=True, key='data_source')
        
        if source == 'Análises':
            df_show = analises[['Nome', 'Posição', 'Idade', 'Clube', 'Liga', 'Perfil', 'Nota_Desempenho']]
        elif source == 'WyScout':
            df_show = wyscout[['Jogador', 'Equipa', 'Posição', 'Idade', 'Partidas jogadas', 'Minutos jogados:', 'Golos', 'Assistências', 'Golos esperados/90', 'Assistências esperadas/90']]
        elif source == 'SkillCorner':
            df_show = skillcorner[['player_name', 'short_name', 'team_name', 'position_group', 'age', 'count_match', 'Direct striker index', 'Link up striker index']]
        else:
            df_show = oferecidos
        
        search = st.text_input("🔍 Buscar jogador", key='search_data')
        if search:
            name_col = 'Jogador' if 'Jogador' in df_show.columns else 'player_name' if 'player_name' in df_show.columns else 'Nome'
            df_show = df_show[df_show[name_col].str.contains(search, case=False, na=False)]
        
        st.dataframe(df_show, use_container_width=True, height=500)
        st.download_button("📥 Exportar CSV", df_show.to_csv(index=False).encode('utf-8'), f"{source.lower()}.csv", key='download_csv')


if __name__ == "__main__":
    main()
