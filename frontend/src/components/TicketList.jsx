import { useState } from 'react';
import { deleteTicket } from '../services/api';

export default function TicketList({ tickets, loading, error, onTicketDeleted }) {
  const [deletingId, setDeletingId] = useState(null);

  const handleDelete = async (id) => {
    if (!window.confirm(`Are you sure you want to delete ticket #${id}?`)) return;
    try {
      setDeletingId(id);
      await deleteTicket(id);
      if (onTicketDeleted) onTicketDeleted(id);
    } catch (err) {
      alert(`Failed to delete ticket: ${err.message}`);
    } finally {
      setDeletingId(null);
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
    if (s === 'frustrated' || s === 'negative') badgeClass = 'badge-sentiment-negative';
    return <span className={`badge ${badgeClass}`}>{sentiment || 'Neutral'}</span>;
  };

  if (loading) {
    return (
      <div className="card">
        <h2 className="card-title">Support Tickets</h2>
        <div className="empty-state">Loading tickets...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h2 className="card-title">Support Tickets</h2>
        <div className="alert alert-error">Failed to load tickets: {error}</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header-flex">
        <div>
          <h2 className="card-title">Support Tickets</h2>
          <p className="card-subtitle">
            Showing {tickets.length} {tickets.length === 1 ? 'ticket' : 'tickets'} in database
          </p>
        </div>
      </div>

      {tickets.length === 0 ? (
        <div className="empty-state">
          <p>No support tickets yet.</p>
          <small>Use the form on the left to submit a test ticket.</small>
        </div>
      ) : (
        <div className="ticket-items">
          {tickets.map((ticket) => (
            <div key={ticket.id} className="ticket-item">
              <div className="ticket-item-header">
                <div className="ticket-title-row">
                  <span className="ticket-id">#{ticket.id}</span>
                  <h3 className="ticket-title">{ticket.title}</h3>
                </div>
                <div className="ticket-badges">
                  <span className="badge badge-category">{ticket.category}</span>
                  {getPriorityBadge(ticket.priority)}
                  {getSentimentBadge(ticket.sentiment)}
                  <button
                    className="btn-text-danger"
                    onClick={() => handleDelete(ticket.id)}
                    disabled={deletingId === ticket.id}
                    title="Delete ticket"
                  >
                    {deletingId === ticket.id ? 'Deleting...' : '✕'}
                  </button>
                </div>
              </div>

              <p className="ticket-desc">{ticket.description}</p>

              <div className="ticket-meta">
                <span>Status: <strong>{ticket.status}</strong></span>
                <span>Submitted: {new Date(ticket.created_at).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
