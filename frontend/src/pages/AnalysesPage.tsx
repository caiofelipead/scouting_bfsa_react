import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Eye,
  Search,
  AlertCircle,
  FileText,
  ExternalLink,
  Video,
  DollarSign,
  User,
  ChevronDown,
  ChevronRight,
  Activity,
  BarChart3,
  X,
  MapPin,
  Filter,
  Unlink,
  Link2,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import api, { proxyImageUrl } from '../lib/api';
import { getScoreColor } from '../lib/utils';
import { usePlayerProfile, useSkillCornerPlayer, useSkillCornerSearch } from '../hooks/usePlayers';
import RadarChart from '../components/RadarChart';

// ── Types ──

interface AnalysesPlayer {
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

// ── Constants ──

const SCORE_LABELS: Record<string, string> = {
  'Técnica': 'Tecnica',
  'Físico': 'Fisico',
  'Tática': 'Tatica',
  'Mental': 'Mental',
  'Nota_Desempenho': 'Desempenho',
  'Potencial': 'Potencial',
};

const LINK_ICONS: Record<string, { label: string }> = {
  'ogol': { label: 'ogol' },
  'TM': { label: 'Transfermarkt' },
  'Vídeo': { label: 'Video' },
  'Relatório': { label: 'Relatorio' },
};

function getAnalysisScoreColor(score: number): string {
  // Proportional color scale for 1-5 range
  // 1=red, 2=orange, 3=green, 4=bright green, 5=emerald
  const clamped = Math.max(1, Math.min(5, score));
  const t = (clamped - 1) / 4; // 0 to 1
  // Shift hue so 3.0 (~t=0.5) already lands on green (120°)
  const hue = t * 150; // 0° (red) → 150° (teal-green)
  const sat = 70 + (1 - Math.abs(t - 0.5) * 2) * 15;
  const light = 45 + (1 - Math.abs(t - 0.5) * 2) * 5;
  return `hsl(${hue}, ${sat}%, ${light}%)`;
}

function getModeloStyle(modelo: string) {
  if (modelo === 'Descartado') return { bg: 'rgba(239,68,68,0.1)', color: '#ef4444', border: 'rgba(239,68,68,0.2)' };
  if (modelo === 'Livre') return { bg: 'rgba(34,197,94,0.1)', color: '#22c55e', border: 'rgba(34,197,94,0.2)' };
  return { bg: 'rgba(59,130,246,0.1)', color: '#3b82f6', border: 'rgba(59,130,246,0.2)' };
}

function getPerfilStyle(perfil: string) {
  const p = perfil.toLowerCase();
  if (p.includes('titular')) return { bg: 'rgba(34,197,94,0.1)', color: '#22c55e', border: 'rgba(34,197,94,0.2)' };
  if (p.includes('rota')) return { bg: 'rgba(59,130,246,0.1)', color: '#3b82f6', border: 'rgba(59,130,246,0.2)' };
  if (p.includes('aposta')) return { bg: 'rgba(168,85,247,0.1)', color: '#a855f7', border: 'rgba(168,85,247,0.2)' };
  if (p.includes('reserva')) return { bg: 'rgba(234,179,8,0.1)', color: '#eab308', border: 'rgba(234,179,8,0.2)' };
  return { bg: 'rgba(107,114,128,0.1)', color: '#9ca3af', border: 'rgba(107,114,128,0.2)' };
}

// ── Hook ──

function useAnalysesPlayers(search: string) {
  return useQuery({
    queryKey: ['analyses-players', search],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (search.trim()) params.search = search.trim();
      const r = await api.get('/analyses/players', { params });
      return r.data as { players: AnalysesPlayer[]; total: number };
    },
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 10000),
  });
}

// ── SkillCorner Identity Resolver ──

function ScIdentityResolver({
  scOverride,
  onOverride,
}: {
  scOverride: string | null;
  onOverride: (name: string | null) => void;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const { data: results } = useSkillCornerSearch(open ? query : '');

  return (
    <div>
      <div className="flex items-center gap-2">
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer"
          style={{
            background: open ? 'var(--color-accent-glow)' : 'var(--color-surface-2)',
            color: open ? 'var(--color-accent)' : 'var(--color-text-muted)',
            border: `1px solid ${open ? 'rgba(220,38,38,0.3)' : 'var(--color-border-subtle)'}`,
          }}
        >
          <Search size={11} />
          Vincular SkillCorner
        </button>
        {scOverride && (
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] px-2 py-0.5 rounded" style={{ background: 'rgba(34,197,94,0.1)', color: '#22c55e', border: '1px solid rgba(34,197,94,0.2)' }}>
              {scOverride}
            </span>
            <button
              onClick={() => { onOverride(null); setQuery(''); setOpen(false); }}
              className="p-0.5 rounded cursor-pointer hover:bg-white/5"
              style={{ color: 'var(--color-text-muted)' }}
            >
              <X size={12} />
            </button>
          </div>
        )}
      </div>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mt-2">
            <input
              type="text"
              placeholder="Buscar jogador na base SkillCorner..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full px-3 py-2 rounded text-xs outline-none"
              style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
              autoFocus
            />
            {results && results.length > 0 && (
              <div className="mt-1 rounded overflow-hidden max-h-48 overflow-y-auto" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)' }}>
                {results.map((r) => (
                  <button
                    key={`${r.player_name}-${r.team_name}`}
                    onClick={() => { onOverride(r.player_name); setOpen(false); setQuery(''); }}
                    className="w-full text-left px-3 py-2 text-xs hover:bg-white/5 transition-colors cursor-pointer flex items-center justify-between"
                    style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                  >
                    <span style={{ color: 'var(--color-text-primary)' }}>{r.player_name}</span>
                    <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                      {r.team_name} {r.position_group ? `· ${r.position_group}` : ''}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── WyScout Identity Resolver ──

function WsIdentityResolver({
  wsOverride,
  onOverride,
}: {
  wsOverride: string | null;
  onOverride: (name: string | null) => void;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const { data: results } = useQuery({
    queryKey: ['ws-search', query],
    queryFn: async () => {
      const res = await api.get('/players', { params: { search: query, limit: 10 } });
      return res.data as { total: number; players: { name: string; display_name: string | null; team: string | null; position: string | null }[] };
    },
    enabled: open && query.length >= 2,
    staleTime: 10 * 60 * 1000,
  });

  return (
    <div>
      <div className="flex items-center gap-2">
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer"
          style={{
            background: open ? 'var(--color-accent-glow)' : 'var(--color-surface-2)',
            color: open ? 'var(--color-accent)' : 'var(--color-text-muted)',
            border: `1px solid ${open ? 'rgba(220,38,38,0.3)' : 'var(--color-border-subtle)'}`,
          }}
        >
          <Search size={11} />
          Buscar no WyScout
        </button>
        {wsOverride && (
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] px-2 py-0.5 rounded" style={{ background: 'rgba(34,197,94,0.1)', color: '#22c55e', border: '1px solid rgba(34,197,94,0.2)' }}>
              {wsOverride}
            </span>
            <button
              onClick={() => { onOverride(null); setQuery(''); setOpen(false); }}
              className="p-0.5 rounded cursor-pointer hover:bg-white/5"
              style={{ color: 'var(--color-text-muted)' }}
            >
              <X size={12} />
            </button>
          </div>
        )}
      </div>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mt-2">
            <input
              type="text"
              placeholder="Buscar jogador na base WyScout..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full px-3 py-2 rounded text-xs outline-none"
              style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
              autoFocus
            />
            {results?.players && results.players.length > 0 && (
              <div className="mt-1 rounded overflow-hidden max-h-48 overflow-y-auto" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)' }}>
                {results.players.map((r) => (
                  <button
                    key={r.display_name || r.name}
                    onClick={() => { onOverride(r.display_name || r.name); setOpen(false); setQuery(''); }}
                    className="w-full text-left px-3 py-2 text-xs hover:bg-white/5 transition-colors cursor-pointer flex items-center justify-between"
                    style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                  >
                    <span style={{ color: 'var(--color-text-primary)' }}>{r.display_name || r.name}</span>
                    <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                      {r.team} {r.position ? `· ${r.position}` : ''}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Detail panel tabs ──

type DetailTab = 'analise' | 'wyscout' | 'skillcorner';

// ── WyScout Profile Mini ──

function WyScoutProfileSection({
  displayName,
  wsOverride,
  onOverrideChange,
  autoMatchCleared,
  onClearAutoMatch,
}: {
  displayName: string | null;
  wsOverride: string | null;
  onOverrideChange: (v: string | null) => void;
  autoMatchCleared: boolean;
  onClearAutoMatch: () => void;
}) {
  // If auto match was cleared and no manual override, show empty state
  const effectiveName = wsOverride || (autoMatchCleared ? null : displayName);
  const { data: profile, isLoading } = usePlayerProfile(effectiveName);

  // Show auto match suggestion when cleared
  const autoMatchSuggestion = autoMatchCleared && displayName && !wsOverride;

  if (!effectiveName) return (
    <div className="space-y-4 p-1">
      <div className="py-6 text-center" style={{ color: 'var(--color-text-muted)' }}>
        <BarChart3 size={24} className="mx-auto mb-2 opacity-30" />
        <p className="text-xs">{autoMatchSuggestion ? 'Match automatico removido' : 'Nenhum match WyScout automatico encontrado'}</p>
        <p className="text-[10px] mt-1">Use a busca abaixo para vincular manualmente</p>
      </div>
      {/* Show suggestion to re-link auto match */}
      {autoMatchSuggestion && (
        <button
          onClick={() => onOverrideChange(displayName)}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded text-xs transition-colors cursor-pointer hover:bg-white/5"
          style={{ border: '1px solid rgba(59,130,246,0.3)', color: '#3b82f6' }}
        >
          <Link2 size={12} />
          Restaurar match: {displayName}
        </button>
      )}
      <WsIdentityResolver wsOverride={wsOverride} onOverride={onOverrideChange} />
    </div>
  );

  if (isLoading) return <div className="p-6"><div className="skeleton h-48 rounded" /></div>;
  if (!profile) return (
    <div className="space-y-4 p-1">
      <div className="p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
        <BarChart3 size={28} className="mx-auto mb-2 opacity-30" />
        <p className="text-sm">Perfil WyScout nao encontrado</p>
      </div>
      <WsIdentityResolver wsOverride={wsOverride} onOverride={onOverrideChange} />
    </div>
  );

  const { summary, percentiles, indices, scout_score, performance_class, projection_score } = profile;

  const percEntries = Object.entries(percentiles).filter(([, v]) => v != null);
  const indEntries = Object.entries(indices).filter(([, v]) => v != null);

  return (
    <div className="space-y-4 p-1">
      {/* Summary header with unlink button */}
      <div className="flex items-center gap-3">
        {summary.photo_url ? (
          <img src={proxyImageUrl(summary.photo_url)!} alt={summary.display_name || summary.name} className="w-14 h-14 rounded-full object-cover" style={{ border: '2px solid var(--color-border-subtle)' }} onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none' }} />
        ) : (
          <div className="w-14 h-14 rounded-full flex items-center justify-center" style={{ background: 'var(--color-surface-2)', border: '2px solid var(--color-border-subtle)' }}>
            <User size={24} style={{ color: 'var(--color-text-muted)' }} />
          </div>
        )}
        <div className="flex-1">
          <div className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>{summary.display_name || summary.name}</div>
          <div className="text-[10px] flex flex-wrap gap-2" style={{ color: 'var(--color-text-muted)' }}>
            {summary.team && <span>{summary.team}</span>}
            {summary.position && <span className="px-1.5 py-0.5 rounded" style={{ background: 'var(--color-accent-glow)', color: 'var(--color-accent)' }}>{summary.position}</span>}
            {summary.age && <span>{summary.age}a</span>}
            {summary.minutes_played && <span>{summary.minutes_played}min</span>}
          </div>
        </div>
        {/* Unlink button */}
        <button
          onClick={() => {
            onOverrideChange(null);
            onClearAutoMatch();
          }}
          className="flex items-center gap-1 px-2 py-1.5 rounded text-[10px] transition-colors cursor-pointer hover:bg-white/5"
          style={{ color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)' }}
          title="Remover vinculo"
        >
          <Unlink size={11} />
          Desvincular
        </button>
      </div>

      {/* SSP + Projection */}
      <div className="flex flex-wrap gap-3">
        {scout_score !== null && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}>
            <span className="text-[10px] uppercase" style={{ color: 'var(--color-text-muted)' }}>SSP</span>
            <span className="text-lg font-[var(--font-mono)] font-bold" style={{ color: getScoreColor(scout_score) }}>{scout_score.toFixed(1)}</span>
            {performance_class && <span className="text-[9px] uppercase font-semibold" style={{ color: 'var(--color-text-muted)' }}>{performance_class}</span>}
          </div>
        )}
        {projection_score !== null && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}>
            <span className="text-[10px] uppercase" style={{ color: 'var(--color-text-muted)' }}>PDI</span>
            <span className="text-lg font-[var(--font-mono)] font-bold" style={{ color: getScoreColor(projection_score) }}>{projection_score.toFixed(1)}</span>
          </div>
        )}
      </div>

      {/* Radar chart for percentiles */}
      {percEntries.length >= 3 && (
        <div>
          <div className="text-[9px] font-[var(--font-display)] tracking-[0.15em] uppercase mb-2" style={{ color: 'var(--color-text-muted)' }}>RADAR DE PERCENTIS</div>
          <div className="max-w-[300px] mx-auto">
            <RadarChart
              labels={percEntries.slice(0, 12).map(([k]) => k.replace(/_/g, ' '))}
              values={percEntries.slice(0, 12).map(([, v]) => Math.min(v, 100))}
              size={300}
            />
          </div>
        </div>
      )}

      {/* Indices as horizontal bar chart */}
      {indEntries.length > 0 && (
        <div>
          <div className="text-[9px] font-[var(--font-display)] tracking-[0.15em] uppercase mb-2" style={{ color: 'var(--color-text-muted)' }}>INDICES COMPOSTOS</div>
          <div className="space-y-2">
            {indEntries.map(([name, value]) => (
              <div key={name}>
                <div className="flex items-center justify-between mb-0.5">
                  <span className="text-[10px]" style={{ color: 'var(--color-text-secondary)' }}>{name}</span>
                  <span className="text-xs font-[var(--font-mono)] font-semibold" style={{ color: getScoreColor(value) }}>{value.toFixed(1)}</span>
                </div>
                <div className="h-2 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-2)' }}>
                  <motion.div
                    className="h-full rounded-full"
                    style={{ background: getScoreColor(value) }}
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(value, 100)}%` }}
                    transition={{ duration: 0.6, ease: 'easeOut' }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Percentiles table */}
      {percEntries.length > 0 && (
        <div>
          <div className="text-[9px] font-[var(--font-display)] tracking-[0.15em] uppercase mb-2" style={{ color: 'var(--color-text-muted)' }}>TODOS OS PERCENTIS</div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            {percEntries.map(([name, value]) => (
              <div key={name} className="flex items-center justify-between text-[10px]">
                <span style={{ color: 'var(--color-text-secondary)' }}>{name.replace(/_/g, ' ')}</span>
                <span className="font-[var(--font-mono)] font-semibold" style={{ color: getScoreColor(value) }}>P{Math.round(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Manual override */}
      <WsIdentityResolver wsOverride={wsOverride} onOverride={onOverrideChange} />
    </div>
  );
}

// ── SkillCorner Profile Mini ──

function SkillCornerProfileSection({ displayName, scOverride, onOverrideChange }: { displayName: string; scOverride: string | null; onOverrideChange: (v: string | null) => void }) {
  const { data: scProfile, isLoading } = useSkillCornerPlayer(displayName, scOverride);

  if (isLoading) return <div className="p-6"><div className="skeleton h-48 rounded" /></div>;

  const indices = scProfile?.indices ?? {};
  const physical = scProfile?.physical ?? {};
  const indicesEntries = Object.entries(indices);
  const physicalEntries = Object.entries(physical);

  // Find max physical value for relative bar sizing
  const maxPhysical = physicalEntries.length > 0 ? Math.max(...physicalEntries.map(([, v]) => v)) : 1;

  return (
    <div className="space-y-4 p-1">
      {/* Identity resolver */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MapPin size={12} style={{ color: 'var(--color-accent)' }} />
          <span className="text-[10px] font-[var(--font-display)] tracking-[0.15em] uppercase" style={{ color: 'var(--color-text-muted)' }}>
            RESOLUCAO DE IDENTIDADE
          </span>
        </div>
        {scProfile?.found && (
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-2 py-0.5 rounded" style={{ background: 'rgba(34,197,94,0.1)', color: '#22c55e', border: '1px solid rgba(34,197,94,0.2)' }}>
              MATCH
            </span>
            <button
              onClick={() => onOverrideChange(null)}
              className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] transition-colors cursor-pointer hover:bg-white/5"
              style={{ color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)' }}
              title="Remover vinculo"
            >
              <Unlink size={10} />
            </button>
          </div>
        )}
      </div>

      {scProfile?.found && (
        <div className="flex flex-wrap gap-3 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
          <span>SC: <strong style={{ color: 'var(--color-text-primary)' }}>{scProfile.matched_name}</strong></span>
          {scProfile.matched_team && <span>Time: {scProfile.matched_team}</span>}
          {scProfile.matched_position && <span>Pos: {scProfile.matched_position}</span>}
        </div>
      )}

      <ScIdentityResolver scOverride={scOverride} onOverride={onOverrideChange} />

      {scProfile?.found && (
        <>
          {/* Indices - Radar + bars */}
          {indicesEntries.length > 0 && (
            <div>
              <div className="text-[9px] font-[var(--font-display)] tracking-[0.15em] uppercase mb-2" style={{ color: 'var(--color-text-muted)' }}>
                INDICES SC {scProfile.position ? `(${scProfile.position})` : ''}
              </div>
              {indicesEntries.length >= 3 && (
                <div className="max-w-[280px] mx-auto mb-3">
                  <RadarChart
                    labels={indicesEntries.map(([k]) => k.replace(/ index$/i, ''))}
                    values={indicesEntries.map(([, v]) => Math.min(v * 10, 100))}
                    size={280}
                  />
                </div>
              )}
              <div className="space-y-2">
                {indicesEntries.map(([name, value], i) => (
                  <div key={name}>
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-[10px]" style={{ color: 'var(--color-text-secondary)' }}>{name.replace(/ index$/i, '')}</span>
                      <span className="text-xs font-[var(--font-mono)] font-semibold" style={{ color: getScoreColor(value * 10) }}>{value.toFixed(2)}</span>
                    </div>
                    <div className="h-2 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-2)' }}>
                      <motion.div
                        className="h-full rounded-full"
                        style={{ background: getScoreColor(value * 10) }}
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(value * 10, 100)}%` }}
                        transition={{ duration: 0.5, delay: i * 0.05, ease: 'easeOut' }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Physical - horizontal bar chart */}
          {physicalEntries.length > 0 && (
            <div>
              <div className="text-[9px] font-[var(--font-display)] tracking-[0.15em] uppercase mb-2" style={{ color: 'var(--color-text-muted)' }}>DADOS FISICOS</div>
              <div className="space-y-2">
                {physicalEntries.map(([name, value], i) => (
                  <div key={name}>
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-[10px]" style={{ color: 'var(--color-text-secondary)' }}>{name.replace(/_/g, ' ').replace(/per 90/i, '/90')}</span>
                      <span className="text-xs font-[var(--font-mono)] font-bold" style={{ color: 'var(--color-text-primary)' }}>{value.toFixed(2)}</span>
                    </div>
                    <div className="h-2 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-2)' }}>
                      <motion.div
                        className="h-full rounded-full"
                        style={{ background: 'var(--color-accent)' }}
                        initial={{ width: 0 }}
                        animate={{ width: `${(value / maxPhysical) * 100}%` }}
                        transition={{ duration: 0.5, delay: i * 0.04, ease: 'easeOut' }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {!scProfile?.found && !isLoading && (
        <div className="py-6 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <Activity size={24} className="mx-auto mb-2 opacity-30" />
          <p className="text-xs">Nenhum dado SkillCorner encontrado</p>
          <p className="text-[10px] mt-1">Use "Vincular SkillCorner" para buscar manualmente</p>
        </div>
      )}
    </div>
  );
}

// ── Main page ──

export default function AnalysesPage() {
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState<AnalysesPlayer | null>(null);
  const [activeTab, setActiveTab] = useState<DetailTab>('analise');
  const [scOverride, setScOverride] = useState<string | null>(null);
  const [wsOverride, setWsOverride] = useState<string | null>(null);
  const [wsAutoCleared, setWsAutoCleared] = useState(false);
  const [filterPosition, setFilterPosition] = useState('');
  const [filterModelo, setFilterModelo] = useState('');
  const [filterLiga, setFilterLiga] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 250);
    return () => clearTimeout(timer);
  }, [search]);

  const { data, isLoading, error } = useAnalysesPlayers(debouncedSearch);
  const allPlayers = data?.players ?? [];

  // Extract unique filter options from data
  const filterOptions = useMemo(() => {
    const positions = new Set<string>();
    const perfis = new Set<string>();
    const ligas = new Set<string>();
    for (const p of allPlayers) {
      if (p.posicao) positions.add(p.posicao);
      if (p.perfil) perfis.add(p.perfil);
      if (p.liga) ligas.add(p.liga);
    }
    return {
      positions: [...positions].sort(),
      perfis: [...perfis].sort(),
      ligas: [...ligas].sort(),
    };
  }, [allPlayers]);

  // Apply client-side filters
  const players = useMemo(() => {
    return allPlayers.filter((p) => {
      if (filterPosition && p.posicao !== filterPosition) return false;
      if (filterModelo && p.perfil !== filterModelo) return false;
      if (filterLiga && p.liga !== filterLiga) return false;
      return true;
    });
  }, [allPlayers, filterPosition, filterModelo, filterLiga]);

  const activeFilterCount = [filterPosition, filterModelo, filterLiga].filter(Boolean).length;

  // Reset overrides when player changes
  useEffect(() => {
    setScOverride(null);
    setWsOverride(null);
    setWsAutoCleared(false);
    setActiveTab('analise');
  }, [selectedPlayer?.nome]);

  // Count by modelo
  const modeloCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const p of players) {
      const m = p.modelo || 'Sem modelo';
      counts[m] = (counts[m] || 0) + 1;
    }
    return counts;
  }, [players]);

  return (
    <div className="flex gap-4 h-[calc(100vh-7rem)]">
      {/* ── Left panel: player list ── */}
      <div className="w-[380px] min-w-[320px] flex flex-col card-glass overflow-hidden">
        {/* Header */}
        <div className="p-4 pb-3" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
          <h1 className="font-[var(--font-display)] text-lg font-bold tracking-tight flex items-center gap-2">
            <Eye size={18} style={{ color: 'var(--color-accent)' }} />
            Analises do Scout
          </h1>
          <p className="text-[10px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
            {players.length}{players.length !== (data?.total ?? 0) ? ` de ${data?.total ?? 0}` : ''} jogadores analisados
          </p>

          {/* Search + Filter toggle */}
          <div className="flex items-center gap-2 mt-3">
            <div className="relative flex-1">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }} />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar jogador..."
                className="w-full pl-9 pr-3 py-2 rounded text-xs outline-none"
                style={{
                  background: 'var(--color-surface-2)',
                  border: '1px solid var(--color-border-subtle)',
                  color: 'var(--color-text-primary)',
                }}
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-1 px-2.5 py-2 rounded text-xs transition-colors cursor-pointer shrink-0"
              style={{
                background: showFilters || activeFilterCount > 0 ? 'var(--color-accent-glow)' : 'var(--color-surface-2)',
                border: `1px solid ${showFilters || activeFilterCount > 0 ? 'rgba(220,38,38,0.3)' : 'var(--color-border-subtle)'}`,
                color: showFilters || activeFilterCount > 0 ? 'var(--color-accent)' : 'var(--color-text-muted)',
              }}
            >
              <Filter size={13} />
              {activeFilterCount > 0 && <span className="text-[9px] font-bold">{activeFilterCount}</span>}
            </button>
          </div>

          {/* Filters panel */}
          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="pt-3 space-y-2">
                  {/* Position filter */}
                  <div>
                    <label className="text-[9px] uppercase tracking-wider block mb-1" style={{ color: 'var(--color-text-muted)' }}>Posicao</label>
                    <select
                      value={filterPosition}
                      onChange={(e) => setFilterPosition(e.target.value)}
                      className="w-full px-2.5 py-1.5 rounded text-xs outline-none cursor-pointer"
                      style={{
                        background: 'var(--color-surface-2)',
                        border: '1px solid var(--color-border-subtle)',
                        color: filterPosition ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                      }}
                    >
                      <option value="">Todas posicoes</option>
                      {filterOptions.positions.map((pos) => (
                        <option key={pos} value={pos}>{pos}</option>
                      ))}
                    </select>
                  </div>

                  {/* Perfil/Elenco filter */}
                  <div>
                    <label className="text-[9px] uppercase tracking-wider block mb-1" style={{ color: 'var(--color-text-muted)' }}>Perfil no Elenco</label>
                    <select
                      value={filterModelo}
                      onChange={(e) => setFilterModelo(e.target.value)}
                      className="w-full px-2.5 py-1.5 rounded text-xs outline-none cursor-pointer"
                      style={{
                        background: 'var(--color-surface-2)',
                        border: '1px solid var(--color-border-subtle)',
                        color: filterModelo ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                      }}
                    >
                      <option value="">Todos perfis</option>
                      {filterOptions.perfis.map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                  </div>

                  {/* Liga filter */}
                  <div>
                    <label className="text-[9px] uppercase tracking-wider block mb-1" style={{ color: 'var(--color-text-muted)' }}>Liga</label>
                    <select
                      value={filterLiga}
                      onChange={(e) => setFilterLiga(e.target.value)}
                      className="w-full px-2.5 py-1.5 rounded text-xs outline-none cursor-pointer"
                      style={{
                        background: 'var(--color-surface-2)',
                        border: '1px solid var(--color-border-subtle)',
                        color: filterLiga ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                      }}
                    >
                      <option value="">Todas ligas</option>
                      {filterOptions.ligas.map((l) => (
                        <option key={l} value={l}>{l}</option>
                      ))}
                    </select>
                  </div>

                  {/* Clear filters */}
                  {activeFilterCount > 0 && (
                    <button
                      onClick={() => { setFilterPosition(''); setFilterModelo(''); setFilterLiga(''); }}
                      className="w-full text-[10px] py-1.5 rounded cursor-pointer transition-colors hover:bg-white/5"
                      style={{ color: 'var(--color-accent)', border: '1px solid rgba(220,38,38,0.2)' }}
                    >
                      Limpar filtros
                    </button>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Player list */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="px-4 py-3" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                <div className="skeleton h-10 rounded" />
              </div>
            ))
          ) : error ? (
            <div className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-xs" style={{ color: '#ef4444' }}>
                <AlertCircle size={14} />
                Erro ao carregar dados
              </div>
              <p className="text-[10px] pl-5" style={{ color: 'var(--color-text-muted)' }}>
                {(error as any)?.response?.data?.detail || (error as Error)?.message || 'Erro desconhecido'}
              </p>
            </div>
          ) : players.length === 0 ? (
            <div className="p-8 text-center text-xs" style={{ color: 'var(--color-text-muted)' }}>
              {search ? 'Nenhum jogador encontrado' : 'Nenhuma analise registrada'}
            </div>
          ) : (
            players.map((p, i) => {
              const isSelected = selectedPlayer?.nome === p.nome;
              const pStyle = p.perfil ? getPerfilStyle(p.perfil) : null;
              const avgScore = Object.values(p.scores).length > 0
                ? Object.values(p.scores).reduce((a, b) => a + b, 0) / Object.values(p.scores).length
                : null;

              return (
                <motion.button
                  key={p.nome + i}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.015 }}
                  onClick={() => setSelectedPlayer(p)}
                  className="w-full text-left px-4 py-3 transition-colors cursor-pointer flex items-center gap-3"
                  style={{
                    borderBottom: '1px solid var(--color-border-subtle)',
                    background: isSelected ? 'var(--color-accent-glow)' : 'transparent',
                    borderLeft: isSelected ? '3px solid var(--color-accent)' : '3px solid transparent',
                  }}
                >
                  {/* Photo */}
                  {p.foto ? (
                    <img src={proxyImageUrl(p.foto)!} alt={p.nome} className="w-10 h-10 rounded-full object-cover shrink-0" style={{ border: '2px solid var(--color-border-subtle)' }} onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none' }} />
                  ) : (
                    <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ background: 'var(--color-surface-2)', border: '2px solid var(--color-border-subtle)' }}>
                      <User size={16} style={{ color: 'var(--color-text-muted)' }} />
                    </div>
                  )}

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium truncate" style={{ color: 'var(--color-text-primary)' }}>{p.nome}</span>
                      {pStyle && (
                        <span className="text-[8px] px-1.5 py-0.5 rounded-full uppercase font-semibold shrink-0" style={{ background: pStyle.bg, color: pStyle.color, border: `1px solid ${pStyle.border}` }}>
                          {p.perfil}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-[10px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                      {p.posicao && <span>{p.posicao}</span>}
                      {p.equipe && <span>{p.equipe}</span>}
                      {p.idade && <span>{p.idade}a</span>}
                    </div>
                  </div>

                  {/* Avg score */}
                  {avgScore !== null && (
                    <span className="text-sm font-[var(--font-mono)] font-bold shrink-0" style={{ color: getAnalysisScoreColor(avgScore) }}>
                      {avgScore.toFixed(1)}
                    </span>
                  )}
                </motion.button>
              );
            })
          )}
        </div>
      </div>

      {/* ── Right panel: detail ── */}
      <div className="flex-1 card-glass overflow-hidden flex flex-col">
        {!selectedPlayer ? (
          <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--color-text-muted)' }}>
            <div className="text-center">
              <Eye size={36} className="mx-auto mb-3 opacity-20" />
              <p className="text-sm">Selecione um jogador para ver a analise</p>
              <p className="text-[10px] mt-1">Com dados da planilha de analises, perfil WyScout e SkillCorner</p>
            </div>
          </div>
        ) : (
          <>
            {/* Player header */}
            <div className="p-5 flex items-center gap-4" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              {selectedPlayer.foto ? (
                <img src={proxyImageUrl(selectedPlayer.foto)!} alt={selectedPlayer.nome} className="w-16 h-16 rounded-full object-cover" style={{ border: '2px solid var(--color-border-subtle)' }} onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none' }} />
              ) : (
                <div className="w-16 h-16 rounded-full flex items-center justify-center" style={{ background: 'var(--color-surface-2)', border: '2px solid var(--color-border-subtle)' }}>
                  <User size={28} style={{ color: 'var(--color-text-muted)' }} />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold" style={{ color: 'var(--color-text-primary)' }}>{selectedPlayer.nome}</h2>
                  {selectedPlayer.perfil && (() => {
                    const ps = getPerfilStyle(selectedPlayer.perfil);
                    return (
                      <span className="text-[9px] px-2 py-0.5 rounded-full uppercase font-semibold" style={{ background: ps.bg, color: ps.color, border: `1px solid ${ps.border}` }}>
                        {selectedPlayer.perfil}
                      </span>
                    );
                  })()}
                </div>
                <div className="flex flex-wrap items-center gap-3 mt-1 text-xs" style={{ color: 'var(--color-text-muted)' }}>
                  {selectedPlayer.posicao && <span>{selectedPlayer.posicao}</span>}
                  {selectedPlayer.equipe && <span>{selectedPlayer.equipe}</span>}
                  {selectedPlayer.liga && <span>{selectedPlayer.liga}</span>}
                  {selectedPlayer.idade && <span>{selectedPlayer.idade} anos</span>}
                </div>
              </div>
              <button
                onClick={() => setSelectedPlayer(null)}
                className="p-2 rounded cursor-pointer hover:bg-white/5 shrink-0"
                style={{ color: 'var(--color-text-muted)' }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex px-5 pt-3 gap-1" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              {([
                { id: 'analise' as DetailTab, label: 'Analise do Scout', icon: <FileText size={13} /> },
                { id: 'wyscout' as DetailTab, label: 'WyScout', icon: <BarChart3 size={13} /> },
                { id: 'skillcorner' as DetailTab, label: 'SkillCorner', icon: <Activity size={13} /> },
              ] as { id: DetailTab; label: string; icon: React.ReactNode }[]).map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className="flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-colors cursor-pointer rounded-t"
                  style={{
                    color: activeTab === tab.id ? 'var(--color-accent)' : 'var(--color-text-secondary)',
                    borderBottom: activeTab === tab.id ? '2px solid var(--color-accent)' : '2px solid transparent',
                  }}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-y-auto p-5">
              <AnimatePresence mode="wait">
                {activeTab === 'analise' && (
                  <motion.div key="analise" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-4">
                    {/* Score grades */}
                    {Object.keys(selectedPlayer.scores).length > 0 && (
                      <div>
                        <div className="text-[9px] font-[var(--font-display)] tracking-[0.15em] uppercase mb-3" style={{ color: 'var(--color-text-muted)' }}>NOTAS</div>
                        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                          {Object.entries(selectedPlayer.scores).map(([key, value], i) => (
                            <motion.div
                              key={key}
                              initial={{ opacity: 0, y: 8 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: 0.05 + i * 0.04 }}
                              className="text-center p-3 rounded-xl"
                              style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}
                            >
                              <div className="text-[9px] mb-1 leading-tight uppercase" style={{ color: 'var(--color-text-muted)' }}>
                                {SCORE_LABELS[key] || key}
                              </div>
                              <div className="text-xl font-[var(--font-mono)] font-bold" style={{ color: getAnalysisScoreColor(value) }}>
                                {value.toFixed(1)}
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Analysis text */}
                    {selectedPlayer.analysis_text && (
                      <div className="p-4 rounded-lg" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}>
                        <div className="text-[9px] font-[var(--font-display)] tracking-[0.15em] uppercase font-semibold mb-2" style={{ color: 'var(--color-text-muted)' }}>
                          PARECER
                        </div>
                        <div className="text-xs leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--color-text-secondary)' }}>
                          {selectedPlayer.analysis_text}
                        </div>
                      </div>
                    )}

                    {/* Financial */}
                    {(selectedPlayer.faixa_salarial || selectedPlayer.transfer_luvas) && (
                      <div className="flex flex-wrap gap-3">
                        {selectedPlayer.faixa_salarial && (
                          <div className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[10px]" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}>
                            <DollarSign size={11} style={{ color: 'var(--color-text-muted)' }} />
                            <span style={{ color: 'var(--color-text-muted)' }}>Salario:</span>
                            <span style={{ color: 'var(--color-text-primary)' }}>{selectedPlayer.faixa_salarial}</span>
                          </div>
                        )}
                        {selectedPlayer.transfer_luvas && (
                          <div className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[10px]" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}>
                            <DollarSign size={11} style={{ color: 'var(--color-text-muted)' }} />
                            <span style={{ color: 'var(--color-text-muted)' }}>Transfer/Luvas:</span>
                            <span style={{ color: 'var(--color-text-primary)' }}>{selectedPlayer.transfer_luvas}</span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* External links */}
                    {Object.keys(selectedPlayer.links).length > 0 && (
                      <div>
                        <div className="text-[9px] font-[var(--font-display)] tracking-[0.15em] uppercase mb-2" style={{ color: 'var(--color-text-muted)' }}>LINKS</div>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(selectedPlayer.links).map(([key, url]) => {
                            const info = LINK_ICONS[key];
                            const label = info?.label || key;
                            const isVideo = key === 'Vídeo';
                            const isReport = key === 'Relatório';
                            return (
                              <a
                                key={key}
                                href={url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-medium transition-colors hover:bg-white/10"
                                style={{ background: 'var(--color-surface-2)', color: 'var(--color-text-secondary)', border: '1px solid var(--color-border-subtle)' }}
                              >
                                {isVideo ? <Video size={11} /> : isReport ? <FileText size={11} /> : <ExternalLink size={11} />}
                                {label}
                              </a>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* WyScout/SkillCorner availability hint */}
                    <div className="flex items-center gap-2 text-[10px] px-3 py-2 rounded-lg" style={{ background: selectedPlayer.wyscout_match && !wsAutoCleared ? 'rgba(34,197,94,0.06)' : 'rgba(59,130,246,0.06)', border: `1px solid ${selectedPlayer.wyscout_match && !wsAutoCleared ? 'rgba(34,197,94,0.15)' : 'rgba(59,130,246,0.15)'}` }}>
                      <BarChart3 size={12} style={{ color: selectedPlayer.wyscout_match && !wsAutoCleared ? '#22c55e' : '#3b82f6' }} />
                      {selectedPlayer.wyscout_match && !wsAutoCleared ? (
                        <>
                          <span style={{ color: 'var(--color-text-muted)' }}>Match WyScout:</span>
                          <span className="flex-1" style={{ color: '#22c55e' }}>{wsOverride || selectedPlayer.wyscout_match}</span>
                          <button
                            onClick={() => { setWsAutoCleared(true); setWsOverride(null); }}
                            className="flex items-center gap-1 px-1.5 py-0.5 rounded cursor-pointer hover:bg-white/5 transition-colors"
                            style={{ color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)' }}
                            title="Remover match automatico"
                          >
                            <Unlink size={10} />
                          </button>
                        </>
                      ) : wsOverride ? (
                        <>
                          <span style={{ color: 'var(--color-text-muted)' }}>Match manual:</span>
                          <span className="flex-1" style={{ color: '#3b82f6' }}>{wsOverride}</span>
                          <button
                            onClick={() => setWsOverride(null)}
                            className="p-0.5 rounded cursor-pointer hover:bg-white/5"
                            style={{ color: 'var(--color-text-muted)' }}
                          >
                            <X size={10} />
                          </button>
                        </>
                      ) : (
                        <span style={{ color: 'var(--color-text-muted)' }}>Use as abas WyScout e SkillCorner para buscar dados do jogador</span>
                      )}
                    </div>

                    {/* Empty state for no analysis data */}
                    {Object.keys(selectedPlayer.scores).length === 0 && !selectedPlayer.analysis_text && (
                      <div className="py-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
                        <FileText size={28} className="mx-auto mb-2 opacity-20" />
                        <p className="text-xs">Nenhum dado de analise registrado</p>
                      </div>
                    )}
                  </motion.div>
                )}

                {activeTab === 'wyscout' && (
                  <motion.div key="wyscout" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                    <WyScoutProfileSection
                      displayName={selectedPlayer.wyscout_match}
                      wsOverride={wsOverride}
                      onOverrideChange={setWsOverride}
                      autoMatchCleared={wsAutoCleared}
                      onClearAutoMatch={() => setWsAutoCleared(true)}
                    />
                  </motion.div>
                )}

                {activeTab === 'skillcorner' && (
                  <motion.div key="skillcorner" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                    <SkillCornerProfileSection
                      displayName={wsOverride || selectedPlayer.wyscout_match || selectedPlayer.nome}
                      scOverride={scOverride}
                      onOverrideChange={setScOverride}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
