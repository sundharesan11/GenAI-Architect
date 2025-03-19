import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const api = axios.create({
  baseURL: 'http://localhost:8000/'
});

const UploadForm = () => {
  const [rawData, setRawData] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      console.log("Uploading URL:", rawData);
      const response = await api.post('/indexing', { url: rawData }, { headers: { 'Content-Type': 'application/json' } });
      console.log("Response received:", response);
      
      if (response.data) {
        setAnswer(response.data.url);
      } else {
        console.error("Unexpected response format:", response.data);
        setError("Could not upload the data provided.");
      }
    } catch (err) {
      console.error("Error details:", err);
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  
  return (
    <div className="qa-container">
      <div className="qa-card">
        <div className="qa-header">
          <h1 className="qa-title">RAG Website Upload</h1>
        </div>
        
        <div className="qa-content">
          <form onSubmit={handleSubmit} className="qa-form">
            <div className="qa-input-group">
              <input
                type="text"
                value={rawData}
                onChange={(e) => setRawData(e.target.value)}
                placeholder="Paste the URL..."
                className="qa-input"
                required
              />
              
              <button
                type="submit"
                disabled={loading}
                className="qa-button"
              >
                {loading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </form>
          
          {error && (
            <div className="qa-error">
              {error}
            </div>
          )}
          
          {loading && (
            <div className="qa-loading">
              <div className="qa-spinner"></div>
              <span className="qa-loading-text">Uploading the contents...</span>
            </div>
          )}

          {!loading && (answer) && (
            <div className="qa-results">
              <div className="qa-result-card">
                <h2 className="qa-result-title">Answer</h2>
                <div className="qa-result-content">
                  {answer ? (
                    <p>{answer}</p>
                  ) : (
                    <p className="qa-empty-text">Data couldn't be uploaded!</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UploadForm;