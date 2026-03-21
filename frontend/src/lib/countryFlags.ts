/**
 * Mapping from nationality/country names to ISO 3166-1 alpha-2 codes.
 * Used to render flag PNGs via flagcdn.com.
 */
const NATIONALITY_TO_CODE: Record<string, string> = {
  // South America
  'Brazil': 'br', 'Brasil': 'br', 'Brazilian': 'br',
  'Argentina': 'ar', 'Argentine': 'ar', 'Argentinian': 'ar',
  'Uruguay': 'uy', 'Uruguai': 'uy', 'Uruguayan': 'uy',
  'Colombia': 'co', 'Colômbia': 'co', 'Colombian': 'co',
  'Paraguay': 'py', 'Paraguai': 'py', 'Paraguayan': 'py',
  'Chile': 'cl', 'Chilean': 'cl',
  'Peru': 'pe', 'Peruvian': 'pe',
  'Ecuador': 'ec', 'Equador': 'ec', 'Ecuadorian': 'ec',
  'Venezuela': 've', 'Venezuelan': 've',
  'Bolivia': 'bo', 'Bolívia': 'bo', 'Bolivian': 'bo',
  'Guyana': 'gy', 'Suriname': 'sr',

  // Central America & Caribbean
  'Mexico': 'mx', 'México': 'mx', 'Mexican': 'mx',
  'Costa Rica': 'cr', 'Costa Rican': 'cr',
  'Panama': 'pa', 'Panamá': 'pa',
  'Honduras': 'hn', 'Honduran': 'hn',
  'Guatemala': 'gt', 'El Salvador': 'sv',
  'Nicaragua': 'ni',
  'Jamaica': 'jm', 'Jamaican': 'jm',
  'Haiti': 'ht', 'Haitian': 'ht',
  'Dominican Republic': 'do', 'República Dominicana': 'do',
  'Cuba': 'cu', 'Cuban': 'cu',
  'Trinidad and Tobago': 'tt', 'Trinidad e Tobago': 'tt',
  'Curaçao': 'cw', 'Curacao': 'cw',

  // North America
  'United States': 'us', 'EUA': 'us', 'USA': 'us', 'American': 'us',
  'Canada': 'ca', 'Canadá': 'ca', 'Canadian': 'ca',

  // Western Europe
  'Portugal': 'pt', 'Portuguese': 'pt',
  'Spain': 'es', 'Espanha': 'es', 'Spanish': 'es',
  'Italy': 'it', 'Itália': 'it', 'Italian': 'it',
  'France': 'fr', 'França': 'fr', 'French': 'fr',
  'Germany': 'de', 'Alemanha': 'de', 'German': 'de',
  'England': 'gb-eng', 'Inglaterra': 'gb-eng', 'English': 'gb-eng',
  'Netherlands': 'nl', 'Holanda': 'nl', 'Dutch': 'nl',
  'Belgium': 'be', 'Bélgica': 'be', 'Belgian': 'be',
  'Switzerland': 'ch', 'Suíça': 'ch', 'Swiss': 'ch',
  'Austria': 'at', 'Áustria': 'at', 'Austrian': 'at',
  'Luxembourg': 'lu', 'Luxemburgo': 'lu',
  'Ireland': 'ie', 'Irlanda': 'ie', 'Irish': 'ie',

  // Northern Europe
  'Sweden': 'se', 'Suécia': 'se', 'Swedish': 'se',
  'Norway': 'no', 'Noruega': 'no', 'Norwegian': 'no',
  'Denmark': 'dk', 'Dinamarca': 'dk', 'Danish': 'dk',
  'Finland': 'fi', 'Finlândia': 'fi', 'Finnish': 'fi',
  'Iceland': 'is', 'Islândia': 'is',

  // British Isles
  'Scotland': 'gb-sct', 'Escócia': 'gb-sct',
  'Wales': 'gb-wls', 'País de Gales': 'gb-wls',
  'Northern Ireland': 'gb-nir', 'Irlanda do Norte': 'gb-nir',

  // Eastern Europe
  'Poland': 'pl', 'Polônia': 'pl', 'Polish': 'pl',
  'Czech Republic': 'cz', 'República Tcheca': 'cz', 'Czechia': 'cz',
  'Croatia': 'hr', 'Croácia': 'hr', 'Croatian': 'hr',
  'Serbia': 'rs', 'Sérvia': 'rs', 'Serbian': 'rs',
  'Russia': 'ru', 'Rússia': 'ru', 'Russian': 'ru',
  'Ukraine': 'ua', 'Ucrânia': 'ua', 'Ukrainian': 'ua',
  'Romania': 'ro', 'Romênia': 'ro', 'Romanian': 'ro',
  'Hungary': 'hu', 'Hungria': 'hu', 'Hungarian': 'hu',
  'Bulgaria': 'bg', 'Bulgária': 'bg',
  'Slovenia': 'si', 'Eslovênia': 'si',
  'Slovakia': 'sk', 'Eslováquia': 'sk',
  'Albania': 'al', 'Albânia': 'al',
  'North Macedonia': 'mk', 'Macedônia do Norte': 'mk',
  'Bosnia and Herzegovina': 'ba', 'Bósnia': 'ba',
  'Montenegro': 'me',
  'Kosovo': 'xk',
  'Belarus': 'by', 'Bielorrússia': 'by',
  'Moldova': 'md', 'Moldávia': 'md',
  'Lithuania': 'lt', 'Lituânia': 'lt',
  'Latvia': 'lv', 'Letônia': 'lv',
  'Estonia': 'ee', 'Estônia': 'ee',
  'Georgia': 'ge', 'Geórgia': 'ge',
  'Armenia': 'am', 'Armênia': 'am',
  'Azerbaijan': 'az', 'Azerbaijão': 'az',

  // Mediterranean & Middle East
  'Turkey': 'tr', 'Turquia': 'tr', 'Turkish': 'tr',
  'Greece': 'gr', 'Grécia': 'gr', 'Greek': 'gr',
  'Cyprus': 'cy', 'Chipre': 'cy',
  'Israel': 'il',
  'United Arab Emirates': 'ae', 'Emirados Árabes': 'ae', 'UAE': 'ae',
  'Qatar': 'qa', 'Catar': 'qa',
  'Saudi Arabia': 'sa', 'Arábia Saudita': 'sa',
  'Iran': 'ir', 'Irã': 'ir', 'Iranian': 'ir',
  'Iraq': 'iq', 'Iraque': 'iq',
  'Kuwait': 'kw',
  'Bahrain': 'bh', 'Bahrein': 'bh',
  'Oman': 'om', 'Omã': 'om',
  'Jordan': 'jo', 'Jordânia': 'jo',
  'Lebanon': 'lb', 'Líbano': 'lb',
  'Syria': 'sy', 'Síria': 'sy',
  'Palestine': 'ps', 'Palestina': 'ps',

  // Africa
  'Nigeria': 'ng', 'Nigéria': 'ng', 'Nigerian': 'ng',
  'Senegal': 'sn', 'Senegalese': 'sn',
  'Ghana': 'gh', 'Gana': 'gh', 'Ghanaian': 'gh',
  'Cameroon': 'cm', 'Camarões': 'cm', 'Cameroonian': 'cm',
  'Morocco': 'ma', 'Marrocos': 'ma', 'Moroccan': 'ma',
  'Egypt': 'eg', 'Egito': 'eg', 'Egyptian': 'eg',
  'South Africa': 'za', 'África do Sul': 'za',
  'Angola': 'ao', 'Angolan': 'ao',
  'Mozambique': 'mz', 'Moçambique': 'mz',
  'Guinea-Bissau': 'gw', 'Guiné-Bissau': 'gw',
  'Cape Verde': 'cv', 'Cabo Verde': 'cv',
  'Algeria': 'dz', 'Argélia': 'dz', 'Algerian': 'dz',
  'Tunisia': 'tn', 'Tunísia': 'tn', 'Tunisian': 'tn',
  'Congo DR': 'cd', 'RD Congo': 'cd', 'DR Congo': 'cd',
  'Congo': 'cg',
  'Ivory Coast': 'ci', "Côte d'Ivoire": 'ci', 'Costa do Marfim': 'ci',
  'Mali': 'ml', 'Malian': 'ml',
  'Burkina Faso': 'bf',
  'Guinea': 'gn', 'Guiné': 'gn',
  'Gabon': 'ga', 'Gabão': 'ga',
  'Zambia': 'zm', 'Zâmbia': 'zm',
  'Zimbabwe': 'zw', 'Zimbábue': 'zw',
  'Tanzania': 'tz', 'Tanzânia': 'tz',
  'Kenya': 'ke', 'Quênia': 'ke',
  'Uganda': 'ug',
  'Ethiopia': 'et', 'Etiópia': 'et',
  'Togo': 'tg',
  'Benin': 'bj',
  'Niger': 'ne', 'Níger': 'ne',
  'Madagascar': 'mg',
  'Libya': 'ly', 'Líbia': 'ly',
  'Sudan': 'sd', 'Sudão': 'sd',
  'Eritrea': 'er', 'Eritreia': 'er',
  'Rwanda': 'rw', 'Ruanda': 'rw',
  'Burundi': 'bi',
  'Sierra Leone': 'sl', 'Serra Leoa': 'sl',
  'Liberia': 'lr', 'Libéria': 'lr',
  'Mauritania': 'mr', 'Mauritânia': 'mr',
  'Equatorial Guinea': 'gq', 'Guiné Equatorial': 'gq',
  'Comoros': 'km', 'Comores': 'km',
  'Central African Republic': 'cf', 'República Centro-Africana': 'cf',
  'Gambia': 'gm', 'Gâmbia': 'gm',

  // Asia
  'Japan': 'jp', 'Japão': 'jp', 'Japanese': 'jp',
  'South Korea': 'kr', 'Coreia do Sul': 'kr', 'Korean': 'kr',
  'China': 'cn', 'Chinese': 'cn',
  'India': 'in', 'Índia': 'in', 'Indian': 'in',
  'Australia': 'au', 'Austrália': 'au', 'Australian': 'au',
  'New Zealand': 'nz', 'Nova Zelândia': 'nz',
  'Thailand': 'th', 'Tailândia': 'th',
  'Vietnam': 'vn', 'Vietnã': 'vn',
  'Indonesia': 'id', 'Indonésia': 'id',
  'Philippines': 'ph', 'Filipinas': 'ph',
  'Malaysia': 'my', 'Malásia': 'my',
  'Singapore': 'sg', 'Cingapura': 'sg',
  'Uzbekistan': 'uz', 'Uzbequistão': 'uz',
  'Kazakhstan': 'kz', 'Cazaquistão': 'kz',
  'Tajikistan': 'tj', 'Tajiquistão': 'tj',
  'Kyrgyzstan': 'kg', 'Quirguistão': 'kg',
  'Turkmenistan': 'tm', 'Turcomenistão': 'tm',
  'Afghanistan': 'af', 'Afeganistão': 'af',
  'Pakistan': 'pk', 'Paquistão': 'pk',
  'Bangladesh': 'bd',
  'Nepal': 'np',
  'Sri Lanka': 'lk',
  'Myanmar': 'mm', 'Burma': 'mm',
  'Cambodia': 'kh', 'Camboja': 'kh',
};

/**
 * Get the flag image URL for a nationality.
 * Uses flagcdn.com which serves free PNG flags.
 * Returns null if nationality is not mapped.
 */
export function getFlagUrl(nationality: string | null | undefined, size: number = 20): string | null {
  if (!nationality) return null;
  const code = NATIONALITY_TO_CODE[nationality];
  if (!code) return null;
  // flagcdn.com serves PNG flags at various widths
  return `https://flagcdn.com/w${size}/${code}.png`;
}
