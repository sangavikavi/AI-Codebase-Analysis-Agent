const API_BASE = ''; // Proxy handles routing to http://localhost:8000

export const getAuthToken = () => localStorage.getItem('token');
export const setAuthToken = (token) => localStorage.setItem('token', token);
export const removeAuthToken = () => localStorage.removeItem('token');

export const getUserInfo = () => {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};

export const setUserInfo = (user) => localStorage.setItem('user', JSON.stringify(user));
export const removeUserInfo = () => localStorage.removeItem('user');

const fetchWithAuth = async (url, options = {}) => {
  const token = getAuthToken();
  const headers = {
    ...options.headers,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    removeAuthToken();
    removeUserInfo();
    window.location.reload();
  }

  return response;
};

export const api = {
  // Auth
  async login(email, password) {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    setAuthToken(data.access_token);
    setUserInfo({ email: data.email, role: data.role, user_id: data.user_id });
    return data;
  },

  async register(email, password, role = 'user') {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, role }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed');
    }
    return await res.json();
  },

  logout() {
    removeAuthToken();
    removeUserInfo();
  },

  // Projects
  async listProjects() {
    const res = await fetchWithAuth('/api/projects');
    if (!res.ok) throw new Error('Failed to load projects');
    return await res.json();
  },

  async getProject(id) {
    const res = await fetchWithAuth(`/api/projects/${id}`);
    if (!res.ok) throw new Error('Failed to load project details');
    return await res.json();
  },

  async deleteProject(id) {
    const res = await fetchWithAuth(`/api/projects/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete project');
    return true;
  },

  async uploadProjectZip(formData) {
    const res = await fetchWithAuth('/api/projects/upload', {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to upload project ZIP');
    }
    return await res.json();
  },

  async createProjectGitHub(data) {
    const res = await fetchWithAuth('/api/projects/github', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create project from GitHub');
    }
    return await res.json();
  },

  // Controls & Streaming
  async startAnalysis(projectId) {
    const res = await fetchWithAuth(`/api/projects/${projectId}/start`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to start analysis');
    return await res.json();
  },

  async pauseAnalysis(projectId) {
    const res = await fetchWithAuth(`/api/projects/${projectId}/pause`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to pause analysis');
    return await res.json();
  },

  async resumeAnalysis(projectId) {
    const res = await fetchWithAuth(`/api/projects/${projectId}/resume`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to resume analysis');
    return await res.json();
  },

  async getProjectEvents(projectId) {
    const res = await fetchWithAuth(`/api/projects/${projectId}/events`);
    if (!res.ok) throw new Error('Failed to load events');
    return await res.json();
  },

  // Chat
  async sendChatMessage(projectId, message) {
    const res = await fetchWithAuth(`/api/projects/${projectId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    if (!res.ok) throw new Error('Failed to send message');
    return await res.json();
  },

  async getChatHistory(projectId) {
    const res = await fetchWithAuth(`/api/projects/${projectId}/chat`);
    if (!res.ok) throw new Error('Failed to load chat history');
    return await res.json();
  },

  // Reports
  async getReports(projectId) {
    const res = await fetchWithAuth(`/api/projects/${projectId}/reports`);
    if (!res.ok) throw new Error('Failed to load reports');
    return await res.json();
  },

  async getPersonaReport(projectId, persona) {
    const res = await fetchWithAuth(`/api/projects/${projectId}/reports/${persona}`);
    if (!res.ok) throw new Error(`Failed to load ${persona} report`);
    return await res.json();
  },

  getExportMarkdownUrl(projectId) {
    return `/api/projects/${projectId}/export/markdown`;
  },

  getExportPdfUrl(projectId) {
    return `/api/projects/${projectId}/export/pdf`;
  },

  // RAG Q&A
  async askQA(projectId, question, persona = 'sde') {
    const res = await fetchWithAuth(`/api/projects/${projectId}/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, persona }),
    });
    if (!res.ok) throw new Error('Q&A query failed');
    return await res.json();
  },

  // Admin
  async getAdminAnalytics() {
    const res = await fetchWithAuth('/api/admin/analytics');
    if (!res.ok) throw new Error('Failed to load analytics');
    return await res.json();
  },

  async getAdminUsers() {
    const res = await fetchWithAuth('/api/admin/users');
    if (!res.ok) throw new Error('Failed to load users');
    return await res.json();
  },

  async deleteAdminUser(userId) {
    const res = await fetchWithAuth(`/api/admin/users/${userId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete user');
    return true;
  },

  async getAdminProjects() {
    const res = await fetchWithAuth('/api/admin/projects');
    if (!res.ok) throw new Error('Failed to load admin projects');
    return await res.json();
  },

  async deleteAdminProject(projectId) {
    const res = await fetchWithAuth(`/api/admin/projects/${projectId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete project');
    return true;
  },

  async getAdminTraces() {
    const res = await fetchWithAuth('/api/admin/traces');
    if (!res.ok) throw new Error('Failed to load traces');
    return await res.json();
  },

  async getAdminErrorLogs() {
    const res = await fetchWithAuth('/api/admin/error-logs');
    if (!res.ok) throw new Error('Failed to load error logs');
    return await res.json();
  },
};
