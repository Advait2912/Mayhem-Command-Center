import { useState } from 'react';
import { predict } from '../services/api';
import { Advisory, PredictRequest } from '../services/types';

export function usePredict() {
  const [data, setData] = useState<Advisory | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = async (body: PredictRequest) => {
    setLoading(true);
    setError(null);
    try {
      const res = await predict(body);
      setData(res);
      return res;
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setData(null);
    setError(null);
  };

  return { execute, reset, data, loading, error };
}
