import { useState, useEffect } from 'react';
import { fetchHealth, fetchTickets, fetchStats } from './services/api';
import DashboardView from './components/DashboardView';
import TicketForm from './components/TicketForm';
import KnowledgeAssistant from './components/KnowledgeAssistant';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard' | 'submit' | 'assistant'
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('supportdesk_theme') || 'light';
  });

  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState(null);
  const [stats, setStats] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [ticketError, setTicketError] = useState(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('supportdesk_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const loadData = async () => {
    setLoading(true);
    setTicketError(null);

    // 1. Health check
    fetchHealth()
      .then((data) => {
        setHealth(data);
        setHealthError(null);
      })
      .catch((err) => {
        setHealth(null);
        setHealthError(err.message);
      });

    // 2. Stats and Tickets
    try {
      const [statsData, ticketsData] = await Promise.all([fetchStats(), fetchTickets()]);
      setStats(statsData);
      setTickets(ticketsData);
    } catch (err) {
      setTicketError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTicketCreated = (newTicket) => {
    setTickets((prev) => [newTicket, ...prev]);
    fetchStats().then(setStats).catch(() => {});
  };

  const handleStatusChanged = (id, newStatus) => {
    setTickets((prev) =>
      prev.map((t) => (t.id === id ? { ...t, status: newStatus } : t))
    );
    fetchStats().then(setStats).catch(() => {});
  };

  const handleTicketDeleted = (id) => {
    setTickets((prev) => prev.filter((t) => t.id !== id));
    fetchStats().then(setStats).catch(() => {});
  };

  return (
    <div className="app-container">
      {/* Global Glass Header */}
      <header className="header">
        <div className="header-top">
          <div className="header-brand">
            <div className="brand-logo-row">
              <div className="brand-icon-shield">
                <span className="brand-icon-sparkle">✦</span>
              </div>
              <div>
                <div className="brand-badge-pill">Intelligent Support & Triage</div>
                <h1 className="header-title">AI SupportDesk</h1>
              </div>
            </div>
          </div>

          <div className="header-meta">
            {/* Health Status Indicator */}
            <div className="status-indicator">
              <span
                className={`status-dot ${
                  health?.status === 'healthy' ? 'status-dot-green' : 'status-dot-red'
                }`}
              />
              <span className="status-text">
                {health?.status === 'healthy'
                  ? `Backend: Online (${health.database})`
                  : healthError
                  ? 'Backend: Offline'
                  : 'Connecting...'}
              </span>
            </div>

            {/* Dark / Light Mode Toggle Button */}
            <button
              className="theme-toggle-btn"
              onClick={toggleTheme}
              title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
              aria-label="Toggle Theme"
            >
              {theme === 'light' ? (
                <>
                  <span className="theme-icon">🌙</span>
                  <span className="theme-text">Dark</span>
                </>
              ) : (
                <>
                  <span className="theme-icon">☀️</span>
                  <span className="theme-text">Light</span>
                </>
              )}
            </button>

            {/* Refresh Button */}
            <button className="btn btn-secondary btn-sm" onClick={loadData} title="Refresh data">
              ↻ Refresh
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-tabs-bar">
          <button
            className={`nav-tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Support Queue
            {tickets.length > 0 && <span className="nav-tab-count">{tickets.length}</span>}
          </button>
          <button
            className={`nav-tab-btn ${activeTab === 'submit' ? 'active' : ''}`}
            onClick={() => setActiveTab('submit')}
          >
            ✍ Submit New Ticket
          </button>
          <button
            className={`nav-tab-btn ${activeTab === 'assistant' ? 'active' : ''}`}
            onClick={() => setActiveTab('assistant')}
          >
            🤖 Knowledge Assistant (RAG)
          </button>
        </nav>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        {activeTab === 'dashboard' && (
          <DashboardView
            tickets={tickets}
            stats={stats}
            loading={loading}
            error={ticketError}
            onRefresh={loadData}
            onStatusChanged={handleStatusChanged}
            onTicketDeleted={handleTicketDeleted}
          />
        )}

        {activeTab === 'submit' && (
          <div className="submit-tab-container">
            <TicketForm
              onTicketCreated={handleTicketCreated}
              onNavigateToDashboard={() => setActiveTab('dashboard')}
            />
          </div>
        )}

        {activeTab === 'assistant' && (
          <KnowledgeAssistant />
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>
          <strong>AI SupportDesk</strong> &bull; End-to-End AI Triage & ChromaDB RAG Knowledge Assistant &bull; SQLite Persistence
        </p>
      </footer>
    </div>
  );
}
