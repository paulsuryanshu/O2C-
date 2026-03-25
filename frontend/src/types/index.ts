// Graph types
export interface GraphNode {
  id: string
  type: string
  label: string
  entity_key: string
  data: Record<string, unknown>
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  type: string
  data: Record<string, unknown>
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface GraphStats {
  node_types: Record<string, number>
  edge_types: Record<string, number>
  total_nodes: number
  total_edges: number
}

// Node detail
export interface NodeDetail {
  node_id: string
  node_type: string
  label: string
  entity_key: string
  metadata: Record<string, unknown>
  outgoing: NeighborEdge[]
  incoming: NeighborEdge[]
}

export interface NeighborEdge {
  edge_id: string
  target_id?: string
  source_id?: string
  edge_type: string
  label: string
  type: string
}

// Chat
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  highlight?: {
    nodes: string[]
    edges: string[]
  }
  query_spec?: Record<string, unknown>
  evidence?: Record<string, unknown>
}

export interface ChatResponse {
  answer: string
  evidence: Record<string, unknown>
  highlight: {
    nodes: string[]
    edges: string[]
  }
  query_spec: Record<string, unknown>
}

// Search
export interface SearchResult {
  type: string
  id: string
  label: string
  node_id: string
  meta: Record<string, unknown>
}

// Node type color/icon mapping
export const NODE_TYPE_COLORS: Record<string, string> = {
  Customer: '#10b981',       // emerald
  SalesOrder: '#3b82f6',    // blue
  Delivery: '#f59e0b',      // amber
  BillingDocument: '#8b5cf6', // violet
  JournalEntry: '#ec4899',  // pink
  Payment: '#06b6d4',       // cyan
  Product: '#f97316',       // orange
  Plant: '#84cc16',         // lime
}

export const NODE_TYPE_ICONS: Record<string, string> = {
  Customer: '👤',
  SalesOrder: '📋',
  Delivery: '🚚',
  BillingDocument: '🧾',
  JournalEntry: '📒',
  Payment: '💳',
  Product: '📦',
  Plant: '🏭',
}

export const SAMPLE_PROMPTS = [
  'Which customers generated the most billing volume?',
  'Which products are associated with the highest number of billing documents?',
  'Find sales orders that were delivered but not billed',
  'Find billed documents without delivery',
  'Find open receivables without payments',
  'Find cancelled billing documents',
]
