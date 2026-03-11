import { useState } from 'react';
import { motion } from 'framer-motion';
import { Database, Search, AlertCircle, Download } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import type { DataTableResponse } from '../types/api';

const SOURCES = [
  { id: 'analises', label: 'Analises' },
  { id: 'wyscout', label: 'WyScout' },
  { id: 'skillcorner', label: 'SkillCorner' },
  { id: 'oferecidos', label: 'Oferecidos' },
];

export default function DataBrowserPage() {
  const [source, setSource] = useState('wyscout');
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [timer, setTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  const handleSearchChange = (v: string) => {
    setSearch(v);
    if (timer) clearTimeout(timer);
    setTimer(setTimeout(() => setDebouncedSearch(v), 300));
  };

  const { data, isLoading, error } = useQuery({
    queryKey: ['data-browser', source, debouncedSearch],
    queryFn: async () => {
      const params: Record<string, string | number> = { limit: 200 };
      if (debouncedSearch) params.search = debouncedSearch;
      const res = await api.get(`/data/${source}`, { params });
      return res.data as DataTableResponse;
    },
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const handleExportCSV = () => {
    if (!data || data.rows.length === 0) return;
    const headers = data.columns.join(',');
    const rows = data.rows.map(row => data.columns.map(col => {
      const val = row[col];
      if (val === null || val === undefined) return '';
      const str = String(val);
      return str.includes(',') || str.includes('"') ? `"${str.replace(/"/g, '""')}"` : str;
    }).join(',')).join('\n');
    const csv = headers + '\n' + rows;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${source}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-[var(--font-display)] text-lg font-bold tracking-tight flex items-center gap-2">
          <Database size={18} style={{ color: 'var(--color-accent)' }} />
          Dados
        </h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>Explorar dados brutos de todas as fontes</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded text-sm" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}>
          <AlertCircle size={16} /><span>Erro: {(error as Error).message}</span>
        </div>
      )}

      {/* Source selector */}
      <div className="flex flex-wrap items-center gap-2">
        {SOURCES.map(s => (
          <button
            key={s.id}
            onClick={() => { setSource(s.id); setSearch(''); setDebouncedSearch(''); }}
            className="px-4 py-2 rounded text-sm font-[var(--font-display)] tracking-wide cursor-pointer transition-all"
            style={{
              background: source === s.id ? 'var(--color-accent-glow)' : 'var(--color-surface-1)',
              color: source === s.id ? 'var(--color-accent)' : 'var(--color-text-secondary)',
              border: `1px solid ${source === s.id ? 'rgba(220,38,38,0.3)' : 'var(--color-border-subtle)'}`,
            }}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Search + info */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }} />
          <input type="text" value={search} onChange={(e) => handleSearchChange(e.target.value)} placeholder="Buscar jogador..." className="w-full pl-9 pr-3 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }} />
        </div>
        {data && (
          <span className="text-[10px] font-[var(--font-mono)]" style={{ color: 'var(--color-text-muted)' }}>
            {data.total} registros
          </span>
        )}
        <button onClick={handleExportCSV} disabled={!data || data.rows.length === 0} className="flex items-center gap-1.5 px-3 py-2 rounded text-xs font-[var(--font-display)] cursor-pointer disabled:opacity-40" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
          <Download size={12} /> CSV
        </button>
      </div>

      {/* Table */}
      <div className="card-glass rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                {(data?.columns ?? []).map(col => (
                  <th key={col} className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase whitespace-nowrap" style={{ color: 'var(--color-text-muted)' }}>
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                    {Array.from({ length: Math.max((data?.columns?.length ?? 5), 5) }).map((_, j) => (
                      <td key={j} className="px-3 py-2.5"><div className="skeleton h-4 rounded" /></td>
                    ))}
                  </tr>
                ))
              ) : data && data.rows.length > 0 ? (
                data.rows.map((row, i) => (
                  <motion.tr key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: Math.min(i * 0.01, 0.5) }} style={{ borderBottom: '1px solid var(--color-border-subtle)' }} className="hover:bg-white/[0.02]">
                    {data.columns.map((col, j) => (
                      <td key={col} className="px-3 py-2.5 whitespace-nowrap" style={{ color: j === 0 ? 'var(--color-text-primary)' : 'var(--color-text-secondary)' }}>
                        {row[col] != null ? String(row[col]) : '—'}
                      </td>
                    ))}
                  </motion.tr>
                ))
              ) : (
                <tr><td colSpan={(data?.columns?.length ?? 1) || 1} className="px-3 py-8 text-center text-xs" style={{ color: 'var(--color-text-muted)' }}>Nenhum dado encontrado</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
