import {
  createElement,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react'

const WebSocketContext = createContext(null)
const DEFAULT_WS_URL = (() => {
  const configuredBaseUrl = import.meta.env.VITE_WS_URL || import.meta.env.VITE_API_BASE_URL
  if (configuredBaseUrl) {
    const normalizedBase = configuredBaseUrl
      .replace(/^http/i, 'ws')
      .replace(/\/$/, '')

    if (normalizedBase.endsWith('/ws')) {
      return normalizedBase
    }

    return `${normalizedBase}/ws`
  }

  return 'ws://localhost:8002/ws'
})()

/**
 * Shared WebSocket provider that keeps a single live connection open
 * for the app and reference-counts symbol subscriptions across components.
 */
export const WebSocketProvider = ({ children, url = DEFAULT_WS_URL }) => {
  const [isConnected, setIsConnected] = useState(false)
  const [message, setMessage] = useState(null)
  const ws = useRef(null)
  const retryCountRef = useRef(0)
  const retryTimeoutRef = useRef(null)
  const shouldReconnectRef = useRef(true)
  const subscriptionsRef = useRef(new Map())
  const maxRetries = 5
  const baseDelay = 1000 // 1 second

  const send = useCallback((data) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  const replaySubscriptions = useCallback(() => {
    subscriptionsRef.current.forEach((count, symbol) => {
      if (count > 0) {
        send({ type: 'subscribe', symbol })
      }
    })
  }, [send])

  const connectWebSocket = useCallback(() => {
    // Prevent multiple simultaneous connection attempts
    if (
      ws.current &&
      (ws.current.readyState === WebSocket.CONNECTING || ws.current.readyState === WebSocket.OPEN)
    ) {
      return
    }

    try {
      ws.current = new WebSocket(url)

      ws.current.onopen = () => {
        console.log('✅ WebSocket connected')
        setIsConnected(true)
        retryCountRef.current = 0 // Reset retry count on successful connection
        replaySubscriptions()
      }

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setMessage(data)
        } catch (err) {
          console.error('Error parsing WebSocket message:', err)
        }
      }

      ws.current.onerror = (error) => {
        if (!shouldReconnectRef.current) {
          return
        }

        console.warn('⚠️ WebSocket connection issue:', error)
        setIsConnected(false)
      }

      ws.current.onclose = () => {
        if (!shouldReconnectRef.current) {
          return
        }

        console.log('❌ WebSocket disconnected')
        setIsConnected(false)
        
        // Attempt to reconnect with exponential backoff
        if (retryCountRef.current < maxRetries && shouldReconnectRef.current) {
          const delay = baseDelay * Math.pow(2, retryCountRef.current)
          console.log(`🔄 Reconnecting in ${delay}ms (attempt ${retryCountRef.current + 1}/${maxRetries})`)
          retryCountRef.current += 1
          retryTimeoutRef.current = setTimeout(connectWebSocket, delay)
        } else {
          console.warn('❌ WebSocket: Max retries reached. Giving up.')
        }
      }
    } catch (err) {
      console.error('Failed to create WebSocket:', err)
      setIsConnected(false)
    }
  }, [replaySubscriptions, url])

  // Connect to WebSocket on mount
  useEffect(() => {
    shouldReconnectRef.current = true
    connectWebSocket()

    return () => {
      shouldReconnectRef.current = false
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current)
      }
      if (ws.current) {
        ws.current.onopen = null
        ws.current.onmessage = null
        ws.current.onerror = null
        ws.current.onclose = null
        ws.current.close()
      }
    }
  }, [connectWebSocket])

  // Subscribe to a symbol
  const subscribe = useCallback((symbol) => {
    if (!symbol) {
      return
    }

    const normalizedSymbol = symbol.toUpperCase()
    const currentCount = subscriptionsRef.current.get(normalizedSymbol) || 0
    subscriptionsRef.current.set(normalizedSymbol, currentCount + 1)

    if (currentCount === 0) {
      send({ type: 'subscribe', symbol: normalizedSymbol })
    }
  }, [send])

  // Unsubscribe from a symbol
  const unsubscribe = useCallback((symbol) => {
    if (!symbol) {
      return
    }

    const normalizedSymbol = symbol.toUpperCase()
    const currentCount = subscriptionsRef.current.get(normalizedSymbol) || 0

    if (currentCount <= 1) {
      subscriptionsRef.current.delete(normalizedSymbol)
      send({ type: 'unsubscribe', symbol: normalizedSymbol })
      return
    }

    subscriptionsRef.current.set(normalizedSymbol, currentCount - 1)
  }, [send])

  const value = useMemo(() => ({
    isConnected,
    message,
    send,
    subscribe,
    unsubscribe
  }), [isConnected, message, send, subscribe, unsubscribe])

  return createElement(WebSocketContext.Provider, { value }, children)
}

/**
 * Custom React hook for app-wide WebSocket access.
 */
export const useWebSocket = () => {
  const context = useContext(WebSocketContext)

  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }

  return context
}
