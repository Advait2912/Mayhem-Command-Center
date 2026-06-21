import React from 'react';

const Section: React.FC<{ title: string; accent?: string; children: React.ReactNode }> = ({ title, accent, children }) => (
  <div style={{ marginBottom: 'var(--space-5)' }}>
    <div className="eyebrow" style={{
      marginBottom: 'var(--space-2)',
      color: accent ?? 'var(--accent-cyan)',
      letterSpacing: '0.08em',
    }}>
      {title}
    </div>
    {children}
  </div>
);

const BulletList: React.FC<{ items: React.ReactNode[] }> = ({ items }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
    {items.map((item, i) => (
      <div key={i} style={{
        display: 'flex',
        gap: '10px',
        fontSize: '12px',
        lineHeight: 1.6,
        padding: '6px 10px',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--glass-border)',
        background: 'rgba(84,104,255,0.03)',
        transition: 'background 0.15s ease, border-color 0.15s ease',
      }}
        onMouseEnter={e => {
          (e.currentTarget as HTMLElement).style.background = 'rgba(84,104,255,0.07)';
          (e.currentTarget as HTMLElement).style.borderColor = 'rgba(52,195,214,0.3)';
        }}
        onMouseLeave={e => {
          (e.currentTarget as HTMLElement).style.background = 'rgba(84,104,255,0.03)';
          (e.currentTarget as HTMLElement).style.borderColor = 'var(--glass-border)';
        }}
      >
        <span style={{ color: 'var(--accent-cyan)', flexShrink: 0, fontFamily: 'var(--font-mono)', fontSize: '10px', marginTop: '2px' }}>—</span>
        <span style={{ color: 'var(--text-secondary)' }}>{item}</span>
      </div>
    ))}
  </div>
);

export const About: React.FC = () => {
  return (
    <div style={{ maxWidth: '720px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-5)' }}>
        <div style={{
          fontFamily: 'var(--font-display)',
          fontWeight: 800,
          fontSize: '22px',
          letterSpacing: '-0.02em',
          background: 'linear-gradient(120deg, #fff 15%, var(--accent-cyan) 50%, var(--accent-blue) 75%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          backgroundSize: '200% auto',
          animation: 'shine 6s linear infinite',
          marginBottom: '4px',
        }}>
          About GridLock
        </div>
        <div className="eyebrow" style={{ color: 'var(--accent-cyan)' }}>
          Command Center · Round 2 demo console
        </div>
      </div>

      <div style={{ height: '1px', background: 'linear-gradient(90deg, rgba(84,104,255,0.4), rgba(52,195,214,0.25), transparent)', marginBottom: 'var(--space-5)' }} />

      <Section title="What this is">
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: '8px' }}>
          A test and demo console for the event-driven congestion pipeline. Two operational modes:
        </p>
        <BulletList items={[
          <><strong style={{ color: 'var(--text-primary)' }}>Browse Historical Events</strong> — replays a real Astram-log event through the full advisory pipeline: closure triage, duration prediction, resource recommendation, case-based retrieval, and network resilience.</>,
          <><strong style={{ color: 'var(--text-primary)' }}>New Event Advisory</strong> — featurizes a hypothetical event from scratch using only cached, already-trained artifacts (no retraining, no live API calls) and runs the same advisory pipeline.</>,
        ]} />
      </Section>

      <div style={{ height: '1px', background: 'linear-gradient(90deg, rgba(229,72,77,0.4), rgba(229,72,77,0.1), transparent)', marginBottom: 'var(--space-5)' }} />

      <Section title="What this deliberately does not do" accent="var(--status-danger)">
        <BulletList items={[
          <><strong style={{ color: 'var(--text-primary)' }}>No live GPS / CCTV / vehicle-count / social-media monitoring</strong> — every advisory is a one-shot, pre-event snapshot, not a continuously-updating dashboard.</>,
          <><strong style={{ color: 'var(--text-primary)' }}>No automatic retraining loop</strong> — the "Log actual outcome" form records predicted-vs-actual to <code style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-cyan)', background: 'rgba(52,195,214,0.08)', padding: '1px 4px', borderRadius: '3px' }}>outcomes_log.csv</code>, but retraining is still a separate offline step.</>,
          <><strong style={{ color: 'var(--text-primary)' }}>No calibrated traffic-volume or average-speed-reduction number</strong> — the routing model uses a flat assumed vehicle volume. Footprint size/radius and routing delay are directional indicators, not precise speed/volume drops.</>,
          <><strong style={{ color: 'var(--text-primary)' }}>Tow-truck count and signal-timing suggestion</strong> are transparent formula-based outputs — there is no tow-dispatch or signal-cycle data in this dataset.</>,
        ]} />
      </Section>

      <div style={{ height: '1px', background: 'linear-gradient(90deg, rgba(52,195,214,0.4), rgba(84,104,255,0.2), transparent)', marginBottom: 'var(--space-5)' }} />

      <Section title="Honesty principle" accent="var(--accent-cyan)">
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: '8px' }}>
          Every model reports its own limitation rather than hiding it:
        </p>
        <BulletList items={[
          <><strong style={{ color: 'var(--text-primary)' }}>Closure probability</strong> is isotonic-calibrated — a real empirical frequency, not a raw model score.</>,
          <><strong style={{ color: 'var(--text-primary)' }}>Slow-track duration</strong> is shown as a risk band with an explicit low-confidence note (concordance ≈ 0.566) rather than a false precise number.</>,
          <><strong style={{ color: 'var(--text-primary)' }}>Fast-track duration</strong> intervals are shown as P10 / P50 / P90, not a single point estimate.</>,
        ]} />
      </Section>
    </div>
  );
};
