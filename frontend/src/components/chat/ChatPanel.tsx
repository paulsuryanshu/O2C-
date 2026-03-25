import { useRef, useEffect, useState, type KeyboardEvent } from 'react'
import { Send, Trash2, ChevronDown, ChevronUp, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { ChatMessage } from '../../types'
import { SAMPLE_PROMPTS } from '../../types'
import { useChat } from '../../hooks/useChat'

interface ChatPanelProps {
  onHighlight: (nodeIds: string[], edgeIds: string[]) => void
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const [showSpec, setShowSpec] = useState(false)
  const isUser = msg.role === 'user'

  return (
    <div className={`flex flex-col gap-1 ${isUser ? 'items-end' : 'items-start'}`}>
      <div className="rounded-2xl px-4 py-2.5 max-w-[93%] text-sm leading-relaxed"
        style={{
          background: isUser
            ? 'linear-gradient(135deg, #3b5bdb, #7048e8)'
            : 'rgba(255,255,255,0.05)',
          color: '#f1f5f9',
          borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
          border: isUser ? 'none' : '1px solid rgba(255,255,255,0.06)',
        }}>
        {isUser ? (
          <span>{msg.content}</span>
        ) : (
          <div className="chat-markdown">
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          </div>
        )}
      </div>

      {msg.query_spec && !isUser && (
        <div className="max-w-[93%] px-1">
          <button onClick={() => setShowSpec(v => !v)}
            className="flex items-center gap-1 text-[10px] transition-colors"
            style={{ color: '#475569' }}
            onMouseEnter={e => (e.currentTarget.style.color = '#94a3b8')}
            onMouseLeave={e => (e.currentTarget.style.color = '#475569')}>
            <Sparkles size={9} />
            <span>Query: {String(msg.query_spec.action)}</span>
            {showSpec ? <ChevronUp size={9} /> : <ChevronDown size={9} />}
          </button>
          {showSpec && (
            <pre className="text-[10px] rounded-lg p-2 mt-1 overflow-x-auto"
              style={{ color: '#64748b', background: '#0a1220', border: '1px solid rgba(255,255,255,0.06)' }}>
              {JSON.stringify(msg.query_spec, null, 2)}
            </pre>
          )}
        </div>
      )}

      <span className="text-[10px] px-1" style={{ color: '#334155' }}>
        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </span>
    </div>
  )
}

export default function ChatPanel({ onHighlight }: ChatPanelProps) {
  const { messages, loading, sendMessage, clearMessages } = useChat()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const msg = input.trim()
    if (!msg || loading) return
    setInput('')
    await sendMessage(msg, onHighlight)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  return (
    <div className="w-96 flex-shrink-0 flex flex-col overflow-hidden"
      style={{ background: '#0d1629', borderLeft: '1px solid rgba(255,255,255,0.06)' }}>

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 flex-shrink-0"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>
            <Sparkles size={11} className="text-white" />
          </div>
          <div>
            <div className="text-sm font-semibold" style={{ color: '#f1f5f9' }}>Query Assistant</div>
            <div className="text-xs" style={{ color: '#475569' }}>Grounded in your O2C data</div>
          </div>
        </div>
        <button onClick={clearMessages} title="Clear chat"
          className="w-7 h-7 flex items-center justify-center rounded-lg transition-colors"
          style={{ color: '#475569' }}
          onMouseEnter={e => (e.currentTarget.style.color = '#94a3b8')}
          onMouseLeave={e => (e.currentTarget.style.color = '#475569')}>
          <Trash2 size={13} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="space-y-4">
            <p className="text-xs text-center leading-relaxed" style={{ color: '#475569' }}>
              Ask questions about your Order-to-Cash data.<br />
              All answers come from real database queries.
            </p>
            <div className="space-y-2">
              <p className="text-xs font-medium" style={{ color: '#334155' }}>Try asking:</p>
              {SAMPLE_PROMPTS.map((p, i) => (
                <button key={i} onClick={() => { setInput(p); inputRef.current?.focus() }}
                  className="w-full text-left text-xs px-3 py-2.5 rounded-xl transition-all"
                  style={{
                    color: '#94a3b8',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.06)',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.07)'
                    e.currentTarget.style.color = '#f1f5f9'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.03)'
                    e.currentTarget.style.color = '#94a3b8'
                  }}>
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(msg => <MessageBubble key={msg.id} msg={msg} />)}

        {loading && (
          <div className="flex items-start">
            <div className="px-4 py-3 rounded-2xl rounded-bl-sm"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div className="flex gap-1.5 items-center h-4">
                {[0, 150, 300].map((delay, i) => (
                  <span key={i} className="w-1.5 h-1.5 rounded-full bounce-dot"
                    style={{ background: '#64748b', animationDelay: `${delay}ms` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="flex-shrink-0 p-3"
        style={{ borderTop: '1px solid rgba(255,255,255,0.06)', background: '#0d1629' }}>
        <div className="flex gap-2 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about orders, deliveries, billing…"
            rows={2}
            className="flex-1 text-sm resize-none focus:outline-none rounded-xl px-3 py-2.5 transition-all"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: '#f1f5f9',
            }}
            onFocus={e => (e.currentTarget.style.borderColor = 'rgba(99,102,241,0.5)')}
            onBlur={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)')}
          />
          <button onClick={handleSend} disabled={!input.trim() || loading}
            className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all disabled:opacity-30"
            style={{
              background: 'linear-gradient(135deg, #3b5bdb, #7048e8)',
              color: 'white',
            }}
            onMouseEnter={e => { if (!e.currentTarget.disabled) e.currentTarget.style.opacity = '0.85' }}
            onMouseLeave={e => { e.currentTarget.style.opacity = '1' }}>
            <Send size={15} />
          </button>
        </div>
        <p className="text-[10px] mt-1.5 px-1" style={{ color: '#334155' }}>
          Enter to send · Shift+Enter for newline
        </p>
      </div>
    </div>
  )
}
