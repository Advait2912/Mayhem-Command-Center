import React from 'react';
import { useOutcomes } from '../hooks/useOutcomes';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorBox } from '../components/ErrorBox';
import { getProbabilityBadge } from '../components/Badge';

export const Outcomes: React.FC = () => {
  const { data, loading, error, refresh } = useOutcomes();

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <header style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ color: 'var(--text-primary)', margin: 0 }}>Outcomes Log</h2>
          <p style={{ color: 'var(--text-secondary)', margin: '0.25rem 0 0 0', fontSize: '0.9rem' }}>
            Historical feedback data from field officers.
          </p>
        </div>
        <button 
          onClick={refresh}
          style={{ padding: '0.5rem 1rem', background: 'var(--bg-panel)', border: '1px solid var(--glass-border)', borderRadius: 'var(--radius-sm)', color: 'white', cursor: 'pointer' }}
        >
          🔄 Refresh
        </button>
      </header>

      <div className="glass-panel" style={{ flex: 1, overflowY: 'auto' }}>
        {loading && <LoadingSpinner fullPage />}
        {error && <div style={{ padding: '2rem' }}><ErrorBox error={error} /></div>}
        
        {!loading && !error && data?.outcomes.length === 0 && (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No outcomes logged yet.
          </div>
        )}

        {!loading && !error && data && data.outcomes.length > 0 && (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.2)', textAlign: 'left' }}>
                <th style={{ padding: '1rem' }}>Logged At</th>
                <th style={{ padding: '1rem' }}>Source ID</th>
                <th style={{ padding: '1rem' }}>Cause & Zone</th>
                <th style={{ padding: '1rem' }}>Prediction</th>
                <th style={{ padding: '1rem' }}>Actual</th>
                <th style={{ padding: '1rem' }}>Notes</th>
              </tr>
            </thead>
            <tbody>
              {data.outcomes.map((row, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '1rem', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                    {new Date(row.logged_at).toLocaleString()}
                  </td>
                  <td style={{ padding: '1rem' }}>{row.source_event_id || '-'}</td>
                  <td style={{ padding: '1rem' }}>
                    <div style={{ fontWeight: 500 }}>{row.event_cause}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{row.zone}</div>
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', alignItems: 'flex-start' }}>
                      {row.predicted_closure_probability != null && getProbabilityBadge(row.predicted_closure_probability)}
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        Officers: {row.predicted_officers ?? '-'}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      <span><strong>Closed:</strong> {row.actual_required_closure ?? '-'}</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        Dur: {row.actual_duration_hrs ? `${row.actual_duration_hrs}h` : '-'} | Off: {row.actual_officers_used ?? '-'}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '1rem', color: 'var(--text-secondary)', maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={row.notes || ''}>
                    {row.notes || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
