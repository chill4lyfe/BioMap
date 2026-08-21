import React, { useEffect, useMemo, useRef } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Pause,
  Play,
  SkipBack,
  SkipForward,
} from 'lucide-react';
import { useBioMapStore } from '../../store/useBioMapStore';

export const Timeline: React.FC = () => {
  const {
    currentFrame,
    totalFrames,
    isPlaying,
    isAnalyzing,
    tracks,
    lineage,
    setFrame,
    togglePlay,
  } = useBioMapStore();

  const frameRef = useRef(currentFrame);

  useEffect(() => {
    frameRef.current = currentFrame;
  }, [currentFrame]);

  useEffect(() => {
    if (!isPlaying || isAnalyzing || totalFrames <= 1) return;

    const timer = window.setInterval(() => {
      if (frameRef.current >= totalFrames - 1) {
        togglePlay();
        return;
      }

      setFrame(frameRef.current + 1);
    }, 250);

    return () => window.clearInterval(timer);
  }, [isPlaying, isAnalyzing, totalFrames, setFrame, togglePlay]);

  const maxFrame = Math.max(0, totalFrames - 1);

  const progress =
    maxFrame > 0 ? (currentFrame / maxFrame) * 100 : 0;

  const frameActivity = useMemo(() => {
    const activity = new Set<number>();

    Object.values(tracks).forEach((track) => {
      track.frames.forEach((frame) => activity.add(frame));
    });

    return activity;
  }, [tracks]);

  const divisionFrames = useMemo(() => {
    return new Set(
      (lineage?.division_events ?? [])
        .map((event) => event.frame)
        .filter((frame): frame is number => typeof frame === 'number')
    );
  }, [lineage]);

  const jump = (amount: number) => {
    setFrame(
      Math.max(0, Math.min(maxFrame, currentFrame + amount))
    );
  };

  const isDisabled =
    totalFrames <= 1 ||
    isAnalyzing;

  return (
    <div className="w-full">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <div className="section-kicker">Temporal Analysis</div>

          <div className="mt-1 font-mono text-sm text-white">
            FRAME {String(currentFrame).padStart(3, '0')}
            <span className="text-slate-600">
              {' '} / {String(maxFrame).padStart(3, '0')}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <ControlButton
            onClick={() => setFrame(0)}
            disabled={isDisabled}
            icon={<SkipBack size={15} />}
          />

          <ControlButton
            onClick={() => jump(-1)}
            disabled={isDisabled}
            icon={<ChevronLeft size={15} />}
          />

          <button
            onClick={togglePlay}
            disabled={isDisabled || totalFrames <= 1}
            className="mx-1 flex h-9 w-9 items-center justify-center rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-300 transition hover:bg-blue-500/20 disabled:opacity-30"
          >
            {isPlaying ? (
              <Pause size={15} fill="currentColor" />
            ) : (
              <Play size={15} fill="currentColor" />
            )}
          </button>

          <ControlButton
            onClick={() => jump(1)}
            disabled={isDisabled}
            icon={<ChevronRight size={15} />}
          />

          <ControlButton
            onClick={() => setFrame(maxFrame)}
            disabled={isDisabled}
            icon={<SkipForward size={15} />}
          />
        </div>
      </div>

      <div className="relative pt-3">
        <div className="absolute left-0 right-0 top-0 h-2">
          {divisionFrames.size > 0 &&
            [...divisionFrames].map((frame) => {
              if (maxFrame === 0) return null;

              return (
                <button
                  key={frame}
                  title={`Mitosis Detected — frame ${frame}`}
                  onClick={() => setFrame(frame)}
                  className="absolute -top-1 h-4 w-[3px] -translate-x-1/2 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,.8)]"
                  style={{
                    left: `${(frame / maxFrame) * 100}%`,
                  }}
                />
              );
            })}
        </div>

        <input
          type="range"
          min={0}
          max={maxFrame}
          value={currentFrame}
          disabled={isDisabled}
          onChange={(event) =>
            setFrame(Number(event.target.value))
          }
          className="timeline-range"
          style={{
            background: `linear-gradient(
              to right,
              #3b82f6 ${progress}%,
              #172033 ${progress}%
            )`,
          }}
        />

        <div className="mt-2 flex justify-between text-[9px] font-mono uppercase tracking-widest text-slate-600">
          <span>START</span>
          <span>
            {frameActivity.size} active frame observations
          </span>
          <span>END</span>
        </div>
      </div>
    </div>
  );
};

const ControlButton = ({
  onClick,
  disabled,
  icon,
}: {
  onClick: () => void;
  disabled: boolean;
  icon: React.ReactNode;
}) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-800 text-slate-400 transition hover:border-slate-600 hover:text-white disabled:opacity-30"
  >
    {icon}
  </button>
);