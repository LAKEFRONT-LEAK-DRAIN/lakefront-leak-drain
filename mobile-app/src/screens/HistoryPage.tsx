import { colors, font, radius, shadow, spacing, hcpUrls } from '../tokens';

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
  jobRow: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: spacing.md,
    padding: `${spacing.md} 0`,
    borderBottom: `1px solid ${colors.bg}`,
  },
  jobIcon: {
    width: 44,
    height: 44,
    borderRadius: radius.sm,
    background: colors.bg,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '20px',
    flexShrink: 0,
  },
  jobTitle: { fontWeight: font.weightBlack, color: colors.ink, fontSize: font.sizeMd },
  jobMeta: { fontSize: font.sizeSm, color: colors.muted, marginTop: '2px' },
  statusBadge: {
    display: 'inline-block',
    padding: `2px ${spacing.sm}`,
    borderRadius: radius.pill,
    fontSize: font.sizeXs,
    fontWeight: font.weightBlack,
    marginTop: spacing.xs,
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
  },
};

interface HistoryJob {
  id: string;
  icon: string;
  title: string;
  date: string;
  address: string;
  status: 'completed' | 'invoiced' | 'scheduled';
  amount: string;
}

const demoJobs: HistoryJob[] = [
  { id: '1', icon: '🚿', title: 'Drain Cleaning', date: 'Mar 28, 2026', address: '123 Lakewood Ave', status: 'completed', amount: '$175' },
  { id: '2', icon: '💧', title: 'Leak Repair – Kitchen', date: 'Feb 14, 2026', address: '123 Lakewood Ave', status: 'invoiced', amount: '$340' },
  { id: '3', icon: '🔧', title: 'Sump Pump Inspection', date: 'Jan 5, 2026', address: '123 Lakewood Ave', status: 'completed', amount: '$95' },
];

const statusColors: Record<HistoryJob['status'], { bg: string; color: string; label: string }> = {
  completed: { bg: 'rgba(16,185,129,0.12)', color: '#065f46', label: '✓ Completed' },
  invoiced: { bg: 'rgba(245,158,11,0.12)', color: '#92400e', label: '📄 Invoice Sent' },
  scheduled: { bg: 'rgba(14,111,190,0.12)', color: '#1e3a5f', label: '📅 Scheduled' },
};

export default function HistoryPage() {
  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div style={styles.headerTitle}>Service History</div>
        <div style={styles.headerSub}>Your past and upcoming jobs</div>
      </div>

      <div style={styles.body}>
        <div style={styles.card}>
          <div style={{ fontSize: font.sizeLg, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.md }}>Past Jobs</div>
          {demoJobs.map((job, i) => {
            const s = statusColors[job.status];
            return (
              <div key={job.id} style={{ ...styles.jobRow, ...(i === demoJobs.length - 1 ? { borderBottom: 'none' } : {}) }}>
                <div style={styles.jobIcon}>{job.icon}</div>
                <div style={{ flex: 1 }}>
                  <div style={styles.jobTitle}>{job.title}</div>
                  <div style={styles.jobMeta}>{job.date} · {job.address}</div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ ...styles.statusBadge, background: s.bg, color: s.color }}>{s.label}</div>
                    <div style={{ fontWeight: font.weightBlack, color: colors.navy, fontSize: font.sizeSm }}>{job.amount}</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Recommendations */}
        <div style={styles.card}>
          <div style={{ fontSize: font.sizeLg, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.xs }}>Recommended Next</div>
          <div style={{ fontSize: font.sizeSm, color: colors.muted, marginBottom: spacing.md }}>Based on your service history</div>
          {['🧹 Annual drain maintenance due', '🔍 Sump pump seasonal check – Spring'].map(item => (
            <div key={item} style={{ padding: `${spacing.sm} 0`, fontSize: font.sizeSm, color: colors.ink, borderBottom: `1px solid ${colors.bg}` }}>{item}</div>
          ))}
        </div>

        <a href={hcpUrls.portal} target="_blank" rel="noopener noreferrer" style={styles.btnPortal}>
          View All Invoices in Portal →
        </a>
      </div>
    </div>
  );
}
