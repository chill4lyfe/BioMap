import { useState } from 'react';

interface QueryResult {
  type: string;
  target: string;
  message: string;
  stats?: Record<string, any>;
}

interface ResearcherQueryBarProps {
  onExecuteQuery?: (result: QueryResult) => void;
}

export default function ResearcherQueryBar({ onExecuteQuery }: ResearcherQueryBarProps) {
  const [query, setQuery] = useState('');
  const [activeResult, setActiveResult] = useState<QueryResult | null>(null);

  const presetQueries = [
    "Show lineage of Cell #17",
    "Show divisions between frames 30-60",
    "Highlight low confidence tracks (<80%)",
    "Filter active tracks at frame 45"
  ];

  const handleSearch = (queryString?: string) => {
    const text = queryString || query;
    if (!text.trim()) return;

    const lower = text.toLowerCase();
    let result: QueryResult;

    if (lower.includes('cell #') || lower.includes('cell')) {
      const match = lower.match(/\d+/);
      const cellId = match ? match[0] : '17';
      result = {
        type: 'LINEAGE_ISOLATION',
        target: `Cell #${cellId}`,
        message: `Isolated lineage tree for Cell #${cellId}. Showing parent-daughter trajectories across all frames.`,
        stats: { generations: 3, totalDivisions: 2 }
      };
    } else if (lower.includes('division') || lower.includes('frame')) {
      result = {
        type: 'FRAME_RANGE_FILTER',
        target: 'Frames 30–60',
        message: 'Filtered viewport to Frames 30–60. Identified 4 mitosis events.',
        stats: { eventsFound: 4, affectedTracks: ['#12', '#17', '#44', '#89'] }
      };
    } else {
      result = {
        type: 'CUSTOM_QUERY',
        target: text,
        message: `Filter applied for query: "${text}". Highlighted matching trajectories.`,
        stats: { matches: 8 }
      };
    }

    setActiveResult(result);
    if (onExecuteQuery) onExecuteQuery(result);
  };

  return (
    <div style={{
      backgroundColor: '#0b1329',
      border: '1px solid #1e293b',
      borderRadius: '12px',
      padding: '16px',
      color: '#fff',
      boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
      marginBottom: '16px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
        <span style={{ fontSize: '16px' }}>🔬</span>
        <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#38bdf8', letterSpacing: '0.5px' }}>
          NATURAL LANGUAGE RESEARCHER QUERY LAYER
        </span>
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder='Try "Show lineage of Cell #17" or "Show divisions between frames 30-60"...'
          style={{
            flex: 1,
            backgroundColor: '#111e38',
            border: '1px solid #334155',
            borderRadius: '8px',
            padding: '10px 14px',
            color: '#fff',
            fontSize: '13px',
            outline: 'none'
          }}
        />
        <button
          onClick={() => handleSearch()}
          style={{
            backgroundColor: '#0284c7',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            padding: '0 18px',
            fontSize: '13px',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          Execute
        </button>
      </div>

      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '10px' }}>
        <span style={{ fontSize: '11px', color: '#64748b', alignSelf: 'center' }}>Suggested:</span>
        {presetQueries.map((preset, idx) => (
          <button
            key={idx}
            onClick={() => {
              setQuery(preset);
              handleSearch(preset);
            }}
            style={{
              backgroundColor: '#1e293b',
              color: '#94a3b8',
              border: '1px solid #334155',
              borderRadius: '9999px',
              padding: '3px 10px',
              fontSize: '11px',
              cursor: 'pointer'
            }}
          >
            {preset}
          </button>
        ))}
      </div>

      {activeResult && (
        <div style={{
          marginTop: '12px',
          padding: '10px 14px',
          backgroundColor: 'rgba(56, 189, 248, 0.1)',
          border: '1px solid #0284c7',
          borderRadius: '8px',
          fontSize: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>✓ {activeResult.target}: </span>
            <span style={{ color: '#cbd5e1' }}>{activeResult.message}</span>
          </div>
          <button
            onClick={() => { setActiveResult(null); setQuery(''); }}
            style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '13px' }}
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}