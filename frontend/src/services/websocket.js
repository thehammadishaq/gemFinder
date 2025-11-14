/**
 * WebSocket Service for Real-time Stock Prices
 */
// Derive WebSocket URL from API URL if VITE_WS_URL is not set
const getWebSocketURL = () => {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL
  }
  
  // Derive from API URL
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
  // Convert http:// to ws:// or https:// to wss://
  const wsUrl = apiUrl.replace(/^http/, 'ws')
  // Replace /api/v1 with /api/v1/ws
  return wsUrl.replace(/\/api\/v1$/, '/api/v1/ws')
}

const WS_BASE_URL = getWebSocketURL()

class StockWebSocket {
  constructor() {
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 1000
    this.messageHandlers = new Set()
    this.connected = false
  }

  connect() {
    try {
      const wsUrl = WS_BASE_URL + '/stock-prices'
      console.log('Attempting to connect to WebSocket:', wsUrl)
      this.ws = new WebSocket(wsUrl)
      
      this.ws.onopen = () => {
        console.log('WebSocket connected successfully')
        this.connected = true
        this.reconnectAttempts = 0
        this.onOpen()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('WebSocket message received:', data)
          this.handleMessage(data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error, event.data)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        console.error('WebSocket URL:', wsUrl)
        console.error('WebSocket readyState:', this.ws?.readyState)
        this.onError(error)
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        })
        this.connected = false
        this.onClose()
        // Only attempt reconnect if it wasn't a clean close
        if (event.code !== 1000) {
          this.attemptReconnect()
        }
      }
    } catch (error) {
      console.error('Error creating WebSocket connection:', error)
      this.attemptReconnect()
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
      this.connected = false
    }
  }

  subscribe(symbol) {
    if (this.connected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        symbol: symbol
      }))
    }
  }

  unsubscribe(symbol) {
    if (this.connected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        symbol: symbol
      }))
    }
  }

  addMessageHandler(handler) {
    this.messageHandlers.add(handler)
  }

  removeMessageHandler(handler) {
    this.messageHandlers.delete(handler)
  }

  handleMessage(data) {
    this.messageHandlers.forEach(handler => {
      try {
        handler(data)
      } catch (error) {
        console.error('Error in message handler:', error)
      }
    })
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
        this.connect()
      }, this.reconnectDelay * this.reconnectAttempts)
    } else {
      console.error('Max reconnection attempts reached')
    }
  }

  onOpen() {
    // Override in subclass or set handler
  }

  onClose() {
    // Override in subclass or set handler
  }

  onError(error) {
    // Override in subclass or set handler
  }
}

// Export singleton instance
export const stockWebSocket = new StockWebSocket()

