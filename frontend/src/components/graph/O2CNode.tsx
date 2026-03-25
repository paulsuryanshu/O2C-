import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { NODE_TYPE_COLORS, NODE_TYPE_ICONS } from '../../types'

interface O2CNodeData {
  label: string
  nodeType: string
  highlighted: boolean
  selected: boolean
  [key: string]: unknown
}

export const O2CNode = memo(({ data, selected }: NodeProps) => {
  const d = data as O2CNodeData
  const color = NODE_TYPE_COLORS[d.nodeType] || '#94a3b8'
  const icon = NODE_TYPE_ICONS[d.nodeType] || '⬡'
  const isHighlighted = d.highlighted
  const isSelected = selected

  return (
    <div
      style={{
        borderColor: color,
        boxShadow: isHighlighted
          ? `0 0 0 3px ${color}, 0 0 12px ${color}66`
          : isSelected
          ? `0 0 0 2px ${color}`
          : 'none',
        transform: isHighlighted ? 'scale(1.08)' : 'scale(1)',
        transition: 'all 0.2s ease',
      }}
      className={`
        rounded-lg border-2 px-3 py-2 min-w-[120px] max-w-[180px] cursor-pointer
        ${isHighlighted ? 'bg-slate-700' : 'bg-slate-800'}
        hover:bg-slate-700
      `}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{ background: color, width: 8, height: 8 }}
      />

      <div className="flex items-center gap-1.5">
        <span className="text-base leading-none">{icon}</span>
        <div className="overflow-hidden">
          <div
            className="text-[10px] font-semibold uppercase tracking-wider mb-0.5"
            style={{ color }}
          >
            {d.nodeType}
          </div>
          <div className="text-xs text-slate-200 font-medium truncate leading-tight">
            {d.label}
          </div>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: color, width: 8, height: 8 }}
      />
    </div>
  )
})

O2CNode.displayName = 'O2CNode'
