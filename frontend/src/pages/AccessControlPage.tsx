import { useEffect, useMemo, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Lock,
  ShieldCheck,
  Eye,
  User as UserIcon,
  Check,
  X as XIcon,
  AlertTriangle,
  ScrollText,
  RefreshCw,
  LogIn,
  MousePointerClick,
} from 'lucide-react';
import api from '../lib/api';
import type { User } from '../types/api';

interface AdminUser {
  id: number;
  email: string;
  name: string;
  role: string;
  created_at: string | null;
}

interface AccessLog {
  id: number;
  email: string | null;
  event_type: string;
  path: string | null;
  ip: string | null;
  user_agent: string | null;
  detail: string | null;
  created_at: string | null;
}

const EVENT_META: Record<string, { label: string; color: string; icon: typeof LogIn }> = {
  login_success: { label: 'Login',         color: 'var(--color-elite)',     icon: LogIn },
  login_failure: { label: 'Login falhou',  color: 'var(--color-accent)',    icon: XIcon },
  page_view:     { label: 'Abriu aba',     color: '#3b82f6',                icon: MousePointerClick },
  user_created:  { label: 'Usuário criado', color: 'var(--color-above)',    icon: UserIcon },
  user_deleted:  { label: 'Usuário removido', color: 'var(--color-accent)', icon: UserIcon },
};

function eventMeta(type: string) {
  return EVENT_META[type] ?? { label: type, color: 'var(--color-text-muted)', icon: ScrollText };
}

function formatTimestamp(iso: string | null): string {
  if (!iso) return '—';
  // Backend returns UTC timestamps without timezone info; parse as UTC.
  const normalized = iso.includes('T') ? iso : iso.replace(' ', 'T');
  const withZ = normalized.endsWith('Z') || /[+-]\d{2}:?\d{2}$/.test(normalized)
    ? normalized
    : normalized + 'Z';
  const d = new Date(withZ);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function shortUserAgent(ua: string | null): string {
  if (!ua) return '—';
  const m = ua.match(/(Chrome|Firefox|Safari|Edg|OPR)\/([\d.]+)/);
  const browser = m ? `${m[1].replace('Edg', 'Edge').replace('OPR', 'Opera')} ${m[2].split('.')[0]}` : 'Desconhecido';
  let os = 'Outro';
  if (/Windows/.test(ua)) os = 'Windows';
  else if (/Mac OS X|Macintosh/.test(ua)) os = 'macOS';
  else if (/Android/.test(ua)) os = 'Android';
  else if (/iPhone|iPad|iOS/.test(ua)) os = 'iOS';
  else if (/Linux/.test(ua)) os = 'Linux';
  return `${browser} · ${os}`;
}

interface PermissionRow {
  label: string;
  admin: boolean;
  viewer: boolean;
  analyst: boolean;
}

const PERMISSIONS: PermissionRow[] = [
  { label: 'Visualizar dashboards e análises',   admin: true,  viewer: true,  analyst: true  },
  { label: 'Acessar rankings, previsões e clusters', admin: true, viewer: true, analyst: true },
  { label: 'Consultar SkillCorner e similaridade', admin: true, viewer: true, analyst: true },
  { label: 'Ver Treinadores',                    admin: true,  viewer: true,  analyst: false },
  { label: 'Ver Shadow Team',                    admin: true,  viewer: true,  analyst: true  },
  { label: 'Ver Scouting Report e Relatórios',   admin: true,  viewer: true,  analyst: true  },
  { label: 'Editar Shadow Team',                 admin: true,  viewer: false, analyst: true  },
  { label: 'Ressincronizar dados (Google Sheets)', admin: true, viewer: false, analyst: false },
  { label: 'Gerenciar usuários e acessos',       admin: true,  viewer: false, analyst: false },
];

const ROLE_META: Record<string, { label: string; desc: string; badge: string; color: string }> = {
  admin: {
    label: 'Administrador',
    desc: 'Acesso total ao sistema, incluindo edição e gestão de usuários.',
    badge: 'ADMIN',
    color: 'var(--color-accent)',
  },
  viewer: {
    label: 'Visualizador Pleno',
    desc: 'Acesso pleno a todas as abas, somente leitura. Não edita dados.',
    badge: 'VIEWER',
    color: '#3b82f6',
  },
  analyst: {
    label: 'Analista',
    desc: 'Acesso padrão às ferramentas de análise e scouting.',
    badge: 'ANALYST',
    color: 'var(--color-above)',
  },
};

function roleMeta(role: string) {
  return ROLE_META[role] ?? {
    label: role,
    desc: 'Perfil personalizado.',
    badge: role.toUpperCase(),
    color: 'var(--color-text-muted)',
  };
}

function getCurrentUser(): User | null {
  try {
    const raw = localStorage.getItem('user');
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

export default function AccessControlPage() {
  const currentUser = useMemo(getCurrentUser, []);
  const isAdmin = currentUser?.role === 'admin';

  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [logs, setLogs] = useState<AccessLog[] | null>(null);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logsError, setLogsError] = useState<string | null>(null);
  const [logFilterUser, setLogFilterUser] = useState<string>('');
  const [logFilterEvent, setLogFilterEvent] = useState<string>('');

  const fetchLogs = useCallback(async () => {
    if (!isAdmin) return;
    setLogsLoading(true);
    setLogsError(null);
    try {
      const params: Record<string, string | number> = { limit: 300 };
      if (logFilterUser) params.email = logFilterUser;
      if (logFilterEvent) params.event_type = logFilterEvent;
      const res = await api.get<AccessLog[]>('/admin/access-logs', { params });
      setLogs(res.data);
    } catch (e: any) {
      setLogsError(e?.response?.data?.detail || e?.message || 'Erro ao carregar registros');
    } finally {
      setLogsLoading(false);
    }
  }, [isAdmin, logFilterUser, logFilterEvent]);

  useEffect(() => {
    if (!isAdmin) return;
    let cancelled = false;
    setLoading(true);
    api
      .get<AdminUser[]>('/admin/users')
      .then((res) => {
        if (!cancelled) setUsers(res.data);
      })
      .catch((e) => {
        if (!cancelled) {
          const msg = e?.response?.data?.detail || e?.message || 'Erro ao carregar usuários';
          setError(msg);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [isAdmin]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return (
    <div className="space-y-8 pb-10">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex items-center gap-3 mb-2">
          <div
            className="p-2 rounded-lg"
            style={{ background: 'var(--color-accent-glow)', color: 'var(--color-accent)' }}
          >
            <Lock size={20} strokeWidth={1.75} />
          </div>
          <div>
            <h1
              className="font-[var(--font-display)] text-2xl font-bold tracking-tight"
              style={{ color: 'var(--color-text-primary)' }}
            >
              Controle de Acesso
            </h1>
            <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
              Perfis, permissões e usuários cadastrados no sistema.
            </p>
          </div>
        </div>
      </motion.div>

      {/* Confidential banner */}
      <div
        className="card-glass-accent rounded-xl p-4 flex items-start gap-3"
        style={{ borderLeft: '3px solid var(--color-accent)' }}
      >
        <AlertTriangle size={18} style={{ color: 'var(--color-accent)' }} className="mt-0.5 shrink-0" />
        <div className="text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
          <span className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>
            Informação confidencial.
          </span>{' '}
          Este conteúdo é de uso interno do Botafogo-SA. Não compartilhe telas, prints ou dados com
          terceiros não autorizados.
        </div>
      </div>

      {/* Role descriptions */}
      <section className="space-y-3">
        <h2
          className="text-[10px] tracking-[0.2em] font-[var(--font-display)] font-semibold"
          style={{ color: 'var(--color-text-muted)' }}
        >
          PERFIS DE ACESSO
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {(['admin', 'viewer', 'analyst'] as const).map((role) => {
            const meta = roleMeta(role);
            const Icon = role === 'admin' ? ShieldCheck : role === 'viewer' ? Eye : UserIcon;
            return (
              <div key={role} className="card-glass rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className="p-1.5 rounded-md"
                    style={{ background: 'var(--color-surface-2)', color: meta.color }}
                  >
                    <Icon size={14} strokeWidth={1.75} />
                  </span>
                  <span
                    className="font-[var(--font-mono)] text-[10px] tracking-[0.15em] font-semibold px-2 py-0.5 rounded"
                    style={{ background: 'var(--color-surface-2)', color: meta.color }}
                  >
                    {meta.badge}
                  </span>
                </div>
                <div
                  className="text-sm font-semibold mb-1"
                  style={{ color: 'var(--color-text-primary)' }}
                >
                  {meta.label}
                </div>
                <div className="text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                  {meta.desc}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Permission matrix */}
      <section className="space-y-3">
        <h2
          className="text-[10px] tracking-[0.2em] font-[var(--font-display)] font-semibold"
          style={{ color: 'var(--color-text-muted)' }}
        >
          MATRIZ DE PERMISSÕES
        </h2>
        <div className="card-glass rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <th
                    className="text-left px-4 py-3 font-[var(--font-display)] text-[10px] tracking-[0.15em] font-semibold"
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    PERMISSÃO
                  </th>
                  <th
                    className="text-center px-4 py-3 font-[var(--font-display)] text-[10px] tracking-[0.15em] font-semibold"
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    ADMIN
                  </th>
                  <th
                    className="text-center px-4 py-3 font-[var(--font-display)] text-[10px] tracking-[0.15em] font-semibold"
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    VIEWER
                  </th>
                  <th
                    className="text-center px-4 py-3 font-[var(--font-display)] text-[10px] tracking-[0.15em] font-semibold"
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    ANALYST
                  </th>
                </tr>
              </thead>
              <tbody>
                {PERMISSIONS.map((row, i) => (
                  <tr
                    key={i}
                    style={{
                      borderBottom:
                        i === PERMISSIONS.length - 1
                          ? 'none'
                          : '1px solid var(--color-border-subtle)',
                    }}
                  >
                    <td className="px-4 py-2.5" style={{ color: 'var(--color-text-secondary)' }}>
                      {row.label}
                    </td>
                    {(['admin', 'viewer', 'analyst'] as const).map((role) => (
                      <td key={role} className="px-4 py-2.5 text-center">
                        {row[role] ? (
                          <Check size={14} strokeWidth={2} style={{ color: 'var(--color-elite)', display: 'inline' }} />
                        ) : (
                          <XIcon size={14} strokeWidth={2} style={{ color: 'var(--color-text-muted)', display: 'inline', opacity: 0.5 }} />
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Users list */}
      <section className="space-y-3">
        <h2
          className="text-[10px] tracking-[0.2em] font-[var(--font-display)] font-semibold"
          style={{ color: 'var(--color-text-muted)' }}
        >
          USUÁRIOS CADASTRADOS
        </h2>

        {!isAdmin && (
          <div className="card-glass rounded-xl p-6 text-center">
            <ScrollText size={18} className="mx-auto mb-2" style={{ color: 'var(--color-text-muted)' }} />
            <div className="text-sm font-semibold mb-1" style={{ color: 'var(--color-text-primary)' }}>
              Lista restrita a administradores
            </div>
            <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
              A relação completa de usuários só é visível para o perfil Administrador.
            </div>
          </div>
        )}

        {isAdmin && loading && (
          <div className="card-glass rounded-xl p-6 text-center text-xs" style={{ color: 'var(--color-text-muted)' }}>
            Carregando usuários...
          </div>
        )}

        {isAdmin && error && (
          <div className="banner-error rounded-xl p-4 text-xs">{error}</div>
        )}

        {isAdmin && users && (
          <div className="card-glass rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                    <th
                      className="text-left px-4 py-3 font-[var(--font-display)] text-[10px] tracking-[0.15em] font-semibold"
                      style={{ color: 'var(--color-text-muted)' }}
                    >
                      NOME
                    </th>
                    <th
                      className="text-left px-4 py-3 font-[var(--font-display)] text-[10px] tracking-[0.15em] font-semibold"
                      style={{ color: 'var(--color-text-muted)' }}
                    >
                      USUÁRIO
                    </th>
                    <th
                      className="text-left px-4 py-3 font-[var(--font-display)] text-[10px] tracking-[0.15em] font-semibold"
                      style={{ color: 'var(--color-text-muted)' }}
                    >
                      PERFIL
                    </th>
                    <th
                      className="text-left px-4 py-3 font-[var(--font-display)] text-[10px] tracking-[0.15em] font-semibold"
                      style={{ color: 'var(--color-text-muted)' }}
                    >
                      CRIADO EM
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u, i) => {
                    const meta = roleMeta(u.role);
                    return (
                      <tr
                        key={u.id}
                        style={{
                          borderBottom:
                            i === users.length - 1
                              ? 'none'
                              : '1px solid var(--color-border-subtle)',
                        }}
                      >
                        <td className="px-4 py-2.5" style={{ color: 'var(--color-text-primary)' }}>
                          {u.name}
                        </td>
                        <td
                          className="px-4 py-2.5 font-[var(--font-mono)]"
                          style={{ color: 'var(--color-text-secondary)' }}
                        >
                          {u.email}
                        </td>
                        <td className="px-4 py-2.5">
                          <span
                            className="font-[var(--font-mono)] text-[10px] tracking-[0.12em] font-semibold px-2 py-0.5 rounded"
                            style={{ background: 'var(--color-surface-2)', color: meta.color }}
                          >
                            {meta.badge}
                          </span>
                        </td>
                        <td
                          className="px-4 py-2.5 font-[var(--font-mono)] text-[11px]"
                          style={{ color: 'var(--color-text-muted)' }}
                        >
                          {formatTimestamp(u.created_at)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      {/* Access logs — admin only */}
      {isAdmin && (
        <section className="space-y-3">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <h2
              className="text-[10px] tracking-[0.2em] font-[var(--font-display)] font-semibold"
              style={{ color: 'var(--color-text-muted)' }}
            >
              REGISTRO DE ACESSOS
            </h2>
            <div className="flex items-center gap-2 flex-wrap">
              <select
                value={logFilterUser}
                onChange={(e) => setLogFilterUser(e.target.value)}
                className="text-xs rounded px-2 py-1.5 outline-none input-focus"
                style={{
                  background: 'var(--color-surface-2)',
                  border: '1px solid var(--color-border-subtle)',
                  color: 'var(--color-text-primary)',
                  fontFamily: 'var(--font-body)',
                }}
              >
                <option value="">Todos os usuários</option>
                {(users ?? []).map((u) => (
                  <option key={u.id} value={u.email}>
                    {u.name} ({u.email})
                  </option>
                ))}
              </select>
              <select
                value={logFilterEvent}
                onChange={(e) => setLogFilterEvent(e.target.value)}
                className="text-xs rounded px-2 py-1.5 outline-none input-focus"
                style={{
                  background: 'var(--color-surface-2)',
                  border: '1px solid var(--color-border-subtle)',
                  color: 'var(--color-text-primary)',
                  fontFamily: 'var(--font-body)',
                }}
              >
                <option value="">Todos os eventos</option>
                <option value="login_success">Login</option>
                <option value="login_failure">Login falhou</option>
                <option value="page_view">Abriu aba</option>
                <option value="user_created">Usuário criado</option>
                <option value="user_deleted">Usuário removido</option>
              </select>
              <button
                onClick={fetchLogs}
                disabled={logsLoading}
                className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded btn-ghost focus-ring cursor-pointer disabled:opacity-50"
                style={{ color: 'var(--color-text-secondary)' }}
                title="Atualizar"
              >
                <RefreshCw size={13} strokeWidth={1.5} className={logsLoading ? 'animate-spin' : ''} />
                Atualizar
              </button>
            </div>
          </div>

          {logsError && <div className="banner-error rounded-xl p-4 text-xs">{logsError}</div>}

          {!logsError && logs && logs.length === 0 && !logsLoading && (
            <div className="card-glass rounded-xl p-6 text-center text-xs" style={{ color: 'var(--color-text-muted)' }}>
              Nenhum registro encontrado com esses filtros.
            </div>
          )}

          {!logsError && logs && logs.length > 0 && (
            <div className="card-glass rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                      {['DATA / HORA', 'USUÁRIO', 'EVENTO', 'DETALHES', 'IP', 'DISPOSITIVO'].map((h) => (
                        <th
                          key={h}
                          className="text-left px-3 py-2.5 font-[var(--font-display)] text-[10px] tracking-[0.15em] font-semibold"
                          style={{ color: 'var(--color-text-muted)' }}
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log, i) => {
                      const meta = eventMeta(log.event_type);
                      const Icon = meta.icon;
                      return (
                        <tr
                          key={log.id}
                          style={{
                            borderBottom:
                              i === logs.length - 1
                                ? 'none'
                                : '1px solid var(--color-border-subtle)',
                          }}
                        >
                          <td
                            className="px-3 py-2 font-[var(--font-mono)] text-[11px] whitespace-nowrap"
                            style={{ color: 'var(--color-text-secondary)' }}
                          >
                            {formatTimestamp(log.created_at)}
                          </td>
                          <td
                            className="px-3 py-2 font-[var(--font-mono)]"
                            style={{ color: log.email ? 'var(--color-text-primary)' : 'var(--color-text-muted)' }}
                          >
                            {log.email || '—'}
                          </td>
                          <td className="px-3 py-2">
                            <span
                              className="inline-flex items-center gap-1.5 font-[var(--font-mono)] text-[10px] tracking-[0.08em] font-semibold px-2 py-0.5 rounded whitespace-nowrap"
                              style={{ background: 'var(--color-surface-2)', color: meta.color }}
                            >
                              <Icon size={11} strokeWidth={2} />
                              {meta.label}
                            </span>
                          </td>
                          <td
                            className="px-3 py-2 font-[var(--font-mono)] text-[11px]"
                            style={{ color: 'var(--color-text-secondary)' }}
                          >
                            {log.path || log.detail || '—'}
                            {log.path && log.detail && (
                              <span className="block text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                                {log.detail}
                              </span>
                            )}
                          </td>
                          <td
                            className="px-3 py-2 font-[var(--font-mono)] text-[11px] whitespace-nowrap"
                            style={{ color: 'var(--color-text-muted)' }}
                          >
                            {log.ip || '—'}
                          </td>
                          <td
                            className="px-3 py-2 text-[11px]"
                            style={{ color: 'var(--color-text-muted)' }}
                          >
                            {shortUserAgent(log.user_agent)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <p className="text-[10px] italic" style={{ color: 'var(--color-text-muted)' }}>
            Os registros são mantidos para auditoria. Em caso de suspeita de vazamento, use estes
            dados para identificar o usuário, horário e dispositivo responsáveis.
          </p>
        </section>
      )}
    </div>
  );
}
