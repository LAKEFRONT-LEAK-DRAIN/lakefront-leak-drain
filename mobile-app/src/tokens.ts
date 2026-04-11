// Lakefront Leak & Drain – Design Tokens
// Mirrors the website brand exactly; reusable in React Native later

export const colors = {
  // Brand primaries
  navy: '#071b32',
  aqua: '#00adb5',
  portalBlue: '#0f77cc',

  // Backgrounds
  bg: '#f4f8fb',
  card: '#ffffff',
  heroBg: 'linear-gradient(180deg,#f7fbfc 0%,#f4f8fb 45%,#fff 100%)',

  // Text
  ink: '#0f172a',
  muted: '#334155',
  onDark: '#ffffff',
  onAqua: '#041014',

  // Status / accents
  warning: '#f59e0b',
  warningBg: '#fffbeb',
  success: '#10b981',
  error: '#ef4444',

  // Surfaces
  navBg: 'rgba(7,27,50,0.96)',
  badgeBg: 'rgba(0,173,181,0.16)',
  badgeBorder: 'rgba(0,173,181,0.26)',
  badgeText: '#e6f6f7',
  overlay: 'rgba(7,27,50,0.06)',
} as const;

export const font = {
  family: "system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif",
  sizeXs: '11px',
  sizeSm: '13px',
  sizeMd: '15px',
  sizeLg: '18px',
  sizeXl: '22px',
  size2xl: '28px',
  weightNormal: 400,
  weightBold: 700,
  weightBlack: 900,
} as const;

export const radius = {
  sm: '10px',
  md: '14px',
  lg: '18px',
  xl: '24px',
  pill: '999px',
} as const;

export const shadow = {
  card: '0 2px 12px rgba(7,27,50,0.08)',
  logo: '0 8px 18px rgba(0,0,0,0.18)',
  sticky: '0 -2px 12px rgba(7,27,50,0.10)',
} as const;

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
} as const;

// HCP booking / portal URLs (shared across app)
export const hcpUrls = {
  book: 'https://book.housecallpro.com/book/Lakefront-Leak--Drain/ae2653195f4d42308810145d8ff8bf21?v2=true',
  portal: 'https://client.housecallpro.com/customer_portal/request-link?token=19d1b66af5ca4e928d038e6f3caa0f44',
  phone: 'tel:+12165057765',
  phoneDisplay: '(216) 505-7765',
} as const;
