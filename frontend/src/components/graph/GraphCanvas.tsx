import { useCallback, useEffect } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  BackgroundVariant,
  type Node,
  type Edge,
  type NodeMouseHandler,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { O2CNode } from './O2CNode'
import type { GraphData } from '../../types'
import { NODE_TYPE_COLORS } from '../../types'

const nodeTypes = { o2cNode: O2CNode }

function autoLayout(nodes: Node[]): Node[] {
  const typeOrder = [
    'Customer', 'SalesOrder', 'Delivery',
    'BillingDocument', 'JournalEntry', 'Payment',
    'Product', 'Plant',
  ]
  const byType: Record<string, Node[]> = {}
  for (const n of nodes) {
    const t = (n.data as { nodeType: string }).nodeType || 'Other'
    if (!byType[t]) byType[t] = []
    byType[t].push(n)
  }
  const COLUMN_WIDTH = 220
  const ROW_HEIGHT = 80
  const laid: Node[] = []
  let col = 0
  for (const type of [...typeOrder, ...Object.keys(byType).filter(t => !typeOrder.includes(t))]) {
    const group = byType[type]
    if (!group?.length) continue
    group.forEach((n, row) => {
      laid.push({ ...n, position: { x: col * COLUMN_WIDTH, y: row * ROW_HEIGHT } })
    })
    col++
  }
  return laid
}

interface GraphCanvasProps {
  graphData: GraphData
  highlightedNodes: Set<string>
  highlightedEdges: Set<string>
  onNodeClick: (nodeId: string) => void
}

export default function GraphCanvas({
  graphData,
  highlightedNodes,
  highlightedEdges,
  onNodeClick,
}: GraphCanvasProps) {
const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  useEffect(() => {
    const rfNodes: Node[] = graphData.nodes.map(n => ({
      id: n.id,
      type: 'o2cNode',
      position: { x: 0, y: 0 },
      data: {
        label: n.label,
        nodeType: n.type,
        highlighted: highlightedNodes.has(n.id),
        ...n.data,
      },
    }))
    setNodes(autoLayout(rfNodes))

    const rfEdges: Edge[] = graphData.edges.map(e => {
      const hl = highlightedEdges.has(e.id)
      const color = hl ? '#facc15' : '#cbd5e1'
      return {
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.type.replace(/_/g, ' '),
        type: 'smoothstep',
        animated: hl,
        style: { stroke: color, strokeWidth: hl ? 3 : 1.5, opacity: hl ? 1 : 0.75 },
        labelStyle: { fill: '#94a3b8', fontSize: 8 },
        labelBgStyle: { fill: '#0f172a', fillOpacity: 0.9 },
        markerEnd: { type: MarkerType.ArrowClosed, color, width: 14, height: 14 },
      }
    })
    setEdges(rfEdges)
  }, [graphData]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setNodes(prev =>
      prev.map(n => ({
        ...n,
        data: { ...n.data, highlighted: highlightedNodes.has(n.id) },
      }))
    )
    setEdges(prev =>
      prev.map(e => {
        const hl = highlightedEdges.has(e.id)
        const color = hl ? '#facc15' : '#cbd5e1'
        return {
          ...e,
          animated: hl,
          style: { stroke: color, strokeWidth: hl ? 3 : 1.5, opacity: hl ? 1 : 0.75 },
          markerEnd: { type: MarkerType.ArrowClosed, color, width: 14, height: 14 },
        }
      })
    )
  }, [highlightedNodes, highlightedEdges]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleNodeClick: NodeMouseHandler = useCallback(
    (_evt, node) => onNodeClick(node.id),
    [onNodeClick]
  )

  const miniMapNodeColor = useCallback((node: Node) => {
    const t = (node.data as { nodeType: string }).nodeType
    return NODE_TYPE_COLORS[t] || '#64748b'
  }, [])

  return (
    <div className="w-full h-full" style={{ background: '#080f1e' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        minZoom={0.04}
        maxZoom={2.5}
        defaultEdgeOptions={{ type: 'smoothstep' }}
        proOptions={{ hideAttribution: true }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          color="#1e293b"
          gap={24}
          size={1.2}
        />
        <Controls />
        <MiniMap
          nodeColor={miniMapNodeColor}
          maskColor="rgba(8,15,30,0.75)"
        />
      </ReactFlow>
    </div>
  )
}
