import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from urllib.parse import quote

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
# GOOGLE SHEETS CONFIG
# ============================================
GOOGLE_SHEET_ID = "1IlCBif0Um_gGXPMa-VV9riYxkX3qAqeKxgQZppSlrjU"

# ============================================
# BANDEIRAS DE NACIONALIDADE
# ============================================
COUNTRY_FLAGS = {
    'Brazil': '🇧🇷', 'Brasil': '🇧🇷', 'Brazilian': '🇧🇷',
    'Argentina': '🇦🇷', 'Argentine': '🇦🇷', 'Argentinian': '🇦🇷',
    'Uruguay': '🇺🇾', 'Uruguai': '🇺🇾', 'Uruguayan': '🇺🇾',
    'Colombia': '🇨🇴', 'Colômbia': '🇨🇴', 'Colombian': '🇨🇴',
    'Paraguay': '🇵🇾', 'Paraguai': '🇵🇾', 'Paraguayan': '🇵🇾',
    'Chile': '🇨🇱', 'Chilean': '🇨🇱',
    'Peru': '🇵🇪', 'Peruvian': '🇵🇪',
    'Ecuador': '🇪🇨', 'Equador': '🇪🇨', 'Ecuadorian': '🇪🇨',
    'Venezuela': '🇻🇪', 'Venezuelan': '🇻🇪',
    'Bolivia': '🇧🇴', 'Bolívia': '🇧🇴', 'Bolivian': '🇧🇴',
    'Mexico': '🇲🇽', 'México': '🇲🇽', 'Mexican': '🇲🇽',
    'United States': '🇺🇸', 'EUA': '🇺🇸', 'USA': '🇺🇸', 'American': '🇺🇸',
    'Portugal': '🇵🇹', 'Portuguese': '🇵🇹',
    'Spain': '🇪🇸', 'Espanha': '🇪🇸', 'Spanish': '🇪🇸',
    'Italy': '🇮🇹', 'Itália': '🇮🇹', 'Italian': '🇮🇹',
    'France': '🇫🇷', 'França': '🇫🇷', 'French': '🇫🇷',
    'Germany': '🇩🇪', 'Alemanha': '🇩🇪', 'German': '🇩🇪',
    'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'Inglaterra': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'English': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    'Netherlands': '🇳🇱', 'Holanda': '🇳🇱', 'Dutch': '🇳🇱',
    'Belgium': '🇧🇪', 'Bélgica': '🇧🇪', 'Belgian': '🇧🇪',
    'Japan': '🇯🇵', 'Japão': '🇯🇵', 'Japanese': '🇯🇵',
    'South Korea': '🇰🇷', 'Coreia do Sul': '🇰🇷', 'Korean': '🇰🇷',
    'Australia': '🇦🇺', 'Austrália': '🇦🇺', 'Australian': '🇦🇺',
    'Nigeria': '🇳🇬', 'Nigéria': '🇳🇬', 'Nigerian': '🇳🇬',
    'Senegal': '🇸🇳', 'Senegalese': '🇸🇳',
    'Ghana': '🇬🇭', 'Gana': '🇬🇭', 'Ghanaian': '🇬🇭',
    'Cameroon': '🇨🇲', 'Camarões': '🇨🇲', 'Cameroonian': '🇨🇲',
    'Morocco': '🇲🇦', 'Marrocos': '🇲🇦', 'Moroccan': '🇲🇦',
    'Egypt': '🇪🇬', 'Egito': '🇪🇬', 'Egyptian': '🇪🇬',
    'South Africa': '🇿🇦', 'África do Sul': '🇿🇦',
    'Angola': '🇦🇴', 'Angolan': '🇦🇴',
    'Mozambique': '🇲🇿', 'Moçambique': '🇲🇿',
    'Guinea-Bissau': '🇬🇼', 'Guiné-Bissau': '🇬🇼',
    'Cape Verde': '🇨🇻', 'Cabo Verde': '🇨🇻',
    'Costa Rica': '🇨🇷', 'Costa Rican': '🇨🇷',
    'Panama': '🇵🇦', 'Panamá': '🇵🇦',
    'Honduras': '🇭🇳', 'Honduran': '🇭🇳',
    'Jamaica': '🇯🇲', 'Jamaican': '🇯🇲',
    'Haiti': '🇭🇹', 'Haitian': '🇭🇹',
    'Dominican Republic': '🇩🇴', 'República Dominicana': '🇩🇴',
    'Cuba': '🇨🇺', 'Cuban': '🇨🇺',
    'Poland': '🇵🇱', 'Polônia': '🇵🇱', 'Polish': '🇵🇱',
    'Czech Republic': '🇨🇿', 'República Tcheca': '🇨🇿', 'Czechia': '🇨🇿',
    'Croatia': '🇭🇷', 'Croácia': '🇭🇷', 'Croatian': '🇭🇷',
    'Serbia': '🇷🇸', 'Sérvia': '🇷🇸', 'Serbian': '🇷🇸',
    'Switzerland': '🇨🇭', 'Suíça': '🇨🇭', 'Swiss': '🇨🇭',
    'Austria': '🇦🇹', 'Áustria': '🇦🇹', 'Austrian': '🇦🇹',
    'Sweden': '🇸🇪', 'Suécia': '🇸🇪', 'Swedish': '🇸🇪',
    'Norway': '🇳🇴', 'Noruega': '🇳🇴', 'Norwegian': '🇳🇴',
    'Denmark': '🇩🇰', 'Dinamarca': '🇩🇰', 'Danish': '🇩🇰',
    'Finland': '🇫🇮', 'Finlândia': '🇫🇮', 'Finnish': '🇫🇮',
    'Russia': '🇷🇺', 'Rússia': '🇷🇺', 'Russian': '🇷🇺',
    'Ukraine': '🇺🇦', 'Ucrânia': '🇺🇦', 'Ukrainian': '🇺🇦',
    'Turkey': '🇹🇷', 'Turquia': '🇹🇷', 'Turkish': '🇹🇷',
    'Greece': '🇬🇷', 'Grécia': '🇬🇷', 'Greek': '🇬🇷',
    'Romania': '🇷🇴', 'Romênia': '🇷🇴', 'Romanian': '🇷🇴',
    'Hungary': '🇭🇺', 'Hungria': '🇭🇺', 'Hungarian': '🇭🇺',
    'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'Escócia': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'Scottish': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
    'Wales': '🏴󠁧󠁢󠁷󠁬󠁳󠁿', 'País de Gales': '🏴󠁧󠁢󠁷󠁬󠁳󠁿', 'Welsh': '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
    'Ireland': '🇮🇪', 'Irlanda': '🇮🇪', 'Irish': '🇮🇪',
    'China': '🇨🇳', 'Chinese': '🇨🇳',
    'India': '🇮🇳', 'Índia': '🇮🇳', 'Indian': '🇮🇳',
    'Saudi Arabia': '🇸🇦', 'Arábia Saudita': '🇸🇦',
    'Iran': '🇮🇷', 'Irã': '🇮🇷', 'Iranian': '🇮🇷',
    'Algeria': '🇩🇿', 'Argélia': '🇩🇿', 'Algerian': '🇩🇿',
    'Tunisia': '🇹🇳', 'Tunísia': '🇹🇳', 'Tunisian': '🇹🇳',
    'Congo DR': '🇨🇩', 'RD Congo': '🇨🇩', 'DR Congo': '🇨🇩',
    'Ivory Coast': '🇨🇮', "Côte d'Ivoire": '🇨🇮', 'Costa do Marfim': '🇨🇮',
    'Mali': '🇲🇱', 'Malian': '🇲🇱',
    'Burkina Faso': '🇧🇫',
    'Slovenia': '🇸🇮', 'Eslovênia': '🇸🇮',
    'Slovakia': '🇸🇰', 'Eslováquia': '🇸🇰',
    'Bulgaria': '🇧🇬', 'Bulgária': '🇧🇬',
    'Albania': '🇦🇱', 'Albânia': '🇦🇱',
    'North Macedonia': '🇲🇰', 'Macedônia do Norte': '🇲🇰',
    'Bosnia and Herzegovina': '🇧🇦', 'Bósnia': '🇧🇦',
    'Montenegro': '🇲🇪',
    'Kosovo': '🇽🇰',
    'Iceland': '🇮🇸', 'Islândia': '🇮🇸',
    'Luxembourg': '🇱🇺', 'Luxemburgo': '🇱🇺',
    'Cyprus': '🇨🇾', 'Chipre': '🇨🇾',
    'Israel': '🇮🇱',
    'United Arab Emirates': '🇦🇪', 'Emirados Árabes': '🇦🇪', 'UAE': '🇦🇪',
    'Qatar': '🇶🇦', 'Catar': '🇶🇦',
    'Kuwait': '🇰🇼',
    'Bahrain': '🇧🇭', 'Bahrein': '🇧🇭',
    'Oman': '🇴🇲', 'Omã': '🇴🇲',
}

def get_flag(country):
    """Retorna emoji de bandeira para o país"""
    if pd.isna(country):
        return ''
    # Tratar múltiplas nacionalidades (ex: "Brazil, Italy")
    country_str = str(country).split(',')[0].strip()
    return COUNTRY_FLAGS.get(country_str, '🏳️')

# ============================================
# ESCUDOS DOS CLUBES (URLs)
# ============================================
CLUB_LOGOS = {
    # Série A
    'Atlético MG': 'https://logodetimes.com/times/atletico-mineiro/logo-atletico-mineiro-256.png',
    'Atlético Mineiro': 'https://logodetimes.com/times/atletico-mineiro/logo-atletico-mineiro-256.png',
    'Athletico Paranaense': 'https://logodetimes.com/times/athletico-paranaense/logo-athletico-paranaense-256.png',
    'Athletico PR': 'https://logodetimes.com/times/athletico-paranaense/logo-athletico-paranaense-256.png',
    'Bahia': 'https://logodetimes.com/times/bahia/logo-bahia-256.png',
    'Botafogo': 'https://logodetimes.com/times/botafogo/logo-botafogo-256.png',
    'Corinthians': 'https://logodetimes.com/times/corinthians/logo-corinthians-256.png',
    'Cruzeiro': 'https://logodetimes.com/times/cruzeiro/logo-cruzeiro-256.png',
    'Cuiabá': 'https://logodetimes.com/times/cuiaba/logo-cuiaba-256.png',
    'Flamengo': 'https://logodetimes.com/times/flamengo/logo-flamengo-256.png',
    'Fluminense': 'https://logodetimes.com/times/fluminense/logo-fluminense-256.png',
    'Fortaleza': 'https://logodetimes.com/times/fortaleza/logo-fortaleza-256.png',
    'Grêmio': 'https://logodetimes.com/times/gremio/logo-gremio-256.png',
    'Internacional': 'https://logodetimes.com/times/internacional/logo-internacional-256.png',
    'Juventude': 'https://logodetimes.com/times/juventude/logo-juventude-256.png',
    'Palmeiras': 'https://logodetimes.com/times/palmeiras/logo-palmeiras-256.png',
    'RB Bragantino': 'https://logodetimes.com/times/red-bull-bragantino/logo-red-bull-bragantino-256.png',
    'Red Bull Bragantino': 'https://logodetimes.com/times/red-bull-bragantino/logo-red-bull-bragantino-256.png',
    'Santos': 'https://logodetimes.com/times/santos/logo-santos-256.png',
    'São Paulo': 'https://logodetimes.com/times/sao-paulo/logo-sao-paulo-256.png',
    'Vasco': 'https://logodetimes.com/times/vasco-da-gama/logo-vasco-da-gama-256.png',
    'Vasco da Gama': 'https://logodetimes.com/times/vasco-da-gama/logo-vasco-da-gama-256.png',
    'Vitória': 'https://logodetimes.com/times/vitoria/logo-vitoria-256.png',
    'Atlético GO': 'https://logodetimes.com/times/atletico-goianiense/logo-atletico-goianiense-256.png',
    'Atlético Goianiense': 'https://logodetimes.com/times/atletico-goianiense/logo-atletico-goianiense-256.png',
    'Criciúma': 'https://logodetimes.com/times/criciuma/logo-criciuma-256.png',
    
    # Série B
    'Amazonas': 'https://logodetimes.com/times/amazonas-fc/logo-amazonas-fc-256.png',
    'América Mineiro': 'https://logodetimes.com/times/america-mineiro/logo-america-mineiro-256.png',
    'América MG': 'https://logodetimes.com/times/america-mineiro/logo-america-mineiro-256.png',
    'Avaí': 'https://logodetimes.com/times/avai/logo-avai-256.png',
    'Botafogo SP': 'https://logodetimes.com/times/botafogo-sp/logo-botafogo-sp-256.png',
    'Botafogo-SP': 'https://logodetimes.com/times/botafogo-sp/logo-botafogo-sp-256.png',
    'Brusque': 'https://logodetimes.com/times/brusque/logo-brusque-256.png',
    'Ceará': 'https://logodetimes.com/times/ceara/logo-ceara-256.png',
    'Chapecoense': 'https://logodetimes.com/times/chapecoense/logo-chapecoense-256.png',
    'CRB': 'https://logodetimes.com/times/crb/logo-crb-256.png',
    'Coritiba': 'https://logodetimes.com/times/coritiba/logo-coritiba-256.png',
    'Goiás': 'https://logodetimes.com/times/goias/logo-goias-256.png',
    'Guarani': 'https://logodetimes.com/times/guarani/logo-guarani-256.png',
    'Ituano': 'https://logodetimes.com/times/ituano/logo-ituano-256.png',
    'Mirassol': 'https://logodetimes.com/times/mirassol/logo-mirassol-256.png',
    'Novorizontino': 'https://logodetimes.com/times/novorizontino/logo-novorizontino-256.png',
    'Grêmio Novorizontino': 'https://logodetimes.com/times/novorizontino/logo-novorizontino-256.png',
    'Operário': 'https://logodetimes.com/times/operario-pr/logo-operario-pr-256.png',
    'Operário PR': 'https://logodetimes.com/times/operario-pr/logo-operario-pr-256.png',
    'Paysandu': 'https://logodetimes.com/times/paysandu/logo-paysandu-256.png',
    'Ponte Preta': 'https://logodetimes.com/times/ponte-preta/logo-ponte-preta-256.png',
    'Sport': 'https://logodetimes.com/times/sport/logo-sport-256.png',
    'Sport Recife': 'https://logodetimes.com/times/sport/logo-sport-256.png',
    'Vila Nova': 'https://logodetimes.com/times/vila-nova/logo-vila-nova-256.png',
    'Vila Nova GO': 'https://logodetimes.com/times/vila-nova/logo-vila-nova-256.png',
    'Volta Redonda': 'https://logodetimes.com/times/volta-redonda/logo-volta-redonda-256.png',
    'Remo': 'https://logodetimes.com/times/remo/logo-remo-256.png',
    
    # Outros
    'Santa Cruz': 'https://logodetimes.com/times/santa-cruz/logo-santa-cruz-256.png',
    'Náutico': 'https://logodetimes.com/times/nautico/logo-nautico-256.png',
    'Sport Club do Recife': 'https://logodetimes.com/times/sport/logo-sport-256.png',
    'Londrina': 'https://logodetimes.com/times/londrina/logo-londrina-256.png',
    'ABC': 'https://logodetimes.com/times/abc/logo-abc-256.png',
    'CSA': 'https://logodetimes.com/times/csa/logo-csa-256.png',
    'Sampaio Corrêa': 'https://logodetimes.com/times/sampaio-correa/logo-sampaio-correa-256.png',
    'Tombense': 'https://logodetimes.com/times/tombense/logo-tombense-256.png',
    'Figueirense': 'https://logodetimes.com/times/figueirense/logo-figueirense-256.png',
    'Brasil de Pelotas': 'https://logodetimes.com/times/brasil-de-pelotas/logo-brasil-de-pelotas-256.png',
    'Confiança': 'https://logodetimes.com/times/confianca/logo-confianca-256.png',
    'Paraná': 'https://logodetimes.com/times/parana/logo-parana-256.png',
    'Joinville': 'https://logodetimes.com/times/joinville/logo-joinville-256.png',
    'Luverdense': 'https://logodetimes.com/times/luverdense/logo-luverdense-256.png',
    
    # Internacionais - Argentina
    'River Plate': 'https://logodetimes.com/times/river-plate/logo-river-plate-256.png',
    'Boca Juniors': 'https://logodetimes.com/times/boca-juniors/logo-boca-juniors-256.png',
    'Racing Club': 'https://logodetimes.com/times/racing/logo-racing-256.png',
    'Independiente': 'https://logodetimes.com/times/independiente/logo-independiente-256.png',
    'San Lorenzo': 'https://logodetimes.com/times/san-lorenzo/logo-san-lorenzo-256.png',
    
    # Outros países
    'Peñarol': 'https://logodetimes.com/times/penarol/logo-penarol-256.png',
    'Nacional': 'https://logodetimes.com/times/nacional-uruguai/logo-nacional-uruguai-256.png',
}

def get_club_logo(club_name):
    """Retorna URL do escudo do clube"""
    if pd.isna(club_name):
        return None
    return CLUB_LOGOS.get(str(club_name).strip(), None)

def get_club_logo_html(club_name, size=20):
    """Retorna HTML img tag para o escudo"""
    logo_url = get_club_logo(club_name)
    if logo_url:
        return f'<img src="{logo_url}" width="{size}" height="{size}" style="vertical-align: middle; margin-right: 5px;">'
    return ''

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
# FUNÇÕES AUXILIARES DE CONVERSÃO
# ============================================

def safe_float(val, default=None):
    """Converte valor para float de forma segura (Google Sheets retorna strings)"""
    if pd.isna(val):
        return default
    try:
        # Tratar vírgula como separador decimal
        if isinstance(val, str):
            val = val.replace(',', '.')
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=None):
    """Converte valor para int de forma segura"""
    num = safe_float(val)
    if num is None:
        return default
    return int(num)


def display_int(val, suffix='', default='-'):
    """Retorna string formatada do inteiro ou default"""
    num = safe_int(val)
    if num is None:
        return default
    return f"{num}{suffix}"


def safe_format(val, fmt=".2f", default="-"):
    """Formata valor numérico de forma segura"""
    num = safe_float(val)
    if num is None:
        return default
    try:
        return f"{num:{fmt}}"
    except (ValueError, TypeError):
        return default


def safe_str(val, default='-'):
    """Retorna string segura - trata None, NaN, 'nan', '' como default"""
    if val is None:
        return default
    if pd.isna(val):
        return default
    s = str(val).strip()
    if s.lower() in ('nan', 'none', 'nat', ''):
        return default
    return s


# ============================================
# FUNÇÕES DE CARREGAMENTO
# ============================================

@st.cache_data(ttl=300)  # Cache por 5 minutos para Google Sheets
def load_from_google_sheets():
    """Carrega dados diretamente do Google Sheets"""
    sheets = {
        'Análises': None,
        'Oferecidos': None,
        'SkillCorner': None,
        'WyScout': None
    }
    
    for sheet_name in sheets.keys():
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(sheet_name)}"
        try:
            sheets[sheet_name] = pd.read_csv(url)
        except Exception as e:
            st.warning(f"Erro ao carregar {sheet_name} do Google Sheets: {e}")
            return None
    
    return sheets['Análises'], sheets['Oferecidos'], sheets['SkillCorner'], sheets['WyScout']

@st.cache_data
def load_data(uploaded_file=None, use_google_sheets=True):
    """Carrega dados do Google Sheets ou arquivo local"""
    
    analises, oferecidos, skillcorner, wyscout = None, None, None, None
    
    # Prioridade: 1) Arquivo uploaded, 2) Google Sheets, 3) Arquivo local
    if uploaded_file:
        xlsx = pd.ExcelFile(uploaded_file)
        analises = pd.read_excel(xlsx, sheet_name='Análises')
        oferecidos = pd.read_excel(xlsx, sheet_name='Oferecidos')
        skillcorner = pd.read_excel(xlsx, sheet_name='SkillCorner')
        wyscout = pd.read_excel(xlsx, sheet_name='WyScout')
    elif use_google_sheets:
        try:
            result = load_from_google_sheets()
            if result:
                analises, oferecidos, skillcorner, wyscout = result
        except:
            pass
    
    # Fallback para arquivo local
    if analises is None:
        try:
            xlsx = pd.ExcelFile('Banco_de_Dados___Jogadores-3.xlsx')
            analises = pd.read_excel(xlsx, sheet_name='Análises')
            oferecidos = pd.read_excel(xlsx, sheet_name='Oferecidos')
            skillcorner = pd.read_excel(xlsx, sheet_name='SkillCorner')
            wyscout = pd.read_excel(xlsx, sheet_name='WyScout')
        except:
            return None, None, None, None
    
    # CONVERTER COLUNAS NUMÉRICAS DO WYSCOUT (Google Sheets retorna strings)
    numeric_cols_ws = [col for col in wyscout.columns if col not in ['Jogador', 'Equipa', 'Equipa dentro de um período de tempo seleccionado', 'Posição', 'Naturalidade', 'País de nacionalidade', 'Pé', 'Emprestado', 'JogadorDisplay']]
    for col in numeric_cols_ws:
        if col in wyscout.columns:
            # Substituir vírgula por ponto e converter
            wyscout[col] = wyscout[col].apply(lambda x: str(x).replace(',', '.') if pd.notna(x) and isinstance(x, str) else x)
            wyscout[col] = pd.to_numeric(wyscout[col], errors='coerce')
    
    # CONVERTER COLUNAS NUMÉRICAS DO SKILLCORNER
    exclude_sc = ['player_id', 'player_name', 'short_name', 'birthday', 'team_id', 'team_name', 'competition_edition_id', 'competition_edition_name', 'competition_id', 'competition_name', 'season_id', 'season_name', 'position_group', 'position_group_detailed', 'data_point_id', 'PlayerDisplay']
    for col in skillcorner.columns:
        if col not in exclude_sc:
            skillcorner[col] = skillcorner[col].apply(lambda x: str(x).replace(',', '.') if pd.notna(x) and isinstance(x, str) else x)
            skillcorner[col] = pd.to_numeric(skillcorner[col], errors='coerce')
    
    # CONVERTER COLUNAS NUMÉRICAS DO ANÁLISES
    numeric_cols_an = ['Idade', 'Ano', 'Técnica', 'Físico', 'Tática', 'Mental', 'Nota_Desempenho', 'Potencial']
    for col in numeric_cols_an:
        if col in analises.columns:
            analises[col] = analises[col].apply(lambda x: str(x).replace(',', '.') if pd.notna(x) and isinstance(x, str) else x)
            analises[col] = pd.to_numeric(analises[col], errors='coerce')
    
    # Criar coluna de display para diferenciar jogadores com nomes iguais
    # Formato: "Jogador (Equipa)" ou "Jogador (Equipa, Idade)" se ainda duplicado
    wyscout['JogadorDisplay'] = wyscout.apply(
        lambda r: f"{r['Jogador']} ({r['Equipa']})" if pd.notna(r['Equipa']) else r['Jogador'], 
        axis=1
    )
    
    # Verificar duplicatas e adicionar idade para diferenciar
    dup_mask = wyscout['JogadorDisplay'].duplicated(keep=False)
    
    def format_display_with_age(r):
        idade = safe_int(r['Idade'])
        if idade is not None:
            return f"{r['Jogador']} ({r['Equipa']}, {idade}a)"
        else:
            return f"{r['Jogador']} ({r['Equipa']}, {r['Posição']})"
    
    wyscout.loc[dup_mask, 'JogadorDisplay'] = wyscout.loc[dup_mask].apply(format_display_with_age, axis=1)
    
    # Se AINDA houver duplicatas (dados realmente duplicados), adicionar índice
    dup_mask2 = wyscout['JogadorDisplay'].duplicated(keep=False)
    if dup_mask2.any():
        # Adicionar contador para cada duplicata
        wyscout['_dup_count'] = wyscout.groupby('JogadorDisplay').cumcount() + 1
        wyscout.loc[dup_mask2, 'JogadorDisplay'] = wyscout.loc[dup_mask2].apply(
            lambda r: f"{r['JogadorDisplay']} #{r['_dup_count']}" if r['_dup_count'] > 1 else r['JogadorDisplay'],
            axis=1
        )
        wyscout.drop('_dup_count', axis=1, inplace=True)
    
    # Criar coluna de display para SkillCorner também
    skillcorner['PlayerDisplay'] = skillcorner.apply(
        lambda r: f"{r['player_name']} ({r['team_name']})" if pd.notna(r['team_name']) else r['player_name'], 
        axis=1
    )
    
    # Verificar duplicatas no SkillCorner e adicionar contador
    dup_mask_sc = skillcorner['PlayerDisplay'].duplicated(keep=False)
    if dup_mask_sc.any():
        skillcorner['_dup_count'] = skillcorner.groupby('PlayerDisplay').cumcount() + 1
        skillcorner.loc[dup_mask_sc, 'PlayerDisplay'] = skillcorner.loc[dup_mask_sc].apply(
            lambda r: f"{r['PlayerDisplay']} #{r['_dup_count']}" if r['_dup_count'] > 1 else r['PlayerDisplay'],
            axis=1
        )
        skillcorner.drop('_dup_count', axis=1, inplace=True)
    
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
    val = safe_float(value)
    if val is None:
        return 50
    # Converter série para numérico
    valid = pd.to_numeric(series, errors='coerce').dropna()
    if len(valid) == 0:
        return 50
    return float((valid < val).sum() / len(valid) * 100)


def calculate_index(player_row, metrics, df_all):
    percentiles = []
    for metric in metrics:
        try:
            if metric in player_row.index and metric in df_all.columns:
                val = safe_float(player_row[metric])
                if val is not None:
                    perc = calculate_percentile(val, df_all[metric])
                    if pd.notna(perc):
                        if 'Faltas/90' in metric or 'Cartões' in metric or 'sofridos' in metric.lower():
                            perc = 100 - perc
                        percentiles.append(float(perc))
        except:
            continue
    if percentiles:
        return float(np.nanmean(percentiles))
    return 50.0


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
    
    # Usar JogadorDisplay para hover e busca (diferencia nomes iguais)
    display_col = 'JogadorDisplay' if 'JogadorDisplay' in df_valid.columns else 'Jogador' if 'Jogador' in df_valid.columns else 'player_name'
    name_col = 'Jogador' if 'Jogador' in df_valid.columns else 'player_name'
    
    fig.add_trace(go.Scatter(
        x=df_valid[x_col], y=df_valid[y_col],
        mode='markers',
        marker=dict(size=7, color='#6b7280', opacity=0.5),
        text=df_valid[display_col],
        hovertemplate='<b>%{text}</b><br>%{x:.2f} | %{y:.2f}<extra></extra>',
        showlegend=False
    ))
    
    # Highlight pode ser JogadorDisplay ou Jogador
    if highlight:
        # Tentar buscar por JogadorDisplay primeiro
        if display_col in df_valid.columns and highlight in df_valid[display_col].values:
            p = df_valid[df_valid[display_col] == highlight].iloc[0]
            label = p[name_col].split()[0] if name_col in p else highlight.split()[0]
        elif name_col in df_valid.columns and highlight in df_valid[name_col].values:
            p = df_valid[df_valid[name_col] == highlight].iloc[0]
            label = highlight.split()[0]
        else:
            p = None
            label = None
        
        if p is not None:
            fig.add_trace(go.Scatter(
                x=[p[x_col]], y=[p[y_col]],
                mode='markers+text',
                marker=dict(size=16, color=COLORS['accent'], line=dict(width=3, color='white')),
                text=[label],
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
            
            # Obter bandeira e escudo
            flag = get_flag(p.get('Nacionalidade', ''))
            club_logo = get_club_logo_html(p.get('Clube', ''), size=24)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div style="background: {COLORS['card']}; border-radius: 12px; padding: 24px; border: 1px solid {COLORS['border']};">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 28px;">{flag}</span>
                        <div>
                            <div style="color: {COLORS['accent']}; font-size: 12px; font-weight: 600; letter-spacing: 1px;">{safe_str(p.get('Posição'), 'JOGADOR')}</div>
                            <div style="color: white; font-size: 32px; font-weight: 800; margin: 4px 0;">{p['Nome']}</div>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 16px;">
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Idade</div><div style="color: white; font-size: 14px;">{display_int(p['Idade'], ' anos')}</div></div>
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Clube</div><div style="color: white; font-size: 14px;">{club_logo}{safe_str(p.get('Clube'))}</div></div>
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Liga</div><div style="color: white; font-size: 14px;">{safe_str(p.get('Liga'))}</div></div>
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Perfil</div><div style="color: white; font-size: 14px;">{safe_str(p.get('Perfil'))}</div></div>
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Contrato</div><div style="color: white; font-size: 14px;">{str(p['Contrato']).split(' ')[0] if pd.notna(p.get('Contrato')) and str(p.get('Contrato')) not in ('nan', '') else '-'}</div></div>
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Modelo</div><div style="color: white; font-size: 14px;">{safe_str(p.get('Modelo'))}</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                nota = safe_float(p.get('Nota_Desempenho'))
                if nota is not None and nota > 0:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {COLORS['accent']}, #b91c1c); border-radius: 12px; padding: 20px; text-align: center;">
                        <div style="color: rgba(255,255,255,0.7); font-size: 10px; letter-spacing: 1px;">NOTA GERAL</div>
                        <div style="color: white; font-size: 42px; font-weight: 800;">{nota:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                if pd.notna(p.get('Link_TM')):
                    st.link_button("🔗 Transfermarkt", p['Link_TM'], width='stretch')
            
            # BUSCAR JOGADOR NO WYSCOUT PARA GRÁFICOS DETALHADOS
            nome_jogador = p['Nome']
            clube_jogador = safe_str(p.get('Clube', ''), '')
            posicao_jogador = safe_str(p.get('Posição', ''), '')
            
            # Tentar match automático no WyScout para pré-selecionar
            auto_match_idx = 0
            jogadores_ws_list = sorted(wyscout['JogadorDisplay'].dropna().unique().tolist())
            
            # Buscar melhor match por nome + clube
            best_matches = []
            nome_norm = normalize_name(nome_jogador)
            nome_parts = set(nome_norm.split())
            
            for jwd in jogadores_ws_list:
                row = wyscout[wyscout['JogadorDisplay'] == jwd].iloc[0]
                jogador_norm = normalize_name(row['Jogador'])
                jogador_parts = set(jogador_norm.split())
                
                score = 0
                
                # Match exato = melhor
                if nome_norm == jogador_norm:
                    score = 100
                # Containment - exigir que ambos tenham mesma qtd de palavras OU nome curto tenha >= 2 palavras
                elif nome_norm in jogador_norm or jogador_norm in nome_norm:
                    shorter = min(nome_norm, jogador_norm, key=len)
                    longer = max(nome_norm, jogador_norm, key=len)
                    shorter_parts = shorter.split()
                    longer_parts = longer.split()
                    if len(shorter_parts) >= 2:
                        # "Rodrigo Saravia" in "Rodrigo Saravia Santos" → alta confiança
                        score = 80
                    elif len(longer_parts) == 1:
                        # Ambos 1 palavra e um contém o outro
                        score = 70
                    else:
                        # 1 palavra tipo "Rodrigo" matching "Rodrigo Saravia" → baixa confiança
                        score = 25
                else:
                    # Overlap de partes do nome
                    common = nome_parts & jogador_parts
                    if common:
                        # Penalizar se só 1 parte comum e ambos têm mais partes
                        overlap_ratio = len(common) / max(len(nome_parts), len(jogador_parts))
                        if overlap_ratio >= 0.5:
                            score = overlap_ratio * 60
                        elif len(common) == 1 and max(len(nome_parts), len(jogador_parts)) > 1:
                            # 1 parte em comum de várias = pouca confiança
                            score = 15
                
                # Bonus se mesmo clube
                if clube_jogador and pd.notna(row.get('Equipa')):
                    clube_norm = normalize_name(str(clube_jogador))
                    equipa_norm = normalize_name(str(row['Equipa']))
                    if clube_norm and equipa_norm:
                        if clube_norm == equipa_norm:
                            score += 25
                        elif clube_norm.split()[0] in equipa_norm or equipa_norm.split()[0] in clube_norm:
                            score += 15
                
                if score > 30:  # Threshold mínimo para considerar
                    best_matches.append((jwd, score))
            
            best_matches.sort(key=lambda x: -x[1])
            
            if best_matches:
                try:
                    auto_match_idx = jogadores_ws_list.index(best_matches[0][0])
                except ValueError:
                    auto_match_idx = 0
            
            # SELETOR MANUAL DE JOGADOR WYSCOUT
            st.markdown(f"""
            <div style="background: {COLORS['card']}; border-radius: 8px; padding: 8px 12px; margin: 8px 0; border: 1px solid {COLORS['border']};">
                <span style="color: {COLORS['text_muted']}; font-size: 11px;">📊 Vincular dados Wyscout ao jogador selecionado:</span>
            </div>
            """, unsafe_allow_html=True)
            
            ws_selected = st.selectbox(
                "Jogador Wyscout", 
                jogadores_ws_list, 
                index=auto_match_idx,
                key='ws_perfil_match'
            )
            
            ws_match = None
            if ws_selected:
                ws_row = wyscout[wyscout['JogadorDisplay'] == ws_selected]
                if not ws_row.empty:
                    ws_match = ws_row.iloc[0]
            
            # Determinar posição para índices
            posicao_categoria = None
            categorias_validas = list(INDICES_CONFIG.keys())  # ['Atacante', 'Extremo', 'Meia', 'Volante', 'Lateral', 'Zagueiro', 'Goleiro']
            
            if posicao_jogador:
                pos_str = str(posicao_jogador).strip()
                # 1) Verificar se já é um nome de categoria válido
                for cat in categorias_validas:
                    if cat.lower() == pos_str.lower():
                        posicao_categoria = cat
                        break
                
                # 2) Verificar aliases comuns em português
                if posicao_categoria is None:
                    POSICAO_ALIAS = {
                        'centroavante': 'Atacante', 'atacante': 'Atacante', 'ponta de lança': 'Atacante', 'ca': 'Atacante', '9': 'Atacante',
                        'ponta': 'Extremo', 'extremo': 'Extremo', 'ala': 'Extremo', 'pe': 'Extremo', 'pd': 'Extremo',
                        'meia': 'Meia', 'meio-campista': 'Meia', 'meia ofensivo': 'Meia', 'meia-atacante': 'Meia', 'armador': 'Meia',
                        'volante': 'Volante', 'primeiro volante': 'Volante', 'segundo volante': 'Volante', 'cabeça de área': 'Volante',
                        'lateral': 'Lateral', 'lateral-direito': 'Lateral', 'lateral-esquerdo': 'Lateral', 'ld': 'Lateral', 'le': 'Lateral', 'ala direito': 'Lateral', 'ala esquerdo': 'Lateral',
                        'zagueiro': 'Zagueiro', 'defensor central': 'Zagueiro', 'beque': 'Zagueiro',
                        'goleiro': 'Goleiro', 'guarda-redes': 'Goleiro', 'gr': 'Goleiro',
                    }
                    if pos_str.lower() in POSICAO_ALIAS:
                        posicao_categoria = POSICAO_ALIAS[pos_str.lower()]
                
                # 3) Tentar siglas Wyscout (DMF, CF, etc.)
                if posicao_categoria is None:
                    for pos in pos_str.replace(' ', '').split(','):
                        if pos in POSICAO_MAP:
                            posicao_categoria = POSICAO_MAP[pos]
                            break
            
            if posicao_categoria is None and ws_match is not None:
                posicao_categoria = get_posicao_categoria(ws_match.get('Posição', ''))
            
            if posicao_categoria is None:
                posicao_categoria = 'Meia'  # Default
            
            # Seletor de categoria de posição (override manual)
            categorias_disponiveis = list(INDICES_CONFIG.keys())
            cat_idx = categorias_disponiveis.index(posicao_categoria) if posicao_categoria in categorias_disponiveis else 0
            posicao_categoria = st.selectbox("Categoria de Posição", categorias_disponiveis, index=cat_idx, key='cat_perfil')
            
            # LEGENDA
            st.markdown(create_legend_html(), unsafe_allow_html=True)
            
            if ws_match is not None:
                # Filtrar jogadores da mesma posição
                wyscout_pos = wyscout[wyscout['Posição'].apply(get_posicao_categoria) == posicao_categoria].copy()
                n_jogadores_pos = len(wyscout_pos)
                
                # Calcular índices compostos
                indices = INDICES_CONFIG.get(posicao_categoria, INDICES_CONFIG['Meia'])
                indices_values = {idx_name: calculate_index(ws_match, metrics, wyscout) for idx_name, metrics in indices.items()}
                
                # Header com info do match
                st.markdown(f"""
                <div style="background: {COLORS['card']}; border-radius: 8px; padding: 12px; margin: 16px 0; border: 1px solid {COLORS['border']}; text-align: center;">
                    <span style="color: {COLORS['accent']}; font-weight: 600;">Dados Wyscout:</span>
                    <span style="color: white; font-weight: 600;"> {ws_match['Jogador']}</span>
                    <span style="color: {COLORS['text_secondary']};"> • {ws_match['Equipa']} • {display_int(ws_match['Minutos jogados:'], ' min', '0 min')}</span>
                    <span style="color: {COLORS['text_muted']};"> | Comparando com {n_jogadores_pos} {posicao_categoria.lower()}s</span>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(create_section_title("📊", f"Índices Compostos ({posicao_categoria})"), unsafe_allow_html=True)
                    st.plotly_chart(create_wyscout_radar(indices_values), width='stretch', config={'displayModeBar': False}, key="radar_idx_t1")
                
                with col2:
                    # Métricas individuais mais importantes para a posição
                    st.markdown(create_section_title("📈", "Métricas Principais"), unsafe_allow_html=True)
                    
                    # Pegar as métricas mais relevantes
                    all_metrics = []
                    for idx_name, metrics in indices.items():
                        all_metrics.extend(metrics[:2])  # 2 principais de cada índice
                    
                    # Limitar a 12 métricas
                    top_metrics = all_metrics[:12]
                    metrics_perc = {}
                    for m in top_metrics:
                        if m in ws_match.index and m in wyscout.columns:
                            perc = calculate_percentile(ws_match[m], wyscout[m])
                            # Nome curto para o radar
                            short_name = m.replace('/90', '').replace(', %', '%').replace('Duelos ', '').replace('ganhos', '%')[:15]
                            metrics_perc[short_name] = perc
                    
                    if metrics_perc:
                        st.plotly_chart(create_wyscout_radar(metrics_perc), width='stretch', config={'displayModeBar': False}, key="radar_met_t1")
                
                # RANKING DA POSIÇÃO
                st.markdown(create_section_title("🏆", f"Ranking de {posicao_categoria}s"), unsafe_allow_html=True)
                
                # Calcular índice médio para todos da posição
                ranking_data = []
                for _, row in wyscout_pos.iterrows():
                    try:
                        idx_vals = []
                        for metrics in indices.values():
                            idx_val = calculate_index(row, metrics, wyscout)
                            if pd.notna(idx_val) and isinstance(idx_val, (int, float)):
                                idx_vals.append(float(idx_val))
                        
                        if idx_vals:
                            media = float(np.nanmean(idx_vals))
                            if pd.notna(media):
                                ranking_data.append({
                                    'Jogador': row['Jogador'],
                                    'Clube': row['Equipa'],
                                    'Idade': safe_int(row.get('Idade')),
                                    'Min': safe_int(row.get('Minutos jogados:')),
                                    'Índice Médio': media
                                })
                    except Exception:
                        continue
                
                if ranking_data:
                    ranking_df = pd.DataFrame(ranking_data)
                    ranking_df = ranking_df.sort_values('Índice Médio', ascending=False).head(20)
                    ranking_df['#'] = range(1, len(ranking_df) + 1)
                    ranking_df = ranking_df[['#', 'Jogador', 'Clube', 'Idade', 'Min', 'Índice Médio']]
                    ranking_df['Índice Médio'] = ranking_df['Índice Médio'].apply(lambda x: f"{x:.0f}")
                    
                    # Destacar o jogador selecionado
                    st.dataframe(
                        ranking_df,
                        width='stretch',
                        hide_index=True,
                        column_config={
                            '#': st.column_config.NumberColumn(width='small'),
                            'Jogador': st.column_config.TextColumn(width='medium'),
                            'Clube': st.column_config.TextColumn(width='medium'),
                            'Idade': st.column_config.NumberColumn(width='small'),
                            'Min': st.column_config.NumberColumn(width='small'),
                            'Índice Médio': st.column_config.TextColumn(width='small'),
                        }
                    )
            
            else:
                # Se não encontrou no WyScout, mostrar só atributos qualitativos
                st.info(f"⚠️ Jogador '{nome_jogador}' não encontrado na base WyScout. Mostrando apenas atributos qualitativos.")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(create_section_title("📊", "Atributos Qualitativos"), unsafe_allow_html=True)
                    attrs = {
                        'Técnica': safe_float(p.get('Técnica'), 2.5) / 5 * 100,
                        'Físico': safe_float(p.get('Físico'), 2.5) / 5 * 100,
                        'Tática': safe_float(p.get('Tática'), 2.5) / 5 * 100,
                        'Mental': safe_float(p.get('Mental'), 2.5) / 5 * 100,
                    }
                    st.plotly_chart(create_wyscout_radar(attrs), width='stretch', config={'displayModeBar': False}, key="radar_attrs_fb")
                
                with col2:
                    st.markdown(create_section_title("⭐", "Potencial"), unsafe_allow_html=True)
                    perc = attrs.copy()
                    perc['Potencial'] = safe_float(p.get('Potencial'), 2.5) / 5 * 100
                    st.plotly_chart(create_wyscout_radar(perc), width='stretch', config={'displayModeBar': False}, key="radar_pot_fb")
            
            # Análise Qualitativa
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
        
        jogadores_ws = sorted(wyscout['JogadorDisplay'].dropna().unique().tolist())
        
        col1, col2 = st.columns([2, 1])
        with col1:
            jogador_ws = st.selectbox("Jogador (Wyscout)", jogadores_ws, key='ws_player')
        with col2:
            categoria = st.selectbox("Categoria de Posição", list(INDICES_CONFIG.keys()), key='cat_indices')
        
        if jogador_ws:
            player_ws = wyscout[wyscout['JogadorDisplay'] == jogador_ws].iloc[0]
            
            # Obter bandeira e escudo
            flag_ws = get_flag(player_ws.get('País de nacionalidade', ''))
            club_logo_ws = get_club_logo_html(player_ws.get('Equipa', ''), size=20)
            
            st.markdown(f"""
            <div style="background: {COLORS['card']}; border-radius: 12px; padding: 16px; margin: 16px 0; border: 1px solid {COLORS['border']};">
                <span style="font-size: 20px;">{flag_ws}</span>
                <span style="color: {COLORS['accent']}; font-weight: 600;">{player_ws['Posição']}</span> | 
                <span style="color: white; font-weight: 700; font-size: 18px;">{player_ws['Jogador']}</span> | 
                <span style="color: {COLORS['text_secondary']};">{club_logo_ws}{player_ws['Equipa']} • {display_int(player_ws['Idade'], ' anos')} • {display_int(player_ws['Minutos jogados:'], ' min', '0 min')}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # LEGENDA
            st.markdown(create_legend_html(), unsafe_allow_html=True)
            
            indices = INDICES_CONFIG.get(categoria, {})
            indices_values = {idx_name: calculate_index(player_ws, metrics, wyscout) for idx_name, metrics in indices.items()}
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_wyscout_radar(indices_values), width='stretch', config={'displayModeBar': False}, key="radar_indices")
            with col2:
                st.plotly_chart(create_bar_chart(indices_values, "Ranking Percentil"), width='stretch', config={'displayModeBar': False}, key="bar_indices")
            
            st.markdown(create_section_title("🔍", "Detalhamento por Índice"), unsafe_allow_html=True)
            
            for idx_name, metrics in indices.items():
                with st.expander(f"📊 {idx_name} — Percentil: {indices_values[idx_name]:.0f}"):
                    cols = st.columns(min(5, len(metrics)))
                    for i, m in enumerate(metrics):
                        if m in player_ws.index:
                            val = player_ws[m]
                            perc = calculate_percentile(val, wyscout[m])
                            color = get_color(perc)
                            val_fmt = safe_format(val, ".2f", "-")
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
        
        jogadores_ws = sorted(wyscout['JogadorDisplay'].dropna().unique().tolist())
        
        col1, col2 = st.columns([2, 1])
        with col1:
            jogador_rel_display = st.selectbox("Selecione o Jogador", jogadores_ws, key='rel_player')
        with col2:
            # SELETOR DE POSIÇÃO PARA O RELATÓRIO
            posicao_rel = st.selectbox("Posição para Índices", list(INDICES_CONFIG.keys()), key='pos_rel')
        
        if jogador_rel_display:
            player_rel = wyscout[wyscout['JogadorDisplay'] == jogador_rel_display].iloc[0]
            jogador_rel = player_rel['Jogador']  # Nome original para scatter
            
            # Obter bandeira e escudo
            flag_rel = get_flag(player_rel.get('País de nacionalidade', ''))
            club_logo_rel = get_club_logo_html(player_rel.get('Equipa', ''), size=24)
            
            st.markdown(f"""
            <div style="background: {COLORS['card']}; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 2px solid {COLORS['accent']};">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 32px;">{flag_rel}</span>
                    <div>
                        <div style="color: {COLORS['accent']}; font-size: 13px; font-weight: 600;">{player_rel['Posição']} → AVALIANDO COMO: {posicao_rel.upper()}</div>
                        <div style="color: white; font-size: 30px; font-weight: 800; margin: 8px 0;">{jogador_rel}</div>
                    </div>
                </div>
                <div style="color: {COLORS['text_secondary']}; font-size: 15px; margin-top: 10px;">
                    {club_logo_rel}{player_rel['Equipa']} • {display_int(player_rel['Idade'], ' anos')} • 
                    {display_int(player_rel['Partidas jogadas'], ' jogos', '0 jogos')} • 
                    {display_int(player_rel['Minutos jogados:'], ' min', '0 min')}
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
                st.plotly_chart(create_wyscout_radar(indices_values), width='stretch', config={'displayModeBar': False}, key="radar_rel")
            with col2:
                st.markdown(create_section_title("📈", "Rankings"), unsafe_allow_html=True)
                st.plotly_chart(create_bar_chart(indices_values), width='stretch', config={'displayModeBar': False}, key="bar_rel")
            
            st.markdown(create_section_title("📍", f"Posicionamento vs {posicao_rel}s da Liga"), unsafe_allow_html=True)
            
            # Filtrar jogadores da mesma posição
            wyscout_pos = wyscout[wyscout['Posição'].apply(get_posicao_categoria) == posicao_rel].copy()
            
            # SEMPRE incluir o jogador selecionado, mesmo que não seja da posição filtrada
            jogador_row = wyscout[wyscout['JogadorDisplay'] == jogador_rel_display]
            if len(jogador_row) > 0 and jogador_rel_display not in wyscout_pos['JogadorDisplay'].values:
                wyscout_pos = pd.concat([wyscout_pos, jogador_row], ignore_index=True)
            
            st.caption(f"Comparando com {len(wyscout_pos)} {posicao_rel.lower()}s da base")
            
            col1, col2 = st.columns(2)
            with col1:
                if posicao_rel in ['Atacante', 'Extremo']:
                    fig = create_scatter_plot(wyscout_pos, 'Golos esperados/90', 'Assistências esperadas/90', jogador_rel_display, 'xG vs xA por 90')
                else:
                    fig = create_scatter_plot(wyscout_pos, 'Passes progressivos/90', 'Corridas progressivas/90', jogador_rel_display, 'Passes Prog. vs Corridas Prog.')
                st.plotly_chart(fig, width='stretch', config={'displayModeBar': False}, key="scatter1")
            
            with col2:
                if posicao_rel in ['Zagueiro', 'Volante']:
                    fig = create_scatter_plot(wyscout_pos, 'Duelos defensivos/90', 'Duelos defensivos ganhos, %', jogador_rel_display, 'Volume vs Eficiência Defensiva')
                else:
                    fig = create_scatter_plot(wyscout_pos, 'Dribles/90', 'Dribles com sucesso, %', jogador_rel_display, 'Volume vs Eficiência 1x1')
                st.plotly_chart(fig, width='stretch', config={'displayModeBar': False}, key="scatter2")
            
            # SkillCorner - DADOS FÍSICOS
            st.markdown(create_section_title("🏃", "Dados Físicos SkillCorner"), unsafe_allow_html=True)
            
            # Criar lista de jogadores SkillCorner para seleção (com time para diferenciar)
            sc_players_list = skillcorner['PlayerDisplay'].dropna().unique().tolist()
            sc_players_list = sorted(sc_players_list)
            
            # Tentar match automático para sugerir
            sc_auto_match = find_skillcorner_player(jogador_rel, skillcorner)
            default_idx = 0
            if sc_auto_match is not None:
                try:
                    auto_display = f"{sc_auto_match['player_name']} ({sc_auto_match['team_name']})"
                    default_idx = sc_players_list.index(auto_display)
                except ValueError:
                    default_idx = 0
            
            # Selectbox para seleção manual
            col_sc1, col_sc2 = st.columns([3, 1])
            with col_sc1:
                sc_selected_display = st.selectbox(
                    "Selecionar Jogador SkillCorner",
                    sc_players_list,
                    index=default_idx,
                    key='sc_player_select',
                    help="Match automático sugerido. Selecione outro se estiver incorreto."
                )
            with col_sc2:
                if sc_auto_match is not None:
                    auto_display = f"{sc_auto_match['player_name']} ({sc_auto_match['team_name']})"
                    if sc_selected_display == auto_display:
                        st.markdown(f"<br><span style='color: {COLORS['elite']}; font-size: 12px;'>✓ Match automático</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<br><span style='color: {COLORS['above']}; font-size: 12px;'>✎ Seleção manual</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<br><span style='color: {COLORS['above']}; font-size: 12px;'>✎ Seleção manual</span>", unsafe_allow_html=True)
            
            # Buscar jogador selecionado
            sc_player = skillcorner[skillcorner['PlayerDisplay'] == sc_selected_display].iloc[0] if sc_selected_display else None
            
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
                            val_float = safe_float(val)
                            if val_float is None:
                                continue
                            # Verificar se não é datetime
                            if hasattr(val, 'year'):
                                continue
                            
                            # Rank já é o percentil - converter para float
                            rank_float = safe_float(rank)
                            if rank_float is not None:
                                physical_perc[label] = rank_float
                                physical_vals[label] = val_float
                    except Exception as e:
                        continue  # Pular métricas com erro
                
                if physical_perc:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(create_wyscout_radar(physical_perc), width='stretch', config={'displayModeBar': False}, key="radar_sc_phys")
                    with col2:
                        st.plotly_chart(create_bar_chart(physical_perc, "Perfil Físico (Percentil)"), width='stretch', config={'displayModeBar': False}, key="bar_sc_phys")
                    
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
                        st.plotly_chart(create_wyscout_radar(sc_style_perc), width='stretch', config={'displayModeBar': False}, key="radar_sc_style")
                    with col2:
                        st.plotly_chart(create_bar_chart(sc_style_perc, "Índices de Estilo"), width='stretch', config={'displayModeBar': False}, key="bar_sc_style")
                else:
                    st.info("ℹ️ Índices de estilo de jogo não disponíveis para este jogador (apenas 435 de 3.298 jogadores têm)")
    
    # ===== TAB 4: COMPARATIVO =====
    with tab4:
        st.markdown(create_section_title("🔄", "Comparar Jogadores"), unsafe_allow_html=True)
        
        jogadores_ws = sorted(wyscout['JogadorDisplay'].dropna().unique().tolist())
        
        col1, col2 = st.columns(2)
        with col1:
            j1_display = st.selectbox("Jogador 1", jogadores_ws, key='cmp1')
        with col2:
            j2_display = st.selectbox("Jogador 2", jogadores_ws, index=min(1, len(jogadores_ws)-1), key='cmp2')
        
        categoria_cmp = st.selectbox("Categoria para comparação", list(INDICES_CONFIG.keys()), key='cat_cmp')
        
        if j1_display and j2_display and j1_display != j2_display:
            p1 = wyscout[wyscout['JogadorDisplay'] == j1_display].iloc[0]
            p2 = wyscout[wyscout['JogadorDisplay'] == j2_display].iloc[0]
            j1 = p1['Jogador']  # Nome original
            j2 = p2['Jogador']  # Nome original
            
            # Obter bandeiras e escudos
            flag_p1 = get_flag(p1.get('País de nacionalidade', ''))
            flag_p2 = get_flag(p2.get('País de nacionalidade', ''))
            club_logo_p1 = get_club_logo_html(p1.get('Equipa', ''), size=18)
            club_logo_p2 = get_club_logo_html(p2.get('Equipa', ''), size=18)
            
            indices = INDICES_CONFIG.get(categoria_cmp, {})
            idx1 = {n: calculate_index(p1, m, wyscout) for n, m in indices.items()}
            idx2 = {n: calculate_index(p2, m, wyscout) for n, m in indices.items()}
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div style="background: rgba(220,38,38,0.2); border: 2px solid {COLORS['accent']}; border-radius: 12px; padding: 16px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 24px;">{flag_p1}</span>
                        <div>
                            <div style="color: {COLORS['accent']}; font-weight: 600;">{p1['Posição']}</div>
                            <div style="color: white; font-size: 20px; font-weight: 700;">{j1}</div>
                        </div>
                    </div>
                    <div style="color: {COLORS['text_secondary']}; margin-top: 8px;">{club_logo_p1}{p1['Equipa']} • {display_int(p1['Idade'], ' anos')}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="background: rgba(59,130,246,0.2); border: 2px solid #3b82f6; border-radius: 12px; padding: 16px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 24px;">{flag_p2}</span>
                        <div>
                            <div style="color: #3b82f6; font-weight: 600;">{p2['Posição']}</div>
                            <div style="color: white; font-size: 20px; font-weight: 700;">{j2}</div>
                        </div>
                    </div>
                    <div style="color: {COLORS['text_secondary']}; margin-top: 8px;">{club_logo_p2}{p2['Equipa']} • {display_int(p2['Idade'], ' anos')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.plotly_chart(create_comparison_radar(idx1, idx2, j1, j2), width='stretch', config={'displayModeBar': False}, key="radar_cmp")
            
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
            
            st.dataframe(pd.DataFrame(comparison_data), width='stretch', hide_index=True)
            
            # COMPARATIVO FÍSICO SKILLCORNER
            st.markdown(create_section_title("🏃", "Comparativo Físico (SkillCorner)"), unsafe_allow_html=True)
            
            # Buscar jogadores no SkillCorner (com time para diferenciar)
            sc_players_list = sorted(skillcorner['PlayerDisplay'].dropna().unique().tolist())
            
            col_sc1, col_sc2 = st.columns(2)
            with col_sc1:
                sc1_auto = find_skillcorner_player(j1, skillcorner)
                sc1_default = 0
                if sc1_auto is not None:
                    try:
                        auto_display = f"{sc1_auto['player_name']} ({sc1_auto['team_name']})"
                        sc1_default = sc_players_list.index(auto_display)
                    except ValueError:
                        sc1_default = 0
                sc1_display = st.selectbox(f"SkillCorner: {j1}", sc_players_list, index=sc1_default, key='sc_cmp1')
            with col_sc2:
                sc2_auto = find_skillcorner_player(j2, skillcorner)
                sc2_default = 0
                if sc2_auto is not None:
                    try:
                        auto_display = f"{sc2_auto['player_name']} ({sc2_auto['team_name']})"
                        sc2_default = sc_players_list.index(auto_display)
                    except ValueError:
                        sc2_default = 0
                sc2_display = st.selectbox(f"SkillCorner: {j2}", sc_players_list, index=sc2_default, key='sc_cmp2')
            
            sc1 = skillcorner[skillcorner['PlayerDisplay'] == sc1_display].iloc[0] if sc1_display else None
            sc2 = skillcorner[skillcorner['PlayerDisplay'] == sc2_display].iloc[0] if sc2_display else None
            
            if sc1 is not None and sc2 is not None:
                physical_metrics = {
                    'Vel. Máx (km/h)': 'avg_psv99_rank',
                    'Top 5 Vel': 'avg_top_5_psv99_rank',
                    'Dist. Total /90': 'distance_per_90_rank',
                    'Dist. Alta Int /90': 'hi_distance_per_90_rank',
                    'Dist. Sprint /90': 'sprint_distance_per_90_rank',
                    'Ações Alta Int /90': 'hi_count_per_90_rank',
                    'm/min (posse)': 'avg_meters_per_minute_tip_rank',
                    'Acel → HSR /90': 'explacceltohsr_count_per_90_rank',
                    'Acel → Sprint /90': 'explacceltosprint_count_per_90_rank',
                }
                
                phys1 = {}
                phys2 = {}
                for label, rank_col in physical_metrics.items():
                    if rank_col in sc1.index and rank_col in sc2.index:
                        r1 = sc1.get(rank_col)
                        r2 = sc2.get(rank_col)
                        if pd.notna(r1) and pd.notna(r2):
                            try:
                                phys1[label] = float(r1)
                                phys2[label] = float(r2)
                            except:
                                pass
                
                if phys1 and phys2:
                    st.plotly_chart(create_comparison_radar(phys1, phys2, j1, j2), width='stretch', config={'displayModeBar': False}, key="radar_phys_cmp")
                    
                    # Tabela comparativa física
                    phys_comparison = []
                    for label in phys1.keys():
                        v1, v2 = phys1[label], phys2[label]
                        diff = v1 - v2
                        phys_comparison.append({
                            'Métrica': label,
                            f'{j1}': f"P{v1:.0f}",
                            f'{j2}': f"P{v2:.0f}",
                            'Diferença': f"+{diff:.0f}" if diff > 0 else f"{diff:.0f}",
                            'Vantagem': '🔴' if diff > 0 else '🔵' if diff < 0 else '='
                        })
                    
                    st.dataframe(pd.DataFrame(phys_comparison), width='stretch', hide_index=True)
                else:
                    st.warning("⚠️ Dados físicos não disponíveis para comparação")
            else:
                st.warning("⚠️ Selecione os jogadores no SkillCorner para comparar dados físicos")
    
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
        
        st.dataframe(df_show, width='stretch', height=500)
        st.download_button("📥 Exportar CSV", df_show.to_csv(index=False).encode('utf-8'), f"{source.lower()}.csv", key='download_csv')


if __name__ == "__main__":
    main()
