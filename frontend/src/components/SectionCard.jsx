function SectionCard({ title, data }) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div>
        <h3 className="text-xl font-bold text-black mb-4">{title}</h3>
        <p className="text-black/70">No data available for this section</p>
      </div>
    )
  }

  // Track depth to prevent infinite recursion
  const renderValue = (value, depth = 0) => {
    // Prevent infinite recursion (max depth 10)
    if (depth > 10) {
      return <span className="text-black/70 italic">[Deep nesting - data too complex to display]</span>
    }

    // Handle null or undefined
    if (value === null || value === undefined) {
      return <span className="text-black/50 italic">null</span>
    }

    // Handle arrays
    if (Array.isArray(value)) {
      if (value.length === 0) {
        return <span className="text-black/50 italic">Empty array</span>
      }
      
      // If array contains objects, render as table-like structure
      if (value.length > 0 && typeof value[0] === 'object' && value[0] !== null) {
        return (
          <div className="mt-2 space-y-4">
            {value.map((item, index) => (
              <div key={index} className="border border-black/20 p-3 bg-black/5">
                {typeof item === 'object' && item !== null ? (
                  <div className="space-y-2">
                    {Object.entries(item).map(([key, val]) => (
                      <div key={key} className="text-sm">
                        <span className="font-semibold text-black">{key}:</span>{' '}
                        <span className="text-black">{renderValue(val, depth + 1)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="text-black">{String(item)}</span>
                )}
              </div>
            ))}
          </div>
        )
      }
      
      // Simple array of primitives
      return (
        <ul className="list-disc list-inside space-y-1 ml-4">
          {value.map((item, index) => (
            <li key={index} className="text-black">
              {typeof item === 'string' && (item.startsWith('http') || item.startsWith('https')) ? (
                <a href={item} target="_blank" rel="noopener noreferrer" className="text-black underline hover:text-black/70 break-all">
                  {item}
                </a>
              ) : (
                String(item)
              )}
            </li>
          ))}
        </ul>
      )
    }
    
    // Handle objects
    if (typeof value === 'object' && value !== null) {
      const entries = Object.entries(value)
      if (entries.length === 0) {
        return <span className="text-black/50 italic">Empty object</span>
      }
      
      return (
        <div className="ml-4 space-y-2 border-l-2 border-black/30 pl-4 mt-2">
          {entries.map(([key, val]) => (
            <div key={key} className="text-black">
              <strong className="font-semibold">{key}:</strong>{' '}
              <span>{renderValue(val, depth + 1)}</span>
            </div>
          ))}
        </div>
      )
    }
    
    // Handle URLs
    if (typeof value === 'string' && (value.startsWith('http') || value.startsWith('https'))) {
      return (
        <a href={value} target="_blank" rel="noopener noreferrer" className="text-black underline hover:text-black/70 break-all">
          {value}
        </a>
      )
    }
    
    // Handle numbers
    if (typeof value === 'number') {
      // Format large numbers
      if (value > 1000000) {
        return <span className="text-black">{value.toLocaleString()}</span>
      }
      return <span className="text-black">{value}</span>
    }
    
    // Handle booleans
    if (typeof value === 'boolean') {
      return <span className="text-black">{value ? 'true' : 'false'}</span>
    }
    
    // Handle strings
    return <span className="text-black">{String(value)}</span>
  }

  const renderField = (key, value) => {
    try {
      return (
        <div key={key} className="border-b border-black pb-4 last:border-b-0">
          <div className="text-sm font-semibold text-black mb-2 uppercase tracking-wide">{key}</div>
          <div className="text-black">{renderValue(value)}</div>
        </div>
      )
    } catch (err) {
      console.error(`Error rendering field ${key}:`, err)
      return (
        <div key={key} className="border-b border-black pb-4 last:border-b-0">
          <div className="text-sm font-semibold text-black mb-2 uppercase tracking-wide">{key}</div>
          <div className="text-red-600 text-sm">Error displaying this field: {err.message}</div>
        </div>
      )
    }
  }

  try {
    return (
      <div>
        <h3 className="text-xl font-bold text-black mb-6">{title}</h3>
        <div className="space-y-6">
          {Object.entries(data).map(([key, value]) => renderField(key, value))}
        </div>
      </div>
    )
  } catch (err) {
    console.error('Error rendering SectionCard:', err)
    return (
      <div>
        <h3 className="text-xl font-bold text-black mb-4">{title}</h3>
        <div className="p-4 border border-red-500 bg-red-50">
          <p className="text-red-600 font-medium">Error rendering section data</p>
          <p className="text-red-500 text-sm mt-1">{err.message}</p>
        </div>
      </div>
    )
  }
}

export default SectionCard
