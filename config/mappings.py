"""
config/mappings.py — Dicionários estáticos e configurações do Scouting Dashboard.

Extraído do monolito app.py para desacoplar dados estáticos da lógica de UI.
Contém: COUNTRY_FLAGS, CLUB_LOGOS, LEAGUE_LOGOS, POSICAO_MAP, INDICES_CONFIG,
         WYSCOUT_LEAGUE_MAP, CLUB_LEAGUE_MAP, SKILLCORNER_INDICES, SERIE_B_TEAMS, COLORS.
"""

import unicodedata
import pandas as pd


# ============================================
# NORMALIZAÇÃO REUTILIZÁVEL
# ============================================

def padronizar_string(texto):
    """Normaliza string removendo acentos, convertendo para minúsculas e strip."""
    if texto is None or (isinstance(texto, float) and pd.isna(texto)):
        return None
    try:
        if pd.isna(texto):
            return None
    except (TypeError, ValueError):
        pass
    s = unicodedata.normalize('NFD', str(texto))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.lower().strip()


def normalize_name(name):
    """Normaliza nome para comparação (sem acentos, lowercase)."""
    if pd.isna(name):
        return ""
    name = unicodedata.normalize('NFD', str(name))
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    return name.lower().strip()


# ============================================
# CORES (Design System)
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
    'England': '🏴\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F', 'Inglaterra': '🏴\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F', 'English': '🏴\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F',
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
    'Scotland': '🏴\U000E0067\U000E0062\U000E0073\U000E0063\U000E0074\U000E007F', 'Escócia': '🏴\U000E0067\U000E0062\U000E0073\U000E0063\U000E0074\U000E007F',
    'Wales': '🏴\U000E0067\U000E0062\U000E0077\U000E006C\U000E0073\U000E007F', 'País de Gales': '🏴\U000E0067\U000E0062\U000E0077\U000E006C\U000E0073\U000E007F',
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


# ============================================
# ESCUDOS DOS CLUBES
# ============================================
CLUB_LOGOS = {
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
    'Criciúma': 'https://logodetimes.com/times/criciuma/logo-criciuma-256.png',
    'Amazonas': 'https://logodetimes.com/times/amazonas-fc/logo-amazonas-fc-256.png',
    'América Mineiro': 'https://logodetimes.com/times/america-mineiro/logo-america-mineiro-256.png',
    'Avaí': 'https://logodetimes.com/times/avai/logo-avai-256.png',
    'Botafogo SP': 'https://logodetimes.com/times/botafogo-sp/logo-botafogo-sp-256.png',
    'Botafogo-SP': 'https://logodetimes.com/times/botafogo-sp/logo-botafogo-sp-256.png',
    'Ceará': 'https://logodetimes.com/times/ceara/logo-ceara-256.png',
    'Chapecoense': 'https://logodetimes.com/times/chapecoense/logo-chapecoense-256.png',
    'CRB': 'https://logodetimes.com/times/crb/logo-crb-256.png',
    'Coritiba': 'https://logodetimes.com/times/coritiba/logo-coritiba-256.png',
    'Goiás': 'https://logodetimes.com/times/goias/logo-goias-256.png',
    'Mirassol': 'https://logodetimes.com/times/mirassol/logo-mirassol-256.png',
    'Novorizontino': 'https://logodetimes.com/times/novorizontino/logo-novorizontino-256.png',
    'Grêmio Novorizontino': 'https://logodetimes.com/times/novorizontino/logo-novorizontino-256.png',
    'Operário PR': 'https://logodetimes.com/times/operario-pr/logo-operario-pr-256.png',
    'Paysandu': 'https://logodetimes.com/times/paysandu/logo-paysandu-256.png',
    'Sport': 'https://logodetimes.com/times/sport/logo-sport-256.png',
    'Sport Recife': 'https://logodetimes.com/times/sport/logo-sport-256.png',
    'Vila Nova': 'https://logodetimes.com/times/vila-nova/logo-vila-nova-256.png',
    'Volta Redonda': 'https://logodetimes.com/times/volta-redonda/logo-volta-redonda-256.png',
    'Remo': 'https://logodetimes.com/times/remo/logo-remo-256.png',
    'River Plate': 'https://logodetimes.com/times/river-plate/logo-river-plate-256.png',
    'Boca Juniors': 'https://logodetimes.com/times/boca-juniors/logo-boca-juniors-256.png',
    'Racing Club': 'https://logodetimes.com/times/racing/logo-racing-256.png',
    'Peñarol': 'https://logodetimes.com/times/penarol/logo-penarol-256.png',
    'Nacional': 'https://logodetimes.com/times/nacional-uruguai/logo-nacional-uruguai-256.png',
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
    'Bayern': 'https://logodetimes.com/times/bayern-de-munique/logo-bayern-de-munique-256.png',
    'PSG': 'https://logodetimes.com/times/psg/logo-psg-256.png',
    'Paris Saint-Germain': 'https://logodetimes.com/times/psg/logo-psg-256.png',
    'Benfica': 'https://logodetimes.com/times/benfica/logo-benfica-256.png',
    'Porto': 'https://logodetimes.com/times/porto/logo-porto-256.png',
    'Sporting': 'https://logodetimes.com/times/sporting/logo-sporting-256.png',
    'Ajax': 'https://logodetimes.com/times/ajax/logo-ajax-256.png',
    'LA Galaxy': 'https://upload.wikimedia.org/wikipedia/en/thumb/7/70/Los_Angeles_Galaxy_logo.svg/200px-Los_Angeles_Galaxy_logo.svg.png',
    'Inter Miami': 'https://upload.wikimedia.org/wikipedia/en/thumb/8/8e/Inter_Miami_CF_logo.svg/200px-Inter_Miami_CF_logo.svg.png',
}


# ============================================
# LOGOS DE LIGAS
# ============================================
LEAGUE_LOGOS = {
    'Série A': 'https://logodetimes.com/times/campeonato-brasileiro/logo-campeonato-brasileiro-256.png',
    'Serie A': 'https://logodetimes.com/times/campeonato-brasileiro/logo-campeonato-brasileiro-256.png',
    'Série B': 'https://logodetimes.com/times/campeonato-brasileiro/logo-campeonato-brasileiro-256.png',
    'Serie B': 'https://logodetimes.com/times/campeonato-brasileiro/logo-campeonato-brasileiro-256.png',
    'Brasil | 1': 'https://logodetimes.com/times/campeonato-brasileiro/logo-campeonato-brasileiro-256.png',
    'Brasil | 2': 'https://logodetimes.com/times/campeonato-brasileiro/logo-campeonato-brasileiro-256.png',
    'Premier League': 'https://logodetimes.com/times/premier-league/logo-premier-league-256.png',
    'England | 1': 'https://logodetimes.com/times/premier-league/logo-premier-league-256.png',
    'La Liga': 'https://logodetimes.com/times/la-liga/logo-la-liga-256.png',
    'Spain | 1': 'https://logodetimes.com/times/la-liga/logo-la-liga-256.png',
    'Italy | 1': 'https://logodetimes.com/times/serie-a-italia/logo-serie-a-italia-256.png',
    'Bundesliga': 'https://logodetimes.com/times/bundesliga/logo-bundesliga-256.png',
    'Germany | 1': 'https://logodetimes.com/times/bundesliga/logo-bundesliga-256.png',
    'Ligue 1': 'https://logodetimes.com/times/ligue-1/logo-ligue-1-256.png',
    'France | 1': 'https://logodetimes.com/times/ligue-1/logo-ligue-1-256.png',
    'Eredivisie': 'https://logodetimes.com/times/eredivisie/logo-eredivisie-256.png',
    'Netherlands | 1': 'https://logodetimes.com/times/eredivisie/logo-eredivisie-256.png',
    'Liga Portugal': 'https://logodetimes.com/times/liga-portugal/logo-liga-portugal-256.png',
    'Portugal | 1': 'https://logodetimes.com/times/liga-portugal/logo-liga-portugal-256.png',
    'Argentina | 1': 'https://logodetimes.com/times/liga-profissional-argentina/logo-liga-profissional-argentina-256.png',
    'MLS': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/MLS_crest_logo_RGB_gradient.svg/200px-MLS_crest_logo_RGB_gradient.svg.png',
    'USA | 1': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/MLS_crest_logo_RGB_gradient.svg/200px-MLS_crest_logo_RGB_gradient.svg.png',
    'Liga MX': 'https://logodetimes.com/times/liga-mx/logo-liga-mx-256.png',
    'Mexico | 1': 'https://logodetimes.com/times/liga-mx/logo-liga-mx-256.png',
    'Saudi Pro League': 'https://upload.wikimedia.org/wikipedia/en/thumb/b/b7/Saudi_Pro_League_Logo.svg/200px-Saudi_Pro_League_Logo.svg.png',
}


# ============================================
# TIMES DA SÉRIE B 2025
# ============================================
SERIE_B_TEAMS = [
    'Amazonas', 'América Mineiro', 'Athletic Club', 'Athletico Paranaense',
    'Atlético GO', 'Avaí', 'Botafogo SP', 'Chapecoense', 'Coritiba', 'CRB',
    'Criciúma', 'Cuiabá', 'Ferroviária', 'Goiás', 'Grêmio Novorizontino',
    'Operário PR', 'Paysandu', 'Vila Nova', 'Volta Redonda',
]


# ============================================
# WYSCOUT LEAGUE MAP (liga WyScout → chave LEAGUE_TIERS)
# ============================================
WYSCOUT_LEAGUE_MAP = {
    'Brasil | 1': 'Serie A Brasil', 'Brasil | 2': 'Serie B Brasil',
    'Brasil | 3': 'Serie C Brasil', 'Brasil | 4': 'Serie D Brasil',
    'Série A': 'Serie A Brasil', 'Serie A': 'Serie A Brasil',
    'Série B': 'Serie B Brasil', 'Serie B': 'Serie B Brasil',
    'Brasileirão': 'Serie A Brasil',
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
    'Portugal | 1': 'Liga Portugal', 'Liga Portugal': 'Liga Portugal',
    'Primeira Liga': 'Liga Portugal', 'Portugal | 2': 'Liga Portugal 2',
    'Netherlands | 1': 'Eredivisie', 'Holanda | 1': 'Eredivisie',
    'Eredivisie': 'Eredivisie',
    'Belgium | 1': 'Belgian Pro League', 'Bélgica | 1': 'Belgian Pro League',
    'Turkey | 1': 'Super Lig', 'Turquia | 1': 'Super Lig',
    'Scotland | 1': 'Scottish Premiership',
    'Russia | 1': 'Russian Premier League',
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
    'Argentina | 1': 'Liga Argentina', 'Liga Profesional': 'Liga Argentina',
    'Argentina | 2': 'Liga Argentina B',
    'USA | 1': 'MLS', 'MLS': 'MLS',
    'Mexico | 1': 'Liga MX', 'Liga MX': 'Liga MX',
    'Colombia | 1': 'Liga Colombia', 'Chile | 1': 'Liga Chile',
    'Uruguay | 1': 'Liga Uruguai', 'Peru | 1': 'Liga Peru',
    'Ecuador | 1': 'Liga Equador', 'Paraguay | 1': 'Liga Paraguai',
    'Bolivia | 1': 'Liga Bolivia', 'Venezuela | 1': 'Liga Venezuela',
    'Japan | 1': 'J1 League', 'Japão | 1': 'J1 League', 'Japan | 2': 'J2 League',
    'Korea | 1': 'K-League 1', 'Coreia | 1': 'K-League 1', 'K League 1': 'K-League 1',
    'Saudi Arabia | 1': 'Saudi Pro League', 'Arábia Saudita | 1': 'Saudi Pro League',
    'Qatar | 1': 'Qatar Stars League', 'UAE | 1': 'UAE Pro League',
    'China | 1': 'Chinese Super League', 'India | 1': 'Indian Super League',
    'Egypt | 1': 'Egyptian Premier League', 'South Africa | 1': 'South African Premier',
    'Morocco | 1': 'Moroccan Botola', 'Tunisia | 1': 'Tunisian Ligue 1',
    'Australia | 1': 'A-League',
    'Paulista A1': 'Paulista A1', 'Paulista A2': 'Paulista A2', 'Paulista A3': 'Paulista A3',
    'Carioca A1': 'Carioca A1', 'Gaúcho A1': 'Gaucho A1', 'Gaucho A1': 'Gaucho A1',
    'Mineiro A1': 'Mineiro A1', 'Paranaense A1': 'Paranaense A1',
    'Cearense A1': 'Cearense A1', 'Pernambucano A1': 'Pernambucano A1',
    'Baiano A1': 'Baiano A1',
    'Copa do Brasil': 'Copa do Brasil', 'Copa do Nordeste': 'Copa do Nordeste',
    'Copa Libertadores': 'Copa Libertadores', 'Copa Sudamericana': 'Copa Sudamericana',
}

_WYSCOUT_LEAGUE_MAP_NORM = {
    padronizar_string(k): v for k, v in WYSCOUT_LEAGUE_MAP.items()
}


# ============================================
# CLUB → LEAGUE MAP (~500 clubes, 40+ ligas)
# ============================================
CLUB_LEAGUE_MAP = {}

for team in SERIE_B_TEAMS:
    CLUB_LEAGUE_MAP[team] = 'Serie B Brasil'

for t in [
    'Atlético MG', 'Atlético Mineiro', 'Athletico Paranaense', 'Athletico PR',
    'Bahia', 'Botafogo', 'Corinthians', 'Cruzeiro', 'Cuiabá',
    'Flamengo', 'Fluminense', 'Fortaleza', 'Grêmio', 'Internacional',
    'Juventude', 'Palmeiras', 'RB Bragantino', 'Red Bull Bragantino',
    'Santos', 'São Paulo', 'Vasco', 'Vasco da Gama', 'Vitória',
    'Sport', 'Sport Recife', 'Ceará', 'Mirassol', 'Novorizontino',
    'Grêmio Novorizontino', 'Atlético GO', 'Atlético Goianiense', 'Criciúma',
]:
    CLUB_LEAGUE_MAP[t] = 'Serie A Brasil'

for t in [
    'Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton',
    'Chelsea', 'Crystal Palace', 'Everton FC', 'Fulham', 'Ipswich',
    'Leicester', 'Liverpool', 'Manchester City', 'Manchester United',
    'Newcastle', 'Newcastle United', 'Nottingham Forest', 'Southampton',
    'Tottenham', 'West Ham', 'Wolverhampton', 'Wolves',
]:
    CLUB_LEAGUE_MAP[t] = 'Premier League'

for t in [
    'Barcelona', 'Real Madrid', 'Atlético Madrid', 'Atlético de Madrid',
    'Real Betis', 'Sevilla', 'Valencia', 'Villarreal', 'Real Sociedad',
    'Athletic Bilbao', 'Celta de Vigo', 'Espanyol', 'Getafe', 'Girona',
    'Las Palmas', 'Mallorca', 'Osasuna', 'Rayo Vallecano', 'Alavés', 'Leganés',
]:
    CLUB_LEAGUE_MAP[t] = 'La Liga'

for t in [
    'Atalanta', 'Bologna', 'Fiorentina', 'Genoa', 'Inter', 'Internazionale',
    'Juventus', 'Lazio', 'Lecce', 'Milan', 'AC Milan', 'Monza', 'Napoli',
    'Parma', 'Roma', 'AS Roma', 'Torino', 'Udinese', 'Venezia', 'Cagliari',
    'Como', 'Empoli', 'Hellas Verona', 'Salernitana', 'Sassuolo',
]:
    CLUB_LEAGUE_MAP[t] = 'Serie A Italia'

for t in [
    'Bayer Leverkusen', 'Bayern', 'Bayern Munich', 'Borussia Dortmund',
    'Dortmund', 'RB Leipzig', 'Leipzig', 'Eintracht Frankfurt', 'Frankfurt',
    'Wolfsburg', 'Freiburg', 'Union Berlin', 'Stuttgart', 'Hoffenheim',
    'Augsburg', 'Mainz', 'Werder Bremen', 'Borussia Mönchengladbach',
    'Holstein Kiel', 'St. Pauli',
]:
    CLUB_LEAGUE_MAP[t] = 'Bundesliga'

for t in [
    'PSG', 'Paris Saint-Germain', 'Marseille', 'Lyon', 'Monaco', 'AS Monaco',
    'Lille', 'Nice', 'Lens', 'Rennes', 'Strasbourg', 'Toulouse',
    'Nantes', 'Montpellier', 'Brest', 'Reims', 'Le Havre', 'Auxerre',
    'Angers', 'Saint-Étienne',
]:
    CLUB_LEAGUE_MAP[t] = 'Ligue 1'

for t in [
    'Benfica', 'Porto', 'FC Porto', 'Sporting', 'Sporting CP', 'Braga',
    'SC Braga', 'Vitória Guimarães', 'Boavista', 'Famalicão', 'Gil Vicente',
    'Moreirense', 'Santa Clara', 'Rio Ave', 'Estoril', 'Arouca', 'Casa Pia',
    'Estrela Amadora',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Portugal')

for t in [
    'Ajax', 'Feyenoord', 'PSV', 'PSV Eindhoven', 'AZ', 'AZ Alkmaar',
    'FC Twente', 'Twente', 'FC Utrecht', 'Go Ahead Eagles',
    'Heerenveen', 'NEC', 'PEC Zwolle', 'Sparta Rotterdam',
    'Fortuna Sittard', 'Groningen', 'Heracles', 'Willem II',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Eredivisie')

for t in [
    'Galatasaray', 'Fenerbahçe', 'Fenerbahce', 'Beşiktaş', 'Besiktas',
    'Trabzonspor', 'Başakşehir', 'Adana Demirspor', 'Alanyaspor',
    'Antalyaspor', 'Kasımpaşa', 'Kayserispor', 'Konyaspor', 'Samsunspor',
]:
    CLUB_LEAGUE_MAP[t] = 'Super Lig'

for t in [
    'River Plate', 'Boca Juniors', 'Racing Club', 'Racing', 'Independiente',
    'San Lorenzo', 'Vélez Sarsfield', 'Lanús', 'Estudiantes',
    'Defensa y Justicia', 'Argentinos Juniors', 'Tigre', 'Huracán',
    'Banfield', 'Talleres', 'Godoy Cruz', 'Belgrano', 'Rosario Central',
    'Platense', 'Instituto', 'Sarmiento', 'Barracas Central',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Argentina')

for t in [
    'Colo-Colo', 'Colo Colo', 'Universidad de Chile', 'U. de Chile',
    'Universidad Católica', 'Unión Española', 'Cobreloa',
    'Huachipato', 'Cobresal', 'Palestino', 'Everton', 'Everton de Viña del Mar',
    'Everton de Viña', 'Everton Chile', "O'Higgins", 'Audax Italiano',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Chile')

for t in [
    'Peñarol', 'Defensor Sporting', 'Danubio', 'Liverpool Montevideo',
    'Wanderers', 'Plaza Colonia', 'Cerro Largo', 'Boston River', 'Fénix',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Uruguai')

for t in [
    'Atlético Nacional', 'Millonarios', 'Millonarios FC', 'Junior', 'Junior FC', 'Junior Barranquilla',
    'Junior de Barranquilla', 'América de Cali', 'Santa Fe', 'Independiente Santa Fe',
    'Deportivo Cali', 'Deportes Tolima', 'Tolima',
    'Once Caldas', 'Bucaramanga', 'Atlético Bucaramanga',
    'Medellin', 'Medellín', 'Independiente Medellín', 'Independiente Medellin', 'DIM',
    'Deportivo Pasto', 'Deportivo Pereira', 'Envigado', 'Boyacá Chicó',
    'Águilas Doradas', 'Aguilas Doradas', 'Jaguares de Córdoba', 'Jaguares', 'Patriotas',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Colombia')

for t in [
    'América', 'Club América', 'Cruz Azul', 'Monterrey', 'Tigres',
    'Tigres UANL', 'Pachuca', 'Pumas UNAM', 'Toluca', 'Santos Laguna',
    'León', 'Guadalajara', 'Chivas', 'Necaxa', 'Puebla',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga MX')

for t in [
    'Atlanta United', 'Austin FC', 'Charlotte FC', 'FC Cincinnati',
    'Columbus Crew', 'Inter Miami', 'LA Galaxy', 'LAFC',
    'Nashville SC', 'New York City FC', 'NY Red Bulls', 'Orlando City',
    'Philadelphia Union', 'Portland Timbers', 'Seattle Sounders',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'MLS')

for t in [
    'Al Hilal', 'Al-Hilal', 'Al Nassr', 'Al-Nassr', 'Al Ahli', 'Al-Ahli',
    'Al Ittihad', 'Al-Ittihad', 'Al Shabab', 'Al Fateh', 'Al Fayha',
    'Al Taawoun', 'Al Ettifaq', 'Damac',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Saudi Pro League')

for t in [
    'Vissel Kobe', 'Yokohama F. Marinos', 'Kawasaki Frontale',
    'Kashima Antlers', 'Urawa', 'Urawa Reds', 'FC Tokyo',
    'Cerezo Osaka', 'Gamba Osaka', 'Nagoya Grampus',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'J1 League')

for t in [
    'Jeonbuk', 'Jeonbuk Hyundai', 'Ulsan', 'Ulsan HD', 'FC Seoul',
    'Pohang Steelers', 'Gangwon', 'Gangwon FC', 'Daegu FC', 'Incheon United',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'K-League 1')

for t in ['Celtic', 'Rangers', 'Aberdeen', 'Hearts', 'Hibernian']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Scottish Premiership')

for t in [
    'Anderlecht', 'Club Brugge', 'Gent', 'Genk', 'Standard Liège',
    'Antwerp', 'Union Saint-Gilloise', 'Mechelen', 'Charleroi',
]:
    CLUB_LEAGUE_MAP[t] = 'Belgian Pro League'

for t in [
    'Alianza Lima', 'Universitario', 'Sporting Cristal', 'Melgar',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Peru')

for t in [
    'Barcelona SC', 'LDU Quito', 'Emelec', 'Independiente del Valle',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Equador')

for t in ['Olimpia', 'Cerro Porteño', 'Libertad', 'Guaraní']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Paraguai')

for t in ['Bolívar', 'The Strongest', 'Jorge Wilstermann', 'Always Ready']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Bolivia')

for t in ['Caracas FC', 'Deportivo Táchira', 'Zamora FC', 'Monagas SC']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Venezuela')

# Dicionário normalizado para lookup O(1)
_CLUB_LEAGUE_MAP_NORM = {
    padronizar_string(k): v for k, v in CLUB_LEAGUE_MAP.items()
}


# ============================================
# MAPEAMENTO DE POSIÇÕES
# ============================================
POSICAO_MAP = {
    'Atacante': 'Atacante', 'Extremo': 'Extremo', 'Meia': 'Meia',
    'Volante': 'Volante', 'Lateral direito': 'Lateral', 'Lateral esquerdo': 'Lateral',
    'Zagueiro': 'Zagueiro', 'Goleiro': 'Goleiro',
    'CF': 'Atacante', 'SS': 'Atacante',
    'LW': 'Extremo', 'RW': 'Extremo', 'LWF': 'Extremo', 'RWF': 'Extremo',
    'LAMF': 'Extremo', 'RAMF': 'Extremo',
    'AMF': 'Meia', 'LCMF': 'Meia', 'RCMF': 'Meia', 'CMF': 'Meia',
    'DMF': 'Volante', 'LDMF': 'Volante', 'RDMF': 'Volante',
    'LB': 'Lateral', 'RB': 'Lateral', 'LWB': 'Lateral', 'RWB': 'Lateral',
    'LB5': 'Lateral', 'RB5': 'Lateral',
    'CB': 'Zagueiro', 'LCB': 'Zagueiro', 'RCB': 'Zagueiro',
    'LCB3': 'Zagueiro', 'RCB3': 'Zagueiro', 'CCB3': 'Zagueiro',
    'GK': 'Goleiro',
}

POSICOES_DISPLAY = [
    'Atacante', 'Extremo', 'Meia', 'Volante',
    'Lateral direito', 'Lateral esquerdo', 'Zagueiro', 'Goleiro',
]

POSICAO_ALIAS = {
    'centroavante': 'Atacante', 'atacante': 'Atacante', 'ponta de lança': 'Atacante',
    'ponta': 'Extremo', 'extremo': 'Extremo', 'ala': 'Extremo',
    'meia': 'Meia', 'meio-campista': 'Meia', 'meia ofensivo': 'Meia', 'armador': 'Meia',
    'volante': 'Volante', 'primeiro volante': 'Volante',
    'lateral': 'Lateral', 'lateral-direito': 'Lateral', 'lateral-esquerdo': 'Lateral',
    'zagueiro': 'Zagueiro', 'defensor central': 'Zagueiro',
    'goleiro': 'Goleiro', 'guarda-redes': 'Goleiro',
}


# ============================================
# ÍNDICES COMPOSTOS POR POSIÇÃO
# ============================================
INDICES_CONFIG = {
    'Atacante': {
        'Finalização': [
            'Golos/90', 'Golos esperados/90', 'Golos sem ser por penálti/90',
            'Remates/90', 'Remates à baliza, %', 'Golos marcados, %',
            'Toques na área/90', 'Golos de cabeça/90',
        ],
        '1x1 Ofensivo': [
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %',
            'Acelerações/90', 'Faltas sofridas/90',
        ],
        'Jogo Aéreo': [
            'Duelos aérios/90', 'Duelos aéreos ganhos, %',
            'Golos de cabeça/90', 'Cruzamentos em profundidade recebidos/90',
        ],
        'Movimentação': [
            'Corridas progressivas/90', 'Receção de passes em profundidade/90',
            'Acelerações/90', 'Passes longos recebidos/90', 'Toques na área/90',
        ],
        'Link-up Play': [
            'Passes recebidos/90', 'Passes/90', 'Passes certos, %',
            'Assistências/90', 'Assistências esperadas/90',
            'Segundas assistências/90', 'Passes chave/90',
        ],
        'Pressing': [
            'Ações defensivas com êxito/90', 'Duelos/90', 'Duelos ganhos, %',
            'Interseções/90',
        ],
    },
    'Extremo': {
        'Finalização': [
            'Golos/90', 'Golos esperados/90', 'Remates/90',
            'Remates à baliza, %', 'Toques na área/90', 'Golos marcados, %',
        ],
        'Criação': [
            'Assistências/90', 'Assistências esperadas/90',
            'Passes chave/90', 'Passes inteligentes/90',
            'Segundas assistências/90', 'Terceiras assistências/90',
            'Passes para a área de penálti/90',
        ],
        '1x1 Ofensivo': [
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %',
            'Faltas sofridas/90', 'Acelerações/90',
        ],
        'Progressão': [
            'Corridas progressivas/90', 'Passes progressivos/90',
            'Passes progressivos certos, %', 'Acelerações/90',
            'Passes para terço final/90', 'Passes certos para terço final, %',
        ],
        'Cruzamentos': [
            'Cruzamentos/90', 'Cruzamentos certos, %',
            'Cruzamentos para a área de baliza/90',
            'Cruzamentos do flanco esquerdo/90', 'Cruzamentos precisos do flanco esquerdo, %',
            'Cruzamentos do flanco direito/90', 'Cruzamentos precisos do flanco direito, %',
        ],
        'Trabalho Defensivo': [
            'Ações defensivas com êxito/90', 'Duelos defensivos/90',
            'Duelos defensivos ganhos, %', 'Interseções/90',
        ],
    },
    'Meia': {
        'Criação': [
            'Assistências/90', 'Assistências esperadas/90',
            'Passes chave/90', 'Passes inteligentes/90', 'Passes inteligentes certos, %',
            'Segundas assistências/90', 'Terceiras assistências/90',
            'Passes para a área de penálti/90', 'Passes precisos para a área de penálti, %',
        ],
        'Progressão': [
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Corridas progressivas/90', 'Passes para terço final/90',
            'Passes certos para terço final, %', 'Passes em profundidade/90',
            'Passes em profundidade certos, %',
        ],
        'Qualidade de Passe': [
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
            'Passes para a frente/90', 'Passes para a frente certos, %',
            'Comprimento médio de passes, m',
        ],
        'Finalização': [
            'Golos/90', 'Golos esperados/90', 'Remates/90',
            'Remates à baliza, %', 'Toques na área/90',
        ],
        'Duelos': [
            'Duelos/90', 'Duelos ganhos, %',
            'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %',
            'Dribles/90', 'Dribles com sucesso, %',
        ],
        'Recuperação': [
            'Ações defensivas com êxito/90', 'Duelos defensivos/90',
            'Duelos defensivos ganhos, %', 'Interseções/90', 'Cortes/90',
        ],
    },
    'Volante': {
        'Recuperação': [
            'Ações defensivas com êxito/90', 'Interseções/90',
            'Interceções ajust. à posse', 'Duelos defensivos/90',
            'Duelos defensivos ganhos, %', 'Cortes/90',
            'Cortes de carrinho ajust. à posse', 'Remates intercetados/90',
        ],
        'Duelos': [
            'Duelos/90', 'Duelos ganhos, %',
            'Duelos aérios/90', 'Duelos aéreos ganhos, %',
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
        ],
        'Construção': [
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
            'Passes para a frente/90', 'Passes para a frente certos, %',
        ],
        'Progressão': [
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terço final/90', 'Passes certos para terço final, %',
            'Corridas progressivas/90', 'Passes em profundidade/90',
        ],
        'Cobertura': [
            'Ações defensivas com êxito/90', 'Interseções/90',
            'Cortes/90', 'Remates intercetados/90',
        ],
        'Disciplina': [
            'Faltas/90', 'Cartões amarelos/90', 'Cartões vermelhos/90',
        ],
    },
    'Lateral': {
        'Apoio Ofensivo': [
            'Cruzamentos/90', 'Cruzamentos certos, %',
            'Cruzamentos para a área de baliza/90',
            'Passes para terço final/90', 'Passes certos para terço final, %',
            'Toques na área/90', 'Passes para a área de penálti/90',
        ],
        'Progressão': [
            'Corridas progressivas/90', 'Passes progressivos/90',
            'Passes progressivos certos, %', 'Acelerações/90',
            'Passes em profundidade/90',
        ],
        '1x1 Ofensivo': [
            'Dribles/90', 'Dribles com sucesso, %',
            'Duelos ofensivos/90', 'Duelos ofensivos ganhos, %',
            'Faltas sofridas/90',
        ],
        'Defesa': [
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Interseções/90', 'Cortes/90',
            'Ações defensivas com êxito/90', 'Remates intercetados/90',
        ],
        'Duelos': [
            'Duelos/90', 'Duelos ganhos, %',
            'Duelos aérios/90', 'Duelos aéreos ganhos, %',
        ],
        'Criação': [
            'Assistências/90', 'Assistências esperadas/90',
            'Passes chave/90', 'Segundas assistências/90',
        ],
    },
    'Zagueiro': {
        'Duelos Defensivos': [
            'Duelos defensivos/90', 'Duelos defensivos ganhos, %',
            'Cortes/90', 'Cortes de carrinho ajust. à posse',
            'Ações defensivas com êxito/90',
        ],
        'Jogo Aéreo': [
            'Duelos aérios/90', 'Duelos aéreos ganhos, %', 'Golos de cabeça/90',
        ],
        'Interceções': [
            'Interseções/90', 'Interceções ajust. à posse',
            'Remates intercetados/90', 'Cortes/90',
        ],
        'Construção': [
            'Passes/90', 'Passes certos, %',
            'Passes longos/90', 'Passes longos certos, %',
            'Passes para a frente/90', 'Passes para a frente certos, %',
            'Comprimento médio de passes longos, m',
        ],
        'Progressão': [
            'Passes progressivos/90', 'Passes progressivos certos, %',
            'Passes para terço final/90', 'Corridas progressivas/90',
            'Passes em profundidade/90',
        ],
        'Disciplina': [
            'Faltas/90', 'Cartões amarelos/90', 'Cartões vermelhos/90',
        ],
    },
    'Goleiro': {
        'Defesas': ['Defesas, %', 'Golos sofridos/90', 'Remates sofridos/90'],
        'xG Prevented': ['Golos sofridos esperados/90', 'Golos expectáveis defendidos por 90´'],
        'Jogo Aéreo': ['Duelos aérios/90.1', 'Saídas/90'],
        'Jogo com Pés': ['Passes para trás recebidos pelo guarda-redes/90', 'Passes longos certos, %'],
        'Clean Sheets': ['Jogos sem sofrer golos'],
    },
}


# ============================================
# ÍNDICES SKILLCORNER
# ============================================
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


# ============================================
# FUNÇÕES DE RESOLUÇÃO DE LIGA
# ============================================

def resolve_league_to_tier(league_name, team_name=None):
    """Resolve nome de liga WyScout para chave do LEAGUE_TIERS."""
    if league_name is None:
        if team_name is None:
            return None
    elif pd.notna(league_name):
        league_str = str(league_name).strip()
        if league_str in WYSCOUT_LEAGUE_MAP:
            return WYSCOUT_LEAGUE_MAP[league_str]
        league_norm = padronizar_string(league_str)
        if league_norm in _WYSCOUT_LEAGUE_MAP_NORM:
            return _WYSCOUT_LEAGUE_MAP_NORM[league_norm]
        for key_norm, val in _WYSCOUT_LEAGUE_MAP_NORM.items():
            if key_norm and (key_norm in league_norm or league_norm in key_norm):
                return val
    if team_name is not None:
        try:
            if pd.notna(team_name):
                team_str = str(team_name).strip()
                if team_str in CLUB_LEAGUE_MAP:
                    return CLUB_LEAGUE_MAP[team_str]
                team_norm = padronizar_string(team_str)
                if team_norm in _CLUB_LEAGUE_MAP_NORM:
                    return _CLUB_LEAGUE_MAP_NORM[team_norm]
        except Exception:
            pass
    return None


def get_posicao_categoria(posicao):
    """Converte posição WyScout para categoria de índices."""
    if pd.isna(posicao):
        return 'Meia'
    posicao_str = str(posicao).strip()
    if posicao_str in INDICES_CONFIG:
        return posicao_str
    return POSICAO_MAP.get(posicao_str, 'Meia')


def is_serie_b_team(team_name):
    """Verifica se o time é da Série B 2025."""
    if pd.isna(team_name):
        return False
    return str(team_name).strip() in SERIE_B_TEAMS
