import React from 'react';

export const About: React.FC = () => {
  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', color: 'var(--text-primary)', lineHeight: 1.6 }}>
      <h2 style={{ color: 'var(--accent-blue)', marginBottom: '1.5rem' }}>About this system</h2>
      
      <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1rem', color: 'var(--text-primary)' }}>What this is</h3>
        <p style={{ marginBottom: '1rem' }}>
          A test/demo console for the Round 2 event-driven congestion pipeline. Two modes:
        </p>
        <ul style={{ paddingLeft: '1.5rem', marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <li>
            <strong>Browse Historical Events</strong> — replays a real Astram-log event through the full advisory pipeline (closure triage, duration, resource recommendation, case-based retrieval, network resilience).
          </li>
          <li>
            <strong>New Event Advisory</strong> — featurizes a hypothetical event from scratch using only cached, already-trained artifacts (no retraining, no live API calls) and runs the same advisory pipeline.
          </li>
        </ul>
      </div>

      <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1rem', color: '#fca5a5' }}>What this deliberately does not do</h3>
        <ul style={{ paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <li>
            <strong>No live GPS / CCTV / vehicle-count / social-media monitoring</strong> — every advisory is a one-shot, pre-event snapshot, not a continuously-updating dashboard.
          </li>
          <li>
            <strong>No automatic retraining loop</strong> — the "Log actual outcome" form on every advisory records predicted-vs-actual to <code>outcomes_log.csv</code>, closing the data-collection gap, but turning that log into a retrained model is still a separate offline step, not something this app does live.
          </li>
          <li>
            <strong>No calibrated traffic-volume or average-speed-reduction number</strong> — the routing model uses a flat assumed vehicle volume because no real per-road traffic-count data exists in this dataset. Footprint size/radius and routing delay are reported instead, honestly labelled as directional, not precise speed/volume drops.
          </li>
          <li>
            <strong>Tow-truck count and signal-timing suggestion are now shown</strong>, but both are transparent formulas (same standard as the officer-count formula), not trained models — there's no tow-dispatch or signal-cycle data in this dataset to fit one on.
          </li>
        </ul>
      </div>

      <div className="glass-panel" style={{ padding: '2rem', borderLeft: '4px solid var(--accent-purple)' }}>
        <h3 style={{ marginBottom: '1rem', color: 'var(--accent-purple)' }}>Honesty principle</h3>
        <p style={{ marginBottom: '1rem' }}>
          Every model reports its own limitation rather than hiding it:
        </p>
        <ul style={{ paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <li><strong>Closure probability</strong> is isotonic-calibrated (a real empirical frequency, not a raw score).</li>
          <li><strong>Slow-track duration</strong> is shown as a risk band with an explicit low-confidence note (concordance ≈0.566) rather than a fake precise number.</li>
          <li><strong>Fast-track duration</strong> intervals are shown as P10/P50/P90, not a single point estimate.</li>
        </ul>
      </div>
    </div>
  );
};
