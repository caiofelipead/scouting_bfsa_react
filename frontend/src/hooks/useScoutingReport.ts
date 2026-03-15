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
    stats: {
      minutes: number | null;
      matches: number | null;
      goals: number | null;
      assists: number | null;
    };
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
    psv99: { value: number; p: number } | null;
    topPsv99: { value: number; p: number } | null;
  } | null;
  qualitative: {
    tactical: string[];
    technical: string[];
    physical: string[];
    mental: string[];
  };
  radarLabels: string[];
  radarValues: number[];
  allRadarMetrics: Array<{ metric: string; p: number }>;
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

/** Parse "D. Barrea (Godoy Cruz)" into clean "D. Barrea" */
function parseCleanName(displayName: string): string {
  const match = displayName.match(/^(.+?)\s*\(.*\)$/);
  return match ? match[1].trim() : displayName;
}

function parseQualitative(_analysisText: string | null | undefined): {
  tactical: string[];
  technical: string[];
  physical: string[];
  mental: string[];
} {
  return {
    tactical: ['Posicionamento inteligente', 'Leitura de jogo', 'Organização tática'],
    technical: ['Qualidade no passe', 'Controle de bola', 'Finalização precisa'],
    physical: ['Boa velocidade', 'Resistência adequada', 'Explosão muscular'],
    mental: ['Mentalidade competitiva', 'Tomada de decisão', 'Liderança em campo'],
  };
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

// ── SkillCorner Search Hook (for independent selector) ──

export interface SkillCornerSearchResult {
  player_name: string;
  short_name: string;
  team_name: string;
  position_group: string | null;
}

export function useSkillCornerSearchReport(query: string) {
  return useQuery({
    queryKey: ['scouting-report', 'sc-search', query],
    queryFn: async () => {
      const res = await api.get('/skillcorner/search', { params: { q: query, limit: 15 } });
      return res.data.results as SkillCornerSearchResult[];
    },
    enabled: query.length >= 2,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    refetchOnWindowFocus: false,
  });
}

// ── SkillCorner Single Player Hook (for comparison) ──

export function useSkillCornerPlayer(playerName: string | null) {
  return useQuery({
    queryKey: ['scouting-report', 'skillcorner', playerName],
    queryFn: async () => {
      const res = await api.get(`/skillcorner/player/${encodeURIComponent(playerName!)}`);
      return res.data as SkillCornerPlayerProfile;
    },
    enabled: !!playerName,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    refetchOnWindowFocus: false,
  });
}

// ── Main Hook ──
// Now accepts an optional separate skillCornerName for independent SC selection

export function useScoutingReport(
  playerName: string | null,
  incumbentName: string | null,
  analysesOverride?: AnalysesPlayerData | null,
  skillCornerName?: string | null,
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
        top_n: 5,
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

  // 7. SkillCorner — uses independent skillCornerName if provided, else playerName
  const scName = skillCornerName || playerName;
  const skillCornerQuery = useQuery({
    queryKey: ['scouting-report', 'skillcorner', scName],
    queryFn: async () => {
      const res = await api.get(`/skillcorner/player/${encodeURIComponent(scName!)}`);
      return res.data as SkillCornerPlayerProfile;
    },
    enabled: !!scName,
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

  // Merge analysis: prefer profile.analises, fallback to analysesOverride
  const profileAnalises = profile?.analises;
  const mergedAnalysis = {
    text: profileAnalises?.analysis_text ?? analysesOverride?.analysis_text ?? null,
    scores: (profileAnalises?.scores && Object.keys(profileAnalises.scores).length > 0)
      ? profileAnalises.scores
      : analysesOverride?.scores ?? {},
    links: (profileAnalises?.links && Object.keys(profileAnalises.links).length > 0)
      ? profileAnalises.links
      : analysesOverride?.links ?? {},
    modelo: profileAnalises?.modelo ?? analysesOverride?.modelo ?? null,
    faixaSalarial: profileAnalises?.faixa_salarial ?? analysesOverride?.faixa_salarial ?? null,
    transferLuvas: profileAnalises?.transfer_luvas ?? analysesOverride?.transfer_luvas ?? null,
  };

  // Clean player name: "D. Barrea (Godoy Cruz)" → "D. Barrea"
  const rawName = profile?.summary.display_name ?? profile?.summary.name ?? '';
  const cleanName = analysesOverride?.nome ?? parseCleanName(rawName);

  const data: ScoutingReportData | null =
    profile
      ? {
          player: {
            name: cleanName,
            position: profile.summary.position ?? analysesOverride?.posicao ?? '—',
            club: profile.summary.team ?? analysesOverride?.equipe ?? '—',
            league: profile.summary.league ?? analysesOverride?.liga ?? '—',
            age: profile.summary.age ?? analysesOverride?.idade ?? 0,
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
            photo: profile.summary.photo_url ?? analysesOverride?.foto ?? null,
            clubLogo: profile.summary.club_logo ?? null,
            stats: {
              minutes: profile.metrics?.['Minutos jogados:'] ?? profile.summary.minutes_played ?? null,
              matches: profile.metrics?.['Partidas jogadas'] ?? null,
              goals: profile.metrics?.['Golos'] ?? null,
              assists: profile.metrics?.['Assistências'] ?? null,
            },
          },
          analysis: mergedAnalysis,
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
            ? similarity.similar_players.slice(0, 5).map((s) => ({
                name: s.display_name ?? s.name,
                club: s.team ?? '—',
                pct: Math.round(s.similarity_pct),
              }))
            : [],
          physical: sc?.found && sc.physical
            ? {
                sprints: sc.physical['Sprints/90'] != null
                  ? { value: sc.physical['Sprints/90'], p: sc.physical_percentiles?.['Sprints/90'] ?? 0 }
                  : null,
                maxSpeed: sc.physical['Max Speed (km/h)'] != null
                  ? { value: sc.physical['Max Speed (km/h)'], p: sc.physical_percentiles?.['Max Speed (km/h)'] ?? 0 }
                  : null,
                accelerations: sc.physical['Accelerations/90'] != null
                  ? { value: sc.physical['Accelerations/90'], p: sc.physical_percentiles?.['Accelerations/90'] ?? 0 }
                  : null,
                distance: sc.physical['Distance/90'] != null
                  ? { value: sc.physical['Distance/90'], p: sc.physical_percentiles?.['Distance/90'] ?? 0 }
                  : null,
                hiRuns: sc.physical['High Intensity Runs/90'] != null
                  ? { value: sc.physical['High Intensity Runs/90'], p: sc.physical_percentiles?.['High Intensity Runs/90'] ?? 0 }
                  : null,
                pressures: sc.physical['Pressing Index/90'] != null
                  ? { value: sc.physical['Pressing Index/90'], p: sc.physical_percentiles?.['Pressing Index/90'] ?? 0 }
                  : null,
                psv99: sc.physical['Avg PSV-99'] != null
                  ? { value: sc.physical['Avg PSV-99'], p: sc.physical_percentiles?.['Avg PSV-99'] ?? 0 }
                  : null,
                topPsv99: sc.physical['Avg Top 5 PSV-99'] != null
                  ? { value: sc.physical['Avg Top 5 PSV-99'], p: sc.physical_percentiles?.['Avg Top 5 PSV-99'] ?? 0 }
                  : null,
              }
            : null,
          qualitative: parseQualitative(profile.analises?.analysis_text),
          radarLabels: radar?.labels ?? [],
          radarValues: radar?.values ?? [],
          allRadarMetrics: radar
            ? radar.labels.map((label, i) => ({
                metric: label,
                p: Math.round(radar.values[i]),
              })).sort((a, b) => b.p - a.p)
            : [],
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
