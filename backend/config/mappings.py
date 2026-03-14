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
    'Amazonas', 'Amazonas FC', 'América Mineiro', 'América MG', 'América-MG',
    'Athletic Club',
    'Avaí', 'Avaí FC', 'Botafogo SP', 'Botafogo-SP',
    'Chapecoense', 'Chapecoense AF', 'Coritiba', 'Coritiba FC', 'CRB',
    'Criciúma', 'Criciúma EC', 'Cuiabá', 'Cuiabá EC',
    'Ferroviária', 'Ferroviária SP', 'Goiás', 'Goiás EC',
    'Grêmio Novorizontino', 'Novorizontino',
    'Operário PR', 'Operário-PR', 'Operário Ferroviário',
    'Paysandu', 'Paysandu SC',
    'Santos', 'Santos FC',
    'Vila Nova', 'Vila Nova FC', 'Volta Redonda', 'Volta Redonda FC',
    # Common alternate names / WyScout variants
]


# ============================================
# ELENCO BOTAFOGO-SP — REFERÊNCIA PARA VALIDAÇÃO DE MODELOS
# ============================================
# Dados usados para calibrar e validar MarketValueModel e TrajectoryModel.
# Jogadores da Serie B devem produzir valores realistas (€0.03M-€1.5M).
BOTAFOGO_SP_SQUAD = {
    # nome_display: (posicao, ano_nasc, nome_completo)
    'Victor Souza': ('Goleiro', 1992, 'Victor Bernardes Andrade e Souza'),
    'Adriano': ('Goleiro', 2006, 'Adriano Vasconcelos da Silva Júnior'),
    'Brenno Klippel': ('Goleiro', 2003, 'Brenno Faro Klippel'),
    'Jordan Esteves': ('Goleiro', 1998, 'Jordan Esteves da Costa Daniel'),
    'Ericson': ('Zagueiro', 1999, 'Ericson da Silva'),
    'Gustavo Vilar': ('Zagueiro', 2000, 'Gustavo Vilar dos Santos'),
    'Carlos Eduardo': ('Zagueiro', 2001, 'Carlos Eduardo da Silva Santos'),
    'Wallace Fortuna': ('Zagueiro', 1994, 'Wallace Fortuna dos Santos'),
    'Guilherme Mariano': ('Zagueiro', 1999, 'Guilherme Mariano Barbosa'),
    'Darlan Batista': ('Zagueiro', 2004, 'Darlan Batista Cobo da Silva'),
    'Hebert Badaró': ('Zagueiro', 2005, 'Hebert William Badaró Oliveira'),
    'Jonathan Lemos': ('Lateral Direito', 1992, 'Jonathan Francisco Lemos'),
    'Gabriel Inocêncio': ('Lateral Direito', 1994, 'Gabriel de Souza Inocêncio'),
    'Pedrinho': ('Lateral Direito', 2006, 'Pedro Henrique Souza do Nascimento'),
    'Patrick Brey': ('Lateral Esquerdo', 1997, 'Patrick de Carvalho Brey'),
    'Felipe Vieira': ('Lateral Esquerdo', 1999, 'Felipe Vieira Augusto'),
    'Henrique Teles': ('Lateral Esquerdo', 2006, 'Henrique Lôvo Teles'),
    'Leandro Maciel': ('Volante', 1995, 'Leandro Isaac Maciel'),
    'Everton Morelli': ('Volante', 1997, 'Everton Morelli Casimiro'),
    'Matheus Sales': ('Volante', 1995, 'Matheus de Sales Cabral'),
    'Thiaguinho': ('Volante', 1998, 'Thiago Henrique Moraes'),
    'Pedro Tortello': ('Volante', 2004, 'Pedro Henrique Tortello'),
    'Yuri Felipe': ('Volante', 2006, 'Yuri Felipe Santos da Conceição'),
    'Érik': ('Volante', 2005, 'Erik Rebello de Castro'),
    'Rafael Gava': ('Meia', 1993, 'Rafael Gustavo Meneghel Gava'),
    'Marquinho': ('Meia', None, 'Marquinho'),
    'Felipe Penha': ('Meia', 2006, 'Felipe Penha de Souza'),
    'Thalles': ('Meia', 2005, 'Thalles Eduardo Gomes Ferreira dos Ramos'),
    'Kelvin Giacobe': ('Extremo', 1997, 'Kelvin Giacobe'),
    'Jéfferson Nem': ('Extremo', 1996, 'Jefferson Vasconcelos Braz da Silva'),
    'Márcio Maranhão': ('Extremo', 1999, 'Márcio Carlos Pestana Dutra'),
    'Wesley Pinheiro': ('Extremo', 2000, 'Wesley Pinheiro Santos'),
    'Zé Hugo': ('Extremo', 1999, 'José Hugo Sousa dos Santos'),
    'Whalacy Ermeliano': ('Extremo', 2006, 'Whalacy Wilhan Gonçalves Ermeliano'),
    'Hygor Cléber': ('Atacante', 1992, 'Hygor Cléber Garcia Silva'),
    'Guilherme Queiróz': ('Atacante', 1990, 'Guilherme de Queiróz Gonçalves'),
    'Luizão': ('Atacante', 2003, 'Luiz Guilherme Vieira da Silva'),
}


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
    ' | 1': 'n Premier League',
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
    # Additional leagues found in scouting data
    'Brasil | 4': 'Serie D Brasil', 'Brasil | 5': 'Serie D Brasil',
    'Grecia | 1': 'Greek Super League', 'Greece | 2': 'Greek Super League 2',
    'Bosnia | 1': 'Bosnian Premier League', 'Bósnia | 1': 'Bosnian Premier League',
    'Slovenia | 1': 'Slovenian PrvaLiga', 'Eslovênia | 1': 'Slovenian PrvaLiga',
    'Slovakia | 1': 'Slovak Super Liga', 'Eslováquia | 1': 'Slovak Super Liga',
    'Moldova | 1': 'Moldovan National Division',
    'Montenegro | 1': 'Montenegrin First League',
    'Azerbaijan | 1': 'Azerbaijan Premier League', 'Azerbaijão | 1': 'Azerbaijan Premier League',
    'Portugal | 3': 'Liga Portugal 3',
    'Spain | 3': 'La Liga 3', 'Espanha | 3': 'La Liga 3',
    'Turkey | 2': 'Super Lig 2', 'Turquia | 2': 'Super Lig 2',
    'Switzerland | 2': 'Swiss Challenge League', 'Suíça | 2': 'Swiss Challenge League',
    'Belgium | 2': 'Belgian Second Division', 'Bélgica | 2': 'Belgian Second Division',
    'Saudi Arabia | 2': 'Saudi First Division',
    'Malaysia | 1': 'Malaysian Super League', 'Malásia | 1': 'Malaysian Super League',
    'Indonesia | 1': 'Indonesian Liga 1', 'Indonésia | 1': 'Indonesian Liga 1',
    'Uzbekistan | 1': 'Uzbek Super League',
    'Thailand | 1': 'Thai League', 'Tailândia | 1': 'Thai League',
    'Coreia | 2': 'K-League 2', 'Korea | 2': 'K-League 2',
    'Emirados | 1': 'UAE Pro League',
    'Chipre | 1': 'Cypriot First Division',
    'Romenia | 1': 'Romanian Liga I', 'Romênia | 1': 'Romanian Liga I',
    'Bulgária | 1': 'Bulgarian First League',
    'Polônia | 1': 'Polish Ekstraklasa', 'Polonia | 1': 'Polish Ekstraklasa',
    'Sérvia | 1': 'Serbian Super Liga',
    'Dinamarca | 1': 'Danish Superliga',
    'Alemanha | 2': '2. Bundesliga',
    'Espanha | 2': 'La Liga 2',
    'Itália | 2': 'Serie B Italia', 'Italy | 2': 'Serie B Italia', 'Italia | 2': 'Serie B Italia',
    'Itália | 3': 'Serie C Italia', 'Italia | 3': 'Serie C Italia',
    'Argentina | 2': 'Liga Argentina B',
    'Japão | 2': 'J2 League',
    'Israel | 1': 'Israeli Premier League',
    # New leagues from power ranking data
    'Hungary | 1': 'Hungarian NB I', 'Hungria | 1': 'Hungarian NB I',
    'Albania | 1': 'Albanian Superiore', 'Albânia | 1': 'Albanian Superiore',
    'Armenia | 1': 'Armenian Premier League', 'Armênia | 1': 'Armenian Premier League',
    'Austria | 2': 'Austrian 2. Liga', 'Áustria | 2': 'Austrian 2. Liga',
    'Romania | 2': 'Romanian Liga II', 'Romênia | 2': 'Romanian Liga II',
    'Colombia | 2': 'Liga Colombia B', 'Colômbia | 2': 'Liga Colombia B',
    'Chile | 2': 'Liga Chile B',
    'Uruguay | 2': 'Liga Uruguai B', 'Uruguai | 2': 'Liga Uruguai B',
    'Paraguay | 2': 'Liga Paraguai B', 'Paraguai | 2': 'Liga Paraguai B',
    'UAE | 2': 'UAE First Division', 'Emirados | 2': 'UAE First Division',
    'Kuwait | 1': 'Kuwaiti Premier League',
    'Bangladesh | 1': 'Bangladesh Premier League',
    'Guatemala | 1': 'Liga Nacional Guatemala',
    'Italy | 3': 'Serie C Italia',
    'Catarinense A1': 'Catarinense A1',
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
    'Atlético MG', 'Atlético Mineiro', 'Atlético-MG', 'Clube Atlético Mineiro',
    'Athletico Paranaense', 'Athletico PR', 'Athletico-PR', 'CAP',
    'Bahia', 'EC Bahia', 'Esporte Clube Bahia',
    'Botafogo', 'Botafogo FR', 'Botafogo RJ', 'Botafogo de Futebol e Regatas',
    'Chapecoense',     
    'Corinthians', 'SC Corinthians', 'SC Corinthians Paulista',
    'Cruzeiro', 'Cruzeiro EC', 'Cruzeiro Esporte Clube',
    'Flamengo', 'CR Flamengo', 'Clube de Regatas do Flamengo',
    'Fluminense', 'Fluminense FC',
    'Grêmio', 'Grêmio FBPA', 'Grêmio Porto Alegre',
    'Internacional', 'SC Internacional', 'Inter RS',
    'Palmeiras', 'SE Palmeiras',
    'RB Bragantino', 'Red Bull Bragantino', 'Bragantino',
    'Remo', 'Clube do Remo',
    'Santos', 'Santos FC',
    'São Paulo', 'São Paulo FC', 'SPFC',
    'Vasco', 'Vasco da Gama', 'CR Vasco da Gama',
    'Vitória', 'EC Vitória', 'Vitória BA',
    'Mirassol', 'Mirassol FC',
]:
    CLUB_LEAGUE_MAP[t] = 'Serie A Brasil'

for t in [
    'Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton',
    'Chelsea', 'Crystal Palace', 'Everton FC', 'Fulham', 'Ipswich',
    'Leicester', 'Liverpool FC', 'Manchester City', 'Manchester United',
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
    'Bayer Leverkusen', 'Bayern', 'Bayern Munich', 'Bo Dortmund',
    'Dortmund', 'RB Leipzig', 'Leipzig', 'Eintracht Frankfurt', 'Frankfurt',
    'Wolfsburg', 'Freiburg', 'Union Berlin', 'Stuttgart', 'Hoffenheim',
    'Augsburg', 'Mainz', 'Werder Bremen', 'Bo Mönchengladbach',
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
    'Atlético Nacional', 'Millonarios', 'Junior', 'Junior Barranquilla',
    'América de Cali', 'Santa Fe', 'Deportivo Cali', 'Deportes Tolima',
    'Once Caldas', 'Bucaramanga',
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

# ── Brazilian Serie B (WyScout alternate names) ──
for t in ['Vila Nova', 'Botafogo-SP', 'America Mineiro', 'America-MG', 'CRB', 'Botafogo SA', 'Operario', 'Atletico-GO',
          'Náutico', 'Club Náutico Capibaribe', 'Cuiabá', 'Cuiabá EC', 'Ponte Preta',
          'Novorizontino', 'Grêmio Novorizontino', 'Atlético GO', 'Atlético Goianiense', 'Atlético-GO', 'Juventude', 'EC Juventude',
          'Criciúma', 'Criciúma EC', 'Fortaleza', 'Fortaleza EC', 'Sport Recife', 'Sport', 'Sport CR']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Serie B Brasil')

# ── Brazilian Serie C ──
for t in [
    'Botafogo PB', 'Botafogo-PB', 'Athletic Club MG',
    'Floresta', 'Floresta EC', 'Ferroviário', 'Ferroviário CE',
    'Figueirense', 'Figueirense FC',
    'Manaus', 'Manaus FC', 'São Bernardo', 'São Bernardo FC', 'Ypiranga', 'Ypiranga RS',
    'Volta Redonda', 'Volta Redonda FC', 
    'Paysandu', 'Paysandu SC',
    'Amazonas', 'Inter de Limeira', 'Santa Cruz', 'Ituano',
    'Ferroviária',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Serie C Brasil')

# ── Brazilian Serie D / lower divisions ──
for t in [
    'AA Maguary', 'Aguia de Marabá', 'Anapolina', 'Azuriz', 'Capivariano',
    'Cianorte', 'Goiatuba', 'Juazeirense', 'Noroeste', 'Portuguesa', 'Aparecidense',
    'Primavera', 'Santa Catarina', 'Santo André', 'Tombense', 'São José', 'São José RS', 'São José EC',
    'Ferroviario', 'ABC', 'São José EC', 'Icasa', 'Jacuipense', 'Altos', 'Altos PI',
    'Imperatriz', 'Imperatriz MA', 'Treze', 'Treze PB',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Serie D Brasil')

# ── Brazilian amateur / 5th division ──
for t in ['Andraus', 'Foz do Iguaçu', 'Osasco Sporting']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Serie D Brasil')

# ── Argentina (additional) ──
for t in [
    'Velez', 'Aldosivi', 'Atletico Tucuman', 'CA Banfield',
    'CA Gimnasia y Esgrima (Mendoza)',
    'Club de Gimnasia y Esgrima La Plata', 'DyJ',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Argentina')

for t in [
    'Arsenal de Sarandi', 'Atlanta', 'Estudiantes de Caseros',
    'Ferro Carril', 'Quilmes', 'San Martin Tucuman', 'Tristan Suarez',
    'Godoy Cruz',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Argentina B')

# ── Portugal (additional) ──
for t in [
    'AFS', 'AVS', 'CD Nacional', 'CF Estrela Amadora',
    'Clube Desportivo Tondela', 'FC Alverca',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Portugal')

for t in [
    'Academico de Viseu', 'Farense', 'Feirense', 'Leixões', 'Maritimo',
    'Paços Ferreira', 'Portimonense SAD', 'Torreense', 'UD Leiria',
    'UD Oliveirense',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Portugal 2')

for t in ['AD Sanjoanense', 'Braga B', 'Mafra']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Portugal 3')

# ── Spain (2nd/3rd division) ──
for t in [
    'Albacete', 'Burgos CF', 'CD Castellón', 'CD Leonesa', 'Ceuta',
    'Cádiz CF', 'Real Valladolid', 'UD Almería',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'La Liga 2')

for t in ['Cartagena']:
    CLUB_LEAGUE_MAP.setdefault(t, 'La Liga 3')

# ── Germany 2. Bundesliga ──
for t in ['Nuremberg', 'Preußen Münster']:
    CLUB_LEAGUE_MAP.setdefault(t, '2. Bundesliga')

# ── Italy lower divisions ──
for t in ['Salernitana Calcio 1919']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Serie B Italia')

# ── Uruguay (additional) ──
for t in [
    'CA Juventud', 'Central Español', 'Danubio FC',
    'Deportivo Maldonado', 'Racing Club de Montevideo', 'Torque',
    'Liverpool',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Uruguai')

# ── Chile (additional) ──
for t in ['CF Universidad de Chile', 'Coquimbo Unido', 'La Serena']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Chile')

# ── Colombia (additional) ──
for t in ['Fortaleza CEIFC']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Colombia')

# ── Venezuela (additional) ──
for t in ['UCV']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Venezuela')

# ── Turkey (additional) ──
for t in ['Fatih Karagümrük', 'Kasimpasa', 'Sakaryaspor']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Super Lig')

for t in ['Ankara Keciörengücü', 'Manisa FK']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Super Lig 2')

# ── Greece ──
for t in [
    'AE Larissa', 'APO Levadiakos', 'Asteras Aktor', 'OFI Creta',
    'Panetolikos', 'Panserraikos', 'Panteolikos',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Greek Super League')

# ── Ukraine ──
for t in [
    'FK Oleksandriya', 'Karpaty', 'Polissya', 'Rukh Lviv',
    'Rukh Vynnyky', 'Zorya',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Ukrainian Premier League')

# ── Poland ──
for t in ['Jagiellonia Bialystok', 'Odra Opole', 'Rakow']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Polish Ekstraklasa')

# ── Bulgaria ──
for t in ['Lokomotiv Sofia', 'Ludogorets', 'Spartak Varna', 'Levski Sofia']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Bulgarian First League')

# ── Cyprus ──
for t in [
    'AEL Limassol', 'Apoel', 'Apollon Limassol',
    'Olympiakos Nicosia', 'Omónia Nicósia', 'Pafos', 
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Cypriot First Division')

# ── Romania ──
for t in ['Otelul Galati']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Romanian Liga I')

# ── Israel ──
for t in ['Beitar Jerusalem', 'Kiryat Shmona', 'Hapoel Beer Sheva', 'Maccabi Netanya']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Israeli Premier League')

# ── Switzerland ──
for t in ['FC Zürich']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Swiss Super League')

for t in ['Etoile Carouge']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Swiss Challenge League')

# ── Denmark ──
for t in ['Midtjylland']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Danish Superliga')

# ── Belgium 2nd division ──
for t in ['RWDM Brussels']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Belgian Second Division')

# ── Austria ──
for t in ['FC Blau-Weiss Linz']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Austrian Bundesliga')

# ── Serbia ──
for t in ['FK Spartak Subotica']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Serbian Super Liga')

# ── Bosnia ──
for t in ['FK Sarajevo', 'Željezničar', 'Levadia']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Bosnian Premier League')

# ── Slovenia ──
for t in ['NK Olimpija']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Slovenian PrvaLiga')

# ── Slovakia ──
for t in ['Dunaiská Streda']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Slovak Super Liga')

# ── Moldova ──
for t in ['Sheriff']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Moldovan National Division')

# ── Montenegro ──
for t in ['FK Bokelj']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Montenegrin First League')

# ── Azerbaijan ──
for t in ['Araz-Nakhchivan', 'Imisli FK', 'Sabah FK', 'Zira FK', 'Qarabag']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Azerbaijan Premier League')

# ── Korea (additional) ──
for t in ['Bucheon FC', 'Suwon Bluewigs', 'Jeju SK', 'Gimpo Citizen', 'Seoul E-Land', 'Seoul', 'Jeonnam Dragons']:
    CLUB_LEAGUE_MAP.setdefault(t, 'K-League 1')

# ── Japan (2nd division) ──
for t in ['FC Imabari', 'RB Omiya Ardija', 'Sagan Tosu']:
    CLUB_LEAGUE_MAP.setdefault(t, 'J2 League')

# ── Saudi Arabia 2nd ──
for t in ['Al-Faisaly']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Saudi First Division')

# ── UAE ──
for t in [
    'Al-Hamriyah', 'Dibba SC', 'FC Baniyas', 'Kalba FC',
    'Khor Fakkan SSC', 'Shabab Al-Ahli Club', 'Shabab Al Ahli Dubai']:
    CLUB_LEAGUE_MAP.setdefault(t, 'UAE Pro League')

# ── USA (additional) ──
for t in ['Atlanta United FC', 'St. Louis CITY SC', 'Dallas', 'Cincinnati']:
    CLUB_LEAGUE_MAP.setdefault(t, 'MLS')

# ── Australia / New Zealand ──
for t in ['Auckland FC']:
    CLUB_LEAGUE_MAP.setdefault(t, 'A-League')

# ── Tunisia ──
for t in ['Esperance Tunis']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Tunisian Ligue 1')

# ── Morocco ──
for t in ['Olympique Safi']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Moroccan Botola')

# ── Malaysia / Thailand / Indonesia ──
for t in ['Selangor FC', 'Lion City Sallors FC']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Malaysian Super League')

for t in ['Johor', 'Port FC', 'Uthai Thani FC']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Thai League')

for t in ['Persija']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Indonesian Liga 1')

# ── India ──
for t in ['East Bengal FC']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Indian Super League')

# ── Uzbekistan ──
for t in ['Pakhtakor Tashkent']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Uzbek Super League')

# ============================================================
# CLUBS FROM POWER RANKING DATABASE (calibrated data)
# ============================================================

# ── Premier League (England) ──
for t in ['Aston Villa', 'Chelsea']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Premier League')

# ── La Liga / Spain ──
for t in ['Barcelona']:
    CLUB_LEAGUE_MAP.setdefault(t, 'La Liga')
for t in ['Albacete', 'Cádiz', 'Cartagena']:
    CLUB_LEAGUE_MAP.setdefault(t, 'La Liga 2')
for t in ['Antequera', 'Cultural Leonesa']:
    CLUB_LEAGUE_MAP.setdefault(t, 'La Liga 3')

# ── Serie A/B Italia ──
for t in ['Cagliari']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Serie A Italia')
for t in ['Catanzaro']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Serie B Italia')

# ── 2. Bundesliga ──
for t in ['Elversberg']:
    CLUB_LEAGUE_MAP.setdefault(t, '2. Bundesliga')

# ── Liga Portugal ──
for t in ['Casa Pia AC', 'Estrela Amadora', 'Famalicão', 'Farense']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Portugal')
for t in [
    'Académico de Viseu F.C.', 'Alverca', 'Chaves',
    'Felgueiras 1932',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Portugal 2')
for t in ['Académica', 'Amarante', 'Amora', 'Anadia', 'Atlético CP']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Portugal 3')
for t in ['AD Marco 09']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Campeonato de Portugal')

# ── Eredivisie ──
for t in ['AZ', 'Fortuna Sittard']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Eredivisie')

# ── Belgium ──
for t in ['Cercle Brugge']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Belgian Pro League')
for t in ['Francs Borains']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Belgian Second Division')

# ── Super Lig / 1. Lig Turkey ──
for t in ['Eyüpspor', 'Fenerbahçe']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Super Lig')
for t in ['BB Erzurumspor', 'Bandırmaspor']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Super Lig 2')

# ── Scotland ──
for t in ['Celtic', 'Rangers']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Scottish Premiership')

# ── Greece ──
for t in ['AEK Athens', 'Aris', 'Athens Kallithea', 'Atromitos']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Greek Super League')

# ── Russia ──
for t in ['Akhmat Grozny', 'Akron Togliatti', 'CSKA Moskva', 'Dinamo Moskva', 'Spartak Moskva']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Russian Premier League')

# ── Ukraine ──
for t in ['Chornomorets']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Ukrainian Premier League')

# ── Austria ──
for t in ['Austria Klagenfurt']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Austrian Bundesliga')
for t in ['Austria Lustenau']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Austrian 2. Liga')

# ── Switzerland ──
for t in ['Basel']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Swiss Super League')
for t in ['Bellinzona']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Swiss Challenge League')

# ── Sweden ──
for t in ['Elfsborg']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Swedish Allsvenskan')

# ── Serbia ──
for t in ['Crvena Zvezda']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Serbian Super Liga')

# ── Hungary ──
for t in ['Ferencváros']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Hungarian NB I')

# ── Romania ──
for t in ['Farul Constanţa']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Romanian Liga I')
for t in ['Argeș']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Romanian Liga II')

# ── Bulgaria ──
for t in ['Arda', 'Beroe', 'Botev Plovdiv', 'CSKA 1948 Sofia', 'CSKA Sofia', 'Cherno More']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Bulgarian First League')

# ── Cyprus ──
for t in ['AEK Larnaca', 'AEL', 'Anorthosis', 'Apollon']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Cypriot First Division')

# ── Slovenia ──
for t in ['Domžale']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Slovenian PrvaLiga')

# ── Montenegro ──
for t in ['Bokelj']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Montenegrin First League')

# ── Albania ──
for t in ['Egnatia Rrogozhinë']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Albanian Superiore')

# ── Armenia ──
for t in ['Ararat-Armenia']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Armenian Premier League')

# ── Argentina ──
for t in [
    'Aldosivi', 'Argentinos Juniors', 'Atlético Tucumán', 'Barracas Central',
    'Belgrano', 'Boca Juniors', 'Central Córdoba SdE', 'Defensa y Justicia',
    'Deportivo Riestra', 'Estudiantes',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Argentina')
for t in [
    'All Boys', 'Almirante Brown', 'Atlético Rafaela', 'Chacarita Juniors',
    'Colón', 'Deportivo Morón', 'Estudiantes Caseros', 'Estudiantes Río Cuarto',
    'Ferro Carril Oeste',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Argentina B')

# ── Brasil (additional) ──
for t in ['Athletico Paranaense', 'Atlético Mineiro', 'Bahia',
           'Botafogo', 'Corinthians', 'Cruzeiro',
           'Flamengo', 'Fluminense', 'Chapecoense', 'Coritiba', 'Remo']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Serie A Brasil')
for t in ['América Mineiro', 'Atlético GO', 'Avaí', 'Botafogo SP', 'Criciúma', 'Cuiabá',
           'Ceará', 'CRB', 'Sport', 'Sport Recife', 'Sport Club do Recife',
           'Ceará SC', 'Fortaleza']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Serie B Brasil')
for t in ['ABC', 'Botafogo PB', 'Confiança', 'CSA', 'Ferroviária', 'Figueirense',
           'Floresta EC', 'Amazonas', 'Brusque']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Serie C Brasil')
for t in ['América RN', 'Anápolis', 'Cianorte']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Serie D Brasil')
for t in ['Camboriú']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Catarinense A1')

# ── MLS ──
for t in ['Colorado Rapids', 'Los Angeles FC', 'LAFC']:
    CLUB_LEAGUE_MAP.setdefault(t, 'MLS')

# ── Mexico ──
for t in ['Atlas', 'Atlético de San Luis']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga MX')

# ── Colombia ──
for t in [
    'América de Cali', 'Atlético Bucaramanga', 'Atlético Nacional',
    'Boyacá Chicó', 'Deportivo Cali', 'Deportivo Pasto', 'Deportivo Pereira',
    'Envigado',
    'Medellin', 'Medellín', 'Independiente Medellín', 'Independiente Medellin', 'DIM',
    'Junior', 'Junior FC', 'Junior de Barranquilla',
    'Millonarios', 'Millonarios FC',
    'Once Caldas', 'Patriotas', 'Patriotas FC',
    'Santa Fe', 'Independiente Santa Fe',
    'Tolima', 'Deportes Tolima',
    'Águilas Doradas', 'Aguilas Doradas', 'Jaguares de Córdoba', 'Jaguares',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Colombia')
for t in ['Atlético Huila', 'Cortuluá', 'Deportes Quindío', 'Union Magdalena']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Colombia B')

# ── Chile ──
for t in ['Audax Italiano', 'Cobresal', 'Colo Colo', 'Coquimbo Unido', 'Deportes Iquique', 'Comerciantes Unidos']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Chile')
for t in ['Deportes Temuco']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Chile B')

# ── Uruguay ──
for t in ['Boston River', 'Cerro', 'Cerro Largo', 'Danubio', 'Defensor Sporting',
           'Deportivo Maldonado', 'Fénix', 'Penarol']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Uruguai')
for t in ['Albion']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Uruguai B')

# ── Paraguay ──
for t in ['Cerro Porteño']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Paraguai')
for t in ['Atlético Tembetary', 'Deportivo Recoleta']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Paraguai B')

# ── Ecuador ──
for t in ['Aucas', 'Emelec', 'Mushuc Runa', 'Orense']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Equador')

# ── Bolivia ──
for t in ['Aurora', 'Blooming', 'Bolívar']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Bolivia')

# ── Venezuela ──
for t in ['Academia Puerto Cabello', 'Deportivo Táchira', 'Estudiantes de Mérida']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Venezuela')

# ── Peru ──
for t in ['ADT', 'Alianza', 'Alianza Lima', 'Carlos Mannucci']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Peru')

# ── Japan ──
for t in ['Albirex Niigata', 'Avispa Fukuoka', 'Cerezo Osaka', 'Consadole Sapporo']:
    CLUB_LEAGUE_MAP.setdefault(t, 'J1 League')
for t in ['Fagiano Okayama']:
    CLUB_LEAGUE_MAP.setdefault(t, 'J2 League')

# ── Korea ──
for t in ['Daegu', 'Daejeon Citizen', 'Jeonbuk Motors']:
    CLUB_LEAGUE_MAP.setdefault(t, 'K-League 1')
for t in ['Anyang', 'Bucheon 1995']:
    CLUB_LEAGUE_MAP.setdefault(t, 'K-League 2')

# ── Saudi Arabia ──
for t in ['Al Ahli']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Saudi Pro League')
for t in ['Al Hazem', 'Al Najma']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Saudi First Division')

# ── Qatar ──
for t in ['Al Khor', 'Al Rayyan', 'Al Sadd', 'Qatar SC']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Qatar Stars League')

# ── UAE ──
for t in [
    'Ajman', 'Al Ain', 'Al Bataeh', 'Al Ittihad Kalba', 'Al Jazira',
    'Al Nasr', 'Al Orooba', 'Al Sharjah', 'Al Wahda', 'Al Wasl',
    'Bani Yas', 'Dibba Al Hisn',
]:
    CLUB_LEAGUE_MAP.setdefault(t, 'UAE Pro League')
for t in ['Al Dhafra', 'Dibba Al Fujairah']:
    CLUB_LEAGUE_MAP.setdefault(t, 'UAE First Division')

# ── China ──
for t in ['Beijing Guoan', 'Qingdao West Coast']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Chinese Super League')

# ── India ──
for t in ['Bengaluru', 'East Bengal', 'Kowloon City']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Indian Super League')

# ── Thailand ──
for t in ['Bangkok United', 'Buriram United', 'Lee Man', 'Chiangrai United', 'Tai Po']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Thai League')

# ── Tunisia ──
for t in ['ES Tunis']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Tunisian Ligue 1')

# ── Other ──
for t in ['Abahani Dhaka']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Bangladesh Premier League')
for t in ['Al Fahaheel']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Kuwaiti Premier League')
for t in ['Antigua GFC']:
    CLUB_LEAGUE_MAP.setdefault(t, 'Liga Nacional Guatemala')

# ============================================================
# FIX: Missing / variant club names from scouting data
# These clubs were falling through to the default "Serie B Brasil"
# ============================================================

# ── Uruguay (variants — direct assignment to override any prior entries) ──
CLUB_LEAGUE_MAP['Nacional'] = 'Liga Uruguai'
CLUB_LEAGUE_MAP['Club Nacional'] = 'Liga Uruguai'
CLUB_LEAGUE_MAP['Nacional Montevideo'] = 'Liga Uruguai'
CLUB_LEAGUE_MAP['Liverpool'] = 'Liga Uruguai'
CLUB_LEAGUE_MAP['Liverpool Montevideo'] = 'Liga Uruguai'
CLUB_LEAGUE_MAP['Juventud'] = 'Liga Uruguai'
CLUB_LEAGUE_MAP['CA Juventud'] = 'Liga Uruguai'
CLUB_LEAGUE_MAP['Juventud de Las Piedras'] = 'Liga Uruguai'
CLUB_LEAGUE_MAP['Wanderers'] = 'Liga Uruguai'
CLUB_LEAGUE_MAP['Montevideo Wanderers'] = 'Liga Uruguai'
CLUB_LEAGUE_MAP['Torque'] = 'Liga Uruguai'
CLUB_LEAGUE_MAP['Montevideo City Torque'] = 'Liga Uruguai'
CLUB_LEAGUE_MAP['Progreso'] = 'Liga Uruguai'
CLUB_LEAGUE_MAP['Miramar Misiones'] = 'Liga Uruguai'

# ── Argentina (variants) ──
CLUB_LEAGUE_MAP['Independiente Rivadavia'] = 'Liga Argentina'
CLUB_LEAGUE_MAP['Talleres Córdoba'] = 'Liga Argentina'
CLUB_LEAGUE_MAP['Talleres de Córdoba'] = 'Liga Argentina'
CLUB_LEAGUE_MAP['Newell\'s Old Boys'] = 'Liga Argentina'
CLUB_LEAGUE_MAP['Newell\'s'] = 'Liga Argentina'
CLUB_LEAGUE_MAP['Unión de Santa Fe'] = 'Liga Argentina'
CLUB_LEAGUE_MAP['Unión'] = 'Liga Argentina'
CLUB_LEAGUE_MAP['Central Córdoba'] = 'Liga Argentina'
CLUB_LEAGUE_MAP['Central Córdoba SdE'] = 'Liga Argentina'
CLUB_LEAGUE_MAP['Gimnasia LP'] = 'Liga Argentina'
CLUB_LEAGUE_MAP['Gimnasia y Esgrima'] = 'Liga Argentina'
CLUB_LEAGUE_MAP['Platense'] = 'Liga Argentina'
CLUB_LEAGUE_MAP['Instituto'] = 'Liga Argentina'
CLUB_LEAGUE_MAP['Deportivo Riestra'] = 'Liga Argentina'
CLUB_LEAGUE_MAP['Sarmiento'] = 'Liga Argentina'

# ── Colombia (variants) ──
CLUB_LEAGUE_MAP['Tolima'] = 'Liga Colombia'
CLUB_LEAGUE_MAP['Deportes Tolima'] = 'Liga Colombia'
CLUB_LEAGUE_MAP['Millonarios FC'] = 'Liga Colombia'
CLUB_LEAGUE_MAP['Santa Fe'] = 'Liga Colombia'
CLUB_LEAGUE_MAP['Independiente Santa Fe'] = 'Liga Colombia'
CLUB_LEAGUE_MAP['Envigado'] = 'Liga Colombia'
CLUB_LEAGUE_MAP['Jaguares de Córdoba'] = 'Liga Colombia'
CLUB_LEAGUE_MAP['Patriotas'] = 'Liga Colombia'
CLUB_LEAGUE_MAP['La Equidad'] = 'Liga Colombia'
CLUB_LEAGUE_MAP['Águilas Doradas'] = 'Liga Colombia'

# ── Japan (variants) ──
CLUB_LEAGUE_MAP['Shimizu S-Pulse'] = 'J1 League'
CLUB_LEAGUE_MAP['Shimizu S Pulse'] = 'J1 League'
CLUB_LEAGUE_MAP['Sanfrecce Hiroshima'] = 'J1 League'
CLUB_LEAGUE_MAP['Kashiwa Reysol'] = 'J1 League'
CLUB_LEAGUE_MAP['Jubilo Iwata'] = 'J1 League'
CLUB_LEAGUE_MAP['Machida Zelvia'] = 'J1 League'
CLUB_LEAGUE_MAP['Tokushima Vortis'] = 'J2 League'
CLUB_LEAGUE_MAP['Tokyo Verdy'] = 'J2 League'
CLUB_LEAGUE_MAP['V-Varen Nagasaki'] = 'J2 League'
CLUB_LEAGUE_MAP['Ventforet Kofu'] = 'J2 League'

# ── Switzerland (variants) ──
CLUB_LEAGUE_MAP['Sion'] = 'Swiss Super League'
CLUB_LEAGUE_MAP['FC Sion'] = 'Swiss Super League'
CLUB_LEAGUE_MAP['Young Boys'] = 'Swiss Super League'
CLUB_LEAGUE_MAP['BSC Young Boys'] = 'Swiss Super League'
CLUB_LEAGUE_MAP['Servette'] = 'Swiss Super League'
CLUB_LEAGUE_MAP['Lausanne'] = 'Swiss Super League'
CLUB_LEAGUE_MAP['Lugano'] = 'Swiss Super League'
CLUB_LEAGUE_MAP['St. Gallen'] = 'Swiss Super League'
CLUB_LEAGUE_MAP['Grasshoppers'] = 'Swiss Super League'
CLUB_LEAGUE_MAP['Luzern'] = 'Swiss Super League'
CLUB_LEAGUE_MAP['Winterthur'] = 'Swiss Super League'
CLUB_LEAGUE_MAP['Yverdon'] = 'Swiss Super League'

# ── Turkey (variants) ──
CLUB_LEAGUE_MAP['Göztepe'] = 'Super Lig'
CLUB_LEAGUE_MAP['Goztepe'] = 'Super Lig'
CLUB_LEAGUE_MAP['Hatayspor'] = 'Super Lig'
CLUB_LEAGUE_MAP['Sivasspor'] = 'Super Lig'
CLUB_LEAGUE_MAP['Gaziantep FK'] = 'Super Lig'
CLUB_LEAGUE_MAP['Rizespor'] = 'Super Lig'
CLUB_LEAGUE_MAP['Pendikspor'] = 'Super Lig'
CLUB_LEAGUE_MAP['Bodrum FK'] = 'Super Lig'
CLUB_LEAGUE_MAP['Eyüpspor'] = 'Super Lig'

# ── Ukraine (variants) ──
CLUB_LEAGUE_MAP['Metalist 1925 Kharkiv'] = 'Ukrainian Premier League'
CLUB_LEAGUE_MAP['Metalist 1925'] = 'Ukrainian Premier League'
CLUB_LEAGUE_MAP['Shakhtar Donetsk'] = 'Ukrainian Premier League'
CLUB_LEAGUE_MAP['Shakhtar'] = 'Ukrainian Premier League'
CLUB_LEAGUE_MAP['Dynamo Kyiv'] = 'Ukrainian Premier League'
CLUB_LEAGUE_MAP['Dnipro-1'] = 'Ukrainian Premier League'
CLUB_LEAGUE_MAP['Vorskla'] = 'Ukrainian Premier League'
CLUB_LEAGUE_MAP['Kolos Kovalivka'] = 'Ukrainian Premier League'
CLUB_LEAGUE_MAP['Kryvbas'] = 'Ukrainian Premier League'
CLUB_LEAGUE_MAP['Mynai'] = 'Ukrainian Premier League'

# ── Malta ──
CLUB_LEAGUE_MAP['Hamrun Spartans'] = 'Maltese Premier League'
CLUB_LEAGUE_MAP['Ħamrun Spartans'] = 'Maltese Premier League'
CLUB_LEAGUE_MAP['Valletta'] = 'Maltese Premier League'
CLUB_LEAGUE_MAP['Hibernians'] = 'Maltese Premier League'
CLUB_LEAGUE_MAP['Floriana'] = 'Maltese Premier League'
CLUB_LEAGUE_MAP['Birkirkara'] = 'Maltese Premier League'
CLUB_LEAGUE_MAP['Sliema Wanderers'] = 'Maltese Premier League'

# ── Croatia ──
CLUB_LEAGUE_MAP['Dinamo Zagreb'] = 'Croatian HNL'
CLUB_LEAGUE_MAP['Hajduk Split'] = 'Croatian HNL'
CLUB_LEAGUE_MAP['Rijeka'] = 'Croatian HNL'
CLUB_LEAGUE_MAP['Osijek'] = 'Croatian HNL'
CLUB_LEAGUE_MAP['Lokomotiva Zagreb'] = 'Croatian HNL'

# ── Czech Republic ──
CLUB_LEAGUE_MAP['Slavia Prague'] = 'Czech First League'
CLUB_LEAGUE_MAP['Sparta Prague'] = 'Czech First League'
CLUB_LEAGUE_MAP['Viktoria Plzeň'] = 'Czech First League'
CLUB_LEAGUE_MAP['Baník Ostrava'] = 'Czech First League'

# ── Denmark (additional) ──
CLUB_LEAGUE_MAP['Copenhagen'] = 'Danish Superliga'
CLUB_LEAGUE_MAP['FC Copenhagen'] = 'Danish Superliga'
CLUB_LEAGUE_MAP['Brøndby'] = 'Danish Superliga'
CLUB_LEAGUE_MAP['Nordsjælland'] = 'Danish Superliga'
CLUB_LEAGUE_MAP['Silkeborg'] = 'Danish Superliga'

# ── Norway ──
CLUB_LEAGUE_MAP['Bodø/Glimt'] = 'Norwegian Eliteserien'
CLUB_LEAGUE_MAP['Molde'] = 'Norwegian Eliteserien'
CLUB_LEAGUE_MAP['Rosenborg'] = 'Norwegian Eliteserien'
CLUB_LEAGUE_MAP['Viking'] = 'Norwegian Eliteserien'
CLUB_LEAGUE_MAP['Brann'] = 'Norwegian Eliteserien'

# ── Sweden (additional) ──
CLUB_LEAGUE_MAP['Malmö FF'] = 'Swedish Allsvenskan'
CLUB_LEAGUE_MAP['AIK'] = 'Swedish Allsvenskan'
CLUB_LEAGUE_MAP['Djurgården'] = 'Swedish Allsvenskan'
CLUB_LEAGUE_MAP['Hammarby'] = 'Swedish Allsvenskan'
CLUB_LEAGUE_MAP['IFK Göteborg'] = 'Swedish Allsvenskan'

# ── Hungary (additional) ──
CLUB_LEAGUE_MAP['Ferencvárosi TC'] = 'Hungarian NB I'
CLUB_LEAGUE_MAP['Puskás Akadémia'] = 'Hungarian NB I'
CLUB_LEAGUE_MAP['Fehérvár'] = 'Hungarian NB I'

# ── Poland (additional) ──
CLUB_LEAGUE_MAP['Legia Warsaw'] = 'Polish Ekstraklasa'
CLUB_LEAGUE_MAP['Lech Poznań'] = 'Polish Ekstraklasa'
CLUB_LEAGUE_MAP['Raków Częstochowa'] = 'Polish Ekstraklasa'
CLUB_LEAGUE_MAP['Pogoń Szczecin'] = 'Polish Ekstraklasa'

# ── Greece (additional) ──
CLUB_LEAGUE_MAP['Olympiacos'] = 'Greek Super League'
CLUB_LEAGUE_MAP['Olympiakos'] = 'Greek Super League'
CLUB_LEAGUE_MAP['PAOK'] = 'Greek Super League'
CLUB_LEAGUE_MAP['Panathinaikos'] = 'Greek Super League'
CLUB_LEAGUE_MAP['AEK Athens'] = 'Greek Super League'

# ── Romania (additional) ──
CLUB_LEAGUE_MAP['CFR Cluj'] = 'Romanian Liga I'
CLUB_LEAGUE_MAP['FCSB'] = 'Romanian Liga I'
CLUB_LEAGUE_MAP['Universitatea Craiova'] = 'Romanian Liga I'
CLUB_LEAGUE_MAP['Rapid Bucharest'] = 'Romanian Liga I'

# ── Russia ──
CLUB_LEAGUE_MAP['Zenit'] = 'Russian Premier League'
CLUB_LEAGUE_MAP['Spartak Moscow'] = 'Russian Premier League'
CLUB_LEAGUE_MAP['Lokomotiv Moscow'] = 'Russian Premier League'
CLUB_LEAGUE_MAP['Krasnodar'] = 'Russian Premier League'

# ── Malaysia (variants) ──
CLUB_LEAGUE_MAP['Selangor'] = 'Malaysian Super League'
CLUB_LEAGUE_MAP['JDT'] = 'Malaysian Super League'
CLUB_LEAGUE_MAP['Johor Darul Ta\'zim'] = 'Malaysian Super League'
CLUB_LEAGUE_MAP['Kedah'] = 'Malaysian Super League'
CLUB_LEAGUE_MAP['Terengganu'] = 'Malaysian Super League'
CLUB_LEAGUE_MAP['Perak'] = 'Malaysian Super League'
CLUB_LEAGUE_MAP['Sabah FK'] = 'Malaysian Super League'
CLUB_LEAGUE_MAP['Negeri Sembilan'] = 'Malaysian Super League'

# ── South Africa ──
CLUB_LEAGUE_MAP['Mamelodi Sundowns'] = 'South African Premier'
CLUB_LEAGUE_MAP['Kaizer Chiefs'] = 'South African Premier'
CLUB_LEAGUE_MAP['Orlando Pirates'] = 'South African Premier'
CLUB_LEAGUE_MAP['Stellenbosch'] = 'South African Premier'
CLUB_LEAGUE_MAP['Cape Town City'] = 'South African Premier'
CLUB_LEAGUE_MAP['SuperSport United'] = 'South African Premier'
CLUB_LEAGUE_MAP['AmaZulu'] = 'South African Premier'
CLUB_LEAGUE_MAP['Richards Bay'] = 'South African Premier'
CLUB_LEAGUE_MAP['Royal AM'] = 'South African Premier'
CLUB_LEAGUE_MAP['Sekhukhune United'] = 'South African Premier'
CLUB_LEAGUE_MAP['Chippa United'] = 'South African Premier'
CLUB_LEAGUE_MAP['Golden Arrows'] = 'South African Premier'
CLUB_LEAGUE_MAP['TS Galaxy'] = 'South African Premier'
CLUB_LEAGUE_MAP['Polokwane City'] = 'South African Premier'

# ── China (variants) ──
CLUB_LEAGUE_MAP['Shenzhen Peng City'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Shenzhen FC'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Yunnan Yukun'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Chengdu Rongcheng'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Shanghai Shenhua'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Shanghai Port'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Shanghai SIPG'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Shandong Taishan'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Guangzhou FC'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Guangzhou Evergrande'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Wuhan Three Towns'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Changchun Yatai'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Dalian Professional'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Henan Songshan'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Tianjin Jinmen Tiger'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Zhejiang FC'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Cangzhou Mighty Lions'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Meizhou Hakka'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Nantong Zhiyun'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Qingdao Hainiu'] = 'Chinese Super League'
CLUB_LEAGUE_MAP['Hebei FC'] = 'Chinese Super League'

# ── Greece (variants) ──
CLUB_LEAGUE_MAP['Olympiacos Piraeus'] = 'Greek Super League'
CLUB_LEAGUE_MAP['Olympiakos Piraeus'] = 'Greek Super League'
CLUB_LEAGUE_MAP['PAOK Thessaloniki'] = 'Greek Super League'
CLUB_LEAGUE_MAP['Panathinaikos Athens'] = 'Greek Super League'
CLUB_LEAGUE_MAP['AEK Athens FC'] = 'Greek Super League'
CLUB_LEAGUE_MAP['Aris Thessaloniki'] = 'Greek Super League'
CLUB_LEAGUE_MAP['Volos'] = 'Greek Super League'
CLUB_LEAGUE_MAP['Volos NFC'] = 'Greek Super League'
CLUB_LEAGUE_MAP['Lamia'] = 'Greek Super League'
CLUB_LEAGUE_MAP['Levadiakos'] = 'Greek Super League'
CLUB_LEAGUE_MAP['Asteras Tripolis'] = 'Greek Super League'
CLUB_LEAGUE_MAP['Ionikos'] = 'Greek Super League'

# ── Egypt ──
CLUB_LEAGUE_MAP['Al Ahly'] = 'Egyptian Premier League'
CLUB_LEAGUE_MAP['Zamalek'] = 'Egyptian Premier League'
CLUB_LEAGUE_MAP['Pyramids FC'] = 'Egyptian Premier League'
CLUB_LEAGUE_MAP['Future FC'] = 'Egyptian Premier League'
CLUB_LEAGUE_MAP['Ceramica Cleopatra'] = 'Egyptian Premier League'

# ── Morocco (additional) ──
CLUB_LEAGUE_MAP['Wydad Casablanca'] = 'Moroccan Botola'
CLUB_LEAGUE_MAP['Raja Casablanca'] = 'Moroccan Botola'
CLUB_LEAGUE_MAP['RS Berkane'] = 'Moroccan Botola'
CLUB_LEAGUE_MAP['FUS Rabat'] = 'Moroccan Botola'

# ── Korea (additional variants) ──
CLUB_LEAGUE_MAP['Ulsan'] = 'K-League 1'
CLUB_LEAGUE_MAP['Ulsan HD'] = 'K-League 1'
CLUB_LEAGUE_MAP['Ulsan Hyundai'] = 'K-League 1'
CLUB_LEAGUE_MAP['Jeonbuk'] = 'K-League 1'
CLUB_LEAGUE_MAP['Jeonbuk Hyundai'] = 'K-League 1'
CLUB_LEAGUE_MAP['Pohang Steelers'] = 'K-League 1'
CLUB_LEAGUE_MAP['Gangwon FC'] = 'K-League 1'
CLUB_LEAGUE_MAP['Incheon United'] = 'K-League 1'
CLUB_LEAGUE_MAP['Jeju United'] = 'K-League 1'
CLUB_LEAGUE_MAP['Gwangju FC'] = 'K-League 1'
CLUB_LEAGUE_MAP['FC Seoul'] = 'K-League 1'
CLUB_LEAGUE_MAP['Suwon FC'] = 'K-League 1'

# ── Japan (additional variants) ──
CLUB_LEAGUE_MAP['Urawa Red Diamonds'] = 'J1 League'
CLUB_LEAGUE_MAP['Urawa Reds'] = 'J1 League'
CLUB_LEAGUE_MAP['Yokohama F. Marinos'] = 'J1 League'
CLUB_LEAGUE_MAP['Yokohama F Marinos'] = 'J1 League'
CLUB_LEAGUE_MAP['Vissel Kobe'] = 'J1 League'
CLUB_LEAGUE_MAP['Kawasaki Frontale'] = 'J1 League'
CLUB_LEAGUE_MAP['Nagoya Grampus'] = 'J1 League'
CLUB_LEAGUE_MAP['Gamba Osaka'] = 'J1 League'
CLUB_LEAGUE_MAP['FC Tokyo'] = 'J1 League'
CLUB_LEAGUE_MAP['Kashima Antlers'] = 'J1 League'
CLUB_LEAGUE_MAP['Sanfrecce Hiroshima'] = 'J1 League'
CLUB_LEAGUE_MAP['Kyoto Sanga'] = 'J1 League'

# ── Turkey (additional variants) ──
CLUB_LEAGUE_MAP['İstanbul Başakşehir'] = 'Super Lig'
CLUB_LEAGUE_MAP['Istanbul Basaksehir'] = 'Super Lig'
CLUB_LEAGUE_MAP['Çaykur Rizespor'] = 'Super Lig'
CLUB_LEAGUE_MAP['Konyaspor'] = 'Super Lig'

# ── Belgium (additional variants) ──
CLUB_LEAGUE_MAP['Union Saint-Gilloise'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['Union SG'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['Club Brugge'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['Anderlecht'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['Gent'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['KAA Gent'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['Standard Liège'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['Genk'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['KRC Genk'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['Antwerp'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['Royal Antwerp'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['OH Leuven'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['Mechelen'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['KV Mechelen'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['Charleroi'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['Sint-Truiden'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['Westerlo'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['KV Kortrijk'] = 'Belgian Pro League'
CLUB_LEAGUE_MAP['Eupen'] = 'Belgian Pro League'

# ── Scotland (additional) ──
CLUB_LEAGUE_MAP['Rangers'] = 'Scottish Premiership'
CLUB_LEAGUE_MAP['Aberdeen'] = 'Scottish Premiership'
CLUB_LEAGUE_MAP['Hibernian'] = 'Scottish Premiership'
CLUB_LEAGUE_MAP['Hearts'] = 'Scottish Premiership'
CLUB_LEAGUE_MAP['St Mirren'] = 'Scottish Premiership'
CLUB_LEAGUE_MAP['Dundee United'] = 'Scottish Premiership'
CLUB_LEAGUE_MAP['Motherwell'] = 'Scottish Premiership'

# ── MLS (additional) ──
CLUB_LEAGUE_MAP['LA Galaxy'] = 'MLS'
CLUB_LEAGUE_MAP['Los Angeles Galaxy'] = 'MLS'
CLUB_LEAGUE_MAP['Inter Miami'] = 'MLS'
CLUB_LEAGUE_MAP['LAFC'] = 'MLS'
CLUB_LEAGUE_MAP['New York Red Bulls'] = 'MLS'
CLUB_LEAGUE_MAP['NYCFC'] = 'MLS'
CLUB_LEAGUE_MAP['New York City FC'] = 'MLS'
CLUB_LEAGUE_MAP['Seattle Sounders'] = 'MLS'
CLUB_LEAGUE_MAP['Portland Timbers'] = 'MLS'
CLUB_LEAGUE_MAP['Nashville SC'] = 'MLS'
CLUB_LEAGUE_MAP['Columbus Crew'] = 'MLS'
CLUB_LEAGUE_MAP['FC Cincinnati'] = 'MLS'
CLUB_LEAGUE_MAP['Austin FC'] = 'MLS'
CLUB_LEAGUE_MAP['Charlotte FC'] = 'MLS'
CLUB_LEAGUE_MAP['CF Montréal'] = 'MLS'
CLUB_LEAGUE_MAP['Toronto FC'] = 'MLS'
CLUB_LEAGUE_MAP['Philadelphia Union'] = 'MLS'
CLUB_LEAGUE_MAP['D.C. United'] = 'MLS'
CLUB_LEAGUE_MAP['Orlando City'] = 'MLS'
CLUB_LEAGUE_MAP['Houston Dynamo'] = 'MLS'
CLUB_LEAGUE_MAP['Real Salt Lake'] = 'MLS'
CLUB_LEAGUE_MAP['Minnesota United'] = 'MLS'
CLUB_LEAGUE_MAP['Sporting Kansas City'] = 'MLS'
CLUB_LEAGUE_MAP['FC Dallas'] = 'MLS'
CLUB_LEAGUE_MAP['Vancouver Whitecaps'] = 'MLS'
CLUB_LEAGUE_MAP['Chicago Fire'] = 'MLS'
CLUB_LEAGUE_MAP['San Jose Earthquakes'] = 'MLS'
CLUB_LEAGUE_MAP['New England Revolution'] = 'MLS'

# ── Mexico (additional) ──
CLUB_LEAGUE_MAP['Club América'] = 'Liga MX'
CLUB_LEAGUE_MAP['Monterrey'] = 'Liga MX'
CLUB_LEAGUE_MAP['Tigres UANL'] = 'Liga MX'
CLUB_LEAGUE_MAP['Guadalajara'] = 'Liga MX'
CLUB_LEAGUE_MAP['Cruz Azul'] = 'Liga MX'
CLUB_LEAGUE_MAP['Toluca'] = 'Liga MX'
CLUB_LEAGUE_MAP['Pumas UNAM'] = 'Liga MX'
CLUB_LEAGUE_MAP['Santos Laguna'] = 'Liga MX'
CLUB_LEAGUE_MAP['León'] = 'Liga MX'
CLUB_LEAGUE_MAP['Pachuca'] = 'Liga MX'
CLUB_LEAGUE_MAP['Necaxa'] = 'Liga MX'
CLUB_LEAGUE_MAP['Puebla'] = 'Liga MX'
CLUB_LEAGUE_MAP['Mazatlán'] = 'Liga MX'
CLUB_LEAGUE_MAP['Querétaro'] = 'Liga MX'
CLUB_LEAGUE_MAP['Tijuana'] = 'Liga MX'
CLUB_LEAGUE_MAP['Juárez'] = 'Liga MX'

# ── Chile (additional) ──
CLUB_LEAGUE_MAP['Universidad de Chile'] = 'Liga Chile'
CLUB_LEAGUE_MAP['Universidad Católica'] = 'Liga Chile'
CLUB_LEAGUE_MAP['Colo-Colo'] = 'Liga Chile'
CLUB_LEAGUE_MAP['O\'Higgins'] = 'Liga Chile'
CLUB_LEAGUE_MAP['Huachipato'] = 'Liga Chile'
CLUB_LEAGUE_MAP['Unión Española'] = 'Liga Chile'
CLUB_LEAGUE_MAP['Everton de Viña del Mar'] = 'Liga Chile'
CLUB_LEAGUE_MAP['Palestino'] = 'Liga Chile'
CLUB_LEAGUE_MAP['La Calera'] = 'Liga Chile'

# ── Ecuador (additional) ──
CLUB_LEAGUE_MAP['LDU Quito'] = 'Liga Equador'
CLUB_LEAGUE_MAP['Liga de Quito'] = 'Liga Equador'
CLUB_LEAGUE_MAP['Barcelona SC'] = 'Liga Equador'
CLUB_LEAGUE_MAP['Independiente del Valle'] = 'Liga Equador'
CLUB_LEAGUE_MAP['El Nacional'] = 'Liga Equador'
CLUB_LEAGUE_MAP['Deportivo Cuenca'] = 'Liga Equador'
CLUB_LEAGUE_MAP['Delfín'] = 'Liga Equador'
CLUB_LEAGUE_MAP['Técnico Universitario'] = 'Liga Equador'

# ── Peru (additional) ──
CLUB_LEAGUE_MAP['Universitario'] = 'Liga Peru'
CLUB_LEAGUE_MAP['Sporting Cristal'] = 'Liga Peru'
CLUB_LEAGUE_MAP['Melgar'] = 'Liga Peru'
CLUB_LEAGUE_MAP['Cienciano'] = 'Liga Peru'
CLUB_LEAGUE_MAP['Sport Huancayo'] = 'Liga Peru'
CLUB_LEAGUE_MAP['Cusco FC'] = 'Liga Peru'

# ── Paraguay (additional) ──
CLUB_LEAGUE_MAP['Olimpia'] = 'Liga Paraguai'
CLUB_LEAGUE_MAP['Libertad'] = 'Liga Paraguai'
CLUB_LEAGUE_MAP['Guaraní'] = 'Liga Paraguai'
CLUB_LEAGUE_MAP['Sol de América'] = 'Liga Paraguai'
CLUB_LEAGUE_MAP['Sportivo Luqueño'] = 'Liga Paraguai'
CLUB_LEAGUE_MAP['Nacional Asunción'] = 'Liga Paraguai'

# ── Venezuela (additional) ──
CLUB_LEAGUE_MAP['Caracas FC'] = 'Liga Venezuela'
CLUB_LEAGUE_MAP['Monagas'] = 'Liga Venezuela'
CLUB_LEAGUE_MAP['Zamora FC'] = 'Liga Venezuela'

# ── Bolivia (additional) ──
CLUB_LEAGUE_MAP['The Strongest'] = 'Liga Bolivia'
CLUB_LEAGUE_MAP['Jorge Wilstermann'] = 'Liga Bolivia'
CLUB_LEAGUE_MAP['Oriente Petrolero'] = 'Liga Bolivia'
CLUB_LEAGUE_MAP['Always Ready'] = 'Liga Bolivia'

# ── Saudi Arabia (additional) ──
CLUB_LEAGUE_MAP['Al Hilal'] = 'Saudi Pro League'
CLUB_LEAGUE_MAP['Al Nassr'] = 'Saudi Pro League'
CLUB_LEAGUE_MAP['Al Ittihad'] = 'Saudi Pro League'
CLUB_LEAGUE_MAP['Al Shabab'] = 'Saudi Pro League'
CLUB_LEAGUE_MAP['Al Ettifaq'] = 'Saudi Pro League'
CLUB_LEAGUE_MAP['Al Fateh'] = 'Saudi Pro League'
CLUB_LEAGUE_MAP['Al Raed'] = 'Saudi Pro League'
CLUB_LEAGUE_MAP['Al Taawoun'] = 'Saudi Pro League'
CLUB_LEAGUE_MAP['Damac FC'] = 'Saudi Pro League'
CLUB_LEAGUE_MAP['Abha'] = 'Saudi Pro League'
CLUB_LEAGUE_MAP['Al Khaleej'] = 'Saudi Pro League'
CLUB_LEAGUE_MAP['Al Riyadh'] = 'Saudi Pro League'

# ── UAE (additional) ──
CLUB_LEAGUE_MAP['Al Wasl'] = 'UAE Pro League'
CLUB_LEAGUE_MAP['Al Ain'] = 'UAE Pro League'

# ── Qatar (additional) ──
CLUB_LEAGUE_MAP['Al Duhail'] = 'Qatar Stars League'
CLUB_LEAGUE_MAP['Al Gharafa'] = 'Qatar Stars League'
CLUB_LEAGUE_MAP['Al Arabi'] = 'Qatar Stars League'

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
