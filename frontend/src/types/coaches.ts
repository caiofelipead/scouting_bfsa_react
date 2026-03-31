// ── Coach evaluation types ──────────────────────────────────────────

export interface CoachTacticalRadar {
  construcao: number | null;
  pressing: number | null;
  trans_ofensiva: number | null;
  trans_defensiva: number | null;
  altura_bloco: number | null;
  org_ofensiva: number | null;
  flexibilidade: number | null;
  uso_base: number | null;
  gestao: number | null;
}

export interface CoachSeason {
  id_treinador: string;
  clube: string | null;
  temporada: string | null;
  divisao: string | null;
  competicao: string | null;
  jogos: number | null;
  vitorias: number | null;
  empates: number | null;
  derrotas: number | null;
  aproveitamento: number | null;
  posicao_final: string | null;
  motivo_saida: string | null;
}

export interface CoachMetrics {
  aproveitamento_geral: number | null;
  aproveitamento_ponderado: number | null;
  estabilidade: number | null;
  taxa_demissao: number | null;
  melhor_aproveitamento: number | null;
  pior_aproveitamento: number | null;
  total_jogos: number;
  total_vitorias: number;
  total_empates: number;
  total_derrotas: number;
  clubes_count: number;
}

export interface Coach {
  id_treinador: string;
  nome: string;
  nascimento: string | null;
  nacionalidade: string | null;
  licenca: string | null;
  status: string | null;
  faixa_salarial: string | null;
  formacao_pref: string | null;
  formacao_alt: string | null;
  clube_atual: string | null;
  observacoes: string | null;
  tactical: CoachTacticalRadar;
  metricas: CoachMetrics;
  score: number;
  historico?: CoachSeason[];
  rank?: number;
}

export interface CoachListResponse {
  total: number;
  coaches: Coach[];
}

export interface CoachHistoryResponse {
  id_treinador: string;
  total: number;
  seasons: CoachSeason[];
}

export interface CoachCompareResponse {
  total: number;
  coaches: Coach[];
}

export interface CoachRankingResponse {
  total: number;
  coaches: Coach[];
  weights: Record<string, number>;
}

export interface CoachRankingWeights {
  w_aproveitamento?: number;
  w_tatico?: number;
  w_gestao?: number;
  w_uso_base?: number;
  w_estabilidade?: number;
  w_flexibilidade?: number;
}

export interface CoachFilters {
  status?: string;
  nacionalidade?: string;
  licenca?: string;
  formacao?: string;
}
