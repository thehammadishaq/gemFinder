import { useState, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { fetchSupplyChainFromGemini } from '../services/api'

// Helper function to resolve API base URL (same logic as API service)
const resolveApiBaseUrl = () => {
  // Priority 1: Use VITE_API_URL from environment variable
  if (import.meta.env.VITE_API_URL) {
    const url = import.meta.env.VITE_API_URL.replace(/\/$/, '')
    return url
  }

  // Priority 2: In production, use window.location.origin (behind proxy)
  if (typeof window !== 'undefined' && window.location?.origin && import.meta.env.PROD) {
    return `${window.location.origin.replace(/\/$/, '')}/api/v1`
  }

  // Priority 3: Development fallback - always use port 9000
  return 'http://localhost:9000/api/v1'
}

function SupplyChainGraph({ ticker, existingData, onDataUpdate, onGraphModalOpen }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [supplyChainData, setSupplyChainData] = useState(existingData || null)
  const [graphUrl, setGraphUrl] = useState(null)
  const [showGraphModal, setShowGraphModal] = useState(false)

  // Expose function to open modal
  const openGraphModal = useCallback(() => {
    if (graphUrl) {
      console.log('[SupplyChainGraph] Opening modal with URL:', graphUrl)
      setShowGraphModal(true)
      if (onGraphModalOpen) {
        onGraphModalOpen()
      }
    } else {
      console.error('[SupplyChainGraph] Graph URL is not set. Cannot open modal.')
      setError('Graph URL is not available. Please fetch the supply chain data first.')
    }
  }, [graphUrl, onGraphModalOpen])

  // Expose openGraphModal via useEffect to parent
  useEffect(() => {
    // Store the function reference globally so parent can call it
    window.supplyChainOpenGraph = openGraphModal
    return () => {
      delete window.supplyChainOpenGraph
    }
  }, [openGraphModal])

  const handleFetchSupplyChain = async () => {
    if (!ticker || !ticker.trim()) {
      setError('Please enter a ticker symbol')
      return
    }

    setLoading(true)
    setError(null)
    setSupplyChainData(null)
    setGraphUrl(null)

    try {
      const response = await fetchSupplyChainFromGemini(ticker.toUpperCase(), true, true)
      setSupplyChainData(response.data)
      
      // Use new server-side endpoint for graph
      if (ticker) {
        const apiBaseUrl = resolveApiBaseUrl()
        const fullUrl = `${apiBaseUrl}/supply-chain/graph/${ticker.toUpperCase()}`
        console.log('[SupplyChainGraph] Setting graph URL (server-side endpoint):', fullUrl)
        setGraphUrl(fullUrl)
      } else if (response.graph_url) {
        // Fallback: use static file URL if endpoint not available
        const apiBaseUrl = resolveApiBaseUrl()
        const baseUrl = apiBaseUrl.replace('/api/v1', '')
        const graphPath = response.graph_url.startsWith('/') ? response.graph_url : `/${response.graph_url}`
        const fullUrl = `${baseUrl}${graphPath}`
        console.log('[SupplyChainGraph] Setting graph URL (fallback static):', fullUrl)
        setGraphUrl(fullUrl)
      } else if (response.graph_file) {
        // Fallback: construct URL from file path
        const apiBaseUrl = resolveApiBaseUrl()
        const baseUrl = apiBaseUrl.replace('/api/v1', '')
        const filename = response.graph_file.split('/').pop() || response.graph_file.split('\\').pop()
        const fullUrl = `${baseUrl}/supply-chain-graphs/${filename}`
        console.log('[SupplyChainGraph] Setting graph URL (from file):', fullUrl)
        setGraphUrl(fullUrl)
      }
      
      if (onDataUpdate) {
        onDataUpdate(response.data)
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch supply chain data')
      console.error('Supply chain fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  // Load existing data from props (database) when it changes
  useEffect(() => {
    if (existingData) {
      // Update with existing data from database
      setSupplyChainData(existingData)
      // Use new server-side endpoint for graph (generates HTML from MongoDB data)
      if (ticker) {
        const apiBaseUrl = resolveApiBaseUrl()
        const fullUrl = `${apiBaseUrl}/supply-chain/graph/${ticker.toUpperCase()}`
        console.log('[SupplyChainGraph] Setting graph URL (from existing data, server-side):', fullUrl)
        setGraphUrl(fullUrl)
      }
    }
  }, [existingData, ticker])

  // Auto-fetch only if no existing data and ticker is provided
  useEffect(() => {
    if (ticker && ticker.trim() && !existingData && !supplyChainData && !loading) {
      // Only auto-fetch if no existing data from database
      // Don't auto-fetch - let user click fetch button
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticker])

  // Don't render anything if no data and not loading
  if (!supplyChainData && !loading && !error) {
    return null
  }

  const graphModal = showGraphModal && graphUrl && typeof document !== 'undefined'
    ? createPortal(
        <div 
          className="fixed inset-0 bg-black/90 flex items-center justify-center z-50"
          onClick={() => setShowGraphModal(false)}
        >
          <div 
            className="bg-black border-2 border-green-500 w-[95vw] h-[95vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="border-b border-green-500 p-4 bg-black flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-green-500">Interactive Supply Chain Graph</h3>
                <p className="text-xs text-green-500/70 mt-1">
                  {ticker} - Drag nodes to explore, zoom with mouse wheel
                </p>
              </div>
              <button
                onClick={() => setShowGraphModal(false)}
                className="px-4 py-2 bg-green-500 text-black font-bold hover:bg-green-400 transition-colors"
              >
                Close
              </button>
            </div>
            
            {/* Graph Container */}
            <div className="flex-1 overflow-hidden relative">
              <iframe
                src={graphUrl}
                title="Supply Chain Graph"
                className="w-full h-full border-0"
                style={{ minHeight: '100%' }}
                onError={(e) => {
                  console.error('[SupplyChainGraph] Iframe load error:', e)
                }}
                onLoad={() => {
                  console.log('[SupplyChainGraph] Iframe loaded successfully:', graphUrl)
                }}
              />
              {graphUrl && (
                <div className="absolute bottom-2 left-2 flex flex-col gap-1">
                  <div className="text-xs text-green-500/70 bg-black/50 px-2 py-1 rounded">
                    URL: {graphUrl}
                  </div>
                  <a
                    href={graphUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-green-500 bg-black/50 px-2 py-1 rounded hover:bg-black/70 transition-colors"
                  >
                    Open in New Tab
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>,
        document.body
      )
    : null

  return (
    <>
      <div className="border border-black bg-white">
        <div className="p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700">
              <p className="font-medium">Error: {error}</p>
            </div>
          )}

          {loading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
              <p className="mt-4 text-sm text-gray-600">
                Fetching supply chain data from Gemini AI... This may take a few minutes.
              </p>
            </div>
          )}

        </div>
      </div>
      {graphModal}
    </>
  )
}

export default SupplyChainGraph

