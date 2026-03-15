import { useState, useRef } from 'react';
import { Upload } from 'lucide-react';

// External logo URLs
const YOUTUBE_LOGO = 'https://upload.wikimedia.org/wikipedia/commons/e/ef/Youtube_logo.png';
const TRANSFERMARKT_LOGO = 'https://upload.wikimedia.org/wikipedia/commons/7/7b/Transfermarkt_logo.png';
const OGOL_LOGO = 'https://img-s-msn-com.akamaized.net/tenant/amp/entityid/AA1C5kUr.img?w=160&h=160';

interface ReportHeaderProps {
  name: string;
  badges: string[];
  clusterDef: string;
  photo: string | null;
  clubLogo: string | null;
  customClubLogo?: string | null;
  onClubLogoChange?: (dataUrl: string) => void;
  position: string;
  age: number;
  height: string;
  club: string;
  league: string;
  contract: string;
  links: Record<string, string>;
}

export default function ReportHeader({
  name,
  badges,
  clusterDef,
  photo,
  clubLogo,
  customClubLogo,
  onClubLogoChange,
  position,
  age,
  height,
  club,
  league,
  contract,
  links,
}: ReportHeaderProps) {
  const [fullBodyImage, setFullBodyImage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const clubLogoInputRef = useRef<HTMLInputElement>(null);

  const now = new Date();
  const monthNames = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
  ];

  const nameParts = name.split(' ');
  const firstName = nameParts[0] ?? '';
  const lastName = nameParts.slice(1).join(' ') ?? '';

  function resizeAndSet(file: File, maxSize: number, setter: (url: string) => void) {
    const reader = new FileReader();
    reader.onload = (ev) => {
      const img = new Image();
      img.onload = () => {
        const scale = Math.min(1, maxSize / Math.max(img.width, img.height));
        const w = Math.round(img.width * scale);
        const h = Math.round(img.height * scale);
        const canvas = document.createElement('canvas');
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext('2d')!;
        ctx.drawImage(img, 0, 0, w, h);
        setter(canvas.toDataURL('image/png'));
      };
      img.src = ev.target?.result as string;
    };
    reader.readAsDataURL(file);
  }

  function handleImageUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    resizeAndSet(file, 800, setFullBodyImage);
    e.target.value = '';
  }

  function handleClubLogoUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    resizeAndSet(file, 256, (url) => onClubLogoChange?.(url));
    e.target.value = '';
  }

  const videoUrl = links['Vídeo'] || links['Video'] || null;
  const tmUrl = links['TM'] || links['Transfermarkt'] || null;
  const ogolUrl = links['ogol'] || links['Ogol'] || null;

  return (
    <div style={styles.coverPage}>
      {/* Top section title */}
      <div style={styles.sectionHeader}>
        <div style={styles.sectionBadge} />
        <div>
          <div style={styles.sectionLabel}>APRESENTAÇÃO</div>
          <div style={styles.sectionName}>
            <span style={styles.nameFirst}>{firstName.toUpperCase()}</span>{' '}
            <span style={styles.nameLast}>{lastName.toUpperCase()}</span>
          </div>
        </div>
      </div>

      {/* Main cover content */}
      <div style={styles.coverBody}>
        {/* Left: Full-body player image */}
        <div style={styles.imageColumn}>
          {fullBodyImage ? (
            <img src={fullBodyImage} alt={name} style={styles.fullBodyImg} />
          ) : photo ? (
            <img
              src={`/api/image-proxy?url=${encodeURIComponent(photo)}`}
              alt={name}
              style={styles.fullBodyImg}
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
            />
          ) : (
            <div style={styles.imagePlaceholder}>
              <Upload size={32} color="#B0B0B0" />
              <span style={styles.placeholderText}>Foto do atleta</span>
            </div>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            style={{ display: 'none' }}
          />
          <button
            className="no-print"
            style={styles.uploadBtn}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={12} />
            {fullBodyImage ? 'Trocar imagem' : 'Carregar PNG'}
          </button>
        </div>

        {/* Right: Player info card */}
        <div style={styles.infoColumn}>
          {/* Name + Position block */}
          <div style={styles.nameBlock}>
            <h1 style={styles.coverName}>
              <span style={{ fontWeight: 700 }}>{firstName.toUpperCase()}</span>{' '}
              {lastName.toUpperCase()}
            </h1>
          </div>

          {/* Data rows */}
          <div style={styles.dataCard}>
            <div style={styles.dataRow}>
              <span style={styles.dataLabel}>POSIÇÃO</span>
              <span style={styles.dataValue}>{position}</span>
            </div>
            <div style={styles.dataRow}>
              <span style={styles.dataLabel}>IDADE</span>
              <span style={styles.dataValue} contentEditable suppressContentEditableWarning>
                {age > 0 ? `${age} Anos` : '—'}
              </span>
            </div>
            <div style={styles.dataRow}>
              <span style={styles.dataLabel}>ALTURA</span>
              <span style={styles.dataValue} contentEditable suppressContentEditableWarning>
                {height}
              </span>
            </div>
          </div>

          {/* Club info */}
          <div style={styles.clubSection}>
            {customClubLogo ? (
              <img src={customClubLogo} alt={club} style={styles.clubLogo} />
            ) : clubLogo ? (
              <img
                src={`/api/image-proxy?url=${encodeURIComponent(clubLogo)}`}
                alt={club}
                style={styles.clubLogo}
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
              />
            ) : onClubLogoChange ? (
              <div style={styles.clubLogoPlaceholder} onClick={() => clubLogoInputRef.current?.click()} className="no-print">
                <Upload size={16} color="#B0B0B0" />
              </div>
            ) : null}
            <div style={{ flex: 1 }}>
              <div style={styles.clubName}>{club}</div>
              <div style={styles.clubMeta}>
                {league}
                {contract !== '—' ? ` | Contrato até ${contract}` : ''}
              </div>
            </div>
            {onClubLogoChange && (
              <>
                <input
                  ref={clubLogoInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleClubLogoUpload}
                  style={{ display: 'none' }}
                />
                <button className="no-print" onClick={() => clubLogoInputRef.current?.click()} style={styles.clubUploadBtn}>
                  <Upload size={10} /> {customClubLogo ? 'Trocar' : 'Escudo'}
                </button>
              </>
            )}
          </div>

          {/* Badges */}
          {badges.length > 0 && (
            <div style={styles.badgeRow}>
              {badges.map((b, i) => (
                <span key={i} style={styles.badge}>{b}</span>
              ))}
            </div>
          )}

          {/* Cluster */}
          <div style={styles.clusterDef}>{clusterDef}</div>
        </div>
      </div>

      {/* External links with logos */}
      <div style={styles.linksRow}>
        {videoUrl && (
          <a href={videoUrl} target="_blank" rel="noopener noreferrer" style={styles.linkCard}>
            <img src={YOUTUBE_LOGO} alt="YouTube" style={styles.linkLogo} />
            <span style={styles.linkLabel}>Clicar no ícone<br />para acessar vídeo</span>
          </a>
        )}
        {tmUrl && (
          <a href={tmUrl} target="_blank" rel="noopener noreferrer" style={styles.linkCard}>
            <img src={TRANSFERMARKT_LOGO} alt="Transfermarkt" style={styles.linkLogo} />
            <span style={styles.linkLabel}>Perfil<br />Transfermarkt</span>
          </a>
        )}
        {ogolUrl && (
          <a href={ogolUrl} target="_blank" rel="noopener noreferrer" style={styles.linkCard}>
            <img src={OGOL_LOGO} alt="oGol" style={{ ...styles.linkLogo, borderRadius: '50%' }} />
            <span style={styles.linkLabel}>Perfil<br />oGol</span>
          </a>
        )}
        {!videoUrl && !tmUrl && !ogolUrl && (
          <div style={styles.noLinks}>Links externos não disponíveis para este jogador</div>
        )}
      </div>

      {/* Footer meta */}
      <div style={styles.footerMeta}>
        RELATÓRIO PRESCRITIVO — {monthNames[now.getMonth()]} {now.getFullYear()} — BFSA
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  coverPage: {
    background: '#F7F6F3',
    borderRadius: 14,
    border: '1px solid #E5E4E0',
    padding: '36px 48px 32px',
    marginBottom: 0,
    boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
  },
  sectionHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: 14,
    marginBottom: 24,
    flexShrink: 0,
  },
  sectionBadge: {
    width: 5,
    height: 48,
    borderRadius: 2,
    background: '#C8102E',
  },
  sectionLabel: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 12,
    fontWeight: 700,
    letterSpacing: '0.12em',
    textTransform: 'uppercase',
    color: '#C8102E',
    marginBottom: 2,
  },
  sectionName: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 30,
    fontWeight: 600,
    lineHeight: 1.15,
    color: '#1A1A1A',
  },
  nameFirst: {
    fontWeight: 700,
  },
  nameLast: {
    fontWeight: 400,
  },
  coverBody: {
    display: 'grid',
    gridTemplateColumns: '400px 1fr',
    gap: 48,
    flex: 1,
    minHeight: 0,
    alignItems: 'start',
    overflow: 'hidden',
  },
  imageColumn: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 10,
    maxHeight: '100%',
    overflow: 'hidden',
  },
  fullBodyImg: {
    width: 380,
    flex: '1 1 0',
    minHeight: 0,
    maxHeight: 420,
    objectFit: 'contain',
    objectPosition: 'bottom center',
    borderRadius: 8,
  },
  imagePlaceholder: {
    width: 380,
    height: 420,
    background: '#EEEDEA',
    borderRadius: 8,
    border: '2px dashed #D4D4D4',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  placeholderText: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 14,
    color: '#B0B0B0',
  },
  uploadBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '8px 16px',
    borderRadius: 6,
    border: '1px solid #E5E4E0',
    background: '#FFFFFF',
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 12,
    fontWeight: 500,
    color: '#4A4A4A',
    cursor: 'pointer',
    flexShrink: 0,
  },
  infoColumn: {
    display: 'flex',
    flexDirection: 'column',
    gap: 24,
  },
  nameBlock: {
    borderLeft: '4px solid #C8102E',
    paddingLeft: 16,
  },
  coverName: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 32,
    fontWeight: 600,
    lineHeight: 1.15,
    color: '#1A1A1A',
    margin: 0,
  },
  dataCard: {
    background: '#FFFFFF',
    border: '1px solid #E5E4E0',
    borderRadius: 10,
    overflow: 'hidden',
  },
  dataRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    padding: '12px 20px',
    borderBottom: '1px solid #EEEDEA',
  },
  dataLabel: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    color: '#8A8A8A',
  },
  dataValue: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 18,
    fontWeight: 400,
    color: '#1A1A1A',
  },
  clubSection: {
    display: 'flex',
    alignItems: 'center',
    gap: 18,
  },
  clubLogo: {
    width: 64,
    height: 64,
    objectFit: 'contain',
  },
  clubLogoPlaceholder: {
    width: 64,
    height: 64,
    borderRadius: 8,
    border: '2px dashed #D4D4D4',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    flexShrink: 0,
  },
  clubUploadBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: 4,
    padding: '5px 12px',
    borderRadius: 6,
    border: '1px solid #E5E4E0',
    background: '#FFFFFF',
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 11,
    fontWeight: 500,
    color: '#4A4A4A',
    cursor: 'pointer',
    flexShrink: 0,
  },
  clubName: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 22,
    fontWeight: 600,
    color: '#C8102E',
  },
  clubMeta: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 13,
    color: '#4A4A4A',
    marginTop: 3,
  },
  badgeRow: {
    display: 'flex',
    gap: 10,
    flexWrap: 'wrap',
  },
  badge: {
    background: 'rgba(200, 16, 46, 0.1)',
    color: '#C8102E',
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 12,
    fontWeight: 600,
    padding: '6px 16px',
    borderRadius: 20,
    letterSpacing: '0.04em',
    textTransform: 'uppercase',
    border: '1px solid rgba(200, 16, 46, 0.2)',
  },
  clusterDef: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 13,
    color: '#8A8A8A',
    fontStyle: 'italic',
  },
  linksRow: {
    display: 'flex',
    justifyContent: 'center',
    gap: 48,
    marginTop: 'auto',
    paddingTop: 24,
    borderTop: '1px solid #E5E4E0',
    flexShrink: 0,
  },
  linkCard: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 10,
    textDecoration: 'none',
    transition: 'transform 0.2s',
  },
  linkLogo: {
    width: 56,
    height: 56,
    objectFit: 'contain',
  },
  linkLabel: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 11,
    fontWeight: 500,
    color: '#4A4A4A',
    textAlign: 'center',
    lineHeight: 1.3,
  },
  noLinks: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 12,
    color: '#B0B0B0',
    fontStyle: 'italic',
    textAlign: 'center',
    padding: '12px 0',
  },
  footerMeta: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 9,
    fontWeight: 600,
    letterSpacing: '0.15em',
    textTransform: 'uppercase',
    color: '#B0B0B0',
    textAlign: 'center',
    marginTop: 20,
    flexShrink: 0,
  },
};
