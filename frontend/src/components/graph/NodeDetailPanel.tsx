import { useEffect, useState } from 'react'
import { X, ExternalLink, ArrowRight, ArrowLeft } from 'lucide-react'
import { fetchNode } from '../../lib/api'
import type { NodeDetail } from '../../types'
import { NODE_TYPE_COLORS, NODE_TYPE_ICONS } from '../../types'

interface NodeDetailPanelProps {
  nodeId: string | null
  onClose: () => void
  onNavigateTo: (nodeId: string) => void
}

export default function NodeDetailPanel({ nodeId, onClose, onNavigateTo }: NodeDetailPanelProps) {
  const [detail, setDetail] = useState<NodeDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!nodeId) { setDetail(null); return }
    setLoading(true)
    setError(null)
    fetchNode(nodeId)
      .then(setDetail)
      .catch(() => setError('Could not load node details'))
      .finally(() => setLoading(false))
  }, [nodeId])

  if (!nodeId) return null

  const color = detail ? (NODE_TYPE_COLORS[detail.node_type] || '#94a3b8') : '#94a3b8'
  const icon = detail ? (NODE_TYPE_ICONS[detail.node_type] || '⬡') : '⬡'

  return (
    <div className="w-72 flex-shrink-0 flex flex-col overflow-hidden"
      style={{
        background: '#0d1629',
        borderLeft: `2px solid ${color}`,
        boxShadow: `-4px 0 24px rgba(0,0,0,0.4)`,
      }}>

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 flex-shrink-0"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', background: `${color}12` }}>
        <div className="flex items-center gap-2 overflow-hidden">
          <span className="text-xl flex-shrink-0">{icon}</span>
          <div className="overflow-hidden">
            {loading ? (
              <span className="text-sm" style={{ color: '#64748b' }}>Loading…</span>
            ) : detail ? (
              <>
                <div className="text-[10px] font-bold uppercase tracking-widest mb-0.5" style={{ color }}>
                  {detail.node_type}
                </div>
                <div className="text-sm font-semibold truncate" style={{ color: '#f1f5f9' }}>
                  {detail.label}
                </div>
              </>
            ) : (
              <span className="text-sm" style={{ color: '#64748b' }}>Node Details</span>
            )}
          </div>
        </div>
        <button onClick={onClose}
          className="w-6 h-6 flex items-center justify-center rounded-full flex-shrink-0 transition-colors"
          style={{ color: '#475569', background: 'rgba(255,255,255,0.05)' }}
          onMouseEnter={e => (e.currentTarget.style.color = '#f1f5f9')}
          onMouseLeave={e => (e.currentTarget.style.color = '#475569')}>
          <X size={13} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {error && (
          <div className="text-xs rounded-lg p-2.5" style={{ color: '#f87171', background: 'rgba(239,68,68,0.1)' }}>
            {error}
          </div>
        )}

        {detail && (
          <>
            {/* Properties */}
            <section>
              <h3 className="text-[10px] font-bold uppercase tracking-widest mb-2.5" style={{ color: '#475569' }}>
                Properties
              </h3>
              <div className="space-y-1.5">
                {Object.entries(detail.metadata).map(([k, v]) => {
                  if (!v && v !== 0) return null
                  return (
                    <div key={k} className="flex gap-2 text-xs">
                      <span className="min-w-[80px] flex-shrink-0 capitalize" style={{ color: '#64748b' }}>
                        {k.replace(/_/g, ' ')}
                      </span>
                      <span className="break-all font-medium" style={{ color: '#cbd5e1' }}>
                        {typeof v === 'boolean' ? (v ? '✅ Yes' : '❌ No') : String(v)}
                      </span>
                    </div>
                  )
                })}
              </div>
            </section>

            {/* Outgoing */}
            {detail.outgoing.length > 0 && (
              <section>
                <h3 className="text-[10px] font-bold uppercase tracking-widest mb-2" style={{ color: '#475569' }}>
                  Outgoing ({detail.outgoing.length})
                </h3>
                <div className="space-y-1">
                  {detail.outgoing.map(e => (
                    <button key={e.edge_id} onClick={() => onNavigateTo(e.target_id!)}
                      className="w-full flex items-center gap-2 text-xs text-left p-2 rounded-lg transition-colors group"
                      style={{ background: 'rgba(255,255,255,0.03)' }}
                      onMouseEnter={e2 => (e2.currentTarget.style.background = 'rgba(255,255,255,0.07)')}
                      onMouseLeave={e2 => (e2.currentTarget.style.background = 'rgba(255,255,255,0.03)')}>
                      <ArrowRight size={11} style={{ color: color, flexShrink: 0 }} />
                      <span className="text-[10px] flex-shrink-0 font-medium" style={{ color: NODE_TYPE_COLORS[e.type] || '#64748b' }}>
                        {e.edge_type.replace(/_/g, ' ')}
                      </span>
                      <span className="truncate" style={{ color: '#94a3b8' }}>{e.label}</span>
                      <ExternalLink size={9} style={{ color: '#334155', flexShrink: 0, marginLeft: 'auto' }} />
                    </button>
                  ))}
                </div>
              </section>
            )}

            {/* Incoming */}
            {detail.incoming.length > 0 && (
              <section>
                <h3 className="text-[10px] font-bold uppercase tracking-widest mb-2" style={{ color: '#475569' }}>
                  Incoming ({detail.incoming.length})
                </h3>
                <div className="space-y-1">
                  {detail.incoming.map(e => (
                    <button key={e.edge_id} onClick={() => onNavigateTo(e.source_id!)}
                      className="w-full flex items-center gap-2 text-xs text-left p-2 rounded-lg transition-colors"
                      style={{ background: 'rgba(255,255,255,0.03)' }}
                      onMouseEnter={e2 => (e2.currentTarget.style.background = 'rgba(255,255,255,0.07)')}
                      onMouseLeave={e2 => (e2.currentTarget.style.background = 'rgba(255,255,255,0.03)')}>
                      <ArrowLeft size={11} style={{ color: '#64748b', flexShrink: 0 }} />
                      <span className="text-[10px] flex-shrink-0 font-medium" style={{ color: NODE_TYPE_COLORS[e.type] || '#64748b' }}>
                        {e.edge_type.replace(/_/g, ' ')}
                      </span>
                      <span className="truncate" style={{ color: '#94a3b8' }}>{e.label}</span>
                      <ExternalLink size={9} style={{ color: '#334155', flexShrink: 0, marginLeft: 'auto' }} />
                    </button>
                  ))}
                </div>
              </section>
            )}

            {/* Node ID footer */}
            <div className="pt-3" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
              <div className="text-[10px] font-mono break-all" style={{ color: '#334155' }}>{detail.node_id}</div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
