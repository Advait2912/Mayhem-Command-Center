import React from 'react';
import { 
  TriageCard, DurationCard, SpatialCard, 
  ResourceCard, SimilarEventsCard, ConflictCard 
} from './ReportCards';

export const IntelligenceReport = ({ report }) => {
  if (!report) {
    return (
      <div className="panel report-panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        Enter an event to generate operational intelligence
      </div>
    );
  }

  return (
    <div className="panel report-panel">
      <h2 style={{ marginBottom: '20px' }}>Intelligence Report</h2>
      <TriageCard data={report.triage} />
      <DurationCard data={report.duration} />
      <SpatialCard data={report.spatial_impact} />
      <ResourceCard data={report.resources} />
      <SimilarEventsCard events={report.similar_events} />
      <ConflictCard data={report.conflict_check} />
    </div>
  );
};
