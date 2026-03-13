import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { FileBarChart, AlertCircle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import { usePlayers, usePositions, useRadarData } from '../hooks/usePlayers';
import { getScoreColor } from '../lib/utils';
import RadarChart from '../components/RadarChart';
import type { IndicesResponse } from '../types/api';

export default function ReportPage() {
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [position, setPosition] = useState('Atacante');
  const [timer, setTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  const { data: positions = [] } = usePositions();

  const searchParams = useMemo(() => ({ search: debouncedSearch || undefined, limit: 10 }), [debouncedSearch]);
  const { data: searchData } = usePlayers(debouncedSearch.length >= 2 && !selectedPlayer ? searchParams : { limit: 0 });
  const players = searchData?.players ?? [];

  const handleSearchChange = (v: string) => {
    setSearch(v);
    setSelectedPlayer('');
    if (timer) clearTimeout(timer);
    setTimer(setTimeout(() => setDebouncedSearch(v), 200));
  };

  // Indices data
  const { data: indicesData, isLoading: indicesLoading, error: indicesError } = useQuery({
    queryKey: ['indices', selectedPlayer, position],
    queryFn: async () => {
      const res = await api.get(`/players/${encodeURIComponent(selectedPlayer)}/indices`, { params: { position } });
      return res.data as IndicesResponse;
    },
    enabled: !!selectedPlayer,
    staleTime: 10 * 60 * 1000,
  });

  // Radar data (percentiles)
  const { data: radarData } = useRadarData(selectedPlayer || null);

  const indexEntries = indicesData ? Object.entries(indicesData.indices) : [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-[var(--font-display)] text-lg font-bold tracking-tight flex items-center gap-2">
          <FileBarChart size={18} style={{ color: 'var(--color-accent)' }} />
          Relatorio
        </h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>Graficos de relatorio com indices compostos e posicionamento</p>
      </div>

      {indicesError && (
        <div className="flex items-center gap-2 px-4 py-3 rounded text-sm" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}>
          <AlertCircle size={16} /><span>Erro: {(indicesError as Error).message}</span>
        </div>
      )}

      <div className="card-glass rounded-lg p-5">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3 items-end">
          <div>
            <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>JOGADOR</label>
            <div className="relative">
              <input type="text" value={search} onChange={(e) => handleSearchChange(e.target.value)} placeholder="Digite o nome..." className="w-full px-3 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }} />
              {debouncedSearch.length >= 2 && !selectedPlayer && players.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 rounded overflow-hidden z-50 max-h-48 overflow-y-auto" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-active)' }}>
                  {players.map((p, i) => (
                    <button key={i} onClick={() => { setSelectedPlayer(p.display_name || p.name); setSearch(p.display_name || p.name); setDebouncedSearch(''); }} className="w-full text-left px-3 py-2 text-sm hover:bg-white/5 cursor-pointer" style={{ borderBottom: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }}>
                      <div>{p.display_name || p.name}</div>
                      <div className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>{p.team} — {p.position}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div>
            <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>POSICAO PARA INDICES</label>
            <select value={position} onChange={(e) => setPosition(e.target.value)} className="px-3 py-2 rounded text-sm cursor-pointer outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
              {(positions.length > 0 ? positions : ['Atacante','Extremo','Meia','Volante','Lateral','Zagueiro','Goleiro']).map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>
      </div>

      {indicesLoading && <div className="card-glass rounded-lg p-8"><div className="skeleton h-48 rounded" /></div>}

      {indicesData && (
        <>
          {/* Player header card */}
          {indicesData.summary && (
            <div className="card-glass rounded-lg p-5" style={{ border: '2px solid var(--color-accent)' }}>
              <div className="flex items-center gap-3">
                <div>
                  <div className="text-xs font-semibold" style={{ color: 'var(--color-accent)' }}>{indicesData.summary.position_raw} → AVALIANDO COMO: {indicesData.position.toUpperCase()}</div>
                  <div className="text-2xl font-bold mt-1">{indicesData.summary.name}</div>
                </div>
              </div>
              <div className="text-sm mt-2" style={{ color: 'var(--color-text-secondary)' }}>
                {indicesData.summary.team} • {indicesData.summary.age} anos • {indicesData.summary.minutes} min
              </div>
            </div>
          )}

          {/* Perfil de Indices + Rankings */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="card-glass rounded-lg p-5">
              <div className="text-[10px] font-[var(--font-display)] tracking-[0.2em] uppercase mb-3" style={{ color: 'var(--color-text-muted)' }}>PERFIL DE INDICES</div>
              {indexEntries.length > 0 && (
                <RadarChart labels={indexEntries.map(([k]) => k)} values={indexEntries.map(([, v]) => v)} size={360} />
              )}
            </div>
            <div className="card-glass rounded-lg p-5">
              <div className="text-[10px] font-[var(--font-display)] tracking-[0.2em] uppercase mb-3" style={{ color: 'var(--color-text-muted)' }}>RANKINGS</div>
              <div className="space-y-2.5">
                {indexEntries.map(([name, value], i) => (
                  <motion.div key={name} initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{name}</span>
                      <span className="text-xs font-[var(--font-mono)] font-semibold" style={{ color: getScoreColor(value) }}>{value.toFixed(1)}</span>
                    </div>
                    <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-2)' }}>
                      <motion.div className="h-full rounded-full" style={{ background: getScoreColor(value) }} initial={{ width: 0 }} animate={{ width: `${Math.min(value, 100)}%` }} transition={{ duration: 0.6, delay: 0.2 + i * 0.06 }} />
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>

          {/* Percentile radar (WyScout top metrics) */}
          {radarData && radarData.labels.length > 0 && (
            <div className="card-glass rounded-lg p-5">
              <div className="text-[10px] font-[var(--font-display)] tracking-[0.2em] uppercase mb-3" style={{ color: 'var(--color-text-muted)' }}>PERCENTIS POR POSICAO (TOP METRICAS)</div>
              <div className="grid grid-cols-1 lg:grid-cols-[1fr_1fr] gap-4">
                <RadarChart labels={radarData.labels} values={radarData.values} size={360} playerName={indicesData.summary.name} />
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 content-start">
                  {radarData.labels.map((label, i) => (
                    <div key={label} className="flex items-center justify-between">
                      <span className="text-[10px] truncate pr-1" style={{ color: 'var(--color-text-muted)' }}>{label}</span>
                      <span className="text-[10px] font-[var(--font-mono)] font-semibold" style={{ color: getScoreColor(radarData.values[i]) }}>P{radarData.values[i].toFixed(0)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Metric breakdown */}
          {indicesData.breakdown && (
            <div className="card-glass rounded-lg p-5">
              <div className="text-[10px] font-[var(--font-display)] tracking-[0.2em] uppercase mb-4" style={{ color: 'var(--color-text-muted)' }}>DETALHAMENTO POR INDICE</div>
              {Object.entries(indicesData.breakdown).map(([idxName, metrics]) => (
                <div key={idxName} className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-bold">{idxName}</span>
                    <span className="text-xs font-[var(--font-mono)]" style={{ color: getScoreColor(indicesData.indices[idxName] ?? 0) }}>P{(indicesData.indices[idxName] ?? 0).toFixed(0)}</span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-2">
                    {metrics.map((m) => (
                      <div key={m.metric} className="p-3 rounded text-center" style={{ background: 'var(--color-surface-2)', borderLeft: `3px solid ${getScoreColor(m.percentile)}` }}>
                        <div className="text-[9px] uppercase truncate" style={{ color: 'var(--color-text-muted)' }}>{m.metric.replace('/90', '').replace(', %', '%').slice(0, 20)}</div>
                        <div className="text-lg font-[var(--font-mono)] font-bold mt-1">{m.value != null ? m.value.toFixed(2) : '—'}</div>
                        <div className="text-[10px] font-[var(--font-mono)]" style={{ color: getScoreColor(m.percentile) }}>P{m.percentile.toFixed(0)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {!selectedPlayer && !indicesLoading && (
        <div className="card-glass rounded-lg p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <FileBarChart size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Selecione um jogador para gerar o relatorio</p>
        </div>
      )}
    </div>
  );
}
