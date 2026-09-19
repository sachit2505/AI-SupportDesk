import { useState, useEffect } from 'react';
import { askAssistant, fetchDocuments } from '../services/api';

const SAMPLE_QUESTIONS = [
  "What is your refund policy for annual plans?",
  "I was charged twice on my card, how do I get a refund?",
  "My account is locked after 5 failed logins, what can I do?",
  "How do I set up or recover Two-Factor Authentication?",
  "How do I cancel my subscription and what happens to my data?",
  "What happens if our company renewal payment fails?",
];

export default function KnowledgeAssistant() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchDocuments()
      .then((data) => setDocuments(data.documents || []))
      .catch(() => {});
  }, []);

  const handleAsk = async (qText) => {
    const q = (qText || question).trim();
    if (!q) {
      setError('Please enter a question to ask the assistant.');
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const data = await askAssistant(q);
      setResponse(data);
    } catch (err) {
      setError(err.message || 'Failed to query the knowledge assistant.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSample = (sampleQ) => {
    setQuestion(sampleQ);
    handleAsk(sampleQ);
  };

  return (
    <div className="assistant-container">
      <div className="card assistant-card">
        <div className="card-header">
          <div>
            <h2 className="card-title">RAG Knowledge Assistant</h2>
            <p className="card-subtitle">
              Ask any customer support question. Answers are retrieved and grounded directly in our verified knowledge articles.
            </p>
          </div>
        </div>

        {/* Question Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAsk();
          }}
          className="assistant-form"
        >
          <div className="assistant-input-row">
            <input
              type="text"
              placeholder="e.g. What is the policy for duplicate subscription charges?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loading}
              className="assistant-input"
            />
            <button type="submit" className="btn btn-primary assistant-submit-btn" disabled={loading}>
              {loading ? 'Searching & Grounding...' : 'Ask Assistant'}
            </button>
          </div>
        </form>

        {/* Suggestion Chips */}
        <div className="sample-chips-section">
          <span className="sample-label">Try asking:</span>
          <div className="chips-list">
            {SAMPLE_QUESTIONS.map((q, idx) => (
              <button
                key={idx}
                type="button"
                className="chip-btn"
                onClick={() => handleSelectSample(q)}
                disabled={loading}
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Error State */}
        {error && <div className="alert alert-error">{error}</div>}

        {/* Loading State */}
        {loading && (
          <div className="assistant-loading-box">
            <div className="spinner"></div>
            <p>Searching ChromaDB vector store and synthesizing answer...</p>
          </div>
        )}

        {/* Answer Display */}
        {response && !loading && (
          <div className="assistant-result-box">
            <div className="result-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="result-badge">✦ Grounded Answer</span>
              <button
                type="button"
                className="btn btn-secondary btn-xs"
                onClick={() => {
                  navigator.clipboard.writeText(response.answer);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2500);
                }}
              >
                {copied ? '✓ Copied' : '📋 Copy Answer'}
              </button>
            </div>

            <div className="answer-text">
              {response.answer.split('\n\n').map((para, i) => (
                <p key={i}>{para}</p>
              ))}
            </div>

            {response.sources && response.sources.length > 0 && (
              <div className="sources-container">
                <span className="sources-label">Sources Cited:</span>
                <div className="sources-list">
                  {response.sources.map((src, idx) => (
                    <span key={idx} className="source-badge">
                      📄 {src}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Available Knowledge Articles Index */}
      {documents.length > 0 && (
        <div className="card kb-index-card">
          <h3 className="kb-index-title">Indexed Knowledge Base Documents ({documents.length})</h3>
          <div className="kb-index-grid">
            {documents.map((doc, idx) => (
              <div key={idx} className="kb-index-item">
                <span className="kb-index-icon">📘</span>
                <span className="kb-index-name">{doc.title}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
