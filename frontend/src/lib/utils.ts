import { twMerge } from 'tailwind-merge';

export function cn(...classes: (string | undefined | null | false)[]) {
  return twMerge(classes.filter(Boolean).join(' '));
}

export function getScoreClass(score: number): string {
  if (score >= 72) return 'score-elite';
  if (score >= 62) return 'score-above';
  if (score >= 50) return 'score-average';
  if (score >= 38) return 'score-below';
  return 'score-discard';
}

export function getScoreColor(score: number): string {
  if (score >= 72) return '#22c55e';
  if (score >= 62) return '#3b82f6';
  if (score >= 50) return '#eab308';
  if (score >= 38) return '#f97316';
  return '#ef4444';
}

export function getPerformanceLabel(cls: string | null): string {
  const map: Record<string, string> = {
    'Muito Alto': 'TOP TARGET',
    'Alto': 'ALTA PRIORIDADE',
    'Médio': 'MONITORAR',
    'Baixo': 'AVALIAR',
    'Muito Baixo': 'DESCARTAR',
  };
  return cls ? map[cls] || cls : '—';
}

export function formatNumber(val: number | null | undefined): string {
  if (val === null || val === undefined) return '—';
  return val % 1 === 0 ? val.toString() : val.toFixed(1);
}
