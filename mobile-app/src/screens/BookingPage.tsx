import type { CSSProperties } from 'react';
import { useMemo, useState } from 'react';
import { colors, hcpUrls, font, radius, shadow, spacing } from '../tokens';

const styles: Record<string, CSSProperties> = {
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
  serviceChipGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  serviceChip: {
    padding: `${spacing.sm} ${spacing.sm}`,
    borderRadius: radius.sm,
    border: `1.5px solid rgba(7,27,50,0.2)`,
    background: colors.bg,
    color: colors.navy,
    fontSize: font.sizeSm,
    fontWeight: font.weightBold,
    cursor: 'pointer',
    textAlign: 'center' as const,
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
  lookupRow: { display: 'grid', gap: spacing.sm, gridTemplateColumns: '1fr 1fr', marginBottom: spacing.sm },
  helper: { fontSize: font.sizeSm, color: colors.muted, marginBottom: spacing.sm },
  btnSecondary: {
    display: 'block',
    width: '100%',
    padding: `${spacing.sm} ${spacing.md}`,
    background: colors.navy,
    color: colors.onDark,
    fontWeight: font.weightBold,
    fontSize: font.sizeMd,
    borderRadius: radius.md,
    textAlign: 'center' as const,
    border: 'none',
    cursor: 'pointer',
    marginBottom: spacing.md,
  },
  statusOk: { fontSize: font.sizeSm, color: colors.success, marginBottom: spacing.sm },
  statusErr: { fontSize: font.sizeSm, color: colors.error, marginBottom: spacing.sm },
  slotGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: spacing.sm, marginBottom: spacing.md },
  slotBtn: {
    padding: `${spacing.sm} ${spacing.sm}`,
    borderRadius: radius.sm,
    border: `1px solid rgba(7,27,50,0.2)`,
    background: colors.bg,
    color: colors.navy,
    fontSize: font.sizeSm,
    cursor: 'pointer',
  },
};

type LookupPayload = {
  customerId?: string;
  addressId?: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
};

type BookingWindow = {
  start_time: string;
  end_time: string;
  available: boolean;
};

export default function BookingPage() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [services, setServices] = useState<string[]>([]);
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');
  const [bestTime, setBestTime] = useState('');
  const [notes, setNotes] = useState('');
  const [customerId, setCustomerId] = useState('');
  const [addressId, setAddressId] = useState('');
  const [lookupPhone, setLookupPhone] = useState('');
  const [lookupEmail, setLookupEmail] = useState('');
  const [lookupMessage, setLookupMessage] = useState('');
  const [lookupError, setLookupError] = useState('');
  const [lookupLoading, setLookupLoading] = useState(false);
  const [windowLoading, setWindowLoading] = useState(false);
  const [windowError, setWindowError] = useState('');
  const [windows, setWindows] = useState<BookingWindow[]>([]);
  const [selectedWindow, setSelectedWindow] = useState<BookingWindow | null>(null);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState('');
  const [bookingSuccess, setBookingSuccess] = useState<{ jobId: string; invoiceNumber?: string } | null>(null);

  const bookingHref = useMemo(() => {
    const url = new URL(hcpUrls.book);
    if (firstName) url.searchParams.set('first_name', firstName);
    if (lastName) url.searchParams.set('last_name', lastName);
    if (phone) url.searchParams.set('phone', phone);
    if (email) url.searchParams.set('email', email);
    if (address) url.searchParams.set('address', address);
    if (city) url.searchParams.set('city', city);
    if (services.length) url.searchParams.set('service', services.join(', '));
    if (bestTime) url.searchParams.set('best_time', bestTime);
    if (notes) url.searchParams.set('notes', notes);
    return url.toString();
  }, [address, bestTime, city, email, firstName, lastName, notes, phone, services]);

  async function handleLookup() {
    setLookupError('');
    setLookupMessage('');

    const cleanPhone = lookupPhone.trim();
    const cleanEmail = lookupEmail.trim();
    if (!cleanPhone && !cleanEmail) {
      setLookupError('Enter phone or email to find your customer record.');
      return;
    }

    try {
      setLookupLoading(true);
      const qs = new URLSearchParams();
      if (cleanPhone) qs.set('phone', cleanPhone);
      if (cleanEmail) qs.set('email', cleanEmail);

      const res = await fetch(`/.netlify/functions/hcp-customer-lookup?${qs.toString()}`);
      const data = (await res.json()) as LookupPayload & { message?: string; error?: string };

      if (!res.ok) {
        throw new Error(data.error ?? `Lookup failed (${res.status})`);
      }

      setCustomerId(data.customerId ?? '');
      setAddressId(data.addressId ?? '');
      setFirstName(data.firstName ?? '');
      setLastName(data.lastName ?? '');
      setPhone(data.phone ?? cleanPhone);
      setEmail(data.email ?? cleanEmail);
      setAddress(data.address ?? '');
      setCity(data.city ?? '');
      setLookupMessage(data.message ?? 'Customer found. Fields are pre-filled below.');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Could not find that customer.';
      setLookupError(msg);
    } finally {
      setLookupLoading(false);
    }
  }

  function formatWindowLabel(start: string, end: string): string {
    const startDate = new Date(start);
    const endDate = new Date(end);
    return `${startDate.toLocaleDateString([], { month: 'short', day: 'numeric' })} ${startDate.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })} - ${endDate.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`;
  }

  async function handleLoadWindows() {
    setWindowError('');
    setWindowLoading(true);
    try {
      const qs = new URLSearchParams({ show_for_days: '5' });
      const res = await fetch(`/.netlify/functions/hcp-booking-windows?${qs.toString()}`);
      const data = (await res.json()) as {
        availableWindows?: BookingWindow[];
        error?: string;
      };

      if (!res.ok) {
        throw new Error(data.error ?? `Failed to load windows (${res.status})`);
      }

      const available = (data.availableWindows ?? []).slice(0, 8);
      setWindows(available);
      if (available.length === 0) {
        setWindowError('No online windows found for the next few days.');
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Could not load available times.';
      setWindowError(msg);
      setWindows([]);
    } finally {
      setWindowLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div style={styles.headerTitle}>Book Service</div>
        <div style={styles.headerSub}>Schedule online in under 2 minutes</div>
      </div>

      {bookingSuccess ? (
        <div style={{ ...styles.body, alignItems: 'center', justifyContent: 'center', flex: 1 }}>
          <div style={{ ...styles.card, textAlign: 'center', maxWidth: 360, width: '100%' }}>
            <div style={{ fontSize: '3rem', marginBottom: spacing.md }}>✅</div>
            <div style={{ fontSize: font.sizeLg, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.sm }}>
              Booking Submitted!
            </div>
            <div style={{ fontSize: font.sizeSm, color: colors.muted, marginBottom: spacing.lg }}>
              {bookingSuccess.invoiceNumber ? `Job #${bookingSuccess.invoiceNumber} created.` : 'Request received.'} We'll call to confirm your appointment.
            </div>
            <button
              type="button"
              style={styles.btnPrimary}
              onClick={() => {
                setBookingSuccess(null);
                setFirstName(''); setLastName(''); setPhone(''); setEmail('');
                setAddress(''); setCity(''); setNotes(''); setServices([]);
                setSelectedWindow(null); setCustomerId(''); setAddressId('');
              }}
            >
              Book Another Service
            </button>
          </div>
        </div>
      ) : (
        <>
        <div style={styles.notice}>
          ⚡ <strong>Same-day service available.</strong> Call <a href={hcpUrls.phone} style={{ color: colors.navy, fontWeight: 700 }}>{hcpUrls.phoneDisplay}</a> for emergencies.
        </div>

        <div style={styles.card}>
          <div style={{ fontSize: font.sizeLg, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.md }}>Your Information</div>

          <div style={styles.helper}>Returning customer? Enter phone or email and we will pre-fill your details.</div>

          <div style={styles.lookupRow}>
            <input
              style={{ ...styles.input, marginBottom: 0 }}
              type="tel"
              placeholder="Lookup phone"
              autoComplete="tel"
              value={lookupPhone}
              onChange={(e) => setLookupPhone(e.target.value)}
            />
            <input
              style={{ ...styles.input, marginBottom: 0 }}
              type="email"
              placeholder="Lookup email"
              autoComplete="email"
              value={lookupEmail}
              onChange={(e) => setLookupEmail(e.target.value)}
            />
          </div>

          <button type="button" style={styles.btnSecondary} onClick={handleLookup} disabled={lookupLoading}>
            {lookupLoading ? 'Finding your details...' : 'Find My Details'}
          </button>

          {lookupMessage ? <div style={styles.statusOk}>{lookupMessage}</div> : null}
          {lookupError ? <div style={styles.statusErr}>{lookupError}</div> : null}

          <label style={styles.label}>First Name</label>
          <input
            style={styles.input}
            type="text"
            placeholder="First name"
            autoComplete="given-name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
          />

          <label style={styles.label}>Last Name</label>
          <input
            style={styles.input}
            type="text"
            placeholder="Last name"
            autoComplete="family-name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
          />

          <label style={styles.label}>Phone</label>
          <input
            style={styles.input}
            type="tel"
            placeholder="(216) 555-0100"
            autoComplete="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />

          <label style={styles.label}>Email</label>
          <input
            style={styles.input}
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div style={styles.card}>
          <div style={{ fontSize: font.sizeLg, fontWeight: font.weightBlack, color: colors.navy, marginBottom: spacing.md }}>Service Details</div>

          <label style={styles.label}>Services Needed <span style={{ fontWeight: 400, opacity: 0.6 }}>(select all that apply)</span></label>
          <div style={styles.serviceChipGrid}>
            {['Leak Repair', 'Drain Cleaning', 'Clogged Drain', 'Sump Pump', 'Water Heater',
              'Frozen Pipe', 'Garbage Disposal', 'Toilet Repair', 'Faucet Repair', 'Emergency Service', 'Other'
            ].map(s => {
              const selected = services.includes(s);
              return (
                <button
                  key={s}
                  type="button"
                  style={{
                    ...styles.serviceChip,
                    background: selected ? colors.aqua : colors.bg,
                    color: selected ? colors.onAqua : colors.navy,
                    border: selected ? `1.5px solid ${colors.aqua}` : `1.5px solid rgba(7,27,50,0.2)`,
                  }}
                  onClick={() => setServices(prev =>
                    prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]
                  )}
                >
                  {s}
                </button>
              );
            })}
          </div>

          <label style={styles.label}>Service Address</label>
          <input
            style={styles.input}
            type="text"
            placeholder="Street address"
            autoComplete="street-address"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
          />
          <input
            style={styles.input}
            type="text"
            placeholder="City"
            autoComplete="address-level2"
            value={city}
            onChange={(e) => setCity(e.target.value)}
          />

          <label style={styles.label}>Best Time</label>
          <select style={styles.select} value={bestTime} onChange={(e) => setBestTime(e.target.value)}>
            <option value="">Any available</option>
            <option value="morning">Morning (8am–12pm)</option>
            <option value="afternoon">Afternoon (12pm–5pm)</option>
            <option value="evening">Evening (5pm–8pm)</option>
            <option value="asap">As soon as possible</option>
          </select>

          <button type="button" style={styles.btnSecondary} onClick={handleLoadWindows} disabled={windowLoading}>
            {windowLoading ? 'Checking available times...' : 'Check Real Availability'}
          </button>

          {windowError ? <div style={styles.statusErr}>{windowError}</div> : null}
          {windows.length > 0 ? (
            <div style={styles.slotGrid}>
              {windows.map((slot) => {
                const label = formatWindowLabel(slot.start_time, slot.end_time);
                return (
                  <button
                    type="button"
                    key={`${slot.start_time}-${slot.end_time}`}
                    style={{
                      ...styles.slotBtn,
                      background: selectedWindow?.start_time === slot.start_time ? colors.aqua : undefined,
                      color: selectedWindow?.start_time === slot.start_time ? colors.onAqua : undefined,
                      fontWeight: selectedWindow?.start_time === slot.start_time ? font.weightBlack : undefined,
                    }}
                    onClick={() => { setSelectedWindow(slot); setBestTime(label); }}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          ) : null}

          <label style={styles.label}>Notes (optional)</label>
          <textarea
            style={{ ...styles.input, minHeight: '80px', resize: 'vertical' }}
            placeholder="Describe the issue…"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>

        {bookingError ? <div style={styles.statusErr}>{bookingError}</div> : null}
        <button
          type="button"
          style={{ ...styles.btnPrimary, opacity: bookingLoading ? 0.7 : 1 }}
              disabled={bookingLoading}
              onClick={async () => {
                if (!customerId || !addressId) {
                  window.open(bookingHref, '_blank', 'noopener,noreferrer');
                  return;
                }
                setBookingError('');
                setBookingLoading(true);
                try {
                  const res = await fetch('/.netlify/functions/hcp-create-booking', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      customerId,
                      addressId,
                      services,
                      notes,
                      scheduledStart: selectedWindow?.start_time,
                      scheduledEnd: selectedWindow?.end_time,
                      firstName,
                      lastName,
                      phone,
                      email,
                      address,
                      city,
                    }),
                  });
                  const data = await res.json() as { jobId?: string; invoiceNumber?: string; error?: string };
                  if (!res.ok) throw new Error(data.error ?? 'Booking failed.');
                  setBookingSuccess({ jobId: data.jobId ?? '', invoiceNumber: data.invoiceNumber });
                } catch (err) {
                  setBookingError(err instanceof Error ? err.message : 'Booking failed. Please try again.');
                } finally {
                  setBookingLoading(false);
                }
              }}
            >
              {bookingLoading ? 'Submitting...' : customerId ? 'Book Appointment' : 'Continue to Booking →'}
            </button>
            {!customerId && (
              <div style={{ fontSize: font.sizeSm, color: colors.muted, textAlign: 'center', marginTop: spacing.xs }}>
                Use "Find My Details" above to book in one tap.
              </div>
            )}
        </>
      )}
    </div>
  );
}
