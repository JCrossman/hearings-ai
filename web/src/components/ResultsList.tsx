import { useState } from 'react';
import { SearchResult, SearchResponse, FacetValue, SearchFilters } from '../types';
import { FileText, Scale, BookOpen, ChevronRight, ChevronDown, X } from 'lucide-react';

interface ResultsListProps {
  response: SearchResponse | undefined;
  isLoading: boolean;
  query: string;
  activeFilters: SearchFilters;
  onFilterChange: (filters: SearchFilters) => void;
}

export default function ResultsList({ response, isLoading, query, activeFilters, onFilterChange }: ResultsListProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-lg p-6 shadow-sm animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
            <div className="h-3 bg-gray-100 rounded w-1/4 mb-4"></div>
            <div className="space-y-2">
              <div className="h-3 bg-gray-100 rounded w-full"></div>
              <div className="h-3 bg-gray-100 rounded w-5/6"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!response) {
    return null;
  }

  if (response.results.length === 0) {
    return (
      <div className="bg-white rounded-lg p-8 shadow-sm text-center">
        <div className="text-gray-400 mb-3">
          <FileText className="h-12 w-12 mx-auto" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
        <p className="text-gray-500">
          No documents matched "{query}". Try different keywords or adjust your filters.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Results header */}
      <div className="flex items-center justify-between">
        <p className="text-gray-600">
          Found <span className="font-semibold text-gray-900">{response.total_count}</span> results for "{query}"
        </p>
      </div>

      {/* Facets */}
      {response.facets && Object.keys(response.facets).length > 0 && (
        <FacetPanel 
          facets={response.facets} 
          activeFilters={activeFilters}
          onFilterChange={onFilterChange}
        />
      )}

      {/* Results list */}
      <ul role="list" className="space-y-4">
        {response.results.map((result) => (
          <ResultCard key={result.document_id} result={result} />
        ))}
      </ul>
    </div>
  );
}

function ResultCard({ result }: { result: SearchResult }) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const getDocIcon = () => {
    if (result.abaer_citation?.includes('ABAER')) {
      return <Scale className="h-5 w-5" />;
    }
    return <FileText className="h-5 w-5" />;
  };

  const formatScore = (score: number) => {
    return Math.round(score * 100);
  };

  return (
    <li>
      <article className="bg-white rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow border border-gray-100">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className="flex-shrink-0 p-2 bg-aer-light-blue text-aer-blue rounded-lg">
            {getDocIcon()}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Title and citation */}
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
                  {result.title}
                </h3>
                {result.abaer_citation && (
                  <p className="text-sm text-aer-teal font-medium mt-1">
                    {result.abaer_citation}
                  </p>
                )}
              </div>
              <div className="flex-shrink-0">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  {formatScore(result.relevance_score)}% match
                </span>
              </div>
            </div>

            {/* Citation reference */}
            <p className="text-sm text-gray-500 mt-2 font-mono">
              📍 {result.citation_ref}
            </p>

            {/* Snippet */}
            <div className="mt-3 text-gray-700 text-sm leading-relaxed">
              <p className="line-clamp-3">{result.snippet}</p>
            </div>

            {/* Parties */}
            {result.parties && result.parties.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {result.parties.slice(0, 3).map((party, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-700 border border-blue-200"
                  >
                    👥 {party}
                  </span>
                ))}
                {result.parties.length > 3 && (
                  <span className="text-xs text-gray-400">
                    +{result.parties.length - 3} more parties
                  </span>
                )}
              </div>
            )}

            {/* Regulatory citations */}
            {result.regulatory_citations && result.regulatory_citations.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {result.regulatory_citations.slice(0, 5).map((citation, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600"
                  >
                    <BookOpen className="h-3 w-3 mr-1" />
                    {citation}
                  </span>
                ))}
                {result.regulatory_citations.length > 5 && (
                  <span className="text-xs text-gray-400">
                    +{result.regulatory_citations.length - 5} more
                  </span>
                )}
              </div>
            )}

            {/* View more button */}
            <button 
              onClick={() => setIsExpanded(!isExpanded)}
              className="mt-4 text-sm text-aer-teal font-medium hover:underline inline-flex items-center"
            >
              {isExpanded ? 'Collapse' : 'View in context'}
              {isExpanded ? <ChevronDown className="h-4 w-4 ml-1" /> : <ChevronRight className="h-4 w-4 ml-1" />}
            </button>
            
            {/* Expanded context panel */}
            {isExpanded && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-900">Full Context</h4>
                  <button 
                    onClick={() => setIsExpanded(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
                
                {/* Document info */}
                <div className="mb-4 pb-4 border-b border-gray-200">
                  <dl className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <dt className="text-gray-500">Document</dt>
                      <dd className="font-medium">{result.title}</dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Citation</dt>
                      <dd className="font-mono">{result.citation_ref}</dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Page</dt>
                      <dd>{result.page_number}</dd>
                    </div>
                    {result.paragraph_number && (
                      <div>
                        <dt className="text-gray-500">Paragraph</dt>
                        <dd>¶{result.paragraph_number}</dd>
                      </div>
                    )}
                  </dl>
                </div>
                
                {/* Full snippet text */}
                <div className="prose prose-sm max-w-none">
                  <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                    {result.snippet}
                  </p>
                </div>
                
                {/* Copy citation button */}
                <div className="mt-4 pt-4 border-t border-gray-200 flex gap-2">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(result.citation_ref);
                      alert('Citation copied to clipboard!');
                    }}
                    className="px-3 py-1.5 text-xs font-medium text-aer-teal border border-aer-teal rounded hover:bg-aer-light-blue"
                  >
                    Copy Citation
                  </button>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(result.snippet);
                      alert('Text copied to clipboard!');
                    }}
                    className="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
                  >
                    Copy Text
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </article>
    </li>
  );
}

function FacetPanel({ facets, activeFilters, onFilterChange }: { 
  facets: Record<string, FacetValue[]>;
  activeFilters: SearchFilters;
  onFilterChange: (filters: SearchFilters) => void;
}) {
  const facetLabels: Record<string, string> = {
    document_type: 'Document Types',
    parties: 'Parties',
    regulatory_citations: 'Cited Legislation',
  };

  const handleFacetClick = (facetKey: string, value: string) => {
    const newFilters = { ...activeFilters };
    
    if (facetKey === 'document_type') {
      const current = newFilters.document_types || [];
      if (current.includes(value as any)) {
        newFilters.document_types = current.filter(v => v !== value);
      } else {
        newFilters.document_types = [...current, value as any];
      }
    } else if (facetKey === 'parties') {
      const current = newFilters.parties || [];
      if (current.includes(value)) {
        newFilters.parties = current.filter(v => v !== value);
      } else {
        newFilters.parties = [...current, value];
      }
    } else if (facetKey === 'regulatory_citations') {
      const current = newFilters.regulatory_citations || [];
      if (current.includes(value)) {
        newFilters.regulatory_citations = current.filter(v => v !== value);
      } else {
        newFilters.regulatory_citations = [...current, value];
      }
    }
    
    onFilterChange(newFilters);
  };

  const isActive = (facetKey: string, value: string): boolean => {
    if (facetKey === 'document_type') {
      return (activeFilters.document_types || []).includes(value as any);
    } else if (facetKey === 'parties') {
      return (activeFilters.parties || []).includes(value);
    } else if (facetKey === 'regulatory_citations') {
      return (activeFilters.regulatory_citations || []).includes(value);
    }
    return false;
  };

  return (
    <div className="bg-aer-light-blue rounded-lg p-4">
      <h3 className="text-sm font-medium text-aer-blue mb-3">Quick Filters</h3>
      <div className="flex flex-wrap gap-6">
        {Object.entries(facets).map(([key, values]) => (
          values.length > 0 && (
            <div key={key}>
              <p className="text-xs text-gray-500 mb-1">{facetLabels[key] || key}</p>
              <div className="flex flex-wrap gap-1">
                {values.slice(0, 4).map((fv) => {
                  const active = isActive(key, fv.value);
                  return (
                    <button
                      key={fv.value}
                      onClick={() => handleFacetClick(key, fv.value)}
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs transition-colors ${
                        active 
                          ? 'bg-aer-teal text-white font-medium' 
                          : 'bg-white text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      {fv.value} <span className={active ? 'text-white opacity-75 ml-1' : 'text-gray-400 ml-1'}>({fv.count})</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )
        ))}
      </div>
    </div>
  );
}
