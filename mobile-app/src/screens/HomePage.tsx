import { colors, hcpUrls, font, radius, shadow, spacing } from '../tokens';

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100%',
    display: 'flex',
    flexDirection: 'column',
    background: colors.heroBg,
  },
  hero: {
    background: `radial-gradient(1200px 420px at 20% 0%, rgba(0,173,181,.25), transparent 55%), ${colors.navy}`,
    color: colors.onDark,
    padding: `${spacing.xxl} ${spacing.lg} ${spacing.xl}`,
    textAlign: 'center' as const,
  },
  logoWrap: {
    marginBottom: spacing.lg,
  },
  logoText: {
    fontSize: font.size2xl,
    fontWeight: font.weightBlack,
    letterSpacing: '-0.5px',
    lineHeight: '1.1',
  },
  tagline: {
    fontSize: font.sizeMd,
    opacity: 0.82,
    marginTop: spacing.sm,
  },
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: spacing.xs,
    background: colors.badgeBg,
    border: `1px solid ${colors.badgeBorder}`,
    color: colors.badgeText,
    padding: `${spacing.xs} ${spacing.md}`,
    borderRadius: radius.pill,
    fontSize: font.sizeSm,
    fontWeight: font.weightBlack,
    marginBottom: spacing.md,
  },
  body: {
    padding: spacing.lg,
    display: 'flex',
    flexDirection: 'column' as const,
    gap: spacing.md,
    flex: 1,
  },
  card: {
    background: colors.card,
    borderRadius: radius.lg,
    padding: spacing.lg,
    boxShadow: shadow.card,
  },
  cardTitle: {
    fontSize: font.sizeLg,
    fontWeight: font.weightBlack,
    color: colors.navy,
    marginBottom: spacing.xs,
  },
  cardSub: {
    fontSize: font.sizeSm,
    color: colors.muted,
    marginBottom: spacing.md,
  },
  btnBook: {
    display: 'block',
    width: '100%',
    padding: `${spacing.md} ${spacing.lg}`,
    background: colors.aqua,
    color: colors.onAqua,
    fontWeight: font.weightBlack,
    fontSize: font.sizeMd,
    borderRadius: radius.md,
    textAlign: 'center' as const,
    marginBottom: spacing.sm,
    boxShadow: shadow.card,
  },
  btnPortal: {
    display: 'block',
    width: '100%',
    padding: `${spacing.md} ${spacing.lg}`,
    background: colors.portalBlue,
    color: colors.onDark,
    fontWeight: font.weightBlack,
    fontSize: font.sizeMd,
    borderRadius: radius.md,
    textAlign: 'center' as const,
    marginBottom: spacing.sm,
  },
  btnCall: {
    display: 'block',
    width: '100%',
    padding: `${spacing.md} ${spacing.lg}`,
    background: colors.card,
    color: colors.navy,
    fontWeight: font.weightBlack,
    fontSize: font.sizeMd,
    borderRadius: radius.md,
    textAlign: 'center' as const,
    border: `2px solid ${colors.navy}`,
  },
  triageGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: spacing.sm,
  },
  triageBtn: {
    padding: spacing.md,
    borderRadius: radius.md,
    background: colors.bg,
    border: `1.5px solid rgba(7,27,50,0.10)`,
    color: colors.navy,
    fontWeight: font.weightBold,
    fontSize: font.sizeSm,
    cursor: 'pointer',
    textAlign: 'center' as const,
  },
};

export default function HomePage() {
  return (
    <div style={styles.page}>
      <div style={styles.hero}>
        <div style={styles.logoWrap}>
          <div style={styles.badge}>⚡ Fast Local Response</div>
          <div style={styles.logoText}>Lakefront<br />Leak &amp; Drain</div>
          <div style={styles.tagline}>Cleveland's trusted plumbing pros</div>
        </div>
      </div>

      <div style={styles.body}>
        {/* Emergency triage */}
        <div style={styles.card}>
          <div style={styles.cardTitle}>What's happening?</div>
          <div style={styles.cardSub}>Tap to get the right help fast.</div>
          <div style={styles.triageGrid}>
            {['🚨 Active leak', '🚿 Clogged drain', '💧 No hot water', '🔧 General repair', '🪠 Sewer issue', '📋 Get estimate'].map(label => (
              <a key={label} href={hcpUrls.book} target="_blank" rel="noopener noreferrer" style={styles.triageBtn}>{label}</a>
            ))}
          </div>
        </div>

        {/* Primary CTAs */}
        <div style={styles.card}>
          <div style={styles.cardTitle}>Book service</div>
          <a href={hcpUrls.book} target="_blank" rel="noopener noreferrer" style={styles.btnBook}>📅 Book Online Now</a>
          <a href={hcpUrls.portal} target="_blank" rel="noopener noreferrer" style={styles.btnPortal}>👤 Customer Portal</a>
          <a href={hcpUrls.phone} style={styles.btnCall}>📞 {hcpUrls.phoneDisplay}</a>
        </div>

        {/* Trust signals */}
        <div style={styles.card}>
          <div style={styles.cardTitle}>Why Lakefront?</div>
          {['✅ Licensed & insured in Ohio', '⚡ Same-day service available', '🏠 Serving 100+ Cleveland communities', '⭐ 5-star rated on Google'].map(item => (
            <div key={item} style={{ padding: `${spacing.xs} 0`, fontSize: font.sizeSm, color: colors.muted, borderBottom: `1px solid ${colors.bg}` }}>{item}</div>
          ))}
        </div>
      </div>
    </div>
  );
}
