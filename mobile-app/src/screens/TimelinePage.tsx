import { colors, font, radius, shadow, spacing } from '../tokens';

const styles: Record<string, React.CSSProperties> = {
  page: { minHeight: '100%', background: colors.bg, display: 'flex', flexDirection: 'column' },
  header: {
    background: colors.navy,
    color: colors.onDark,
    padding: `${spacing.lg} ${spacing.lg} ${spacing.md}`,
  },
  headerTitle: { fontSize: font.sizeXl, fontWeight: font.weightBlack },
  headerSub: { fontSize: font.sizeSm, opacity: 0.75, marginTop: spacing.xs },
  body: { padding: spacing.lg, display: 'flex', flexDirection: 'column', gap: spacing.md },
  card: { background: colors.card, borderRadius: radius.lg, padding: spacing.lg, boxShadow: shadow.card },
  timelineWrap: { position: 'relative', paddingLeft: '32px' },
  timelineBar: {
    position: 'absolute',
    left: '11px',
    top: '8px',
    bottom: '8px',
    width: '2px',
    background: `linear-gradient(to bottom, ${colors.aqua}, rgba(0,173,181,0.15))`,
  },
  step: { position: 'relative', marginBottom: spacing.lg },
  dot: {
    position: 'absolute',
    left: '-28px',
    top: '2px',
    width: '20px',
    height: '20px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '10px',
    fontWeight: font.weightBlack,
    flexShrink: 0,
  },
  dotDone: { background: colors.aqua, color: colors.onAqua },
  dotActive: { background: colors.navy, color: colors.onDark, boxShadow: `0 0 0 3px ${colors.aqua}` },
  dotPending: { background: '#e2e8f0', color: colors.muted },
  stepTitle: { fontSize: font.sizeMd, fontWeight: font.weightBlack, color: colors.navy },
  stepSub: { fontSize: font.sizeSm, color: colors.muted, marginTop: '2px' },
  emptyState: { textAlign: 'center' as const, padding: `${spacing.xxl} ${spacing.lg}`, color: colors.muted },
  emptyIcon: { fontSize: '48px', marginBottom: spacing.md },
};

interface TimelineStep {
  label: string;
  sub: string;
  status: 'done' | 'active' | 'pending';
}

const demoSteps: TimelineStep[] = [
  { label: 'Booking Confirmed', sub: 'Today at 9:14 AM', status: 'done' },
  { label: 'Technician Assigned', sub: 'Mike R. — Licensed Plumber', status: 'done' },
  { label: 'En Route', sub: 'ETA: ~15 minutes', status: 'active' },
  { label: 'Arrived', sub: 'Pending', status: 'pending' },
  { label: 'Job Complete', sub: 'Pending', status: 'pending' },
];

export default function TimelinePage() {
  const hasJob = true; // swap to false to see empty state

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div style={styles.headerTitle}>Your Appointment</div>
        <div style={styles.headerSub}>Live service status</div>
      </div>

      <div style={styles.body}>
        {hasJob ? (
          <>
            <div style={styles.card}>
              <div style={{ fontSize: font.sizeLg, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.xs }}>
                🔧 Drain Cleaning
              </div>
              <div style={{ fontSize: font.sizeSm, color: colors.muted }}>123 Lakewood Ave, Cleveland OH</div>
              <div style={{ fontSize: font.sizeSm, color: colors.muted, marginTop: spacing.xs }}>Today · Morning window</div>
              <div style={{
                marginTop: spacing.md,
                display: 'inline-block',
                background: 'rgba(0,173,181,0.12)',
                border: `1px solid rgba(0,173,181,0.25)`,
                color: colors.navy,
                fontWeight: font.weightBlack,
                fontSize: font.sizeSm,
                padding: `${spacing.xs} ${spacing.md}`,
                borderRadius: radius.pill,
              }}>⚡ Technician en route</div>
            </div>

            <div style={styles.card}>
              <div style={{ fontSize: font.sizeLg, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.lg }}>Progress</div>
              <div style={styles.timelineWrap}>
                <div style={styles.timelineBar} />
                {demoSteps.map((step) => (
                  <div key={step.label} style={styles.step}>
                    <div style={{ ...styles.dot, ...(step.status === 'done' ? styles.dotDone : step.status === 'active' ? styles.dotActive : styles.dotPending) }}>
                      {step.status === 'done' ? '✓' : step.status === 'active' ? '●' : '○'}
                    </div>
                    <div style={styles.stepTitle}>{step.label}</div>
                    <div style={styles.stepSub}>{step.sub}</div>
                  </div>
                ))}
              </div>
            </div>

            <div style={styles.card}>
              <div style={{ fontSize: font.sizeMd, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.sm }}>Your Technician</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: spacing.md }}>
                <div style={{ width: 52, height: 52, borderRadius: '50%', background: colors.navy, color: colors.onDark, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '22px', flexShrink: 0 }}>👷</div>
                <div>
                  <div style={{ fontWeight: font.weightBlack, color: colors.ink }}>Mike R.</div>
                  <div style={{ fontSize: font.sizeSm, color: colors.muted }}>Licensed & Insured · ⭐ 4.9</div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div style={styles.card}>
            <div style={styles.emptyState}>
              <div style={styles.emptyIcon}>📅</div>
              <div style={{ fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.xs }}>No active appointment</div>
              <div style={{ fontSize: font.sizeSm }}>Book a service to track your technician in real time.</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
