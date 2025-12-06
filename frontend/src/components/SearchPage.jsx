import React, { useState } from 'react'
import ResultsModal from './ResultsModal'
import './SearchPage.css'

const methodDisplayNames = {
  openalex: 'OpenAlex',
  openai: 'OpenAI (API-based)',
  nlp: 'NLP-based'
}

const SearchPage = () => {
  const [keywords, setKeywords] = useState([''])
  const [abstracts, setAbstracts] = useState([''])
  const [startDate, setStartDate] = useState('2018-01-01')
  const [endDate, setEndDate] = useState('2025-12-31')
  const [selectedMethod, setSelectedMethod] = useState(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [searchResults, setSearchResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleAddKeyword = () => {
    setKeywords([...keywords, ''])
  }

  const handleKeywordChange = (index, value) => {
    const newKeywords = [...keywords]
    newKeywords[index] = value
    setKeywords(newKeywords)
  }

  const handleRemoveKeyword = (index) => {
    if (keywords.length > 1) {
      const newKeywords = keywords.filter((_, i) => i !== index)
      setKeywords(newKeywords)
    }
  }

  const handleAddAbstract = () => {
    setAbstracts([...abstracts, ''])
  }

  const handleAbstractChange = (index, value) => {
    const newAbstracts = [...abstracts]
    newAbstracts[index] = value
    setAbstracts(newAbstracts)
  }

  const handleRemoveAbstract = (index) => {
    if (abstracts.length > 1) {
      const newAbstracts = abstracts.filter((_, i) => i !== index)
      setAbstracts(newAbstracts)
    }
  }

  const handleReset = () => {
    setKeywords([''])
    setAbstracts([''])
    setStartDate('2018-01-01')
    setEndDate('2025-12-31')
    setSelectedMethod(null)
    setSearchResults([])
  }

  const handleSearch = async (methodOverride = null) => {
      const activeMethod = methodOverride || selectedMethod || 'openalex'
      
      setIsLoading(true)
      setError(null)

      try {
        // Call Backend
        const response = await fetch('http://127.0.0.1:8000/api/works/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            keywords: keywords.filter(k => k.trim() !== ''),
            abstracts: abstracts.filter(a => a.trim() !== ''),
            start_date: startDate,
            end_date: endDate
          }),
        })

        if (!response.ok) throw new Error('Network response was not ok')

        const data = await response.json()

        // Map backend "title" to frontend "display_name"
        const formattedResults = data.results.map(item => ({
          ...item,
          display_name: item.title, 
        }))

        setSearchResults(formattedResults)
        
        if (!selectedMethod) setSelectedMethod(activeMethod)
        setIsModalOpen(true)

      } catch (err) {
        console.error("Search error:", err)
        setError("Failed to fetch results. Is the backend running?")
      } finally {
        setIsLoading(false)
      }
    }

  const handleMethodSelect = (method) => {
    setSelectedMethod(method)
    handleSearch(method)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
  }

  const activeKeywords = keywords.filter(k => k.trim() !== '')
  const activeAbstracts = abstracts.filter(a => a.trim() !== '')
  const dateRangeLabel = `${startDate} → ${endDate}`
  const selectedMethodLabel = selectedMethod ? methodDisplayNames[selectedMethod] : 'Not selected'

  return (
    <div className="search-page">
      <header className="search-header">
        <h1 className="page-title">Search Page</h1>
      </header>
      <main className="search-container">
        <div className="page-intro">
          <h2 className="main-heading">Research Paper Finder</h2>
          <p className="sub-heading">
            Provide a few keywords or drop in a reference abstract(s), narrow the timeline, then search for related papers.
          </p>
        </div>

        <div className="search-layout">
          <div className="search-parameters-card">
          <h3 className="card-title">Search Parameters</h3>
          
          {/* Keywords Section */}
          <div className="form-section">
            <label className="form-label">Keywords</label>
            <div className="input-group">
              {keywords.map((keyword, index) => (
                <div key={index} className="input-with-button">
                  <input
                    type="text"
                    className="form-input"
                    placeholder={index === 0 ? "e.g., graph neural networks, transformer retrieval" : "Add another keyword..."}
                    value={keyword}
                    onChange={(e) => handleKeywordChange(index, e.target.value)}
                  />
                  {keywords.length > 1 && (
                    <button
                      type="button"
                      className="remove-button"
                      onClick={() => handleRemoveKeyword(index)}
                      aria-label="Remove keyword"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                className="add-button"
                onClick={handleAddKeyword}
              >
                + Add keyword
              </button>
            </div>
          </div>

          {/* Abstracts Section */}
          <div className="form-section">
            <label className="form-label">Abstracts</label>
            <div className="input-group">
              {abstracts.map((abstract, index) => (
                <div key={index} className="textarea-with-button">
                  <textarea
                    className="form-textarea"
                    placeholder={index === 0 ? "Paste a paper abstract here..." : "Paste another abstract..."}
                    value={abstract}
                    onChange={(e) => handleAbstractChange(index, e.target.value)}
                    rows="4"
                  />
                  {abstracts.length > 1 && (
                    <button
                      type="button"
                      className="remove-button"
                      onClick={() => handleRemoveAbstract(index)}
                      aria-label="Remove abstract"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                className="add-button"
                onClick={handleAddAbstract}
              >
                + Add abstract
              </button>
            </div>
          </div>

          {/* Date Range Section */}
          <div className="form-section">
            <label className="form-label">Date range</label>
            <div className="date-range-group">
              <div className="date-input-group">
                <label className="date-label">Start:</label>
                <input
                  type="date"
                  className="date-input"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>
              <div className="date-input-group">
                <label className="date-label">End:</label>
                <input
                  type="date"
                  className="date-input"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Error Message Display (ADD THIS) */}
          {error && <div style={{color: 'red', marginBottom: '1rem'}}>{error}</div>}

          {/* Action Buttons (UPDATE THIS BLOCK) */}
          <div className="action-buttons">
            <button
              type="button"
              className="search-button"
              onClick={() => handleSearch()}
              disabled={isLoading} // Disable while loading
            >
              {isLoading ? 'Searching...' : 'Search'} 
            </button>
            <button
              type="button"
              className="reset-button"
              onClick={handleReset}
              disabled={isLoading}
            >
              Reset
            </button>
          </div>          
          </div>

          {/* Right-hand column */}
          <aside className="side-panel">
            {/* Method Selection */}
            <div className="method-selection">
              <p className="method-label">Choose method (opens results in a modal):</p>
              <div className="method-buttons">
                <button
                  type="button"
                  className={`method-button ${selectedMethod === 'openalex' ? 'active' : ''}`}
                  onClick={() => handleMethodSelect('openalex')}
                >
                  OpenAlex
                </button>
                <button
                  type="button"
                  className={`method-button ${selectedMethod === 'openai' ? 'active' : ''}`}
                  onClick={() => handleMethodSelect('openai')}
                >
                  OpenAI (API-based)
                </button>
                <button
                  type="button"
                  className={`method-button ${selectedMethod === 'nlp' ? 'active' : ''}`}
                  onClick={() => handleMethodSelect('nlp')}
                >
                  NLP-based
                </button>
              </div>
            </div>

            <div className="search-summary-card">
              <h4 className="summary-title">At a glance</h4>
              <div className="summary-row">
                <span className="summary-label">Keywords</span>
                <span className="summary-value">
                  {activeKeywords.length ? `${activeKeywords.length} added` : 'None yet'}
                </span>
              </div>
              <div className="summary-row">
                <span className="summary-label">Abstracts</span>
                <span className="summary-value">
                  {activeAbstracts.length ? `${activeAbstracts.length} added` : 'None yet'}
                </span>
              </div>
              <div className="summary-row">
                <span className="summary-label">Date range</span>
                <span className="summary-value">{dateRangeLabel}</span>
              </div>
              <div className="summary-row">
                <span className="summary-label">Method</span>
                <span className="summary-value">{selectedMethodLabel}</span>
              </div>
              {(activeKeywords.length > 0 || activeAbstracts.length > 0) && (
                <button
                  type="button"
                  className="summary-cta"
                  onClick={handleSearch}
                >
                  Run search now
                </button>
              )}
            </div>
          </aside>
        </div>
      </main>

      {/* Results Modal */}
      {isModalOpen && (
        <ResultsModal
          results={searchResults}
          method={selectedMethod || 'openalex'}
          onClose={handleCloseModal}
        />
      )}
    </div>
  )
}

export default SearchPage

