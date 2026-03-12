import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield,
  BarChart3,
  Users,
  Search,
  Trophy,
  FileText,
  LogOut,
  Menu,
  X,
  ArrowLeftRight,
  Database,
  Target,
  Dna,
  FileBarChart,
} from 'lucide-react';
import type { User } from '../types/api';

export type TabId =
  | 'dashboard'
  | 'indices'
  | 'report'
  | 'comparison'
  | 'data'
  | 'rankings'
  | 'similarity'
  | 'prediction'
  | 'clusters'
  | 'offered'
  | 'analyses';

interface LayoutProps {
  user: User;
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  onLogout: () => void;
  children: React.ReactNode;
}

const NAV_ITEMS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: 'dashboard', label: 'Perfil', icon: <BarChart3 size={16} /> },
  { id: 'indices', label: 'Indices', icon: <FileBarChart size={16} /> },
  { id: 'report', label: 'Relatorio', icon: <FileText size={16} /> },
  { id: 'comparison', label: 'Comparativo', icon: <ArrowLeftRight size={16} /> },
  { id: 'data', label: 'Dados', icon: <Database size={16} /> },
  { id: 'rankings', label: 'Ranking', icon: <Trophy size={16} /> },
  { id: 'similarity', label: 'Similaridade', icon: <Search size={16} /> },
  { id: 'prediction', label: 'Predicao', icon: <Target size={16} /> },
  { id: 'clusters', label: 'Clusters', icon: <Dna size={16} /> },
  { id: 'offered', label: 'Oferecidos', icon: <Users size={16} /> },
  { id: 'analyses', label: 'Analises', icon: <BarChart3 size={16} /> },
];

export default function Layout({ user, activeTab, onTabChange, onLogout, children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen flex relative">
      <div className="noise-overlay" />

      {/* ── Sidebar ───────────────────────────────────────────────── */}
      <aside
        className="hidden lg:flex flex-col w-56 fixed top-0 left-0 h-screen z-30"
        style={{
          background: 'var(--color-surface-0)',
          borderRight: '1px solid var(--color-border-subtle)',
        }}
      >
        {/* Brand */}
        <div className="px-4 py-5 flex items-center gap-2.5">
          <img
            src="/3154_imgbank_1685113109.png"
            alt="Logo Botafogo-SP"
            className="w-8 h-8 object-contain"
          />
          <div>
            <div className="font-[var(--font-display)] text-sm font-bold tracking-tight">SCOUTING</div>
            <div className="text-[9px] tracking-[0.15em]" style={{ color: 'var(--color-text-muted)' }}>
              BOTAFOGO-SA
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2 py-2 space-y-0.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const active = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded text-sm transition-all duration-150 text-left cursor-pointer"
                style={{
                  background: active ? 'var(--color-accent-glow)' : 'transparent',
                  color: active ? 'var(--color-accent)' : 'var(--color-text-secondary)',
                  border: active ? '1px solid rgba(220, 38, 38, 0.2)' : '1px solid transparent',
                }}
              >
                {item.icon}
                <span className="font-[var(--font-display)] text-xs tracking-wide">{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* User footer */}
        <div
          className="px-4 py-3 flex items-center justify-between"
          style={{ borderTop: '1px solid var(--color-border-subtle)' }}
        >
          <div className="min-w-0">
            <div className="text-xs font-medium truncate" style={{ color: 'var(--color-text-primary)' }}>
              {user.name}
            </div>
            <div className="text-[10px] truncate" style={{ color: 'var(--color-text-muted)' }}>
              {user.role}
            </div>
          </div>
          <button
            onClick={onLogout}
            className="p-1.5 rounded transition-colors hover:bg-white/5 cursor-pointer"
            style={{ color: 'var(--color-text-muted)' }}
            title="Sair"
          >
            <LogOut size={14} />
          </button>
        </div>
      </aside>

      {/* ── Mobile header ─────────────────────────────────────────── */}
      <div
        className="lg:hidden fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-4 py-3"
        style={{
          background: 'var(--color-surface-0)',
          borderBottom: '1px solid var(--color-border-subtle)',
        }}
      >
        <div className="flex items-center gap-2">
          <Shield size={16} style={{ color: 'var(--color-accent)' }} />
          <span className="font-[var(--font-display)] text-sm font-bold">SCOUTING</span>
        </div>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-1.5 cursor-pointer"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 z-40 lg:hidden"
              onClick={() => setSidebarOpen(false)}
            />
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed top-0 left-0 bottom-0 w-56 z-50 flex flex-col lg:hidden"
              style={{
                background: 'var(--color-surface-0)',
                borderRight: '1px solid var(--color-border-subtle)',
              }}
            >
              <div className="px-4 py-5">
                <div className="font-[var(--font-display)] text-sm font-bold">SCOUTING BFSA</div>
              </div>
              <nav className="flex-1 px-2 space-y-0.5 overflow-y-auto">
                {NAV_ITEMS.map((item) => {
                  const active = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        onTabChange(item.id);
                        setSidebarOpen(false);
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 rounded text-sm text-left cursor-pointer"
                      style={{
                        background: active ? 'var(--color-accent-glow)' : 'transparent',
                        color: active ? 'var(--color-accent)' : 'var(--color-text-secondary)',
                      }}
                    >
                      {item.icon}
                      <span className="font-[var(--font-display)] text-xs">{item.label}</span>
                    </button>
                  );
                })}
              </nav>
              <div className="px-4 py-3" style={{ borderTop: '1px solid var(--color-border-subtle)' }}>
                <button
                  onClick={onLogout}
                  className="flex items-center gap-2 text-xs cursor-pointer"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  <LogOut size={13} />
                  Sair ({user.name})
                </button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ── Main content ──────────────────────────────────────────── */}
      <main className="flex-1 lg:ml-56 pt-14 lg:pt-0 relative z-10">
        <div className="max-w-7xl mx-auto px-4 lg:px-6 py-6">
          {children}
        </div>
      </main>
    </div>
  );
}
