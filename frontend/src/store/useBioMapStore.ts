import { create } from 'zustand';

export interface Track {
  track_id: number;
  positions: [number, number][];
  frames: number[];
  areas: number[];
  mean_confidence?: number;
  length: number;
}

export interface LineageNode {
  track_id: number;
  start_frame: number;
  end_frame: number;
  parent_id?: number | null;
  [key: string]: unknown;
}

export interface LineageEdge {
  parent_id: number;
  child_id: number;
  [key: string]: unknown;
}

export interface DivisionEvent {
  parent_id: number;
  child_ids?: number[];
  frame?: number;
  confidence?: number;
  [key: string]: unknown;
}

export interface Lineage {
  nodes: LineageNode[];
  edges: LineageEdge[];
  division_events: DivisionEvent[];
}

interface BioMapState {
  activeDataset: string;
  sequence: string;

  availableDatasets: string[];
  metadata: any;

  currentFrame: number;
  totalFrames: number;
  isPlaying: boolean;
  isAnalyzing: boolean;
  analysisReady: boolean;
  isFrameLoading: boolean;

  tracks: Record<number, Track>;
  lineage: Lineage | null;

  selectedCellId: number | null;

  processingMode: 'basic' | 'advanced';

  setDataset: (dataset: string) => void;
  setDatasets: (datasets: string[]) => void;
  setMetadata: (metadata: any) => void;
  setFrame: (frame: number) => void;
  togglePlay: () => void;
  setAnalyzing: (value: boolean) => void;
  setAnalysisReady: (value:boolean) => void;
  setFrameLoading: (value:boolean) => void;
  setSelectedCell: (id: number | null) => void;
  setProcessingMode: (mode: 'basic' | 'advanced') => void;

  setPipelineData: (
    tracks: Record<number, Track>,
    lineage: Lineage
  ) => void;

  resetAnalysis: () => void;
}

export const useBioMapStore = create<BioMapState>((set) => ({
  activeDataset: '',
  sequence: '01',

  availableDatasets: [],
  metadata: null,

  currentFrame: 0,
  totalFrames: 0,
  isPlaying: false,
  isAnalyzing: false,
  analysisReady: false,
  isFrameLoading: false,

  tracks: {},
  lineage: null,

  selectedCellId: null,

  processingMode: 'basic',

  setDataset: (dataset) =>
    set((state) => ({
      activeDataset: dataset,
      currentFrame: 0,
      tracks: {},
      lineage: null,
      selectedCellId: null,
      totalFrames:
        state.metadata?.sequences?.[state.sequence]?.frameCount ?? 0,
      isPlaying: false,
      analysisReady: false,
      isFrameLoading: false,
    })),

  setDatasets: (datasets) =>
    set({
      availableDatasets: datasets,
    }),

  setMetadata: (metadata) =>
    set((state) => ({
      metadata,
      totalFrames:
        metadata?.sequences?.[state.sequence]?.frameCount ?? 0,
    })),
  
  setFrame: (frame) =>
    set((state) => ({
      currentFrame: Math.max(
        0,
        Math.min(frame, Math.max(0, state.totalFrames - 1))
      ),
    })),

  togglePlay: () =>
    set((state) => ({
      isPlaying: !state.isPlaying,
    })),

  setAnalyzing: (value) =>
    set({
      isAnalyzing: value,
      isPlaying: value ? false : false,
    } as Partial<BioMapState>),

  setAnalysisReady: (value) =>
    set({
      analysisReady: value,
    }),

  setFrameLoading: (value) =>
    set({
      isFrameLoading: value,
    }),

  setSelectedCell: (id) =>
    set({
      selectedCellId: id,
    }),

  setProcessingMode: (mode) =>
    set({
      processingMode: mode,
    }),

  setPipelineData: (tracks, lineage) =>
    set({
      tracks,
      lineage,
      currentFrame: 0,
      isPlaying: false,
      analysisReady: true,
    }),

  resetAnalysis: () =>
    set({
      tracks: {},
      lineage: null,
      selectedCellId: null,
      currentFrame: 0,
      totalFrames: 0,
      analysisReady: false,
      isPlaying: false,
      isFrameLoading: false,
    }),
}));