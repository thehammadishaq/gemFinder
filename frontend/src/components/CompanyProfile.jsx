import { useState, useEffect } from 'react'
import SectionCard from './SectionCard'
import { fetchFundamentalsFromGemini, fetchProfileFromYFinance, fetchProfileFromGemini, fetchProfileFromPolygon, fetchDataFromFinnhub } from '../services/api'
import { fetchYahooFinanceDirect } from '../services/yahooFinance'

function CompanyProfile({ data, ticker, onDataUpdate }) {
  const [activeDataSource, setActiveDataSource] = useState('Gemini') // Gemini, YahooFinance, Polygon, Finnhub
  const [activeMainSection, setActiveMainSection] = useState('Identity')
  const [activeSubSection, setActiveSubSection] = useState('What')
  const [fundamentalsLoading, setFundamentalsLoading] = useState(false)
  const [fundamentalsStatus, setFundamentalsStatus] = useState('')
  const [fundamentalsError, setFundamentalsError] = useState(null)
  const [geminiLoading, setGeminiLoading] = useState(false)
  const [geminiStatus, setGeminiStatus] = useState('')
  const [geminiError, setGeminiError] = useState(null)
  const [yfinanceLoading, setYfinanceLoading] = useState(false)
  const [yfinanceStatus, setYfinanceStatus] = useState('')
  const [yfinanceError, setYfinanceError] = useState(null)
  const [polygonLoading, setPolygonLoading] = useState(false)
  const [polygonStatus, setPolygonStatus] = useState('')
  const [polygonError, setPolygonError] = useState(null)
  const [finnhubLoading, setFinnhubLoading] = useState(false)
  const [finnhubStatus, setFinnhubStatus] = useState('')
  const [finnhubError, setFinnhubError] = useState(null)

  // Determine available data sources
  const availableSources = []
  if (data?.Gemini) availableSources.push('Gemini')
  if (data?.YahooFinance) availableSources.push('YahooFinance')
  if (data?.Polygon) availableSources.push('Polygon')
  if (data?.Finnhub) availableSources.push('Finnhub')
  if (availableSources.length === 0) {
    // Default to Gemini if no data exists
    availableSources.push('Gemini')
  }

  // Set default active source if current one doesn't exist
  useEffect(() => {
    if (!data?.[activeDataSource] && availableSources.length > 0) {
      setActiveDataSource(availableSources[0])
    }
  }, [data, activeDataSource, availableSources])

  // Get current source data
  const currentSourceData = data?.[activeDataSource] || {}

  // Identity sub-sections (moved from top tabs)
  const identitySections = {
    What: currentSourceData.What || {},
    When: currentSourceData.When || {},
    Where: currentSourceData.Where || {},
    How: currentSourceData.How || {},
    Who: currentSourceData.Who || {},
    Sources: currentSourceData.Sources || {}
  }

  // Main sections configuration
  const sidebarSections = [
    { key: 'Identity', label: 'Identity', hasSubSections: true },
    { key: 'Fundamentals', label: 'Fundamentals', hasSubSections: false },
    { key: 'Ratings', label: 'Ratings', hasSubSections: false },
    { key: 'News', label: 'News', hasSubSections: false },
    { key: 'Developments', label: 'Developments / Events / Catalyst', hasSubSections: false },
    { key: 'StockBehaviour', label: 'Stock Behaviour', hasSubSections: false }
  ]

  // Get data for current section
  const getSectionData = () => {
    if (activeMainSection === 'Identity') {
      return identitySections[activeSubSection] || {}
    }
    
    // Try multiple possible keys for each section
    const sectionMap = {
      Fundamentals: data?.Fundamentals || data?.fundamentals || {},
      Ratings: currentSourceData.Ratings || currentSourceData.ratings || {},
      News: currentSourceData.News || currentSourceData.news || {},
      Developments: currentSourceData.Developments || currentSourceData.Events || currentSourceData.Catalyst || currentSourceData.developments || currentSourceData.events || currentSourceData.catalyst || {},
      StockBehaviour: currentSourceData.StockBehaviour || currentSourceData['Stock Behaviour'] || currentSourceData.stockBehaviour || currentSourceData['stock behaviour'] || {}
    }
    
    return sectionMap[activeMainSection] || {}
  }

  const getSectionTitle = () => {
    if (activeMainSection === 'Identity') {
      return activeSubSection
    }
    return sidebarSections.find(s => s.key === activeMainSection)?.label || activeMainSection
  }

  const handleFetchFundamentals = async () => {
    if (!ticker) {
      setFundamentalsError('Ticker symbol is required')
      return
    }

    setFundamentalsLoading(true)
    setFundamentalsError(null)
    setFundamentalsStatus('Opening Gemini browser...')

    try {
      setFundamentalsStatus('Sending query to Gemini AI...')
      const result = await fetchFundamentalsFromGemini(ticker.toUpperCase(), true)
      
      setFundamentalsStatus('Fundamentals fetched successfully!')
      
      // Merge fundamentals data into existing data
      if (onDataUpdate && result.data) {
        const updatedData = {
          ...data,
          Fundamentals: result.data
        }
        onDataUpdate(updatedData)
      }
      
      setFundamentalsError(null)
      
      setTimeout(() => {
        setFundamentalsStatus('')
      }, 3000)
    } catch (err) {
      const errorMsg = err.message || 'Failed to fetch fundamentals from Gemini'
      setFundamentalsError(errorMsg)
      setFundamentalsStatus('Failed to fetch fundamentals')
      setTimeout(() => {
        setFundamentalsStatus('')
      }, 5000)
    } finally {
      setFundamentalsLoading(false)
    }
  }

  const handleFetchGemini = async () => {
    if (!ticker) {
      setGeminiError('Ticker symbol is required')
      return
    }

    setGeminiLoading(true)
    setGeminiError(null)
    setGeminiStatus('Opening Gemini browser...')

    try {
      setGeminiStatus('Sending query to Gemini AI...')
      const result = await fetchProfileFromGemini(ticker.toUpperCase(), true)
      
      setGeminiStatus('Profile fetched successfully from Gemini!')
      
      // Save Gemini data separately under "Gemini" key
      if (onDataUpdate && result.data) {
        const updatedData = {
          ...data,
          Gemini: result.data  // Save separately by source
        }
        onDataUpdate(updatedData)
        // Switch to Gemini source after fetching
        setActiveDataSource('Gemini')
      }
      
      setGeminiError(null)
      
      setTimeout(() => {
        setGeminiStatus('')
      }, 3000)
    } catch (err) {
      const errorMsg = err.message || 'Failed to fetch profile from Gemini'
      setGeminiError(errorMsg)
      setGeminiStatus('Failed to fetch profile')
      setTimeout(() => {
        setGeminiStatus('')
      }, 5000)
    } finally {
      setGeminiLoading(false)
    }
  }

  const handleFetchYFinance = async () => {
    if (!ticker) {
      setYfinanceError('Ticker symbol is required')
      return
    }

    setYfinanceLoading(true)
    setYfinanceError(null)
    setYfinanceStatus('Fetching from Yahoo Finance (Direct)...')

    try {
      setYfinanceStatus('Fetching company profile data directly from Yahoo Finance...')
      
      // Use direct frontend fetch instead of backend API
      const result = await fetchYahooFinanceDirect(ticker.toUpperCase())
      
      setYfinanceStatus('Profile fetched successfully from Yahoo Finance!')
      
      // Save Yahoo Finance data separately under "YahooFinance" key
      if (onDataUpdate && result.data) {
        console.log('🔍 [COMPONENT] Result data:', result.data)
        console.log('🔍 [COMPONENT] Result data.What:', result.data.What)
        console.log('🔍 [COMPONENT] Result data.What keys:', Object.keys(result.data.What || {}))
        
        const updatedData = {
          ...data,
          YahooFinance: result.data  // Save separately by source
        }
        
        console.log('🔍 [COMPONENT] Updated data.YahooFinance:', updatedData.YahooFinance)
        console.log('🔍 [COMPONENT] Updated data.YahooFinance.What:', updatedData.YahooFinance?.What)
        
        onDataUpdate(updatedData)
        // Switch to Yahoo Finance source after fetching
        setActiveDataSource('YahooFinance')
      }
      
      setYfinanceError(null)
      
      setTimeout(() => {
        setYfinanceStatus('')
      }, 3000)
    } catch (err) {
      const errorMsg = err.message || 'Failed to fetch profile from Yahoo Finance'
      setYfinanceError(errorMsg)
      setYfinanceStatus('Failed to fetch profile')
      setTimeout(() => {
        setYfinanceStatus('')
      }, 5000)
    } finally {
      setYfinanceLoading(false)
    }
  }

  const handleFetchPolygon = async () => {
    if (!ticker) {
      setPolygonError('Ticker symbol is required')
      return
    }

    setPolygonLoading(true)
    setPolygonError(null)
    setPolygonStatus('Fetching from Polygon.io...')

    try {
      setPolygonStatus('Fetching company profile data...')
      const result = await fetchProfileFromPolygon(ticker.toUpperCase(), true)
      
      setPolygonStatus('Profile fetched successfully from Polygon.io!')
      
      // Save Polygon data separately under "Polygon" key
      if (onDataUpdate && result.data) {
        const updatedData = {
          ...data,
          Polygon: result.data  // Save separately by source
        }
        onDataUpdate(updatedData)
        // Switch to Polygon source after fetching
        setActiveDataSource('Polygon')
      }
      
      setPolygonError(null)
      
      setTimeout(() => {
        setPolygonStatus('')
      }, 3000)
    } catch (err) {
      const errorMsg = err.message || 'Failed to fetch profile from Polygon.io'
      setPolygonError(errorMsg)
      setPolygonStatus('Failed to fetch profile')
      setTimeout(() => {
        setPolygonStatus('')
      }, 5000)
      } finally {
        setPolygonLoading(false)
      }
    }

    const handleFetchFinnhub = async () => {
      if (!ticker) {
        setFinnhubError('Ticker symbol is required')
        return
      }

      setFinnhubLoading(true)
      setFinnhubError(null)
      setFinnhubStatus('Fetching from Finnhub...')

      try {
        setFinnhubStatus('Fetching company data...')
        const result = await fetchDataFromFinnhub(ticker.toUpperCase(), true)
        
        setFinnhubStatus('Data fetched successfully from Finnhub!')
        
        // Save Finnhub data separately under "Finnhub" key
        if (onDataUpdate && result.data) {
          const updatedData = {
            ...data,
            Finnhub: result.data  // Save separately by source
          }
          onDataUpdate(updatedData)
          // Switch to Finnhub source after fetching
          setActiveDataSource('Finnhub')
        }
        
        setFinnhubError(null)
        
        setTimeout(() => {
          setFinnhubStatus('')
        }, 3000)
      } catch (err) {
        const errorMsg = err.message || 'Failed to fetch data from Finnhub'
        setFinnhubError(errorMsg)
        setFinnhubStatus('Failed to fetch data')
        setTimeout(() => {
          setFinnhubStatus('')
        }, 5000)
      } finally {
        setFinnhubLoading(false)
      }
    }

  return (
    <div className="mt-8 border border-black bg-white">
      <div className="border-b border-black px-6 py-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-black">
            Company Profile{ticker ? `: ${ticker}` : ''}
          </h2>
        </div>
      </div>

      {/* Data Sources Tab Bar */}
      <div className="border-b border-black bg-white">
        <div className="flex">
          <button
            className={`px-6 py-3 text-sm font-medium transition-colors border-r border-black ${
              activeDataSource === 'Gemini'
                ? 'bg-black text-white'
                : 'bg-white text-black hover:bg-black/5'
            } ${!data?.Gemini ? 'opacity-60' : ''}`}
            onClick={() => setActiveDataSource('Gemini')}
          >
            Gemini AI
            {data?.Gemini && <span className="ml-2 text-xs">●</span>}
          </button>
          <button
            className={`px-6 py-3 text-sm font-medium transition-colors border-r border-black ${
              activeDataSource === 'YahooFinance'
                ? 'bg-black text-white'
                : 'bg-white text-black hover:bg-black/5'
            } ${!data?.YahooFinance ? 'opacity-60' : ''}`}
            onClick={() => setActiveDataSource('YahooFinance')}
          >
            Yahoo Finance
            {data?.YahooFinance && <span className="ml-2 text-xs">●</span>}
          </button>
              <button
                className={`px-6 py-3 text-sm font-medium transition-colors border-r border-black ${
                  activeDataSource === 'Polygon'
                    ? 'bg-black text-white'
                    : 'bg-white text-black hover:bg-black/5'
                } ${!data?.Polygon ? 'opacity-60' : ''}`}
                onClick={() => setActiveDataSource('Polygon')}
              >
                Polygon.io
                {data?.Polygon && <span className="ml-2 text-xs">●</span>}
              </button>
              <button
                className={`px-6 py-3 text-sm font-medium transition-colors ${
                  activeDataSource === 'Finnhub'
                    ? 'bg-black text-white'
                    : 'bg-white text-black hover:bg-black/5'
                } ${!data?.Finnhub ? 'opacity-60' : ''}`}
                onClick={() => setActiveDataSource('Finnhub')}
              >
                Finnhub
                {data?.Finnhub && <span className="ml-2 text-xs">●</span>}
              </button>
            </div>
          </div>

      {/* Fetch Buttons for Data Sources */}
      <div className="border-b border-black bg-black/5 px-6 py-4">
        <div className="flex gap-4">
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-black">Gemini AI</p>
                <p className="text-xs text-black/70">Browser automation (30-60 seconds)</p>
              </div>
              <button
                className="px-4 py-2 bg-black text-white text-xs font-medium hover:bg-black/90 transition-colors disabled:bg-black/50 disabled:cursor-not-allowed"
                onClick={handleFetchGemini}
                disabled={geminiLoading || !ticker}
              >
                {geminiLoading ? 'Fetching...' : 'Fetch'}
              </button>
            </div>
            {geminiStatus && (
              <p className="text-xs text-black/70 mt-1">{geminiStatus}</p>
            )}
            {geminiError && (
              <p className="text-xs text-red-600 mt-1">{geminiError}</p>
            )}
          </div>
          <div className="w-px bg-black/20"></div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-black">Yahoo Finance</p>
                <p className="text-xs text-black/70">Direct Frontend (1-3 seconds)</p>
              </div>
              <button
                className="px-4 py-2 bg-black text-white text-xs font-medium hover:bg-black/90 transition-colors disabled:bg-black/50 disabled:cursor-not-allowed"
                onClick={handleFetchYFinance}
                disabled={yfinanceLoading || !ticker}
              >
                {yfinanceLoading ? 'Fetching...' : 'Fetch'}
              </button>
            </div>
            {yfinanceStatus && (
              <p className="text-xs text-black/70 mt-1">{yfinanceStatus}</p>
            )}
            {yfinanceError && (
              <p className="text-xs text-red-600 mt-1">{yfinanceError}</p>
            )}
          </div>
              <div className="w-px bg-black/20"></div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-black">Polygon.io</p>
                    <p className="text-xs text-black/70">Fast API (2-5 seconds)</p>
                  </div>
                  <button
                    className="px-4 py-2 bg-black text-white text-xs font-medium hover:bg-black/90 transition-colors disabled:bg-black/50 disabled:cursor-not-allowed"
                    onClick={handleFetchPolygon}
                    disabled={polygonLoading || !ticker}
                  >
                    {polygonLoading ? 'Fetching...' : 'Fetch'}
                  </button>
                </div>
                {polygonStatus && (
                  <p className="text-xs text-black/70 mt-1">{polygonStatus}</p>
                )}
                {polygonError && (
                  <p className="text-xs text-red-600 mt-1">{polygonError}</p>
                )}
              </div>
              <div className="w-px bg-black/20"></div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-black">Finnhub</p>
                    <p className="text-xs text-black/70">Fast API (3-8 seconds)</p>
                  </div>
                  <button
                    className="px-4 py-2 bg-black text-white text-xs font-medium hover:bg-black/90 transition-colors disabled:bg-black/50 disabled:cursor-not-allowed"
                    onClick={handleFetchFinnhub}
                    disabled={finnhubLoading || !ticker}
                  >
                    {finnhubLoading ? 'Fetching...' : 'Fetch'}
                  </button>
                </div>
                {finnhubStatus && (
                  <p className="text-xs text-black/70 mt-1">{finnhubStatus}</p>
                )}
                {finnhubError && (
                  <p className="text-xs text-red-600 mt-1">{finnhubError}</p>
                )}
              </div>
            </div>
          </div>

      <div className="flex min-h-[600px]">
        {/* Left Sidebar */}
        <div className="w-72 border-r border-black bg-white flex-shrink-0">
          <nav className="py-4">
            {sidebarSections.map((section) => (
              <div key={section.key}>
                <button
                  className={`w-full text-left px-6 py-3 text-sm font-medium transition-colors border-b border-black ${
                    activeMainSection === section.key
                      ? 'bg-black text-white'
                      : 'bg-white text-black hover:bg-black/5'
                  }`}
                  onClick={() => {
                    setActiveMainSection(section.key)
                    if (section.key === 'Identity') {
                      setActiveSubSection('What')
                    }
                  }}
                >
                  {section.label}
                </button>

                {/* Sub-sections for Identity */}
                {activeMainSection === 'Identity' && section.key === 'Identity' && (
                  <div className="bg-black/5 border-b border-black">
                    {Object.keys(identitySections).map((subSection) => (
                      <button
                        key={subSection}
                        className={`w-full text-left px-10 py-2.5 text-xs font-medium transition-colors border-b border-black/20 last:border-b-0 ${
                          activeSubSection === subSection
                            ? 'bg-black/10 text-black font-semibold border-l-2 border-l-black'
                            : 'bg-transparent text-black/70 hover:bg-black/5'
                        }`}
                        onClick={() => setActiveSubSection(subSection)}
                      >
                        {subSection}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </nav>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-auto">
          <div className="p-8">
            {/* Data Source Indicator */}
            {!currentSourceData || Object.keys(currentSourceData).length === 0 ? (
              <div className="mb-6 border border-black bg-black/5 p-4">
                <p className="text-sm text-black">
                    No data available from {activeDataSource === 'Gemini' ? 'Gemini AI' : activeDataSource === 'YahooFinance' ? 'Yahoo Finance' : activeDataSource === 'Polygon' ? 'Polygon.io' : 'Finnhub'}.
                  Click "Fetch" above to load data from this source.
                </p>
              </div>
            ) : (
              <div className="mb-4 text-xs text-black/70">
                    Viewing data from: <span className="font-medium">
                      {activeDataSource === 'Gemini' ? 'Gemini AI' : activeDataSource === 'YahooFinance' ? 'Yahoo Finance' : activeDataSource === 'Polygon' ? 'Polygon.io' : 'Finnhub'}
                    </span>
              </div>
            )}

            {/* Fundamentals Section with Fetch Button */}
            {activeMainSection === 'Fundamentals' && (
              <div className="mb-6 border border-black bg-black/5 p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-black mb-1">Fundamentals Data</h3>
                    <p className="text-sm text-black/70">
                      Fetch comprehensive fundamentals data from Gemini AI
                    </p>
                  </div>
                  <button
                    className="px-6 py-2 bg-black text-white text-sm font-medium hover:bg-black/90 transition-colors disabled:bg-black/50 disabled:cursor-not-allowed"
                    onClick={handleFetchFundamentals}
                    disabled={fundamentalsLoading || !ticker}
                  >
                    {fundamentalsLoading ? 'Fetching...' : 'Fetch from Gemini'}
                  </button>
                </div>
                
                {fundamentalsStatus && (
                  <div className={`p-3 border ${
                    fundamentalsStatus.includes('Failed') 
                      ? 'border-black bg-black/5' 
                      : 'border-black bg-black/5'
                  }`}>
                    <p className="text-sm text-black">{fundamentalsStatus}</p>
                  </div>
                )}
                
                {fundamentalsError && (
                  <div className="p-3 border border-black bg-black/5 mt-2">
                    <p className="text-sm text-black">{fundamentalsError}</p>
                  </div>
                )}
                
                {fundamentalsLoading && (
                  <div className="p-4 border border-black bg-black/5 mt-2">
                    <p className="text-sm text-black mb-2">{fundamentalsStatus || 'Fetching from Gemini AI...'}</p>
                    <p className="text-xs text-black/70">This may take 30-60 seconds. Browser window will open.</p>
                  </div>
                )}
              </div>
            )}
            
            <SectionCard 
              title={getSectionTitle()} 
              data={getSectionData()} 
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default CompanyProfile
