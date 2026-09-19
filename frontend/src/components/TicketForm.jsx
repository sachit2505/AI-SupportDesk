import { useState } from 'react';
import { createTicket } from '../services/api';

export default function TicketForm({ onTicketCreated, onNavigateToDashboard }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [createdTicket, setCreatedTicket] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) {
      setError('Please provide both an issue summary and a detailed description.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const ticket = await createTicket({
        issue_summary: title.trim(),
        description: description.trim(),
      });
      setCreatedTicket(ticket);
      setTitle('');
      setDescription('');
      if (onTicketCreated) onTicketCreated(ticket);
    } catch (err) {
      setError(err.message || 'Failed to submit ticket');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setCreatedTicket(null);
    setError(null);
  };

  return (
    <div className="ticket-form-wrapper">
      <div className="card">
        <h2 className="card-title">Submit Support Ticket</h2>
        <p className="card-subtitle">
          Submit your support request. The AI engine will immediately categorize, prioritize, assess sentiment, and recommend a grounded response.
        </p>

        {error && <div className="alert alert-error">{error}</div>}

        {!createdTicket ? (
          <form onSubmit={handleSubmit} className="form">
            <div className="form-group">
              <label htmlFor="ticket-title">Issue Summary</label>
              <input
                id="ticket-title"
                type="text"
                placeholder="e.g. Charged twice for annual subscription renewal"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={submitting}
                required
                minLength={3}
              />
            </div>

            <div className="form-group">
              <label htmlFor="ticket-desc">Detailed Description</label>
              <textarea
                id="ticket-desc"
                rows={5}
                placeholder="Provide details, error codes, dates, transaction numbers, or circumstances..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={submitting}
                required
                minLength={5}
              />
            </div>

            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Analyzing & Triaging Ticket...' : 'Submit Ticket & Run AI Triage'}
            </button>
          </form>
        ) : (
          <div className="triage-result-card">
            <div className="alert alert-success">
              ✓ Ticket #{createdTicket.id} successfully created and analyzed!
            </div>

            <div className="triage-badges-row">
              <div className="triage-badge-block">
                <span className="triage-label">Category:</span>
                <span className="badge badge-category">{createdTicket.category}</span>
              </div>
              <div className="triage-badge-block">
                <span className="triage-label">Priority:</span>
                <span className={`badge badge-priority-${createdTicket.priority.toLowerCase()}`}>
                  {createdTicket.priority}
                </span>
              </div>
              <div className="triage-badge-block">
                <span className="triage-label">Sentiment:</span>
                <span className={`badge badge-sentiment-${createdTicket.sentiment.toLowerCase()}`}>
                  {createdTicket.sentiment}
                </span>
              </div>
            </div>

            <div className="triage-section-box">
              <span className="triage-section-title">AI Summary:</span>
              <p>{createdTicket.ai_summary || createdTicket.summary}</p>
            </div>

            {createdTicket.relevant_articles && createdTicket.relevant_articles.length > 0 && (
              <div className="triage-section-box">
                <span className="triage-section-title">Knowledge Policy Grounding:</span>
                <div className="kb-tags">
                  {createdTicket.relevant_articles.map((art, idx) => (
                    <span key={idx} className="kb-tag">📖 {art}</span>
                  ))}
                </div>
              </div>
            )}

            <div className="triage-section-box">
              <span className="triage-section-title">Suggested Customer Response:</span>
              <div className="suggested-response-preview">
                {createdTicket.suggested_response}
              </div>
            </div>

            <div className="triage-actions-row">
              <button className="btn btn-secondary" onClick={handleReset}>
                Submit Another Ticket
              </button>
              {onNavigateToDashboard && (
                <button className="btn btn-primary" onClick={onNavigateToDashboard}>
                  View on Dashboard &rarr;
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
