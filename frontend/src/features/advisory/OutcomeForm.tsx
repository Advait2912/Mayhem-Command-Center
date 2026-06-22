import React, { useState } from 'react';
import { Advisory } from '../../services/types';
import { useOutcomes } from '../../hooks/useOutcomes';


interface OutcomeFormProps {
  advisory: Advisory;
  sourceEventId?: string | number;
}

export const OutcomeForm: React.FC<OutcomeFormProps> = ({ advisory, sourceEventId }) => {
  const { submitOutcome, isSubmitting } = useOutcomes();
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const [actualOfficers, setActualOfficers] = useState('');
  const [actualDuration, setActualDuration] = useState('');
  const [actualClosure, setActualClosure] = useState('');
  const [actualPriority, setActualPriority] = useState('');
  const [notes, setNotes] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    try {
      await submitOutcome({
        source_event_id: sourceEventId,
        event_cause: advisory.event_cause,
        zone: advisory.zone,
        predicted_officers: advisory.recommended_officers,
        predicted_closure_probability: advisory.closure_probability,
        predicted_cascade_risk_score: advisory.cascade_risk_score,
        actual_officers_used: actualOfficers ? parseInt(actualOfficers) : undefined,
        actual_duration_hrs: actualDuration ? parseFloat(actualDuration) : undefined,
        actual_required_closure: actualClosure || undefined,
        actual_priority: actualPriority || undefined,
        notes: notes || undefined,
      });
      setSuccess(true);
      // reset form
      setActualOfficers('');
      setActualDuration('');
      setActualClosure('');
      setActualPriority('');
      setNotes('');
    } catch (err: any) {
      setError(err.message || 'Failed to log outcome.');
    }
  };

  return (
    <div>
      {success && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'var(--status-success-bg)', color: 'var(--status-success)', borderRadius: 'var(--radius-sm)' }}>
          Outcome logged successfully.
        </div>
      )}
      {error && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'var(--status-danger-bg)', color: '#FFFFFF', borderRadius: 'var(--radius-sm)' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '0.5rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '3px' }}>Actual Officers Used</label>
            <input 
              type="number" 
              value={actualOfficers} 
              onChange={e => setActualOfficers(e.target.value)} 
              style={{ width: '100%', padding: '0.4rem 0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.2)', color: 'white', fontFamily: 'var(--font-mono)', fontSize: '12px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '3px' }}>Actual Duration (hrs)</label>
            <input 
              type="number" 
              step="0.1" 
              value={actualDuration} 
              onChange={e => setActualDuration(e.target.value)} 
              style={{ width: '100%', padding: '0.4rem 0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.2)', color: 'white', fontFamily: 'var(--font-mono)', fontSize: '12px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '3px' }}>Required Road Closure?</label>
            <select 
              value={actualClosure} 
              onChange={e => setActualClosure(e.target.value)}
              style={{ width: '100%', padding: '0.4rem 0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.2)', color: 'white', fontFamily: 'var(--font-mono)', fontSize: '12px' }}
            >
              <option value="">-- Select --</option>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '3px' }}>Actual Priority</label>
            <select
              value={actualPriority}
              onChange={e => setActualPriority(e.target.value)}
              style={{ width: '100%', padding: '0.4rem 0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.2)', color: 'white', fontFamily: 'var(--font-mono)', fontSize: '12px' }}
            >
              <option value="">-- Select --</option>
              <option value="HIGH">High</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '10px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '3px' }}>Notes</label>
          <textarea 
            value={notes} 
            onChange={e => setNotes(e.target.value)} 
            rows={3}
            style={{ width: '100%', padding: '0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.2)', color: 'white', resize: 'vertical' }}
          />
        </div>

        <button 
          type="submit" 
          disabled={isSubmitting}
          style={{
            alignSelf: 'flex-start',
            padding: '6px 18px',
            background: 'var(--accent-blue)',
            border: '1px solid var(--border-strong)',
            color: 'var(--bg)',
            borderRadius: '30px',
            fontWeight: 700,
            fontFamily: 'var(--font-display)',
            fontSize: '12px',
            opacity: isSubmitting ? 0.7 : 1,
            cursor: 'pointer',
            transition: 'transform 0.2s, box-shadow 0.2s',
          }}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Log'}
        </button>
      </form>
    </div>
  );
};
