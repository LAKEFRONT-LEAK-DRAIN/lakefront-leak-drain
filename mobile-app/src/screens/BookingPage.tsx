import { colors, hcpUrls, font, radius, shadow, spacing } from '../tokens';

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
  label: { fontSize: font.sizeSm, fontWeight: font.weightBold, color: colors.navy, marginBottom: spacing.xs, display: 'block' },
  input: {
    width: '100%',
    padding: `${spacing.sm} ${spacing.md}`,
    borderRadius: radius.sm,
    border: `1.5px solid rgba(7,27,50,0.15)`,
    fontSize: font.sizeMd,
    color: colors.ink,
    background: colors.bg,
    outline: 'none',
    marginBottom: spacing.md,
  },
  select: {
    width: '100%',
    padding: `${spacing.sm} ${spacing.md}`,
    borderRadius: radius.sm,
    border: `1.5px solid rgba(7,27,50,0.15)`,
    fontSize: font.sizeMd,
    color: colors.ink,
    background: colors.bg,
    marginBottom: spacing.md,
  },
  btnPrimary: {
    display: 'block',
    width: '100%',
    padding: `${spacing.md} ${spacing.lg}`,
    background: colors.aqua,
    color: colors.onAqua,
    fontWeight: font.weightBlack,
    fontSize: font.sizeMd,
    borderRadius: radius.md,
    textAlign: 'center' as const,
    border: 'none',
    cursor: 'pointer',
  },
  notice: {
    background: colors.warningBg,
    borderTop: `3px solid ${colors.warning}`,
    borderBottom: `3px solid ${colors.warning}`,
    padding: spacing.md,
    borderRadius: radius.sm,
    fontSize: font.sizeSm,
    color: colors.ink,
  },
};

const services = [
  'Leak Repair', 'Drain Cleaning', 'Clogged Drain', 'Sump Pump', 'Water Heater',
  'Frozen Pipe', 'Garbage Disposal', 'Toilet Repair', 'Faucet Repair', 'Emergency Service', 'Other',
];

export default function BookingPage() {
  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div style={styles.headerTitle}>Book Service</div>
        <div style={styles.headerSub}>Schedule online in under 2 minutes</div>
      </div>

      <div style={styles.body}>
        <div style={styles.notice}>
          ⚡ <strong>Same-day service available.</strong> Call <a href={hcpUrls.phone} style={{ color: colors.navy, fontWeight: 700 }}>{hcpUrls.phoneDisplay}</a> for emergencies.
        </div>

        <div style={styles.card}>
          <div style={{ fontSize: font.sizeLg, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.md }}>Your Information</div>

          <label style={styles.label}>First Name</label>
          <input style={styles.input} type="text" placeholder="First name" autoComplete="given-name" />

          <label style={styles.label}>Last Name</label>
          <input style={styles.input} type="text" placeholder="Last name" autoComplete="family-name" />

          <label style={styles.label}>Phone</label>
          <input style={styles.input} type="tel" placeholder="(216) 555-0100" autoComplete="tel" />

          <label style={styles.label}>Email</label>
          <input style={styles.input} type="email" placeholder="you@example.com" autoComplete="email" />
        </div>

        <div style={styles.card}>
          <div style={{ fontSize: font.sizeLg, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.md }}>Service Details</div>

          <label style={styles.label}>Service Needed</label>
          <select style={styles.select}>
            <option value="">Select a service…</option>
            {services.map(s => <option key={s} value={s}>{s}</option>)}
          </select>

          <label style={styles.label}>Service Address</label>
          <input style={styles.input} type="text" placeholder="Street address" autoComplete="street-address" />
          <input style={styles.input} type="text" placeholder="City" autoComplete="address-level2" />

          <label style={styles.label}>Best Time</label>
          <select style={styles.select}>
            <option value="">Any available</option>
            <option value="morning">Morning (8am–12pm)</option>
            <option value="afternoon">Afternoon (12pm–5pm)</option>
            <option value="evening">Evening (5pm–8pm)</option>
            <option value="asap">As soon as possible</option>
          </select>

          <label style={styles.label}>Notes (optional)</label>
          <textarea style={{ ...styles.input, minHeight: '80px', resize: 'vertical' }} placeholder="Describe the issue…" />
        </div>

        <a href={hcpUrls.book} target="_blank" rel="noopener noreferrer" style={styles.btnPrimary}>
          Continue to Booking →
        </a>
      </div>
    </div>
  );
}
