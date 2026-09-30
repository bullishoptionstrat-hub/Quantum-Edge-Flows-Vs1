'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

export interface PolledState<T> {
  status: 'loading' | 'ok' | 'error';
  /** The last payload that parsed. Kept through later failures so a panel can show it as stale. */
  data?: T;
  error?: string;
  /** When `data` was fetched, in epoch milliseconds. */
  fetchedAt?: number;
}

/**
 * Fetch JSON from `url`, validate it with `parse` (return null to reject the shape) and, with `intervalMs`,
 * poll it — the next request is scheduled only after the previous one settles. A new url starts from
 * loading; a failed request keeps the previous data and reports the error, so a panel never shows an
 * outage as an empty list.
 */
export function usePolledJson<T>(url: string, parse: (json: unknown) => T | null, intervalMs?: number) {
  const [entry, setEntry] = useState<{ url: string; state: PolledState<T> }>({ url, state: { status: 'loading' } });
  const [attempt, setAttempt] = useState(0);
  const parseRef = useRef(parse);
  useEffect(() => {
    parseRef.current = parse;
  });

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let controller: AbortController | undefined;

    const run = async () => {
      controller = new AbortController();
      try {
        const res = await fetch(url, { signal: controller.signal, cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = parseRef.current(await res.json());
        if (data === null) throw new Error('Unexpected response shape');
        if (!cancelled) setEntry({ url, state: { status: 'ok', data, fetchedAt: Date.now() } });
      } catch (err) {
        if (cancelled) return;
        const error = err instanceof TypeError ? 'API unreachable' : err instanceof Error ? err.message : 'Request failed';
        setEntry((prev) => {
          const same = prev.url === url;
          return { url, state: { status: 'error', error, data: same ? prev.state.data : undefined, fetchedAt: same ? prev.state.fetchedAt : undefined } };
        });
      } finally {
        if (!cancelled && intervalMs) timer = setTimeout(run, intervalMs);
      }
    };

    void run();
    return () => {
      cancelled = true;
      controller?.abort();
      if (timer) clearTimeout(timer);
    };
  }, [url, intervalMs, attempt]);

  const retry = useCallback(() => setAttempt((n) => n + 1), []);
  const state: PolledState<T> = entry.url === url ? entry.state : { status: 'loading' };
  return { state, retry };
}
