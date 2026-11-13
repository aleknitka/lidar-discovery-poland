import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type { CandidateInput, CandidatePatch } from './types';

export const useLocations = () => useQuery({ queryKey: ['locations'], queryFn: api.locations });

export const useLocation = (id: string | null) =>
  useQuery({
    queryKey: ['location', id],
    queryFn: () => api.location(id as string),
    enabled: !!id,
  });

export const useCoverage = (id: string | null) =>
  useQuery({
    queryKey: ['coverage', id],
    queryFn: () => api.coverage(id as string),
    enabled: !!id,
  });

export const useLayers = (id: string | null) =>
  useQuery({
    queryKey: ['layers', id],
    queryFn: () => api.layers(id as string),
    enabled: !!id,
  });

export const useCandidates = (filter: { location_id?: string; review_status?: string } = {}) =>
  useQuery({ queryKey: ['candidates', filter], queryFn: () => api.candidates(filter) });

export function useCreateCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CandidateInput) => api.createCandidate(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['candidates'] }),
  });
}

export function useUpdateCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: CandidatePatch }) =>
      api.updateCandidate(id, patch),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['candidates'] }),
  });
}
