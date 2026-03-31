import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield,
  BarChart3,
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
  Activity,
  Eye,
  Sun,
  Moon,
  TrendingUp,
  Gem,
  Users,
  UserPlus,
  Globe,
} from 'lucide-react';
import type { User } from '../types/api';
import { useTheme } from '../contexts/ThemeContext';

export type TabId =
  | 'dashboard'
  | 'indices'
  | 'report'
  | 'comparison'
  | 'skillcorner'
  | 'data'
  | 'rankings'
  | 'prediction'
  | 'similarity'
  | 'clusters'
  | 'analyses'
  | 'trajectory'
  | 'opportunities'
  | 'replacements'
  | 'contract_impact'
  | 'scouting_report'
  | 'apifootball'
  | 'coaches';

interface LayoutProps {
  user: User;
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  onLogout: () => void;
  children: React.ReactNode;
}

const NAV_SECTIONS: { title?: string; items: { id: TabId; label: string; icon: React.ReactNode }[] }[] = [
  {
    title: 'ANALISE',
    items: [
      { id: 'dashboard', label: 'Dashboard Geral', icon: <BarChart3 size={18} strokeWidth={1.5} /> },
      { id: 'indices', label: 'Indices', icon: <FileBarChart size={18} strokeWidth={1.5} /> },
      { id: 'report', label: 'Relatorio', icon: <FileText size={18} strokeWidth={1.5} /> },
      { id: 'comparison', label: 'Comparativo', icon: <ArrowLeftRight size={18} strokeWidth={1.5} /> },
    ],
  },
  {
    title: 'MERCADO',
    items: [
      { id: 'rankings', label: 'Ranking', icon: <Trophy size={18} strokeWidth={1.5} /> },
      { id: 'prediction', label: 'Predicao', icon: <Target size={18} strokeWidth={1.5} /> },
      { id: 'trajectory', label: 'Trajetoria', icon: <TrendingUp size={18} strokeWidth={1.5} /> },
      { id: 'opportunities', label: 'Oportunidades', icon: <Gem size={18} strokeWidth={1.5} /> },
      { id: 'contract_impact', label: 'Impacto Contratação', icon: <UserPlus size={18} strokeWidth={1.5} /> },
    ],
  },
  {
    title: 'MONITORAMENTO',
    items: [
      { id: 'skillcorner', label: 'SkillCorner', icon: <Activity size={18} strokeWidth={1.5} /> },
      { id: 'similarity', label: 'Similaridade', icon: <Search size={18} strokeWidth={1.5} /> },
      { id: 'replacements', label: 'Substitutos', icon: <Users size={18} strokeWidth={1.5} /> },
      { id: 'clusters', label: 'Clusters', icon: <Dna size={18} strokeWidth={1.5} /> },
    ],
  },
  {
    title: 'GESTÃO',
    items: [
      { id: 'coaches', label: 'Treinadores', icon: <Users size={18} strokeWidth={1.5} /> },
    ],
  },
  {
    title: 'RELATORIOS',
    items: [
      { id: 'scouting_report', label: 'Scouting Report', icon: <FileText size={18} strokeWidth={1.5} /> },
      { id: 'apifootball', label: 'API-Football', icon: <Globe size={18} strokeWidth={1.5} /> },
      { id: 'data', label: 'Dados', icon: <Database size={18} strokeWidth={1.5} /> },
      { id: 'analyses', label: 'Analises', icon: <Eye size={18} strokeWidth={1.5} /> },
    ],
  },
];

// Flat list for mobile
const ALL_NAV_ITEMS = NAV_SECTIONS.flatMap((s) => s.items);

export default function Layout({ user, activeTab, onTabChange, onLogout, children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen flex relative">
      <div className="noise-overlay" />

      {/* ── Sidebar (Desktop) ─────────────────────────────────────── */}
      <aside
        className="hidden lg:flex flex-col fixed top-0 left-0 h-screen z-30"
        style={{
          width: '280px',
          background: theme === 'dark' ? 'rgba(14, 14, 14, 0.85)' : 'rgba(255, 255, 255, 0.82)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderRight: '1px solid var(--color-border-subtle)',
        }}
      >
        {/* Brand */}
        <div className="px-5 py-5 flex items-center gap-3">
          <img
            src="/3154_imgbank_1685113109.png"
            alt="Logo Botafogo-SP"
            className="w-9 h-9 object-contain"
          />
          <div>
            <div className="font-[var(--font-display)] text-sm font-bold tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
              SCOUTING
            </div>
            <div className="text-[9px] tracking-[0.2em] font-semibold" style={{ color: 'var(--color-text-muted)' }}>
              BOTAFOGO-SA
            </div>
          </div>
        </div>

        {/* Nav sections */}
        <nav className="flex-1 px-3 py-2 overflow-y-auto space-y-4">
          {NAV_SECTIONS.map((section, si) => (
            <div key={si}>
              {section.title && (
                <div
                  className="px-3 mb-2 text-[9px] font-[var(--font-display)] tracking-[0.2em] font-semibold"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  {section.title}
                </div>
              )}
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const active = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => onTabChange(item.id)}
                      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 text-left cursor-pointer relative overflow-hidden"
                      style={{
                        background: active ? 'var(--color-accent-glow)' : 'transparent',
                        color: active ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
                      }}
                    >
                      {/* Vertical red indicator for active */}
                      {active && (
                        <motion.div
                          layoutId="sidebar-indicator"
                          className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full"
                          style={{ background: 'var(--color-accent)' }}
                          transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                        />
                      )}
                      <span style={{ color: active ? 'var(--color-accent)' : 'var(--color-text-muted)' }}>
                        {item.icon}
                      </span>
                      <span className="font-[var(--font-body)] text-[13px] font-medium">{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* User footer */}
        <div
          className="px-5 py-4 flex items-center justify-between"
          style={{ borderTop: '1px solid var(--color-border-subtle)' }}
        >
          <div className="min-w-0">
            <div className="text-xs font-semibold truncate" style={{ color: 'var(--color-text-primary)' }}>
              {user.name}
            </div>
            <div className="text-[10px] truncate" style={{ color: 'var(--color-text-muted)' }}>
              {user.role}
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg transition-colors hover:bg-white/5 cursor-pointer"
              style={{ color: 'var(--color-text-muted)' }}
              title={theme === 'dark' ? 'Modo claro' : 'Modo escuro'}
            >
              {theme === 'dark' ? <Sun size={16} strokeWidth={1.5} /> : <Moon size={16} strokeWidth={1.5} />}
            </button>
            <button
              onClick={onLogout}
              className="p-2 rounded-lg transition-colors hover:bg-white/5 cursor-pointer"
              style={{ color: 'var(--color-text-muted)' }}
              title="Sair"
            >
              <LogOut size={16} strokeWidth={1.5} />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Mobile header ─────────────────────────────────────────── */}
      <div
        className="lg:hidden fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-4 py-3"
        style={{
          background: theme === 'dark' ? 'rgba(14, 14, 14, 0.9)' : 'rgba(255, 255, 255, 0.88)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderBottom: '1px solid var(--color-border-subtle)',
        }}
      >
        <div className="flex items-center gap-2">
          <Shield size={16} strokeWidth={1.5} style={{ color: 'var(--color-accent)' }} />
          <span className="font-[var(--font-display)] text-sm font-bold" style={{ color: 'var(--color-text-primary)' }}>SCOUTING</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={toggleTheme}
            className="p-1.5 cursor-pointer"
            style={{ color: 'var(--color-text-secondary)' }}
            title={theme === 'dark' ? 'Modo claro' : 'Modo escuro'}
          >
            {theme === 'dark' ? <Sun size={16} strokeWidth={1.5} /> : <Moon size={16} strokeWidth={1.5} />}
          </button>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 cursor-pointer"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
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
              className="fixed top-0 left-0 bottom-0 z-50 flex flex-col lg:hidden"
              style={{
                width: '280px',
                background: theme === 'dark' ? 'rgba(14, 14, 14, 0.95)' : 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)',
                borderRight: '1px solid var(--color-border-subtle)',
              }}
            >
              <div className="px-5 py-5 flex items-center gap-3">
                <Shield size={18} strokeWidth={1.5} style={{ color: 'var(--color-accent)' }} />
                <div className="font-[var(--font-display)] text-sm font-bold">SCOUTING BFSA</div>
              </div>
              <nav className="flex-1 px-3 space-y-4 overflow-y-auto">
                {NAV_SECTIONS.map((section, si) => (
                  <div key={si}>
                    {section.title && (
                      <div
                        className="px-3 mb-2 text-[9px] font-[var(--font-display)] tracking-[0.2em] font-semibold"
                        style={{ color: 'var(--color-text-muted)' }}
                      >
                        {section.title}
                      </div>
                    )}
                    <div className="space-y-0.5">
                      {section.items.map((item) => {
                        const active = activeTab === item.id;
                        return (
                          <button
                            key={item.id}
                            onClick={() => {
                              onTabChange(item.id);
                              setSidebarOpen(false);
                            }}
                            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-left cursor-pointer relative"
                            style={{
                              background: active ? 'var(--color-accent-glow)' : 'transparent',
                              color: active ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
                            }}
                          >
                            {active && (
                              <div
                                className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full"
                                style={{ background: 'var(--color-accent)' }}
                              />
                            )}
                            <span style={{ color: active ? 'var(--color-accent)' : 'var(--color-text-muted)' }}>
                              {item.icon}
                            </span>
                            <span className="font-[var(--font-body)] text-[13px] font-medium">{item.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </nav>
              <div className="px-5 py-4" style={{ borderTop: '1px solid var(--color-border-subtle)' }}>
                <button
                  onClick={onLogout}
                  className="flex items-center gap-2 text-xs cursor-pointer"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  <LogOut size={14} strokeWidth={1.5} />
                  Sair ({user.name})
                </button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ── Main content ──────────────────────────────────────────── */}
      <main className="flex-1 pt-14 lg:pt-0 relative z-10" style={{ marginLeft: '0', paddingLeft: '0' }}>
        <div className="lg:hidden" />
        <div className="max-w-7xl mx-auto px-4 lg:px-8 py-6" style={{ marginLeft: '0' }}>
          {children}
        </div>
      </main>

      {/* Spacer for sidebar width on desktop */}
      <style>{`
        @media (min-width: 1024px) {
          main { margin-left: 280px !important; }
        }
      `}</style>
    </div>
  );
}
