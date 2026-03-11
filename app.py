import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from urllib.parse import quote, urlparse
import html as html_module
import logging
import os
import requests
from bs4 import BeautifulSoup
import re
from fuzzy_match import build_skillcorner_index, find_skillcorner_player
from auth import init_db, is_authenticated, render_login_page, logout, get_current_user, render_admin_panel
from similarity import (
    compute_weighted_cosine_similarity, get_similarity_breakdown,
    calculate_weighted_index, calculate_all_indices,
    calculate_overall_score, rank_players_weighted,
    get_top_metrics_for_position, calculate_metric_percentiles,
    POSITION_WEIGHTS, INVERTED_METRICS
)

# Motor Preditivo v3 (calibração acadêmica)
try:
    from predictive_engine import (
        ScoutScorePreditivo,
        ContractSuccessPredictor,
        compute_advanced_similarity,
        calculate_overall_score_v3,
        TacticalClusterer,
        DataPreprocessor,
        POSITION_PROFILES,
    )
    HAS_PREDICTIVE = True
except Exception:
    HAS_PREDICTIVE = False

# ============================================
# LOGGING
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# ============================================
# SANITIZAÇÃO DE URLs E HTML
# ============================================
_ALLOWED_URL_SCHEMES = {'http', 'https'}
_ALLOWED_IMG_DOMAINS = {
    'logodetimes.com', 'upload.wikimedia.org', 'cdn-img.zerozero.pt',
    'img.a.transfermarkt.technology', 'tmssl.akamaized.net',
    'www.ogol.com.br', 'ogol.com.br', 'zerozero.pt',
}

def sanitize_url(url: str) -> str:
    """Valida e sanitiza URL para uso seguro em HTML.
    Retorna string vazia se a URL não for segura."""
    if not url or not isinstance(url, str):
        return ''
    url = url.strip()
    try:
        parsed = urlparse(url)
        if parsed.scheme not in _ALLOWED_URL_SCHEMES:
            return ''
        if not parsed.netloc:
            return ''
        return url
    except Exception:
        return ''

def escape_html(text: str) -> str:
    """Escapa texto para uso seguro em HTML."""
    if text is None:
        return ''
    return html_module.escape(str(text))

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
GOOGLE_SHEET_ID = os.environ.get(
    "GOOGLE_SHEET_ID",
    st.secrets.get("GOOGLE_SHEET_ID", "1aRjJAxYHJED4FyPnq4PfcrzhhRhzw-vNQ9Vg1pIlak0")
    if hasattr(st, 'secrets') and st.secrets else "1aRjJAxYHJED4FyPnq4PfcrzhhRhzw-vNQ9Vg1pIlak0"
)

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

def get_primary_nationality(nationality):
    """Retorna apenas a primeira nacionalidade (ex: 'Brazil, Senegal' -> 'Brazil')"""
    if pd.isna(nationality):
        return None
    return str(nationality).split(',')[0].strip()

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
    
    # Outros países - Uruguai
    'Peñarol': 'https://logodetimes.com/times/penarol/logo-penarol-256.png',
    'Nacional': 'https://logodetimes.com/times/nacional-uruguai/logo-nacional-uruguai-256.png',
    
    # Ásia - Coreia do Sul (K League)
    'Gangwon': 'https://upload.wikimedia.org/wikipedia/en/thumb/4/4c/Gangwon_FC.svg/200px-Gangwon_FC.svg.png',
    'Gangwon FC': 'https://upload.wikimedia.org/wikipedia/en/thumb/4/4c/Gangwon_FC.svg/200px-Gangwon_FC.svg.png',
    'Bucheon FC': 'https://upload.wikimedia.org/wikipedia/en/thumb/d/d5/Bucheon_FC_1995_emblem.svg/200px-Bucheon_FC_1995_emblem.svg.png',
    'Bucheon': 'https://upload.wikimedia.org/wikipedia/en/thumb/d/d5/Bucheon_FC_1995_emblem.svg/200px-Bucheon_FC_1995_emblem.svg.png',
    'Jeonbuk': 'https://upload.wikimedia.org/wikipedia/en/thumb/e/e2/Jeonbuk_Hyundai_Motors_FC_emblem.svg/200px-Jeonbuk_Hyundai_Motors_FC_emblem.svg.png',
    'Ulsan': 'https://upload.wikimedia.org/wikipedia/en/thumb/c/c5/Ulsan_Hyundai_FC.svg/200px-Ulsan_Hyundai_FC.svg.png',
    'Seoul': 'https://upload.wikimedia.org/wikipedia/en/thumb/3/3e/FC_Seoul_emblem.svg/200px-FC_Seoul_emblem.svg.png',
    'FC Seoul': 'https://upload.wikimedia.org/wikipedia/en/thumb/3/3e/FC_Seoul_emblem.svg/200px-FC_Seoul_emblem.svg.png',
    
    # Ásia - Japão (J League)
    'Urawa': 'https://upload.wikimedia.org/wikipedia/en/thumb/8/8b/Urawa_Red_Diamonds_logo.svg/200px-Urawa_Red_Diamonds_logo.svg.png',
    'Urawa Reds': 'https://upload.wikimedia.org/wikipedia/en/thumb/8/8b/Urawa_Red_Diamonds_logo.svg/200px-Urawa_Red_Diamonds_logo.svg.png',
    'Yokohama F. Marinos': 'https://upload.wikimedia.org/wikipedia/en/thumb/e/ea/Yokohama_F._Marinos_logo.svg/200px-Yokohama_F._Marinos_logo.svg.png',
    'Vissel Kobe': 'https://upload.wikimedia.org/wikipedia/en/thumb/6/65/Vissel_Kobe_logo.svg/200px-Vissel_Kobe_logo.svg.png',
    'Kashima Antlers': 'https://upload.wikimedia.org/wikipedia/en/thumb/4/44/Kashima_Antlers.svg/200px-Kashima_Antlers.svg.png',
    
    # Ásia - China
    'Guangzhou': 'https://upload.wikimedia.org/wikipedia/en/thumb/b/b0/Guangzhou_FC_logo.svg/200px-Guangzhou_FC_logo.svg.png',
    'Guangdong GZ-Power': 'https://upload.wikimedia.org/wikipedia/en/thumb/b/b0/Guangzhou_FC_logo.svg/200px-Guangzhou_FC_logo.svg.png',
    'Shanghai Port': 'https://upload.wikimedia.org/wikipedia/en/thumb/d/d3/Shanghai_Port_FC_logo.svg/200px-Shanghai_Port_FC_logo.svg.png',
    'Shanghai Shenhua': 'https://upload.wikimedia.org/wikipedia/en/thumb/c/c9/Shanghai_Shenhua_FC_2019.svg/200px-Shanghai_Shenhua_FC_2019.svg.png',
    
    # Ásia - Oriente Médio
    'Al Hilal': 'https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Al_Hilal_SFC_logo.svg/200px-Al_Hilal_SFC_logo.svg.png',
    'Al Nassr': 'https://upload.wikimedia.org/wikipedia/en/thumb/8/83/Al-Nassr_FC_Badge.png/200px-Al-Nassr_FC_Badge.png',
    'Al Ahli': 'https://upload.wikimedia.org/wikipedia/en/thumb/1/1e/Al_Ahli_SFC_logo.svg/200px-Al_Ahli_SFC_logo.svg.png',
    'Beitar Jerusalem': 'https://upload.wikimedia.org/wikipedia/en/thumb/7/7b/Beitar_Jerusalem_FC_logo.svg/200px-Beitar_Jerusalem_FC_logo.svg.png',
    'Maccabi Haifa': 'https://upload.wikimedia.org/wikipedia/en/thumb/1/12/Maccabi_Haifa_FC_Logo.svg/200px-Maccabi_Haifa_FC_Logo.svg.png',
    
    # Europa - Principais
    'Barcelona': 'https://logodetimes.com/times/barcelona/logo-barcelona-256.png',
    'Real Madrid': 'https://logodetimes.com/times/real-madrid/logo-real-madrid-256.png',
    'Manchester United': 'https://logodetimes.com/times/manchester-united/logo-manchester-united-256.png',
    'Manchester City': 'https://logodetimes.com/times/manchester-city/logo-manchester-city-256.png',
    'Liverpool': 'https://logodetimes.com/times/liverpool/logo-liverpool-256.png',
    'Chelsea': 'https://logodetimes.com/times/chelsea/logo-chelsea-256.png',
    'Arsenal': 'https://logodetimes.com/times/arsenal/logo-arsenal-256.png',
    'Juventus': 'https://logodetimes.com/times/juventus/logo-juventus-256.png',
    'Milan': 'https://logodetimes.com/times/milan/logo-milan-256.png',
    'AC Milan': 'https://logodetimes.com/times/milan/logo-milan-256.png',
    'Inter': 'https://logodetimes.com/times/inter-de-milao/logo-inter-de-milao-256.png',
    'Inter de Milão': 'https://logodetimes.com/times/inter-de-milao/logo-inter-de-milao-256.png',
    'Bayern': 'https://logodetimes.com/times/bayern-de-munique/logo-bayern-de-munique-256.png',
    'Bayern Munich': 'https://logodetimes.com/times/bayern-de-munique/logo-bayern-de-munique-256.png',
    'PSG': 'https://logodetimes.com/times/psg/logo-psg-256.png',
    'Paris Saint-Germain': 'https://logodetimes.com/times/psg/logo-psg-256.png',
    'Benfica': 'https://logodetimes.com/times/benfica/logo-benfica-256.png',
    'Porto': 'https://logodetimes.com/times/porto/logo-porto-256.png',
    'Sporting': 'https://logodetimes.com/times/sporting/logo-sporting-256.png',
    'Ajax': 'https://logodetimes.com/times/ajax/logo-ajax-256.png',
    'Nottingham Forest': 'https://upload.wikimedia.org/wikipedia/en/thumb/e/e5/Nottingham_Forest_F.C._logo.svg/200px-Nottingham_Forest_F.C._logo.svg.png',
    
    # MLS
    'LA Galaxy': 'https://upload.wikimedia.org/wikipedia/en/thumb/7/70/Los_Angeles_Galaxy_logo.svg/200px-Los_Angeles_Galaxy_logo.svg.png',
    'Inter Miami': 'https://upload.wikimedia.org/wikipedia/en/thumb/8/8e/Inter_Miami_CF_logo.svg/200px-Inter_Miami_CF_logo.svg.png',
}

# ============================================
# LOGOS DE LIGAS
# ============================================
LEAGUE_LOGOS = {
    # Brasil
    'Série A': 'https://logodetimes.com/times/campeonato-brasileiro/logo-campeonato-brasileiro-256.png',
    'Serie A': 'https://logodetimes.com/times/campeonato-brasileiro/logo-campeonato-brasileiro-256.png',
    'Brasileirão': 'https://logodetimes.com/times/campeonato-brasileiro/logo-campeonato-brasileiro-256.png',
    'Série B': 'https://logodetimes.com/times/campeonato-brasileiro/logo-campeonato-brasileiro-256.png',
    'Serie B': 'https://logodetimes.com/times/campeonato-brasileiro/logo-campeonato-brasileiro-256.png',
    'Brasil | 1': 'https://logodetimes.com/times/campeonato-brasileiro/logo-campeonato-brasileiro-256.png',
    'Brasil | 2': 'https://logodetimes.com/times/campeonato-brasileiro/logo-campeonato-brasileiro-256.png',
    
    # Europa
    'Premier League': 'https://logodetimes.com/times/premier-league/logo-premier-league-256.png',
    'England | 1': 'https://logodetimes.com/times/premier-league/logo-premier-league-256.png',
    'Inglaterra | 1': 'https://logodetimes.com/times/premier-league/logo-premier-league-256.png',
    'La Liga': 'https://logodetimes.com/times/la-liga/logo-la-liga-256.png',
    'LaLiga': 'https://logodetimes.com/times/la-liga/logo-la-liga-256.png',
    'Spain | 1': 'https://logodetimes.com/times/la-liga/logo-la-liga-256.png',
    'Espanha | 1': 'https://logodetimes.com/times/la-liga/logo-la-liga-256.png',
    'Serie A (Itália)': 'https://logodetimes.com/times/serie-a-italia/logo-serie-a-italia-256.png',
    'Italy | 1': 'https://logodetimes.com/times/serie-a-italia/logo-serie-a-italia-256.png',
    'Itália | 1': 'https://logodetimes.com/times/serie-a-italia/logo-serie-a-italia-256.png',
    'Bundesliga': 'https://logodetimes.com/times/bundesliga/logo-bundesliga-256.png',
    'Germany | 1': 'https://logodetimes.com/times/bundesliga/logo-bundesliga-256.png',
    'Alemanha | 1': 'https://logodetimes.com/times/bundesliga/logo-bundesliga-256.png',
    'Ligue 1': 'https://logodetimes.com/times/ligue-1/logo-ligue-1-256.png',
    'France | 1': 'https://logodetimes.com/times/ligue-1/logo-ligue-1-256.png',
    'França | 1': 'https://logodetimes.com/times/ligue-1/logo-ligue-1-256.png',
    'Eredivisie': 'https://logodetimes.com/times/eredivisie/logo-eredivisie-256.png',
    'Netherlands | 1': 'https://logodetimes.com/times/eredivisie/logo-eredivisie-256.png',
    'Holanda | 1': 'https://logodetimes.com/times/eredivisie/logo-eredivisie-256.png',
    'Primeira Liga': 'https://logodetimes.com/times/liga-portugal/logo-liga-portugal-256.png',
    'Liga Portugal': 'https://logodetimes.com/times/liga-portugal/logo-liga-portugal-256.png',
    'Portugal | 1': 'https://logodetimes.com/times/liga-portugal/logo-liga-portugal-256.png',
    
    # América do Sul
    'Argentina | 1': 'https://logodetimes.com/times/liga-profissional-argentina/logo-liga-profissional-argentina-256.png',
    'Liga Profesional': 'https://logodetimes.com/times/liga-profissional-argentina/logo-liga-profissional-argentina-256.png',
    'Uruguay | 1': 'https://logodetimes.com/times/primera-division-uruguaia/logo-primera-division-uruguaia-256.png',
    'Chile | 1': 'https://logodetimes.com/times/campeonato-chileno/logo-campeonato-chileno-256.png',
    'Colombia | 1': 'https://logodetimes.com/times/liga-betplay/logo-liga-betplay-256.png',
    'Peru | 1': 'https://logodetimes.com/times/liga-1-peru/logo-liga-1-peru-256.png',
    'Paraguay | 1': 'https://logodetimes.com/times/division-profesional-paraguai/logo-division-profesional-paraguai-256.png',
    'Bolivia | 1': 'https://logodetimes.com/times/liga-boliviana/logo-liga-boliviana-256.png',
    'Ecuador | 1': 'https://logodetimes.com/times/liga-pro-equador/logo-liga-pro-equador-256.png',
    'Venezuela | 1': 'https://logodetimes.com/times/liga-futve/logo-liga-futve-256.png',
    'Mexico | 1': 'https://logodetimes.com/times/liga-mx/logo-liga-mx-256.png',
    'Liga MX': 'https://logodetimes.com/times/liga-mx/logo-liga-mx-256.png',
    
    # Ásia
    'Japan | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/a/a5/J.League_%28logo%29.svg/200px-J.League_%28logo%29.svg.png',
    'Japão | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/a/a5/J.League_%28logo%29.svg/200px-J.League_%28logo%29.svg.png',
    'J1 League': 'https://upload.wikimedia.org/wikipedia/en/thumb/a/a5/J.League_%28logo%29.svg/200px-J.League_%28logo%29.svg.png',
    'Korea | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/0/05/K_League_1_logo.svg/200px-K_League_1_logo.svg.png',
    'Coreia | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/0/05/K_League_1_logo.svg/200px-K_League_1_logo.svg.png',
    'K League 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/0/05/K_League_1_logo.svg/200px-K_League_1_logo.svg.png',
    'China | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/f/fc/Chinese_Super_League_logo.svg/200px-Chinese_Super_League_logo.svg.png',
    'Chinese Super League': 'https://upload.wikimedia.org/wikipedia/en/thumb/f/fc/Chinese_Super_League_logo.svg/200px-Chinese_Super_League_logo.svg.png',
    'Saudi Arabia | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/b/b7/Saudi_Pro_League_Logo.svg/200px-Saudi_Pro_League_Logo.svg.png',
    'Saudi Pro League': 'https://upload.wikimedia.org/wikipedia/en/thumb/b/b7/Saudi_Pro_League_Logo.svg/200px-Saudi_Pro_League_Logo.svg.png',
    'Arábia Saudita | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/b/b7/Saudi_Pro_League_Logo.svg/200px-Saudi_Pro_League_Logo.svg.png',
    
    # MLS
    'USA | 1': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/MLS_crest_logo_RGB_gradient.svg/200px-MLS_crest_logo_RGB_gradient.svg.png',
    'MLS': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/MLS_crest_logo_RGB_gradient.svg/200px-MLS_crest_logo_RGB_gradient.svg.png',
    
    # Outros
    'Israel | 1': 'https://upload.wikimedia.org/wikipedia/he/thumb/1/1e/Israeli_Premier_League_Logo.svg/200px-Israeli_Premier_League_Logo.svg.png',
    'Turkey | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/0/01/S%C3%BCper_Lig_logo.svg/200px-S%C3%BCper_Lig_logo.svg.png',
    'Turquia | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/0/01/S%C3%BCper_Lig_logo.svg/200px-S%C3%BCper_Lig_logo.svg.png',
    'Greece | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/0/05/Super_League_Greece_logo.svg/200px-Super_League_Greece_logo.svg.png',
    'Grécia | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/0/05/Super_League_Greece_logo.svg/200px-Super_League_Greece_logo.svg.png',
    'Russia | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/f/f2/Russian_Premier_League_logo.svg/200px-Russian_Premier_League_logo.svg.png',
    'Rússia | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/f/f2/Russian_Premier_League_logo.svg/200px-Russian_Premier_League_logo.svg.png',
    'Belgium | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/0/07/Belgian_First_Division_A_logo.svg/200px-Belgian_First_Division_A_logo.svg.png',
    'Bélgica | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/0/07/Belgian_First_Division_A_logo.svg/200px-Belgian_First_Division_A_logo.svg.png',
    'Switzerland | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/9/9e/Swiss_Super_League_logo.svg/200px-Swiss_Super_League_logo.svg.png',
    'Suíça | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/9/9e/Swiss_Super_League_logo.svg/200px-Swiss_Super_League_logo.svg.png',
    'Austria | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/e/e2/Austrian_Football_Bundesliga_logo.svg/200px-Austrian_Football_Bundesliga_logo.svg.png',
    'Áustria | 1': 'https://upload.wikimedia.org/wikipedia/en/thumb/e/e2/Austrian_Football_Bundesliga_logo.svg/200px-Austrian_Football_Bundesliga_logo.svg.png',
}

def get_league_logo(league_name):
    """Retorna URL do logo da liga"""
    if pd.isna(league_name):
        return None
    league_str = str(league_name).strip()
    # Tentar match exato
    if league_str in LEAGUE_LOGOS:
        return LEAGUE_LOGOS[league_str]
    # Tentar match parcial
    for key, url in LEAGUE_LOGOS.items():
        if key.lower() in league_str.lower() or league_str.lower() in key.lower():
            return url
    return None

def get_league_logo_html(league_name, size=20):
    """Retorna HTML img tag para o logo da liga"""
    logo_url = get_league_logo(league_name)
    if logo_url:
        safe_url = sanitize_url(logo_url)
        if safe_url:
            return f'<img src="{escape_html(safe_url)}" width="{int(size)}" height="{int(size)}" style="vertical-align: middle; margin-right: 5px;" onerror="this.style.display=\'none\'">'
    return ''

def get_club_logo(club_name):
    """Retorna URL do escudo do clube"""
    if pd.isna(club_name):
        return None
    return CLUB_LOGOS.get(str(club_name).strip(), None)

def get_club_logo_html(club_name, size=20):
    """Retorna HTML img tag para o escudo"""
    logo_url = get_club_logo(club_name)
    if logo_url:
        safe_url = sanitize_url(logo_url)
        if safe_url:
            return f'<img src="{escape_html(safe_url)}" width="{int(size)}" height="{int(size)}" style="vertical-align: middle; margin-right: 5px;">'
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

# ============================================
# ÍNDICES COMPOSTOS POR POSIÇÃO
# ============================================
# Metodologia baseada em:
# - xG/xA (Expected Goals/Assists) - StatsBomb/Opta
# - VAEP (Valuing Actions by Estimating Probabilities) - KU Leuven
# - Packing/Progressive actions - Impect
# - Player Contribution Ratings - Soccerment
# - Physical Performance Metrics - SkillCorner integration
#
# Estrutura: Cada índice combina métricas de VOLUME e EFICIÊNCIA
# Normalização: Percentil dentro da posição (0-100)
# ============================================

INDICES_CONFIG = {
    'Atacante': {
        # OUTPUT: Métricas de produção final
        'Finalização': [
            'Golos/90', 'Golos esperados/90', 'Golos sem ser por penálti/90',
            'Remates/90', 'Remates à baliza, %', 'Golos marcados, %',
            'Toques na área/90', 'Golos de cabeça/90'
        ],
        # PROCESSO: Capacidade de criar para si mesmo
        '1x1 Ofensivo': [
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %',
            'Acelerações/90', 'Faltas sofridas/90'
        ],
        # JOGO AÉREO: Dominância aérea ofensiva
        'Jogo Aéreo': [
            'Duelos aérios/90', 'Duelos aéreos ganhos, %',
            'Golos de cabeça/90', 'Cruzamentos em profundidade recebidos/90'
        ],
        # MOVIMENTAÇÃO: Qualidade de movimentos sem bola
        'Movimentação': [
            'Corridas progressivas/90', 'Receção de passes em profundidade/90',
            'Acelerações/90', 'Passes longos recebidos/90',
            'Toques na área/90'
        ],
        # LINK-UP: Participação na construção
        'Link-up Play': [
            'Passes recebidos/90', 'Passes/90', 'Passes certos, %',
            'Assistências/90', 'Assistências esperadas/90',
            'Segundas assistências/90', 'Passes chave/90'
        ],
        # PRESSING: Contribuição defensiva (contra-pressão)
        'Pressing': [
            'Ações defensivas com êxito/90', 'Duelos/90', 'Duelos ganhos, %',
            'Interseções/90'
        ],
    },
    'Extremo': {
        # OUTPUT: Gols e assistências
        'Finalização': [
            'Golos/90', 'Golos esperados/90', 'Remates/90',
            'Remates à baliza, %', 'Toques na área/90', 'Golos marcados, %'
        ],
        # CRIAÇÃO: Geração de chances para terceiros
        'Criação': [
            'Assistências/90', 'Assistências esperadas/90',
            'Passes chave/90', 'Passes inteligentes/90',
            'Segundas assistências/90', 'Terceiras assistências/90',
            'Passes para a área de penálti/90'
        ],
        # 1x1: Capacidade de drible e superação
        '1x1 Ofensivo': [
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %',
            'Faltas sofridas/90', 'Acelerações/90'
        ],
        # PROGRESSÃO: Capacidade de transportar jogo
        'Progressão': [
            'Corridas progressivas/90', 'Passes progressivos/90',
            'Passes progressivos certos, %', 'Acelerações/90',
            'Passes para terço final/90', 'Passes certos para terço final, %'
        ],
        # CRUZAMENTOS: Qualidade de cruzamentos
        'Cruzamentos': [
            'Cruzamentos/90', 'Cruzamentos certos, %',
            'Cruzamentos para a área de baliza/90',
            'Cruzamentos do flanco esquerdo/90', 'Cruzamentos precisos do flanco esquerdo, %',
            'Cruzamentos do flanco direito/90', 'Cruzamentos precisos do flanco direito, %'
        ],
        # TRABALHO DEFENSIVO: Contribuição sem bola
        'Trabalho Defensivo': [
            'Ações defensivas com êxito/90', 'Duelos defensivos/90',
            'Duelos defensivos ganhos, %', 'Interseções/90'
        ],
    },
    'Meia': {
        # CRIAÇÃO: Motor criativo da equipe
        'Criação': [
            'Assistências/90', 'Assistências esperadas/90',
            'Passes chave/90', 'Passes inteligentes/90', 'Passes inteligentes certos, %',
            'Segundas assistências/90', 'Terceiras assistências/90',
            'Passes para a área de penálti/90', 'Passes precisos para a área de penálti, %'
        ],
        # PROGRESSÃO: Capacidade de avançar o jogo
        'Progressão': [
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Corridas progressivas/90', 'Passes para terço final/90',
            'Passes certos para terço final, %', 'Passes em profundidade/90',
            'Passes em profundidade certos, %'
        ],
        # QUALIDADE DE PASSE: Técnica e precisão
        'Qualidade de Passe': [
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
            'Passes para a frente/90', 'Passes para a frente certos, %',
            'Comprimento médio de passes, m'
        ],
        # FINALIZAÇÃO: Contribuição de gols
        'Finalização': [
            'Golos/90', 'Golos esperados/90', 'Remates/90',
            'Remates à baliza, %', 'Toques na área/90'
        ],
        # DUELOS: Capacidade física
        'Duelos': [
            'Duelos/90', 'Duelos ganhos, %',
            'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %',
            'Dribles/90', 'Dribles com sucesso, %'
        ],
        # RECUPERAÇÃO: Contribuição defensiva
        'Recuperação': [
            'Ações defensivas com êxito/90', 'Duelos defensivos/90',
            'Duelos defensivos ganhos, %', 'Interseções/90',
            'Cortes/90'
        ],
    },
    'Volante': {
        # RECUPERAÇÃO: Core da posição - interceptar e recuperar
        'Recuperação': [
            'Ações defensivas com êxito/90', 'Interseções/90',
            'Interceções ajust. à posse', 'Duelos defensivos/90',
            'Duelos defensivos ganhos, %', 'Cortes/90',
            'Cortes de carrinho ajust. à posse', 'Remates intercetados/90'
        ],
        # DUELOS: Dominância física
        'Duelos': [
            'Duelos/90', 'Duelos ganhos, %',
            'Duelos aérios/90', 'Duelos aéreos ganhos, %',
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %'
        ],
        # CONSTRUÇÃO: Capacidade de iniciar jogadas
        'Construção': [
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
            'Passes para a frente/90', 'Passes para a frente certos, %'
        ],
        # PROGRESSÃO: Capacidade de avançar o jogo
        'Progressão': [
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terço final/90', 'Passes certos para terço final, %',
            'Corridas progressivas/90', 'Passes em profundidade/90'
        ],
        # COBERTURA: Posicionamento e cobertura de espaços
        'Cobertura': [
            'Ações defensivas com êxito/90', 'Interseções/90',
            'Cortes/90', 'Remates intercetados/90'
        ],
        # DISCIPLINA: Controle emocional (invertido - menos é melhor)
        'Disciplina': [
            'Faltas/90', 'Cartões amarelos/90', 'Cartões vermelhos/90'
        ],
    },
    'Lateral': {
        # APOIO OFENSIVO: Contribuição no ataque
        'Apoio Ofensivo': [
            'Cruzamentos/90', 'Cruzamentos certos, %',
            'Cruzamentos para a área de baliza/90',
            'Passes para terço final/90', 'Passes certos para terço final, %',
            'Toques na área/90', 'Passes para a área de penálti/90'
        ],
        # PROGRESSÃO: Capacidade de transportar jogo
        'Progressão': [
            'Corridas progressivas/90', 'Passes progressivos/90',
            'Passes progressivos certos, %', 'Acelerações/90',
            'Passes em profundidade/90'
        ],
        # 1x1 OFENSIVO: Capacidade de superar adversário
        '1x1 Ofensivo': [
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %',
            'Faltas sofridas/90'
        ],
        # DEFESA: Core defensivo da posição
        'Defesa': [
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Interseções/90', 'Cortes/90',
            'Ações defensivas com êxito/90', 'Remates intercetados/90'
        ],
        # DUELOS TOTAIS: Dominância em duelos
        'Duelos': [
            'Duelos/90', 'Duelos ganhos, %',
            'Duelos aérios/90', 'Duelos aéreos ganhos, %'
        ],
        # CRIAÇÃO: Assistências e passes chave
        'Criação': [
            'Assistências/90', 'Assistências esperadas/90',
            'Passes chave/90', 'Segundas assistências/90'
        ],
    },
    'Zagueiro': {
        # DUELOS DEFENSIVOS: Core da posição
        'Duelos Defensivos': [
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Cortes/90', 'Cortes de carrinho ajust. à posse',
            'Ações defensivas com êxito/90'
        ],
        # JOGO AÉREO: Dominância aérea
        'Jogo Aéreo': [
            'Duelos aérios/90', 'Duelos aéreos ganhos, %',
            'Golos de cabeça/90'
        ],
        # INTERCEÇÕES: Leitura de jogo
        'Interceções': [
            'Interseções/90', 'Interceções ajust. à posse',
            'Remates intercetados/90', 'Cortes/90'
        ],
        # CONSTRUÇÃO: Qualidade de passe
        'Construção': [
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
            'Passes para a frente/90', 'Passes para a frente certos, %',
            'Comprimento médio de passes longos, m'
        ],
        # PROGRESSÃO: Capacidade de avançar jogo desde trás
        'Progressão': [
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terço final/90', 'Corridas progressivas/90',
            'Passes em profundidade/90'
        ],
        # DISCIPLINA: Controle (invertido)
        'Disciplina': [
            'Faltas/90', 'Cartões amarelos/90', 'Cartões vermelhos/90'
        ],
    },
    'Goleiro': {
        # DEFESAS: Capacidade de evitar gols
        'Defesas': [
            'Defesas, %', 'Golos sofridos/90', 'Remates sofridos/90'
        ],
        # xG PREVENTED: Métrica avançada de performance
        'xG Prevented': [
            'Golos sofridos esperados/90', 'Golos expectáveis defendidos por 90´'
        ],
        # JOGO AÉREO: Dominância na área
        'Jogo Aéreo': [
            'Duelos aérios/90.1', 'Saídas/90'
        ],
        # JOGO COM PÉS: Construção desde trás
        'Jogo com Pés': [
            'Passes para trás recebidos pelo guarda-redes/90',
            'Passes longos certos, %'
        ],
        # CLEAN SHEETS: Jogos sem sofrer
        'Clean Sheets': [
            'Jogos sem sofrer golos'
        ],
    },
}

# Mapeamento de posições WyScout para categorias de índices
# Suporta tanto formato antigo (siglas) quanto novo (português)
POSICAO_MAP = {
    # ===== FORMATO NOVO (Português) =====
    'Atacante': 'Atacante',
    'Extremo': 'Extremo',
    'Meia': 'Meia',
    'Volante': 'Volante',
    'Lateral direito': 'Lateral',
    'Lateral esquerdo': 'Lateral',
    'Zagueiro': 'Zagueiro',
    'Goleiro': 'Goleiro',
    
    # ===== FORMATO ANTIGO (Siglas - retrocompatibilidade) =====
    # Atacantes
    'CF': 'Atacante', 'SS': 'Atacante',
    # Extremos/Wingers
    'LW': 'Extremo', 'RW': 'Extremo', 'LWF': 'Extremo', 'RWF': 'Extremo', 
    'LAMF': 'Extremo', 'RAMF': 'Extremo',
    # Meias
    'AMF': 'Meia', 'LCMF': 'Meia', 'RCMF': 'Meia', 'CMF': 'Meia',
    # Volantes
    'DMF': 'Volante', 'LDMF': 'Volante', 'RDMF': 'Volante',
    # Laterais
    'LB': 'Lateral', 'RB': 'Lateral', 'LWB': 'Lateral', 'RWB': 'Lateral',
    'LB5': 'Lateral', 'RB5': 'Lateral',
    # Zagueiros
    'CB': 'Zagueiro', 'LCB': 'Zagueiro', 'RCB': 'Zagueiro',
    'LCB3': 'Zagueiro', 'RCB3': 'Zagueiro', 'CCB3': 'Zagueiro',
    # Goleiros
    'GK': 'Goleiro',
}

# Lista de posições para filtros (formato novo)
POSICOES_DISPLAY = [
    'Atacante', 'Extremo', 'Meia', 'Volante', 
    'Lateral direito', 'Lateral esquerdo', 'Zagueiro', 'Goleiro'
]

# ============================================
# ÍNDICES SKILLCORNER - Perfis de jogo físico
# ============================================
# Estes índices são pré-calculados pelo SkillCorner e medem
# aspectos físicos e táticos do jogo sem bola
SKILLCORNER_INDICES = {
    'Atacante': ['Direct striker index', 'Link up striker index'],
    'Extremo': ['Inverted winger index', 'Wide winger index'],
    'Meia': ['Dynamic number 8 index', 'Box to box midfielder index'],
    'Volante': ['Number 6 index', 'Box to box midfielder index'],
    'Lateral': ['Intense full back index', 'Technical full back index'],
    'Lateral direito': ['Intense full back index', 'Technical full back index'],
    'Lateral esquerdo': ['Intense full back index', 'Technical full back index'],
    'Zagueiro': ['Physical & aggressive defender index', 'Ball playing central defender index'],
}

# Times da Série B 2025 (nomes exatos do dataset WyScout)
SERIE_B_TEAMS = [
    'Amazonas',
    'América Mineiro',
    'Athletic Club',
    'Athletico Paranaense',
    'Atlético GO',
    'Avaí',
    'Botafogo SP',
    'Chapecoense',
    'Coritiba',
    'CRB',
    'Criciúma',
    'Cuiabá',
    'Ferroviária',
    'Goiás',
    'Grêmio Novorizontino',
    'Operário PR',
    'Paysandu',
    'Remo',
    'Vila Nova',
    'Volta Redonda',
]

# ============================================
# MAPEAMENTO LIGA WYSCOUT → LEAGUE_TIERS
# ============================================
WYSCOUT_LEAGUE_MAP = {
    'Brasil | 1': 'Serie A Brasil', 'Brasil | 2': 'Serie B Brasil',
    'Brasil | 3': 'Serie C Brasil', 'Brasil | 4': 'Serie D Brasil',
    'Série A': 'Serie A Brasil', 'Serie A': 'Serie A Brasil',
    'Série B': 'Serie B Brasil', 'Serie B': 'Serie B Brasil',
    'England | 1': 'Premier League', 'Inglaterra | 1': 'Premier League',
    'England | 2': 'Championship',
    'Spain | 1': 'La Liga', 'Espanha | 1': 'La Liga', 'La Liga': 'La Liga',
    'Spain | 2': 'La Liga 2',
    'Italy | 1': 'Serie A Italia', 'Itália | 1': 'Serie A Italia',
    'Italy | 2': 'Serie B Italia',
    'Germany | 1': 'Bundesliga', 'Alemanha | 1': 'Bundesliga',
    'Germany | 2': '2. Bundesliga',
    'France | 1': 'Ligue 1', 'França | 1': 'Ligue 1',
    'France | 2': 'Ligue 2',
    'Portugal | 1': 'Liga Portugal', 'Liga Portugal': 'Liga Portugal',
    'Portugal | 2': 'Liga Portugal 2',
    'Netherlands | 1': 'Eredivisie', 'Holanda | 1': 'Eredivisie',
    'Belgium | 1': 'Belgian Pro League', 'Bélgica | 1': 'Belgian Pro League',
    'Turkey | 1': 'Super Lig', 'Turquia | 1': 'Super Lig',
    'Russia | 1': 'Russian Premier League', 'Rússia | 1': 'Russian Premier League',
    'Austria | 1': 'Austrian Bundesliga', 'Áustria | 1': 'Austrian Bundesliga',
    'Switzerland | 1': 'Swiss Super League', 'Suíça | 1': 'Swiss Super League',
    'Denmark | 1': 'Danish Superliga',
    'Greece | 1': 'Greek Super League', 'Grécia | 1': 'Greek Super League',
    'Argentina | 1': 'Liga Argentina', 'Liga Profesional': 'Liga Argentina',
    'Argentina | 2': 'Liga Argentina B',
    'USA | 1': 'MLS', 'MLS': 'MLS',
    'Mexico | 1': 'Liga MX', 'Liga MX': 'Liga MX',
    'Colombia | 1': 'Liga Colombia', 'Chile | 1': 'Liga Chile',
    'Uruguay | 1': 'Liga Uruguai', 'Peru | 1': 'Liga Peru',
    'Ecuador | 1': 'Liga Equador', 'Paraguay | 1': 'Liga Paraguai',
    'Bolivia | 1': 'Liga Bolivia', 'Venezuela | 1': 'Liga Venezuela',
    'Japan | 1': 'J1 League', 'Japão | 1': 'J1 League',
    'Japan | 2': 'J2 League',
    'Korea | 1': 'K-League 1', 'Coreia | 1': 'K-League 1',
    'Saudi Arabia | 1': 'Saudi Pro League', 'Arábia Saudita | 1': 'Saudi Pro League',
    'China | 1': 'Chinese Super League',
    'Australia | 1': 'A-League',
    'Paulista A1': 'Paulista A1', 'Paulista A2': 'Paulista A2',
    'Carioca A1': 'Carioca A1',
}


def resolve_league_to_tier(league_name, team_name=None):
    """Resolve nome de liga WyScout para chave do LEAGUE_TIERS."""
    if pd.isna(league_name) and team_name is None:
        return None
    if pd.notna(league_name):
        league_str = str(league_name).strip()
        if league_str in WYSCOUT_LEAGUE_MAP:
            return WYSCOUT_LEAGUE_MAP[league_str]
        for key, val in WYSCOUT_LEAGUE_MAP.items():
            if key.lower() in league_str.lower() or league_str.lower() in key.lower():
                return val
    if team_name and not pd.isna(team_name):
        if str(team_name).strip() in SERIE_B_TEAMS:
            return 'Serie B Brasil'
    return None


# ============================================
# MAPEAMENTO LIGA WYSCOUT → LEAGUE_TIERS
# ============================================
WYSCOUT_LEAGUE_MAP = {
    # Brasil
    'Brasil | 1': 'Serie A Brasil', 'Brasil | 2': 'Serie B Brasil',
    'Brasil | 3': 'Serie C Brasil', 'Brasil | 4': 'Serie D Brasil',
    'Série A': 'Serie A Brasil', 'Serie A': 'Serie A Brasil',
    'Série B': 'Serie B Brasil', 'Serie B': 'Serie B Brasil',
    'Brasileirão': 'Serie A Brasil',
    # Europa Top 5
    'England | 1': 'Premier League', 'Inglaterra | 1': 'Premier League',
    'Premier League': 'Premier League',
    'England | 2': 'Championship', 'Championship': 'Championship',
    'Spain | 1': 'La Liga', 'Espanha | 1': 'La Liga', 'La Liga': 'La Liga',
    'LaLiga': 'La Liga', 'Spain | 2': 'La Liga 2',
    'Italy | 1': 'Serie A Italia', 'Itália | 1': 'Serie A Italia',
    'Italy | 2': 'Serie B Italia',
    'Germany | 1': 'Bundesliga', 'Alemanha | 1': 'Bundesliga',
    'Bundesliga': 'Bundesliga', 'Germany | 2': '2. Bundesliga',
    'France | 1': 'Ligue 1', 'França | 1': 'Ligue 1', 'Ligue 1': 'Ligue 1',
    'France | 2': 'Ligue 2',
    # Europa Tier 2
    'Portugal | 1': 'Liga Portugal', 'Liga Portugal': 'Liga Portugal',
    'Primeira Liga': 'Liga Portugal', 'Portugal | 2': 'Liga Portugal 2',
    'Netherlands | 1': 'Eredivisie', 'Holanda | 1': 'Eredivisie',
    'Eredivisie': 'Eredivisie',
    'Belgium | 1': 'Belgian Pro League', 'Bélgica | 1': 'Belgian Pro League',
    'Turkey | 1': 'Super Lig', 'Turquia | 1': 'Super Lig',
    'Scotland | 1': 'Scottish Premiership',
    'Russia | 1': 'Russian Premier League', 'Rússia | 1': 'Russian Premier League',
    'Austria | 1': 'Austrian Bundesliga', 'Áustria | 1': 'Austrian Bundesliga',
    'Switzerland | 1': 'Swiss Super League', 'Suíça | 1': 'Swiss Super League',
    'Denmark | 1': 'Danish Superliga', 'Dinamarca | 1': 'Danish Superliga',
    'Greece | 1': 'Greek Super League', 'Grécia | 1': 'Greek Super League',
    'Ukraine | 1': 'Ukrainian Premier League',
    'Czech Republic | 1': 'Czech First League',
    'Croatia | 1': 'Croatian First League',
    'Serbia | 1': 'Serbian Super Liga',
    'Poland | 1': 'Polish Ekstraklasa',
    'Romania | 1': 'Romanian Liga I',
    'Norway | 1': 'Norwegian Eliteserien',
    'Sweden | 1': 'Swedish Allsvenskan',
    'Israel | 1': 'Israeli Premier League',
    'Bulgaria | 1': 'Bulgarian First League',
    'Cyprus | 1': 'Cypriot First Division',
    # Américas
    'Argentina | 1': 'Liga Argentina', 'Liga Profesional': 'Liga Argentina',
    'Argentina | 2': 'Liga Argentina B',
    'USA | 1': 'MLS', 'MLS': 'MLS',
    'Mexico | 1': 'Liga MX', 'Liga MX': 'Liga MX',
    'Colombia | 1': 'Liga Colombia', 'Chile | 1': 'Liga Chile',
    'Uruguay | 1': 'Liga Uruguai', 'Peru | 1': 'Liga Peru',
    'Ecuador | 1': 'Liga Equador', 'Paraguay | 1': 'Liga Paraguai',
    'Bolivia | 1': 'Liga Bolivia', 'Venezuela | 1': 'Liga Venezuela',
    # Ásia
    'Japan | 1': 'J1 League', 'Japão | 1': 'J1 League', 'Japan | 2': 'J2 League',
    'Korea | 1': 'K-League 1', 'Coreia | 1': 'K-League 1', 'K League 1': 'K-League 1',
    'Saudi Arabia | 1': 'Saudi Pro League', 'Arábia Saudita | 1': 'Saudi Pro League',
    'Qatar | 1': 'Qatar Stars League', 'UAE | 1': 'UAE Pro League',
    'China | 1': 'Chinese Super League', 'India | 1': 'Indian Super League',
    # África / Oceania
    'Egypt | 1': 'Egyptian Premier League', 'South Africa | 1': 'South African Premier',
    'Morocco | 1': 'Moroccan Botola', 'Tunisia | 1': 'Tunisian Ligue 1',
    'Australia | 1': 'A-League',
    # Estaduais / Copas Brasil
    'Paulista A1': 'Paulista A1', 'Paulista A2': 'Paulista A2', 'Paulista A3': 'Paulista A3',
    'Carioca A1': 'Carioca A1', 'Gaúcho A1': 'Gaucho A1', 'Gaucho A1': 'Gaucho A1',
    'Mineiro A1': 'Mineiro A1', 'Paranaense A1': 'Paranaense A1',
    'Cearense A1': 'Cearense A1', 'Pernambucano A1': 'Pernambucano A1',
    'Baiano A1': 'Baiano A1',
    'Copa do Brasil': 'Copa do Brasil', 'Copa do Nordeste': 'Copa do Nordeste',
    'Copa Libertadores': 'Copa Libertadores', 'Copa Sudamericana': 'Copa Sudamericana',
}


def resolve_league_to_tier(league_name, team_name=None):
    """Resolve nome de liga WyScout para chave do ContractSuccessPredictor.LEAGUE_TIERS."""
    if league_name is None:
        if team_name is None:
            return None
    elif pd.notna(league_name):
        league_str = str(league_name).strip()
        if league_str in WYSCOUT_LEAGUE_MAP:
            return WYSCOUT_LEAGUE_MAP[league_str]
        for key, val in WYSCOUT_LEAGUE_MAP.items():
            if key.lower() in league_str.lower() or league_str.lower() in key.lower():
                return val
    if team_name is not None:
        try:
            if pd.notna(team_name) and str(team_name).strip() in SERIE_B_TEAMS:
                return 'Serie B Brasil'
        except Exception:
            pass
    return None


def is_serie_b_team(team_name):
    """Verifica se o time é da Série B 2025"""
    if pd.isna(team_name):
        return False
    return str(team_name).strip() in SERIE_B_TEAMS

# ============================================
# FUNÇÕES AUXILIARES DE CONVERSÃO
# ============================================

def get_posicao_categoria(posicao):
    """Converte posição WyScout para categoria de índices (INDICES_CONFIG)
    
    Ex: 'Lateral direito' -> 'Lateral'
        'CF' -> 'Atacante'
        'Atacante' -> 'Atacante'
    """
    if pd.isna(posicao):
        return 'Meia'  # Default
    posicao_str = str(posicao).strip()
    # Se já é uma categoria válida no INDICES_CONFIG, retorna diretamente
    if posicao_str in INDICES_CONFIG:
        return posicao_str
    # Caso contrário, usa o mapeamento
    return POSICAO_MAP.get(posicao_str, 'Meia')

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
# FUNÇÕES DE SCRAPING (OGol/Transfermarkt)
# ============================================

@st.cache_data(ttl=3600)  # Cache por 1 hora
def scrape_ogol_data(ogol_url):
    """Faz scraping do OGol para obter foto e histórico do jogador"""
    if not ogol_url or pd.isna(ogol_url) or not str(ogol_url).startswith('http'):
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(ogol_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        data = {
            'foto': None,
            'carreira': [],
            'info': {}
        }
        
        # Extrair foto do jogador
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if 'jogadores' in src.lower() and '.jpg' in src:
                if not src.startswith('http'):
                    src = 'https://www.ogol.com.br' + src
                data['foto'] = src
                break
        
        # Extrair carreira (tabela com TEMPORADA, EQUIPE, J, G)
        tables = soup.find_all('table')
        for table in tables:
            headers = [th.get_text(strip=True).upper() for th in table.find_all('th')]
            if 'TEMPORADA' in headers or 'EQUIPE' in headers:
                rows = table.find_all('tr')[1:]  # Pular header
                for row in rows[:5]:  # Últimas 5 temporadas
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        data['carreira'].append({
                            'temporada': cols[1].get_text(strip=True) if len(cols) > 1 else '',
                            'equipe': cols[2].get_text(strip=True) if len(cols) > 2 else '',
                            'jogos': cols[3].get_text(strip=True) if len(cols) > 3 else '',
                            'gols': cols[4].get_text(strip=True) if len(cols) > 4 else '',
                            'assists': cols[5].get_text(strip=True) if len(cols) > 5 else ''
                        })
                break
        
        return data
    except requests.RequestException as e:
        logger.warning("Erro no scraping OGol (%s): %s", ogol_url, e)
        return None
    except Exception as e:
        logger.error("Erro inesperado no scraping OGol: %s", e)
        return None


@st.cache_data(ttl=3600)
def scrape_transfermarkt_data(tm_url):
    """Faz scraping do Transfermarkt para obter dados do jogador incluindo escudos"""
    if not tm_url or pd.isna(tm_url) or not str(tm_url).startswith('http'):
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(tm_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        data = {
            'foto': None,
            'contrato': None,
            'valor': None,
            'clube': None,
            'clube_escudo': None,
            'liga': None,
            'liga_escudo': None
        }
        
        # Extrair foto do jogador (portrait)
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if 'portrait' in src.lower() and 'transfermarkt' in src.lower():
                data['foto'] = src
                break
        
        # Extrair escudo do clube (padrão: wappen/kaderquad ou wappen/small)
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            title = img.get('title', '')
            if 'wappen' in src.lower() and ('kaderquad' in src.lower() or 'small' in src.lower() or 'medium' in src.lower()):
                data['clube_escudo'] = src
                if alt:
                    data['clube'] = alt
                elif title:
                    data['clube'] = title
                break
        
        # Extrair escudo da liga (procurar especificamente pelo logo com title definido)
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            title = img.get('title', '')
            # Liga do jogador tem title definido e está em /logo/
            if '/logo/' in src.lower() and 'tiny' in src.lower() and title and title not in ['Transfermarkt', '']:
                # Converter para versão maior do logo
                if 'verytiny' in src:
                    src = src.replace('verytiny', 'medium')
                elif 'tiny' in src:
                    src = src.replace('tiny', 'medium')
                data['liga_escudo'] = src
                data['liga'] = title
                break
        
        # Extrair contrato
        for span in soup.find_all(['span', 'div', 'li']):
            text = span.get_text(strip=True)
            if 'contrato até' in text.lower() or 'contract until' in text.lower():
                match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
                if match:
                    data['contrato'] = match.group(1)
                break
        
        # Extrair valor de mercado
        for span in soup.find_all(['span', 'div']):
            text = span.get_text(strip=True)
            if '€' in text and ('mi.' in text.lower() or 'mil' in text.lower() or 'M' in text):
                data['valor'] = text
                break
        
        return data
    except requests.RequestException as e:
        logger.warning("Erro no scraping Transfermarkt (%s): %s", tm_url, e)
        return None
    except Exception as e:
        logger.error("Erro inesperado no scraping Transfermarkt: %s", e)
        return None


def get_player_photo(p, ogol_data=None, tm_data=None):
    """Retorna URL da foto do jogador priorizando: planilha > OGol > TM"""
    # 1. Verificar se tem foto na planilha
    foto_planilha = safe_str(p.get('Foto'), None)
    if foto_planilha:
        safe_url = sanitize_url(foto_planilha)
        if safe_url:
            return safe_url

    # 2. Verificar OGol
    if ogol_data and ogol_data.get('foto'):
        safe_url = sanitize_url(ogol_data['foto'])
        if safe_url:
            return safe_url

    # 3. Verificar Transfermarkt
    if tm_data and tm_data.get('foto'):
        safe_url = sanitize_url(tm_data['foto'])
        if safe_url:
            return safe_url

    return None


# ============================================
# FUNÇÕES DE CARREGAMENTO
# ============================================

@st.cache_data
def create_skillcorner_lookup(skillcorner_df):
    """Cria lookup dict do SkillCorner para busca O(1)
    
    Inclui todos os índices pré-calculados do SkillCorner:
    - Direct/Link up striker index (Atacantes)
    - Inverted/Wide winger index (Extremos)
    - Dynamic 8/Box to box midfielder index (Meias)
    - Number 6 index (Volantes)
    - Intense/Technical full back index (Laterais)
    - Physical/Ball playing CB index (Zagueiros)
    """
    # Lista de todos os índices SkillCorner
    all_sc_indices = [
        'Direct striker index', 'Link up striker index',
        'Inverted winger index', 'Wide winger index',
        'Dynamic number 8 index', 'Box to box midfielder index',
        'Number 6 index',
        'Intense full back index', 'Technical full back index',
        'Physical & aggressive defender index', 'Ball playing central defender index'
    ]
    
    # Métricas físicas relevantes
    physical_metrics = [
        'sprint_count_per_90', 'hi_count_per_90', 'distance_per_90',
        'avg_psv99', 'avg_top_5_psv99',  # Peak Sprint Velocity
        'count_pressing_engagements_per_30_otip',
        'count_runs_in_behind_per_30_tip'
    ]
    
    sc_lookup = {}
    for _, sc_row in skillcorner_df.iterrows():
        nome_norm = normalize_name(str(sc_row.get('player_name', '')))
        if nome_norm and nome_norm not in sc_lookup:
            sc_data_temp = {}
            
            # Adicionar índices compostos
            for sc_idx in all_sc_indices:
                if sc_idx in sc_row.index:
                    val = safe_float(sc_row[sc_idx])
                    if val is not None:
                        # Simplificar nome do índice
                        short_name = sc_idx.replace(' index', '').replace(' midfielder', '').replace('central ', '')
                        sc_data_temp[short_name] = round(val, 1)
            
            # Adicionar métricas físicas
            for pm in physical_metrics:
                if pm in sc_row.index:
                    val = safe_float(sc_row[pm])
                    if val is not None:
                        sc_data_temp[pm] = round(val, 1)
            
            # Adicionar posição do SkillCorner
            if 'position_group' in sc_row.index:
                sc_data_temp['sc_position'] = str(sc_row['position_group'])
            
            if sc_data_temp:
                sc_lookup[nome_norm] = sc_data_temp
    return sc_lookup

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
            logger.warning("Erro ao carregar '%s' do Google Sheets: %s", sheet_name, e)
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
        except (IOError, pd.errors.ParserError, ValueError) as e:
            logger.warning("Falha ao carregar Google Sheets: %s", e)
    
    # Fallback para arquivo local
    if analises is None:
        try:
            xlsx = pd.ExcelFile('Banco_de_Dados___Jogadores-3.xlsx')
            analises = pd.read_excel(xlsx, sheet_name='Análises')
            oferecidos = pd.read_excel(xlsx, sheet_name='Oferecidos')
            skillcorner = pd.read_excel(xlsx, sheet_name='SkillCorner')
            wyscout = pd.read_excel(xlsx, sheet_name='WyScout')
        except (FileNotFoundError, ValueError, KeyError) as e:
            logger.error("Falha ao carregar arquivo local: %s", e)
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
    # Delega para weighted - retrocompativel
    return calculate_weighted_index(player_row, metrics, df_all, position=None)


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

# ============================================
# MOTOR PREDITIVO — CACHE
# ============================================
@st.cache_resource
def get_ssp_engine(_df_cols_hash, df, position):
    """Treina o motor preditivo uma vez por posição (cached)."""
    if not HAS_PREDICTIVE:
        return None
    try:
        # Pré-filtrar por posição usando mapeamento correto (CF→Atacante, etc.)
        df_pos = df[df['Posição'].apply(get_posicao_categoria) == position].copy()
        if len(df_pos) < 15:
            return None
        engine = ScoutScorePreditivo()
        # pos_col='_prefiltrado_' evita re-filtro interno (já filtrado acima)
        engine.fit(df=df_pos, position=position, min_minutes=500, pos_col='_prefiltrado_')
        return engine
    except Exception:
        return None


def main():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 20px 0;">
            <img src="https://cdn-img.zerozero.pt/img/logos/equipas/3154_imgbank_1685113109.png" 
                 style="width: 80px; height: 80px; margin-bottom: 10px; border-radius: 8px;"
                 onerror="this.style.display='none'">
            <div style="color: #dc2626; font-size: 11px; letter-spacing: 3px; font-weight: 600;">SCOUTING</div>
            <div style="color: white; font-size: 26px; font-weight: 800; letter-spacing: -1px;">BOTAFOGO</div>
            <div style="color: #6b7280; font-size: 10px; letter-spacing: 2px;">RIBEIRÃO PRETO</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Info do usuário logado e botão de logout
        user = get_current_user()
        if user:
            st.markdown(f"""
            <div style="text-align:center; padding: 4px 0 8px 0;">
                <span style="color: #9ca3af; font-size: 12px;">{user['name']}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Sair", key="btn_logout", type="secondary"):
                logout()
                st.rerun()

        st.divider()
        uploaded = st.file_uploader("📂 Carregar Planilha", type=['xlsx'])
        
        try:
            analises, oferecidos, skillcorner, wyscout = load_data(uploaded)
        except Exception as e:
            logger.error("Erro ao carregar dados: %s", e)
            st.error(f"⚠️ Erro ao carregar dados: {e}. Faça upload do Excel ou verifique a conexão.")
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
    
    # Tabs - incluir aba Admin apenas para administradores
    current_user = get_current_user()
    is_admin = current_user and current_user.get("role") == "admin"

    tab_names = ["📊 Perfil", "📈 Índices", "📋 Relatório", "🔄 Comparativo", "🗂️ Dados", "🏆 Ranking", "🔍 Similaridade", "🎯 Predição", "🧬 Clusters"]
    if is_admin:
        tab_names.append("👥 Usuários")

    tabs = st.tabs(tab_names)
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = tabs[:9]
    tab_admin = tabs[9] if is_admin else None
    
    # ===== TAB 1: PERFIL =====
    with tab1:
        if jogador:
            p = df[df['Nome'] == jogador].iloc[0]
            
            # Obter bandeira
            flag = get_flag(p.get('Nacionalidade', ''))
            
            # Scraping de dados externos (OGol e TM)
            ogol_url = safe_str(p.get('ogol'), None)
            tm_url = safe_str(p.get('TM'), None)
            ogol_data = scrape_ogol_data(ogol_url) if ogol_url else None
            tm_data = scrape_transfermarkt_data(tm_url) if tm_url else None
            
            # Obter escudos - prioridade: TM scraping > dicionário estático
            clube_nome = safe_str(p.get('Clube'))
            liga_nome = safe_str(p.get('Liga'))
            
            # Escudo do clube
            if tm_data and tm_data.get('clube_escudo'):
                safe_clube_url = sanitize_url(tm_data["clube_escudo"])
                if safe_clube_url:
                    club_logo = f'<img src="{escape_html(safe_clube_url)}" width="24" height="24" style="vertical-align: middle; margin-right: 5px; border-radius: 4px;" onerror="this.style.display=\'none\'">'
                else:
                    club_logo = get_club_logo_html(clube_nome, size=24)
            else:
                club_logo = get_club_logo_html(clube_nome, size=24)

            # Escudo da liga
            if tm_data and tm_data.get('liga_escudo'):
                safe_liga_url = sanitize_url(tm_data["liga_escudo"])
                if safe_liga_url:
                    league_logo = f'<img src="{escape_html(safe_liga_url)}" width="24" height="24" style="vertical-align: middle; margin-right: 5px; border-radius: 4px;" onerror="this.style.display=\'none\'">'
                else:
                    league_logo = get_league_logo_html(liga_nome, size=24)
            else:
                league_logo = get_league_logo_html(liga_nome, size=24)
            
            # Obter foto do jogador
            foto_url = get_player_photo(p, ogol_data, tm_data)
            
            # Layout: Info (3) | Foto + Nota (1)
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div style="background: {COLORS['card']}; border-radius: 12px; padding: 24px; border: 1px solid {COLORS['border']};">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 28px;">{flag}</span>
                        <div>
                            <div style="color: {COLORS['accent']}; font-size: 12px; font-weight: 600; letter-spacing: 1px;">{escape_html(safe_str(p.get('Posição'), 'JOGADOR'))}</div>
                            <div style="color: white; font-size: 32px; font-weight: 800; margin: 4px 0;">{escape_html(str(p['Nome']))}</div>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 16px;">
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Idade</div><div style="color: white; font-size: 14px;">{display_int(p['Idade'], ' anos')}</div></div>
                        <div style="background: rgba(255,255,255,0.03); border-radius: 8px; padding: 8px;"><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Clube</div><div style="color: white; font-size: 14px; display: flex; align-items: center; gap: 4px;">{club_logo}<span>{clube_nome}</span></div></div>
                        <div style="background: rgba(255,255,255,0.03); border-radius: 8px; padding: 8px;"><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Liga</div><div style="color: white; font-size: 14px; display: flex; align-items: center; gap: 4px;">{league_logo}<span>{liga_nome}</span></div></div>
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Perfil</div><div style="color: white; font-size: 14px;">{safe_str(p.get('Perfil'))}</div></div>
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Contrato</div><div style="color: white; font-size: 14px;">{str(p['Contrato']).split(' ')[0] if pd.notna(p.get('Contrato')) and str(p.get('Contrato')) not in ('nan', '') else '-'}</div></div>
                        <div><div style="color: {COLORS['text_muted']}; font-size: 10px; text-transform: uppercase;">Modelo</div><div style="color: white; font-size: 14px;">{safe_str(p.get('Modelo'))}</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # FOTO DO JOGADOR
                if foto_url:
                    st.markdown(f"""
                    <div style="background: {COLORS['card']}; border-radius: 12px; padding: 8px; border: 1px solid {COLORS['border']}; text-align: center;">
                        <img src="{escape_html(foto_url)}" style="width: 100%; max-height: 180px; object-fit: contain; border-radius: 8px;" onerror="this.style.display='none'"/>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: {COLORS['card']}; border-radius: 12px; padding: 40px 20px; border: 1px solid {COLORS['border']}; text-align: center;">
                        <div style="color: {COLORS['text_muted']}; font-size: 12px;">📷</div>
                        <div style="color: {COLORS['text_muted']}; font-size: 10px; margin-top: 4px;">SEM FOTO</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # NOTA GERAL
                nota = safe_float(p.get('Nota_Desempenho'))
                if nota is not None and nota > 0:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {COLORS['accent']}, #b91c1c); border-radius: 12px; padding: 15px; text-align: center; margin-top: 8px;">
                        <div style="color: rgba(255,255,255,0.7); font-size: 9px; letter-spacing: 1px;">NOTA</div>
                        <div style="color: white; font-size: 32px; font-weight: 800;">{nota:.1f}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # LINKS EXTERNOS (Vídeo, Relatório, TM, OGol)
            video_url = safe_str(p.get('Vídeo'), None)
            relatorio_url = safe_str(p.get('Relatório'), None)
            
            links_html = []
            link_style = f'background: {COLORS["card"]}; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 12px; border: 1px solid {COLORS["border"]};'
            # Vídeo - pode ser URL ou nome de arquivo
            if video_url:
                safe_video = sanitize_url(video_url)
                if safe_video:
                    links_html.append(f'<a href="{escape_html(safe_video)}" target="_blank" rel="noopener noreferrer" style="{link_style} color: {COLORS["accent"]};">🎬 Vídeo</a>')
                else:
                    links_html.append(f'<span style="{link_style} color: {COLORS["accent"]};" title="{escape_html(video_url)}">🎬 Vídeo ✓</span>')

            # Relatório - pode ser URL ou nome de arquivo
            if relatorio_url:
                safe_relatorio = sanitize_url(relatorio_url)
                if safe_relatorio:
                    links_html.append(f'<a href="{escape_html(safe_relatorio)}" target="_blank" rel="noopener noreferrer" style="{link_style} color: {COLORS["accent"]};">📄 Relatório</a>')
                else:
                    links_html.append(f'<span style="{link_style} color: {COLORS["accent"]};" title="{escape_html(relatorio_url)}">📄 Relatório ✓</span>')

            if tm_url:
                safe_tm = sanitize_url(tm_url)
                if safe_tm:
                    links_html.append(f'<a href="{escape_html(safe_tm)}" target="_blank" rel="noopener noreferrer" style="{link_style} color: #00b386;">🔗 Transfermarkt</a>')
            if ogol_url:
                safe_ogol = sanitize_url(ogol_url)
                if safe_ogol:
                    links_html.append(f'<a href="{escape_html(safe_ogol)}" target="_blank" rel="noopener noreferrer" style="{link_style} color: #3b82f6;">⚽ OGol</a>')
            
            if links_html:
                st.markdown(f"""
                <div style="display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0;">
                    {' '.join(links_html)}
                </div>
                """, unsafe_allow_html=True)
            
            # HISTÓRICO DE CARREIRA (do OGol)
            if ogol_data and ogol_data.get('carreira'):
                st.markdown(create_section_title("📜", "Histórico Recente (OGol)"), unsafe_allow_html=True)
                
                carreira_html = f"""
                <div style="background: {COLORS['card']}; border-radius: 8px; padding: 12px; border: 1px solid {COLORS['border']};">
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <tr style="color: {COLORS['text_muted']}; border-bottom: 1px solid {COLORS['border']};">
                            <th style="padding: 8px; text-align: left;">Temporada</th>
                            <th style="padding: 8px; text-align: left;">Equipe</th>
                            <th style="padding: 8px; text-align: center;">J</th>
                            <th style="padding: 8px; text-align: center;">G</th>
                            <th style="padding: 8px; text-align: center;">A</th>
                        </tr>
                """
                for item in ogol_data['carreira']:
                    carreira_html += f"""
                        <tr style="color: white; border-bottom: 1px solid {COLORS['border']};">
                            <td style="padding: 8px;">{item.get('temporada', '-')}</td>
                            <td style="padding: 8px;">{item.get('equipe', '-')}</td>
                            <td style="padding: 8px; text-align: center;">{item.get('jogos', '-')}</td>
                            <td style="padding: 8px; text-align: center;">{item.get('gols', '-')}</td>
                            <td style="padding: 8px; text-align: center;">{item.get('assists', '-')}</td>
                        </tr>
                    """
                carreira_html += "</table></div>"
                st.markdown(carreira_html, unsafe_allow_html=True)
            
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
            
            col_cat, col_comp = st.columns([2, 1])
            with col_cat:
                posicao_categoria = st.selectbox("Categoria de Posição", categorias_disponiveis, index=cat_idx, key='cat_perfil')
            with col_comp:
                comparar_serie_b_t1 = st.checkbox("🇧🇷 Comparar c/ Série B", value=False, key='comp_serie_b_t1',
                                                   help="Percentis apenas contra jogadores da Série B")
            
            # Dataset para cálculo de percentis
            if comparar_serie_b_t1:
                wyscout_percentil_t1 = wyscout[wyscout['Equipa'].apply(is_serie_b_team)].copy()
            else:
                wyscout_percentil_t1 = wyscout.copy()
            
            # LEGENDA
            st.markdown(create_legend_html(), unsafe_allow_html=True)
            
            if ws_match is not None:
                # Filtrar jogadores da mesma posição
                wyscout_pos = wyscout_percentil_t1[wyscout_percentil_t1['Posição'].apply(get_posicao_categoria) == posicao_categoria].copy()
                n_jogadores_pos = len(wyscout_pos)
                
                # Calcular índices compostos
                indices = INDICES_CONFIG.get(posicao_categoria, INDICES_CONFIG['Meia'])
                indices_values = calculate_all_indices(ws_match, indices, wyscout_percentil_t1, posicao_categoria)
                
                # Header com info do match
                comp_label = " (vs Série B)" if comparar_serie_b_t1 else ""
                st.markdown(f"""
                <div style="background: {COLORS['card']}; border-radius: 8px; padding: 12px; margin: 16px 0; border: 1px solid {COLORS['border']}; text-align: center;">
                    <span style="color: {COLORS['accent']}; font-weight: 600;">Dados Wyscout:</span>
                    <span style="color: white; font-weight: 600;"> {ws_match['Jogador']}</span>
                    <span style="color: {COLORS['text_secondary']};"> • {ws_match['Equipa']} • {display_int(ws_match['Minutos jogados:'], ' min', '0 min')}</span>
                    <span style="color: {COLORS['text_muted']};"> | Comparando com {n_jogadores_pos} {posicao_categoria.lower()}s{comp_label}</span>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(create_section_title("📊", f"Índices Compostos ({posicao_categoria})"), unsafe_allow_html=True)
                    st.plotly_chart(create_wyscout_radar(indices_values), width='stretch', config={'displayModeBar': False}, key="radar_idx_t1")
                
                with col2:
                    st.markdown(create_section_title("📈", "Métricas Principais"), unsafe_allow_html=True)
                    metrics_perc = calculate_metric_percentiles(ws_match, posicao_categoria, wyscout_percentil_t1, top_n=12)
                    if metrics_perc:
                        st.plotly_chart(create_bar_chart(metrics_perc, "Top Métricas (Percentil)"), width='stretch', config={'displayModeBar': False}, key="bar_metrics_t1")
                
                # RANKING DA POSIÇÃO
                st.markdown(create_section_title("🏆", f"Ranking de {posicao_categoria}s"), unsafe_allow_html=True)
                
                # Calcular índice médio para todos da posição
                df_ranking_t1 = rank_players_weighted(
                    wyscout_pos, posicao_categoria, wyscout_percentil_t1,
                    indices_config=indices, min_minutes=0, include_indices=False
                )
                ranking_data = []
                if len(df_ranking_t1) > 0:
                    for _, row in df_ranking_t1.head(20).iterrows():
                        ranking_data.append({
                            'Jogador': row['Jogador'],
                            'Clube': row['Equipa'],
                            'Idade': safe_int(row.get('Idade')),
                            'Min': safe_int(row.get('Minutos jogados:')),
                            'Índice Médio': row['Score']
                        })
                
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
            indices_values = calculate_all_indices(player_ws, indices, wyscout, categoria)
            
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
            indices_values = calculate_all_indices(player_rel, indices, wyscout, posicao_rel)
            
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
                except (ValueError, TypeError):
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
                            except (ValueError, TypeError):
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
            idx1 = calculate_all_indices(p1, indices, wyscout, categoria_cmp)
            idx2 = calculate_all_indices(p2, indices, wyscout, categoria_cmp)
            
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
                            except (ValueError, TypeError):
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
    
    # ===== TAB 6: RANKING =====
    with tab6:
        st.markdown(create_section_title("🏆", "Ranking de Jogadores"), unsafe_allow_html=True)
        
        # Info dos dados disponíveis
        st.markdown(f"""
        <div style="background: {COLORS['card']}; border-radius: 8px; padding: 12px; margin-bottom: 16px; border: 1px solid {COLORS['border']};">
            <span style="color: {COLORS['text_muted']}; font-size: 12px;">
                📊 {len(wyscout)} jogadores WyScout | 🏃 {len(skillcorner)} jogadores SkillCorner (dados físicos integrados quando disponíveis)
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # ===== OPÇÃO DE COMPARATIVO =====
        col_comp1, col_comp2 = st.columns([1, 3])
        with col_comp1:
            comparar_serie_b = st.checkbox("🇧🇷 Comparar com Série B", value=False, key='comp_serie_b',
                                           help="Calcula percentis apenas contra jogadores da Série B 2025")
        
        # Dataset para cálculo de percentis
        if comparar_serie_b:
            # Filtrar apenas jogadores de times da Série B
            wyscout_percentil = wyscout[wyscout['Equipa'].apply(is_serie_b_team)].copy()
            with col_comp2:
                st.markdown(f"""
                <div style="background: #1a3a1a; border-radius: 6px; padding: 8px 12px; display: inline-block;">
                    <span style="color: #22c55e; font-size: 12px;">
                        ✓ Percentis calculados contra {len(wyscout_percentil)} jogadores da Série B 2025
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            wyscout_percentil = wyscout.copy()
        
        # ===== FILTROS LINHA 1 =====
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            posicao_rank = st.selectbox("📍 Posição", ['Todas'] + list(INDICES_CONFIG.keys()), key='pos_ranking')
        
        with col_f2:
            # Ligas únicas - verificar qual coluna existe
            liga_col = None
            for col_name in ['Liga', 'Competição', 'Competition', 'League']:
                if col_name in wyscout.columns:
                    liga_col = col_name
                    break
            
            if liga_col:
                ligas_unicas = sorted([str(l) for l in wyscout[liga_col].dropna().unique() if str(l) not in ('nan', '')])
                liga_rank = st.selectbox("🏆 Liga", ['Todas'] + ligas_unicas, key='liga_ranking')
            else:
                liga_rank = 'Todas'
                st.caption("Liga não disponível")
        
        with col_f3:
            # Clubes únicos
            equipa_col = 'Equipa' if 'Equipa' in wyscout.columns else 'Team' if 'Team' in wyscout.columns else None
            if equipa_col:
                if liga_rank != 'Todas' and liga_col:
                    clubes_liga = sorted([str(c) for c in wyscout[wyscout[liga_col] == liga_rank][equipa_col].dropna().unique() if str(c) not in ('nan', '')])
                else:
                    clubes_liga = sorted([str(c) for c in wyscout[equipa_col].dropna().unique() if str(c) not in ('nan', '')])
                clube_rank = st.selectbox("🏟️ Clube", ['Todos'] + clubes_liga, key='clube_ranking')
            else:
                clube_rank = 'Todos'
        
        with col_f4:
            # Nacionalidades - usa apenas a primeira de cada (ex: "Brazil, Senegal" -> "Brazil")
            nac_col = None
            for col_name in ['Passaporte', 'País de nacionalidade', 'Nacionalidade', 'Nationality']:
                if col_name in wyscout.columns:
                    nac_col = col_name
                    break
            
            if nac_col:
                # Extrair apenas a primeira nacionalidade de cada jogador
                nacionalidades_primarias = wyscout[nac_col].apply(get_primary_nationality).dropna().unique()
                nacionalidades = sorted([str(n) for n in nacionalidades_primarias if str(n) not in ('nan', '', 'None')])
                nac_rank = st.selectbox("🌍 Nacionalidade", ['Todas'] + nacionalidades, key='nac_ranking')
            else:
                nac_rank = 'Todas'
        
        # ===== FILTROS LINHA 2 =====
        col_f5, col_f6, col_f7, col_f8 = st.columns(4)
        
        with col_f5:
            idade_range = st.slider("📅 Idade", 15, 45, (18, 35), key='idade_ranking')
        
        with col_f6:
            min_minutos = st.number_input("⏱️ Minutos Mín", min_value=0, max_value=5000, value=500, step=100, key='min_min_rank')
        
        with col_f7:
            # Pé preferido
            if 'Pé' in wyscout.columns:
                pes = ['Todos'] + sorted([str(p) for p in wyscout['Pé'].dropna().unique() if str(p) not in ('nan', '')])
                pe_rank = st.selectbox("🦶 Pé Preferido", pes, key='pe_ranking')
            else:
                pe_rank = 'Todos'
        
        with col_f8:
            # Altura
            if 'Altura' in wyscout.columns:
                altura_range = st.slider("📏 Altura (cm)", 150, 210, (160, 200), key='altura_ranking')
            else:
                altura_range = (150, 210)
        
        # ===== FILTROS LINHA 3 =====
        col_f9, col_f10 = st.columns(2)
        
        with col_f9:
            busca_nome = st.text_input("🔍 Buscar por nome", key='busca_ranking')
        
        with col_f10:
            # Opções de ordenação baseadas na posição
            if posicao_rank != 'Todas':
                posicao_cat = get_posicao_categoria(posicao_rank)
                indices_posicao = INDICES_CONFIG.get(posicao_cat, {})
                
                # Métricas específicas por posição
                metricas_especificas = []
                for idx_name, metrics in indices_posicao.items():
                    metricas_especificas.append(f"📊 {idx_name} (índice)")
                    metricas_especificas.extend(metrics[:3])  # Top 3 métricas de cada índice
                
                metricas_ord = ['🎯 Índice Geral'] + metricas_especificas
            else:
                metricas_ord = [
                    '🎯 Índice Geral',
                    'Golos/90', 'Assistências/90', 'Golos esperados/90', 'Assistências esperadas/90',
                    'Passes progressivos/90', 'Corridas progressivas/90', 'Dribles/90', 
                    'Duelos ganhos, %', 'Interseções/90', 'Passes certos, %'
                ]
            # Adicionar P(Sucesso) como opção de ordenação (requer motor preditivo)
            if HAS_PREDICTIVE:
                metricas_ord.append('🎯 P(Sucesso)')
            ordenar_por = st.selectbox("📈 Ordenar por", metricas_ord, key='ordenar_ranking')
        
        # ===== FILTRO EXTRA: LIGA ALVO (para predição) =====
        if HAS_PREDICTIVE:
            col_pred1, col_pred2 = st.columns([1, 3])
            with col_pred1:
                incluir_predicao = st.checkbox("🎯 Incluir P(Sucesso)", value=False, key=f'inc_pred_rank_{posicao_rank}',
                                                help="Calcula probabilidade de sucesso contratual para cada jogador")
            with col_pred2:
                if incluir_predicao:
                    ligas_alvo_ranking = [
                        'Serie B Brasil', 'Serie A Brasil', 'Serie C Brasil',
                        'Liga Portugal', 'Liga Portugal 2', 'MLS',
                        'Liga Argentina', 'J1 League', 'Saudi Pro League',
                        'Premier League', 'La Liga', 'Bundesliga',
                        'Serie A Italia', 'Ligue 1', 'Eredivisie',
                        'Championship', 'Belgian Pro League', 'Super Lig',
                        'Liga MX', 'Liga Colombia', 'Liga Chile',
                        'K-League 1', 'A-League',
                    ]
                    liga_alvo_rank = st.selectbox("Liga Alvo (contratação)", ligas_alvo_ranking,
                                                   index=0, key=f'liga_alvo_rank_{posicao_rank}')
                else:
                    liga_alvo_rank = 'Serie B Brasil'
        else:
            incluir_predicao = False
            liga_alvo_rank = 'Serie B Brasil'
        
                # ===== APLICAR FILTROS =====
        df_rank = wyscout.copy()
        
        # Filtro de posição
        if posicao_rank != 'Todas' and 'Posição' in df_rank.columns:
            df_rank = df_rank[df_rank['Posição'].apply(get_posicao_categoria) == posicao_rank]
        
        # Filtro de liga (WyScout não tem essa coluna)
        if liga_rank != 'Todas' and liga_col and liga_col in df_rank.columns:
            df_rank = df_rank[df_rank[liga_col] == liga_rank]
        
        # Filtro de clube
        if clube_rank != 'Todos' and equipa_col and equipa_col in df_rank.columns:
            df_rank = df_rank[df_rank[equipa_col] == clube_rank]
        
        # Filtro de nacionalidade (compara com a primeira nacionalidade)
        if nac_rank != 'Todas' and nac_col and nac_col in df_rank.columns:
            df_rank = df_rank[df_rank[nac_col].apply(get_primary_nationality) == nac_rank]
        
        # Filtro de idade
        if 'Idade' in df_rank.columns:
            df_rank['Idade'] = df_rank['Idade'].apply(safe_float)
            df_rank = df_rank[(df_rank['Idade'] >= idade_range[0]) & (df_rank['Idade'] <= idade_range[1])]
        
        # Filtro de minutos
        if 'Minutos jogados:' in df_rank.columns:
            df_rank['Minutos jogados:'] = df_rank['Minutos jogados:'].apply(safe_float)
            df_rank = df_rank[df_rank['Minutos jogados:'] >= min_minutos]
        
        # Filtro de pé
        if pe_rank != 'Todos' and 'Pé' in df_rank.columns:
            df_rank = df_rank[df_rank['Pé'] == pe_rank]
        
        # Filtro de altura
        if 'Altura' in df_rank.columns:
            df_rank['Altura'] = df_rank['Altura'].apply(safe_float)
            df_rank = df_rank[(df_rank['Altura'] >= altura_range[0]) & (df_rank['Altura'] <= altura_range[1]) | df_rank['Altura'].isna()]
        
        # Filtro de busca por nome
        if busca_nome and 'Jogador' in df_rank.columns:
            df_rank = df_rank[df_rank['Jogador'].str.contains(busca_nome, case=False, na=False)]
        
        # ===== CALCULAR E MOSTRAR RANKING =====
        if len(df_rank) > 0:
            st.markdown(f"**{len(df_rank)} jogadores encontrados**")
            
            # Verificar se é ordenação por índice
            is_indice = ordenar_por.startswith('📊') or ordenar_por == '🎯 Índice Geral'
            
            if is_indice:
                # Calcular índices compostos
                if posicao_rank == 'Todas':
                    posicao_calc = 'Meia'  # Default para cálculo
                else:
                    posicao_calc = get_posicao_categoria(posicao_rank)
                
                indices_cfg = INDICES_CONFIG.get(posicao_calc, INDICES_CONFIG['Meia'])
                ranking_data = []
                
                # Usar lookup cached do SkillCorner (O(1) ao invés de O(n²))
                sc_lookup = create_skillcorner_lookup(skillcorner)
                
                # Limitar para performance (calcular só top candidatos)
                df_rank_limited = df_rank.head(500)
                
                with st.spinner(f'Calculando ranking ponderado para {len(df_rank_limited)} jogadores...'):
                    # Motor preditivo v3 (se disponível)
                    ssp_engine = None
                    if HAS_PREDICTIVE:
                        ssp_engine = get_ssp_engine(
                            hash(tuple(wyscout_percentil.columns)),
                            wyscout_percentil, posicao_calc
                        )

                    if ssp_engine is not None:
                        df_ranked = ssp_engine.rank_players(
                            df_rank_limited, wyscout_percentil, min_minutes=0
                        )
                        # Compatibilizar coluna Score
                        if 'SSP' in df_ranked.columns and 'Score' not in df_ranked.columns:
                            df_ranked['Score'] = df_ranked['SSP']
                        # Adicionar índices compostos (backward compat)
                        for idx_name, metrics in indices_cfg.items():
                            if idx_name not in df_ranked.columns:
                                for ridx, row in df_ranked.iterrows():
                                    df_ranked.loc[ridx, idx_name] = calculate_weighted_index(
                                        row, metrics, wyscout_percentil, posicao_calc
                                    )
                    else:
                        df_ranked = rank_players_weighted(
                            df_rank_limited,
                            posicao_calc,
                            wyscout_percentil,
                            indices_config=indices_cfg,
                            min_minutes=0,
                            include_indices=True
                        )

                if len(df_ranked) > 0:
                    sc_lookup = create_skillcorner_lookup(skillcorner)

                    ranking_data = []
                    for _, row in df_ranked.iterrows():
                        entry = {
                            'Jogador': row['Jogador'],
                            'Clube': row.get('Equipa', row.get('Team', '-')),
                            'Idade': safe_int(row.get('Idade')),
                            'Min': safe_int(row.get('Minutos jogados:')),
                            'Score': row['Score'],
                        }
                        # Colunas SSP (motor preditivo)
                        for ssp_col in ['WP', 'Efficiency', 'Cluster', 'Percentile']:
                            if ssp_col in row.index and pd.notna(row.get(ssp_col)):
                                entry[ssp_col] = row[ssp_col]
                        for idx_name in indices_cfg.keys():
                            if idx_name in row.index and pd.notna(row[idx_name]):
                                entry[idx_name] = row[idx_name]

                        nome_jogador = normalize_name(row['Jogador'])
                        sc_data = sc_lookup.get(nome_jogador, {})
                        if sc_data and posicao_calc in SKILLCORNER_INDICES:
                            for sc_idx in SKILLCORNER_INDICES[posicao_calc]:
                                short_name = sc_idx.replace(' index', '').replace(' midfielder', '').replace('central ', '')
                                if short_name in sc_data:
                                    entry[f'SC: {short_name}'] = sc_data[short_name]

                    # P(Sucesso) — predição de contratação
                        if HAS_PREDICTIVE and incluir_predicao:
                            _age = safe_float(row.get('Idade'), 25)
                            _mins = safe_float(row.get('Minutos jogados:'), 0)
                            _ssp = entry['Score']
                            _liga_ws = row.get(liga_col) if liga_col and liga_col in row.index else None
                            _equipa = row.get('Equipa', row.get('Team'))
                            _liga_origin = resolve_league_to_tier(_liga_ws, _equipa)
                            if _liga_origin is None:
                                _liga_origin = liga_alvo_rank
                            try:
                                _pred = ContractSuccessPredictor().predict_success_unsupervised(
                                    ssp_score=_ssp, age=_age,
                                    league_origin=_liga_origin,
                                    league_target=liga_alvo_rank,
                                    minutes=_mins,
                                )
                                entry['P(Sucesso)'] = round(_pred['success_probability'] * 100, 1)
                                entry['Risco'] = _pred['risk_level'].capitalize()
                                entry['Gap Liga'] = round(_pred.get('league_gap', 0), 1)
                            except Exception:
                                entry['P(Sucesso)'] = None
                                entry['Risco'] = '-'
                                entry['Gap Liga'] = None    
                        
                        ranking_data.append(entry)

                    if ranking_data:
                        df_resultado = pd.DataFrame(ranking_data)

                        if ordenar_por == '🎯 Índice Geral':
                            sort_col = 'Score'
                        elif ordenar_por == '🎯 P(Sucesso)':
                            sort_col = 'P(Sucesso)'
                        else:
                            sort_col = ordenar_por.replace('📊 ', '').replace(' (índice)', '')

                        if sort_col in df_resultado.columns:
                            df_resultado = df_resultado.sort_values(sort_col, ascending=False)
                        else:
                            df_resultado = df_resultado.sort_values('Score', ascending=False)

                        df_resultado = df_resultado.head(100)
                        df_resultado.insert(0, '#', range(1, len(df_resultado) + 1))

                        column_config = {
                            '#': st.column_config.NumberColumn(width='small'),
                            'Score': st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
                        }
                        for ssp_c in ['WP', 'Efficiency', 'Cluster', 'Percentile']:
                            if ssp_c in df_resultado.columns:
                                column_config[ssp_c] = st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f")
                        for col in df_resultado.columns:
                            if col in list(indices_cfg.keys()):
                                column_config[col] = st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f")
                            elif col.startswith('SC:'):
                                column_config[col] = st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f")
                        # Colunas de predicao de sucesso
                        if 'P(Sucesso)' in df_resultado.columns:
                            column_config['P(Sucesso)'] = st.column_config.ProgressColumn(
                                label="P(Sucesso) %", min_value=0, max_value=100, format="%.1f%%"
                            )
                        if 'Gap Liga' in df_resultado.columns:
                            column_config['Gap Liga'] = st.column_config.NumberColumn(format="%.1f")

                        st.dataframe(df_resultado, width='stretch', height=600, hide_index=True, column_config=column_config)

            else:
                # Ordenacao por metrica bruta (nao-indice)
                sort_col = ordenar_por
                if sort_col in df_rank.columns:
                    df_rank_sorted = df_rank.sort_values(sort_col, ascending=False).head(100)

                    show_cols = ['Jogador']
                    if equipa_col and equipa_col in df_rank_sorted.columns:
                        show_cols.append(equipa_col)
                    for c in ['Idade', 'Minutos jogados:', sort_col]:
                        if c in df_rank_sorted.columns and c not in show_cols:
                            show_cols.append(c)

                    df_resultado = df_rank_sorted[show_cols].copy()
                    df_resultado.insert(0, '#', range(1, len(df_resultado) + 1))
                    st.dataframe(df_resultado, width='stretch', height=600, hide_index=True)
                else:
                    st.warning(f"Coluna '{sort_col}' nao encontrada nos dados")
    
    # ===== TAB 7: SIMILARIDADE =====
    with tab7:
        st.markdown(create_section_title("🔍", "Busca por Similaridade"), unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background: {COLORS['card']}; border-radius: 8px; padding: 12px; margin-bottom: 16px; border: 1px solid {COLORS['border']};">
            <span style="color: {COLORS['text_secondary']}; font-size: 13px;">
                Algoritmo de similaridade ponderada por posição (cosine similarity + proximity bonus).
                Pesos específicos para cada posição destacam as métricas mais relevantes.
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Seleção do jogador de referência
        col_sim1, col_sim2 = st.columns(2)
        
        with col_sim1:
            jogadores_ws_sim = sorted(wyscout['JogadorDisplay'].dropna().unique().tolist())
            jogador_ref = st.selectbox("Jogador de Referência", jogadores_ws_sim, key='jogador_sim_ref')
        
        with col_sim2:
            if jogador_ref:
                row_ref = wyscout[wyscout['JogadorDisplay'] == jogador_ref].iloc[0]
                pos_ref = get_posicao_categoria(row_ref.get('Posição', ''))
                if pos_ref is None:
                    pos_ref = 'Meia'
            else:
                pos_ref = 'Meia'
            
            categorias_sim = list(POSITION_WEIGHTS.keys())
            idx_cat = categorias_sim.index(pos_ref) if pos_ref in categorias_sim else 0
            categoria_sim = st.selectbox("Categoria de Posição", categorias_sim, index=idx_cat, key='cat_sim')
        
        # Filtros
        col_sim3, col_sim4, col_sim5, col_sim6 = st.columns(4)
        
        with col_sim3:
            apenas_mesma_pos = st.checkbox("Apenas mesma posição", value=True, key='mesma_pos_sim')
        
        with col_sim4:
            idade_sim_range = st.slider("Faixa de Idade", 16, 40, (18, 35), key='idade_sim')
        
        with col_sim5:
            min_min_sim = st.number_input("Minutos Mín", min_value=0, max_value=5000, value=500, step=100, key='min_sim')
        
        with col_sim6:
            top_n_sim = st.number_input("Top N resultados", min_value=5, max_value=50, value=20, step=5, key='top_n_sim')
        
        comparar_serie_b_sim = st.checkbox("🇧🇷 Percentis vs Série B", value=False, key='comp_serie_b_sim',
                                            help="Calcula percentis apenas contra jogadores da Série B 2025")
        
        if st.button("🔍 Buscar Similares", key='btn_sim', type='primary'):
            if jogador_ref:
                row_ref = wyscout[wyscout['JogadorDisplay'] == jogador_ref].iloc[0]
                
                # Montar pool de comparação
                wyscout_pool = wyscout.copy()
                
                if apenas_mesma_pos:
                    wyscout_pool = wyscout_pool[wyscout_pool['Posição'].apply(get_posicao_categoria) == categoria_sim]
                
                # Filtro de idade
                wyscout_pool['_idade_f'] = wyscout_pool['Idade'].apply(safe_float)
                wyscout_pool = wyscout_pool[
                    (wyscout_pool['_idade_f'] >= idade_sim_range[0]) & 
                    (wyscout_pool['_idade_f'] <= idade_sim_range[1])
                ]
                wyscout_pool = wyscout_pool.drop(columns=['_idade_f'])
                
                # Excluir o próprio jogador
                wyscout_pool = wyscout_pool[wyscout_pool['JogadorDisplay'] != jogador_ref]
                
                # Base de percentis
                if comparar_serie_b_sim:
                    percentile_base_sim = wyscout[wyscout['Equipa'].apply(is_serie_b_team)].copy()
                else:
                    percentile_base_sim = wyscout.copy()
                
                with st.spinner(f'Calculando similaridade ponderada para {len(wyscout_pool)} candidatos...'):
                    try:
                        if HAS_PREDICTIVE:
                            similar_players = compute_advanced_similarity(
                                target_player=row_ref,
                                comparison_pool=wyscout_pool,
                                position=categoria_sim,
                                top_n=top_n_sim,
                                min_minutes=min_min_sim,
                                minutes_col='Minutos jogados:',
                                player_display_col='JogadorDisplay',
                                percentile_base=percentile_base_sim,
                            )
                        else:
                            similar_players = compute_weighted_cosine_similarity(
                                target_player=row_ref,
                                comparison_pool=wyscout_pool,
                                position=categoria_sim,
                                top_n=top_n_sim,
                                min_minutes=min_min_sim,
                                minutes_col='Minutos jogados:',
                                player_display_col='JogadorDisplay',
                                percentile_base=percentile_base_sim,
                            )
                    except Exception as e:
                        st.error(f"Erro no cálculo de similaridade: {e}")
                        similar_players = None
                
                if similar_players is not None and len(similar_players) > 0:
                    # Info do jogador de referência
                    flag_ref_sim = get_flag(row_ref.get('País de nacionalidade', ''))
                    club_logo_ref_sim = get_club_logo_html(row_ref.get('Equipa', ''), size=20)
                    
                    comp_label_sim = "| Percentis vs Série B" if comparar_serie_b_sim else ""
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {COLORS['accent']}, #b91c1c); border-radius: 8px; padding: 16px; margin: 16px 0;">
                        <div style="color: rgba(255,255,255,0.7); font-size: 11px; letter-spacing: 1px;">JOGADOR DE REFERÊNCIA</div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
                            <span style="font-size: 24px;">{flag_ref_sim}</span>
                            <span style="color: white; font-size: 20px; font-weight: 700;">{row_ref['Jogador']}</span>
                        </div>
                        <div style="color: rgba(255,255,255,0.8); font-size: 13px; margin-top: 4px;">
                            {club_logo_ref_sim}{row_ref['Equipa']} | {safe_int(row_ref.get('Idade'))} anos | 
                            {display_int(row_ref.get('Minutos jogados:'), ' min')} | {categoria_sim}
                        </div>
                        <div style="color: rgba(255,255,255,0.6); font-size: 11px; margin-top: 6px;">
                            {'Mahalanobis + RF Proximity + Cluster Fit' if HAS_PREDICTIVE else 'Cosine Similarity ponderada (70%) + Proximity Bonus (30%)'} | 
                            {len(wyscout_pool)} candidatos {comp_label_sim}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Preparar DataFrame para exibição
                    df_sim_display = similar_players.copy()
                    df_sim_display.insert(0, '#', range(1, len(df_sim_display) + 1))
                    
                    # Colunas para exibição
                    show_cols = ['#']
                    col_rename = {'similarity_pct': 'Similaridade %', 'matched_metrics': 'Métricas'}
                    
                    if 'JogadorDisplay' in df_sim_display.columns:
                        show_cols.append('JogadorDisplay')
                        col_rename['JogadorDisplay'] = 'Jogador'
                    elif 'Jogador' in df_sim_display.columns:
                        show_cols.append('Jogador')
                    
                    if 'Equipa' in df_sim_display.columns:
                        show_cols.append('Equipa')
                        col_rename['Equipa'] = 'Clube'
                    
                    for c in ['Idade', 'Minutos jogados:']:
                        if c in df_sim_display.columns:
                            show_cols.append(c)
                    
                    show_cols.extend(['similarity_pct', 'matched_metrics'])
                    # Colunas do motor avançado
                    for adv_col in ['mahalanobis_sim', 'rf_proximity']:
                        if adv_col in df_sim_display.columns:
                            show_cols.append(adv_col)
                            col_rename[adv_col] = adv_col.replace('_', ' ').title()
                    show_cols = [c for c in show_cols if c in df_sim_display.columns]
                    
                    df_sim_show = df_sim_display[show_cols].rename(columns=col_rename)
                    
                    st.markdown(f"**Top {len(df_sim_show)} jogadores mais similares**")
                    
                    st.dataframe(
                        df_sim_show,
                        width='stretch',
                        height=min(500, 50 + len(df_sim_show) * 35),
                        hide_index=True,
                        column_config={
                            '#': st.column_config.NumberColumn(width='small'),
                            'Similaridade %': st.column_config.ProgressColumn(
                                min_value=0, max_value=100, format="%.1f%%"
                            ),
                            'Métricas': st.column_config.NumberColumn(width='small'),
                        }
                    )
                    
                    # ===== COMPARAÇÃO DETALHADA =====
                    st.markdown(create_section_title("📊", "Comparação Detalhada"), unsafe_allow_html=True)
                    
                    if 'JogadorDisplay' in similar_players.columns:
                        similares_list = similar_players['JogadorDisplay'].tolist()
                    elif 'Jogador' in similar_players.columns:
                        similares_list = similar_players['Jogador'].tolist()
                    else:
                        similares_list = []
                    
                    if similares_list:
                        comparar_com = st.selectbox("Comparar com:", similares_list, key='sim_compare_select')
                        
                        if comparar_com:
                            if 'JogadorDisplay' in similar_players.columns:
                                row_similar = wyscout[wyscout['JogadorDisplay'] == comparar_com]
                            else:
                                row_similar = wyscout[wyscout['Jogador'] == comparar_com]
                            
                            if not row_similar.empty:
                                row_similar = row_similar.iloc[0]
                                
                                # Breakdown detalhado
                                try:
                                    breakdown = get_similarity_breakdown(
                                        row_ref, row_similar, categoria_sim, percentile_base=percentile_base_sim
                                    )
                                except Exception:
                                    breakdown = None
                                
                                # Radar comparativo de índices compostos
                                indices_cfg_sim = INDICES_CONFIG.get(categoria_sim, INDICES_CONFIG['Meia'])
                                base_calc_sim = percentile_base_sim if comparar_serie_b_sim else wyscout
                                
                                indices_ref_vals = calculate_all_indices(row_ref, indices_cfg_sim, base_calc_sim, categoria_sim)
                                indices_sim_vals = calculate_all_indices(row_similar, indices_cfg_sim, base_calc_sim, categoria_sim)
                                
                                # Headers
                                flag_sim_h = get_flag(row_similar.get('País de nacionalidade', ''))
                                club_logo_sim_h = get_club_logo_html(row_similar.get('Equipa', ''), size=18)
                                
                                col_h1, col_h2 = st.columns(2)
                                with col_h1:
                                    st.markdown(f"""
                                    <div style="background: rgba(220,38,38,0.2); border: 2px solid {COLORS['accent']}; border-radius: 8px; padding: 12px;">
                                        <span style="font-size: 20px;">{flag_ref_sim}</span>
                                        <span style="color: white; font-weight: 700;">{row_ref['Jogador']}</span>
                                        <div style="color: {COLORS['text_secondary']}; font-size: 12px; margin-top: 4px;">{club_logo_ref_sim}{row_ref['Equipa']}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col_h2:
                                    st.markdown(f"""
                                    <div style="background: rgba(59,130,246,0.2); border: 2px solid #3b82f6; border-radius: 8px; padding: 12px;">
                                        <span style="font-size: 20px;">{flag_sim_h}</span>
                                        <span style="color: white; font-weight: 700;">{row_similar['Jogador']}</span>
                                        <div style="color: {COLORS['text_secondary']}; font-size: 12px; margin-top: 4px;">{club_logo_sim_h}{row_similar['Equipa']}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                # Radar overlay
                                st.plotly_chart(
                                    create_comparison_radar(indices_ref_vals, indices_sim_vals, row_ref['Jogador'], row_similar['Jogador']),
                                    width='stretch', config={'displayModeBar': False}, key="radar_sim_cmp"
                                )
                                
                                # Tabela de índices
                                comparison_idx_data = []
                                for idx_name in indices_cfg_sim.keys():
                                    v1 = indices_ref_vals[idx_name]
                                    v2 = indices_sim_vals[idx_name]
                                    diff = v1 - v2
                                    comparison_idx_data.append({
                                        'Índice': idx_name,
                                        row_ref['Jogador']: f"{v1:.0f}",
                                        row_similar['Jogador']: f"{v2:.0f}",
                                        'Diff': f"+{diff:.0f}" if diff > 0 else f"{diff:.0f}",
                                        ' ': '🔴' if diff > 0 else '🔵' if diff < 0 else '='
                                    })
                                st.dataframe(pd.DataFrame(comparison_idx_data), width='stretch', hide_index=True)
                                
                                # Breakdown métrica a métrica
                                if breakdown is not None and len(breakdown) > 0:
                                    st.markdown(create_section_title("🔬", "Breakdown por Métrica"), unsafe_allow_html=True)
                                    st.dataframe(
                                        breakdown,
                                        width='stretch',
                                        height=min(500, 50 + len(breakdown) * 35),
                                        hide_index=True,
                                    )
                    
                    # Exportar
                    st.download_button(
                        "📥 Exportar Similaridade (CSV)",
                        df_sim_show.to_csv(index=False).encode('utf-8'),
                        f"similaridade_{categoria_sim}.csv",
                        key='download_sim'
                    )
                
                elif similar_players is not None:
                    st.warning("Nenhum jogador similar encontrado com os critérios especificados")
            else:
                st.warning("Selecione um jogador de referência")

    # ===== TAB 8: PREDIÇÃO DE CONTRATAÇÃO =====
    with tab8:
        st.markdown("### 🎯 Predição de Sucesso de Contratação")
        if not HAS_PREDICTIVE:
            st.warning("Motor preditivo não disponível. Instale as dependências: `pip install scikit-learn scipy statsmodels xgboost`")
        else:
            st.caption("Modelo baseado em SSP + idade + nível da liga + minutagem (Nunes, 2025; Buso, 2025)")
            
            # Seleção do jogador
            jogadores_ws_pred = sorted(wyscout['JogadorDisplay'].dropna().unique().tolist())
            jogador_pred = st.selectbox("Jogador", jogadores_ws_pred, key='jogador_pred')
            
            if jogador_pred:
                row_pred = wyscout[wyscout['JogadorDisplay'] == jogador_pred].iloc[0]
                pos_pred = get_posicao_categoria(row_pred.get('Posição', ''))
                if pos_pred is None:
                    pos_pred = 'Meia'
                
                col_p1, col_p2, col_p3 = st.columns(3)
                with col_p1:
                    # Idade puxada automaticamente do jogador selecionado
                    idade_auto = int(safe_float(row_pred.get('Idade'), 24))
                    st.metric("Idade", f"{idade_auto} anos")
                    idade_pred = idade_auto
                with col_p2:
                    ligas_origem_all = [
                        # Brasil
                        'Serie A Brasil', 'Serie B Brasil', 'Serie C Brasil', 'Serie D Brasil',
                        # Estaduais
                        'Paulista A1', 'Paulista A2', 'Paulista A3',
                        'Carioca A1', 'Gaucho A1', 'Mineiro A1',
                        'Paranaense A1', 'Cearense A1', 'Pernambucano A1', 'Baiano A1',
                        # Copas Brasil
                        'Copa do Brasil', 'Copa do Nordeste',
                        # Top 5 Europa
                        'Premier League', 'La Liga', 'Bundesliga', 'Serie A Italia', 'Ligue 1',
                        # 2ª Divisões Europa
                        'Championship', 'La Liga 2', 'Serie B Italia', '2. Bundesliga', 'Ligue 2',
                        # Europa Tier 2
                        'Liga Portugal', 'Liga Portugal 2', 'Eredivisie', 'Belgian Pro League',
                        'Super Lig', 'Scottish Premiership', 'Russian Premier League',
                        'Austrian Bundesliga', 'Swiss Super League', 'Danish Superliga',
                        'Greek Super League', 'Ukrainian Premier League',
                        'Czech First League', 'Croatian First League', 'Serbian Super Liga',
                        'Polish Ekstraklasa', 'Romanian Liga I',
                        'Norwegian Eliteserien', 'Swedish Allsvenskan',
                        'Israeli Premier League', 'Bulgarian First League', 'Cypriot First Division',
                        # Américas
                        'Liga Argentina', 'Liga Argentina B', 'MLS', 'Liga MX',
                        'Liga Colombia', 'Liga Chile', 'Liga Uruguai', 'Liga Peru',
                        'Liga Equador', 'Liga Paraguai', 'Liga Bolivia', 'Liga Venezuela',
                        # Copas Continentais
                        'Copa Libertadores', 'Copa Sudamericana',
                        # Ásia / Oriente Médio
                        'J1 League', 'J2 League', 'K-League 1',
                        'Saudi Pro League', 'Qatar Stars League', 'UAE Pro League',
                        'Chinese Super League', 'Indian Super League', 'Thai League',
                        # África
                        'Egyptian Premier League', 'Moroccan Botola', 'Tunisian Ligue 1',
                        'South African Premier',
                        # Oceania
                        'A-League',
                    ]
                    liga_origem = st.selectbox("Liga Origem", ligas_origem_all, key='liga_orig')
                with col_p3:
                    ligas_alvo_all = ligas_origem_all.copy()
                    liga_alvo = st.selectbox("Liga Alvo", ligas_alvo_all,
                                             index=ligas_alvo_all.index('Serie B Brasil') if 'Serie B Brasil' in ligas_alvo_all else 0,
                                             key='liga_alvo')
                
                if st.button("Calcular Predição", type='primary', key='btn_pred'):
                    # Obter engine
                    ssp_engine_pred = get_ssp_engine(
                        hash(tuple(wyscout.columns)), wyscout, pos_pred
                    )
                    
                    if ssp_engine_pred is not None:
                        ssp_result = ssp_engine_pred.score_player(row_pred, wyscout)
                        ssp_val = ssp_result.get('ssp', 50.0)
                    else:
                        ssp_val = calculate_overall_score(row_pred, pos_pred, wyscout) or 50.0
                    
                    minutes = safe_float(row_pred.get('Minutos jogados:'), 0)
                    
                    predictor = ContractSuccessPredictor()
                    pred = predictor.predict_success_unsupervised(
                        ssp_score=ssp_val,
                        age=idade_pred,
                        league_origin=liga_origem,
                        league_target=liga_alvo,
                        minutes=minutes,
                    )
                    
                    # Header do jogador
                    flag_pred = get_flag(row_pred.get('País de nacionalidade', ''))
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #1e293b, #0f172a); border-radius: 12px; padding: 20px; margin: 16px 0;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="font-size: 32px;">{flag_pred}</span>
                            <div>
                                <div style="color: white; font-size: 22px; font-weight: 700;">{row_pred['Jogador']}</div>
                                <div style="color: #94a3b8; font-size: 13px;">{row_pred.get('Equipa', '-')} | {pos_pred} | {idade_pred} anos</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Métricas principais
                    risk_colors = {'baixo': '#22c55e', 'medio': '#eab308', 'alto': '#ef4444', 'muito alto': '#991b1b'}
                    risk_color = risk_colors.get(pred['risk_level'], '#6b7280')
                    
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    col_m1.metric("SSP (Score Preditivo)", f"{ssp_val:.1f}/100")
                    col_m2.metric("P(Sucesso)", f"{pred['success_probability']:.1%}")
                    col_m3.metric("Nível de Risco", pred['risk_level'].upper())
                    col_m4.metric("Gap de Liga", f"{pred.get('league_gap', 0):+.1f} tiers")
                    
                    # Info de contexto do gap
                    gap_val = pred.get('league_gap', 0)
                    if gap_val >= 4:
                        st.warning(f"⚠️ Gap de **{gap_val:.0f} tiers** ({liga_origem} → {liga_alvo}). Probabilidade limitada pelo ceiling de {35 if gap_val < 5 else 25 if gap_val < 6 else 15}%.")
                    
                    # Componentes
                    st.markdown("**Decomposição dos Fatores:**")
                    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
                    col_f1.metric("SSP Ajustado", f"{pred['ssp_contribution']:.3f}", help="SSP descontado pelo nível da liga de origem")
                    col_f2.metric("Fator Idade", f"{pred['age_factor']:.3f}", help="Peak=26, decay quadrático")
                    col_f3.metric("Fator Liga", f"{pred['league_factor']:.3f}", help=f"Tiers: {pred.get('tier_origin', '?')} → {pred.get('tier_target', '?')}")
                    col_f4.metric("Fator Minutos", f"{pred['minutes_factor']:.3f}")
                    col_f5.metric("Desconto Liga", f"{pred.get('league_discount', 1):.1%}", help="SSP de ligas fracas é descontado")
                    
                    if ssp_engine_pred is not None:
                        st.markdown("**Componentes do SSP:**")
                        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                        col_s1.metric("Win-Prob", f"{ssp_result.get('wp_component', 0):.1f}")
                        col_s2.metric("Eficiência xG", f"{ssp_result.get('efficiency_component', 0):.1f}")
                        col_s3.metric("Cluster Fit", f"{ssp_result.get('cluster_component', 0):.1f}")
                        col_s4.metric("Percentil", f"{ssp_result.get('percentile_component', 0):.1f}")

    # ===== TAB 9: CLUSTERS TÁTICOS =====
    with tab9:
        st.markdown("### 🧬 Perfis Táticos por Clusterização")
        if not HAS_PREDICTIVE:
            st.warning("Motor preditivo não disponível. Instale as dependências: `pip install scikit-learn scipy statsmodels xgboost`")
        else:
            st.caption("K-Means + Gaussian Mixture + Random Forest (Ferra, 2025; Nunes, 2025)")
            
            categorias_cluster = list(POSITION_WEIGHTS.keys())
            posicao_cluster = st.selectbox("Posição para Clusterização", categorias_cluster, key='pos_cluster')
            
            min_min_cluster = st.number_input("Minutos Mínimos", 0, 5000, 500, 100, key='min_cluster')
            
            if st.button("🧬 Identificar Perfis", type='primary', key='btn_cluster'):
                pp = DataPreprocessor()
                # Filtrar por posição antes de clusterizar
                wyscout_cluster = wyscout[wyscout['Posição'].apply(get_posicao_categoria) == posicao_cluster].copy()
                features = pp.get_available_features(wyscout_cluster, posicao_cluster)
                
                if len(features) < 5:
                    st.error(f"Features insuficientes para {posicao_cluster}: {len(features)}")
                else:
                    try:
                        df_f, X, available = pp.prepare_matrix(wyscout_cluster, features, min_minutes=min_min_cluster)
                        
                        if len(df_f) < 15:
                            st.warning(f"Jogadores insuficientes para clustering: {len(df_f)} (mínimo: 15)")
                        else:
                            with st.spinner(f'Clusterizando {len(df_f)} jogadores...'):
                                tc = TacticalClusterer()
                                tc.fit(X, available)
                                
                                result = tc.predict(X)
                                df_f['Cluster'] = result['labels']
                                df_f['Prob_Cluster'] = (result['probabilities'].max(axis=1) * 100).round(1)
                            
                            st.success(f"**{tc.optimal_k} perfis táticos** identificados em {len(df_f)} {posicao_cluster.lower()}s")
                            
                            # Resumo por cluster
                            for k in range(tc.optimal_k):
                                mask = df_f['Cluster'] == k
                                df_cluster = df_f[mask]
                                profile = tc.cluster_profiles.get(k, {})
                                
                                with st.expander(f"Perfil {k+1} — {profile.get('size', 0)} jogadores", expanded=(k==0)):
                                    # Top jogadores do cluster — ordenados por probabilidade de pertencimento
                                    jogadores_cluster = df_cluster.sort_values('Prob_Cluster', ascending=False).head(10)
                                    show_cols_cl = ['Jogador', 'Equipa', 'Prob_Cluster']
                                    for c in ['Idade', 'Minutos jogados:']:
                                        if c in jogadores_cluster.columns:
                                            show_cols_cl.append(c)
                                    show_cols_cl = [c for c in show_cols_cl if c in jogadores_cluster.columns]
                                    
                                    if show_cols_cl:
                                        st.dataframe(jogadores_cluster[show_cols_cl], hide_index=True, width='stretch')
                                    
                                    # Características do cluster
                                    if 'centroid' in profile:
                                        top_feats = sorted(
                                            profile['centroid'].items(),
                                            key=lambda x: -abs(x[1])
                                        )[:8]
                                        feat_df = pd.DataFrame(top_feats, columns=['Métrica', 'Centróide (z-score)'])
                                        feat_df['Centróide (z-score)'] = feat_df['Centróide (z-score)'].round(2)
                                        st.dataframe(feat_df, hide_index=True)
                    
                    except Exception as e:
                        st.error(f"Erro na clusterização: {e}")

    # ===== TAB ADMIN: USUÁRIOS =====
    if is_admin and tab_admin:
        with tab_admin:
            render_admin_panel()


if __name__ == "__main__":
    # Inicializar banco de autenticação
    init_db()

    # Gate de autenticação
    if not is_authenticated():
        render_login_page()
    else:
        main()
