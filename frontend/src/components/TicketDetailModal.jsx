import { useState } from 'react';
import { updateTicketStatus } from '../services/api';

export default function TicketDetailModal({ ticket, onClose, onStatusChanged }) {
  const [updating, setUpdating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [currentStatus, setCurrentStatus] = useState(ticket.status);

  if (!ticket) return null;

  const handleStatusUpdate = async (newStatus) => {
    try {
      setUpdating(true);
      await updateTicketStatus(ticket.id, newStatus);
      setCurrentStatus(newStatus);
      if (onStatusChanged) onStatusChanged(ticket.id, newStatus);
    } catch (err) {
      alert(`Failed to update ticket status: ${err.message}`);
    } finally {
      setUpdating(false);
    }
  };

  const handleCopy = () => {
    if (ticket.suggested_response) {
      navigator.clipboard.writeText(ticket.suggested_response);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const getPriorityBadge = (priority) => {
    const p = (priority || 'medium').toLowerCase();
    let badgeClass = 'badge-priority-medium';
    if (p === 'urgent' || p === 'high') badgeClass = 'badge-priority-high';
    if (p === 'low') badgeClass = 'badge-priority-low';
    return <span className={`badge ${badgeClass}`}>{priority || 'Medium'}</span>;
  };

  const getSentimentBadge = (sentiment) => {
    const s = (sentiment || 'neutral').toLowerCase();
    let badgeClass = 'badge-sentiment-neutral';
    if (s === 'positive') badgeClass = 'badge-sentiment-positive';
    if (s === 'negative') badgeClass = 'badge-sentiment-negative';
    return <span className={`badge ${badgeClass}`}>{sentiment || 'Neutral'}</span>;
  };

  const getStatusBadge = (status) => {
    let cls = 'badge-status-open';
    if (status === 'In Progress') cls = 'badge-status-progress';
    if (status === 'Resolved') cls = 'badge-status-resolved';
    return <span className={`badge ${cls}`}>{status}</span>;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <span className="ticket-id">#{ticket.id}</span>
            <h2 className="modal-title">{ticket.issue_summary || ticket.title}</h2>
          </div>
          <button className="modal-close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          {/* Status & Meta Row */}
          <div className="modal-meta-bar">
            <div className="meta-item">
              <span className="meta-label">Status:</span>
              {getStatusBadge(currentStatus)}
            </div>
            <div className="meta-item">
              <span className="meta-label">Category:</span>
              <span className="badge badge-category">{ticket.category}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Priority:</span>
              {getPriorityBadge(ticket.priority)}
            </div>
            <div className="meta-item">
              <span className="meta-label">Sentiment:</span>
              {getSentimentBadge(ticket.sentiment)}
            </div>
          </div>

          {/* Original Customer Problem */}
          <div className="detail-section">
            <h3 className="section-heading">Original Customer Issue</h3>
            <div className="customer-desc-box">
              {ticket.description}
            </div>
            <div className="ticket-timestamp">
              Submitted on: {new Date(ticket.created_at).toLocaleString()}
            </div>
          </div>

          {/* AI Triage Analysis */}
          <div className="detail-section ai-analysis-section">
            <div className="ai-section-title">
              <span className="ai-sparkle">✦</span>
              <h3 className="section-heading">AI Triage Summary</h3>
            </div>
            <p className="ai-summary-text">
              {ticket.ai_summary || ticket.summary || 'Summary generated during triage.'}
            </p>

            {/* Relevant Knowledge Base Articles from RAG */}
            {ticket.relevant_articles && ticket.relevant_articles.length > 0 && (
              <div className="relevant-kb-box">
                <span className="kb-label">Grounded Knowledge Policy:</span>
                <div className="kb-tags">
                  {ticket.relevant_articles.map((art, idx) => (
                    <span key={idx} className="kb-tag">
                      📖 {art}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Suggested Response */}
          <div className="detail-section">
            <div className="response-header-row">
              <h3 className="section-heading">AI Suggested Response</h3>
              <button className="btn btn-secondary btn-sm" onClick={handleCopy}>
                {copied ? '✓ Copied to Clipboard' : '📋 Copy Response'}
              </button>
            </div>
            <div className="suggested-response-box">
              {ticket.suggested_response || 'No suggested response available.'}
            </div>
          </div>

          {/* Workflow Status Action */}
          <div className="detail-section status-action-section">
            <h3 className="section-heading">Update Ticket Workflow</h3>
            <div className="status-buttons">
              <button
                className={`btn btn-sm ${currentStatus === 'Open' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => handleStatusUpdate('Open')}
                disabled={updating || currentStatus === 'Open'}
              >
                Mark Open
              </button>
              <button
                className={`btn btn-sm ${currentStatus === 'In Progress' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => handleStatusUpdate('In Progress')}
                disabled={updating || currentStatus === 'In Progress'}
              >
                Mark In Progress
              </button>
              <button
                className={`btn btn-sm ${currentStatus === 'Resolved' ? 'btn-success' : 'btn-secondary'}`}
                onClick={() => handleStatusUpdate('Resolved')}
                disabled={updating || currentStatus === 'Resolved'}
              >
                ✓ Mark Resolved
              </button>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
