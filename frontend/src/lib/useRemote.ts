import { useEffect, useRef, useState } from 'react';

export type Remote<T> = { state: 'loading' | 'ready' | 'error'; data: T | null; error: unknown };
export function useRemote<T>(load: (signal: AbortSignal) => Promise<T>, dependencies: unknown[]): Remote<T> {
  const loader = useRef(load); loader.current = load;
  const [value, setValue] = useState<Remote<T>>({ state: 'loading', data: null, error: null });
  useEffect(() => {
    const controller = new AbortController();
    setValue({ state: 'loading', data: null, error: null });
    loader.current(controller.signal).then(data => {
      if (!controller.signal.aborted) setValue({ state: 'ready', data, error: null });
    }).catch(error => { if (!controller.signal.aborted) setValue({ state: 'error', data: null, error }); });
    return () => controller.abort();
  }, dependencies);
  return value;
}
