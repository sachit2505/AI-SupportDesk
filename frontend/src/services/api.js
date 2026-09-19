/**
 * Centralized API client for AI SupportDesk
 */

const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed (${res.status})`);
  return res.json();
}

export async function fetchStats() {
  const res = await fetch(`${API_BASE}/tickets/stats`);
  if (!res.ok) throw new Error(`Failed to fetch stats (${res.status})`);
  return res.json();
}

export async function fetchTickets(filters = {}) {
  const params = new URLSearchParams();
  if (filters.status && filters.status !== 'All') params.append('status', filters.status);
  if (filters.priority && filters.priority !== 'All') params.append('priority', filters.priority);
  if (filters.category && filters.category !== 'All') params.append('category', filters.category);

  const url = `${API_BASE}/tickets${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch tickets (${res.status})`);
  return res.json();
}

export async function getTicket(id) {
  const res = await fetch(`${API_BASE}/tickets/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch ticket #${id}`);
  return res.json();
}

export async function createTicket(ticketData) {
  const res = await fetch(`${API_BASE}/tickets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ticketData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to create ticket (${res.status})`);
  }
  return res.json();
}

export async function updateTicketStatus(id, status) {
  const res = await fetch(`${API_BASE}/tickets/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to update status (${res.status})`);
  }
  return res.json();
}

export async function deleteTicket(id) {
  const res = await fetch(`${API_BASE}/tickets/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(`Failed to delete ticket #${id}`);
  return true;
}

export async function askAssistant(question) {
  const res = await fetch(`${API_BASE}/assistant/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Assistant failed (${res.status})`);
  }
  return res.json();
}

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE}/assistant/documents`);
  if (!res.ok) throw new Error('Failed to load documents');
  return res.json();
}

export async function seedDemoData(force = true) {
  const res = await fetch(`${API_BASE}/seed?force=${force}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to seed demo data');
  return res.json();
}
