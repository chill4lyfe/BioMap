import React from 'react';
import { Activity, GitBranch, MapPin, Ruler, Timer } from 'lucide-react';
import { useBioMapStore } from '../../store/useBioMapStore';

export const CellCard: React.FC = () => {
  const { selectedCellId, tracks, lineage } = useBioMapStore();

  if (selectedCellId === null || !tracks[selectedCellId]) {
    return (
      <section className="panel p-5">
        <div className="section-kicker">Cell Inspector</div>

        <div className="mt-8 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full border border-slate-800 bg-slate-950">
            <Activity size={18} className="text-slate-600" />
          </div>

          <p className="text-sm text-slate-500">
            Select a tracked cell to inspect its trajectory.
          </p>
        </div>
      </section>
    );
  }

  const track = tracks[selectedCellId];

  const frameIndex = track.frames.indexOf(
    Math.max(...track.frames)
  );

  const lastPosition =
    track.positions[frameIndex >= 0 ? frameIndex : track.positions.length - 1];

  const lastArea =
    track.areas.length > 0
      ? track.areas[track.areas.length - 1]
      : null;

  const parent = lineage?.edges.find(
    (edge) => edge.child_id === selectedCellId
  );

  const children =
    lineage?.edges.filter(
      (edge) => edge.parent_id === selectedCellId
    ) ?? [];

  return (
    <section className="panel overflow-hidden">
      <div className="border-b border-slate-800/80 bg-gradient-to-r from-blue-950/40 to-transparent p-5">
        <div className="flex items-start justify-between">
          <div>
            <div className="section-kicker">Cell Inspector</div>

            <div className="mt-2 flex items-center gap-3">
              <span className="font-display text-2xl text-white">
                #{track.track_id}
              </span>

              <span className="status-pill">
                TRACKED
              </span>
            </div>
          </div>

          <div className="h-10 w-10 rounded-full border border-blue-500/20 bg-blue-500/10 flex items-center justify-center">
            <Activity size={17} className="text-blue-400" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-px bg-slate-800/60">
        <Metric
          icon={<Timer size={13} />}
          label="Frames"
          value={`${track.length}`}
        />

        <Metric
          icon={<Ruler size={13} />}
          label="Area"
          value={lastArea !== null ? `${lastArea.toFixed(1)} px²` : '—'}
        />

        <Metric
          icon={<MapPin size={13} />}
          label="Position"
          value={
            lastPosition
              ? `${lastPosition[0].toFixed(1)}, ${lastPosition[1].toFixed(1)}`
              : '—'
          }
        />

        <Metric
          icon={<Activity size={13} />}
          label="Confidence"
          value={
            track.mean_confidence !== undefined
              ? `${(track.mean_confidence * 100).toFixed(1)}%`
              : 'N/A'
          }
        />
      </div>

      <div className="space-y-3 p-5">
        <Relationship
          icon={<GitBranch size={13} />}
          label="Parent"
          value={parent ? `Cell #${parent.parent_id}` : 'Founder'}
        />

        <Relationship
          icon={<GitBranch size={13} />}
          label="Daughters"
          value={
            children.length > 0
              ? children.map((child) => `#${child.child_id}`).join(', ')
              : 'None detected'
          }
        />

        <Relationship
          icon={<Timer size={13} />}
          label="Temporal span"
          value={`Frame ${track.frames[0]} → ${track.frames[track.frames.length - 1]}`}
        />
      </div>
    </section>
  );
};

const Metric = ({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) => (
  <div className="bg-[#080d18] p-4">
    <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-slate-500">
      {icon}
      {label}
    </div>
    <div className="mt-1 font-mono text-sm text-slate-200">
      {value}
    </div>
  </div>
);

const Relationship = ({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) => (
  <div className="flex items-center justify-between border-b border-slate-800/70 pb-3 last:border-0 last:pb-0">
    <div className="flex items-center gap-2 text-xs text-slate-500">
      {icon}
      {label}
    </div>
    <span className="font-mono text-xs text-slate-300">{value}</span>
  </div>
);