import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import { ACTIVE_JOB_STATES, type Job } from './areaTypes';
import type { CandidateInput, CandidatePatch } from './types';

export const isActiveJob = (j: Job | undefined) => !!j && ACTIVE_JOB_STATES.includes(j.state);

/** Jobs still running on the server (re-attaches the progress panel after a reload). */
export const useActiveJobs = () =>
  useQuery({ queryKey: ['jobs', 'active'], queryFn: api.activeJobs, staleTime: 0 });

/** Polls once per second while the job is active, then stops. */
export const useJob = (id: string | null) =>
  useQuery({
    queryKey: ['job', id],
    queryFn: () => api.job(id as string),
    enabled: !!id,
    refetchInterval: (q) => (!q.state.data || isActiveJob(q.state.data) ? 1000 : false),
  });

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
