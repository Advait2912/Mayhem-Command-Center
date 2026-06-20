import { useState, useEffect, useCallback } from 'react';
import { getOutcomes, postOutcome } from '../services/api';
import { OutcomeListResponse, OutcomeCreateRequest } from '../services/types';

export function useOutcomes() {
  const [data, setData] = useState<OutcomeListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const fetchOutcomes = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getOutcomes();
      setData(res);
      setError(null);
    } catch (err: any) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOutcomes();
  }, [fetchOutcomes]);

  const submitOutcome = async (body: OutcomeCreateRequest) => {
    setIsSubmitting(true);
    try {
      const res = await postOutcome(body);
      // Auto-refresh the list after a successful submission
      await fetchOutcomes();
      return res;
    } catch (err: any) {
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  };

  return { data, loading, error, submitOutcome, isSubmitting, refresh: fetchOutcomes };
}
