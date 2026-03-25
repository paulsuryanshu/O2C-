import axios from 'axios'
import type { GraphData, GraphStats, NodeDetail, ChatResponse, SearchResult } from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export async function fetchGraph(params?: {
  node_type?: string
  focal?: string
  limit?: number
}): Promise<GraphData> {
  const { data } = await api.get('/graph', { params })
  return data
}

export async function fetchGraphStats(): Promise<GraphStats> {
  const { data } = await api.get('/graph/stats')
  return data
}

export async function fetchNode(nodeId: string): Promise<NodeDetail> {
  const { data } = await api.get(`/node/${encodeURIComponent(nodeId)}`)
  return data
}

export async function searchDocuments(q: string): Promise<{ results: SearchResult[]; count: number }> {
  const { data } = await api.get('/search', { params: { q } })
  return data
}

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  const { data } = await api.post('/chat', { message })
  return data
}

export async function runIngestion(): Promise<{ status: string; ingestion: Record<string, number>; graph: { nodes: number; edges: number } }> {
  const { data } = await api.post('/ingest/run')
  return data
}

export async function checkHealth(): Promise<{ status: string }> {
  const { data } = await api.get('/health')
  return data
}
