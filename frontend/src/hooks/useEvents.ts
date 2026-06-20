import { useState, useEffect } from 'react';
import { getEvents } from '../services/api';
import { EventListResponse } from '../services/types';

interface EventsFilters {
  search?: string;
  cause?: string;
  zone?: string;
  track?: string;
  limit?: number;
  offset?: number;
}

export function useEvents(filters: EventsFilters) {
  const [data, setData] = useState<EventListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  // Stringify filters so we can reliably use them in the dependency array
  const filterKey = JSON.stringify(filters);

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    getEvents(filters)
      .then((res) => {
        if (mounted) {
          setData(res);
          setLoading(false);
          setError(null);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err);
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterKey]);

  return { data, loading, error };
}
