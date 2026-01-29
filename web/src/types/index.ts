// API types matching the backend models

export type DocumentType = 'decision' | 'transcript' | 'procedural' | 'evidence' | 'notice' | 'information_request';

export type ConfidentialityLevel = 'public' | 'protected_a' | 'confidential';

export type DemoRole = 'Hearing_Panel' | 'Staff' | 'Intervener' | 'Public';

export interface SearchFilters {
  document_types?: DocumentType[];
  parties?: string[];
  regulatory_citations?: string[];
  date_from?: string;
  date_to?: string;
}

export interface SearchRequest {
  query: string;
  proceeding_id?: string;
  filters?: SearchFilters;
  top?: number;
  search_mode?: 'hybrid' | 'vector' | 'keyword';
}

export interface SearchResult {
  document_id: string;
  title: string;
  abaer_citation: string | null;
  snippet: string;
  relevance_score: number;
  page_number: number;
  paragraph_number: string | null;
  citation_ref: string;
  parties: string[];
  regulatory_citations: string[];
}

export interface FacetValue {
  value: string;
  count: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total_count: number;
  facets: Record<string, FacetValue[]>;
}

export interface RoleInfo {
  id: DemoRole;
  name: string;
  description: string;
  color: string;
}

export const DEMO_ROLES: RoleInfo[] = [
  {
    id: 'Hearing_Panel',
    name: 'Hearing Panel',
    description: 'Full access including confidential documents',
    color: 'bg-purple-100 text-purple-800',
  },
  {
    id: 'Staff',
    name: 'Staff',
    description: 'Public and Protected A documents',
    color: 'bg-blue-100 text-blue-800',
  },
  {
    id: 'Intervener',
    name: 'Intervener',
    description: 'Public and own-party Protected A',
    color: 'bg-green-100 text-green-800',
  },
  {
    id: 'Public',
    name: 'Public',
    description: 'Public documents only',
    color: 'bg-gray-100 text-gray-800',
  },
];
