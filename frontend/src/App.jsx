import React, { useState } from 'react';
import './styles/index.css';
import { InputPanel, ScenarioPanel } from './components/ControlPanels';
import { TacticalMap } from './components/TacticalMap';
import { IntelligenceReport } from './components/IntelligenceReport';
import { api } from './services/api';
import { SCENARIOS } from './data/scenarios';

const App = () => {
  const [input, setInput] = useState({
    event_type: '',
    location: '',
    zone: '',
    time: '',
    description: ''
  });
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mapCenter, setMapCenter] = useState([12.9716, 77.5946]);

  const handleGenerate = async (eventData) => {
    setLoading(true);
    try {
      const data = await api.generateReport(eventData);
      setReport(data);
      // Dynamic center based on input if available, otherwise fallback
      // In a real app, we'd geocode the 'location' string.
    } catch (e) {
      alert('Error generating report');
    } finally {
      setLoading(false);
    }
  };

  const handleScenario = (id) => {
    const scenario = SCENARIOS[id];
    setInput(scenario);
    setMapCenter(scenario.coords);
    handleGenerate(scenario);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="app-title">GRIDLOCK // COMMAND CENTER</div>
        <div className="mock-indicator">Mode: Simulated / Mock</div>
      </header>

      <div className="command-center-grid" style={{ position: 'relative' }}>
        {loading && (
          <div className="loading-overlay">
            <div className="spinner"></div>
          </div>
        )}
        
        <div className="panel side-panel">
          <InputPanel 
            currentInput={input} 
            setInput={setInput} 
            onGenerate={handleGenerate} 
          />
          <ScenarioPanel onScenarioSelect={handleScenario} />
        </div>

        <TacticalMap impactData={report?.spatial_impact} center={mapCenter} />

        <IntelligenceReport report={report} />
      </div>
    </div>
  );
};

export default App;
