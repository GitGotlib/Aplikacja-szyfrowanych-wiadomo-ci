import { useMemo } from 'react';
import { useLocation } from 'react-router-dom';

export function useQueryParam(name: string): string | null {
  const loc = useLocation();
  return useMemo(() => {
    const sp = new URLSearchParams(loc.search);
    return sp.get(name);
  }, [loc.search, name]);
}
