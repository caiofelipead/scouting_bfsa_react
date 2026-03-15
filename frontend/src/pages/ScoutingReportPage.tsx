import { useState, useRef, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, Download, Loader2, Eye, Zap } from 'lucide-react';
import { useScoutingReport, useAnalysesPlayers, useSkillCornerSearchReport, useSkillCornerPlayer } from '../hooks/useScoutingReport';
import api from '../lib/api';
import { usePlayers } from '../hooks/usePlayers';
import ReportHeader from '../components/report/ReportHeader';
import SectionDivider from '../components/report/SectionDivider';
import StatBox from '../components/report/StatBox';
import ReportRadar from '../components/report/ReportRadar';
import WedgeRadar from '../components/report/WedgeRadar';
import DeltaChart from '../components/report/DeltaChart';

// ── Google Fonts link (injected once) ──
const FONTS_HREF =
  'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap';

function injectFonts() {
  if (document.querySelector(`link[href="${FONTS_HREF}"]`)) return;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = FONTS_HREF;
  document.head.appendChild(link);
}

// ── Botafogo shield path (public) ──
const BFSA_SHIELD = '/3154_imgbank_1685113109.png';

// ── Colors ──
const C = {
  red: '#C8102E',
  redBright: '#E8213F',
  redDark: '#A00D24',
  navy: '#0C1B37',
  teal: '#80CBA2',
  green: '#1B9E5A',
  amber: '#D97706',
  blue: '#3B82F6',
  bg: '#F7F6F3',
  bgCard: '#FFFFFF',
  bgSubtle: '#EEEDEA',
  bgMuted: '#E5E4E0',
  textPrimary: '#1A1A1A',
  textSecondary: '#4A4A4A',
  textTertiary: '#8A8A8A',
  textMuted: '#B0B0B0',
};

// ── Quadrant colors ──
const QUADRANT = {
  tactical: C.red,
  technical: C.green,
  physical: C.amber,
  mental: C.blue,
};

// ── Slide dimensions (16:9 landscape, matching reference 1440×809) ──
const PAGE_WIDTH = 1440;
const PAGE_HEIGHT = 809;

// ── Page wrapper component with shield watermark + auto-scaling ──
function ReportPage({ children, noPadding }: { children: React.ReactNode; noPadding?: boolean }) {
  return (
    <SlideScaler>
      <div data-slide style={{
        ...pageStyles.page,
        padding: noPadding ? 0 : '36px 52px 44px',
      }}>
        {/* Shield watermark */}
        <img
          src={BFSA_SHIELD}
          alt=""
          style={pageStyles.watermark}
        />
        {/* Footer */}
        <div style={pageStyles.footer}>
          <img src={BFSA_SHIELD} alt="" style={{ width: 14, height: 14, objectFit: 'contain', opacity: 0.5 }} />
          <span style={pageStyles.footerText}>BOTAFOGO FUTEBOL SA — DEPARTAMENTO DE SCOUTING</span>
        </div>
        {children}
      </div>
    </SlideScaler>
  );
}

const pageStyles: Record<string, React.CSSProperties> = {
  page: {
    width: PAGE_WIDTH,
    height: PAGE_HEIGHT,
    background: '#FFFFFF',
    borderRadius: 10,
    boxShadow: '0 4px 24px rgba(0,0,0,0.10)',
    position: 'relative',
    overflow: 'hidden',
    overflowX: 'hidden',
    pageBreakAfter: 'always',
    boxSizing: 'border-box',
    display: 'flex',
    flexDirection: 'column',
  },
  watermark: {
    position: 'absolute',
    bottom: 24,
    right: 36,
    width: 60,
    height: 60,
    objectFit: 'contain',
    opacity: 0.04,
    pointerEvents: 'none',
  },
  footer: {
    position: 'absolute',
    bottom: 12,
    left: 52,
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  footerText: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 8,
    fontWeight: 600,
    letterSpacing: '0.12em',
    color: '#C0C0C0',
    textTransform: 'uppercase',
  },
};

// ── Slide scaler: scales 1440px slides to fit viewport ──
function SlideScaler({ children }: { children: React.ReactNode }) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(0.7); // Start small to prevent flash of oversized content

  useEffect(() => {
    function updateScale() {
      if (!wrapperRef.current) return;
      // Walk up to find the report container (the element with constrained width)
      // Skip motion.div wrappers that shrink-to-fit their content
      let container = wrapperRef.current.parentElement;
      while (container && container.clientWidth >= PAGE_WIDTH) {
        if (container.parentElement) {
          container = container.parentElement;
        } else {
          break;
        }
      }
      const availableWidth = container ? container.clientWidth - 48 : window.innerWidth - 260;
      const s = Math.min(1, availableWidth / PAGE_WIDTH);
      setScale(s);
    }
    updateScale();
    window.addEventListener('resize', updateScale);
    return () => window.removeEventListener('resize', updateScale);
  }, []);

  return (
    <div
      ref={wrapperRef}
      style={{
        width: PAGE_WIDTH * scale,
        height: PAGE_HEIGHT * scale,
        marginBottom: 24,
        margin: '0 auto 24px',
      }}
    >
      <div style={{
        transform: `scale(${scale})`,
        transformOrigin: 'top left',
        width: PAGE_WIDTH,
        height: PAGE_HEIGHT,
      }}>
        {children}
      </div>
    </div>
  );
}

// ── Skeleton ──
function Skeleton({ width, height }: { width: string | number; height: string | number }) {
  return (
    <div
      style={{
        width,
        height,
        borderRadius: 8,
        background: `linear-gradient(90deg, ${C.bgSubtle} 25%, ${C.bgMuted} 50%, ${C.bgSubtle} 75%)`,
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.5s infinite',
      }}
    />
  );
}

// ── Embed Google Fonts as base64 for PDF export ──
let _cachedEmbeddedFontCSS: string | null = null;

async function getEmbeddedFontCSS(): Promise<string> {
  if (_cachedEmbeddedFontCSS) return _cachedEmbeddedFontCSS;
  try {
    // Fetch Google Fonts CSS (must use a browser-like User-Agent to get woff2)
    const cssResp = await fetch(FONTS_HREF, {
      headers: { 'User-Agent': navigator.userAgent },
    });
    if (!cssResp.ok) return '';
    let css = await cssResp.text();

    // Find all url(...) references and replace with base64 data URIs
    const urlRegex = /url\((https:\/\/fonts\.gstatic\.com\/[^)]+)\)/g;
    const urls = new Set<string>();
    let match: RegExpExecArray | null;
    while ((match = urlRegex.exec(css)) !== null) urls.add(match[1]);

    const urlMap = new Map<string, string>();
    await Promise.all(
      Array.from(urls).map(async (fontUrl) => {
        try {
          const resp = await fetch(fontUrl);
          if (!resp.ok) return;
          const blob = await resp.blob();
          const dataUrl = await new Promise<string>((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result as string);
            reader.readAsDataURL(blob);
          });
          urlMap.set(fontUrl, dataUrl);
        } catch { /* skip */ }
      }),
    );

    urlMap.forEach((dataUrl, fontUrl) => {
      css = css.split(fontUrl).join(dataUrl);
    });

    _cachedEmbeddedFontCSS = css;
    return css;
  } catch {
    return '';
  }
}

// ── Page ──
export default function ScoutingReportPage() {
  injectFonts();

  // Independent selectors — none depends on the other
  const [playerSearch, setPlayerSearch] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
  const [incumbentSearch, setIncumbentSearch] = useState('');
  const [selectedIncumbent, setSelectedIncumbent] = useState<string | null>(null);
  const [showPlayerDropdown, setShowPlayerDropdown] = useState(false);
  const [showIncumbentDropdown, setShowIncumbentDropdown] = useState(false);

  // Analyses (independent)
  const [showAnalysesDropdown, setShowAnalysesDropdown] = useState(false);
  const [analysesSearch, setAnalysesSearch] = useState('');
  const [selectedAnalysesPlayer, setSelectedAnalysesPlayer] = useState<import('../hooks/useScoutingReport').AnalysesPlayerData | null>(null);

  // SkillCorner (independent)
  const [scSearch, setScSearch] = useState('');
  const [selectedSC, setSelectedSC] = useState<string | null>(null);
  const [showSCDropdown, setShowSCDropdown] = useState(false);

  // SkillCorner internal comparison (on the slide itself)
  const [scInternalSearch, setScInternalSearch] = useState('');
  const [selectedSCInternal, setSelectedSCInternal] = useState<string | null>(null);
  const [showSCInternalDropdown, setShowSCInternalDropdown] = useState(false);

  // Club logo upload
  const [customClubLogo, setCustomClubLogo] = useState<string | null>(null);
  const clubLogoInputRef = useRef<HTMLInputElement>(null);

  const reportRef = useRef<HTMLDivElement>(null);

  const playersQuery = usePlayers({ search: playerSearch, limit: 8 });
  const incumbentQuery = usePlayers({ search: incumbentSearch, limit: 8 });
  const analysesQuery = useAnalysesPlayers(analysesSearch);
  const scSearchQuery = useSkillCornerSearchReport(scSearch);

  const scInternalSearchQuery = useSkillCornerSearchReport(scInternalSearch);
  const scInternalQuery = useSkillCornerPlayer(selectedSCInternal);

  const { data, isLoading, isError, predictionLoading, similarityLoading, skillCornerLoading, comparisonLoading } =
    useScoutingReport(selectedPlayer, selectedIncumbent, selectedAnalysesPlayer, selectedSC);

  const fadeIn = (delay = 0) => ({
    initial: { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4, delay, ease: [0.22, 1, 0.36, 1] },
  });

  const [exporting, setExporting] = useState(false);

  /** Convert a URL to a base64 data URL */
  async function toDataUrl(url: string): Promise<string | null> {
    try {
      const resp = await fetch(url, { mode: 'cors', credentials: 'same-origin' });
      if (!resp.ok) return null;
      const blob = await resp.blob();
      return await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result as string);
        reader.readAsDataURL(blob);
      });
    } catch { return null; }
  }

  const handleExportPDF = useCallback(async () => {
    if (!reportRef.current || exporting) return;
    setExporting(true);
    try {
      const slides = reportRef.current.querySelectorAll<HTMLElement>('[data-slide]');
      if (!slides.length) { setExporting(false); return; }

      // ── 1. Get embedded font CSS ──
      const embeddedFontCSS = await getEmbeddedFontCSS();

      // ── 2. Convert proxy images to data URLs in cloned nodes ──
      const slideHtmls: string[] = [];
      for (const slide of Array.from(slides)) {
        const clone = slide.cloneNode(true) as HTMLElement;
        // Remove no-print elements
        clone.querySelectorAll('.no-print').forEach((el) => el.remove());
        // Convert proxy images to data URLs
        const imgs = clone.querySelectorAll<HTMLImageElement>('img[src^="/api/"]');
        await Promise.all(
          Array.from(imgs).map(async (img) => {
            const dataUrl = await toDataUrl(img.src);
            if (dataUrl) img.src = dataUrl;
          }),
        );
        // Also convert relative images (like shield)
        const relImgs = clone.querySelectorAll<HTMLImageElement>('img[src^="/"]');
        await Promise.all(
          Array.from(relImgs).map(async (img) => {
            if (img.src.startsWith('data:')) return;
            const dataUrl = await toDataUrl(img.src);
            if (dataUrl) img.src = dataUrl;
          }),
        );
        slideHtmls.push(clone.outerHTML);
      }

      // ── 3. Build self-contained HTML document ──
      // Collect all computed styles from <style> tags and stylesheets
      const styleSheets = Array.from(document.styleSheets);
      let allCSS = '';
      for (const sheet of styleSheets) {
        try {
          const rules = Array.from(sheet.cssRules);
          allCSS += rules.map((r) => r.cssText).join('\n') + '\n';
        } catch {
          // Cross-origin stylesheet — skip (we embed fonts separately)
        }
      }

      const fullHTML = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>${embeddedFontCSS}</style>
<style>
${allCSS}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { margin: 0; padding: 0; background: white; }
.slide-page {
  width: ${PAGE_WIDTH}px;
  height: ${PAGE_HEIGHT}px;
  page-break-after: always;
  break-after: page;
  overflow: hidden;
  position: relative;
}
.slide-page:last-child { page-break-after: avoid; }
</style>
</head>
<body>
${slideHtmls.map((html) => `<div class="slide-page">${html}</div>`).join('\n')}
</body>
</html>`;

      // ── 4. Send to backend Playwright endpoint ──
      const filename = `Scouting_${(data?.player.name ?? 'Report').replace(/\s+/g, '_')}`;
      const response = await api.post('/report/export-pdf', {
        html: fullHTML,
        filename,
      }, {
        responseType: 'blob',
        timeout: 120_000, // 2min for PDF generation
      });

      // ── 5. Download the PDF ──
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.pdf`;
      a.click();
      URL.revokeObjectURL(url);

    } catch (err) {
      console.error('PDF export error:', err);
      // Fallback to browser print
      alert('Erro ao gerar PDF via servidor. Usando impressão do navegador como fallback.');
      window.print();
    } finally {
      setExporting(false);
    }
  }, [exporting, data]);

  function handleClubLogoUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setCustomClubLogo(ev.target?.result as string);
    reader.readAsDataURL(file);
  }

  return (
    <>
      {/* Print styles */}
      <style>{`
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
        @media print {
          .no-print { display: none !important; }
          @page { margin: 0; size: ${PAGE_WIDTH}px ${PAGE_HEIGHT}px landscape; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; margin: 0; padding: 0; }
          /* Remove SlideScaler transforms for native print */
          [data-slide] {
            width: ${PAGE_WIDTH}px !important;
            height: ${PAGE_HEIGHT}px !important;
            page-break-after: always;
            break-after: page;
            box-shadow: none !important;
            border-radius: 0 !important;
          }
          [data-slide] > * { transform: none !important; }
        }
      `}</style>

      <div style={styles.page}>
        {/* ── Toolbar ── */}
        <div className="no-print" style={styles.toolbar}>
          <div style={styles.toolbarInner}>
            {/* Player search (WyScout) */}
            <div style={styles.searchGroup}>
              <label style={styles.searchLabel}>Jogador</label>
              <div style={styles.searchWrapper}>
                <Search size={14} color={C.textMuted} style={{ flexShrink: 0 }} />
                <input
                  style={styles.searchInput}
                  placeholder="Buscar jogador..."
                  value={playerSearch}
                  onChange={(e) => {
                    setPlayerSearch(e.target.value);
                    setShowPlayerDropdown(true);
                  }}
                  onFocus={() => setShowPlayerDropdown(true)}
                  onBlur={() => setTimeout(() => setShowPlayerDropdown(false), 200)}
                />
              </div>
              {showPlayerDropdown && playersQuery.data?.players?.length ? (
                <div style={styles.dropdown}>
                  {playersQuery.data.players.map((p) => (
                    <button
                      key={p.id}
                      style={styles.dropdownItem}
                      onMouseDown={() => {
                        setSelectedPlayer(p.display_name ?? p.name);
                        setPlayerSearch(p.display_name ?? p.name);
                        setShowPlayerDropdown(false);
                      }}
                    >
                      <span style={styles.dropdownName}>{p.display_name ?? p.name}</span>
                      <span style={styles.dropdownMeta}>
                        {p.team ?? ''} · {p.position ?? ''}
                      </span>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>

            {/* Analyses player selector (independent) */}
            <div style={styles.searchGroup}>
              <label style={styles.searchLabel}>
                <Eye size={10} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
                Atleta Analisado
              </label>
              <div style={styles.searchWrapper}>
                <Search size={14} color={C.textMuted} style={{ flexShrink: 0 }} />
                <input
                  style={styles.searchInput}
                  placeholder="Buscar atleta analisado..."
                  value={analysesSearch}
                  onChange={(e) => {
                    setAnalysesSearch(e.target.value);
                    setShowAnalysesDropdown(true);
                  }}
                  onFocus={() => setShowAnalysesDropdown(true)}
                  onBlur={() => setTimeout(() => setShowAnalysesDropdown(false), 200)}
                />
              </div>
              {showAnalysesDropdown && analysesQuery.data?.players?.length ? (
                <div style={styles.dropdown}>
                  {analysesQuery.data.players.map((p, idx) => {
                    const apiName = p.wyscout_match ?? p.nome;
                    return (
                      <button
                        key={`${p.nome}-${idx}`}
                        style={styles.dropdownItem}
                        onMouseDown={() => {
                          // Set both: player API name AND analyses override
                          setSelectedPlayer(apiName);
                          setPlayerSearch(apiName);
                          setAnalysesSearch(p.nome);
                          setSelectedAnalysesPlayer(p);
                          setShowAnalysesDropdown(false);
                        }}
                      >
                        <span style={styles.dropdownName}>{p.nome}</span>
                        <span style={styles.dropdownMeta}>
                          {p.equipe ?? ''} · {p.posicao ?? ''}
                          {p.modelo ? ` · ${p.modelo}` : ''}
                        </span>
                      </button>
                    );
                  })}
                </div>
              ) : null}
            </div>

            {/* SkillCorner selector (fully independent) */}
            <div style={styles.searchGroup}>
              <label style={styles.searchLabel}>
                <Zap size={10} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
                SkillCorner
              </label>
              <div style={styles.searchWrapper}>
                <Search size={14} color={C.textMuted} style={{ flexShrink: 0 }} />
                <input
                  style={styles.searchInput}
                  placeholder="Buscar jogador SkillCorner..."
                  value={scSearch}
                  onChange={(e) => {
                    setScSearch(e.target.value);
                    setShowSCDropdown(true);
                  }}
                  onFocus={() => setShowSCDropdown(true)}
                  onBlur={() => setTimeout(() => setShowSCDropdown(false), 200)}
                />
              </div>
              {showSCDropdown && scSearchQuery.data?.length ? (
                <div style={styles.dropdown}>
                  {scSearchQuery.data.map((p, idx) => (
                    <button
                      key={`${p.player_name}-${idx}`}
                      style={styles.dropdownItem}
                      onMouseDown={() => {
                        setSelectedSC(p.player_name);
                        setScSearch(p.short_name || p.player_name);
                        setShowSCDropdown(false);
                      }}
                    >
                      <span style={styles.dropdownName}>{p.short_name || p.player_name}</span>
                      <span style={styles.dropdownMeta}>
                        {p.team_name ?? ''} · {p.position_group ?? ''}
                      </span>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>

            {/* Incumbent search (independent) */}
            <div style={styles.searchGroup}>
              <label style={styles.searchLabel}>Titular (Delta)</label>
              <div style={styles.searchWrapper}>
                <Search size={14} color={C.textMuted} style={{ flexShrink: 0 }} />
                <input
                  style={styles.searchInput}
                  placeholder="Comparar com titular..."
                  value={incumbentSearch}
                  onChange={(e) => {
                    setIncumbentSearch(e.target.value);
                    setShowIncumbentDropdown(true);
                  }}
                  onFocus={() => setShowIncumbentDropdown(true)}
                  onBlur={() => setTimeout(() => setShowIncumbentDropdown(false), 200)}
                />
              </div>
              {showIncumbentDropdown && incumbentQuery.data?.players?.length ? (
                <div style={styles.dropdown}>
                  {incumbentQuery.data.players.map((p) => (
                    <button
                      key={p.id}
                      style={styles.dropdownItem}
                      onMouseDown={() => {
                        setSelectedIncumbent(p.display_name ?? p.name);
                        setIncumbentSearch(p.display_name ?? p.name);
                        setShowIncumbentDropdown(false);
                      }}
                    >
                      <span style={styles.dropdownName}>{p.display_name ?? p.name}</span>
                      <span style={styles.dropdownMeta}>
                        {p.team ?? ''} · {p.position ?? ''}
                      </span>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>

            {/* Export PDF button */}
            <button style={styles.printBtn} onClick={handleExportPDF} title="Exportar PDF" disabled={exporting}>
              {exporting ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Download size={16} />}
              {exporting ? 'Gerando PDF...' : 'Exportar PDF'}
            </button>
          </div>
        </div>

        {/* ── Report ── */}
        <div ref={reportRef} style={styles.report}>
          {!selectedPlayer && (
            <div style={styles.emptyState}>
              <Search size={48} color={C.textMuted} />
              <p style={styles.emptyText}>
                Selecione um jogador acima para gerar o relatório prescritivo.
              </p>
              <p style={{ ...styles.emptyText, fontSize: 11, marginTop: 0 }}>
                Cada seletor funciona de forma independente. Selecione o jogador WyScout, o atleta analisado, o jogador SkillCorner e o titular para comparação separadamente.
              </p>
            </div>
          )}

          {selectedPlayer && isLoading && !isError && (
            <div style={styles.loadingState}>
              <Loader2 size={32} color={C.red} style={{ animation: 'spin 1s linear infinite' }} />
              <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
              <p style={{ ...styles.emptyText, marginTop: 16 }}>Carregando dados do relatório...</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16, width: '100%', marginTop: 24, maxWidth: PAGE_WIDTH, margin: '24px auto 0' }}>
                <Skeleton width="100%" height={180} />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <Skeleton width="100%" height={200} />
                  <Skeleton width="100%" height={200} />
                </div>
              </div>
            </div>
          )}

          {selectedPlayer && !isLoading && isError && !data && (
            <div style={styles.emptyState}>
              <div style={{ fontSize: 40 }}>&#9888;</div>
              <p style={styles.emptyText}>
                Jogador &ldquo;{selectedPlayer}&rdquo; não encontrado na base de dados.
              </p>
              <p style={{ ...styles.emptyText, fontSize: 12, marginTop: 0 }}>
                Use o seletor &ldquo;Atleta Analisado&rdquo; para buscar jogadores com análise disponível,
                ou o seletor &ldquo;Jogador&rdquo; para buscar na base Wyscout.
              </p>
            </div>
          )}

          {selectedPlayer && data && (
            <>
              {/* ═══════ SLIDE 1: COVER ═══════ */}
              <motion.div {...fadeIn(0)}>
                <ReportPage noPadding>
                  <div style={{ padding: '40px 56px 56px', flex: 1 }}>
                    {/* Club logo upload */}
                    <input ref={clubLogoInputRef} type="file" accept="image/*" onChange={handleClubLogoUpload} style={{ display: 'none' }} />
                    <ReportHeader
                      name={data.player.name}
                      badges={data.player.badges}
                      clusterDef={data.player.clusterDef}
                      photo={data.player.photo}
                      clubLogo={data.player.clubLogo}
                      customClubLogo={customClubLogo}
                      onUploadClubLogo={() => clubLogoInputRef.current?.click()}
                      position={data.player.position}
                      age={data.player.age}
                      height={data.player.height}
                      club={data.player.club}
                      league={data.player.league}
                      contract={data.player.contract}
                      links={data.analysis.links}
                    />
                  </div>
                </ReportPage>
              </motion.div>

              {/* ═══════ SLIDE 2: ANÁLISE DESCRITIVA ═══════ */}
              <motion.div {...fadeIn(0.05)}>
                <ReportPage>

                  <SectionDivider number={1} title="Análise Descritiva" />
                  <div style={{ ...styles.card, flex: 1, display: 'flex', flexDirection: 'column' as const }}>
                    <div style={styles.analysisHeader}>
                      {data.player.clubLogo && (
                        <img src={`/api/image-proxy?url=${encodeURIComponent(data.player.clubLogo)}`} alt={data.player.club} style={{ width: 36, height: 36, objectFit: 'contain' }} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                      )}
                      <div>
                        <div style={styles.analysisLabel}>ANÁLISE</div>
                        <div style={styles.analysisPlayerName}>
                          <span style={{ fontWeight: 700 }}>{data.player.name.split(' ')[0]?.toUpperCase()}</span>{' '}
                          {data.player.name.split(' ').slice(1).join(' ').toUpperCase()}
                        </div>
                      </div>
                      {data.analysis.modelo && (
                        <span style={{ ...styles.modeloBadge, background: data.analysis.modelo === 'Descartado' ? 'rgba(239,68,68,0.1)' : 'rgba(59,130,246,0.1)', color: data.analysis.modelo === 'Descartado' ? '#ef4444' : '#3b82f6', border: `1px solid ${data.analysis.modelo === 'Descartado' ? 'rgba(239,68,68,0.2)' : 'rgba(59,130,246,0.2)'}` }}>
                          {data.analysis.modelo}
                        </span>
                      )}
                    </div>
                    {Object.keys(data.analysis.scores).length > 0 && (
                      <div style={styles.scoresGrid}>
                        {Object.entries(data.analysis.scores).map(([key, value]) => {
                          const label = key === 'Nota_Desempenho' ? 'Desempenho' : key === 'Técnica' ? 'Técnica' : key;
                          const scoreColor = value >= 4 ? '#1B9E5A' : value >= 3 ? '#3B82F6' : value >= 2 ? '#D97706' : '#C8102E';
                          return (<div key={key} style={styles.scoreBox}><div style={styles.scoreLabel}>{label}</div><div style={{ ...styles.scoreValue, color: scoreColor }}>{value.toFixed(1)}</div></div>);
                        })}
                      </div>
                    )}
                    <div style={{ ...styles.analysisText, flex: 1 }} contentEditable suppressContentEditableWarning>
                      {data.analysis.text || 'Análise descritiva não disponível para este jogador. Clique aqui para inserir manualmente.'}
                    </div>
                    {(data.analysis.faixaSalarial || data.analysis.transferLuvas) && (
                      <div style={styles.financialRow}>
                        {data.analysis.faixaSalarial && (<div style={styles.financialTag}><span style={{ color: C.textTertiary }}>Salário:</span> <span style={{ fontWeight: 600 }}>{data.analysis.faixaSalarial}</span></div>)}
                        {data.analysis.transferLuvas && (<div style={styles.financialTag}><span style={{ color: C.textTertiary }}>Transfer/Luvas:</span> <span style={{ fontWeight: 600 }}>{data.analysis.transferLuvas}</span></div>)}
                      </div>
                    )}
                  </div>
                </ReportPage>
              </motion.div>

              {/* ═══════ SLIDE 3: IDENTIFICAÇÃO & VEREDITO ═══════ */}
              <motion.div {...fadeIn(0.1)}>
                <ReportPage>

                  <SectionDivider number={2} title="Identificação & Veredito Preditivo" />
                  <div style={{ ...styles.grid2, flex: 1 }}>
                    <div style={{ ...styles.card, display: 'flex', flexDirection: 'column' as const }}>
                      <h3 style={styles.cardTitle}>Dados do Jogador</h3>
                      <div style={styles.idGrid}>
                        {[['Nome', data.player.name], ['Idade', data.player.age ? `${data.player.age} anos` : '—'], ['Posição', data.player.position], ['Altura', data.player.height], ['Pé', data.player.foot], ['Clube', data.player.club], ['Liga', data.player.league], ['Contrato', data.player.contract]].map(([label, value]) => (
                          <div key={label} style={styles.idRow}><span style={styles.idLabel}>{label}</span><span style={styles.idValue}>{value}</span></div>
                        ))}
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column' as const }}>
                      <div style={{ display: 'flex', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
                        <StatBox label="Impact Score" value={data.predict.impactScore.toFixed(1)} color={C.green} subtitle="SSP / 10" />
                        <StatBox label="P(Sucesso)" value={`${data.predict.pSuccess}%`} color={C.blue} />
                        <StatBox label="Risco" value={data.predict.risk} color={data.predict.riskColor} />
                      </div>
                      <div style={styles.legendBox}>
                        <div style={styles.legendEntry}><strong>Impact Score (SSP):</strong> Índice composto de desempenho do jogador (0-10), calculado a partir de métricas ponderadas da posição.</div>
                        <div style={styles.legendEntry}><strong>P(Sucesso):</strong> Probabilidade estimada de sucesso na adaptação ao elenco, baseada em modelo preditivo com variáveis técnicas, táticas e contextuais.</div>
                      </div>
                      {predictionLoading ? <Skeleton width="100%" height={80} /> : (
                        <div style={{ ...styles.cardElevated, borderTop: `3px solid ${C.green}`, flex: 1, display: 'flex', flexDirection: 'column' as const }}>
                          <div style={styles.verdictLabel}>VEREDITO</div>
                          <p style={{ ...styles.verdictText, flex: 1 }} contentEditable suppressContentEditableWarning>{data.predict.verdict}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </ReportPage>
              </motion.div>

              {/* ═══════ SLIDE 4: FOUR CORNERS ═══════ */}
              <motion.div {...fadeIn(0.15)}>
                <ReportPage>

                  <SectionDivider number={3} title="Matriz Qualitativa — Four Corners" />
                  <div style={{ ...styles.grid2x2, flex: 1 }}>
                    {([
                      { key: 'tactical' as const, label: 'TÁTICO', color: QUADRANT.tactical },
                      { key: 'technical' as const, label: 'TÉCNICO', color: QUADRANT.technical },
                      { key: 'physical' as const, label: 'FÍSICO', color: QUADRANT.physical },
                      { key: 'mental' as const, label: 'MENTAL', color: QUADRANT.mental },
                    ] as const).map((q) => (
                      <div key={q.key} style={{ ...styles.cardElevated, borderTop: `3px solid ${q.color}` }}>
                        <div style={{ ...styles.quadrantLabel, color: q.color }}>{q.label}</div>
                        <ul style={styles.bulletList}>
                          {data.qualitative[q.key].map((item, i) => (
                            <li key={i} style={styles.bulletItem} contentEditable suppressContentEditableWarning>{item}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </ReportPage>
              </motion.div>

              {/* ═══════ SLIDE 5: RADAR ÍNDICES ═══════ */}
              <motion.div {...fadeIn(0.2)}>
                <ReportPage>

                  <SectionDivider number={4} title="Índices Compostos & Filtro de Elite" />
                  <div style={{ ...styles.grid2, flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                      {data.composites.length ? (
                        <ReportRadar data={data.composites} size={400} />
                      ) : <Skeleton width="100%" height={300} />}
                    </div>
                    <div style={styles.card}>
                      <h3 style={styles.cardTitle}>Filtro de Elite (P85+)</h3>
                      {data.eliteMetrics.length ? (
                        <>
                          <div style={styles.eliteSummary}>
                            <span style={styles.eliteCount}>{data.eliteMetrics.length}</span>
                            <span style={styles.eliteSummaryText}>métricas no nível elite</span>
                          </div>
                          <table style={styles.table}><thead><tr><th style={styles.th}>Métrica</th><th style={{ ...styles.th, textAlign: 'center' }}>Percentil</th><th style={styles.th}>Impacto</th></tr></thead>
                            <tbody>{data.eliteMetrics.map((m, i) => (<tr key={i} style={{ background: i % 2 === 0 ? C.bgCard : C.bgSubtle }}><td style={styles.td}>{m.metric}</td><td style={{ ...styles.td, textAlign: 'center' }}><span style={{ ...styles.pBadge, background: m.p >= 95 ? C.green : m.p >= 90 ? C.teal : C.amber, color: '#fff' }}>P{m.p}</span></td><td style={{ ...styles.td, color: C.textTertiary, fontSize: 11 }}>{m.impact}</td></tr>))}</tbody>
                          </table>
                        </>
                      ) : <p style={styles.placeholder}>Nenhuma métrica P85+ encontrada</p>}
                    </div>
                  </div>
                </ReportPage>
              </motion.div>

              {/* ═══════ SLIDE 6: RADAR COMPLETO DE MÉTRICAS DA POSIÇÃO + WEDGE ELITE ═══════ */}
              <motion.div {...fadeIn(0.25)}>
                <ReportPage>

                  <SectionDivider number={5} title="Radar de Métricas — Visão Completa" />
                  <div style={{ ...styles.grid2, flex: 1 }}>
                    {/* Full position metrics radar */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <h3 style={{ ...styles.cardTitle, textAlign: 'center' }}>Todas as Métricas da Posição</h3>
                      {data.allRadarMetrics.length ? (
                        <WedgeRadar data={data.allRadarMetrics} size={400} />
                      ) : <Skeleton width="100%" height={300} />}
                    </div>
                    {/* Elite wedge */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <h3 style={{ ...styles.cardTitle, textAlign: 'center' }}>Métricas Elite (P85+)</h3>
                      {data.eliteMetrics.length ? (
                        <WedgeRadar data={data.eliteMetrics} size={400} />
                      ) : <p style={styles.placeholder}>Sem métricas de elite suficientes</p>}
                    </div>
                  </div>
                </ReportPage>
              </motion.div>

              {/* ═══════ SLIDE 7: DELTA VS TITULAR ═══════ */}
              <motion.div {...fadeIn(0.3)}>
                <ReportPage>

                  <SectionDivider number={6} title="Delta vs. Titular — Squad Impact" />
                  <div style={{ ...styles.card, flex: 1, display: 'flex', flexDirection: 'column' }}>
                    {!selectedIncumbent ? (
                      <p style={styles.placeholder}>Selecione um titular na barra acima para gerar a comparação Delta</p>
                    ) : comparisonLoading ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, flex: 1 }}><Skeleton width="100%" height={100} /><Skeleton width="100%" height={400} /></div>
                    ) : data.delta.length ? (
                      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                        <DeltaChart data={data.delta} playerName={data.player.name} incumbentName={selectedIncumbent} fill />
                      </div>
                    ) : <p style={styles.placeholder}>Dados de comparação indisponíveis</p>}
                  </div>
                </ReportPage>
              </motion.div>

              {/* ═══════ SLIDE 8: SKILLCORNER ═══════ */}
              <motion.div {...fadeIn(0.35)}>
                <ReportPage>

                  <SectionDivider number={7} title="Dados Físicos — SkillCorner" />
                  {selectedSC && (
                    <div style={{ ...styles.scTag, marginBottom: 8 }}><Zap size={12} /> SkillCorner: <strong>{selectedSC}</strong></div>
                  )}
                  {skillCornerLoading ? (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}><Skeleton width="100%" height={200} /><Skeleton width="100%" height={200} /><Skeleton width="100%" height={200} /></div>
                  ) : data.physical ? (
                    <div style={styles.grid3}>
                      <div style={styles.card}><h4 style={styles.physTitle}>Velocidade</h4><PhysicalBar label="Vel. Máxima" data={data.physical.maxSpeed} unit="km/h" /><PhysicalBar label="Sprints p90" data={data.physical.sprints} unit="/90" /></div>
                      <div style={styles.card}><h4 style={styles.physTitle}>Resistência</h4><PhysicalBar label="Distância" data={data.physical.distance} unit="km" /><PhysicalBar label="High Runs" data={data.physical.hiRuns} unit="/90" /></div>
                      <div style={styles.card}><h4 style={styles.physTitle}>Explosividade</h4><PhysicalBar label="PSV-99" data={data.physical.psv99} unit="km/h" /><PhysicalBar label="Top 5 PSV-99" data={data.physical.topPsv99} unit="km/h" /><PhysicalBar label="Acelerações" data={data.physical.accelerations} unit="/90" /><PhysicalBar label="Pressões" data={data.physical.pressures} unit="/90" /></div>
                    </div>
                  ) : (
                    <div style={{ ...styles.card, borderLeft: `3px solid ${C.amber}` }}>
                      <p style={{ ...styles.placeholder, color: C.amber }}>
                        {selectedSC ? `Dados SkillCorner não encontrados para "${selectedSC}".` : 'Selecione um jogador no seletor SkillCorner para carregar dados físicos.'}
                      </p>
                      <div style={styles.grid3}>
                        {['Velocidade', 'Resistência', 'Explosividade'].map((cat) => (
                          <div key={cat} style={styles.card}><h4 style={styles.physTitle}>{cat}</h4><div contentEditable suppressContentEditableWarning style={styles.editablePlaceholder}>Inserir dados manualmente</div></div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* ── Comparativo com Internos ── */}
                  <div style={{ marginTop: 16, borderTop: `1px solid ${C.bgMuted}`, paddingTop: 12 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
                      <span style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 13, fontWeight: 600, color: C.textSecondary, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Comparativo Interno</span>
                      <div className="no-print" style={{ position: 'relative', flex: 1, maxWidth: 280 }}>
                        <div style={{ ...styles.searchWrapper, padding: '5px 10px' }}>
                          <Search size={12} color={C.textMuted} style={{ flexShrink: 0 }} />
                          <input
                            style={{ ...styles.searchInput, fontSize: 12 }}
                            placeholder="Buscar jogador interno..."
                            value={scInternalSearch}
                            onChange={(e) => { setScInternalSearch(e.target.value); setShowSCInternalDropdown(true); }}
                            onFocus={() => setShowSCInternalDropdown(true)}
                            onBlur={() => setTimeout(() => setShowSCInternalDropdown(false), 200)}
                          />
                        </div>
                        {showSCInternalDropdown && scInternalSearchQuery.data?.length ? (
                          <div style={{ ...styles.dropdown, maxHeight: 200 }}>
                            {scInternalSearchQuery.data.map((p, idx) => (
                              <button
                                key={`${p.player_name}-${idx}`}
                                style={{ ...styles.dropdownItem, padding: '7px 12px' }}
                                onMouseDown={() => {
                                  setSelectedSCInternal(p.player_name);
                                  setScInternalSearch(p.short_name || p.player_name);
                                  setShowSCInternalDropdown(false);
                                }}
                              >
                                <span style={{ ...styles.dropdownName, fontSize: 12 }}>{p.short_name || p.player_name}</span>
                                <span style={{ ...styles.dropdownMeta, fontSize: 10 }}>{p.team_name ?? ''}</span>
                              </button>
                            ))}
                          </div>
                        ) : null}
                      </div>
                      {selectedSCInternal && (
                        <div style={{ ...styles.scTag, padding: '4px 10px', fontSize: 11 }}><Zap size={10} /> <strong>{selectedSCInternal}</strong></div>
                      )}
                    </div>
                    {selectedSCInternal && scInternalQuery.isLoading ? (
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}><Skeleton width="100%" height={100} /><Skeleton width="100%" height={100} /><Skeleton width="100%" height={100} /></div>
                    ) : selectedSCInternal && scInternalQuery.data?.found && scInternalQuery.data.physical ? (
                      <InternalPhysicalData
                        internalPhysical={scInternalQuery.data}
                      />
                    ) : selectedSCInternal && !scInternalQuery.isLoading ? (
                      <p style={{ ...styles.placeholder, fontSize: 12, padding: '8px 0' }}>Dados SkillCorner não encontrados para &ldquo;{selectedSCInternal}&rdquo;.</p>
                    ) : (
                      <p style={{ ...styles.placeholder, fontSize: 11, padding: '4px 0', color: C.textMuted }}>Selecione um jogador interno para comparação física.</p>
                    )}
                  </div>
                </ReportPage>
              </motion.div>

              {/* ═══════ SLIDE 9: SIMILARES ═══════ */}
              <motion.div {...fadeIn(0.4)}>
                <ReportPage>

                  <SectionDivider number={8} title="Contingência — Jogadores Similares" />
                  <div style={{ ...styles.grid2, flex: 1 }}>
                    <div style={styles.card}>
                      <h3 style={styles.cardTitle}>Top 3 Similares</h3>
                      {similarityLoading ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}><Skeleton width="100%" height={48} /><Skeleton width="100%" height={48} /><Skeleton width="100%" height={48} /></div>
                      ) : data.similar.length ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                          {data.similar.map((s, i) => (
                            <div key={i} style={styles.similarRow}>
                              <div style={styles.similarRank}>{i + 1}</div>
                              <div style={{ flex: 1 }}><div style={styles.similarName}>{s.name}</div><div style={styles.similarClub}>{s.club}</div></div>
                              <div style={styles.similarPct}>{s.pct}%</div>
                              <div style={styles.progressTrack}><div style={{ ...styles.progressBar, width: `${s.pct}%` }} /></div>
                            </div>
                          ))}
                        </div>
                      ) : <p style={styles.placeholder}>Sem jogadores similares encontrados</p>}
                    </div>
                    <div style={styles.card}>
                      <h3 style={styles.cardTitle}>Observação Analítica</h3>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                        {['Nível Competitivo', 'Valor de Mercado', 'Estratégia'].map((field) => (
                          <div key={field}><div style={styles.obsLabel}>{field}</div><div contentEditable suppressContentEditableWarning style={styles.obsField}>Inserir observação...</div></div>
                        ))}
                      </div>
                    </div>
                  </div>
                </ReportPage>
              </motion.div>

              {/* ═══════ SLIDE 10: CONCLUSÃO ═══════ */}
              <motion.div {...fadeIn(0.45)}>
                <ReportPage>

                  <SectionDivider number={9} title="Conclusão & Recomendação" />
                  <div style={{ ...styles.grid3, flex: 1 }}>
                    <div style={{ ...styles.cardElevated, borderTop: `3px solid ${C.green}` }}>
                      <div style={{ ...styles.quadrantLabel, color: C.green }}>VEREDITO FINAL</div>
                      <div contentEditable suppressContentEditableWarning style={styles.conclusionText}>Jogador apresenta perfil compatível com as necessidades do elenco. Recomendação de avanço nas tratativas.</div>
                    </div>
                    <div style={{ ...styles.cardElevated, borderTop: `3px solid ${C.red}` }}>
                      <div style={{ ...styles.quadrantLabel, color: C.red }}>NEGOCIAÇÃO</div>
                      <ul style={styles.bulletList}>{['Definir teto salarial', 'Avaliar cláusulas contratuais', 'Consultar agente do jogador'].map((item, i) => (<li key={i} style={styles.bulletItem} contentEditable suppressContentEditableWarning>{item}</li>))}</ul>
                    </div>
                    <div style={{ ...styles.cardElevated, borderTop: `3px solid ${C.amber}` }}>
                      <div style={{ ...styles.quadrantLabel, color: C.amber }}>DESENVOLVIMENTO</div>
                      <ul style={styles.bulletList}>{['Plano de adaptação tática', 'Acompanhamento físico', 'Integração com elenco'].map((item, i) => (<li key={i} style={styles.bulletItem} contentEditable suppressContentEditableWarning>{item}</li>))}</ul>
                    </div>
                  </div>
                  <div style={styles.recBanner}>
                    <div style={styles.recTitle}>RECOMENDAÇÃO</div>
                    <div contentEditable suppressContentEditableWarning style={styles.recText}>
                      {data.predict.risk.toLowerCase().includes('baix') || data.predict.risk.toLowerCase() === 'low'
                        ? `AVANÇAR — Jogador com P(Sucesso) de ${data.predict.pSuccess}% e perfil de risco baixo. Recomendamos avanço imediato nas negociações.`
                        : data.predict.risk.toLowerCase().includes('med')
                          ? `AVALIAR COM CAUTELA — P(Sucesso) de ${data.predict.pSuccess}% com risco moderado. Recomendamos avaliação presencial antes de avançar.`
                          : `MONITORAR — P(Sucesso) de ${data.predict.pSuccess}% com risco elevado. Manter em observação e reavaliar em 60 dias.`}
                    </div>
                  </div>
                </ReportPage>
              </motion.div>
            </>
          )}
        </div>
      </div>
    </>
  );
}

// ── PhysicalBar sub-component ──
function PhysicalBar({
  label,
  data,
  unit,
}: {
  label: string;
  data: { value: number; p: number } | null;
  unit: string;
}) {
  if (!data) return null;

  const pColor =
    data.p >= 90 ? C.green : data.p >= 65 ? C.amber : data.p >= 36 ? C.textTertiary : C.red;

  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={phStyles.label}>{label}</span>
        <span style={{ ...phStyles.pValue, color: pColor }}>P{Math.round(data.p)}</span>
      </div>
      <div style={phStyles.track}>
        <div
          style={{
            ...phStyles.bar,
            width: `${Math.min(data.p, 100)}%`,
            background: pColor,
          }}
        />
      </div>
      <div style={phStyles.valueText}>
        {typeof data.value === 'number' ? data.value.toFixed(1) : '—'} {unit}
      </div>
    </div>
  );
}

const phStyles: Record<string, React.CSSProperties> = {
  label: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 14,
    color: C.textSecondary,
  },
  pValue: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 14,
    fontWeight: 700,
  },
  track: {
    height: 8,
    background: C.bgSubtle,
    borderRadius: 4,
    overflow: 'hidden',
  },
  bar: {
    height: '100%',
    borderRadius: 4,
    transition: 'width 0.6s ease',
  },
  valueText: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 12,
    color: C.textTertiary,
    marginTop: 3,
  },
};

// ── PhysicalComparison sub-component ──
function InternalPhysicalData({
  internalPhysical,
}: {
  internalPhysical: import('../types/api').SkillCornerPlayerProfile;
}) {
  const sc = internalPhysical;
  const intPhys = sc.physical ? {
    sprints: sc.physical['Sprints/90'] != null ? { value: sc.physical['Sprints/90'], p: sc.physical_percentiles?.['Sprints/90'] ?? 0 } : null,
    maxSpeed: sc.physical['Max Speed (km/h)'] != null ? { value: sc.physical['Max Speed (km/h)'], p: sc.physical_percentiles?.['Max Speed (km/h)'] ?? 0 } : null,
    accelerations: sc.physical['Accelerations/90'] != null ? { value: sc.physical['Accelerations/90'], p: sc.physical_percentiles?.['Accelerations/90'] ?? 0 } : null,
    distance: sc.physical['Distance/90'] != null ? { value: sc.physical['Distance/90'], p: sc.physical_percentiles?.['Distance/90'] ?? 0 } : null,
    hiRuns: sc.physical['High Intensity Runs/90'] != null ? { value: sc.physical['High Intensity Runs/90'], p: sc.physical_percentiles?.['High Intensity Runs/90'] ?? 0 } : null,
    pressures: sc.physical['Pressing Index/90'] != null ? { value: sc.physical['Pressing Index/90'], p: sc.physical_percentiles?.['Pressing Index/90'] ?? 0 } : null,
    psv99: sc.physical['Avg PSV-99'] != null ? { value: sc.physical['Avg PSV-99'], p: sc.physical_percentiles?.['Avg PSV-99'] ?? 0 } : null,
    topPsv99: sc.physical['Avg Top 5 PSV-99'] != null ? { value: sc.physical['Avg Top 5 PSV-99'], p: sc.physical_percentiles?.['Avg Top 5 PSV-99'] ?? 0 } : null,
  } : null;

  if (!intPhys) return null;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
      <div style={{ background: C.bgSubtle, borderRadius: 8, padding: '10px 14px' }}>
        <h5 style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 12, fontWeight: 600, color: C.textPrimary, margin: '0 0 8px' }}>Velocidade</h5>
        <PhysicalBar label="Vel. Máxima" data={intPhys.maxSpeed} unit="km/h" />
        <PhysicalBar label="Sprints p90" data={intPhys.sprints} unit="/90" />
      </div>
      <div style={{ background: C.bgSubtle, borderRadius: 8, padding: '10px 14px' }}>
        <h5 style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 12, fontWeight: 600, color: C.textPrimary, margin: '0 0 8px' }}>Resistência</h5>
        <PhysicalBar label="Distância" data={intPhys.distance} unit="km" />
        <PhysicalBar label="High Runs" data={intPhys.hiRuns} unit="/90" />
      </div>
      <div style={{ background: C.bgSubtle, borderRadius: 8, padding: '10px 14px' }}>
        <h5 style={{ fontFamily: "'DM Sans', sans-serif", fontSize: 12, fontWeight: 600, color: C.textPrimary, margin: '0 0 8px' }}>Explosividade</h5>
        <PhysicalBar label="PSV-99" data={intPhys.psv99} unit="km/h" />
        <PhysicalBar label="Top 5 PSV-99" data={intPhys.topPsv99} unit="km/h" />
        <PhysicalBar label="Acelerações" data={intPhys.accelerations} unit="/90" />
        <PhysicalBar label="Pressões" data={intPhys.pressures} unit="/90" />
      </div>
    </div>
  );
}

// ── Page Styles ──
const styles: Record<string, React.CSSProperties> = {
  page: {
    background: C.bg,
    minHeight: '100vh',
    fontFamily: "'DM Sans', sans-serif",
    display: 'flex',
    flexDirection: 'column',
    overflowX: 'hidden',
  },
  toolbar: {
    position: 'sticky',
    top: 0,
    zIndex: 20,
    background: 'rgba(247, 246, 243, 0.92)',
    backdropFilter: 'blur(12px)',
    borderBottom: `1px solid ${C.bgMuted}`,
    padding: '12px 0',
    marginBottom: 24,
  },
  toolbarInner: {
    maxWidth: 1200,
    margin: '0 auto',
    padding: '0 24px',
    display: 'flex',
    gap: 12,
    alignItems: 'flex-end',
    flexWrap: 'wrap',
  },
  searchGroup: {
    position: 'relative',
    flex: 1,
    minWidth: 160,
  },
  searchLabel: {
    display: 'block',
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 10,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    color: C.textTertiary,
    marginBottom: 4,
  },
  searchWrapper: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    background: C.bgCard,
    border: `1px solid ${C.bgMuted}`,
    borderRadius: 8,
    padding: '8px 12px',
  },
  searchInput: {
    border: 'none',
    outline: 'none',
    background: 'transparent',
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 13,
    color: C.textPrimary,
    flex: 1,
    minWidth: 0,
  },
  dropdown: {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    background: C.bgCard,
    border: `1px solid ${C.bgMuted}`,
    borderRadius: 8,
    boxShadow: '0 8px 24px rgba(0,0,0,0.1)',
    zIndex: 30,
    maxHeight: 280,
    overflowY: 'auto',
    marginTop: 4,
  },
  dropdownItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    padding: '10px 14px',
    border: 'none',
    background: 'transparent',
    cursor: 'pointer',
    textAlign: 'left',
    transition: 'background 0.15s',
    borderBottom: `1px solid ${C.bgSubtle}`,
  },
  dropdownName: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 13,
    fontWeight: 500,
    color: C.textPrimary,
  },
  dropdownMeta: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 11,
    color: C.textTertiary,
  },
  printBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    background: C.red,
    color: '#fff',
    border: 'none',
    borderRadius: 8,
    padding: '10px 20px',
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 12,
    fontWeight: 600,
    cursor: 'pointer',
    letterSpacing: '0.04em',
    whiteSpace: 'nowrap',
    flexShrink: 0,
  },
  report: {
    padding: '0 24px 60px',
    flexGrow: 1,
    overflowX: 'hidden',
    boxSizing: 'border-box',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 400,
    gap: 16,
  },
  emptyText: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 14,
    color: C.textTertiary,
    textAlign: 'center',
  },
  loadingState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 400,
  },
  grid2: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 28,
  },
  grid2x2: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 28,
  },
  grid3: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr 1fr',
    gap: 28,
  },
  card: {
    background: C.bgCard,
    border: `1px solid ${C.bgMuted}`,
    borderRadius: 12,
    padding: '24px 28px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
  },
  cardElevated: {
    background: C.bgCard,
    border: `1px solid ${C.bgMuted}`,
    borderRadius: 12,
    padding: '24px 28px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
  },
  cardTitle: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 18,
    fontWeight: 600,
    color: C.textPrimary,
    marginTop: 0,
    marginBottom: 18,
  },
  idGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: 0,
  },
  idRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '10px 0',
    borderBottom: `1px solid ${C.bgSubtle}`,
  },
  idLabel: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 14,
    color: C.textTertiary,
    fontWeight: 500,
  },
  idValue: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 15,
    color: C.textPrimary,
    fontWeight: 600,
  },
  verdictLabel: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: '0.12em',
    textTransform: 'uppercase',
    color: C.textTertiary,
    marginBottom: 10,
  },
  verdictText: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 14,
    color: C.textSecondary,
    lineHeight: 1.6,
    margin: 0,
    outline: 'none',
  },
  quadrantLabel: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 14,
    fontWeight: 700,
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    marginBottom: 14,
  },
  bulletList: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  bulletItem: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 15,
    color: C.textSecondary,
    lineHeight: 1.5,
    paddingLeft: 16,
    position: 'relative',
    outline: 'none',
  },
  eliteSummary: {
    display: 'flex',
    alignItems: 'center',
    gap: 14,
    marginBottom: 24,
    padding: '16px 22px',
    background: C.bgSubtle,
    borderRadius: 10,
  },
  eliteCount: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 32,
    fontWeight: 700,
    color: C.green,
  },
  eliteSummaryText: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 15,
    color: C.textSecondary,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: 14,
  },
  th: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 12,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    color: C.textTertiary,
    padding: '10px 14px',
    textAlign: 'left',
    borderBottom: `2px solid ${C.bgMuted}`,
  },
  td: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 14,
    color: C.textPrimary,
    padding: '10px 14px',
  },
  pBadge: {
    display: 'inline-block',
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 13,
    fontWeight: 700,
    padding: '3px 10px',
    borderRadius: 12,
  },
  placeholder: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 15,
    color: C.textTertiary,
    fontStyle: 'italic',
    textAlign: 'center',
    padding: '24px 0',
  },
  physTitle: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 18,
    fontWeight: 600,
    color: C.textPrimary,
    marginTop: 0,
    marginBottom: 18,
  },
  editablePlaceholder: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 14,
    color: C.textMuted,
    padding: '16px',
    borderRadius: 8,
    border: `1px dashed ${C.bgMuted}`,
    outline: 'none',
    minHeight: 80,
  },
  similarRow: {
    display: 'grid',
    gridTemplateColumns: '36px 1fr 56px 100px',
    alignItems: 'center',
    gap: 14,
    padding: '14px 0',
    borderBottom: `1px solid ${C.bgSubtle}`,
  },
  similarRank: {
    width: 32,
    height: 32,
    borderRadius: 8,
    background: C.bgSubtle,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 14,
    fontWeight: 700,
    color: C.textSecondary,
  },
  similarName: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 16,
    fontWeight: 600,
    color: C.textPrimary,
  },
  similarClub: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 13,
    color: C.textTertiary,
  },
  similarPct: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 15,
    fontWeight: 700,
    color: C.green,
    textAlign: 'right',
  },
  progressTrack: {
    height: 6,
    background: C.bgSubtle,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    background: C.green,
    borderRadius: 3,
    transition: 'width 0.6s ease',
  },
  obsLabel: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 12,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    color: C.textTertiary,
    marginBottom: 8,
  },
  obsField: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 14,
    color: C.textSecondary,
    padding: '14px 18px',
    borderRadius: 8,
    border: `1px solid ${C.bgMuted}`,
    outline: 'none',
    lineHeight: 1.5,
    minHeight: 60,
  },
  conclusionText: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 15,
    color: C.textSecondary,
    lineHeight: 1.6,
    outline: 'none',
  },
  recBanner: {
    marginTop: 28,
    background: `linear-gradient(135deg, ${C.red}, ${C.redDark})`,
    borderRadius: 14,
    padding: '28px 36px',
    boxShadow: '0 8px 24px rgba(200, 16, 46, 0.25)',
  },
  recTitle: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 12,
    fontWeight: 700,
    letterSpacing: '0.15em',
    textTransform: 'uppercase',
    color: 'rgba(255,255,255,0.6)',
    marginBottom: 10,
  },
  recText: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 16,
    color: '#fff',
    lineHeight: 1.6,
    fontWeight: 500,
    outline: 'none',
  },
  quoteBox: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 14,
    color: C.textSecondary,
    fontStyle: 'italic',
    padding: '18px 24px',
    borderLeft: `4px solid ${C.teal}`,
    background: C.bgSubtle,
    borderRadius: '0 10px 10px 0',
    outline: 'none',
    lineHeight: 1.5,
  },
  // Analysis section styles
  analysisHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: 14,
    marginBottom: 20,
    paddingBottom: 16,
    borderBottom: `2px solid ${C.red}`,
  },
  analysisLabel: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 12,
    fontWeight: 700,
    letterSpacing: '0.12em',
    textTransform: 'uppercase',
    color: C.red,
  },
  analysisPlayerName: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 24,
    fontWeight: 600,
    lineHeight: 1.15,
    color: C.textPrimary,
  },
  modeloBadge: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 11,
    fontWeight: 600,
    padding: '5px 14px',
    borderRadius: 14,
    letterSpacing: '0.06em',
    textTransform: 'uppercase',
    marginLeft: 'auto',
  },
  scoresGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
    gap: 16,
    marginBottom: 24,
  },
  scoreBox: {
    background: C.bgSubtle,
    borderRadius: 10,
    padding: '14px 12px',
    textAlign: 'center' as const,
    border: `1px solid ${C.bgMuted}`,
  },
  scoreLabel: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 11,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    color: C.textTertiary,
    marginBottom: 6,
  },
  scoreValue: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 28,
    fontWeight: 700,
    lineHeight: 1.1,
  },
  analysisText: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 14,
    color: C.textSecondary,
    lineHeight: 1.7,
    textAlign: 'justify' as const,
    outline: 'none',
    padding: '20px 24px',
    background: C.bgSubtle,
    borderRadius: 10,
    border: `1px solid ${C.bgMuted}`,
    marginBottom: 16,
  },
  financialRow: {
    display: 'flex',
    gap: 14,
    flexWrap: 'wrap' as const,
  },
  financialTag: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 13,
    color: C.textPrimary,
    padding: '8px 16px',
    background: C.bgSubtle,
    borderRadius: 8,
    border: `1px solid ${C.bgMuted}`,
  },
  legendBox: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    padding: '12px 16px',
    background: C.bgSubtle,
    borderRadius: 8,
    border: `1px solid ${C.bgMuted}`,
    marginBottom: 16,
  },
  legendEntry: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 12,
    color: C.textTertiary,
    lineHeight: 1.5,
  },
  scTag: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 12,
    color: C.textSecondary,
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '6px 14px',
    background: 'rgba(128, 203, 162, 0.1)',
    border: '1px solid rgba(128, 203, 162, 0.3)',
    borderRadius: 6,
  },
};
