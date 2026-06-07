import React, { useState, useRef, useEffect } from 'react'
import { cryptoAPI } from '../utils/api'
import './ChatPanel.css'

export default function ChatPanel() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm your CryptoAI assistant. I can answer direct questions about your investments, your profile, your buying power, and the market.",
      sender: 'ai',
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [ollamaStatus, setOllamaStatus] = useState({ available: false, model: 'N/A' })
  const [statusLoading, setStatusLoading] = useState(true)
  const messagesEndRef = useRef(null)
  const statusRequestInFlight = useRef(false)

  // Check Ollama status on mount
  useEffect(() => {
    checkOllamaStatus({ initial: true })
    // Refresh status every 60 seconds and skip overlapping checks.
    const interval = setInterval(() => checkOllamaStatus({ initial: false }), 60000)
    return () => clearInterval(interval)
  }, [])

  const checkOllamaStatus = async ({ initial = false } = {}) => {
    if (statusRequestInFlight.current) {
      return
    }

    statusRequestInFlight.current = true
    try {
      const response = await cryptoAPI.ollamaStatus({ timeout: 4000 })
      setOllamaStatus({
        available: response.data.available,
        model: response.data.model,
        models: response.data.available_models
      })
    } catch (error) {
      if (initial) {
        console.warn('Could not fetch Ollama status:', error)
      }
      setOllamaStatus({ available: false, model: 'N/A' })
    } finally {
      statusRequestInFlight.current = false
      if (initial) {
        setStatusLoading(false)
      }
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMsg = inputValue

    // Add user message
    const userMessage = {
      id: messages.length + 1,
      text: userMsg,
      sender: 'user',
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setLoading(true)

    try {
      // Send to backend for AI processing
      const response = await cryptoAPI.sendChat(userMsg, 'crypto')

      // Add AI response
      const aiMessage = {
        id: messages.length + 2,
        text: response.data.response,
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage = {
        id: messages.length + 2,
        text: "Sorry, I encountered an error. Please try again. Make sure the backend is running.",
        sender: 'ai',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="header-title">
          <h3>🤖 CryptoAI Assistant</h3>
          <small>AI-powered cryptocurrency insights</small>
        </div>
        <div className="header-status">
          {statusLoading ? (
            <span className="status-badge loading">🔄 Checking...</span>
          ) : ollamaStatus.available ? (
            <span className="status-badge online">
              🟢 Ollama ({ollamaStatus.model})
            </span>
          ) : (
            <span className="status-badge offline">
              🔴 Ollama Offline (fallback mode)
            </span>
          )}
        </div>
      </div>

      <div className="chat-messages">
        {messages.map(msg => (
          <div key={msg.id} className={`message message-${msg.sender}`}>
            <div className="message-avatar">
              {msg.sender === 'ai' ? '🤖' : '😊'}
            </div>
            <div className="message-content">
              <div className="message-text">{msg.text}</div>
              <div className="message-time">
                {msg.timestamp.toLocaleTimeString([], { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </div>
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="message message-ai">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="message-text typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about your holdings, profile, prices, trends, or analysis... (Press Enter to send)"
          disabled={loading}
          rows="3"
        />
        <button 
          onClick={handleSendMessage} 
          disabled={loading || !inputValue.trim()}
          className="send-button"
        >
          {loading ? '⏳ Thinking...' : '📤 Send'}
        </button>
      </div>

      <div className="chat-footer">
        <small>💡 Tip: Ask about your portfolio, buying power, profile, Bitcoin, Ethereum, trends, alerts, or market analysis</small>
      </div>
    </div>
  )
}
