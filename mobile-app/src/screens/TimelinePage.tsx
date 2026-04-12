import { useEffect, useState } from 'react';
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

interface Job {
  id: string;
  workStatus: string;
  invoiceNumber: string | null;
  scheduledStart: string | null;
  scheduledEnd: string | null;
  address: string;
  services: string[];
  totalCents: number | null;
  assignedEmployee: string | null;
}

interface OtpSession {
  phone: string;
  token: string;
  exp: number;
}

type LookupResult =
  | { found: false }
  | { found: true; customerName: string; customerId: string; jobs: Job[] };

const SESSION_KEY = 'hcpOtpSession';
const MAX_VERIFY_ATTEMPTS = 5;
const VERIFY_LOCKOUT_SEC = 15 * 60;

function loadSession(): OtpSession | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as OtpSession;
    if (!parsed.exp || Date.now() > parsed.exp) {
      localStorage.removeItem(SESSION_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function saveSession(session: OtpSession) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}

function formatMaskedPhone(input: string) {
  const digits = input.replace(/\D/g, '');
  if (digits.length < 4) return '**********';
  const last4 = digits.slice(-4);
  return `******${last4}`;
}

type StepStatus = 'done' | 'active' | 'pending';
interface TimelineStep { label: string; sub: string; status: StepStatus; }

const ACTIVE_STATUSES = new Set([
  'needs_scheduling', 'needs scheduling', 'scheduled', 'in_progress', 'in progress',
]);

function norm(s: string) { return s.toLowerCase().replace(/_/g, ' '); }

function getSteps(workStatus: string): TimelineStep[] {
  const s = norm(workStatus);
  const steps: TimelineStep[] = [
    { label: 'Booking Confirmed', sub: 'Request received', status: 'pending' },
    { label: 'Scheduled', sub: 'Time window set', status: 'pending' },
    { label: 'Technician En Route', sub: 'On the way', status: 'pending' },
    { label: 'Job Complete', sub: 'Service finished', status: 'pending' },
  ];
  if (s === 'needs scheduling') {
    steps[0].status = 'active';
  } else if (s === 'scheduled') {
    steps[0] = { ...steps[0], sub: 'Confirmed', status: 'done' };
    steps[1].status = 'active';
  } else if (s === 'in progress') {
    steps[0] = { ...steps[0], sub: 'Confirmed', status: 'done' };
    steps[1] = { ...steps[1], sub: 'Confirmed', status: 'done' };
    steps[2].status = 'active';
  } else if (s.includes('complete')) {
    steps.forEach((step) => { step.status = 'done'; });
  }
  return steps;
}

function formatDate(iso: string | null) {
  if (!iso) return 'TBD';
  try {
    return new Date(iso).toLocaleString('en-US', {
      weekday: 'short', month: 'short', day: 'numeric',
      hour: 'numeric', minute: '2-digit',
    });
  } catch { return iso; }
}

function statusBadge(ws: string): { label: string; bg: string; color: string } {
  const s = norm(ws);
  if (s.includes('needs scheduling')) return { label: '📋 Awaiting Scheduling', bg: 'rgba(245,158,11,0.12)', color: '#92400e' };
  if (s === 'scheduled')              return { label: '📅 Scheduled', bg: 'rgba(14,111,190,0.12)', color: '#1e3a5f' };
  if (s.includes('in progress'))      return { label: '⚡ In Progress', bg: 'rgba(0,173,181,0.12)', color: colors.navy };
  if (s.includes('complete'))         return { label: '✓ Complete', bg: 'rgba(16,185,129,0.12)', color: '#065f46' };
  return { label: ws, bg: colors.bg, color: colors.muted };
}

export default function TimelinePage() {
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [resendCountdown, setResendCountdown] = useState(0);
  const [sendLoading, setSendLoading] = useState(false);
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [_loading, setLoading] = useState(false);
  const [verifyFailedAttempts, setVerifyFailedAttempts] = useState(0);
  const [verifyLockCountdown, setVerifyLockCountdown] = useState(0);
  const [statusMsg, setStatusMsg] = useState('');
  const [authError, setAuthError] = useState('');
  const [session, setSession] = useState<OtpSession | null>(loadSession());
  const [result, setResult] = useState<LookupResult | null>(null);
  const [looked, setLooked] = useState(false);

  async function fetchJobs(activePhone: string, token: string) {
    const q = activePhone.trim();
    if (!q) return;
    setLoading(true);
    setAuthError('');
    setResult(null);
    setLooked(false);
    try {
      const res = await fetch(`/.netlify/functions/hcp-customer-jobs?phone=${encodeURIComponent(q)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data: LookupResult = await res.json();
      if (!res.ok) throw new Error((data as { error?: string }).error || 'Unable to load jobs.');
      setResult(data);
      setLooked(true);
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : 'Unable to load jobs.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (session) {
      setPhone(session.phone);
      void fetchJobs(session.phone, session.token);
    }
  }, []);

  useEffect(() => {
    if (resendCountdown <= 0) return;
    const timer = window.setInterval(() => {
      setResendCountdown((prev) => (prev > 1 ? prev - 1 : 0));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [resendCountdown]);

  useEffect(() => {
    if (verifyLockCountdown <= 0) return;
    const timer = window.setInterval(() => {
      setVerifyLockCountdown((prev) => (prev > 1 ? prev - 1 : 0));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [verifyLockCountdown]);

  async function handleSendCode() {
    const q = phone.trim();
    if (!q) return;
    setSendLoading(true);
    setAuthError('');
    setStatusMsg('');
    try {
      const res = await fetch('/.netlify/functions/hcp-send-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: q }),
      });
      const data = await res.json() as { error?: string };
      if (!res.ok) throw new Error(data.error || 'Unable to send code.');
      setCodeSent(true);
      const retryAfter = Number((data as { retryAfterSec?: number }).retryAfterSec || 45);
      setResendCountdown(retryAfter);
      setStatusMsg('Verification code sent by text message.');
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : 'Unable to send code.');
    } finally {
      setSendLoading(false);
    }
  }

  async function handleVerifyCode() {
    const q = phone.trim();
    if (!q || !code.trim() || verifyLockCountdown > 0) return;
    setVerifyLoading(true);
    setAuthError('');
    setStatusMsg('');
    try {
      const res = await fetch('/.netlify/functions/hcp-verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: q, code: code.trim() }),
      });
      const data = await res.json() as {
        error?: string;
        sessionToken?: string;
        expiresInSec?: number;
      };
      if (!res.ok || !data.sessionToken || !data.expiresInSec) {
        throw new Error(data.error || 'Verification failed.');
      }
      const nextSession: OtpSession = {
        phone: q,
        token: data.sessionToken,
        exp: Date.now() + (data.expiresInSec * 1000),
      };
      saveSession(nextSession);
      setSession(nextSession);
      setCode('');
      setVerifyFailedAttempts(0);
      setVerifyLockCountdown(0);
      setStatusMsg('Phone verified. Loading your status...');
      await fetchJobs(q, nextSession.token);
    } catch (err) {
      const nextAttempts = verifyFailedAttempts + 1;
      setVerifyFailedAttempts(nextAttempts);
      if (nextAttempts >= MAX_VERIFY_ATTEMPTS) {
        setVerifyLockCountdown(VERIFY_LOCKOUT_SEC);
        setAuthError(`Too many failed attempts. Try again in ${VERIFY_LOCKOUT_SEC / 60} minutes.`);
      } else {
        setAuthError(err instanceof Error ? err.message : 'Verification failed.');
      }
    } finally {
      setVerifyLoading(false);
    }
  }

  function handleSignOut() {
    clearSession();
    setSession(null);
    setCodeSent(false);
    setCode('');
    setResult(null);
    setLooked(false);
    setStatusMsg('');
    setAuthError('');
    setVerifyFailedAttempts(0);
    setVerifyLockCountdown(0);
  }

  const found = result && result.found === true
    ? result as Extract<LookupResult, { found: true }>
    : null;
  const activeJobs = found?.jobs.filter((j) => ACTIVE_STATUSES.has(norm(j.workStatus))) ?? [];

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div style={styles.headerTitle}>Your Appointment</div>
        <div style={styles.headerSub}>Live service status</div>
      </div>

      <div style={styles.body}>
        {/* OTP auth card */}
        <div style={styles.card}>
          <div style={{ fontSize: font.sizeMd, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.sm }}>
            Verify Your Phone
          </div>
          <div style={{ fontSize: font.sizeSm, color: colors.muted, marginBottom: spacing.md }}>
            Enter your phone and verify by text message to view your status
          </div>
          <input
            style={styles.input}
            type="tel"
            placeholder="(216) 555-0100"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            disabled={!!session}
          />

          {!session ? (
            <>
              <button style={styles.btn} onClick={handleSendCode} disabled={sendLoading || resendCountdown > 0}>
                {sendLoading
                  ? 'Sending code...'
                  : resendCountdown > 0
                  ? `Resend in ${resendCountdown}s`
                  : 'Send Verification Code'}
              </button>

              {codeSent && (
                <>
                  <input
                    style={{ ...styles.input, marginTop: spacing.sm }}
                    type="text"
                    placeholder="Enter 6-digit code"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleVerifyCode()}
                    disabled={verifyLockCountdown > 0}
                  />
                  <button style={styles.btn} onClick={handleVerifyCode} disabled={verifyLoading || verifyLockCountdown > 0}>
                    {verifyLoading
                      ? 'Verifying...'
                      : verifyLockCountdown > 0
                      ? `Locked (${verifyLockCountdown}s)`
                      : 'Verify & View Status'}
                  </button>
                </>
              )}
            </>
          ) : (
            <>
              <div style={{ fontSize: font.sizeSm, color: colors.success, marginTop: spacing.sm }}>
                Phone verified for {formatMaskedPhone(session.phone)}. You can now view your status.
              </div>
              <button
                style={{ ...styles.btn, background: colors.navy }}
                onClick={handleSignOut}
              >
                Verify Different Phone
              </button>
            </>
          )}

          {statusMsg ? <div style={{ fontSize: font.sizeSm, color: colors.success, marginTop: spacing.sm }}>{statusMsg}</div> : null}
          {authError ? <div style={{ fontSize: font.sizeSm, color: colors.error, marginTop: spacing.sm }}>{authError}</div> : null}
        </div>

        {session && looked && result && !result.found && (
          <div style={styles.card}>
            <div style={styles.emptyState}>
              <div style={styles.emptyIcon}>🔍</div>
              <div style={{ fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.xs }}>No account found</div>
              <div style={{ fontSize: font.sizeSm }}>Try the phone number you used when booking.</div>
            </div>
          </div>
        )}

        {session && found && activeJobs.length === 0 && (
          <div style={styles.card}>
            <div style={styles.emptyState}>
              <div style={styles.emptyIcon}>📅</div>
              <div style={{ fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.xs }}>No active appointments</div>
              <div style={{ fontSize: font.sizeSm }}>
                Hi {found.customerName.split(' ')[0]}! Book a service to track your technician in real time.
              </div>
            </div>
          </div>
        )}

        {session && activeJobs.map((job) => {
          const steps = getSteps(job.workStatus);
          const badge = statusBadge(job.workStatus);
          const title = job.services.length > 0 ? job.services.join(' + ') : 'Service Request';
          return (
            <div key={job.id}>
              <div style={styles.card}>
                <div style={{ fontSize: font.sizeLg, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.xs }}>
                  🔧 {title}
                </div>
                {job.address && (
                  <div style={{ fontSize: font.sizeSm, color: colors.muted }}>{job.address}</div>
                )}
                {job.scheduledStart && (
                  <div style={{ fontSize: font.sizeSm, color: colors.muted, marginTop: spacing.xs }}>
                    {formatDate(job.scheduledStart)}
                  </div>
                )}
                <div style={{
                  marginTop: spacing.md,
                  display: 'inline-block',
                  background: badge.bg,
                  color: badge.color,
                  fontWeight: font.weightBlack,
                  fontSize: font.sizeSm,
                  padding: `${spacing.xs} ${spacing.md}`,
                  borderRadius: radius.pill,
                }}>{badge.label}</div>
              </div>

              <div style={styles.card}>
                <div style={{ fontSize: font.sizeLg, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.lg }}>Progress</div>
                <div style={styles.timelineWrap}>
                  <div style={styles.timelineBar} />
                  {steps.map((step) => (
                    <div key={step.label} style={styles.step}>
                      <div style={{
                        ...styles.dot,
                        ...(step.status === 'done' ? styles.dotDone : step.status === 'active' ? styles.dotActive : styles.dotPending),
                      }}>
                        {step.status === 'done' ? '✓' : step.status === 'active' ? '●' : '○'}
                      </div>
                      <div style={styles.stepTitle}>{step.label}</div>
                      <div style={styles.stepSub}>{step.sub}</div>
                    </div>
                  ))}
                </div>
              </div>

              {job.assignedEmployee && (
                <div style={styles.card}>
                  <div style={{ fontSize: font.sizeMd, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.sm }}>Your Technician</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: spacing.md }}>
                    <div style={{ width: 52, height: 52, borderRadius: '50%', background: colors.navy, color: colors.onDark, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '22px', flexShrink: 0 }}>👷</div>
                    <div>
                      <div style={{ fontWeight: font.weightBlack, color: colors.ink }}>{job.assignedEmployee}</div>
                      <div style={{ fontSize: font.sizeSm, color: colors.muted }}>Licensed & Insured</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
