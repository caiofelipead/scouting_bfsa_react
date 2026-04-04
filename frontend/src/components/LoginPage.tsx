import { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, Mail, AlertCircle } from 'lucide-react';

interface LoginPageProps {
  onLogin: (email: string, password: string) => Promise<boolean>;
  loading: boolean;
  error: string | null;
}

export default function LoginPage({ onLogin, loading, error }: LoginPageProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onLogin(email, password);
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      <div className="noise-overlay" />

      {/* Background accent glow */}
      <div
        className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(227, 6, 19, 0.06) 0%, transparent 70%)',
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 w-full max-w-sm mx-4"
      >
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <motion.img
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1, duration: 0.5 }}
            src="/3154_imgbank_1685113109.png"
            alt="Logo Botafogo-SA"
            className="w-20 h-20 mx-auto mb-4 object-contain"
          />
          <h1 className="font-[var(--font-display)] text-xl font-bold tracking-tight">
            SCOUTING BFSA
          </h1>
          <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
            Plataforma de Analise de Jogadores
          </p>
        </div>

        {/* Login form */}
        <form onSubmit={handleSubmit} className="card-glass-accent rounded-lg p-6 space-y-4">
          <div>
            <label
              className="block text-[10px] font-[var(--font-display)] tracking-[0.15em] uppercase mb-2"
              style={{ color: 'var(--color-text-muted)' }}
            >
              E-MAIL
            </label>
            <div className="relative">
              <Mail
                size={14}
                className="absolute left-3 top-1/2 -translate-y-1/2"
                style={{ color: 'var(--color-text-muted)' }}
              />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@botafogo-sp.com"
                required
                className="w-full pl-9 pr-3 py-2.5 rounded text-sm outline-none input-focus"
                style={{
                  background: 'var(--color-surface-2)',
                  border: '1px solid var(--color-border-subtle)',
                  color: 'var(--color-text-primary)',
                  fontFamily: 'var(--font-body)',
                }}
              />
            </div>
          </div>

          <div>
            <label
              className="block text-[10px] font-[var(--font-display)] tracking-[0.15em] uppercase mb-2"
              style={{ color: 'var(--color-text-muted)' }}
            >
              SENHA
            </label>
            <div className="relative">
              <Lock
                size={14}
                className="absolute left-3 top-1/2 -translate-y-1/2"
                style={{ color: 'var(--color-text-muted)' }}
              />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="******"
                required
                className="w-full pl-9 pr-3 py-2.5 rounded text-sm outline-none input-focus"
                style={{
                  background: 'var(--color-surface-2)',
                  border: '1px solid var(--color-border-subtle)',
                  color: 'var(--color-text-primary)',
                  fontFamily: 'var(--font-body)',
                }}
              />
            </div>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 px-3 py-2 rounded text-xs banner-error"
            >
              <AlertCircle size={13} />
              {error}
            </motion.div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded text-sm font-[var(--font-display)] font-semibold tracking-wide uppercase transition-all duration-200 cursor-pointer disabled:opacity-50 focus-ring hover:brightness-110 active:scale-[0.98]"
            style={{
              background: loading ? 'var(--color-accent-dim)' : 'var(--color-accent)',
              color: '#fff',
              border: 'none',
            }}
          >
            {loading ? 'AUTENTICANDO...' : 'ENTRAR'}
          </button>
        </form>

        <p className="text-center text-[10px] mt-4" style={{ color: 'var(--color-text-muted)' }}>
          Botafogo Futebol SA — Departamento de Scouting
        </p>
      </motion.div>
    </div>
  );
}
