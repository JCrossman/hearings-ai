import { SearchRequest, SearchResponse, DemoRole } from '../types';

// Use relative path in production (served from same domain via proxy) or absolute for local dev
const API_BASE = import.meta.env.DEV ? '/api' : 'https://hearingsai-api.lemonground-4dbaf9d3.canadacentral.azurecontainerapps.io/api';

let currentRole: DemoRole = 'Staff';
let userEmail: string | null = null;

export function setCurrentRole(role: DemoRole) {
  currentRole = role;
}

export function getCurrentRole(): DemoRole {
  return currentRole;
}

// Fetch authenticated user info from Static Web Apps
async function getUserEmail(): Promise<string | null> {
  if (userEmail) return userEmail;
  
  try {
    const response = await fetch('/.auth/me');
    if (!response.ok) return null;
    
    const data = await response.json();
    const principal = data.clientPrincipal;
    
    if (principal && principal.userDetails) {
      userEmail = principal.userDetails;
    } else if (principal && principal.claims) {
      // Find email in claims
      const emailClaim = principal.claims.find((c: any) => 
        c.typ === 'emails' || c.typ === 'email' || c.typ === 'preferred_username'
      );
      if (emailClaim) {
        userEmail = emailClaim.val;
      }
    }
    
    return userEmail;
  } catch (error) {
    console.error('Failed to get user email:', error);
    return null;
  }
}

async function fetchWithRole<T>(url: string, options: RequestInit = {}): Promise<T> {
  const email = await getUserEmail();
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Demo-Role': currentRole,
    ...options.headers as Record<string, string>,
  };
  
  // Send user email to API for allowlist validation
  if (email) {
    headers['X-User-Email'] = email;
  }

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
