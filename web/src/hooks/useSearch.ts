import { useMutation, useQueryClient } from '@tanstack/react-query';
import { searchDocuments } from '../api/client';
import { SearchRequest, SearchResponse } from '../types';

export function useSearch() {
  const queryClient = useQueryClient();

  const mutation = useMutation<SearchResponse, Error, SearchRequest>({
    mutationFn: searchDocuments,
    onSuccess: (data, variables) => {
      // Cache the result
      queryClient.setQueryData(['search', variables.query], data);
    },
  });

  return {
    search: mutation.mutate,
    searchAsync: mutation.mutateAsync,
    data: mutation.data,
    isLoading: mutation.isPending,
    error: mutation.error,
    reset: mutation.reset,
  };
}
