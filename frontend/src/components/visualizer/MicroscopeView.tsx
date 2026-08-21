import React, { useEffect, useMemo } from 'react';
import { Crosshair, Layers3 } from 'lucide-react';
import { useBioMapStore } from '../../store/useBioMapStore';
import { Spinner } from '../ui/Spinner';

const API_BASE = 'http://localhost:8000';

export const MicroscopeView: React.FC = () => {
  const {
    currentFrame,
    totalFrames,
    tracks,
    selectedCellId,
    activeDataset,
    isAnalyzing,
    setSelectedCell,
    setFrameLoading,
  } = useBioMapStore();

  const imageUrl =
    activeDataset
      ? `${API_BASE}/api/datasets/${encodeURIComponent(
          activeDataset
        )}/sequence/01/frame/${currentFrame}/image`
      : '';
    
  useEffect(() => {
    if (activeDataset && totalFrames > 0) {
      setFrameLoading(true);
    }
  }, [
    currentFrame,
    activeDataset,
    totalFrames,
    setFrameLoading,
  ]);

  const activeCells = useMemo(() => {
    return Object.values(tracks)
      .map((track) => {
        const index = track.frames.indexOf(currentFrame);

        if (index === -1) return null;

        return {
          track,
          index,
          position: track.positions[index],
          history: track.positions.slice(0, index + 1),
        };
      })
      .filter(Boolean) as {
      track: any;
      index: number;
      position: [number, number];
      history: [number, number][];
    }[];
  }, [tracks, currentFrame]);

  return (
    <div className="relative h-full w-full overflow-hidden bg-[#02050b]">
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={`Microscopy frame ${currentFrame}`}
          className="absolute inset-0 h-full w-full object-contain"
          onLoad={() => setFrameLoading(false)}
          onError={() => setFrameLoading(false)}
        />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center text-slate-600">
          No sequence loaded
        </div>
      )}

      <svg
        className="absolute inset-0 h-full w-full"
        viewBox="0 0 512 512"
        preserveAspectRatio="xMidYMid meet"
      >
        {activeCells.map(({ track, history, position }) => {
          const selected = selectedCellId === track.track_id;

          return (
            <g key={track.track_id}>
              {history.length > 1 && (
                <polyline
                  points={history
                    .map((point) => point.join(','))
                    .join(' ')}
                  fill="none"
                  stroke={
                    selected
                      ? '#f87171'
                      : 'rgba(248,113,113,.30)'
                  }
                  strokeWidth={selected ? 2.5 : 1}
                />
              )}

              <circle
                cx={position[0]}
                cy={position[1]}
                r={selected ? 9 : 5}
                fill={
                  selected
                    ? 'rgba(228, 83, 78, 0.38)'
                    : 'rgba(239,68,68,.12)'
                }
                stroke={
                  selected
                    ? '#f87171'
                    : 'rgba(248,113,113,.75)'
                }
                strokeWidth={selected ? 2 : 1}
                className="cursor-pointer"
                onClick={() => setSelectedCell(track.track_id)}
              />

              {selected && (
                <text
                  x={position[0] + 11}
                  y={position[1] - 10}
                  fill="#bfdbfe"
                  fontSize="10"
                  fontFamily="monospace"
                >
                  #{track.track_id}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      <div className="absolute left-5 top-5 flex items-center gap-3 rounded-lg border border-slate-800/80 bg-[#050914]/80 px-4 py-3 backdrop-blur-md">
        <Crosshair size={15} className="text-blue-400" />

        <div>
          <div className="text-[9px] uppercase tracking-[0.2em] text-slate-500">
            Spatial Field
          </div>
          <div className="font-mono text-xs text-slate-200">
            FRAME {currentFrame}
          </div>
        </div>
      </div>

      <div className="absolute bottom-5 left-5 flex items-center gap-2 rounded-md border border-slate-800/80 bg-black/60 px-3 py-2 font-mono text-[10px] text-slate-400 backdrop-blur-md">
        <Layers3 size={13} />
        {activeCells.length} CELLS IN FRAME
      </div>

      {isAnalyzing && (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-black/75 backdrop-blur-sm">
          <Spinner />
        </div>
      )}

      {!activeDataset && !isAnalyzing && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="font-display text-lg text-slate-500">
              NO DATASET LOADED
            </div>
            <div className="mt-2 text-xs text-slate-700">
              Select a dataset or upload one to populate the spatial field.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};