import { useState, useEffect } from 'react';
import { getAdvisory } from '../services/api';
import { Advisory } from '../services/types';

export function useAdvisory(eventId: number | string | null) {
  const [data, setData] = useState<Advisory | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (eventId === null) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }

    let mounted = true;
    setLoading(true);
    setError(null);

    getAdvisory(eventId)
      .then((res) => {
        if (mounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err);
          setLoading(false);
          setData(null);
        }
      });

    return () => {
      mounted = false;
    };
  }, [eventId]);

  return { data, loading, error };
}
