import { SearchRequest, SearchResponse, DemoRole } from '../types';

// Use relative path in production (served from same domain via proxy) or absolute for local dev
const API_BASE = import.meta.env.DEV ? '/api' : 'https://hearingsai-api.lemonground-4dbaf9d3.canadacentral.azurecontainerapps.io/api';

let currentRole: DemoRole = 'Staff';

export function setCurrentRole(role: DemoRole) {
  currentRole = role;
}

export function getCurrentRole(): DemoRole {
  return currentRole;
}

async function fetchWithRole<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    'X-Demo-Role': currentRole,
    ...options.headers,
  };

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function searchDocuments(request: SearchRequest): Promise<SearchResponse> {
  return fetchWithRole<SearchResponse>(`${API_BASE}/search`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function healthCheck(): Promise<{ status: string; version: string }> {
  const response = await fetch(`${API_BASE.replace('/api', '')}/health`);
  return response.json();
}
