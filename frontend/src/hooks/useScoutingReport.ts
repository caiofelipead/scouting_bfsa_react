import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import type {
  PlayerProfile,
  IndicesResponse,
  SimilarityResponse,
  ComparisonResponse,
  SkillCornerPlayerProfile,
  ClustersResponse,
  PredictionResponse,
} from '../types/api';

// ── Types ──

export interface AnalysesPlayerData {
  nome: string;
  foto: string | null;
  posicao: string | null;
  idade: number | null;
  equipe: string | null;
  liga: string | null;
  modelo: string | null;
  perfil: string | null;
  scores: Record<string, number>;
  links: Record<string, string>;
  analysis_text: string | null;
  faixa_salarial: string | null;
  transfer_luvas: string | null;
  wyscout_match: string | null;
}

export interface ScoutingReportData {
  player: {
    name: string;
    position: string;
    club: string;
    league: string;
    age: number;
    height: string;
    foot: string;
    contract: string;
    badges: string[];
    clusterDef: string;
    photo: string | null;
    clubLogo: string | null;
  };
  analysis: {
    text: string | null;
    scores: Record<string, number>;
    links: Record<string, string>;
    modelo: string | null;
    faixaSalarial: string | null;
    transferLuvas: string | null;
  };
  predict: {
    impactScore: number;
    pSuccess: number;
    risk: string;
    riskColor: string;
    verdict: string;
  };
  composites: Array<{ name: string; value: number }>;
  eliteMetrics: Array<{ metric: string; p: number; impact: string }>;
  delta: Array<{ metric: string; player: number; incumbent: number }>;
  similar: Array<{ name: string; club: string; pct: number }>;
  physical: {
    sprints: { value: number; p: number } | null;
    maxSpeed: { value: number; p: number } | null;
    accelerations: { value: number; p: number } | null;
    distance: { value: number; p: number } | null;
    hiRuns: { value: number; p: number } | null;
    pressures: { value: number; p: number } | null;
  } | null;
  qualitative: {
    tactical: string[];
    technical: string[];
    physical: string[];
    mental: string[];
  };
  radarLabels: string[];
  radarValues: number[];
}

// ── Helpers ──

const STALE_TIME = 10 * 60 * 1000;
const GC_TIME = 30 * 60 * 1000;

function getRiskColor(risk: string): string {
  const lower = risk.toLowerCase();
  if (lower.includes('baix') || lower === 'low') return '#1B9E5A';
  if (lower.includes('med') || lower === 'medium') return '#D97706';
  return '#C8102E';
}

function deriveBadges(
  clusterName: string | undefined,
  trajectoryScore: number | null | undefined,
  ssp: number | null | undefined,
): string[] {
  const badges: string[] = [];
  if (clusterName) badges.push(clusterName);
  if (trajectoryScore != null && trajectoryScore >= 7) badges.push('Alta Projeção');
  if (ssp != null && ssp >= 8) badges.push('Elite SSP');
  if (ssp != null && ssp >= 6 && ssp < 8) badges.push('SSP Acima da Média');
  return badges;
}

function extractImpactText(p: number): string {
  if (p >= 95) return 'Nível de elite absoluta';
  if (p >= 90) return 'Referência na posição';
  if (p >= 85) return 'Destaque significativo';
  return 'Acima da média';
}

function parseQualitative(analysisText: string | null | undefined): {
  tactical: string[];
  technical: string[];
  physical: string[];
  mental: string[];
} {
  const defaults = {
    tactical: ['Posicionamento inteligente', 'Leitura de jogo', 'Organização tática'],
    technical: ['Qualidade no passe', 'Controle de bola', 'Finalização precisa'],
    physical: ['Boa velocidade', 'Resistência adequada', 'Explosão muscular'],
    mental: ['Mentalidade competitiva', 'Tomada de decisão', 'Liderança em campo'],
  };
  if (!analysisText) return defaults;
  return defaults;
}

// ── Analyses Players Hook ──

export function useAnalysesPlayers(search: string) {
  return useQuery({
    queryKey: ['scouting-report', 'analyses-players', search],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (search.trim()) params.search = search.trim();
      const r = await api.get('/analyses/players', { params });
      return r.data as { players: AnalysesPlayerData[]; total: number };
    },
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    refetchOnWindowFocus: false,
  });
}

// ── Main Hook ──

export function useScoutingReport(
  playerName: string | null,
  incumbentName: string | null,
) {
  // 1. Player profile
  const profileQuery = useQuery({
    queryKey: ['scouting-report', 'profile', playerName],
    queryFn: async () => {
      const res = await api.get(`/players/${encodeURIComponent(playerName!)}/profile`);
      return res.data as PlayerProfile;
    },
    enabled: !!playerName,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });

  const position = profileQuery.data?.summary?.position ?? '';

  // 2. Indices
  const indicesQuery = useQuery({
    queryKey: ['scouting-report', 'indices', playerName],
    queryFn: async () => {
      const res = await api.get(`/players/${encodeURIComponent(playerName!)}/indices`);
      return res.data as IndicesResponse;
    },
    enabled: !!playerName,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });

  // 3. Radar data
  const radarQuery = useQuery({
    queryKey: ['scouting-report', 'radar', playerName],
    queryFn: async () => {
      const res = await api.get(`/players/${encodeURIComponent(playerName!)}/radar`);
      return res.data as { labels: string[]; values: number[] };
    },
    enabled: !!playerName,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });

  // 4. Prediction
  const predictionQuery = useQuery({
    queryKey: ['scouting-report', 'prediction', playerName, position],
    queryFn: async () => {
      const res = await api.post('/prediction', {
        player_name: playerName,
        position: position,
      });
      return res.data as PredictionResponse;
    },
    enabled: !!playerName && !!position,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });

  // 5. Similarity
  const similarityQuery = useQuery({
    queryKey: ['scouting-report', 'similarity', playerName, position],
    queryFn: async () => {
      const res = await api.post('/similarity', {
        player_name: playerName,
        position: position,
        top_n: 3,
        min_minutes: 500,
      });
      return res.data as SimilarityResponse;
    },
    enabled: !!playerName && !!position,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });

  // 6. Clusters
  const clustersQuery = useQuery({
    queryKey: ['scouting-report', 'clusters', playerName, position],
    queryFn: async () => {
      const res = await api.post('/clusters', {
        position: position,
        player_name: playerName,
      });
      return res.data as ClustersResponse;
    },
    enabled: !!playerName && !!position,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });

  // 7. SkillCorner
  const skillCornerQuery = useQuery({
    queryKey: ['scouting-report', 'skillcorner', playerName],
    queryFn: async () => {
      const res = await api.get(`/skillcorner/player/${encodeURIComponent(playerName!)}`);
      return res.data as SkillCornerPlayerProfile;
    },
    enabled: !!playerName,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });

  // 8. Comparison (delta vs incumbent)
  const comparisonQuery = useQuery({
    queryKey: ['scouting-report', 'comparison', playerName, incumbentName, position],
    queryFn: async () => {
      const res = await api.post('/comparison', {
        player1: playerName,
        player2: incumbentName,
        position: position,
      });
      return res.data as ComparisonResponse;
    },
    enabled: !!playerName && !!incumbentName && !!position,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });

  // 9. Trajectory
  const trajectoryQuery = useQuery({
    queryKey: ['scouting-report', 'trajectory', playerName, position],
    queryFn: async () => {
      const res = await api.post('/trajectory', {
        player_name: playerName,
        position: position,
      });
      return res.data as { trajectory_score: number; projected_rating: number };
    },
    enabled: !!playerName && !!position,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });

  // ── Assemble data ──

  const isLoading =
    profileQuery.isLoading ||
    indicesQuery.isLoading ||
    radarQuery.isLoading;

  const isError =
    profileQuery.isError ||
    (profileQuery.isFetched && !profileQuery.data);

  const profile = profileQuery.data;
  const indices = indicesQuery.data;
  const radar = radarQuery.data;
  const prediction = predictionQuery.data;
  const similarity = similarityQuery.data;
  const clusters = clustersQuery.data;
  const sc = skillCornerQuery.data;
  const comparison = comparisonQuery.data;
  const trajectory = trajectoryQuery.data;

  // Find player's cluster
  const playerCluster = clusters?.clusters?.find((c) =>
    c.players?.some(
      (p) => p.name.toLowerCase() === (playerName ?? '').toLowerCase(),
    ),
  );

  const ssp = profile?.scout_score ?? null;

  const data: ScoutingReportData | null =
    profile
      ? {
          player: {
            name: profile.summary.display_name ?? profile.summary.name,
            position: profile.summary.position ?? '—',
            club: profile.summary.team ?? '—',
            league: profile.summary.league ?? '—',
            age: profile.summary.age ?? 0,
            height: '—',
            foot: '—',
            contract: '—',
            badges: deriveBadges(
              playerCluster?.name,
              trajectory?.trajectory_score,
              ssp,
            ),
            clusterDef: playerCluster?.name
              ? `Cluster: ${playerCluster.name}`
              : 'Cluster não identificado',
            photo: profile.summary.photo_url ?? null,
            clubLogo: profile.summary.club_logo ?? null,
          },
          analysis: {
            text: profile.analises?.analysis_text ?? null,
            scores: profile.analises?.scores ?? {},
            links: profile.analises?.links ?? {},
            modelo: profile.analises?.modelo ?? null,
            faixaSalarial: profile.analises?.faixa_salarial ?? null,
            transferLuvas: profile.analises?.transfer_luvas ?? null,
          },
          predict: {
            impactScore: ssp != null ? Math.round(ssp * 10) / 10 : 0,
            pSuccess: prediction
              ? Math.round(prediction.prediction.success_probability * 100)
              : 0,
            risk: prediction?.prediction.risk_level ?? '—',
            riskColor: getRiskColor(prediction?.prediction.risk_level ?? 'alto'),
            verdict:
              profile.analises?.analysis_text ??
              'Análise detalhada não disponível para este jogador.',
          },
          composites: indices
            ? Object.entries(indices.indices).map(([name, value]) => ({
                name,
                value: Math.round(value * 10) / 10,
              }))
            : [],
          eliteMetrics:
            radar
              ? radar.labels
                  .map((label, i) => ({
                    metric: label,
                    p: Math.round(radar.values[i]),
                    impact: extractImpactText(radar.values[i]),
                  }))
                  .filter((m) => m.p >= 85)
                  .sort((a, b) => b.p - a.p)
              : [],
          delta: comparison
            ? comparison.comparison.map((c) => ({
                metric: c.index,
                player: Math.round(c.player1_value * 10) / 10,
                incumbent: Math.round(c.player2_value * 10) / 10,
              }))
            : [],
          similar: similarity
            ? similarity.similar_players.slice(0, 3).map((s) => ({
                name: s.display_name ?? s.name,
                club: s.team ?? '—',
                pct: Math.round(s.similarity_pct),
              }))
            : [],
          physical: sc?.found && sc.physical_percentiles
            ? {
                sprints: sc.physical?.['sprints'] != null
                  ? { value: sc.physical['sprints'], p: sc.physical_percentiles['sprints'] ?? 0 }
                  : null,
                maxSpeed: sc.physical?.['max_speed'] != null
                  ? { value: sc.physical['max_speed'], p: sc.physical_percentiles['max_speed'] ?? 0 }
                  : null,
                accelerations: sc.physical?.['accelerations'] != null
                  ? { value: sc.physical['accelerations'], p: sc.physical_percentiles['accelerations'] ?? 0 }
                  : null,
                distance: sc.physical?.['distance'] != null
                  ? { value: sc.physical['distance'], p: sc.physical_percentiles['distance'] ?? 0 }
                  : null,
                hiRuns: sc.physical?.['hi_runs'] != null
                  ? { value: sc.physical['hi_runs'], p: sc.physical_percentiles['hi_runs'] ?? 0 }
                  : null,
                pressures: sc.physical?.['pressures_p90'] != null
                  ? { value: sc.physical['pressures_p90'], p: sc.physical_percentiles['pressures_p90'] ?? 0 }
                  : null,
              }
            : null,
          qualitative: parseQualitative(profile.analises?.analysis_text),
          radarLabels: radar?.labels ?? [],
          radarValues: radar?.values ?? [],
        }
      : null;

  return {
    data,
    isLoading,
    isError,
    profileLoading: profileQuery.isLoading,
    indicesLoading: indicesQuery.isLoading,
    radarLoading: radarQuery.isLoading,
    predictionLoading: predictionQuery.isLoading,
    similarityLoading: similarityQuery.isLoading,
    skillCornerLoading: skillCornerQuery.isLoading,
    comparisonLoading: comparisonQuery.isLoading,
    deltaAvailable: !!incumbentName && !comparisonQuery.isLoading,
  };
}
