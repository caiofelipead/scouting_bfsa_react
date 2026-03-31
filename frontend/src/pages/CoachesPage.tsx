import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend,
} from 'recharts';
import {
  Users, Search, AlertCircle, ChevronDown, SlidersHorizontal,
  Trophy, TrendingUp, TrendingDown, Minus, User,
} from 'lucide-react';
import { useCoaches, useCoachProfile, useCoachCompare, useCoachRanking } from '../hooks/useCoaches';
import type { Coach, CoachFilters, CoachRankingWeights, CoachTacticalRadar, CoachSeason } from '../types/coaches';

// ── Helpers ──

const TACTICAL_LABELS: Record<keyof CoachTacticalRadar, string> = {
  construcao: 'Construção',
  pressing: 'Pressing',
  trans_ofensiva: 'Trans. Ofensiva',
  trans_defensiva: 'Trans. Defensiva',
  altura_bloco: 'Altura Bloco',
  org_ofensiva: 'Org. Ofensiva',
  flexibilidade: 'Flexibilidade',
  uso_base: 'Uso da Base',
  gestao: 'Gestão',
};

const RADAR_COLORS = ['var(--color-accent)', '#3b82f6', '#22c55e'];

function getScoreBadge(score: number) {
  if (score >= 75) return { label: 'Elite', cls: 'score-elite' };
  if (score >= 55) return { label: 'Acima', cls: 'score-above' };
  if (score >= 35) return { label: 'Médio', cls: 'score-average' };
  return { label: 'Abaixo', cls: 'score-below' };
}

function getAprovColor(aprov: number | null) {
  if (aprov === null) return '';
  if (aprov >= 60) return 'text-green-400';
  if (aprov >= 40) return 'text-yellow-400';
  return 'text-red-400';
}

function tacticalToRadarData(tactical: CoachTacticalRadar) {
  return Object.entries(TACTICAL_LABELS).map(([key, label]) => ({
    dimension: label,
    value: tactical[key as keyof CoachTacticalRadar] ?? 0,
  }));
}

function multiRadarData(coaches: Coach[]) {
  return Object.entries(TACTICAL_LABELS).map(([key, label]) => {
    const entry: Record<string, string | number> = { dimension: label };
    coaches.forEach((c, i) => {
      entry[`coach${i}`] = c.tactical[key as keyof CoachTacticalRadar] ?? 0;
    });
    return entry;
  });
}

// ── Skeleton ──

function SkeletonCoaches() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card-glass p-5 space-y-2">
            <div className="skeleton h-4 w-24 rounded" />
            <div className="skeleton h-8 w-16 rounded" />
          </div>
        ))}
      </div>
      <div className="card-glass p-6 space-y-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="skeleton h-10 w-full rounded" />
        ))}
      </div>
    </motion.div>
  );
}

// ── StatBox ──

function StatBox({ label, value, sub, icon }: {
  label: string;
  value: string | number | null;
  sub?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="card-glass p-4 space-y-1">
      <div className="flex items-center gap-2 text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>
        {icon}
        {label}
      </div>
      <div className="text-xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
        {value ?? '—'}
      </div>
      {sub && <div className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>{sub}</div>}
    </div>
  );
}

// ── Tab: Visão Geral ──

function TabOverview({ coaches, onSelect }: {
  coaches: Coach[];
  onSelect: (id: string) => void;
}) {
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const filtered = useMemo(() => {
    let list = coaches;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter((c) => c.nome.toLowerCase().includes(q) || (c.clube_atual || '').toLowerCase().includes(q));
    }
    if (filterStatus) {
      list = list.filter((c) => (c.status || '').toLowerCase() === filterStatus.toLowerCase());
    }
    return list;
  }, [coaches, search, filterStatus]);

  const disponiveis = coaches.filter((c) => (c.status || '').toLowerCase() === 'disponível' || (c.status || '').toLowerCase() === 'disponivel').length;
  const avgAprov = coaches.length > 0
    ? (coaches.reduce((s, c) => s + (c.metricas?.aproveitamento_geral ?? 0), 0) / coaches.length).toFixed(1)
    : '—';

  const statuses = [...new Set(coaches.map((c) => c.status).filter(Boolean))] as string[];

  return (
    <div className="space-y-4">
      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatBox label="Total Cadastrados" value={coaches.length} icon={<Users size={14} />} />
        <StatBox label="Disponíveis" value={disponiveis} icon={<User size={14} />} />
        <StatBox label="Aproveitamento Médio" value={`${avgAprov}%`} icon={<TrendingUp size={14} />} />
      </div>

      {/* Filters */}
      <div className="card-glass p-4 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }} />
          <input
            type="text"
            placeholder="Buscar treinador..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-lg text-sm bg-transparent border"
            style={{
              borderColor: 'var(--color-border-subtle)',
              color: 'var(--color-text-primary)',
            }}
          />
        </div>
        <div className="relative">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="appearance-none pl-3 pr-8 py-2 rounded-lg text-sm bg-transparent border cursor-pointer"
            style={{
              borderColor: 'var(--color-border-subtle)',
              color: 'var(--color-text-primary)',
            }}
          >
            <option value="">Todos os Status</option>
            {statuses.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <ChevronDown size={14} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--color-text-muted)' }} />
        </div>
      </div>

      {/* Table */}
      <div className="card-glass overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              {['Nome', 'Clube Atual', 'Status', 'Licença', 'Formação', 'Aproveitamento', 'Score'].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold" style={{ color: 'var(--color-text-muted)' }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => {
              const badge = getScoreBadge(c.score);
              return (
                <tr
                  key={c.id_treinador}
                  className="table-zebra cursor-pointer transition-colors hover:bg-white/5"
                  style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                  onClick={() => onSelect(c.id_treinador)}
                >
                  <td className="px-4 py-3 font-medium" style={{ color: 'var(--color-text-primary)' }}>
                    {c.nome}
                  </td>
                  <td className="px-4 py-3" style={{ color: 'var(--color-text-secondary)' }}>
                    {c.clube_atual || '—'}
                  </td>
                  <td className="px-4 py-3" style={{ color: 'var(--color-text-secondary)' }}>
                    {c.status || '—'}
                  </td>
                  <td className="px-4 py-3" style={{ color: 'var(--color-text-secondary)' }}>
                    {c.licenca || '—'}
                  </td>
                  <td className="px-4 py-3" style={{ color: 'var(--color-text-secondary)' }}>
                    {c.formacao_pref || '—'}
                  </td>
                  <td className={`px-4 py-3 font-mono ${getAprovColor(c.metricas?.aproveitamento_geral ?? null)}`}>
                    {c.metricas?.aproveitamento_geral != null ? `${c.metricas.aproveitamento_geral}%` : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`${badge.cls} px-2 py-0.5 rounded text-xs font-bold`}>
                      {c.score.toFixed(1)} — {badge.label}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Nenhum treinador encontrado.
          </div>
        )}
      </div>
    </div>
  );
}

// ── Tab: Perfil Individual ──

function TabProfile({ coaches, initialId }: { coaches: Coach[]; initialId?: string | null }) {
  const [selectedId, setSelectedId] = useState<string | null>(initialId ?? null);
  const { data: coach, isLoading } = useCoachProfile(selectedId);

  const radarData = coach ? tacticalToRadarData(coach.tactical) : [];
  const history = coach?.historico ?? [];

  // Build line chart data from history
  const lineData = history
    .filter((s) => s.aproveitamento != null)
    .map((s) => ({
      name: `${s.clube || ''} ${s.temporada || ''}`.trim(),
      aproveitamento: s.aproveitamento,
    }));

  return (
    <div className="space-y-4">
      {/* Coach selector */}
      <div className="card-glass p-4">
        <label className="block text-xs font-medium mb-2" style={{ color: 'var(--color-text-muted)' }}>
          Selecionar Treinador
        </label>
        <div className="relative">
          <select
            value={selectedId || ''}
            onChange={(e) => setSelectedId(e.target.value || null)}
            className="w-full appearance-none pl-3 pr-8 py-2.5 rounded-lg text-sm bg-transparent border cursor-pointer"
            style={{
              borderColor: 'var(--color-border-subtle)',
              color: 'var(--color-text-primary)',
            }}
          >
            <option value="">Escolha um treinador...</option>
            {coaches.map((c) => (
              <option key={c.id_treinador} value={c.id_treinador}>
                {c.nome} {c.clube_atual ? `(${c.clube_atual})` : ''}
              </option>
            ))}
          </select>
          <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--color-text-muted)' }} />
        </div>
      </div>

      {!selectedId && (
        <div className="card-glass p-12 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <Users size={32} className="mx-auto mb-3 opacity-40" />
          <p className="text-sm">Selecione um treinador para ver o perfil completo.</p>
        </div>
      )}

      {isLoading && selectedId && <SkeletonCoaches />}

      {coach && !isLoading && (
        <>
          {/* Stat boxes */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <StatBox
              label="Aproveitamento Pond."
              value={coach.metricas?.aproveitamento_ponderado != null ? `${coach.metricas.aproveitamento_ponderado}%` : '—'}
              icon={<Trophy size={14} />}
            />
            <StatBox
              label="Estabilidade"
              value={coach.metricas?.estabilidade != null ? `${coach.metricas.estabilidade} temp/clube` : '—'}
              icon={<Minus size={14} />}
            />
            <StatBox
              label="Melhor Aprov."
              value={coach.metricas?.melhor_aproveitamento != null ? `${coach.metricas.melhor_aproveitamento}%` : '—'}
              icon={<TrendingUp size={14} />}
            />
            <StatBox
              label="Pior Aprov."
              value={coach.metricas?.pior_aproveitamento != null ? `${coach.metricas.pior_aproveitamento}%` : '—'}
              icon={<TrendingDown size={14} />}
            />
            <StatBox
              label="Taxa Demissão"
              value={coach.metricas?.taxa_demissao != null ? `${coach.metricas.taxa_demissao}%` : '—'}
              icon={<AlertCircle size={14} />}
            />
            <StatBox
              label="Total Jogos"
              value={coach.metricas?.total_jogos ?? '—'}
              sub={`${coach.metricas?.total_vitorias ?? 0}V ${coach.metricas?.total_empates ?? 0}E ${coach.metricas?.total_derrotas ?? 0}D`}
            />
          </div>

          {/* Formations */}
          {(coach.formacao_pref || coach.formacao_alt) && (
            <div className="card-glass p-4">
              <div className="text-xs font-medium mb-2" style={{ color: 'var(--color-text-muted)' }}>Formações</div>
              <div className="flex gap-3">
                {coach.formacao_pref && (
                  <span className="px-3 py-1.5 rounded-lg text-sm font-bold" style={{ background: 'var(--color-accent-glow)', color: 'var(--color-accent)' }}>
                    {coach.formacao_pref}
                  </span>
                )}
                {coach.formacao_alt && (
                  <span className="px-3 py-1.5 rounded-lg text-sm" style={{ background: 'var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
                    {coach.formacao_alt}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Radar + Line chart */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Radar */}
            <div className="card-glass p-5">
              <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-primary)' }}>Perfil Tático</h3>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
                  <PolarGrid stroke="var(--color-border-subtle)" />
                  <PolarAngleAxis dataKey="dimension" tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }} />
                  <PolarRadiusAxis domain={[0, 10]} tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} />
                  <Radar
                    dataKey="value"
                    stroke="var(--color-accent)"
                    fill="var(--color-accent)"
                    fillOpacity={0.2}
                    strokeWidth={2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Line chart: aproveitamento evolution */}
            {lineData.length > 1 && (
              <div className="card-glass p-5">
                <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-primary)' }}>Evolução do Aproveitamento</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={lineData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
                    <XAxis dataKey="name" tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
                    <YAxis domain={[0, 100]} tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{
                        background: 'var(--color-surface-1)',
                        border: '1px solid var(--color-border-subtle)',
                        borderRadius: 8,
                        color: 'var(--color-text-primary)',
                      }}
                      formatter={(v: number) => [`${v.toFixed(1)}%`, 'Aproveitamento']}
                    />
                    <Line
                      type="monotone"
                      dataKey="aproveitamento"
                      stroke="var(--color-accent)"
                      strokeWidth={2}
                      dot={{ fill: 'var(--color-accent)', r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* History table */}
          {history.length > 0 && (
            <div className="card-glass overflow-x-auto">
              <h3 className="text-sm font-semibold p-4 pb-2" style={{ color: 'var(--color-text-primary)' }}>Histórico por Clube/Temporada</h3>
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                    {['Clube', 'Temporada', 'Divisão', 'Jogos', 'V', 'E', 'D', 'Aprov.', 'Posição', 'Saída'].map((h) => (
                      <th key={h} className="px-3 py-2.5 text-left text-xs font-semibold" style={{ color: 'var(--color-text-muted)' }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {history.map((s, i) => (
                    <tr key={i} className="table-zebra" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                      <td className="px-3 py-2.5 font-medium" style={{ color: 'var(--color-text-primary)' }}>{s.clube || '—'}</td>
                      <td className="px-3 py-2.5" style={{ color: 'var(--color-text-secondary)' }}>{s.temporada || '—'}</td>
                      <td className="px-3 py-2.5" style={{ color: 'var(--color-text-secondary)' }}>{s.divisao || '—'}</td>
                      <td className="px-3 py-2.5 font-mono" style={{ color: 'var(--color-text-primary)' }}>{s.jogos ?? '—'}</td>
                      <td className="px-3 py-2.5 font-mono text-green-400">{s.vitorias ?? '—'}</td>
                      <td className="px-3 py-2.5 font-mono text-yellow-400">{s.empates ?? '—'}</td>
                      <td className="px-3 py-2.5 font-mono text-red-400">{s.derrotas ?? '—'}</td>
                      <td className={`px-3 py-2.5 font-mono font-bold ${getAprovColor(s.aproveitamento)}`}>
                        {s.aproveitamento != null ? `${s.aproveitamento}%` : '—'}
                      </td>
                      <td className="px-3 py-2.5" style={{ color: 'var(--color-text-secondary)' }}>{s.posicao_final || '—'}</td>
                      <td className="px-3 py-2.5 text-xs" style={{ color: 'var(--color-text-muted)' }}>{s.motivo_saida || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Observations */}
          {coach.observacoes && (
            <div className="card-glass p-4">
              <div className="text-xs font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>Observações</div>
              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>{coach.observacoes}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Tab: Comparativo ──

function TabCompare({ coaches }: { coaches: Coach[] }) {
  const [selected, setSelected] = useState<string[]>([]);
  const { data: comparison, isLoading } = useCoachCompare(selected);

  const toggleCoach = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 3 ? [...prev, id] : prev,
    );
  };

  const compared = comparison?.coaches ?? [];
  const radarData = compared.length >= 2 ? multiRadarData(compared) : [];

  return (
    <div className="space-y-4">
      {/* Selector */}
      <div className="card-glass p-4">
        <div className="text-xs font-medium mb-2" style={{ color: 'var(--color-text-muted)' }}>
          Selecione até 3 treinadores para comparar
        </div>
        <div className="flex flex-wrap gap-2">
          {coaches.map((c) => {
            const active = selected.includes(c.id_treinador);
            return (
              <button
                key={c.id_treinador}
                onClick={() => toggleCoach(c.id_treinador)}
                className="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer"
                style={{
                  background: active ? 'var(--color-accent-glow)' : 'transparent',
                  color: active ? 'var(--color-accent)' : 'var(--color-text-secondary)',
                  border: `1px solid ${active ? 'var(--color-accent)' : 'var(--color-border-subtle)'}`,
                }}
              >
                {c.nome}
              </button>
            );
          })}
        </div>
      </div>

      {selected.length < 2 && (
        <div className="card-glass p-12 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <Users size={32} className="mx-auto mb-3 opacity-40" />
          <p className="text-sm">Selecione pelo menos 2 treinadores para comparar.</p>
        </div>
      )}

      {isLoading && selected.length >= 2 && <SkeletonCoaches />}

      {compared.length >= 2 && !isLoading && (
        <>
          {/* Overlaid radar */}
          <div className="card-glass p-5">
            <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-primary)' }}>Perfil Tático Comparado</h3>
            <ResponsiveContainer width="100%" height={350}>
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
                <PolarGrid stroke="var(--color-border-subtle)" />
                <PolarAngleAxis dataKey="dimension" tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }} />
                <PolarRadiusAxis domain={[0, 10]} tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} />
                {compared.map((c, i) => (
                  <Radar
                    key={c.id_treinador}
                    name={c.nome}
                    dataKey={`coach${i}`}
                    stroke={RADAR_COLORS[i]}
                    fill={RADAR_COLORS[i]}
                    fillOpacity={0.1}
                    strokeWidth={2}
                  />
                ))}
                <Legend
                  wrapperStyle={{ fontSize: 12, color: 'var(--color-text-secondary)' }}
                  formatter={(_, entry) => {
                    const idx = parseInt((entry.dataKey as string).replace('coach', ''));
                    return compared[idx]?.nome ?? '';
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Side-by-side table */}
          <div className="card-glass overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <th className="px-4 py-3 text-left text-xs font-semibold" style={{ color: 'var(--color-text-muted)' }}>Métrica</th>
                  {compared.map((c, i) => (
                    <th key={i} className="px-4 py-3 text-left text-xs font-semibold" style={{ color: RADAR_COLORS[i] }}>
                      {c.nome}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {/* Tactical dimensions */}
                {Object.entries(TACTICAL_LABELS).map(([key, label]) => {
                  const vals = compared.map((c) => c.tactical[key as keyof CoachTacticalRadar] ?? 0);
                  const maxVal = Math.max(...vals);
                  return (
                    <tr key={key} className="table-zebra" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                      <td className="px-4 py-2.5 text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>{label}</td>
                      {vals.map((v, i) => (
                        <td key={i} className="px-4 py-2.5 font-mono text-sm" style={{
                          color: v === maxVal && maxVal > 0 ? 'var(--color-elite)' : 'var(--color-text-primary)',
                          fontWeight: v === maxVal && maxVal > 0 ? 700 : 400,
                        }}>
                          {v || '—'}
                        </td>
                      ))}
                    </tr>
                  );
                })}
                {/* Key metrics */}
                {[
                  { key: 'aproveitamento_geral', label: 'Aproveitamento Geral', suffix: '%' },
                  { key: 'aproveitamento_ponderado', label: 'Aproveitamento Ponderado', suffix: '%' },
                  { key: 'estabilidade', label: 'Estabilidade', suffix: ' temp/clube' },
                  { key: 'taxa_demissao', label: 'Taxa Demissão', suffix: '%', invert: true },
                  { key: 'total_jogos', label: 'Total Jogos', suffix: '' },
                ].map(({ key, label, suffix, invert }) => {
                  const vals = compared.map((c) => (c.metricas as Record<string, number | null>)?.[key] ?? null);
                  const numVals = vals.filter((v): v is number => v !== null);
                  const bestVal = invert ? Math.min(...numVals) : Math.max(...numVals);
                  return (
                    <tr key={key} className="table-zebra" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                      <td className="px-4 py-2.5 text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>{label}</td>
                      {vals.map((v, i) => (
                        <td key={i} className="px-4 py-2.5 font-mono text-sm" style={{
                          color: v === bestVal && numVals.length > 1 ? 'var(--color-elite)' : 'var(--color-text-primary)',
                          fontWeight: v === bestVal && numVals.length > 1 ? 700 : 400,
                        }}>
                          {v != null ? `${v}${suffix}` : '—'}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

// ── Tab: Ranking ──

function TabRanking({ coaches }: { coaches: Coach[] }) {
  const [weights, setWeights] = useState<CoachRankingWeights>({
    w_aproveitamento: 0.30,
    w_tatico: 0.25,
    w_gestao: 0.15,
    w_uso_base: 0.10,
    w_estabilidade: 0.10,
    w_flexibilidade: 0.10,
  });
  const [filters] = useState<CoachFilters>({});
  const { data, isLoading } = useCoachRanking(weights, filters);

  const ranked = data?.coaches ?? [];

  const weightSliders: { key: keyof CoachRankingWeights; label: string }[] = [
    { key: 'w_aproveitamento', label: 'Aproveitamento' },
    { key: 'w_tatico', label: 'Perfil Tático' },
    { key: 'w_gestao', label: 'Gestão' },
    { key: 'w_uso_base', label: 'Uso da Base' },
    { key: 'w_estabilidade', label: 'Estabilidade' },
    { key: 'w_flexibilidade', label: 'Flexibilidade' },
  ];

  return (
    <div className="space-y-4">
      {/* Weight sliders */}
      <div className="card-glass p-5">
        <div className="flex items-center gap-2 mb-4">
          <SlidersHorizontal size={16} style={{ color: 'var(--color-accent)' }} />
          <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>Pesos do Score Composto</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-3">
          {weightSliders.map(({ key, label }) => (
            <div key={key} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span style={{ color: 'var(--color-text-secondary)' }}>{label}</span>
                <span className="font-mono" style={{ color: 'var(--color-text-primary)' }}>
                  {((weights[key] ?? 0) * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={100}
                value={(weights[key] ?? 0) * 100}
                onChange={(e) => setWeights({ ...weights, [key]: parseInt(e.target.value) / 100 })}
                className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
                style={{ accentColor: 'var(--color-accent)' }}
              />
            </div>
          ))}
        </div>
      </div>

      {isLoading && <SkeletonCoaches />}

      {/* Ranking table */}
      {!isLoading && (
        <div className="card-glass overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                {['#', 'Nome', 'Clube Atual', 'Licença', 'Formação', 'Aprov. Geral', 'Aprov. Pond.', 'Score'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold" style={{ color: 'var(--color-text-muted)' }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ranked.map((c, i) => {
                const badge = getScoreBadge(c.score);
                return (
                  <tr key={c.id_treinador} className="table-zebra" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                    <td className="px-4 py-3 font-mono text-xs" style={{ color: 'var(--color-text-muted)' }}>
                      {c.rank ?? i + 1}
                    </td>
                    <td className="px-4 py-3 font-medium" style={{ color: 'var(--color-text-primary)' }}>
                      {c.nome}
                    </td>
                    <td className="px-4 py-3" style={{ color: 'var(--color-text-secondary)' }}>
                      {c.clube_atual || '—'}
                    </td>
                    <td className="px-4 py-3" style={{ color: 'var(--color-text-secondary)' }}>
                      {c.licenca || '—'}
                    </td>
                    <td className="px-4 py-3" style={{ color: 'var(--color-text-secondary)' }}>
                      {c.formacao_pref || '—'}
                    </td>
                    <td className={`px-4 py-3 font-mono ${getAprovColor(c.metricas?.aproveitamento_geral ?? null)}`}>
                      {c.metricas?.aproveitamento_geral != null ? `${c.metricas.aproveitamento_geral}%` : '—'}
                    </td>
                    <td className={`px-4 py-3 font-mono ${getAprovColor(c.metricas?.aproveitamento_ponderado ?? null)}`}>
                      {c.metricas?.aproveitamento_ponderado != null ? `${c.metricas.aproveitamento_ponderado}%` : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`${badge.cls} px-2 py-0.5 rounded text-xs font-bold`}>
                        {c.score.toFixed(1)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {ranked.length === 0 && (
            <div className="p-8 text-center text-sm" style={{ color: 'var(--color-text-muted)' }}>
              Nenhum treinador encontrado no ranking.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Page ──

type CoachTab = 'overview' | 'profile' | 'compare' | 'ranking';

export default function CoachesPage() {
  const [activeTab, setActiveTab] = useState<CoachTab>('overview');
  const [profileSelect, setProfileSelect] = useState<string | null>(null);
  const { data, isLoading, error } = useCoaches();

  const coaches = data?.coaches ?? [];

  const tabs: { id: CoachTab; label: string }[] = [
    { id: 'overview', label: 'Visão Geral' },
    { id: 'profile', label: 'Perfil Individual' },
    { id: 'compare', label: 'Comparativo' },
    { id: 'ranking', label: 'Ranking' },
  ];

  const handleSelectFromOverview = (id: string) => {
    setProfileSelect(id);
    setActiveTab('profile');
  };

  if (error) {
    return (
      <div className="card-glass p-8 text-center space-y-3">
        <AlertCircle size={32} className="mx-auto" style={{ color: 'var(--color-accent)' }} />
        <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          Erro ao carregar treinadores. Tente novamente.
        </p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
          <Users size={22} strokeWidth={1.5} style={{ color: 'var(--color-accent)' }} />
          Avaliação de Treinadores
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>
          Análise tática, histórica e comparativa de treinadores
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 p-1 rounded-xl" style={{ background: 'var(--color-surface-1)' }}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className="flex-1 px-4 py-2 rounded-lg text-xs font-medium transition-all cursor-pointer"
            style={{
              background: activeTab === tab.id ? 'var(--color-accent-glow)' : 'transparent',
              color: activeTab === tab.id ? 'var(--color-accent)' : 'var(--color-text-secondary)',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {isLoading ? (
        <SkeletonCoaches />
      ) : (
        <>
          {activeTab === 'overview' && <TabOverview coaches={coaches} onSelect={handleSelectFromOverview} />}
          {activeTab === 'profile' && <TabProfileWrapper coaches={coaches} preselected={profileSelect} />}
          {activeTab === 'compare' && <TabCompare coaches={coaches} />}
          {activeTab === 'ranking' && <TabRanking coaches={coaches} />}
        </>
      )}
    </motion.div>
  );
}

// Wrapper to handle preselected coach for profile tab
function TabProfileWrapper({ coaches, preselected }: { coaches: Coach[]; preselected: string | null }) {
  return <TabProfile coaches={coaches} initialId={preselected} key={preselected} />;
}
