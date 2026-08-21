import React, { useEffect, useMemo, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from 'reactflow';
import * as dagre from 'dagre';
import 'reactflow/dist/style.css';
import { Maximize2, X } from 'lucide-react';
import { useBioMapStore } from '../../store/useBioMapStore';

const NODE_WIDTH = 120;
const NODE_HEIGHT = 58;

interface LineageNodeData {
  track_id: number;
  start_frame: number;
  end_frame: number;
}

interface LineageEdgeData {
  parent_id: number;
  child_id: number;
}

function layoutLineage(
  nodes: Node[],
  edges: Edge[],
): { nodes: Node[]; edges: Edge[] } {

  const graph = new dagre.graphlib.Graph();

  graph.setDefaultEdgeLabel(() => ({}));

  graph.setGraph({
    rankdir: 'TB',
    ranksep: 90,
    nodesep: 55,
    marginx: 30,
    marginy: 30,
  });

  nodes.forEach((node) => {
    graph.setNode(node.id, {
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
    });
  });

  edges.forEach((edge) => {
    graph.setEdge(edge.source, edge.target);
  });

  dagre.layout(graph);

  const positionedNodes = nodes.map((node) => {
    const position = graph.node(node.id);

    return {
      ...node,
      position: {
        x: position.x - NODE_WIDTH / 2,
        y: position.y - NODE_HEIGHT / 2,
      },
    };
  });

  return {
    nodes: positionedNodes,
    edges,
  };
}

export const LineageGraph: React.FC = () => {
  const {
    lineage,
    selectedCellId,
    setSelectedCell,
  } = useBioMapStore();

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const [fullscreen, setFullscreen] = useState(false);

  const lineageNodes = useMemo(
    () => lineage?.nodes ?? [],
    [lineage]
  );

  const lineageEdges = useMemo(
    () => lineage?.edges ?? [],
    [lineage]
  );

  useEffect(() => {
    if (!lineageNodes.length) {
      setNodes([]);
      setEdges([]);
      return;
    }

    const graphNodes: Node[] = lineageNodes.map(
      (node: LineageNodeData) => {

        const selected =
          selectedCellId === node.track_id;

        return {
          id: String(node.track_id),

          position: {
            x: 0,
            y: 0,
          },

          data: {
            label: (
              <div className="flex flex-col items-center justify-center h-full">
                <span className="font-mono font-bold text-xs">
                  Cell {node.track_id}
                </span>

                <span className="text-[10px] text-gray-400 mt-1">
                  F{node.start_frame}–F{node.end_frame}
                </span>
              </div>
            ),
          },

          style: {
            width: NODE_WIDTH,
            height: NODE_HEIGHT,

            background: selected
              ? 'rgba(239, 68, 68, 0.18)'
              : '#0b1220',

            color: selected
              ? '#fecaca'
              : '#e5e7eb',

            border: selected
              ? '2px solid #ef4444'
              : '1px solid #374151',

            borderRadius: '10px',

            boxShadow: selected
              ? '0 0 20px rgba(239,68,68,0.35)'
              : '0 4px 18px rgba(0,0,0,0.25)',

            cursor: 'pointer',
          },
        };
      }
    );

    const graphEdges: Edge[] = lineageEdges.map(
      (edge: LineageEdgeData) => ({
        id: `division-${edge.parent_id}-${edge.child_id}`,

        source: String(edge.parent_id),
        target: String(edge.child_id),

        type: 'smoothstep',

        animated: false,

        style: {
          stroke: '#ef4444',
          strokeWidth: 2.5,
        },

        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#ef4444',
        },
      })
    );

    const {
      nodes: positionedNodes,
      edges: positionedEdges,
    } = layoutLineage(
      graphNodes,
      graphEdges
    );

    setNodes(positionedNodes);
    setEdges(positionedEdges);

  }, [
    lineageNodes,
    lineageEdges,
    selectedCellId,
    setNodes,
    setEdges,
  ]);

  const graphContent = (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={(_, node) => {
        setSelectedCell(Number(node.id));
      }}
      fitView
      fitViewOptions={{
        padding: 0.2,
        minZoom: 0.5,
        maxZoom: 1.5,
      }}
      proOptions={{
        hideAttribution: true,
      }}
    >
      <Background
        color="#1f2937"
        gap={24}
        size={1}
      />

        <MiniMap
          pannable
          zoomable
          nodeColor="#334155"
          maskColor="rgba(2,6,23,.75)"
          className="!bg-[#080d18] !border !border-slate-800"
        />

      <Controls
        showInteractive={false}
        className="bg-[#0b1220] border-gray-700"
      />
    </ReactFlow>
  );

  if (!nodes.length) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-[#050914]">
        <div className="text-center font-mono">
          <div className="text-gray-500 text-sm">
            No lineage available
          </div>

          <div className="text-gray-700 text-xs mt-2">
            Run the analysis pipeline to reconstruct lineage.
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="relative w-full h-full bg-[#050914]">

        <button
          onClick={() => setFullscreen(true)}
          className="
            absolute
            right-4
            top-4
            z-20
            p-2
            rounded-md
            bg-[#0b1220]
            border
            border-gray-700
            text-gray-400
            hover:text-white
            hover:border-gray-500
            transition
          "
          title="Expand lineage graph"
        >
          <Maximize2 size={16} />
        </button>

        <div className="absolute left-4 top-4 z-20 pointer-events-none">
          <div className="text-[10px] text-gray-500 uppercase tracking-[0.2em]">
            Cell Lineage
          </div>

          <div className="text-xs text-gray-300 font-mono mt-1">
            {lineageNodes.length} cells · {lineageEdges.length} divisions
          </div>
        </div>

        {graphContent}
      </div>

      {fullscreen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm">

          <div
            className="
              relative
              w-[80vw]
              h-[80vh]
              bg-[#050914]
              border
              border-gray-700
              rounded-2xl
              shadow-2xl
              overflow-hidden
            "
          >

            <div className="absolute left-6 top-5 z-20">
              <div className="text-[10px] text-gray-500 uppercase tracking-[0.2em]">
                Cell Lineage
              </div>

              <div className="text-sm text-gray-300 font-mono mt-1">
                {lineageNodes.length} cells · {lineageEdges.length} divisions
              </div>
            </div>

            <button
              onClick={() => setFullscreen(false)}
              className="
                absolute
                right-5
                top-5
                z-30
                p-2
                rounded-md
                bg-[#0b1220]
                border
                border-gray-700
                text-gray-400
                hover:text-white
                transition
              "
              title="Close fullscreen"
            >
              <X size={17} />
            </button>

            {graphContent}
          </div>
        </div>
      )}
    </>
  );
};