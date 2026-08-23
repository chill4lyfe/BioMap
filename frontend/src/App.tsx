import React, { useEffect, useRef, useState } from 'react';
import {
  Database,
  Dna,
  Layers3,
  Play,
  RefreshCw,
  Sparkles,
  Upload,
} from 'lucide-react';

import { useBioMapStore } from './store/useBioMapStore';
import { Dropdown } from './components/ui/Dropdown';
import { CellCard } from './components/ui/CellCard';
import { Timeline } from './components/ui/Timeline';
import { MicroscopeView } from './components/visualizer/MicroscopeView';
import { LineageGraph } from './components/visualizer/LineageGraph';
import QCReportModal from './components/QCReportModal';
import QueryOverlayModal from './components/QueryOverlayModal';


const API_BASE = 'http://localhost:8000';

function App() {
  const {
    activeDataset,
    availableDatasets,
    currentFrame,
    totalFrames,
    tracks,
    lineage,
    isAnalyzing,
    processingMode,
    setDataset,
    setDatasets,
    setMetadata,
    setAnalyzing,
    setPipelineData,
    setProcessingMode,
  } = useBioMapStore();

  const [metadataLoading, setMetadataLoading] = useState(false);
  const [error, setError] = useState('');
  const [isQCOpen, setIsQCOpen] = useState(false);
  const [isQueryOpen, setIsQueryOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadDatasets();
  }, []);

  useEffect(() => {
    if (!activeDataset) return;

    loadMetadata(activeDataset);
  }, [activeDataset]);

  async function loadDatasets() {
    try {
      const response = await fetch(`${API_BASE}/api/datasets`);

      if (!response.ok) throw new Error('Failed to load datasets.');

      const data = await response.json();

      setDatasets(data.datasets ?? []);

      if (!activeDataset && data.datasets?.length) {
        setDataset(data.datasets[0]);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not connect to BioMap backend.'
      );
    }
  }

  async function loadMetadata(datasetName: string) {
    setMetadataLoading(true);

    try {
      const response = await fetch(
        `${API_BASE}/api/datasets/${encodeURIComponent(
          datasetName
        )}/metadata`
      );

      if (!response.ok) throw new Error('Metadata unavailable.');

      const data = await response.json();

      setMetadata(data);

      const sequence = data.sequences?.['01'];

      if (sequence?.frameCount) {
        useBioMapStore.setState({
          totalFrames: sequence.frameCount,
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setMetadataLoading(false);
    }
  }

  async function runAnalysis() {
    if (!activeDataset) return;

    setError('');
    setAnalyzing(true);

    try {
      const response = await fetch(
        `${API_BASE}/api/datasets/${encodeURIComponent(
          activeDataset
        )}/sequence/01/analyze`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            mode: processingMode,
            start_frame: 0,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || 'Pipeline analysis failed.'
        );
      }

      setPipelineData(
        data.tracking?.tracks ?? {},
        data.lineage ?? {
          nodes: [],
          edges: [],
          division_events: [],
        }
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Pipeline failed.'
      );
    } finally {
      setAnalyzing(false);
    }
  }

  async function uploadDataset(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const file = event.target.files?.[0];

    if (!file) return;

    setError('');
    setAnalyzing(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(
        `${API_BASE}/api/datasets/upload`,
        {
          method: 'POST',
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed.');
      }

      await loadDatasets();
      setDataset(data.name);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Dataset upload failed.'
      );
    } finally {
      setAnalyzing(false);

      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }

  const trackCount = Object.keys(tracks).length;
  const divisionCount = lineage?.division_events?.length ?? 0;

  const averageConfidence =
    trackCount > 0
      ? Object.values(tracks).reduce(
          (sum, track) =>
            sum + (track.mean_confidence ?? 0),
          0
        ) / trackCount
      : null;

  return (
    <div className="flex h-screen min-h-0 overflow-hidden bg-[#02050b] text-slate-200">
      <input
        ref={fileInputRef}
        type="file"
        accept=".zip"
        onChange={uploadDataset}
        className="hidden"
      />

      {/* SIDEBAR */}
      <aside className="flex w-[330px] shrink-0 flex-col border-r border-slate-800/80 bg-[#070b14]">
        <header className="border-b border-slate-800/80 px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10">
              <Dna size={19} className="text-blue-400" />
            </div>

            <div>
              <h1 className="font-display text-xl tracking-wider text-white">
                BIOMAP
              </h1>
              <p className="text-[9px] uppercase tracking-[0.2em] text-slate-600">
                Cellular Intelligence
              </p>
            </div>
          </div>
        </header>

        <div className="flex-1 space-y-6 overflow-y-auto p-5">
          <section>
            <div className="section-kicker mb-3">
              Dataset Configuration
            </div>

            <Dropdown
              label="Dataset"
              options={availableDatasets}
              selected={activeDataset}
              onSelect={setDataset}
            />

            <button
              onClick={() => fileInputRef.current?.click()}
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-slate-700 py-3 text-xs text-slate-400 transition hover:border-blue-500/40 hover:text-blue-300"
            >
              <Upload size={14} />
              Upload CTC ZIP
            </button>
          </section>

          <section>
            <div className="section-kicker mb-3">
              Processing Engine
            </div>

            <div className="grid grid-cols-2 gap-2">
              <ModeButton
                active={processingMode === 'basic'}
                title="Basic"
                subtitle="Classical CV"
                onClick={() => setProcessingMode('basic')}
              />

              <ModeButton
                active={processingMode === 'advanced'}
                title="Advanced"
                subtitle="AI / Cellpose"
                onClick={() =>
                  setProcessingMode('advanced')
                }
              />
            </div>

            <button
              onClick={runAnalysis}
              disabled={!activeDataset || isAnalyzing}
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-3 text-xs font-semibold uppercase tracking-wider text-white shadow-[0_0_25px_rgba(37,99,235,.18)] transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw
                    size={14}
                    className="animate-spin"
                  />
                  Processing
                </>
              ) : (
                <>
                  <Play size={14} fill="currentColor" />
                  Initialize Pipeline
                </>
              )}
            </button>
            <button
             onClick={() => setIsQCOpen(true)}
             disabled={trackCount === 0}
             className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg border border-indigo-500/30 bg-indigo-950/40 px-3 py-2 text-xs font-semibold text-indigo-300 hover:bg-indigo-900/60 hover:text-white transition-colors"
           >
             <span>🛡️</span>
             <span>Run Anomaly Report</span>
            </button>
          </section>

          <CellCard />
        </div>

        <footer className="border-t border-slate-800/80 px-5 py-4">
          <div className="flex items-center justify-between text-[9px] font-mono uppercase tracking-widest text-slate-600">
            <span>Backend</span>
            <span className="text-emerald-500">
              ● Connected
            </span>
          </div>
        </footer>
      </aside>

      {/* WORKSPACE */}
      <main className="flex min-w-0 flex-1 flex-col">
        {/* HEADER */}
        <header className="flex h-[76px] shrink-0 items-center justify-between border-b border-slate-800/80 bg-[#070b14]/90 px-7 backdrop-blur">
          <div>
            <div className="flex items-center gap-2">
              <Database size={14} className="text-blue-400" />
              <span className="font-mono text-xs text-slate-300">
                {activeDataset || 'NO DATASET'}
              </span>
            </div>

            <div className="mt-1 text-[9px] uppercase tracking-[0.22em] text-slate-600">
              Sequence 01
              {metadataLoading && ' · Loading metadata'}
            </div>
          </div>

          <div className="flex items-center gap-8">
             <button
             onClick={() => setIsQueryOpen(true)}
             className="flex h-9 w-9 items-center justify-center rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-400 transition hover:bg-blue-500/20 hover:text-blue-300"
             title="Ask Researcher Query"
              >
            <Sparkles size={16} />
          </button>
            <Stat
              label="Tracks"
              value={String(trackCount)}
            />

            <Stat
              label="Mitosis"
              value={String(divisionCount)}
              highlight
            />

            <Stat
              label="Avg Tracking Confidence"
              value={
                averageConfidence !== null
                  ? `${(averageConfidence * 100).toFixed(1)}%`
                  : '—'
              }
            />

            <Stat
              label="Frame"
              value={`${currentFrame} / ${Math.max(
                0,
                totalFrames - 1
              )}`}
            />
          </div>
        </header>

        {error && (
          <div className="border-b border-red-900/40 bg-red-950/20 px-7 py-3 text-xs text-red-300">
            {error}
          </div>
        )}
      
        {/* VISUAL WORKSPACE */}
        <div className="grid min-h-0 flex-1 grid-cols-[minmax(0,1.35fr)_minmax(420px,0.9fr)]">
          <section className="relative min-h-0 border-r border-slate-800/80">
            <MicroscopeView />
          </section>

          <section className="relative min-h-0">
            <LineageGraph />
          </section>
        </div>

        {/* TIMELINE */}
        <section className="shrink-0 border-t border-slate-800/80 bg-[#070b14] px-7 py-5">
          <Timeline />
        </section>
      </main>
      {/* QC REPORT MODAL */}
      <QueryOverlayModal
        isOpen={isQueryOpen}
        onClose={() => setIsQueryOpen(false)}
        onExecuteQuery={(result: any) => console.log('Researcher Query:', result)}
      />
      <QCReportModal isOpen={isQCOpen} onClose={() => setIsQCOpen(false)}
      datasetName={activeDataset}
      processingMode={processingMode}
   />
        
    </div>
  );
}

const Stat = ({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) => (
  <div>
    <div className="text-[10px] uppercase tracking-[0.18em] text-slate-600">
      {label}
    </div>
    <div
      className={`mt-1 font-mono text-base font-semibold ${
        highlight ? 'text-blue-400' : 'text-slate-200'
      }`}
    >
      {value}
    </div>
  </div>
);

const ModeButton = ({
  active,
  title,
  subtitle,
  onClick,
}: {
  active: boolean;
  title: string;
  subtitle: string;
  onClick: () => void;
}) => (
  <button
    onClick={onClick}
    className={`rounded-lg border p-3 text-left transition ${
      active
        ? 'border-blue-500/50 bg-blue-500/10'
        : 'border-slate-800 bg-[#080d18] hover:border-slate-700'
    }`}
  >
    <div
      className={`text-xs font-semibold ${
        active ? 'text-blue-300' : 'text-slate-300'
      }`}
    >
      {title}
    </div>

    <div className="mt-1 text-[9px] uppercase tracking-wider text-slate-600">
      {subtitle}
    </div>
  </button>
);

export default App;