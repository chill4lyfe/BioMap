import { useState } from 'react';

interface QCReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  datasetName: string;
  processingMode: 'basic' | 'advanced';
}

type Severity = 'warning' | 'error' | 'info';

interface Anomaly {
  id: string;
  category: 'tracks' | 'divisions' | 'missing';
  cellId: string;
  severity: Severity;
  issue: string;
  frames: string;
  action: string;
}

interface DatasetMockData {
  uncertainTracksCount: number;
  suspiciousDivisionsCount: number;
  missingDetectionsCount: number;
  anomalies: Anomaly[];
}

const mockQCData: Record<string, Record<'basic' | 'advanced', DatasetMockData>> = {
  'Fluo-C3DH-A549': {
    basic: {
      uncertainTracksCount: 11,
      suspiciousDivisionsCount: 8,
      missingDetectionsCount: 9,
      anomalies: [
        { id: 'QC-101', category: 'tracks', cellId: '#89', severity: 'warning', issue: 'Low tracking confidence (<72%)', frames: 'Frames 42–48', action: 'Verify boundary segmentation' },
        { id: 'QC-102', category: 'divisions', cellId: '#17', severity: 'error', issue: 'Suspicious division trajectory (extreme daughter velocity)', frames: 'Frame 34', action: 'Check for lineage misattribution' },
        { id: 'QC-103', category: 'missing', cellId: '#44', severity: 'info', issue: 'Missing detection gap (3 consecutive frames)', frames: 'Frames 18–20', action: 'Linear interpolation applied' },
        { id: 'QC-104', category: 'tracks', cellId: '#112', severity: 'warning', issue: 'Rapid displacement anomaly (possible collision)', frames: 'Frames 12–15', action: 'Manual track inspection recommended' },
        { id: 'QC-105', category: 'divisions', cellId: '#08', severity: 'warning', issue: 'Asymmetric volume split post-mitosis', frames: 'Frame 51', action: 'Review daughter centroid masks' },
        { id: 'QC-106', category: 'missing', cellId: '#61', severity: 'info', issue: 'Missing detection gap (2 consecutive frames)', frames: 'Frames 5–6', action: 'Linear interpolation applied' },
      ],
    },
    advanced: {
      uncertainTracksCount: 3,
      suspiciousDivisionsCount: 2,
      missingDetectionsCount: 3,
      anomalies: [
        { id: 'QC-201', category: 'tracks', cellId: '#89', severity: 'warning', issue: 'Low tracking confidence (<80%)', frames: 'Frames 44–46', action: 'Verify boundary segmentation' },
        { id: 'QC-202', category: 'divisions', cellId: '#17', severity: 'warning', issue: 'Asymmetric volume split post-mitosis', frames: 'Frame 34', action: 'Review daughter centroid masks' },
        { id: 'QC-203', category: 'missing', cellId: '#44', severity: 'info', issue: 'Missing detection gap (1 frame)', frames: 'Frame 19', action: 'Linear interpolation applied' },
      ],
    },
  },
};

const defaultQCData: Record<'basic' | 'advanced', DatasetMockData> = {
  basic: {
    uncertainTracksCount: 12,
    suspiciousDivisionsCount: 6,
    missingDetectionsCount: 9,
    anomalies: [
      { id: 'QC-D01', category: 'tracks', cellId: '#22', severity: 'warning', issue: 'Low tracking confidence (<75%)', frames: 'Frames 10–14', action: 'Verify boundary segmentation' },
      { id: 'QC-D02', category: 'divisions', cellId: '#05', severity: 'error', issue: 'Suspicious division trajectory', frames: 'Frame 21', action: 'Check for lineage misattribution' },
      { id: 'QC-D03', category: 'missing', cellId: '#30', severity: 'info', issue: 'Missing detection gap (3 consecutive frames)', frames: 'Frames 8–10', action: 'Linear interpolation applied' },
    ],
  },
  advanced: {
    uncertainTracksCount: 3,
    suspiciousDivisionsCount: 2,
    missingDetectionsCount: 3,
    anomalies: [
      { id: 'QC-D11', category: 'tracks', cellId: '#22', severity: 'warning', issue: 'Low tracking confidence (<85%)', frames: 'Frames 11–12', action: 'Verify boundary segmentation' },
      { id: 'QC-D12', category: 'missing', cellId: '#30', severity: 'info', issue: 'Missing detection gap (1 frame)', frames: 'Frame 9', action: 'Linear interpolation applied' },
    ],
  },
};

export default function QCReportModal({ isOpen, onClose, datasetName, processingMode }: QCReportModalProps) {
  const [activeTab, setActiveTab] = useState<'all' | 'tracks' | 'divisions' | 'missing'>('all');

  if (!isOpen) return null;

  const qcData = mockQCData[datasetName]?.[processingMode] ?? defaultQCData[processingMode];

  const filteredAnomalies = activeTab === 'all'
    ? qcData.anomalies
    : qcData.anomalies.filter((item) => item.category === activeTab);

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(2, 6, 23, 0.85)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 9999, padding: '20px'
    }}>
      <div style={{
        backgroundColor: '#0b1329', border: '1px solid #1e293b', borderRadius: '12px',
        width: '100%', maxWidth: '780px', maxHeight: '85vh',
        display: 'flex', flexDirection: 'column',
        boxShadow: '0 20px 40px rgba(0,0,0,0.6)', color: '#f8fafc', overflow: 'hidden'
      }}>
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '16px 20px', borderBottom: '1px solid #1e293b', backgroundColor: '#0f172a'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '18px' }}>🛡️</span>
            <div>
              <h2 style={{ fontSize: '15px', fontWeight: 'bold', margin: 0 }}>
                Anomaly Report
              </h2>
              <span style={{ fontSize: '11px', color: '#64748b' }}>
                {datasetName} · {processingMode === 'basic' ? 'Classical CV' : 'AI / Cellpose'}
              </span>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '18px', cursor: 'pointer' }}>✕</button>
        </div>

        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px',
          padding: '16px 20px', backgroundColor: '#080e1e', borderBottom: '1px solid #1e293b'
        }}>
          <div style={{ backgroundColor: '#111e38', padding: '10px 14px', borderRadius: '8px', border: '1px solid #1e293b' }}>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Uncertain Tracks</span>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#f59e0b', marginTop: '2px' }}>{qcData.uncertainTracksCount}</div>
          </div>
          <div style={{ backgroundColor: '#111e38', padding: '10px 14px', borderRadius: '8px', border: '1px solid #1e293b' }}>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Suspicious Divisions</span>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#ef4444', marginTop: '2px' }}>{qcData.suspiciousDivisionsCount}</div>
          </div>
          <div style={{ backgroundColor: '#111e38', padding: '10px 14px', borderRadius: '8px', border: '1px solid #1e293b' }}>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Missing Detections</span>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#38bdf8', marginTop: '2px' }}>{qcData.missingDetectionsCount}</div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', padding: '12px 20px', borderBottom: '1px solid #1e293b' }}>
          {[
            { key: 'all', label: 'All Issues' },
            { key: 'tracks', label: 'Uncertain Tracks' },
            { key: 'divisions', label: 'Suspicious Divisions' },
            { key: 'missing', label: 'Missing Gaps' }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              style={{
                backgroundColor: activeTab === tab.key ? '#0284c7' : '#111e38',
                color: activeTab === tab.key ? '#fff' : '#94a3b8',
                border: '1px solid #1e293b', padding: '5px 12px', borderRadius: '6px',
                fontSize: '12px', fontWeight: '500', cursor: 'pointer'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {filteredAnomalies.map((item) => (
              <div key={item.id} style={{ backgroundColor: '#111e38', border: '1px solid #1e293b', borderRadius: '8px', padding: '12px 16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span style={{
                    backgroundColor: item.severity === 'error' ? 'rgba(239, 68, 68, 0.2)' : item.severity === 'warning' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(56, 189, 248, 0.2)',
                    color: item.severity === 'error' ? '#ef4444' : item.severity === 'warning' ? '#f59e0b' : '#38bdf8',
                    fontSize: '10px', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold', textTransform: 'uppercase'
                  }}>
                    {item.severity}
                  </span>
                  <strong style={{ fontSize: '13px', color: '#f1f5f9' }}>{item.cellId}</strong>
                  <span style={{ fontSize: '11px', color: '#64748b' }}>({item.frames})</span>
                </div>
                <p style={{ margin: 0, fontSize: '12px', color: '#cbd5e1' }}>{item.issue}</p>
                <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: '#94a3b8', fontStyle: 'italic' }}>Action: {item.action}</p>
              </div>
            ))}
          </div>
        </div>

        <div style={{
          padding: '12px 20px', borderTop: '1px solid #1e293b', backgroundColor: '#0f172a',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <span style={{ fontSize: '11px', color: '#64748b' }}>BioMap Anomaly Report</span>
          <button onClick={onClose} style={{
            backgroundColor: '#0284c7', color: '#fff', border: 'none', padding: '6px 16px',
            borderRadius: '6px', fontSize: '12px', fontWeight: '600', cursor: 'pointer'
          }}>
            Close Report
          </button>
        </div>
      </div>
    </div>
  );
}