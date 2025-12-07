import React from 'react'
import './ResultsModal.css'

const ResultsModal = ({ results, method, onClose }) => {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Search Results</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <p className="method-indicator">Method: <strong>{method}</strong></p>
          <div className="results-list">
            {results.length === 0 ? (
              <p className="no-results">No results found.</p>
            ) : (
              results.map((result) => (
                <div key={result.id} className="result-item">
                  <h3 className="result-title">{result.display_name}</h3>
                  <div className="result-meta">
                    {result.publication_year && (
                      <span className="result-year">Year: {result.publication_year}</span>
                    )}
                    {result.authorships && result.authorships.length > 0 && (
                      <span className="result-authors">
                        Authors: {result.authorships.map(a => a.author?.display_name || 'Unknown').join(', ')}
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
        <div className="modal-footer">
          <button className="modal-button" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}

export default ResultsModal

