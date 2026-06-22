import React from 'react';
import { useOutcomes } from '../hooks/useOutcomes';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorBox } from '../components/ErrorBox';
import { OutcomeRecord } from '../services/types';

const officerDelta = (rec: OutcomeRecord): string => {
  if (rec.predicted_officers == null || rec.actual_officers_used == null) return '—';
  const d = rec.actual_officers_used - rec.predicted_officers;
  if (d === 0) return '✓ exact';
  return d > 0 ? `+${d} under-pred` : `${d} over-pred`;
};

const deltaColor = (rec: OutcomeRecord): string => {
  if (rec.predicted_officers == null || rec.actual_officers_used == null) return 'var(--text-muted)';
  const d = rec.actual_officers_used - rec.predicted_officers;
  if (d === 0) return 'var(--status-success)';
  if (Math.abs(d) <= 1) return 'var(--status-warning)';
  return 'var(--status-danger)';
};

const closureMatch = (rec: OutcomeRecord): { text: string; color: string } => {
  const predicted = rec.predicted_closure_probability != null
    ? rec.predicted_closure_probability >= 0.5 ? 'true' : 'false'
    : null;
  const actual = rec.actual_required_closure;
  if (!predicted || !actual) return { text: '—', color: 'var(--text-muted)' };
  const match = predicted === actual;
  return {
    text: match ? '✓ match' : `✗ pred=${predicted}`,
    color: match ? 'var(--status-success)' : 'var(--status-danger)',
  };
};

const EmptyState: React.FC = () => (
  <div style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
    <div style={{ fontSize: '28px', marginBottom: '8px' }}>📋</div>
    <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)', marginBottom: '4px' }}>
      No outcomes logged yet
    </div>
    <div className="eyebrow">
      Use "Log Actual Outcome" on any advisory to add entries
    </div>
  </div>
);

const TH: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <th className="eyebrow" style={{
    padding: '6px 10px',
    textAlign: 'left',
    whiteSpace: 'nowrap',
    background: 'rgba(255, 255, 255,0.06)',
    borderBottom: '1px solid rgba(255, 255, 255,0.2)',
    color: 'var(--accent-cyan)',
    fontWeight: 700,
  }}>
    {children}
  </th>
);

const TD: React.FC<{ children: React.ReactNode; style?: React.CSSProperties; title?: string }> = ({ children, style, title }) => (
  <td style={{ padding: '5px 10px', ...style }} title={title}>
    {children}
  </td>
);

const TrainingStatus: React.FC<{ used: boolean }> = ({ used }) => (
  <span className="metric metric-sm" style={{ 
    color: used ? 'var(--status-success)' : 'var(--status-warning)',
    fontSize: '10px',
    fontWeight: 700,
    textTransform: 'uppercase'
  }}>
    {used ? 'Used' : 'Pending'}
  </span>
);

export const Outcomes: React.FC = () => {

  const { data, loading, error, refresh } = useOutcomes();

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{ marginBottom: 'var(--space-4)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{
            fontFamily: 'var(--font-display)',
            fontWeight: 800,
            fontSize: '18px',
            letterSpacing: '-0.02em',
            color: 'var(--text-primary)',
          }}>
            Outcomes Log
          </div>
          <div className="eyebrow" style={{ marginTop: '3px', color: 'var(--accent-cyan)' }}>
            Predicted vs. actual · field officer feedback
          </div>
        </div>
        <button
          onClick={refresh}
          style={{
            padding: '6px 14px',
            background: 'var(--accent-blue)',
            border: '1px solid var(--border-strong)',
            borderRadius: '30px',
            color: 'var(--bg)',
            cursor: 'pointer',
            fontFamily: 'var(--font-display)',
            fontSize: '12px',
            fontWeight: 700,
            transition: 'transform 0.2s ease, box-shadow 0.2s ease',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = 'var(--glow-blue)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.transform = 'none';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          Refresh
        </button>
      </header>

      <div className="glass-panel" style={{ flex: 1, overflowY: 'auto' }}>
        {loading && <LoadingSpinner fullPage message="Loading outcomes" />}
        {error && <div style={{ padding: 'var(--space-5)' }}><ErrorBox error={error} /></div>}
        {!loading && !error && data?.outcomes.length === 0 && <EmptyState />}

        {!loading && !error && data && data.outcomes.length > 0 && (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
             <thead>
               <tr>
                 {['Logged At', 'Event', 'Closure pred.', 'Closure match', 'Officers pred.', 'Officers actual', 'Officer Δ', 'Duration', 'Priority', 'Training', 'Notes'].map(h => (
                   <TH key={h}>{h}</TH>
                 ))}
               </tr>
             </thead>

            <tbody>
              {data.outcomes.map((row, idx) => {
                const cl = closureMatch(row);
                return (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: '1px solid rgba(255,255,255,0.04)',
                      transition: 'background 0.15s ease',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255, 255, 255,0.05)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  >
                    <TD>
                      <span className="metric metric-sm" style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
                        {new Date(row.logged_at).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </TD>
                    <TD>
                      <div style={{ fontWeight: 600, fontFamily: 'var(--font-display)', fontSize: '12px', color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
                        {row.event_cause.replace(/_/g, ' ')}
                      </div>
                      <div className="eyebrow" style={{ marginTop: '1px', color: 'var(--accent-cyan)' }}>{row.zone}</div>
                    </TD>
                    <TD>
                      <span className="metric metric-sm" style={{ color: 'var(--text-secondary)' }}>
                        {row.predicted_closure_probability != null ? `${(row.predicted_closure_probability * 100).toFixed(0)}%` : '—'}
                      </span>
                    </TD>
                    <TD>
                      <span className="metric metric-sm" style={{ color: cl.color }}>{cl.text}</span>
                    </TD>
                    <TD>
                      <span className="metric metric-sm">{row.predicted_officers ?? '—'}</span>
                    </TD>
                    <TD>
                      <span className="metric metric-sm">{row.actual_officers_used ?? '—'}</span>
                    </TD>
                    <TD>
                      <span className="metric metric-sm" style={{ color: deltaColor(row) }}>{officerDelta(row)}</span>
                    </TD>
                    <TD>
                      <span className="metric metric-sm" style={{ color: 'var(--text-secondary)' }}>
                        {row.actual_duration_hrs != null ? `${row.actual_duration_hrs}h` : '—'}
                      </span>
                    </TD>
                    <TD>
                      <span className="metric metric-sm" style={{ color: row.actual_priority === 'HIGH' ? 'var(--status-danger)' : 'var(--text-secondary)' }}>
                        {row.actual_priority ?? '—'}
                      </span>
                    </TD>
                    <TD>
                      <TrainingStatus used={row.used_for_training ?? false} />
                    </TD>
                    <TD style={{ color: 'var(--text-muted)', maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.notes || ''}>
                      {row.notes || '—'}
                    </TD>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
