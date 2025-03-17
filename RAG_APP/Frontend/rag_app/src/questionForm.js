import React, { useState } from 'react';
import axios from 'axios';
import './App.css'; // Import the CSS file

const api = axios.create({
  baseURL: 'http://localhost:8000/'
});

const QuestionForm = () => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [document, setDocument] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      console.log("Submitting question:", question);
      const response = await api.post('/chat', { message: question });
      console.log("Response received:", response);
      
      if (response.data && response.data.Answer) {
        setAnswer(response.data.Answer);
        setDocument(response.data.Documents || response.data.Document || '');
      } else {
        console.error("Unexpected response format:", response.data);
        setError("Received response but couldn't find an answer in the expected format.");
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
          <h1 className="qa-title">RAG Question Answering System</h1>
        </div>
        
        <div className="qa-content">
          <form onSubmit={handleSubmit} className="qa-form">
            <div className="qa-input-group">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question..."
                className="qa-input"
                required
              />
              
              <button
                type="submit"
                disabled={loading}
                className="qa-button"
              >
                {loading ? 'Searching...' : 'Ask Question'}
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
              <span className="qa-loading-text">Retrieving answer...</span>
            </div>
          )}
          
          {!loading && (answer || document) && (
            <div className="qa-results">
              <div className="qa-result-card">
                <h2 className="qa-result-title">Answer</h2>
                <div className="qa-result-content">
                  {answer ? (
                    <p>{answer}</p>
                  ) : (
                    <p className="qa-empty-text">No answer available</p>
                  )}
                </div>
              </div>
              
              <div className="qa-result-card">
                <h2 className="qa-result-title">Source Documents</h2>
                <div className="qa-result-content">
                  {document ? (
                    <pre className="qa-document-content">{document}</pre>
                  ) : (
                    <p className="qa-empty-text">No source documents available</p>
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

export default QuestionForm;