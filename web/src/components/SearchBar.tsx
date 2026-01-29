import { useState, FormEvent } from 'react';
import { Search, Filter } from 'lucide-react';
import { DocumentType } from '../types';

interface SearchBarProps {
  onSearch: (query: string, filters?: { documentTypes?: DocumentType[] }) => void;
  isLoading?: boolean;
}

export default function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedTypes, setSelectedTypes] = useState<DocumentType[]>([]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query, selectedTypes.length > 0 ? { documentTypes: selectedTypes } : undefined);
    }
  };

  const toggleDocType = (type: DocumentType) => {
    setSelectedTypes(prev =>
      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
    );
  };

  const docTypes: { value: DocumentType; label: string }[] = [
    { value: 'decision', label: 'Decisions' },
    { value: 'transcript', label: 'Transcripts' },
    { value: 'evidence', label: 'Evidence' },
    { value: 'procedural', label: 'Procedural' },
    { value: 'notice', label: 'Notices' },
  ];

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search hearing documents... (e.g., 'groundwater contamination evidence')"
              className="w-full pl-12 pr-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-aer-teal focus:border-transparent text-lg"
              aria-label="Search hearing documents"
            />
          </div>
          
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-3 rounded-lg border ${
              showFilters || selectedTypes.length > 0
                ? 'border-aer-teal bg-aer-light-blue text-aer-teal'
                : 'border-gray-300 text-gray-600 hover:bg-gray-50'
            }`}
            aria-label="Toggle filters"
          >
            <Filter className="h-5 w-5" />
            {selectedTypes.length > 0 && (
              <span className="ml-1 text-sm font-medium">{selectedTypes.length}</span>
            )}
          </button>

          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="px-6 py-3 bg-aer-teal text-white rounded-lg font-medium hover:bg-aer-blue transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="loading-dots">Searching</span>
            ) : (
              'Search'
            )}
          </button>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="absolute top-full left-0 right-0 mt-2 p-4 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-medium text-gray-700">Filter by Document Type</h3>
              {selectedTypes.length > 0 && (
                <button
                  type="button"
                  onClick={() => setSelectedTypes([])}
                  className="text-sm text-aer-teal hover:underline"
                >
                  Clear all
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {docTypes.map(({ value, label }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => toggleDocType(value)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    selectedTypes.includes(value)
                      ? 'bg-aer-teal text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        )}
      </form>

      {/* Search tips */}
      <div className="mt-3 text-sm text-gray-500">
        <span className="font-medium">Try:</span>{' '}
        <button
          onClick={() => { setQuery('groundwater contamination'); }}
          className="text-aer-teal hover:underline"
        >
          groundwater contamination
        </button>
        {' • '}
        <button
          onClick={() => { setQuery('EPEA section 2'); }}
          className="text-aer-teal hover:underline"
        >
          EPEA section 2
        </button>
        {' • '}
        <button
          onClick={() => { setQuery('environmental assessment methodology'); }}
          className="text-aer-teal hover:underline"
        >
          environmental assessment
        </button>
      </div>
    </div>
  );
}
