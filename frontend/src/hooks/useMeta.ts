import { useState, useEffect } from 'react';
import { getMeta } from '../services/api';
import { MetaResponse } from '../services/types';

let cachedMeta: MetaResponse | null = null;

export function useMeta() {
  const [data, setData] = useState<MetaResponse | null>(cachedMeta);
  const [loading, setLoading] = useState<boolean>(!cachedMeta);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (cachedMeta) return;

    let mounted = true;
    setLoading(true);
    getMeta()
      .then((meta) => {
        if (mounted) {
          cachedMeta = meta;
          setData(meta);
          setLoading(false);
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
  }, []);

  return { data, loading, error };
}
