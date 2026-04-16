import { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Plus, Trash2, ChevronDown, StickyNote,
  Users, Target, ClipboardList, AlertCircle, GripVertical,
  Search, Loader2, User, ArrowLeftRight,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { usePlayers, usePositions } from '../hooks/usePlayers';
import api, { proxyImageUrl, isProxyFallback } from '../lib/api';
import { getScoreColor } from '../lib/utils';
import RadarChart from '../components/RadarChart';
import type { PlayerSummary, PlayersQueryParams, ComparisonResponse } from '../types/api';

// ── Types ──

interface Need {
  id: string;
  position: string;
  priority: 'Alta' | 'Média' | 'Baixa';
  status: 'Aberta' | 'Em Andamento' | 'Fechada';
  notes: string;
}

type PipelineStatus = 'Pendente de avaliação' | 'Titular' | 'Briga por titularidade' | 'Rotação' | 'Aposta' | 'Fundo de elenco' | 'Reprovado';

interface TargetPlayer {
  id: string;
  dbId?: number | null;
  name: string;
  club: string;
  age: number;
  position: string;
  pipeline: PipelineStatus;
  photoUrl?: string | null;
  score?: number | null;
  league?: string | null;
}

interface ShadowXISlot {
  positionKey: string;
  playerIds: string[];
}

interface Note {
  id: string;
  targetId: string;
  text: string;
  date: string;
}

// ── Helpers ──

const uid = () => crypto.randomUUID();

function loadJSON<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function saveJSON<T>(key: string, data: T) {
  localStorage.setItem(key, JSON.stringify(data));
}

const PRIORITY_COLORS: Record<string, string> = {
  Alta: '#ef4444',
  Média: '#eab308',
  Baixa: '#3b82f6',
};

const STATUS_COLORS: Record<string, string> = {
  Aberta: '#22c55e',
  'Em Andamento': '#eab308',
  Fechada: '#6b7280',
};

const PIPELINE_COLORS: Record<PipelineStatus, string> = {
  'Pendente de avaliação': '#6b7280',
  Titular: '#22c55e',
  'Briga por titularidade': '#3b82f6',
  Rotação: '#eab308',
  Aposta: '#f97316',
  'Fundo de elenco': '#a855f7',
  Reprovado: '#ef4444',
};

const PIPELINE_STEPS: PipelineStatus[] = ['Pendente de avaliação', 'Titular', 'Briga por titularidade', 'Rotação', 'Aposta', 'Fundo de elenco', 'Reprovado'];

// 4-3-3 formation positions
const FORMATION_433: { key: string; label: string; x: number; y: number }[] = [
  { key: 'GK', label: 'GOL', x: 50, y: 90 },
  { key: 'LB', label: 'LE', x: 15, y: 72 },
  { key: 'CB1', label: 'ZAG', x: 37, y: 75 },
  { key: 'CB2', label: 'ZAG', x: 63, y: 75 },
  { key: 'RB', label: 'LD', x: 85, y: 72 },
  { key: 'CM1', label: 'VOL', x: 30, y: 52 },
  { key: 'CM2', label: 'MEI', x: 50, y: 45 },
  { key: 'CM3', label: 'VOL', x: 70, y: 52 },
  { key: 'LW', label: 'PE', x: 18, y: 22 },
  { key: 'ST', label: 'ATA', x: 50, y: 18 },
  { key: 'RW', label: 'PD', x: 82, y: 22 },
];

// ── Tab 1: Necessidades do Elenco ──

function TabNeeds({ needs, setNeeds }: { needs: Need[]; setNeeds: (n: Need[]) => void }) {
  const addRow = () => {
    setNeeds([...needs, { id: uid(), position: '', priority: 'Média', status: 'Aberta', notes: '' }]);
  };

  const removeRow = (id: string) => {
    setNeeds(needs.filter((n) => n.id !== id));
  };

  const update = (id: string, field: keyof Need, value: string) => {
    setNeeds(needs.map((n) => (n.id === id ? { ...n, [field]: value } : n)));
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          Defina as posições prioritárias para reforço do elenco.
        </p>
        <button
          onClick={addRow}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer"
          style={{ background: 'var(--color-accent)', color: '#fff' }}
        >
          <Plus size={14} /> Adicionar
        </button>
      </div>

      <div className="card-glass overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              {['Posição', 'Prioridade', 'Status', 'Observações', ''].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold" style={{ color: 'var(--color-text-muted)' }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {needs.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-sm" style={{ color: 'var(--color-text-muted)' }}>
                  Nenhuma necessidade cadastrada. Clique em "Adicionar" para começar.
                </td>
              </tr>
            )}
            {needs.map((need, i) => (
              <motion.tr
                key={need.id}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
              >
                <td className="px-4 py-2">
                  <input
                    type="text"
                    value={need.position}
                    onChange={(e) => update(need.id, 'position', e.target.value)}
                    placeholder="Ex: Lateral Esquerdo"
                    className="w-full bg-transparent border-0 text-sm outline-none"
                    style={{ color: 'var(--color-text-primary)' }}
                  />
                </td>
                <td className="px-4 py-2">
                  <div className="relative">
                    <select
                      value={need.priority}
                      onChange={(e) => update(need.id, 'priority', e.target.value)}
                      className="appearance-none bg-transparent border rounded-md px-2 py-1 text-xs cursor-pointer pr-6"
                      style={{ borderColor: PRIORITY_COLORS[need.priority], color: PRIORITY_COLORS[need.priority] }}
                    >
                      <option value="Alta">Alta</option>
                      <option value="Média">Média</option>
                      <option value="Baixa">Baixa</option>
                    </select>
                    <ChevronDown size={12} className="absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: PRIORITY_COLORS[need.priority] }} />
                  </div>
                </td>
                <td className="px-4 py-2">
                  <div className="relative">
                    <select
                      value={need.status}
                      onChange={(e) => update(need.id, 'status', e.target.value)}
                      className="appearance-none bg-transparent border rounded-md px-2 py-1 text-xs cursor-pointer pr-6"
                      style={{ borderColor: STATUS_COLORS[need.status], color: STATUS_COLORS[need.status] }}
                    >
                      <option value="Aberta">Aberta</option>
                      <option value="Em Andamento">Em Andamento</option>
                      <option value="Fechada">Fechada</option>
                    </select>
                    <ChevronDown size={12} className="absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: STATUS_COLORS[need.status] }} />
                  </div>
                </td>
                <td className="px-4 py-2">
                  <input
                    type="text"
                    value={need.notes}
                    onChange={(e) => update(need.id, 'notes', e.target.value)}
                    placeholder="Observações..."
                    className="w-full bg-transparent border-0 text-sm outline-none"
                    style={{ color: 'var(--color-text-primary)' }}
                  />
                </td>
                <td className="px-2 py-2">
                  <button
                    onClick={() => removeRow(need.id)}
                    className="p-1.5 rounded-md transition-colors cursor-pointer hover:bg-red-500/10"
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    <Trash2 size={14} />
                  </button>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Player Search Dropdown ──

function PlayerSearchPicker({ onSelect, existingIds }: {
  onSelect: (player: PlayerSummary) => void;
  existingIds: Set<number>;
}) {
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState('');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { data: apiPositions = [] } = usePositions();

  const handleSearchChange = (value: string) => {
    setSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setDebouncedSearch(value), 300);
  };

  const queryParams = useMemo<PlayersQueryParams>(() => ({
    search: debouncedSearch || undefined,
    position: position || undefined,
    min_minutes: 0,
    limit: 30,
  }), [debouncedSearch, position]);

  const { data, isLoading, isFetching } = usePlayers(queryParams);
  const players = useMemo(() => {
    const list = data?.players ?? [];
    return [...list].sort((a, b) => (b.score ?? 0) - (a.score ?? 0));
  }, [data]);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSelect = (player: PlayerSummary) => {
    onSelect(player);
    setSearch('');
    setDebouncedSearch('');
    setOpen(false);
  };

  return (
    <div ref={containerRef} className="relative">
      <div className="card-glass p-4 space-y-3">
        <p className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>
          Buscar jogador no banco de dados
        </p>
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }} />
            <input
              type="text"
              placeholder="Digite o nome do jogador..."
              value={search}
              onChange={(e) => { handleSearchChange(e.target.value); setOpen(true); }}
              onFocus={() => setOpen(true)}
              className="w-full pl-9 pr-3 py-2 rounded-lg text-sm bg-transparent border outline-none"
              style={{ borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
            />
            {(isLoading || isFetching) && (
              <Loader2 size={14} className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin" style={{ color: 'var(--color-text-muted)' }} />
            )}
          </div>
          <div className="relative">
            <select
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              className="appearance-none pl-3 pr-8 py-2 rounded-lg text-sm bg-transparent border cursor-pointer"
              style={{ borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
            >
              <option value="">Todas as Posições</option>
              {apiPositions.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
            <ChevronDown size={14} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--color-text-muted)' }} />
          </div>
        </div>
      </div>

      {/* Results dropdown */}
      <AnimatePresence>
        {open && players.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="absolute z-50 left-0 right-0 mt-1 rounded-xl overflow-hidden"
            style={{
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border-subtle)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
              maxHeight: '320px',
              overflowY: 'auto',
            }}
          >
            {players.map((player) => {
              const alreadyAdded = existingIds.has(player.id);
              return (
                <button
                  key={player.id}
                  onClick={() => !alreadyAdded && handleSelect(player)}
                  disabled={alreadyAdded}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors cursor-pointer hover:bg-white/5 disabled:opacity-40 disabled:cursor-not-allowed"
                  style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                >
                  {player.photo_url ? (
                    <img
                      src={proxyImageUrl(player.photo_url)!}
                      alt={player.name}
                      className="w-8 h-8 rounded-full object-cover"
                      referrerPolicy="no-referrer"
                      onLoad={(e) => { if (isProxyFallback(e.target as HTMLImageElement)) (e.target as HTMLImageElement).style.display = 'none'; }} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: 'var(--color-surface-2)' }}>
                      <User size={14} strokeWidth={1.5} style={{ color: 'var(--color-text-muted)' }} />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate" style={{ color: 'var(--color-text-primary)' }}>
                      {player.display_name || player.name}
                    </div>
                    <div className="text-[11px] truncate" style={{ color: 'var(--color-text-muted)' }}>
                      {player.team ?? '—'} · {player.position ?? '—'} · {player.age ?? '—'} anos
                      {player.league ? ` · ${player.league}` : ''}
                    </div>
                  </div>
                  {player.score != null && (
                    <span className="text-xs font-bold px-2 py-0.5 rounded-md" style={{
                      background: player.score >= 60 ? 'rgba(34,197,94,0.15)' : player.score >= 40 ? 'rgba(234,179,8,0.15)' : 'rgba(239,68,68,0.15)',
                      color: player.score >= 60 ? '#22c55e' : player.score >= 40 ? '#eab308' : '#ef4444',
                    }}>
                      {player.score.toFixed(1)}
                    </span>
                  )}
                  {alreadyAdded && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'var(--color-surface-2)', color: 'var(--color-text-muted)' }}>
                      Já adicionado
                    </span>
                  )}
                </button>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Tab 2: Alvos ──

function TabTargets({
  targets,
  setTargets,
  needs,
}: {
  targets: TargetPlayer[];
  setTargets: (t: TargetPlayer[]) => void;
  needs: Need[];
}) {
  const [filterPos, setFilterPos] = useState('');
  const [filterPipeline, setFilterPipeline] = useState('');
  const [showSearch, setShowSearch] = useState(false);

  const needPositions = useMemo(() => [...new Set(needs.map((n) => n.position).filter(Boolean))], [needs]);
  const allPositions = useMemo(() => {
    const fromTargets = targets.map((t) => t.position).filter(Boolean);
    return [...new Set([...needPositions, ...fromTargets])];
  }, [needPositions, targets]);

  const existingPlayerIds = useMemo(() => new Set(targets.map((t) => t.dbId).filter((id): id is number => id != null)), [targets]);

  const filtered = useMemo(() => {
    let list = targets;
    if (filterPos) list = list.filter((t) => t.position === filterPos);
    if (filterPipeline) list = list.filter((t) => t.pipeline === filterPipeline);
    return list;
  }, [targets, filterPos, filterPipeline]);

  const addFromDB = (player: PlayerSummary) => {
    // Find best matching need position, or use the player's own position
    const playerPos = player.position ?? '';
    const matchingNeed = needPositions.find((p) => p.toLowerCase() === playerPos.toLowerCase());
    setTargets([
      ...targets,
      {
        id: uid(),
        dbId: player.id,
        name: player.display_name || player.name,
        club: player.team ?? '',
        age: player.age ?? 0,
        position: matchingNeed || playerPos,
        pipeline: 'Pendente de avaliação',
        photoUrl: player.photo_url,
        score: player.score,
        league: player.league,
      },
    ]);
  };

  const updatePipeline = (id: string, pipeline: PipelineStatus) => {
    setTargets(targets.map((t) => (t.id === id ? { ...t, pipeline } : t)));
  };

  const removeTarget = (id: string) => {
    setTargets(targets.filter((t) => t.id !== id));
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="card-glass p-4 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[160px]">
          <select
            value={filterPos}
            onChange={(e) => setFilterPos(e.target.value)}
            className="appearance-none w-full pl-3 pr-8 py-2 rounded-lg text-sm bg-transparent border cursor-pointer"
            style={{ borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
          >
            <option value="">Todas as Posições</option>
            {allPositions.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <ChevronDown size={14} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--color-text-muted)' }} />
        </div>
        <div className="relative">
          <select
            value={filterPipeline}
            onChange={(e) => setFilterPipeline(e.target.value)}
            className="appearance-none pl-3 pr-8 py-2 rounded-lg text-sm bg-transparent border cursor-pointer"
            style={{ borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
          >
            <option value="">Todos os Status</option>
            {PIPELINE_STEPS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <ChevronDown size={14} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--color-text-muted)' }} />
        </div>
        <button
          onClick={() => setShowSearch(!showSearch)}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all cursor-pointer"
          style={{ background: 'var(--color-accent)', color: '#fff' }}
        >
          <Plus size={14} /> Adicionar Jogador
        </button>
      </div>

      {/* Player search picker */}
      <AnimatePresence>
        {showSearch && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <PlayerSearchPicker onSelect={addFromDB} existingIds={existingPlayerIds} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Target cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {filtered.length === 0 && (
          <div className="col-span-full card-glass p-8 text-center text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Nenhum alvo encontrado. Clique em "Adicionar Jogador" para buscar no banco de dados.
          </div>
        )}
        {filtered.map((target, i) => (
          <motion.div
            key={target.id}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            className="card-glass p-4 space-y-3"
          >
            <div className="flex items-start gap-3">
              {/* Player photo */}
              {target.photoUrl ? (
                <img
                  src={proxyImageUrl(target.photoUrl)!}
                  alt={target.name}
                  className="w-10 h-10 rounded-full object-cover flex-shrink-0"
                  referrerPolicy="no-referrer"
                  onLoad={(e) => { if (isProxyFallback(e.target as HTMLImageElement)) (e.target as HTMLImageElement).style.display = 'none'; }} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
              ) : (
                <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: 'var(--color-surface-2)' }}>
                  <User size={16} strokeWidth={1.5} style={{ color: 'var(--color-text-muted)' }} />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3
                    className="text-sm font-semibold truncate cursor-pointer hover:underline"
                    style={{ color: 'var(--color-accent)' }}
                    onClick={() => window.open(`${window.location.origin}${window.location.pathname}?tab=dashboard&player=${encodeURIComponent(target.name)}`, '_blank')}
                    title="Abrir perfil do jogador"
                  >{target.name}</h3>
                  {target.score != null && (
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded flex-shrink-0" style={{
                      background: target.score >= 60 ? 'rgba(34,197,94,0.15)' : target.score >= 40 ? 'rgba(234,179,8,0.15)' : 'rgba(239,68,68,0.15)',
                      color: target.score >= 60 ? '#22c55e' : target.score >= 40 ? '#eab308' : '#ef4444',
                    }}>
                      {target.score.toFixed(1)}
                    </span>
                  )}
                </div>
                <p className="text-xs truncate" style={{ color: 'var(--color-text-muted)' }}>
                  {target.club} · {target.age} anos · {target.position}
                  {target.league ? ` · ${target.league}` : ''}
                </p>
              </div>
              <button
                onClick={() => removeTarget(target.id)}
                className="p-1 rounded-md transition-colors cursor-pointer hover:bg-red-500/10 flex-shrink-0"
                style={{ color: 'var(--color-text-muted)' }}
              >
                <Trash2 size={14} />
              </button>
            </div>

            {/* Perfil */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-medium" style={{ color: 'var(--color-text-muted)' }}>Perfil:</span>
              <div className="relative flex-1">
                <select
                  value={target.pipeline}
                  onChange={(e) => updatePipeline(target.id, e.target.value as PipelineStatus)}
                  className="appearance-none w-full bg-transparent border rounded-md px-2.5 py-1.5 text-xs font-medium cursor-pointer pr-7"
                  style={{
                    borderColor: PIPELINE_COLORS[target.pipeline],
                    color: PIPELINE_COLORS[target.pipeline],
                  }}
                >
                  {PIPELINE_STEPS.map((step) => (
                    <option key={step} value={step}>{step}</option>
                  ))}
                </select>
                <ChevronDown size={12} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: PIPELINE_COLORS[target.pipeline] }} />
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// ── Tab 3: Shadow XI ──

const MAX_PER_POSITION = 5;

function TabShadowXI({
  xi,
  setXI,
  targets,
}: {
  xi: ShadowXISlot[];
  setXI: (slots: ShadowXISlot[]) => void;
  targets: TargetPlayer[];
}) {
  const available = useMemo(() => targets.filter((t) => t.pipeline !== 'Reprovado' && t.pipeline !== 'Pendente de avaliação'), [targets]);
  const [selectedPos, setSelectedPos] = useState<string | null>(null);

  const getSlotIds = useCallback(
    (key: string): string[] => xi.find((s) => s.positionKey === key)?.playerIds ?? [],
    [xi],
  );

  const updateSlotIds = (key: string, playerIds: string[]) => {
    const exists = xi.find((s) => s.positionKey === key);
    if (exists) {
      setXI(xi.map((s) => (s.positionKey === key ? { ...s, playerIds } : s)));
    } else {
      setXI([...xi, { positionKey: key, playerIds }]);
    }
  };

  const addToSlot = (key: string, playerId: string) => {
    const current = getSlotIds(key);
    if (current.length >= MAX_PER_POSITION || current.includes(playerId)) return;
    updateSlotIds(key, [...current, playerId]);
  };

  const removeFromSlot = (key: string, playerId: string) => {
    const current = getSlotIds(key);
    updateSlotIds(key, current.filter((id) => id !== playerId));
  };

  const getPlayer = (id: string) => targets.find((t) => t.id === id);

  // All player IDs already assigned to any slot
  const assignedIds = useMemo(() => new Set(xi.flatMap((s) => s.playerIds)), [xi]);

  const selectedSlotIds = selectedPos ? getSlotIds(selectedPos) : [];
  const selectedLabel = selectedPos ? FORMATION_433.find((f) => f.key === selectedPos)?.label ?? '' : '';

  return (
    <div className="space-y-4">
      <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
        Clique em uma posição no campo para adicionar até {MAX_PER_POSITION} alvos.
      </p>

      {available.length === 0 && (
        <div className="card-glass p-6 text-center text-sm" style={{ color: 'var(--color-text-muted)' }}>
          <AlertCircle size={24} className="mx-auto mb-2" style={{ color: 'var(--color-text-muted)' }} />
          Nenhum alvo avaliado. Altere o perfil dos alvos na aba Alvos.
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_340px] gap-4">
        {/* Pitch */}
        <div className="card-glass p-4 flex justify-center">
          <div
            className="relative"
            style={{
              width: '100%',
              maxWidth: '520px',
              aspectRatio: '68/105',
              background: 'linear-gradient(180deg, #1a5e2a 0%, #1d6b30 50%, #1a5e2a 100%)',
              borderRadius: '12px',
              border: '2px solid rgba(255,255,255,0.15)',
              overflow: 'hidden',
            }}
          >
            {/* Field lines */}
            <div style={{ position: 'absolute', top: '50%', left: '5%', right: '5%', height: '1px', background: 'rgba(255,255,255,0.2)' }} />
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', width: '18%', aspectRatio: '1', borderRadius: '50%', border: '1px solid rgba(255,255,255,0.2)' }} />
            <div style={{ position: 'absolute', bottom: '0', left: '20%', right: '20%', height: '16%', border: '1px solid rgba(255,255,255,0.2)', borderBottom: 'none' }} />
            <div style={{ position: 'absolute', top: '0', left: '20%', right: '20%', height: '16%', border: '1px solid rgba(255,255,255,0.2)', borderTop: 'none' }} />

            {/* Positions */}
            {FORMATION_433.map((pos) => {
              const ids = getSlotIds(pos.key);
              const count = ids.length;
              const isSelected = selectedPos === pos.key;
              const firstName = count > 0 ? getPlayer(ids[0])?.name : null;
              return (
                <div
                  key={pos.key}
                  style={{
                    position: 'absolute',
                    left: `${pos.x}%`,
                    top: `${pos.y}%`,
                    transform: 'translate(-50%,-50%)',
                    textAlign: 'center',
                    zIndex: 2,
                  }}
                >
                  <button
                    onClick={() => setSelectedPos(isSelected ? null : pos.key)}
                    className="cursor-pointer"
                    style={{
                      width: '44px',
                      height: '44px',
                      borderRadius: '50%',
                      background: count > 0 ? 'var(--color-accent)' : 'rgba(0,0,0,0.45)',
                      border: isSelected ? '3px solid #fff' : '2px solid rgba(255,255,255,0.4)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto',
                      position: 'relative',
                      boxShadow: isSelected ? '0 0 12px rgba(227,6,19,0.6)' : 'none',
                      transition: 'all 0.2s',
                    }}
                  >
                    <span className="text-[10px] font-bold text-white">{pos.label}</span>
                    {count > 0 && (
                      <span
                        className="absolute -top-1 -right-1 text-[8px] font-bold rounded-full flex items-center justify-center"
                        style={{ width: '16px', height: '16px', background: '#fff', color: 'var(--color-accent)' }}
                      >
                        {count}
                      </span>
                    )}
                  </button>
                  {firstName && (
                    <div
                      className="text-[8px] font-semibold mt-1 px-1 py-0.5 rounded max-w-[80px] truncate mx-auto"
                      style={{ background: 'rgba(0,0,0,0.6)', color: '#fff', whiteSpace: 'nowrap' }}
                    >
                      {firstName}{count > 1 ? ` +${count - 1}` : ''}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Side panel — position detail */}
        <div className="card-glass p-4 space-y-3">
          {!selectedPos ? (
            <div className="text-center py-8 text-sm" style={{ color: 'var(--color-text-muted)' }}>
              Selecione uma posição no campo para gerenciar os alvos.
            </div>
          ) : (
            <>
              <h3 className="text-sm font-bold flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
                <span className="w-3 h-3 rounded-full" style={{ background: 'var(--color-accent)' }} />
                {selectedLabel} — {selectedSlotIds.length}/{MAX_PER_POSITION}
              </h3>

              {/* Current players in this position */}
              <div className="space-y-1.5">
                {selectedSlotIds.map((pid, idx) => {
                  const p = getPlayer(pid);
                  if (!p) return null;
                  return (
                    <motion.div
                      key={pid}
                      initial={{ opacity: 0, x: -4 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg"
                      style={{ background: 'var(--color-surface-2)' }}
                    >
                      <span className="text-[10px] font-bold w-4 text-center" style={{ color: 'var(--color-accent)' }}>
                        {idx + 1}
                      </span>
                      {p.photoUrl ? (
                        <img
                          src={proxyImageUrl(p.photoUrl)!}
                          alt={p.name}
                          className="w-6 h-6 rounded-full object-cover"
                          referrerPolicy="no-referrer"
                          onLoad={(e) => { if (isProxyFallback(e.target as HTMLImageElement)) (e.target as HTMLImageElement).style.display = 'none'; }} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                        />
                      ) : (
                        <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: 'var(--color-surface-3)' }}>
                          <User size={10} style={{ color: 'var(--color-text-muted)' }} />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <span className="text-xs font-medium truncate block" style={{ color: 'var(--color-text-primary)' }}>{p.name}</span>
                        <span className="text-[10px] truncate block" style={{ color: 'var(--color-text-muted)' }}>{p.club}</span>
                      </div>
                      <button
                        onClick={() => removeFromSlot(selectedPos, pid)}
                        className="p-1 rounded-md cursor-pointer hover:bg-red-500/10"
                        style={{ color: 'var(--color-text-muted)' }}
                      >
                        <Trash2 size={12} />
                      </button>
                    </motion.div>
                  );
                })}
              </div>

              {/* Add player */}
              {selectedSlotIds.length < MAX_PER_POSITION && (
                <div>
                  <p className="text-[10px] font-medium mb-1.5" style={{ color: 'var(--color-text-muted)' }}>
                    Adicionar alvo:
                  </p>
                  <div className="space-y-1 max-h-[200px] overflow-y-auto">
                    {available.filter((t) => !selectedSlotIds.includes(t.id)).map((t) => (
                      <button
                        key={t.id}
                        onClick={() => addToSlot(selectedPos, t.id)}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-colors cursor-pointer hover:bg-white/5"
                        style={{ border: '1px solid var(--color-border-subtle)' }}
                      >
                        {t.photoUrl ? (
                          <img
                            src={proxyImageUrl(t.photoUrl)!}
                            alt={t.name}
                            className="w-5 h-5 rounded-full object-cover"
                            referrerPolicy="no-referrer"
                            onLoad={(e) => { if (isProxyFallback(e.target as HTMLImageElement)) (e.target as HTMLImageElement).style.display = 'none'; }} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                          />
                        ) : (
                          <div className="w-5 h-5 rounded-full flex items-center justify-center" style={{ background: 'var(--color-surface-3)' }}>
                            <User size={8} style={{ color: 'var(--color-text-muted)' }} />
                          </div>
                        )}
                        <span className="text-xs truncate" style={{ color: 'var(--color-text-primary)' }}>{t.name}</span>
                        <span className="text-[10px] ml-auto flex-shrink-0" style={{ color: PIPELINE_COLORS[t.pipeline] }}>{t.pipeline}</span>
                      </button>
                    ))}
                    {available.filter((t) => !selectedSlotIds.includes(t.id)).length === 0 && (
                      <p className="text-[10px] text-center py-2" style={{ color: 'var(--color-text-muted)' }}>
                        Nenhum alvo disponível.
                      </p>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Tab 4: Notas ──

function TabNotes({
  notes,
  setNotes,
  targets,
}: {
  notes: Note[];
  setNotes: (n: Note[]) => void;
  targets: TargetPlayer[];
}) {
  const [selectedTarget, setSelectedTarget] = useState('');
  const [text, setText] = useState('');

  const filtered = useMemo(
    () => (selectedTarget ? notes.filter((n) => n.targetId === selectedTarget) : notes).sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
    ),
    [notes, selectedTarget],
  );

  const addNote = () => {
    if (!text.trim() || !selectedTarget) return;
    setNotes([
      ...notes,
      { id: uid(), targetId: selectedTarget, text: text.trim(), date: new Date().toISOString() },
    ]);
    setText('');
  };

  const removeNote = (id: string) => {
    setNotes(notes.filter((n) => n.id !== id));
  };

  const getTargetName = (id: string) => targets.find((t) => t.id === id)?.name ?? 'Desconhecido';

  return (
    <div className="space-y-4">
      {/* Select target + input */}
      <div className="card-glass p-4 space-y-3">
        <div className="relative">
          <select
            value={selectedTarget}
            onChange={(e) => setSelectedTarget(e.target.value)}
            className="appearance-none w-full pl-3 pr-8 py-2 rounded-lg text-sm bg-transparent border cursor-pointer"
            style={{ borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
          >
            <option value="">Selecione um alvo...</option>
            {targets.map((t) => (
              <option key={t.id} value={t.id}>{t.name} — {t.position}</option>
            ))}
          </select>
          <ChevronDown size={14} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--color-text-muted)' }} />
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addNote()}
            placeholder={selectedTarget ? 'Adicione uma nota...' : 'Selecione um alvo primeiro'}
            disabled={!selectedTarget}
            className="flex-1 bg-transparent border rounded-lg px-3 py-2 text-sm outline-none disabled:opacity-50"
            style={{ borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
          />
          <button
            onClick={addNote}
            disabled={!selectedTarget || !text.trim()}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all cursor-pointer disabled:opacity-40"
            style={{ background: 'var(--color-accent)', color: '#fff' }}
          >
            <Plus size={14} /> Adicionar
          </button>
        </div>
      </div>

      {/* Timeline */}
      <div className="space-y-2">
        {filtered.length === 0 && (
          <div className="card-glass p-8 text-center text-sm" style={{ color: 'var(--color-text-muted)' }}>
            {selectedTarget ? 'Nenhuma nota para este alvo.' : 'Selecione um alvo para ver suas notas.'}
          </div>
        )}
        {filtered.map((note, i) => (
          <motion.div
            key={note.id}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04 }}
            className="card-glass p-4 flex gap-3"
          >
            <div className="flex flex-col items-center pt-0.5">
              <div className="w-2 h-2 rounded-full" style={{ background: 'var(--color-accent)' }} />
              <div className="w-px flex-1 mt-1" style={{ background: 'var(--color-border-subtle)' }} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                  {getTargetName(note.targetId)}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                    {new Date(note.date).toLocaleDateString('pt-BR')} {new Date(note.date).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <button
                    onClick={() => removeNote(note.id)}
                    className="p-1 rounded-md transition-colors cursor-pointer hover:bg-red-500/10"
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
              <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>{note.text}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// ── Tab 5: Comparativo ──

function TabComparison({ targets }: { targets: TargetPlayer[] }) {
  const [player1Id, setPlayer1Id] = useState('');
  const [player2Id, setPlayer2Id] = useState('');
  const [position, setPosition] = useState('');

  const { data: apiPositions = [] } = usePositions();

  const player1 = targets.find((t) => t.id === player1Id);
  const player2 = targets.find((t) => t.id === player2Id);

  // Auto-detect position from selected players
  const effectivePosition = position || player1?.position || player2?.position || 'Atacante';

  const { data: comparison, isLoading, error } = useQuery({
    queryKey: ['comparison', player1?.name, player2?.name, effectivePosition],
    queryFn: async () => {
      const res = await api.post('/comparison', {
        player1: player1!.name,
        player2: player2!.name,
        position: effectivePosition,
      });
      return res.data as ComparisonResponse;
    },
    enabled: !!player1 && !!player2 && player1.id !== player2.id,
    staleTime: 10 * 60 * 1000,
  });

  return (
    <div className="space-y-4">
      {/* Selection card */}
      <div className="card-glass p-4 space-y-4">
        <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          Selecione dois alvos para comparar seus índices compostos.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-3 items-end">
          {/* Player 1 */}
          <div>
            <label className="block text-[10px] font-semibold tracking-wider uppercase mb-1.5" style={{ color: 'var(--color-accent)' }}>
              Jogador 1
            </label>
            <div className="relative">
              <select
                value={player1Id}
                onChange={(e) => setPlayer1Id(e.target.value)}
                className="appearance-none w-full pl-3 pr-8 py-2.5 rounded-lg text-sm bg-transparent border cursor-pointer"
                style={{ borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
              >
                <option value="">Selecione um alvo...</option>
                {targets.filter((t) => t.id !== player2Id).map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} — {t.position} {t.score != null ? `(${t.score.toFixed(1)})` : ''}
                  </option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--color-text-muted)' }} />
            </div>
          </div>

          {/* Player 2 */}
          <div>
            <label className="block text-[10px] font-semibold tracking-wider uppercase mb-1.5" style={{ color: '#3b82f6' }}>
              Jogador 2
            </label>
            <div className="relative">
              <select
                value={player2Id}
                onChange={(e) => setPlayer2Id(e.target.value)}
                className="appearance-none w-full pl-3 pr-8 py-2.5 rounded-lg text-sm bg-transparent border cursor-pointer"
                style={{ borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
              >
                <option value="">Selecione um alvo...</option>
                {targets.filter((t) => t.id !== player1Id).map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} — {t.position} {t.score != null ? `(${t.score.toFixed(1)})` : ''}
                  </option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--color-text-muted)' }} />
            </div>
          </div>

          {/* Position */}
          <div>
            <label className="block text-[10px] font-semibold tracking-wider uppercase mb-1.5" style={{ color: 'var(--color-text-muted)' }}>
              Posição
            </label>
            <div className="relative">
              <select
                value={position}
                onChange={(e) => setPosition(e.target.value)}
                className="appearance-none pl-3 pr-8 py-2.5 rounded-lg text-sm bg-transparent border cursor-pointer"
                style={{ borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
              >
                <option value="">Auto-detectar</option>
                {apiPositions.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--color-text-muted)' }} />
            </div>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg text-sm" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}>
          <AlertCircle size={16} />
          <span>Erro ao comparar: {(error as Error).message}</span>
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="card-glass p-8 text-center">
          <Loader2 size={24} className="animate-spin mx-auto mb-2" style={{ color: 'var(--color-accent)' }} />
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Carregando comparação...</p>
        </div>
      )}

      {/* Empty state */}
      {!player1Id && !player2Id && (
        <div className="card-glass p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <ArrowLeftRight size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Selecione dois alvos acima para comparar</p>
          {targets.length < 2 && (
            <p className="text-xs mt-2 opacity-60">Você precisa de pelo menos 2 alvos na aba "Alvos" para usar o comparativo.</p>
          )}
        </div>
      )}

      {/* Comparison results */}
      {comparison && (
        <>
          {/* Player info cards */}
          <div className="grid grid-cols-2 gap-3">
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              className="card-glass p-4 flex items-center gap-3"
              style={{ borderLeft: '3px solid var(--color-accent)' }}
            >
              {player1?.photoUrl ? (
                <img
                  src={proxyImageUrl(player1.photoUrl)!}
                  alt={player1.name}
                  className="w-10 h-10 rounded-full object-cover flex-shrink-0"
                  referrerPolicy="no-referrer"
                  onLoad={(e) => { if (isProxyFallback(e.target as HTMLImageElement)) (e.target as HTMLImageElement).style.display = 'none'; }}
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
              ) : (
                <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: 'var(--color-surface-2)' }}>
                  <User size={16} style={{ color: 'var(--color-text-muted)' }} />
                </div>
              )}
              <div className="min-w-0">
                <div className="font-bold text-sm truncate" style={{ color: 'var(--color-text-primary)' }}>{comparison.player1.name}</div>
                <div className="text-[11px] truncate" style={{ color: 'var(--color-text-muted)' }}>
                  {comparison.player1.team} · {comparison.player1.position_raw} · {comparison.player1.age} anos
                </div>
              </div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              className="card-glass p-4 flex items-center gap-3"
              style={{ borderLeft: '3px solid #3b82f6' }}
            >
              {player2?.photoUrl ? (
                <img
                  src={proxyImageUrl(player2.photoUrl)!}
                  alt={player2.name}
                  className="w-10 h-10 rounded-full object-cover flex-shrink-0"
                  referrerPolicy="no-referrer"
                  onLoad={(e) => { if (isProxyFallback(e.target as HTMLImageElement)) (e.target as HTMLImageElement).style.display = 'none'; }}
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
              ) : (
                <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: 'var(--color-surface-2)' }}>
                  <User size={16} style={{ color: 'var(--color-text-muted)' }} />
                </div>
              )}
              <div className="min-w-0">
                <div className="font-bold text-sm truncate" style={{ color: 'var(--color-text-primary)' }}>{comparison.player2.name}</div>
                <div className="text-[11px] truncate" style={{ color: 'var(--color-text-muted)' }}>
                  {comparison.player2.team} · {comparison.player2.position_raw} · {comparison.player2.age} anos
                </div>
              </div>
            </motion.div>
          </div>

          {/* Radar chart */}
          <div className="card-glass p-5">
            <div className="text-[10px] font-semibold tracking-widest uppercase mb-3" style={{ color: 'var(--color-text-muted)' }}>
              RADAR COMPARATIVO ({comparison.position})
            </div>
            <div className="max-w-lg mx-auto">
              <RadarChart
                labels={Object.keys(comparison.indices1)}
                values={Object.values(comparison.indices1)}
                values2={Object.keys(comparison.indices1).map((k) => comparison.indices2[k] ?? 0)}
                color1="#ef4444"
                color2="#3b82f6"
                size={400}
                playerName={comparison.player1.name}
              />
            </div>
            <div className="flex items-center justify-center gap-6 mt-2">
              <span className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                <span className="w-3 h-3 rounded-full" style={{ background: 'var(--color-accent)' }} />
                {comparison.player1.name}
              </span>
              <span className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                <span className="w-3 h-3 rounded-full" style={{ background: '#3b82f6' }} />
                {comparison.player2.name}
              </span>
            </div>
          </div>

          {/* Comparison table */}
          <div className="card-glass rounded-xl overflow-hidden">
            <div className="px-4 py-2.5" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              <span className="text-[10px] font-semibold tracking-widest uppercase" style={{ color: 'var(--color-text-muted)' }}>
                TABELA COMPARATIVA
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                    <th className="px-4 py-2.5 text-left text-[10px] font-semibold tracking-wider uppercase" style={{ color: 'var(--color-text-muted)' }}>Índice</th>
                    <th className="px-4 py-2.5 text-right text-[10px] font-semibold tracking-wider uppercase" style={{ color: 'var(--color-accent)' }}>{comparison.player1.name}</th>
                    <th className="px-4 py-2.5 text-right text-[10px] font-semibold tracking-wider uppercase" style={{ color: '#3b82f6' }}>{comparison.player2.name}</th>
                    <th className="px-4 py-2.5 text-right text-[10px] font-semibold tracking-wider uppercase" style={{ color: 'var(--color-text-muted)' }}>Diff</th>
                    <th className="px-2 py-2.5 w-8" />
                  </tr>
                </thead>
                <tbody>
                  {comparison.comparison.map((row, i) => (
                    <motion.tr
                      key={row.index}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.04 }}
                      style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                      className="hover:bg-white/[0.02]"
                    >
                      <td className="px-4 py-2.5 font-medium text-sm" style={{ color: 'var(--color-text-primary)' }}>{row.index}</td>
                      <td className="px-4 py-2.5 text-right font-mono text-xs" style={{ color: getScoreColor(row.player1_value) }}>
                        {row.player1_value.toFixed(0)}
                      </td>
                      <td className="px-4 py-2.5 text-right font-mono text-xs" style={{ color: getScoreColor(row.player2_value) }}>
                        {row.player2_value.toFixed(0)}
                      </td>
                      <td className="px-4 py-2.5 text-right font-mono text-xs" style={{
                        color: row.diff > 0 ? 'var(--color-accent)' : row.diff < 0 ? '#3b82f6' : 'var(--color-text-muted)',
                      }}>
                        {row.diff > 0 ? '+' : ''}{row.diff.toFixed(0)}
                      </td>
                      <td className="px-2 py-2.5 text-center text-xs">
                        {row.diff > 0 ? (
                          <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: 'var(--color-accent)' }} />
                        ) : row.diff < 0 ? (
                          <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: '#3b82f6' }} />
                        ) : (
                          <span style={{ color: 'var(--color-text-muted)' }}>=</span>
                        )}
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ── Main Page ──

type ShadowTab = 'needs' | 'targets' | 'xi' | 'comparison' | 'notes';

const TABS: { id: ShadowTab; label: string }[] = [
  { id: 'needs', label: 'Necessidades' },
  { id: 'targets', label: 'Alvos' },
  { id: 'comparison', label: 'Comparativo' },
  { id: 'xi', label: 'Shadow XI' },
  { id: 'notes', label: 'Notas' },
];

export default function ShadowTeamPage() {
  const [activeTab, setActiveTab] = useState<ShadowTab>('needs');

  // State persisted to localStorage
  const [needs, setNeedsState] = useState<Need[]>(() => loadJSON('shadow_needs', []));
  const [targets, setTargetsState] = useState<TargetPlayer[]>(() => loadJSON('shadow_targets', []));
  const [xi, setXIState] = useState<ShadowXISlot[]>(() => loadJSON('shadow_xi', []));
  const [notes, setNotesState] = useState<Note[]>(() => loadJSON('shadow_notes', []));

  const setNeeds = useCallback((data: Need[]) => {
    setNeedsState(data);
    saveJSON('shadow_needs', data);
  }, []);

  const setTargets = useCallback((data: TargetPlayer[]) => {
    setTargetsState(data);
    saveJSON('shadow_targets', data);
  }, []);

  const setXI = useCallback((data: ShadowXISlot[]) => {
    setXIState(data);
    saveJSON('shadow_xi', data);
  }, []);

  const setNotes = useCallback((data: Note[]) => {
    setNotesState(data);
    saveJSON('shadow_notes', data);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
          <Shield size={22} strokeWidth={1.5} style={{ color: 'var(--color-accent)' }} />
          Shadow Team
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>
          Gestão de alvos, necessidades e montagem do time ideal
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 p-1 rounded-xl" style={{ background: 'var(--color-surface-1)' }}>
        {TABS.map((tab) => (
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
      {activeTab === 'needs' && <TabNeeds needs={needs} setNeeds={setNeeds} />}
      {activeTab === 'targets' && <TabTargets targets={targets} setTargets={setTargets} needs={needs} />}
      {activeTab === 'comparison' && <TabComparison targets={targets} />}
      {activeTab === 'xi' && <TabShadowXI xi={xi} setXI={setXI} targets={targets} />}
      {activeTab === 'notes' && <TabNotes notes={notes} setNotes={setNotes} targets={targets} />}
    </motion.div>
  );
}
