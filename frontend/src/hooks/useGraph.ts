import { useState, useCallback, useRef } from 'react'
import { fetchGraph, fetchGraphStats } from '../lib/api'
import type { GraphData, GraphStats } from '../types'

export function useGraph() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] })
  const [stats, setStats] = useState<GraphStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set())
  const [highlightedEdges, setHighlightedEdges] = useState<Set<string>>(new Set())
  const [focalNode, setFocalNodeState] = useState<string | null>(null)
  const loadedRef = useRef(false)

  const loadGraph = useCallback(async (options?: { node_type?: string; focal?: string; limit?: number }) => {
    setLoading(true)
    setError(null)
    try {
      const [data, statsData] = await Promise.all([
        fetchGraph(options),
        fetchGraphStats(),
      ])
      setGraphData(data)
      setStats(statsData)
      loadedRef.current = true
    } catch (e) {
      setError('Failed to load graph. Make sure the backend is running and data has been ingested.')
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [])

  const setFocalNode = useCallback((nodeId: string | null) => {
    setFocalNodeState(nodeId)
    if (nodeId) {
      loadGraph({ focal: nodeId })
    } else {
      loadGraph()
    }
  }, [loadGraph])

  const highlight = useCallback((nodeIds: string[], edgeIds: string[]) => {
    setHighlightedNodes(new Set(nodeIds))
    setHighlightedEdges(new Set(edgeIds))
  }, [])

  const clearHighlight = useCallback(() => {
    setHighlightedNodes(new Set())
    setHighlightedEdges(new Set())
  }, [])

  return {
    graphData,
    stats,
    loading,
    error,
    loadGraph,
    focalNode,
    setFocalNode,
    highlightedNodes,
    highlightedEdges,
    highlight,
    clearHighlight,
    isLoaded: loadedRef.current,
  }
}
