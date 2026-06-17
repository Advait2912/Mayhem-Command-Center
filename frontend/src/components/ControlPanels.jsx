import React from 'react';

export const InputPanel = ({ onGenerate, onScenarioSelect, currentInput, setInput }) => {
  const handleChange = (e) => setInput({ ...currentInput, [e.target.name]: e.target.value });

  return (
    <div className="panel side-panel">
      <h2>Event Input</h2>
      <div className="input-group">
        <input name="event_type" value={currentInput.event_type} onChange={handleChange} placeholder="Event Type" className="form-input" />
        <input name="location" value={currentInput.location} onChange={handleChange} placeholder="Location" className="form-input" />
        <input name="zone" value={currentInput.zone} onChange={handleChange} placeholder="Zone" className="form-input" />
        <input name="time" value={currentInput.time} onChange={handleChange} placeholder="Time" className="form-input" />
        <textarea name="description" value={currentInput.description} onChange={handleChange} placeholder="Description" className="form-input" style={{ height: '80px' }} />
        <button onClick={() => onGenerate(currentInput)} className="btn-primary">Generate Report</button>
      </div>
    </div>
  );
};

export const ScenarioPanel = ({ onScenarioSelect }) => {
  const scenarios = [
    { id: 'RCB_MATCH', label: 'RCB Match' },
    { id: 'VIP_MOVEMENT', label: 'VIP Movement' },
    { id: 'BUS_BREAKDOWN', label: 'Bus Breakdown' },
    { id: 'WATER_LOGGING', label: 'Water Logging' },
    { id: 'METRO_CONSTRUCTION', label: 'Metro Construction' },
  ];

  return (
    <div style={{ marginTop: '30px' }}>
      <h3 style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Quick Scenarios</h3>
      <div className="scenario-grid">
        {scenarios.map(s => (
          <button key={s.id} onClick={() => onScenarioSelect(s.id)} className="scenario-btn">{s.label}</button>
        ))}
      </div>
    </div>
  );
};
