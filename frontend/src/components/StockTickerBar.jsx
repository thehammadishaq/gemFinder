import { useState, useEffect, useRef } from 'react'
import { stockWebSocket } from '../services/websocket'
import { getMultipleQuotes } from '../services/api'

function StockTickerBar() {
  const [stocks, setStocks] = useState(new Map())
  const [isConnected, setIsConnected] = useState(false)
  const containerRef = useRef(null)
  const animationRef = useRef(null)

  // Top 25 US Stocks to track
  const defaultSymbols = [
    'AAPL',   // 1
    'MSFT',   // 2
    'NVDA',   // 3
    'GOOGL',  // 4
    'GOOG',   // 5
    'AMZN',   // 6
    'META',   // 7
    'BRK.B',  // 8
    'TSLA',   // 9
    'AVGO',   // 10
    'UNH',    // 11
    'JNJ',    // 12
    'V',      // 13
    'WMT',    // 14
    'MA',     // 15
    'HD',     // 16
    'PG',     // 17
    'DIS',    // 18
    'NKE',    // 19
    'JPM',    // 20
    'BAC',    // 21
    'XOM',    // 22
    'CVX',    // 23
    'KO',     // 24
    'MRK'     // 25
  ]

  useEffect(() => {
    // Initialize stocks with default symbols
    const initialStocks = new Map()
    defaultSymbols.forEach(symbol => {
      initialStocks.set(symbol, {
        symbol,
        price: null,
        previousPrice: null,
        change: null,
        changePercent: null,
        volume: 0,
        timestamp: null
      })
    })
    setStocks(initialStocks)

    // Track if we should use quotes (fallback mode)
    let useQuotesFallback = false
    let quoteTimeout = null
    let websocketCheckTimeout = null

    // Set up WebSocket message handler
    const handleMessage = (data) => {
      console.log('TickerBar received message:', data)
      
      if (data.type === 'trade' && data.data && Array.isArray(data.data)) {
        data.data.forEach(trade => {
          const symbol = trade.s
          const price = trade.p
          const volume = trade.v || 0
          const timestamp = trade.t

          setStocks(prevStocks => {
            const newStocks = new Map(prevStocks)
            const existing = newStocks.get(symbol) || {
              symbol,
              price: null,
              previousPrice: null,
              change: null,
              changePercent: null,
              volume: 0,
              timestamp: null
            }

            const previousPrice = existing.price || price
            const change = price - previousPrice
            const changePercent = previousPrice ? ((change / previousPrice) * 100) : 0

            newStocks.set(symbol, {
              symbol,
              price,
              previousPrice,
              change,
              changePercent,
              volume: volume + (existing.volume || 0),
              timestamp
            })

            return newStocks
          })
        })
      } else if (data.type === 'subscribed') {
        console.log(`Subscribed to ${data.symbol}`)
      } else if (data.type === 'error') {
        console.error('WebSocket error:', data.message)
        setIsConnected(false)
        // If WebSocket fails, switch to quotes fallback
        if (!useQuotesFallback) {
          useQuotesFallback = true
          fetchQuotesFallback()
        }
      } else if (data.type === 'ping' || data.type === 'pong') {
        // Ignore ping/pong messages
        return
      } else {
        console.log('Unknown message type:', data.type, data)
      }
    }

    stockWebSocket.addMessageHandler(handleMessage)

    // Fetch quotes as fallback (when WebSocket fails)
    const fetchQuotesFallback = async () => {
      // Only fetch if we're in fallback mode or WebSocket is not connected
      if (useQuotesFallback || !stockWebSocket.connected) {
        try {
          console.log('📊 Fetching quotes as fallback for', defaultSymbols.length, 'symbols...')
          const quotes = await getMultipleQuotes(defaultSymbols)
          console.log('📊 Quotes received:', Object.keys(quotes).length, 'symbols')
          
          setStocks(prevStocks => {
            const newStocks = new Map(prevStocks)
            
            Object.entries(quotes).forEach(([symbol, quoteData]) => {
              if (quoteData) {
                // Finnhub quote format: c = current price, pc = previous close, h = high, l = low, o = open, t = timestamp
                const price = quoteData.c  // current price
                const previousClose = quoteData.pc  // previous close
                
                if (price !== null && price !== undefined && price !== 0) {
                  const change = previousClose ? (price - previousClose) : 0
                  const changePercent = previousClose && previousClose !== 0 ? ((change / previousClose) * 100) : 0
                  
                  newStocks.set(symbol, {
                    symbol,
                    price,
                    previousPrice: previousClose || price,
                    change,
                    changePercent,
                    volume: quoteData.v || 0, // v = volume
                    timestamp: quoteData.t || Date.now() // t = timestamp
                  })
                }
              }
            })
            
            console.log('📊 Updated stocks:', newStocks.size, 'symbols with data')
            return newStocks
          })
          console.log('📊 Quotes fallback processed successfully')
        } catch (error) {
          console.error('❌ Failed to fetch quotes fallback:', error)
        }
      }
    }

    // Connect to WebSocket
    stockWebSocket.onOpen = () => {
      console.log('✅ WebSocket connected successfully - using real-time data')
      setIsConnected(true)
      useQuotesFallback = false // Don't use quotes if WebSocket is connected
      
      // Cancel quote fallback timeout if it was scheduled
      if (quoteTimeout) {
        clearTimeout(quoteTimeout)
        quoteTimeout = null
      }
      
      // Cancel WebSocket check timeout since we're connected
      if (websocketCheckTimeout) {
        clearTimeout(websocketCheckTimeout)
        websocketCheckTimeout = null
      }
      
      // Subscribe to default symbols
      defaultSymbols.forEach(symbol => {
        stockWebSocket.subscribe(symbol)
      })
    }

    stockWebSocket.onClose = () => {
      console.log('⚠️ WebSocket disconnected - switching to quotes fallback')
      setIsConnected(false)
      
      // If WebSocket disconnects, switch to quotes fallback
      if (!useQuotesFallback) {
        useQuotesFallback = true
        fetchQuotesFallback()
      }
    }

    stockWebSocket.onError = (error) => {
      console.error('❌ WebSocket error:', error)
      setIsConnected(false)
      
      // If WebSocket errors, switch to quotes fallback
      if (!useQuotesFallback) {
        useQuotesFallback = true
        fetchQuotesFallback()
      }
    }

    // Step 1: Try WebSocket first
    console.log('🔄 Attempting WebSocket connection...')
    stockWebSocket.connect()

    // Step 2: Wait 5 seconds to see if WebSocket connects
    // If not connected after 5 seconds, use quotes as fallback
    websocketCheckTimeout = setTimeout(() => {
      // Check actual WebSocket connection status, not state (state might not be updated yet)
      if (!stockWebSocket.connected && !useQuotesFallback) {
        console.log('⏱️ WebSocket did not connect within 5 seconds - using quotes fallback')
        useQuotesFallback = true
        fetchQuotesFallback()
      }
    }, 5000) // Wait 5 seconds

    // Cleanup
    return () => {
      if (quoteTimeout) {
        clearTimeout(quoteTimeout)
      }
      if (websocketCheckTimeout) {
        clearTimeout(websocketCheckTimeout)
      }
      stockWebSocket.removeMessageHandler(handleMessage)
      stockWebSocket.disconnect()
    }
  }, [])

  // Set up CSS animation for infinite scrolling
  useEffect(() => {
    if (!containerRef.current) return

    const content = containerRef.current.querySelector('.ticker-content')
    if (!content) return

    // Wait for content to render and calculate width
    const setupAnimation = () => {
      const contentWidth = content.scrollWidth
      
      if (contentWidth === 0) {
        setTimeout(setupAnimation, 100)
        return
      }

      // Calculate width of one set (we have 4 copies)
      const singleSetWidth = contentWidth / 4
      
      if (singleSetWidth === 0 || !isFinite(singleSetWidth)) {
        setTimeout(setupAnimation, 100)
        return
      }

      // Set CSS custom property for animation
      content.style.setProperty('--ticker-width', `${singleSetWidth}px`)
      content.classList.add('ticker-animate')
    }

    const timeoutId = setTimeout(setupAnimation, 100)

    return () => {
      clearTimeout(timeoutId)
      if (content) {
        content.classList.remove('ticker-animate')
      }
    }
  }, [stocks])

  const formatPrice = (price) => {
    if (price === null || price === undefined) return '--'
    return price.toFixed(2)
  }

  const formatChange = (change) => {
    if (change === null || change === undefined) return '--'
    const sign = change >= 0 ? '+' : ''
    return `${sign}${change.toFixed(2)}`
  }

  const formatChangePercent = (percent) => {
    if (percent === null || percent === undefined) return '--'
    const sign = percent >= 0 ? '+' : ''
    return `${sign}${percent.toFixed(2)}%`
  }

  const getChangeColor = (change) => {
    if (change === null || change === undefined) return 'text-gray-600'
    return change >= 0 ? 'text-green-600' : 'text-red-600'
  }

  // Filter to only show the 5 stocks we're tracking, and ensure all 5 are present
  const stockArray = defaultSymbols.map(symbol => {
    const stock = stocks.get(symbol)
    return stock || {
      symbol,
      price: null,
      previousPrice: null,
      change: null,
      changePercent: null,
      volume: 0,
      timestamp: null
    }
  })

  return (
    <div className="w-full bg-black text-white py-2 overflow-hidden relative">
      {/* Connection status indicator */}
      <div className="absolute top-1 right-4 z-10 flex items-center gap-2 text-xs">
        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
        <span>{isConnected ? 'Live' : 'Connecting...'}</span>
      </div>

      {/* Ticker bar */}
      <div ref={containerRef} className="w-full overflow-hidden relative">
        <div 
          className="ticker-content flex items-center gap-8 whitespace-nowrap"
          style={{ 
            display: 'inline-flex', 
            willChange: 'transform',
            width: 'max-content'
          }}
        >
          {/* Create 4 copies for seamless infinite loop */}
          {[...stockArray, ...stockArray, ...stockArray, ...stockArray].map((stock, index) => (
            <div
              key={`${stock.symbol}-${index}`}
              className="ticker-item flex items-center gap-4 px-4 flex-shrink-0"
            >
              <span className="font-bold text-sm">{stock.symbol}</span>
              <span className="text-sm">${formatPrice(stock.price)}</span>
              <span className={`text-sm font-medium ${getChangeColor(stock.change)}`}>
                {formatChange(stock.change)}
              </span>
              <span className={`text-sm font-medium ${getChangeColor(stock.change)}`}>
                ({formatChangePercent(stock.changePercent)})
              </span>
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}

export default StockTickerBar

