import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeftRight, AlertCircle, Activity, Shield } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import api, { proxyImageUrl, isProxyFallback } from '../lib/api';
import { usePlayers, usePositions, useSkillCornerComparison } from '../hooks/usePlayers';
import { getScoreColor } from '../lib/utils';
import RadarChart from '../components/RadarChart';
import type { ComparisonResponse } from '../types/api';

function PlayerSearchInput({ label, value, onChange, onSelect, players, showDropdown }: {
  label: string; value: string; onChange: (v: string) => void; onSelect: (v: string) => void;
  players: { name: string; display_name: string | null; team: string | null; position: string | null }[];
  showDropdown: boolean;
}) {
  return (
    <div>
      <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>{label}</label>
      <div className="relative">
        <input type="text" value={value} onChange={(e) => onChange(e.target.value)} placeholder="Digite o nome..." className="w-full px-3 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }} />
        {showDropdown && players.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 rounded overflow-hidden z-50 max-h-48 overflow-y-auto" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-active)' }}>
            {players.map((p, i) => (
              <button key={i} onClick={() => onSelect(p.display_name || p.name)} className="w-full text-left px-3 py-2 text-sm hover:bg-white/5 cursor-pointer" style={{ borderBottom: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }}>
                <div>{p.display_name || p.name}</div>
                <div className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>{p.team}</div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ComparisonPage() {
  const [search1, setSearch1] = useState('');
  const [search2, setSearch2] = useState('');
  const [debounced1, setDebounced1] = useState('');
  const [debounced2, setDebounced2] = useState('');
  const [player1, setPlayer1] = useState('');
  const [player2, setPlayer2] = useState('');
  const [position, setPosition] = useState('Atacante');
  const [timer1, setTimer1] = useState<ReturnType<typeof setTimeout> | null>(null);
  const [timer2, setTimer2] = useState<ReturnType<typeof setTimeout> | null>(null);

  const { data: positions = [] } = usePositions();

  const { data: results1 } = usePlayers(debounced1.length >= 2 && !player1 ? { search: debounced1, limit: 8 } : { limit: 0 });
  const { data: results2 } = usePlayers(debounced2.length >= 2 && !player2 ? { search: debounced2, limit: 8 } : { limit: 0 });

  const handleSearch1 = (v: string) => { setSearch1(v); setPlayer1(''); if (timer1) clearTimeout(timer1); setTimer1(setTimeout(() => setDebounced1(v), 200)); };
  const handleSearch2 = (v: string) => { setSearch2(v); setPlayer2(''); if (timer2) clearTimeout(timer2); setTimer2(setTimeout(() => setDebounced2(v), 200)); };

  const { data: comparison, isLoading, error } = useQuery({
    queryKey: ['comparison', player1, player2, position],
    queryFn: async () => {
      const res = await api.post('/comparison', { player1, player2, position });
      return res.data as ComparisonResponse;
    },
    enabled: !!player1 && !!player2 && player1 !== player2,
    staleTime: 10 * 60 * 1000,
  });

  // SkillCorner comparison (complementary, non-destructive)
  const { data: scComparison } = useSkillCornerComparison(
    player1, player2, position
  );

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-[var(--font-display)] text-lg font-bold tracking-tight flex items-center gap-2">
          <ArrowLeftRight size={18} style={{ color: 'var(--color-accent)' }} />
          Comparativo
        </h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>Comparacao de indices compostos entre dois jogadores</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded text-sm" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}>
          <AlertCircle size={16} /><span>Erro: {(error as Error).message}</span>
        </div>
      )}

      <div className="card-glass rounded-lg p-5">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-3 items-end">
          <PlayerSearchInput label="JOGADOR 1" value={search1} onChange={handleSearch1} onSelect={(v) => { setPlayer1(v); setSearch1(v); setDebounced1(''); }} players={results1?.players ?? []} showDropdown={debounced1.length >= 2 && !player1} />
          <PlayerSearchInput label="JOGADOR 2" value={search2} onChange={handleSearch2} onSelect={(v) => { setPlayer2(v); setSearch2(v); setDebounced2(''); }} players={results2?.players ?? []} showDropdown={debounced2.length >= 2 && !player2} />
          <div>
            <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>POSICAO</label>
            <select value={position} onChange={(e) => setPosition(e.target.value)} className="px-3 py-2 rounded text-sm cursor-pointer outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
              {(positions.length > 0 ? positions : ['Atacante','Extremo','Meia','Volante','Lateral direito','Lateral esquerdo','Zagueiro','Goleiro']).map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>
      </div>

      {isLoading && <div className="card-glass rounded-lg p-8 text-center"><div className="skeleton h-48 rounded" /></div>}

      {comparison && (
        <>
          {/* Player cards */}
          <div className="grid grid-cols-2 gap-3">
            <div className="card-glass rounded-lg p-4" style={{ borderLeft: '3px solid var(--color-accent)' }}>
              <div className="font-bold text-lg">{comparison.player1.name}</div>
              <div className="text-xs flex items-center gap-1" style={{ color: 'var(--color-text-muted)' }}>
                {comparison.player1.club_logo ? (
                  <img src={proxyImageUrl(comparison.player1.club_logo)!} alt="" className="w-4 h-4 object-contain" onLoad={(e) => { if (isProxyFallback(e.target as HTMLImageElement)) (e.target as HTMLImageElement).style.display = 'none'; }} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                ) : <Shield size={13} strokeWidth={1.5} />}
                {comparison.player1.team} • {comparison.player1.position_raw} • {comparison.player1.age} anos
              </div>
            </div>
            <div className="card-glass rounded-lg p-4" style={{ borderLeft: '3px solid #3b82f6' }}>
              <div className="font-bold text-lg">{comparison.player2.name}</div>
              <div className="text-xs flex items-center gap-1" style={{ color: 'var(--color-text-muted)' }}>
                {comparison.player2.club_logo ? (
                  <img src={proxyImageUrl(comparison.player2.club_logo)!} alt="" className="w-4 h-4 object-contain" onLoad={(e) => { if (isProxyFallback(e.target as HTMLImageElement)) (e.target as HTMLImageElement).style.display = 'none'; }} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                ) : <Shield size={13} strokeWidth={1.5} />}
                {comparison.player2.team} • {comparison.player2.position_raw} • {comparison.player2.age} anos
              </div>
            </div>
          </div>

          {/* Dual radar */}
          <div className="card-glass rounded-lg p-5">
            <div className="text-[10px] font-[var(--font-display)] tracking-[0.2em] uppercase mb-3" style={{ color: 'var(--color-text-muted)' }}>RADAR COMPARATIVO ({comparison.position})</div>
            <div className="max-w-lg mx-auto">
              <RadarChart
                labels={Object.keys(comparison.indices1)}
                values={Object.values(comparison.indices1)}
                values2={Object.keys(comparison.indices1).map(k => comparison.indices2[k] ?? 0)}
                color1="#ef4444"
                color2="#3b82f6"
                size={400}
                playerName={comparison.player1.name}
              />
            </div>
            <div className="flex items-center justify-center gap-4 mt-2">
              <span className="flex items-center gap-1 text-xs"><span className="w-3 h-3 rounded-full" style={{ background: 'var(--color-accent)' }} />{comparison.player1.name}</span>
              <span className="flex items-center gap-1 text-xs"><span className="w-3 h-3 rounded-full" style={{ background: '#3b82f6' }} />{comparison.player2.name}</span>
            </div>
          </div>

          {/* Comparison table */}
          <div className="card-glass rounded-lg overflow-hidden">
            <div className="px-4 py-2.5" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              <span className="text-[10px] font-[var(--font-display)] tracking-[0.15em] uppercase" style={{ color: 'var(--color-text-muted)' }}>TABELA COMPARATIVA</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                    <th className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Indice</th>
                    <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-accent)' }}>{comparison.player1.name}</th>
                    <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: '#3b82f6' }}>{comparison.player2.name}</th>
                    <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Diff</th>
                    <th className="px-3 py-2.5 text-center text-[10px]" style={{ color: 'var(--color-text-muted)' }}></th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.comparison.map((row, i) => (
                    <motion.tr key={row.index} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.04 }} style={{ borderBottom: '1px solid var(--color-border-subtle)' }} className="hover:bg-white/[0.02]">
                      <td className="px-3 py-2.5 font-medium">{row.index}</td>
                      <td className="px-3 py-2.5 text-right font-[var(--font-mono)] text-xs" style={{ color: getScoreColor(row.player1_value) }}>{row.player1_value.toFixed(0)}</td>
                      <td className="px-3 py-2.5 text-right font-[var(--font-mono)] text-xs" style={{ color: getScoreColor(row.player2_value) }}>{row.player2_value.toFixed(0)}</td>
                      <td className="px-3 py-2.5 text-right font-[var(--font-mono)] text-xs" style={{ color: row.diff > 0 ? 'var(--color-accent)' : row.diff < 0 ? '#3b82f6' : 'var(--color-text-muted)' }}>
                        {row.diff > 0 ? '+' : ''}{row.diff.toFixed(0)}
                      </td>
                      <td className="px-3 py-2.5 text-center">{row.diff > 0 ? '🔴' : row.diff < 0 ? '🔵' : '='}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* SkillCorner comparison section (non-destructive extension) */}
      {scComparison && (scComparison.player1.found || scComparison.player2.found) && (
        <div className="card-glass rounded-lg overflow-hidden">
          <div className="px-4 py-2.5 flex items-center gap-2" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
            <Activity size={13} style={{ color: 'var(--color-accent)' }} />
            <span className="text-[10px] font-[var(--font-display)] tracking-[0.15em] uppercase" style={{ color: 'var(--color-text-muted)' }}>
              SKILLCORNER — METRICAS FISICAS
            </span>
            <div className="ml-auto flex gap-2">
              {scComparison.player1.found ? (
                <span className="text-[9px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(34,197,94,0.1)', color: '#22c55e' }}>
                  {scComparison.player1.sc_name}
                </span>
              ) : (
                <span className="text-[9px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>
                  J1: sem dados
                </span>
              )}
              {scComparison.player2.found ? (
                <span className="text-[9px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(34,197,94,0.1)', color: '#22c55e' }}>
                  {scComparison.player2.sc_name}
                </span>
              ) : (
                <span className="text-[9px] px-1.5 py-0.5 rounded" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>
                  J2: sem dados
                </span>
              )}
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <th className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Metrica</th>
                  <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-accent)' }}>{comparison?.player1.name || player1}</th>
                  <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: '#3b82f6' }}>{comparison?.player2.name || player2}</th>
                  <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Diff</th>
                </tr>
              </thead>
              <tbody>
                {scComparison.comparison.map((row, i) => (
                  <motion.tr
                    key={row.metric}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.03 }}
                    style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                    className="hover:bg-white/[0.02]"
                  >
                    <td className="px-3 py-2 text-xs font-medium">
                      {row.metric.replace(/_/g, ' ').replace(/per 90/i, '/90').replace(/ index$/i, '')}
                    </td>
                    <td className="px-3 py-2 text-right font-[var(--font-mono)] text-xs" style={{ color: row.player1_value != null ? 'var(--color-text-primary)' : 'var(--color-text-muted)' }}>
                      {row.player1_value != null ? row.player1_value.toFixed(2) : '—'}
                    </td>
                    <td className="px-3 py-2 text-right font-[var(--font-mono)] text-xs" style={{ color: row.player2_value != null ? 'var(--color-text-primary)' : 'var(--color-text-muted)' }}>
                      {row.player2_value != null ? row.player2_value.toFixed(2) : '—'}
                    </td>
                    <td className="px-3 py-2 text-right font-[var(--font-mono)] text-xs" style={{ color: row.diff != null ? (row.diff > 0 ? 'var(--color-accent)' : row.diff < 0 ? '#3b82f6' : 'var(--color-text-muted)') : 'var(--color-text-muted)' }}>
                      {row.diff != null ? `${row.diff > 0 ? '+' : ''}${row.diff.toFixed(2)}` : '—'}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!player1 && !player2 && (
        <div className="card-glass rounded-lg p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <ArrowLeftRight size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Selecione dois jogadores para comparar</p>
        </div>
      )}
    </div>
  );
}
