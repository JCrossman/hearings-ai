import { useState, useCallback } from 'react';
import Layout from './components/Layout';
import SearchBar from './components/SearchBar';
import ResultsList from './components/ResultsList';
import { useSearch } from './hooks/useSearch';
import { DemoRole, DocumentType, DEMO_ROLES } from './types';
import { setCurrentRole } from './api/client';

export default function App() {
  const [currentRole, setRole] = useState<DemoRole>('Staff');
  const [searchQuery, setSearchQuery] = useState('');
  const { search, data, isLoading, error } = useSearch();

  const handleRoleChange = useCallback((role: DemoRole) => {
    setRole(role);
    setCurrentRole(role);
    // Re-run search with new role if there's an active query
    if (searchQuery) {
      search({ query: searchQuery });
    }
  }, [search, searchQuery]);

  const handleSearch = useCallback((query: string, filters?: { documentTypes?: DocumentType[] }) => {
    setSearchQuery(query);
    search({
      query,
      filters: filters?.documentTypes ? { document_types: filters.documentTypes } : undefined,
      top: 20,
      search_mode: 'hybrid',
    });
  }, [search]);

  const roleInfo = DEMO_ROLES.find(r => r.id === currentRole)!;

  return (
    <Layout currentRole={currentRole} onRoleChange={handleRoleChange}>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Search Hearing Documents
          </h2>
          <p className="text-lg text-gray-600 mb-4">
            Find evidence, decisions, and transcripts across proceedings
          </p>
          
          {/* Role indicator */}
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${roleInfo.color}`}>
            <span className="text-sm font-medium">Viewing as: {roleInfo.name}</span>
            <span className="text-xs opacity-75">• {roleInfo.description}</span>
          </div>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <SearchBar onSearch={handleSearch} isLoading={isLoading} />
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <p className="font-medium">Search failed</p>
            <p className="text-sm">{error.message}</p>
          </div>
        )}

        {/* Results */}
        <ResultsList response={data} isLoading={isLoading} query={searchQuery} />

        {/* Empty state when no search yet */}
        {!data && !isLoading && !error && (
          <div className="text-center py-16">
            <div className="text-gray-300 mb-4">
              <svg className="h-24 w-24 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-medium text-gray-500 mb-2">
              Start your search
            </h3>
            <p className="text-gray-400 max-w-md mx-auto">
              Enter keywords to search across hearing documents. Results are filtered based on your role.
            </p>
          </div>
        )}
      </div>
    </Layout>
  );
}
