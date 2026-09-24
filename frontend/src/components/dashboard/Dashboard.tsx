import { useMemo, useState } from 'react';
import type { LucideIcon } from 'lucide-react';
import {
  Activity,
  ArrowRight,
  Bell,
  BookOpen,
  Clock3,
  Cpu,
  Database,
  FileBarChart,
  FlaskConical,
  FolderKanban,
  LineChart,
  LogOut,
  Microscope,
  Network,
  PlayCircle,
  Search,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  UploadCloud,
  UserRound,
} from 'lucide-react';

type DashboardProps = {
  datasets: string[];
  selectedDataset: string;
  trackCount: number;
  divisionCount: number;
  isAnalyzing: boolean;
  onOpenDataset: (dataset: string) => void;
  onOpenWorkspace: () => void;
  onUploadDataset: () => void;
  onLogout: () => void;
};

const fallbackDatasets = ['Fluo-N3DH-CHO', 'Fluo-C3DL-MDA231'];

const proliferationTrends = {
  'Fluo-N3DH-CHO': [
    { time: 0, cells: 9 },
    { time: 10, cells: 10 },
    { time: 20, cells: 11 },
    { time: 30, cells: 12 },
    { time: 40, cells: 13 },
    { time: 50, cells: 14 },
    { time: 60, cells: 14 },
    { time: 70, cells: 15 },
    { time: 80, cells: 16 },
    { time: 91, cells: 16 },
  ],
  'Fluo-C3DL-MDA231': [
    { time: 0, cells: 20 },
    { time: 1, cells: 21 },
    { time: 2, cells: 23 },
    { time: 3, cells: 24 },
    { time: 4, cells: 26 },
    { time: 5, cells: 27 },
    { time: 6, cells: 29 },
    { time: 7, cells: 30 },
    { time: 8, cells: 32 },
    { time: 9, cells: 33 },
    { time: 10, cells: 34 },
    { time: 11, cells: 35 },
  ],
};

const recentAnalyses = [
  {
    title: 'CHO Cell Lineage - Run 04',
    dataset: 'Fluo-N3DH-CHO',
    method: 'Cellpose + centroid tracking',
    status: 'Complete',
    time: 'Today',
  },
  {
    title: 'MDA231 Migration - Run 03',
    dataset: 'Fluo-C3DL-MDA231',
    method: 'Classical watershed',
    status: 'Review',
    time: 'Yesterday',
  },
  {
    title: 'CHO Baseline - Run 02',
    dataset: 'Fluo-N3DH-CHO',
    method: 'Basic segmentation',
    status: 'Complete',
    time: 'Aug 20',
  },
];

const activityItems = [
  'Cell proliferation trend generated from mock dataset profile.',
  'Dataset metadata loaded from the local BioMap backend.',
  'Tracking and lineage statistics are ready for review.',
  'Saved project notes are prepared for the next auth phase.',
];

const savedProjects = [
  {
    name: 'Cell division kinetics',
    detail: 'CHO lineage comparison across baseline and treated samples',
    meta: '6 analyses',
  },
  {
    name: 'Migration phenotype screen',
    detail: 'MDA231 trajectory and displacement review',
    meta: '4 analyses',
  },
  {
    name: 'Prototype validation',
    detail: 'SIH demo datasets and pipeline checkpoints',
    meta: '9 notes',
  },
];

const sidebarItems: { label: string; icon: LucideIcon }[] = [
  { label: 'Overview', icon: LineChart },
  { label: 'Datasets', icon: Database },
  { label: 'Analyses', icon: FileBarChart },
  { label: 'Engines', icon: Cpu },
  { label: 'Projects', icon: FolderKanban },
];

export function Dashboard({
  datasets,
  selectedDataset,
  trackCount,
  divisionCount,
  isAnalyzing,
  onOpenDataset,
  onOpenWorkspace,
  onUploadDataset,
  onLogout,
}: DashboardProps) {
  const visibleDatasets = datasets.length > 0 ? datasets : fallbackDatasets;
  const cellCount = Math.max(trackCount * 3, divisionCount * 2, 2390);

  const [trendDataset, setTrendDataset] =
    useState<keyof typeof proliferationTrends>('Fluo-N3DH-CHO');

  const trendData = proliferationTrends[trendDataset];

  const trendPath = useMemo(() => {
    const width = 520;
    const height = 210;
    const padding = 28;

    const maxTime = Math.max(...trendData.map((point) => point.time));
    const minCells = Math.min(...trendData.map((point) => point.cells));
    const maxCells = Math.max(...trendData.map((point) => point.cells));

    return trendData
      .map((point, index) => {
        const x =
          padding + (point.time / maxTime) * (width - padding * 2);
        const y =
          height -
          padding -
          ((point.cells - minCells) /
            Math.max(1, maxCells - minCells)) *
            (height - padding * 2);

        return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');
  }, [trendData]);

  return (
    <div className="h-screen overflow-y-auto bg-[#02050b] text-slate-200">
      <div className="flex min-h-screen">
        <aside className="hidden w-[300px] shrink-0 border-r border-slate-800/80 bg-[#070b14] px-6 py-5 lg:flex lg:flex-col">
          <div className="mb-9 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10">
              <Microscope size={20} className="text-blue-400" />
            </div>
            <div>
              <h1 className="font-display text-xl tracking-wider text-white">
                BIOMAP
              </h1>
              <p className="text-[9px] uppercase tracking-[0.2em] text-slate-600">
                Research Dashboard
              </p>
            </div>
          </div>

          <nav className="space-y-2">
            {sidebarItems.map(({ label, icon: Icon }) => (
              <button
                key={label}
                type="button"
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm text-slate-400 transition hover:bg-slate-900 hover:text-blue-300"
              >
                <Icon size={16} className="text-blue-400" />
                {label}
              </button>
            ))}
          </nav>

          <div className="mt-6 border-t border-slate-800/80 pt-4">
            <button
              type="button"
              onClick={onLogout}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm text-slate-400 transition hover:bg-red-500/10 hover:text-red-300"
            >
              <LogOut size={16} />
              Logout
            </button>
          </div>

          <div className="panel mt-auto p-4">
            <div className="mb-3 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-500/10">
                <UserRound size={18} className="text-blue-300" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">
                  Dr. Victor Von Doom
                </p>
                <p className="text-xs text-slate-500">
                  Cell imaging researcher
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-emerald-400">
              <ShieldCheck size={14} />
              Local profile mode
            </div>
          </div>
        </aside>

        <main className="flex-1 px-5 py-5 lg:px-8">
          <header className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <div className="section-kicker mb-2">
                Scientist workspace
              </div>
              <h2 className="font-display text-3xl tracking-wide text-white md:text-4xl">
                Research command center
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
                Review datasets, analysis history, lineage outcomes, and project
                activity before opening the existing BioMap analysis workspace.
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <label className="flex items-center gap-2 rounded-lg border border-slate-800 bg-[#080d18] px-3 py-2 text-sm text-slate-400">
                <Search size={15} />
                <input
                  type="search"
                  placeholder="Search research data"
                  className="w-full bg-transparent outline-none placeholder:text-slate-600"
                />
              </label>
              <button
                type="button"
                className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-800 bg-[#080d18] text-slate-400 transition hover:text-blue-300"
                aria-label="Notifications"
              >
                <Bell size={16} />
              </button>
            </div>
          </header>

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              icon={Database}
              label="Datasets"
              value={String(visibleDatasets.length)}
              detail="Ready in local backend"
            />
            <MetricCard
              icon={Microscope}
              label="Cells analyzed"
              value={String(cellCount)}
              detail="From recent experiments"
            />
            <MetricCard
              icon={Activity}
              label="Frames Processed"
              value="713"
              detail="Across recent analyses"
            />
            <MetricCard
              icon={Network}
              label="Cumulative Confidence"
              value="87.3%"
              detail="Overall analysis confidence"
            />
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
            <div className="space-y-6">
              <div className="panel p-5">
                <div className="mb-4 flex items-center justify-between gap-4">
                  <div>
                    <div className="section-kicker mb-2">Open dataset</div>
                    <h3 className="font-display text-xl tracking-wide text-white">
                      Recent datasets
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={onUploadDataset}
                    className="flex items-center gap-2 rounded-lg border border-dashed border-slate-700 px-3 py-2 text-xs text-slate-400 transition hover:border-blue-500/40 hover:text-blue-300"
                  >
                    <UploadCloud size={15} />
                    Upload CTC ZIP
                  </button>
                </div>

                <div className="grid gap-3 md:grid-cols-2">
                  {visibleDatasets.map((dataset) => (
                    <button
                      key={dataset}
                      type="button"
                      onClick={() => onOpenDataset(dataset)}
                      className="group rounded-lg border border-slate-800 bg-[#050914] p-4 text-left transition hover:border-blue-500/40 hover:bg-blue-500/10"
                    >
                      <div className="mb-4 flex items-start justify-between gap-3">
                        <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-blue-500/10">
                          <FlaskConical size={20} className="text-blue-300" />
                        </div>
                        <span className="status-pill">
                          {selectedDataset === dataset ? 'Selected' : 'Ready'}
                        </span>
                      </div>
                      <h4 className="font-semibold text-white">{dataset}</h4>
                      <p className="mt-2 text-sm leading-6 text-slate-500">
                        Open this dataset in the existing analysis UI.
                      </p>
                      <div className="mt-4 flex items-center gap-2 text-sm font-medium text-blue-300">
                        Open analysis
                        <ArrowRight
                          size={15}
                          className="transition group-hover:translate-x-1"
                        />
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="panel p-5">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <div className="section-kicker mb-2">
                      Previous analyses
                    </div>
                    <h3 className="font-display text-xl tracking-wide text-white">
                      Analysis history
                    </h3>
                  </div>
                  <FileBarChart size={18} className="text-blue-400" />
                </div>

                <div className="space-y-3">
                  {recentAnalyses.map((analysis) => (
                    <article
                      key={analysis.title}
                      className="rounded-lg border border-slate-800 bg-[#050914] p-4"
                    >
                      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                        <div>
                          <h4 className="font-semibold text-white">
                            {analysis.title}
                          </h4>
                          <p className="mt-1 text-sm text-slate-500">
                            {analysis.dataset} - {analysis.method}
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="status-pill">
                            {analysis.status}
                          </span>
                          <span className="flex items-center gap-1 text-xs text-slate-600">
                            <Clock3 size={13} />
                            {analysis.time}
                          </span>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="panel p-5">
                <div className="mb-5 flex items-start justify-between gap-4">
                  <div>
                    <div className="section-kicker mb-2">
                      Cell proliferation trend
                    </div>
                    <h3 className="font-display text-xl tracking-wide text-white">
                      Cells over time
                    </h3>
                    <p className="mt-2 text-sm leading-6 text-slate-500">
                      Mock cell-count trend matched to the selected BioMap
                      dataset.
                    </p>
                  </div>

                  <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-[#050914] px-3 py-2">
                    <TrendingUp size={15} className="text-blue-400" />
                    <select
                      value={trendDataset}
                      onChange={(event) =>
                        setTrendDataset(
                          event.target
                            .value as keyof typeof proliferationTrends
                        )
                      }
                      className="bg-transparent text-xs text-slate-300 outline-none"
                    >
                      <option value="Fluo-N3DH-CHO">CHO</option>
                      <option value="Fluo-C3DL-MDA231">MDA231</option>
                    </select>
                  </div>
                </div>

                <div className="rounded-lg border border-slate-800 bg-[#050914] p-4">
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.18em] text-slate-600">
                        Dataset
                      </p>
                      <p className="mt-1 text-sm font-semibold text-blue-300">
                        {trendDataset}
                      </p>
                    </div>

                    <div className="text-right">
                      <p className="text-xs uppercase tracking-[0.18em] text-slate-600">
                        Latest count
                      </p>
                      <p className="mt-1 font-display text-2xl text-white">
                        {trendData[trendData.length - 1].cells}
                      </p>
                    </div>
                  </div>

                  <svg
                    viewBox="0 0 520 210"
                    className="h-[260px] w-full overflow-visible"
                    role="img"
                    aria-label="Cell proliferation trend graph"
                  >
                    {[0, 1, 2, 3].map((line) => (
                      <line
                        key={line}
                        x1="28"
                        x2="492"
                        y1={32 + line * 48}
                        y2={32 + line * 48}
                        stroke="#1e293b"
                        strokeWidth="1"
                      />
                    ))}

                    <path
                      d={trendPath}
                      fill="none"
                      stroke="#3b82f6"
                      strokeWidth="4"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />

                    {trendData.map((point) => {
                      const width = 520;
                      const height = 210;
                      const padding = 28;
                      const maxTime = Math.max(
                        ...trendData.map((item) => item.time)
                      );
                      const minCells = Math.min(
                        ...trendData.map((item) => item.cells)
                      );
                      const maxCells = Math.max(
                        ...trendData.map((item) => item.cells)
                      );

                      const x =
                        padding +
                        (point.time / maxTime) *
                          (width - padding * 2);
                      const y =
                        height -
                        padding -
                        ((point.cells - minCells) /
                          Math.max(1, maxCells - minCells)) *
                          (height - padding * 2);

                      return (
                        <g key={`${point.time}-${point.cells}`}>
                          <circle
                            cx={x}
                            cy={y}
                            r="5"
                            fill="#02050b"
                            stroke="#60a5fa"
                            strokeWidth="3"
                          />
                          <text
                            x={x}
                            y={y - 12}
                            textAnchor="middle"
                            className="fill-slate-400 text-[10px]"
                          >
                            {point.cells}
                          </text>
                        </g>
                      );
                    })}

                    <text
                      x="28"
                      y="205"
                      className="fill-slate-600 text-[10px]"
                    >
                      Time
                    </text>
                    <text
                      x="455"
                      y="205"
                      className="fill-slate-600 text-[10px]"
                    >
                      {trendDataset === 'Fluo-N3DH-CHO'
                        ? '91 frames'
                        : '11 frames'}
                    </text>
                    <text
                      x="8"
                      y="18"
                      className="fill-slate-600 text-[10px]"
                    >
                      Cells
                    </text>
                  </svg>

                  <div className="mt-3 grid grid-cols-3 gap-3">
                    <TrendStat label="Start" value={`${trendData[0].cells} cells`} />
                    <TrendStat
                      label="End"
                      value={`${trendData[trendData.length - 1].cells} cells`}
                    />
                    <TrendStat
                      label="Duration"
                      value={`${
                        trendDataset === 'Fluo-N3DH-CHO' ? '91' : '11'
                      } frames`}
                    />
                  </div>
                </div>
              </div>

              <div className="panel p-5">
                <div className="mb-4 flex items-center gap-2">
                  <Sparkles size={18} className="text-blue-400" />
                  <h3 className="font-display text-xl tracking-wide text-white">
                    Recent activity
                  </h3>
                </div>
                <div className="space-y-3">
                  {activityItems.map((item) => (
                    <div key={item} className="flex gap-3 text-sm">
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-400" />
                      <span className="leading-6 text-slate-400">{item}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="panel p-5">
                <div className="mb-4 flex items-center gap-2">
                  <BookOpen size={18} className="text-blue-400" />
                  <h3 className="font-display text-xl tracking-wide text-white">
                    Saved projects
                  </h3>
                </div>
                <div className="space-y-3">
                  {savedProjects.map((project) => (
                    <article
                      key={project.name}
                      className="rounded-lg border border-slate-800 bg-[#050914] p-3"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <h4 className="text-sm font-semibold text-white">
                          {project.name}
                        </h4>
                        <span className="text-xs text-slate-600">
                          {project.meta}
                        </span>
                      </div>
                      <p className="mt-1 text-xs leading-5 text-slate-500">
                        {project.detail}
                      </p>
                    </article>
                  ))}
                </div>
              </div>

              <button
                type="button"
                onClick={onOpenWorkspace}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-3 text-xs font-semibold uppercase tracking-wider text-white shadow-[0_0_25px_rgba(37,99,235,.18)] transition hover:bg-blue-500"
              >
                <PlayCircle size={15} fill="currentColor" />
                Open workspace
              </button>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-blue-500/10">
          <Icon size={20} className="text-blue-300" />
        </div>
        <span className="status-pill">Live</span>
      </div>
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 font-display text-3xl text-white">{value}</p>
      <p className="mt-2 text-xs text-slate-600">{detail}</p>
    </div>
  );
}

function TrendStat({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-[#080d18] p-3">
      <p className="text-[10px] uppercase tracking-[0.18em] text-slate-600">
        {label}
      </p>
      <p className="mt-1 text-sm text-slate-200">{value}</p>
    </div>
  );
}