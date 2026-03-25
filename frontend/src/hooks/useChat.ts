import { useState, useCallback } from 'react'
import { sendChatMessage } from '../lib/api'
import type { ChatMessage } from '../types'

let msgId = 0

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)

  const sendMessage = useCallback(async (
    content: string,
    onHighlight?: (nodeIds: string[], edgeIds: string[]) => void
  ) => {
    const userMsg: ChatMessage = {
      id: `msg-${++msgId}`,
      role: 'user',
      content,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const response = await sendChatMessage(content)
      const assistantMsg: ChatMessage = {
        id: `msg-${++msgId}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        highlight: response.highlight,
        query_spec: response.query_spec,
        evidence: response.evidence,
      }
      setMessages(prev => [...prev, assistantMsg])

      if (onHighlight && response.highlight?.nodes?.length) {
        onHighlight(response.highlight.nodes, response.highlight.edges || [])
      }
    } catch (e) {
      const errMsg: ChatMessage = {
        id: `msg-${++msgId}`,
        role: 'assistant',
        content: 'Error connecting to the backend. Please check that the server is running.',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errMsg])
    } finally {
      setLoading(false)
    }
  }, [])

  const clearMessages = useCallback(() => setMessages([]), [])

  return { messages, loading, sendMessage, clearMessages }
}
