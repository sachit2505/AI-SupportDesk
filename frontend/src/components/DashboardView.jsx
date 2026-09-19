import { useState } from 'react';
import TicketDetailModal from './TicketDetailModal';
import { deleteTicket, seedDemoData } from '../services/api';

export default function DashboardView({
  tickets,
  stats,
  loading,
  error,
  onRefresh,
  onStatusChanged,
  onTicketDeleted,
}) {
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [statusFilter, setStatusFilter] = useState('All');
  const [priorityFilter, setPriorityFilter] = useState('All');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [seeding, setSeeding] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const handleSeed = async () => {
    try {
      setSeeding(true);
      await seedDemoData(true);
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(`Failed to seed data: ${err.message}`);
    } finally {
      setSeeding(false);
    }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm(`Delete ticket #${id}?`)) return;
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

  // Filter tickets locally for instantaneous UI response
  const filteredTickets = tickets.filter((t) => {
    if (statusFilter !== 'All' && t.status !== statusFilter) return false;
    if (priorityFilter !== 'All' && t.priority !== priorityFilter) return false;
    if (categoryFilter !== 'All' && t.category !== categoryFilter) return false;
    return true;
  });

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
    <div className="dashboard-view">
      {/* 1. Metric Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card" onClick={() => setStatusFilter('All')}>
          <div className="stat-label">Total Tickets</div>
          <div className="stat-value">{stats?.total ?? tickets.length}</div>
          <div className="stat-hint">All tickets in system</div>
        </div>

        <div className="stat-card stat-card-open" onClick={() => setStatusFilter('Open')}>
          <div className="stat-label">Open Tickets</div>
          <div className="stat-value text-primary">{stats?.open ?? 0}</div>
          <div className="stat-hint">Awaiting agent action</div>
        </div>

        <div className="stat-card stat-card-urgent" onClick={() => setPriorityFilter('High')}>
          <div className="stat-label">High / Urgent</div>
          <div className="stat-value text-danger">{stats?.high_urgent ?? 0}</div>
          <div className="stat-hint">Require priority attention</div>
        </div>

        <div className="stat-card stat-card-resolved" onClick={() => setStatusFilter('Resolved')}>
          <div className="stat-label">Resolved Tickets</div>
          <div className="stat-value text-success">{stats?.resolved ?? 0}</div>
          <div className="stat-hint">Closed & completed</div>
        </div>
      </div>

      {/* 2. Filter & Actions Toolbar */}
      <div className="card toolbar-card">
        <div className="filter-group">
          <div className="filter-tabs">
            {['All', 'Open', 'In Progress', 'Resolved'].map((st) => (
              <button
                key={st}
                className={`filter-tab ${statusFilter === st ? 'active' : ''}`}
                onClick={() => setStatusFilter(st)}
              >
                {st}
              </button>
            ))}
          </div>

          <div className="filter-dropdowns">
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="select-filter"
            >
              <option value="All">All Priorities</option>
              <option value="Urgent">Urgent</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>

            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="select-filter"
            >
              <option value="All">All Categories</option>
              <option value="Billing">Billing</option>
              <option value="Technical Issue">Technical Issue</option>
              <option value="Account">Account</option>
              <option value="Subscription">Subscription</option>
              <option value="Security">Security</option>
              <option value="General">General</option>
            </select>
          </div>
        </div>

        <div className="toolbar-actions">
          <button
            className="btn btn-secondary btn-sm"
            onClick={handleSeed}
            disabled={seeding}
            title="Populate 5 realistic sample tickets"
          >
            {seeding ? 'Seeding...' : '⚡ Seed Demo Tickets'}
          </button>
          <button className="btn btn-secondary btn-sm" onClick={onRefresh} title="Refresh tickets">
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* 3. Ticket List Table / Cards */}
      <div className="card ticket-table-card">
        <div className="card-header-flex">
          <div>
            <h2 className="card-title">Support Queue</h2>
            <p className="card-subtitle">
              Showing {filteredTickets.length} of {tickets.length} tickets &bull; Click any ticket to inspect AI triage & suggested response
            </p>
          </div>
        </div>

        {loading ? (
          <div className="empty-state">Loading tickets...</div>
        ) : error ? (
          <div className="alert alert-error">{error}</div>
        ) : filteredTickets.length === 0 ? (
          <div className="empty-state">
            <p>No tickets match current filter criteria.</p>
            <button className="btn btn-primary btn-sm" style={{ marginTop: '0.75rem' }} onClick={handleSeed}>
              ⚡ Seed 5 Demo Tickets
            </button>
          </div>
        ) : (
          <div className="ticket-list-items">
            {filteredTickets.map((ticket) => (
              <div
                key={ticket.id}
                className="ticket-row-card"
                onClick={() => setSelectedTicket(ticket)}
              >
                <div className="ticket-row-main">
                  <div className="ticket-row-header">
                    <span className="ticket-id">#{ticket.id}</span>
                    <h3 className="ticket-row-title">{ticket.issue_summary || ticket.title}</h3>
                    {getStatusBadge(ticket.status)}
                  </div>

                  <p className="ticket-row-desc">{ticket.description}</p>

                  {/* AI Summary Highlight */}
                  {ticket.ai_summary && (
                    <div className="ticket-row-ai-summary">
                      <span className="ai-sparkle-sm">✦</span>
                      <span>{ticket.ai_summary}</span>
                    </div>
                  )}

                  <div className="ticket-row-meta">
                    <span>Submitted: {new Date(ticket.created_at).toLocaleString()}</span>
                    {ticket.relevant_articles && ticket.relevant_articles.length > 0 && (
                      <span className="meta-policy-link">
                        📖 {ticket.relevant_articles[0]}
                      </span>
                    )}
                  </div>
                </div>

                <div className="ticket-row-side">
                  <div className="ticket-badges-col">
                    <span className="badge badge-category">{ticket.category}</span>
                    {getPriorityBadge(ticket.priority)}
                    {getSentimentBadge(ticket.sentiment)}
                  </div>

                  <div className="ticket-row-actions">
                    <button
                      className="btn btn-secondary btn-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedTicket(ticket);
                      }}
                    >
                      Review &rarr;
                    </button>
                    <button
                      className="btn-text-danger"
                      onClick={(e) => handleDelete(e, ticket.id)}
                      disabled={deletingId === ticket.id}
                      title="Delete ticket"
                    >
                      &times;
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 4. Ticket Detail Modal */}
      {selectedTicket && (
        <TicketDetailModal
          ticket={selectedTicket}
          onClose={() => setSelectedTicket(null)}
          onStatusChanged={(id, newStatus) => {
            if (onStatusChanged) onStatusChanged(id, newStatus);
            setSelectedTicket((prev) => (prev && prev.id === id ? { ...prev, status: newStatus } : prev));
          }}
        />
      )}
    </div>
  );
}
