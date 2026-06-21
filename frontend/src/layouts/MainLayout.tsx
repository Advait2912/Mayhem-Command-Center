import React, { useEffect, useState } from 'react';
import { Outlet, NavLink, Link } from 'react-router-dom';

// Inline SVG icons (Feather/Lucide style)
const IconHistory = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
    <path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>
  </svg>
);
const IconPlus = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 8v8M8 12h8"/>
  </svg>
);
const IconRadio = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="2"/><path d="M16.24 7.76a6 6 0 0 1 0 8.49"/><path d="M7.76 7.76a6 6 0 0 0 0 8.49"/>
    <path d="M20.07 4.93a10 10 0 0 1 0 14.14M3.93 4.93a10 10 0 0 0 0 14.14"/>
  </svg>
);
const IconClipboard = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
    <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>
  </svg>
);
const IconInfo = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 16v-4M12 8h.01"/>
  </svg>
);

const navItems = [
  { to: '/app', label: 'Historical Events', icon: <IconHistory />, end: true },
  { to: '/app/new', label: 'New Advisory', icon: <IconPlus />, end: false },
  { to: '/app/live', label: 'Live Situation Room', icon: <IconRadio />, end: false },
  { to: '/app/outcomes', label: 'Outcomes Log', icon: <IconClipboard />, end: false },
  { to: '/app/about', label: 'About', icon: <IconInfo />, end: false },
];

export const MainLayout: React.FC = () => {
  const [clock, setClock] = useState(() =>
    new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  );

  useEffect(() => {
    const id = setInterval(() => {
      setClock(new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', position: 'relative' }}>
      {/* Ambient glow blobs */}
      <div className="ambient-glow ambient-glow-1" />
      <div className="ambient-glow ambient-glow-2" />

      {/* Sidebar */}
      <aside style={{
        width: '210px',
        flexShrink: 0,
        background: 'rgba(15, 17, 22, 0.92)',
        borderRight: '1px solid rgba(84,104,255,0.15)',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        zIndex: 10,
        backdropFilter: 'blur(12px)',
      }}>
        {/* Logo → links to landing page */}
        <Link to="/" style={{ textDecoration: 'none' }}>
          <div style={{
            padding: 'var(--space-4)',
            borderBottom: '1px solid rgba(84,104,255,0.12)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            transition: 'background var(--transition-fast)',
          }}
            onMouseEnter={e => (e.currentTarget.style.background = 'rgba(84,104,255,0.06)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
          >
            {/* Pulsing cyan dot — landing-page style */}
            <span style={{
              width: '9px',
              height: '9px',
              borderRadius: '50%',
              background: 'var(--accent-cyan)',
              boxShadow: '0 0 8px var(--accent-cyan), 0 0 18px var(--accent-cyan-glow)',
              flexShrink: 0,
              animation: 'dotPulse 2s ease-in-out infinite',
            }} />
            <div>
              <div style={{
                fontFamily: 'var(--font-display)',
                fontSize: '15px',
                fontWeight: 800,
                letterSpacing: '-0.01em',
                background: 'linear-gradient(90deg, #fff 20%, var(--accent-cyan) 80%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}>GridLock</div>
              <div style={{ fontSize: '9px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-muted)', marginTop: '1px' }}>Command Center</div>
            </div>
          </div>
        </Link>

        {/* Nav */}
        <nav style={{ padding: 'var(--space-3) var(--space-2)', display: 'flex', flexDirection: 'column', gap: '2px', flex: 1 }}>
          {navItems.map(({ to, label, icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-3)',
                padding: '7px 10px',
                borderRadius: 'var(--radius-md)',
                borderLeft: isActive ? '2px solid var(--accent-cyan)' : '2px solid transparent',
                background: isActive
                  ? 'linear-gradient(90deg, rgba(52,195,214,0.1), rgba(84,104,255,0.06))'
                  : 'transparent',
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 400,
                fontSize: '12.5px',
                textDecoration: 'none',
                transition: 'all var(--transition-fast)',
                boxShadow: isActive ? '0 0 10px rgba(52,195,214,0.12)' : 'none',
              })}
            >
              {icon}
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer: live clock */}
        <div style={{
          padding: 'var(--space-3) var(--space-4)',
          borderTop: '1px solid rgba(84,104,255,0.12)',
        }}>
          <div className="metric metric-sm panel-live" style={{
            color: 'var(--accent-cyan)',
            marginBottom: 'var(--space-1)',
            padding: '2px 6px',
            borderRadius: 'var(--radius-sm)',
            display: 'inline-block',
            background: 'rgba(52,195,214,0.06)',
            border: '1px solid rgba(52,195,214,0.15)',
          }}>
            {clock} IST
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)', fontSize: '10px', color: 'var(--status-success)', marginTop: '4px' }}>
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: 'var(--status-success)', boxShadow: '0 0 6px var(--status-success)', display: 'inline-block' }} />
            System Operational
          </div>
        </div>
      </aside>

      <main style={{ flex: 1, padding: 'var(--space-5)', height: '100vh', overflowY: 'auto', minWidth: 0, position: 'relative', zIndex: 1 }}>
        <Outlet />
      </main>

      {/* Inline keyframe for dot pulse */}
      <style>{`
        @keyframes dotPulse {
          0%, 100% { opacity: 1; box-shadow: 0 0 8px var(--accent-cyan), 0 0 18px rgba(52,195,214,0.4); }
          50% { opacity: 0.4; box-shadow: 0 0 4px var(--accent-cyan); }
        }
      `}</style>
    </div>
  );
};
