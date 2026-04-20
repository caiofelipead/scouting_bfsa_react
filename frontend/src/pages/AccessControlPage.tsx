import { useEffect, useMemo, useState } from 'react';
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
                      E-MAIL
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
                          {u.created_at ? u.created_at.split('.')[0].replace('T', ' ') : '—'}
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
    </div>
  );
}
