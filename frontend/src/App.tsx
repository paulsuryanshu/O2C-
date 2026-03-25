import { useEffect, useState, useCallback } from 'react'
import { ReactFlowProvider } from '@xyflow/react'

import TopBar from './components/layout/TopBar'
import GraphCanvas from './components/graph/GraphCanvas'
import GraphStatsBar from './components/graph/GraphStatsBar'
import GraphOverlay from './components/graph/GraphOverlay'
import NodeDetailPanel from './components/graph/NodeDetailPanel'
import ChatPanel from './components/chat/ChatPanel'

import { useGraph } from './hooks/useGraph'
import { runIngestion } from './lib/api'

export default function App() {
  const {
    graphData, stats, loading, error,
    loadGraph, setFocalNode,
    highlightedNodes, highlightedEdges,
    highlight, clearHighlight,
  } = useGraph()

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [typeFilter, setTypeFilter] = useState<string | null>(null)
  const [ingesting, setIngesting] = useState(false)

  useEffect(() => { loadGraph() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleNodeClick = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId)
  }, [])

  const handleNavigateTo = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId)
    highlight([nodeId], [])
  }, [highlight])

  const handleFilterType = useCallback((type: string | null) => {
    setTypeFilter(type)
    clearHighlight()
    if (type) loadGraph({ node_type: type })
    else loadGraph()
  }, [loadGraph, clearHighlight])

  const handleHighlight = useCallback((nodeIds: string[], edgeIds: string[]) => {
    highlight(nodeIds, edgeIds)
    if (nodeIds.length > 0) setSelectedNodeId(nodeIds[0])
  }, [highlight])

  const handleIngest = useCallback(async () => {
    setIngesting(true)
    try {
      await runIngestion()
      await loadGraph()
    } catch (e) {
      console.error('Ingestion failed', e)
    } finally {
      setIngesting(false)
    }
  }, [loadGraph])

  const handleSearchSelect = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId)
    highlight([nodeId], [])
    setFocalNode(nodeId)
  }, [highlight, setFocalNode])

  const handleRefreshGraph = useCallback(() => {
    clearHighlight()
    setTypeFilter(null)
    loadGraph()
  }, [loadGraph, clearHighlight])

  const isEmpty = !loading && !error && graphData.nodes.length === 0

  return (
    <div className="h-screen flex flex-col overflow-hidden" style={{ background: '#080f1e', color: '#f1f5f9' }}>

      {/* ── Top Bar ───────────────────────────────── */}
      <TopBar
        onNodeSelect={handleSearchSelect}
        onRefreshGraph={handleRefreshGraph}
        isGraphLoaded={graphData.nodes.length > 0}
      />

      {/* ── Stats Bar ─────────────────────────────── */}
      <GraphStatsBar
        stats={stats}
        onFilterType={handleFilterType}
        activeFilter={typeFilter}
      />

      {/* ── Main Layout ───────────────────────────── */}
      <div className="flex flex-1 overflow-hidden relative">

        {/* Graph canvas — takes all remaining space */}
        <div className="flex-1 relative overflow-hidden">
          <ReactFlowProvider>
            <GraphCanvas
              graphData={graphData}
              highlightedNodes={highlightedNodes}
              highlightedEdges={highlightedEdges}
              onNodeClick={handleNodeClick}
            />
          </ReactFlowProvider>

          <GraphOverlay
            loading={loading}
            error={error}
            isEmpty={isEmpty}
            onIngest={handleIngest}
            onRefresh={() => loadGraph()}
            ingesting={ingesting}
          />
        </div>

        {/* Node detail panel — only shows when a node is selected */}
        {selectedNodeId && (
          <NodeDetailPanel
            nodeId={selectedNodeId}
            onClose={() => setSelectedNodeId(null)}
            onNavigateTo={handleNavigateTo}
          />
        )}

        {/* Chat panel — always visible on right */}
        <ChatPanel onHighlight={handleHighlight} />
      </div>
    </div>
  )
}
