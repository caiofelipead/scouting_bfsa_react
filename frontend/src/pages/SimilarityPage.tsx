import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, Users, AlertCircle } from 'lucide-react';
import { usePlayers, useSimilarity, usePositions } from '../hooks/usePlayers';
import { proxyImageUrl, isProxyFallback } from '../lib/api';

export default function SimilarityPage() {
  const similarity = useSimilarity();
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [position, setPosition] = useState('Atacante');
  const [topN, setTopN] = useState(20);
  const [minMinutes, setMinMinutes] = useState(500);
  const [debounceTimer, setDebounceTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  const { data: positions = [], error: posErr } = usePositions();

  const searchParams = useMemo(() => ({
    search: debouncedSearch || undefined,
    limit: 10,
  }), [debouncedSearch]);

  const { data: searchData } = usePlayers(
    debouncedSearch.length >= 2 && !selectedPlayer ? searchParams : { limit: 0 }
  );
  const players = searchData?.players ?? [];

  const handleSearchChange = (value: string) => {
    setSearch(value);
    setSelectedPlayer('');
    if (debounceTimer) clearTimeout(debounceTimer);
    setDebounceTimer(setTimeout(() => setDebouncedSearch(value), 200));
  };

  const handleSearch = () => {
    if (selectedPlayer) {
      similarity.mutate({
        player_name: selectedPlayer,
        position,
        top_n: topN,
        min_minutes: minMinutes,
      });
    }
  };

  const result = similarity.data;
  const simLoading = similarity.isPending;
  const simError = similarity.error || posErr;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title flex items-center gap-2.5">
          <Users size={22} strokeWidth={2} style={{ color: 'var(--color-accent)' }} />
          Similaridade
        </h1>
        <p className="page-subtitle">
          Cosine similarity ponderada por posicao + proximity bonus (POSITION_WEIGHTS)
        </p>
      </div>

      {/* Error display */}
      {simError && (
        <div
          className="flex items-center gap-2 px-4 py-3 rounded text-sm"
          style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}
        >
          <AlertCircle size={16} />
          <span>Erro: {(simError as Error).message || 'Erro ao buscar jogadores similares'}</span>
        </div>
      )}

      {/* Controls */}
      <div className="card-glass rounded-lg p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto_auto_auto] gap-3 items-end">
          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>
              JOGADOR REFERENCIA
            </label>
            <div className="relative">
              <input
                type="text"
                value={search}
                onChange={(e) => handleSearchChange(e.target.value)}
                placeholder="Digite o nome..."
                className="w-full px-3 py-2 rounded text-sm outline-none"
                style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)', fontFamily: 'var(--font-body)' }}
              />
              {debouncedSearch.length >= 2 && !selectedPlayer && players.length > 0 && (
                <div
                  className="absolute top-full left-0 right-0 mt-1 rounded overflow-hidden z-50 max-h-48 overflow-y-auto"
                  style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-active)' }}
                >
                  {players.map((p, i) => (
                    <button
                      key={i}
                      onClick={() => { setSelectedPlayer(p.display_name || p.name); setSearch(p.display_name || p.name); setDebouncedSearch(''); }}
                      className="w-full text-left px-3 py-2 text-sm transition-colors hover:bg-white/5 cursor-pointer"
                      style={{ borderBottom: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
                    >
                      <div>{p.display_name || p.name}</div>
                      <div className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>{p.team} — {p.position}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>POSICAO</label>
            <select value={position} onChange={(e) => setPosition(e.target.value)} className="px-3 py-2 rounded text-sm cursor-pointer outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
              {positions.length > 0 ? (
                positions.map((p) => <option key={p} value={p}>{p}</option>)
              ) : (
                <>
                  <option value="Atacante">Atacante</option>
                  <option value="Extremo">Extremo</option>
                  <option value="Meia">Meia</option>
                  <option value="Volante">Volante</option>
                  <option value="Lateral direito">Lateral direito</option>
                  <option value="Lateral esquerdo">Lateral esquerdo</option>
                  <option value="Zagueiro">Zagueiro</option>
                  <option value="Goleiro">Goleiro</option>
                </>
              )}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>TOP N</label>
            <input type="number" value={topN} onChange={(e) => setTopN(Number(e.target.value))} className="w-16 px-3 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }} />
          </div>

          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>MIN MIN</label>
            <input type="number" value={minMinutes} onChange={(e) => setMinMinutes(Number(e.target.value))} className="w-20 px-3 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }} />
          </div>

          <button
            onClick={handleSearch}
            disabled={!selectedPlayer || simLoading}
            className="px-4 py-2 rounded text-sm font-[var(--font-display)] font-semibold tracking-wide uppercase transition-all cursor-pointer disabled:opacity-40"
            style={{ background: 'var(--color-accent)', color: '#fff', border: 'none' }}
          >
            {simLoading ? '...' : 'BUSCAR'}
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="card-glass rounded-lg overflow-hidden">
          <div className="px-4 py-2.5" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
            <span className="text-[11px] font-[var(--font-display)] tracking-[0.14em] font-semibold uppercase" style={{ color: 'var(--color-text-muted)' }}>
              SIMILARES A {result.reference_player} ({result.position}) — {result.similar_players.length} resultados
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <th className="px-3 py-2.5 text-left text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase" style={{ color: 'var(--color-text-muted)' }}>#</th>
                  <th className="px-3 py-2.5 text-left text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase" style={{ color: 'var(--color-text-muted)' }}>Jogador</th>
                  <th className="px-3 py-2.5 text-left text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase" style={{ color: 'var(--color-text-muted)' }}>Equipa</th>
                  <th className="px-3 py-2.5 text-right text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase" style={{ color: 'var(--color-text-muted)' }}>Metricas</th>
                  <th className="px-3 py-2.5 text-right text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase" style={{ color: 'var(--color-accent)' }}>Similaridade</th>
                </tr>
              </thead>
              <tbody>
                {result.similar_players.map((sp, i) => (
                  <motion.tr
                    key={i}
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03 }}
                    style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                    className="transition-colors hover:bg-white/[0.02]"
                  >
                    <td className="px-3 py-2.5 font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-muted)' }}>{i + 1}</td>
                    <td className="px-3 py-2.5 font-medium">{sp.display_name || sp.name}</td>
                    <td className="px-3 py-2.5 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                      <span className="flex items-center gap-1">
                        {sp.club_logo && <img src={proxyImageUrl(sp.club_logo)!} alt="" className="w-4 h-4 object-contain flex-shrink-0" onLoad={(e) => { if (isProxyFallback(e.target as HTMLImageElement)) (e.target as HTMLImageElement).style.display = 'none'; }} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />}
                        {sp.team || '—'}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-right font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-muted)' }}>{sp.matched_metrics}</td>
                    <td className="px-3 py-2.5 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-3)' }}>
                          <div className="h-full rounded-full" style={{ width: `${sp.similarity_pct}%`, background: sp.similarity_pct >= 80 ? '#22c55e' : sp.similarity_pct >= 60 ? '#eab308' : '#f97316' }} />
                        </div>
                        <span className="font-[var(--font-mono)] text-xs font-bold" style={{ color: sp.similarity_pct >= 80 ? '#22c55e' : sp.similarity_pct >= 60 ? '#eab308' : '#f97316' }}>
                          {sp.similarity_pct.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                  </motion.tr>
                ))}
                {result.similar_players.length === 0 && (
                  <tr><td colSpan={5} className="px-3 py-8 text-center text-xs" style={{ color: 'var(--color-text-muted)' }}>Nenhum jogador similar encontrado</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Initial state — no search yet */}
      {!result && !simLoading && !simError && (
        <div
          className="card-glass rounded-lg p-8 text-center"
          style={{ color: 'var(--color-text-muted)' }}
        >
          <Search size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Selecione um jogador e clique em BUSCAR</p>
          <p className="text-xs mt-1 opacity-60">Algoritmo: cosine similarity + proximity bonus ponderados por POSITION_WEIGHTS</p>
        </div>
      )}
    </div>
  );
}
