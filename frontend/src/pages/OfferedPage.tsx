import { motion } from 'framer-motion';
import { FileText, AlertCircle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';

export default function OfferedPage() {
  const { data: players = [], isLoading: loading, error } = useQuery({
    queryKey: ['offered'],
    queryFn: async () => {
      const r = await api.get('/offered');
      return (r.data.players ?? []) as Record<string, string>[];
    },
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const columns = players.length > 0 ? Object.keys(players[0]).slice(0, 8) : [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title flex items-center gap-2.5">
          <FileText size={22} strokeWidth={2} style={{ color: 'var(--color-accent)' }} />
          Jogadores Oferecidos
        </h1>
        <p className="page-subtitle">
          {players.length} jogadores na lista de oferecidos
        </p>
      </div>

      {/* Error display */}
      {error && (
        <div
          className="flex items-center gap-2 px-4 py-3 rounded text-sm"
          style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}
        >
          <AlertCircle size={16} />
          <span>Erro ao carregar oferecidos: {(error as Error).message || 'Erro desconhecido'}</span>
        </div>
      )}

      <div className="card-glass overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm table-zebra">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border-subtle)', background: 'var(--color-surface-1)' }}>
                {columns.map((col) => (
                  <th key={col} className="px-3 py-3 text-left text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase whitespace-nowrap sticky top-0" style={{ color: 'var(--color-text-muted)', background: 'var(--color-surface-1)' }}>
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                    {Array.from({ length: Math.max(columns.length, 5) }).map((_, j) => (
                      <td key={j} className="px-3 py-2.5"><div className="skeleton h-4 rounded" /></td>
                    ))}
                  </tr>
                ))
              ) : players.length > 0 ? (
                players.map((p, i) => (
                  <motion.tr
                    key={i}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.02 }}
                    style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                    className="transition-colors hover:bg-white/[0.02]"
                  >
                    {columns.map((col) => (
                      <td key={col} className="px-3 py-2.5 whitespace-nowrap" style={{ color: col === columns[0] ? 'var(--color-text-primary)' : 'var(--color-text-secondary)' }}>
                        {p[col] || '—'}
                      </td>
                    ))}
                  </motion.tr>
                ))
              ) : (
                <tr>
                  <td colSpan={columns.length || 1} className="px-3 py-8 text-center text-xs" style={{ color: 'var(--color-text-muted)' }}>
                    {error ? 'Erro ao carregar dados' : 'Nenhum jogador oferecido'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
