import { Database, RefreshCw, AlertCircle } from 'lucide-react'

interface GraphOverlayProps {
  loading: boolean
  error: string | null
  isEmpty: boolean
  onIngest: () => void
  onRefresh: () => void
  ingesting: boolean
}

export default function GraphOverlay({
  loading, error, isEmpty, onIngest, onRefresh, ingesting
}: GraphOverlayProps) {
  if (loading) {
    return (
      <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80 z-20">
        <div className="text-center space-y-3">
          <RefreshCw size={32} className="text-blue-400 animate-spin mx-auto" />
          <p className="text-slate-300 text-sm">Loading graph…</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80 z-20">
        <div className="text-center space-y-3 max-w-sm mx-auto px-4">
          <AlertCircle size={32} className="text-red-400 mx-auto" />
          <p className="text-red-300 text-sm">{error}</p>
          <button
            onClick={onRefresh}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg text-sm text-slate-300 hover:text-white"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (isEmpty) {
    return (
      <div className="absolute inset-0 flex items-center justify-center z-20">
        <div className="text-center space-y-4 max-w-md mx-auto px-6">
          <Database size={48} className="text-slate-600 mx-auto" />
          <div>
            <h3 className="text-lg font-semibold text-white mb-1">No Data Yet</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Place your SAP-style JSON files in the <code className="bg-slate-800 px-1 rounded text-blue-300">backend/data/</code> folder
              (or run the sample data generator), then click <strong>Ingest Data</strong>.
            </p>
          </div>
          <div className="flex flex-col gap-2 items-center">
            <button
              onClick={onIngest}
              disabled={ingesting}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-white font-medium text-sm transition-colors"
            >
              <Database size={16} />
              {ingesting ? 'Ingesting…' : 'Ingest Data & Build Graph'}
            </button>
            <p className="text-xs text-slate-600">
              Or run: <code className="bg-slate-800 px-1 rounded">python scripts/ingest.py</code> in backend/
            </p>
          </div>
        </div>
      </div>
    )
  }

  return null
}
