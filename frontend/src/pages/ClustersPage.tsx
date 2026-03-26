import { useState } from 'react';
import { motion } from 'framer-motion';
import { Dna, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import api from '../lib/api';
import { usePositions } from '../hooks/usePlayers';
import { getScoreColor } from '../lib/utils';
import type { ClustersResponse } from '../types/api';

export default function ClustersPage() {
  const [position, setPosition] = useState('Atacante');
  const [minMinutes, setMinMinutes] = useState(500);
  const [expandedCluster, setExpandedCluster] = useState<number | null>(0);

  const { data: positions = [] } = usePositions();

  const clustering = useMutation({
    mutationFn: async () => {
      const res = await api.post('/clusters', { position, min_minutes: minMinutes });
      return res.data as ClustersResponse;
    },
  });

  const result = clustering.data;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-[var(--font-display)] text-lg font-bold tracking-tight flex items-center gap-2">
          <Dna size={18} style={{ color: 'var(--color-accent)' }} />
          Clusters Taticos
        </h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
          K-Means + Gaussian Mixture + Random Forest para perfis taticos
        </p>
      </div>

      {clustering.error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded text-sm" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}>
          <AlertCircle size={16} /><span>Erro: {(clustering.error as Error).message}</span>
        </div>
      )}

      <div className="card-glass rounded-lg p-5">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>POSICAO</label>
            <select value={position} onChange={(e) => setPosition(e.target.value)} className="px-3 py-2 rounded text-sm cursor-pointer outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
              {(positions.length > 0 ? positions : ['Atacante','Extremo','Meia','Volante','Lateral direito','Lateral esquerdo','Zagueiro','Goleiro']).map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>MIN MINUTOS</label>
            <input type="number" value={minMinutes} onChange={(e) => setMinMinutes(Number(e.target.value))} className="w-24 px-3 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }} />
          </div>
          <button
            onClick={() => clustering.mutate()}
            disabled={clustering.isPending}
            className="px-5 py-2 rounded text-sm font-[var(--font-display)] font-semibold tracking-wide uppercase transition-all cursor-pointer disabled:opacity-40"
            style={{ background: 'var(--color-accent)', color: '#fff', border: 'none' }}
          >
            {clustering.isPending ? 'ANALISANDO...' : 'IDENTIFICAR PERFIS'}
          </button>
        </div>
      </div>

      {result && !result.error && (
        <>
          <div className="px-4 py-2 rounded text-sm" style={{ background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.3)', color: '#22c55e' }}>
            <strong>{result.n_clusters} perfis taticos</strong> identificados em {result.total_players} {position.toLowerCase()}s
          </div>

          <div className="space-y-3">
            {result.clusters.map((cluster) => (
              <div key={cluster.id} className="card-glass rounded-lg overflow-hidden">
                <button
                  onClick={() => setExpandedCluster(expandedCluster === cluster.id ? null : cluster.id)}
                  className="w-full flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-white/[0.02] transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {expandedCluster === cluster.id ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    <span className="font-[var(--font-display)] font-bold">{cluster.name || `Perfil ${cluster.id + 1}`}</span>
                    <span className="text-xs px-2 py-0.5 rounded" style={{ background: 'var(--color-surface-2)', color: 'var(--color-text-muted)' }}>
                      {cluster.size} jogadores
                    </span>
                  </div>
                </button>

                {expandedCluster === cluster.id && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="px-4 pb-4 space-y-4">
                    {/* Top players */}
                    <div>
                      <div className="text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-2" style={{ color: 'var(--color-text-muted)' }}>TOP JOGADORES</div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                              <th className="px-2 py-1.5 text-left text-[10px] uppercase" style={{ color: 'var(--color-text-muted)' }}>Jogador</th>
                              <th className="px-2 py-1.5 text-left text-[10px] uppercase" style={{ color: 'var(--color-text-muted)' }}>Equipa</th>
                              <th className="px-2 py-1.5 text-right text-[10px] uppercase" style={{ color: 'var(--color-text-muted)' }}>Prob%</th>
                              <th className="px-2 py-1.5 text-right text-[10px] uppercase" style={{ color: 'var(--color-text-muted)' }}>Idade</th>
                              <th className="px-2 py-1.5 text-right text-[10px] uppercase" style={{ color: 'var(--color-text-muted)' }}>Min</th>
                            </tr>
                          </thead>
                          <tbody>
                            {cluster.players.map((p, i) => (
                              <tr key={i} style={{ borderBottom: '1px solid var(--color-border-subtle)' }} className="hover:bg-white/[0.02]">
                                <td className="px-2 py-1.5 font-medium">{p.name}</td>
                                <td className="px-2 py-1.5 text-xs" style={{ color: 'var(--color-text-muted)' }}>{p.team || '—'}</td>
                                <td className="px-2 py-1.5 text-right font-[var(--font-mono)] text-xs" style={{ color: getScoreColor(p.probability) }}>{p.probability.toFixed(1)}%</td>
                                <td className="px-2 py-1.5 text-right font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-muted)' }}>{p.age ?? '—'}</td>
                                <td className="px-2 py-1.5 text-right font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-muted)' }}>{p.minutes ?? '—'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Cluster features (centroid z-scores) */}
                    {cluster.features.length > 0 && (
                      <div>
                        <div className="text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-2" style={{ color: 'var(--color-text-muted)' }}>CARACTERISTICAS (Z-SCORE DO CENTROIDE)</div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                          {cluster.features.map((f) => (
                            <div key={f.metric} className="p-2 rounded text-center" style={{ background: 'var(--color-surface-2)', borderLeft: `3px solid ${f.zscore > 0 ? '#22c55e' : '#ef4444'}` }}>
                              <div className="text-[9px] uppercase truncate" style={{ color: 'var(--color-text-muted)' }}>{f.metric.replace('/90', '').slice(0, 25)}</div>
                              <div className="text-sm font-[var(--font-mono)] font-bold" style={{ color: f.zscore > 0 ? '#22c55e' : '#ef4444' }}>
                                {f.zscore > 0 ? '+' : ''}{f.zscore.toFixed(2)}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {result?.error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded text-sm" style={{ background: 'rgba(234,179,8,0.1)', border: '1px solid rgba(234,179,8,0.3)', color: '#eab308' }}>
          <AlertCircle size={16} /><span>{result.error}</span>
        </div>
      )}

      {!result && !clustering.isPending && (
        <div className="card-glass rounded-lg p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <Dna size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Selecione a posicao e clique em IDENTIFICAR PERFIS</p>
          <p className="text-xs mt-1 opacity-60">Clusterizacao K-Means automatica com selecao otima de K</p>
        </div>
      )}
    </div>
  );
}
