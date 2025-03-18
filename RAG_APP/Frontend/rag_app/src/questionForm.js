import React, { useState } from 'react';
import axios from 'axios';
import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import './App.css';

const api = axios.create({
  baseURL: 'http://localhost:8000/'
});

const QuestionForm = () => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expandedDocs, setExpandedDocs] = useState({});

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
        
        // Handle different possible document formats
        let docData = response.data.Documents || response.data.Document || '';
        
        // Convert string to array if it's not already an array
        let docsArray = [];
        if (Array.isArray(docData)) {
          docsArray = docData;
        } else if (typeof docData === 'string' && docData.trim() !== '') {
          // Assume the string might contain multiple documents separated somehow
          // This is a simple approach - you might need to adjust based on your actual format
          docsArray = [docData];
        }
        
        setDocuments(docsArray);
        setExpandedDocs({}); // Reset expanded state
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
  
  const toggleDocument = (index) => {
    setExpandedDocs(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };
  
  const getDocumentPreview = (doc) => {
    if (typeof doc !== 'string') {
      return JSON.stringify(doc).substring(0, 100) + '...';
    }
    const lines = doc.split('\n');
    return lines[0] ? (lines[0].substring(0, 100) + (lines[0].length > 100 ? '...' : '')) : 'Empty document';
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
          
          {!loading && (answer || documents.length > 0) && (
            <div className="qa-results">
              <div className="qa-result-card">
                <h2 className="qa-result-title">Answer</h2>
                <div className="qa-result-content">
                  {answer ? (
                    <ReactMarkdown rehypePlugins={[rehypeRaw]}>{answer}</ReactMarkdown>
                  ) : (
                    <p className="qa-empty-text">No answer available</p>
                  )}
                </div>
              </div>
              
              <div className="qa-result-card">
                <h2 className="qa-result-title">Source Documents</h2>
                <div className="qa-result-content">
                  {documents.length > 0 ? (
                    <div className="qa-documents-list">
                      {documents.map((doc, index) => (
                        <div key={index} className="qa-document-item">
                          <div 
                            className="qa-document-header" 
                            onClick={() => toggleDocument(index)}
                          >
                            <span className="qa-expand-icon">
                              {expandedDocs[index] ? '▼' : '>>>'}
                            </span>
                            <span className="qa-document-preview">
                              {getDocumentPreview(doc)}
                            </span>
                          </div>
                          
                          {expandedDocs[index] && (
                            <pre className="qa-document-content">
                              {typeof doc === 'string' ? doc : JSON.stringify(doc, null, 2)}
                            </pre>
                          )}
                        </div>
                      ))}
                    </div>
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