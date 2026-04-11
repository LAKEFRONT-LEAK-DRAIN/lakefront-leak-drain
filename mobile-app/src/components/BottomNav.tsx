import { useLocation, useNavigate } from 'react-router-dom';
import { colors, font, spacing } from '../tokens';

const tabs = [
  { path: '/', icon: '🏠', label: 'Home' },
  { path: '/book', icon: '📅', label: 'Book' },
  { path: '/timeline', icon: '⚡', label: 'Status' },
  { path: '/history', icon: '🗂️', label: 'History' },
];

export default function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <nav style={{
      display: 'flex',
      background: 'rgba(7,27,50,0.97)',
      backdropFilter: 'blur(12px)',
      borderTop: '1px solid rgba(255,255,255,0.08)',
      position: 'sticky',
      bottom: 0,
      zIndex: 100,
      paddingBottom: 'env(safe-area-inset-bottom)',
    }}>
      {tabs.map(tab => {
        const active = location.pathname === tab.path;
        return (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: `${spacing.sm} 0`,
              gap: '2px',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              opacity: active ? 1 : 0.55,
              transition: 'opacity 0.15s',
            }}
            aria-label={tab.label}
            aria-current={active ? 'page' : undefined}
          >
            <span style={{ fontSize: '20px', lineHeight: 1 }}>{tab.icon}</span>
            <span style={{
              fontSize: font.sizeXs,
              fontWeight: active ? font.weightBlack : font.weightNormal,
              color: active ? colors.aqua : colors.onDark,
              letterSpacing: '0.3px',
            }}>{tab.label}</span>
            {active && (
              <span style={{
                position: 'absolute',
                bottom: 'calc(100% + 2px)',
                width: '32px',
                height: '2px',
                background: colors.aqua,
                borderRadius: '2px',
              }} />
            )}
          </button>
        );
      })}
    </nav>
  );
}
