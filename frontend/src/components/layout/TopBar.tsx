import { useState, useRef, useEffect } from 'react'
import { Search, RefreshCw, Database, X, AlertCircle, CheckCircle } from 'lucide-react'
import { searchDocuments, runIngestion } from '../../lib/api'
import type { SearchResult } from '../../types'
import { NODE_TYPE_COLORS, NODE_TYPE_ICONS } from '../../types'

interface TopBarProps {
  onNodeSelect: (nodeId: string) => void
  onRefreshGraph: () => void
  isGraphLoaded: boolean
}

export default function TopBar({ onNodeSelect, onRefreshGraph, isGraphLoaded }: TopBarProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [ingestStatus, setIngestStatus] = useState<'idle' | 'running' | 'done' | 'error'>('idle')
  const [ingestMsg, setIngestMsg] = useState('')
  const searchRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node))
        setShowResults(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSearch = (value: string) => {
    setQuery(value)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (value.length < 2) { setResults([]); setShowResults(false); return }
    debounceRef.current = setTimeout(async () => {
      setSearching(true)
      try {
        const data = await searchDocuments(value)
        setResults(data.results)
        setShowResults(true)
      } catch { /* ignore */ } finally { setSearching(false) }
    }, 300)
  }

  const handleSelect = (result: SearchResult) => {
    onNodeSelect(result.node_id)
    setQuery('')
    setShowResults(false)
  }

  const handleIngest = async () => {
    setIngestStatus('running')
    setIngestMsg('Ingesting…')
    try {
      const res = await runIngestion()
      setIngestMsg(`Done — ${res.graph.nodes} nodes, ${res.graph.edges} edges`)
      setIngestStatus('done')
      onRefreshGraph()
      setTimeout(() => setIngestStatus('idle'), 5000)
    } catch {
      setIngestMsg('Failed — check backend logs')
      setIngestStatus('error')
      setTimeout(() => setIngestStatus('idle'), 5000)
    }
  }

  return (
    <div className="h-13 flex items-center gap-3 px-4 py-2.5 flex-shrink-0 z-10"
      style={{ background: '#0d1629', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>

      {/* Logo */}
      <div className="flex items-center gap-2 mr-1 flex-shrink-0">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center"
          style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>
          <span className="text-white text-xs font-bold">O2</span>
        </div>
        <div>
          <div className="text-white font-semibold text-sm leading-none">O2C Graph</div>
          <div className="text-xs leading-none mt-0.5" style={{ color: '#64748b' }}>Explorer</div>
        </div>
      </div>

      {/* Search */}
      <div ref={searchRef} className="relative flex-1 max-w-md">
        <div className="flex items-center rounded-lg px-3 h-9 gap-2"
          style={{ background: '#1a2540', border: '1px solid rgba(255,255,255,0.08)' }}>
          <Search size={13} style={{ color: '#64748b' }} className="flex-shrink-0" />
          <input
            type="text"
            value={query}
            onChange={e => handleSearch(e.target.value)}
            placeholder="Search customers, billing docs, products…"
            className="bg-transparent text-sm flex-1 focus:outline-none"
            style={{ color: '#f1f5f9' }}
          />
          {query && (
            <button onClick={() => { setQuery(''); setShowResults(false) }} style={{ color: '#64748b' }}
              className="hover:text-white">
              <X size={12} />
            </button>
          )}
          {searching && <RefreshCw size={12} style={{ color: '#64748b' }} className="animate-spin" />}
        </div>

        {showResults && results.length > 0 && (
          <div className="absolute top-full mt-1 left-0 right-0 rounded-xl shadow-2xl z-50 overflow-hidden max-h-72 overflow-y-auto"
            style={{ background: '#1a2540', border: '1px solid rgba(255,255,255,0.1)' }}>
            {results.map(r => {
              const color = NODE_TYPE_COLORS[r.type] || '#94a3b8'
              const icon = NODE_TYPE_ICONS[r.type] || '⬡'
              return (
                <button key={r.node_id} onClick={() => handleSelect(r)}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors"
                  style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}
                  onMouseEnter={e => (e.currentTarget.style.background = '#243050')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                  <span className="text-base">{icon}</span>
                  <div className="overflow-hidden flex-1">
                    <div className="text-sm font-medium truncate" style={{ color: '#f1f5f9' }}>{r.label}</div>
                    <div className="text-xs flex gap-2">
                      <span style={{ color }}>{r.type}</span>
                      <span style={{ color: '#64748b' }} className="font-mono">{r.id}</span>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </div>

      <div className="flex-1" />

      {/* Ingest status badge */}
      {ingestStatus !== 'idle' && (
        <div className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg ${
          ingestStatus === 'done' ? 'text-green-400 bg-green-950/60' :
          ingestStatus === 'error' ? 'text-red-400 bg-red-950/60' :
          'text-blue-400 bg-blue-950/60'}`}>
          {ingestStatus === 'done' ? <CheckCircle size={12} /> :
           ingestStatus === 'error' ? <AlertCircle size={12} /> :
           <RefreshCw size={12} className="animate-spin" />}
          {ingestMsg}
        </div>
      )}

      {/* Buttons */}
      <button onClick={handleIngest} disabled={ingestStatus === 'running'}
        className="flex items-center gap-2 px-3 h-8 rounded-lg text-xs font-medium disabled:opacity-50 transition-all"
        style={{ background: '#1a2540', border: '1px solid rgba(255,255,255,0.1)', color: '#cbd5e1' }}
        onMouseEnter={e => (e.currentTarget.style.background = '#243050')}
        onMouseLeave={e => (e.currentTarget.style.background = '#1a2540')}>
        <Database size={13} />
        {ingestStatus === 'running' ? 'Ingesting…' : 'Ingest Data'}
      </button>

      <button onClick={onRefreshGraph} disabled={!isGraphLoaded}
        className="flex items-center gap-2 px-3 h-8 rounded-lg text-xs font-medium disabled:opacity-40 transition-all"
        style={{ background: '#1a2540', border: '1px solid rgba(255,255,255,0.1)', color: '#cbd5e1' }}
        onMouseEnter={e => (e.currentTarget.style.background = '#243050')}
        onMouseLeave={e => (e.currentTarget.style.background = '#1a2540')}>
        <RefreshCw size={13} />
        Refresh
      </button>
    </div>
  )
}
