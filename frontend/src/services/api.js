// API Client for AI Project Intelligence & Risk Advisor Backend

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = options.headers || {};

  // If body is not FormData, set Content-Type to application/json
  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorDetail = `HTTP ${response.status} ${response.statusText}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          errorDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch {
        // Fallback to text
        const text = await response.text();
        if (text) errorDetail = text;
      }
      const err = new Error(errorDetail);
      err.status = response.status;
      throw err;
    }

    return await response.json();
  } catch (error) {
    if (error.message && (error.message.includes('Failed to fetch') || error.message.includes('NetworkError'))) {
      const netErr = new Error(`Cannot connect to backend server at ${BASE_URL}. Please ensure FastAPI is running.`);
      netErr.isNetworkError = true;
      throw netErr;
    }
    throw error;
  }
}

export const api = {
  // Health & System
  getHealth: (options = {}) => request('/health', options),

  // Milestone 1: Document Ingestion
  uploadDocument: (file, options = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/api/documents/upload', {
      method: 'POST',
      body: formData,
      ...options,
    });
  },

  getDocuments: (options = {}) => request('/api/documents', options),

  // Milestone 1: RAG Pipeline
  indexDocument: (file, options = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/api/rag/index', {
      method: 'POST',
      body: formData,
      ...options,
    });
  },

  searchRAG: (queryOrPayload, top_k = 5, options = {}) => {
    let body;
    if (typeof queryOrPayload === 'object' && queryOrPayload !== null) {
      body = JSON.stringify(queryOrPayload);
    } else {
      body = JSON.stringify({ query: queryOrPayload, top_k });
    }
    return request('/api/rag/search', {
      method: 'POST',
      body,
      ...options,
    });
  },

  getRAGStatus: (options = {}) => request('/api/rag/status', options),

  // Milestone 2: Agents
  analyzeScope: ({ query, text, top_k = 10, document_id, filename }, options = {}) => {
    return request('/api/agents/analyze-scope', {
      method: 'POST',
      body: JSON.stringify({ query, text, top_k, document_id, filename }),
      ...options,
    });
  },

  detectRisks: ({ query, text, top_k = 10, document_id, filename }, options = {}) => {
    return request('/api/agents/detect-risks', {
      method: 'POST',
      body: JSON.stringify({ query, text, top_k, document_id, filename }),
      ...options,
    });
  },

  identifyBlockers: ({ query, text, top_k = 10, document_id, filename }, options = {}) => {
    return request('/api/agents/identify-blockers', {
      method: 'POST',
      body: JSON.stringify({ query, text, top_k, document_id, filename }),
      ...options,
    });
  },

  // Milestone 2: Multi-Agent Orchestrator
  analyzeProject: ({ query, text, top_k = 15, document_ids, filename }, options = {}) => {
    return request('/api/agents/analyze-project', {
      method: 'POST',
      body: JSON.stringify({ query, text, top_k, document_ids: document_ids || [], filename }),
      ...options,
    });
  },

  getAgentStatus: (options = {}) => request('/api/agents/status', options),
};

export default api;
