import { motion } from 'framer-motion';
import { FileText } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';

export default function OfferedPage() {
  const { data: players = [], isLoading: loading } = useQuery({
    queryKey: ['offered'],
    queryFn: async () => {
      const r = await api.get('/offered');
      return r.data.players as Record<string, string>[];
    },
    staleTime: 5 * 60 * 1000,
  });

  const columns = players.length > 0 ? Object.keys(players[0]).slice(0, 8) : [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-[var(--font-display)] text-lg font-bold tracking-tight flex items-center gap-2">
          <FileText size={18} style={{ color: 'var(--color-accent)' }} />
          Jogadores Oferecidos
        </h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
          {players.length} jogadores na lista de oferecidos
        </p>
      </div>

      <div className="card-glass rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                {columns.map((col) => (
                  <th key={col} className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase whitespace-nowrap" style={{ color: 'var(--color-text-muted)' }}>
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
                    Nenhum jogador oferecido
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
