import { NODE_TYPE_COLORS, NODE_TYPE_ICONS, type GraphStats } from '../../types'

interface GraphStatsBarProps {
  stats: GraphStats | null
  onFilterType: (type: string | null) => void
  activeFilter: string | null
}

export default function GraphStatsBar({ stats, onFilterType, activeFilter }: GraphStatsBarProps) {
  if (!stats) return null

  const visibleTypes = [
    'Customer', 'SalesOrder', 'Delivery', 'BillingDocument',
    'JournalEntry', 'Payment', 'Product', 'Plant',
  ]

  return (
    <div className="flex items-center gap-2 px-4 py-2 flex-shrink-0 overflow-x-auto"
      style={{ background: '#0a1220', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
      <span className="text-xs flex-shrink-0 font-mono mr-1" style={{ color: '#475569' }}>
        {stats.total_nodes.toLocaleString()} nodes · {stats.total_edges.toLocaleString()} edges
      </span>
      <div className="w-px h-4 flex-shrink-0" style={{ background: 'rgba(255,255,255,0.08)' }} />
      <div className="flex gap-1.5 flex-wrap">
        {visibleTypes.map(type => {
          const count = stats.node_types[type] ?? 0
          if (!count) return null
          const color = NODE_TYPE_COLORS[type] || '#94a3b8'
          const icon = NODE_TYPE_ICONS[type] || '⬡'
          const isActive = activeFilter === type
          return (
            <button
              key={type}
              onClick={() => onFilterType(isActive ? null : type)}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all select-none"
              style={{
                border: `1px solid ${isActive ? color : 'rgba(255,255,255,0.08)'}`,
                background: isActive ? `${color}20` : 'rgba(255,255,255,0.03)',
                color: isActive ? color : '#94a3b8',
                opacity: activeFilter && !isActive ? 0.5 : 1,
              }}
            >
              <span className="text-sm leading-none">{icon}</span>
              <span>{type}</span>
              <span className="font-bold font-mono" style={{ color: isActive ? color : '#64748b' }}>
                {count}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
