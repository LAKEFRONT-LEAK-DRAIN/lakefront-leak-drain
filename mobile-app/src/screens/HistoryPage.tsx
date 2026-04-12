import { useState } from 'react';
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
  input: {
    width: '100%',
    padding: `${spacing.sm} ${spacing.md}`,
    borderRadius: radius.md,
    border: '1.5px solid #e2e8f0',
    fontSize: font.sizeMd,
    color: colors.ink,
    background: colors.bg,
    boxSizing: 'border-box' as const,
  },
  btn: {
    width: '100%',
    padding: `${spacing.md} ${spacing.lg}`,
    background: colors.aqua,
    color: colors.onDark,
    fontWeight: font.weightBlack,
    fontSize: font.sizeMd,
    borderRadius: radius.md,
    border: 'none',
    cursor: 'pointer',
    marginTop: spacing.sm,
  },
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
  emptyState: { textAlign: 'center' as const, padding: `${spacing.xxl} ${spacing.lg}`, color: colors.muted },
  emptyIcon: { fontSize: '48px', marginBottom: spacing.md },
};

interface Job {
  id: string;
  workStatus: string;
  invoiceNumber: string | null;
  scheduledStart: string | null;
  address: string;
  services: string[];
  totalCents: number | null;
  assignedEmployee: string | null;
}

type LookupResult =
  | { found: false }
  | { found: true; customerName: string; customerId: string; jobs: Job[] };

const PAST_STATUSES = new Set([
  'complete_rated', 'complete rated',
  'complete_unrated', 'complete unrated',
  'user_canceled', 'user canceled',
  'pro_canceled', 'pro canceled',
]);

function norm(s: string) { return s.toLowerCase().replace(/_/g, ' '); }

function formatDate(iso: string | null) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return iso; }
}

function statusBadge(ws: string): { label: string; bg: string; color: string } {
  const s = norm(ws);
  if (s.includes('complete')) return { label: '✓ Completed', bg: 'rgba(16,185,129,0.12)', color: '#065f46' };
  if (s.includes('canceled')) return { label: '✗ Canceled', bg: 'rgba(239,68,68,0.1)', color: '#991b1b' };
  return { label: ws, bg: colors.bg, color: colors.muted };
}

function formatDollars(cents: number | null): string | null {
  if (cents == null || cents === 0) return null;
  return `$${(cents / 100).toFixed(2)}`;
}

export default function HistoryPage() {
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<LookupResult | null>(null);
  const [looked, setLooked] = useState(false);

  async function handleLookup() {
    const q = phone.trim();
    if (!q) return;
    setLoading(true);
    setResult(null);
    setLooked(false);
    try {
      const res = await fetch(`/.netlify/functions/hcp-customer-jobs?phone=${encodeURIComponent(q)}`);
      const data: LookupResult = await res.json();
      setResult(data);
      setLooked(true);
    } finally {
      setLoading(false);
    }
  }

  const found = result && result.found === true
    ? result as Extract<LookupResult, { found: true }>
    : null;
  const pastJobs = found?.jobs.filter((j) => PAST_STATUSES.has(norm(j.workStatus))) ?? [];

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div style={styles.headerTitle}>Service History</div>
        <div style={styles.headerSub}>Your past and upcoming jobs</div>
      </div>

      <div style={styles.body}>
        {/* Lookup card */}
        <div style={styles.card}>
          <div style={{ fontSize: font.sizeMd, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.sm }}>
            Look Up Your History
          </div>
          <div style={{ fontSize: font.sizeSm, color: colors.muted, marginBottom: spacing.md }}>
            Enter the phone number on your account
          </div>
          <input
            style={styles.input}
            type="tel"
            placeholder="(216) 555-0100"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleLookup()}
          />
          <button style={styles.btn} onClick={handleLookup} disabled={loading}>
            {loading ? 'Looking up…' : 'View History'}
          </button>
        </div>

        {looked && result && !result.found && (
          <div style={styles.card}>
            <div style={styles.emptyState}>
              <div style={styles.emptyIcon}>🔍</div>
              <div style={{ fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.xs }}>No account found</div>
              <div style={{ fontSize: font.sizeSm }}>Try the phone number you used when booking.</div>
            </div>
          </div>
        )}

        {found && pastJobs.length === 0 && (
          <div style={styles.card}>
            <div style={styles.emptyState}>
              <div style={styles.emptyIcon}>🗂️</div>
              <div style={{ fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.xs }}>No past jobs yet</div>
              <div style={{ fontSize: font.sizeSm }}>
                Hi {found.customerName.split(' ')[0]}! Your completed services will appear here.
              </div>
            </div>
          </div>
        )}

        {found && pastJobs.length > 0 && (
          <div style={styles.card}>
            <div style={{ fontSize: font.sizeLg, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.md }}>
              Past Jobs
            </div>
            {pastJobs.map((job, i) => {
              const badge = statusBadge(job.workStatus);
              const title = job.services.length > 0 ? job.services.join(' · ') : 'Service';
              const amount = formatDollars(job.totalCents);
              return (
                <div key={job.id} style={{ ...styles.jobRow, ...(i === pastJobs.length - 1 ? { borderBottom: 'none' } : {}) }}>
                  <div style={styles.jobIcon}>🔧</div>
                  <div style={{ flex: 1 }}>
                    <div style={styles.jobTitle}>{title}</div>
                    <div style={styles.jobMeta}>
                      {[formatDate(job.scheduledStart), job.address].filter(Boolean).join(' · ')}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ ...styles.statusBadge, background: badge.bg, color: badge.color }}>{badge.label}</div>
                      {amount && <div style={{ fontWeight: font.weightBlack, color: colors.navy, fontSize: font.sizeSm }}>{amount}</div>}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <a href={hcpUrls.portal} target="_blank" rel="noopener noreferrer" style={styles.btnPortal}>
          View All Invoices in Portal →
        </a>
      </div>
    </div>
  );
}
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
