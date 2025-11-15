/**
 * API Service for Backend Communication
 */
// Resolve API base URL with sensible defaults for production deployments behind proxies
const resolveApiBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL.replace(/\/$/, '')
  }

  if (typeof window !== 'undefined' && window.location?.origin) {
    return `${window.location.origin.replace(/\/$/, '')}/api/v1`
  }

  // Development fallback
  return 'http://localhost:9000/api/v1'
}

const API_BASE_URL = resolveApiBaseUrl()

/**
 * Upload a JSON file to the backend
 */
export const uploadProfile = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/profiles/upload`, {
    method: 'POST',
    body: formData
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to upload profile')
  }

  return await response.json()
}

/**
 * Get all company profiles
 */
export const getAllProfiles = async (skip = 0, limit = 100) => {
  const response = await fetch(`${API_BASE_URL}/profiles/?skip=${skip}&limit=${limit}`)

  if (!response.ok) {
    throw new Error('Failed to fetch profiles')
  }

  return await response.json()
}

/**
 * Get profile by ID
 */
export const getProfileById = async (id) => {
  const response = await fetch(`${API_BASE_URL}/profiles/${id}`)

  if (!response.ok) {
    throw new Error('Profile not found')
  }

  return await response.json()
}

/**
 * Get profile by ticker
 */
export const getProfileByTicker = async (ticker) => {
  const response = await fetch(`${API_BASE_URL}/profiles/ticker/${ticker}`)

  if (!response.ok) {
    throw new Error('Profile not found')
  }

  return await response.json()
}

/**
 * Search profiles by query
 */
export const searchProfiles = async (query) => {
  if (!query || !query.trim()) {
    throw new Error('Search query is required')
  }

  const response = await fetch(`${API_BASE_URL}/profiles/search/${encodeURIComponent(query.trim())}`)

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Search failed' }))
    throw new Error(error.detail || 'Search failed')
  }

  const results = await response.json()
  // Backend returns array directly, ensure it's always an array
  return Array.isArray(results) ? results : []
}

/**
 * Delete profile
 */
export const deleteProfile = async (id) => {
  const response = await fetch(`${API_BASE_URL}/profiles/${id}`, {
    method: 'DELETE'
  })

  if (!response.ok) {
    throw new Error('Failed to delete profile')
  }

  return await response.json()
}

/**
 * Create profile manually
 */
export const createProfile = async (ticker, data) => {
  const response = await fetch(`${API_BASE_URL}/profiles/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      ticker,
      data
    })
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to create profile')
  }

  return await response.json()
}

/**
 * Fetch company profile from Gemini AI
 */
export const fetchProfileFromGemini = async (ticker, saveToDb = true) => {
  const response = await fetch(`${API_BASE_URL}/gemini/fetch-profile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      ticker: ticker.toUpperCase(),
      save_to_db: saveToDb
    })
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch profile from Gemini')
  }

  return await response.json()
}

/**
 * Fetch company profile from Gemini AI (GET method)
 */
export const fetchProfileFromGeminiGet = async (ticker, saveToDb = true) => {
  const response = await fetch(
    `${API_BASE_URL}/gemini/fetch-profile/${ticker.toUpperCase()}?save_to_db=${saveToDb}`
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch profile from Gemini')
  }

  return await response.json()
}

/**
 * Fetch fundamentals from Gemini AI
 */
export const fetchFundamentalsFromGemini = async (ticker, saveToDb = true) => {
  const response = await fetch(`${API_BASE_URL}/fundamentals/fetch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      ticker: ticker.toUpperCase(),
      save_to_db: saveToDb
    })
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch fundamentals from Gemini')
  }

  return await response.json()
}

/**
 * Fetch fundamentals from Gemini AI (GET method)
 */
export const fetchFundamentalsFromGeminiGet = async (ticker, saveToDb = true) => {
  const response = await fetch(
    `${API_BASE_URL}/fundamentals/fetch/${ticker.toUpperCase()}?save_to_db=${saveToDb}`
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch fundamentals from Gemini')
  }

  return await response.json()
}

/**
 * Fetch company profile from Yahoo Finance
 */
export const fetchProfileFromYFinance = async (ticker, saveToDb = true) => {
  const response = await fetch(`${API_BASE_URL}/yfinance/fetch-data`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      ticker: ticker.toUpperCase(),
      save_to_db: saveToDb
    })
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch profile from Yahoo Finance')
  }

  return await response.json()
}

/**
 * Fetch company profile from Yahoo Finance (GET method)
 */
export const fetchProfileFromYFinanceGet = async (ticker, saveToDb = true) => {
  const response = await fetch(
    `${API_BASE_URL}/yfinance/fetch-data/${ticker.toUpperCase()}?save_to_db=${saveToDb}`
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch profile from Yahoo Finance')
  }

  return await response.json()
}

/**
 * Fetch company profile from Polygon.io
 */
export const fetchProfileFromPolygon = async (ticker, saveToDb = true) => {
  const response = await fetch(`${API_BASE_URL}/polygon/fetch-profile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      ticker: ticker.toUpperCase(),
      save_to_db: saveToDb
    })
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch profile from Polygon.io')
  }

  return await response.json()
}

  /**
   * Fetch company profile from Polygon.io (GET method)
   */
  export const fetchProfileFromPolygonGet = async (ticker, saveToDb = true) => {
    const response = await fetch(
      `${API_BASE_URL}/polygon/fetch-profile/${ticker.toUpperCase()}?save_to_db=${saveToDb}`
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch profile from Polygon.io')
    }

    return await response.json()
  }

  /**
   * Fetch data from Finnhub
   */
  export const fetchDataFromFinnhub = async (ticker, saveToDb = true) => {
    const response = await fetch(`${API_BASE_URL}/finnhub/fetch-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ticker: ticker.toUpperCase(),
        save_to_db: saveToDb
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch data from Finnhub')
    }

    return await response.json()
  }

  /**
   * Fetch data from Finnhub (GET method)
   */
  export const fetchDataFromFinnhubGet = async (ticker, saveToDb = true) => {
    const response = await fetch(
      `${API_BASE_URL}/finnhub/fetch-data/${ticker.toUpperCase()}?save_to_db=${saveToDb}`
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch data from Finnhub')
    }

    return await response.json()
  }

  /**
   * Get quote (price) for a symbol - works even when market is closed
   */
  export const getQuote = async (symbol) => {
    const response = await fetch(`${API_BASE_URL}/finnhub/quote/${symbol.toUpperCase()}`)

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch quote')
    }

    return await response.json()
  }

  /**
   * Get quotes for multiple symbols
   */
  export const getMultipleQuotes = async (symbols) => {
    const response = await fetch(`${API_BASE_URL}/finnhub/quotes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(symbols)
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch quotes')
    }

    return await response.json()
  }

