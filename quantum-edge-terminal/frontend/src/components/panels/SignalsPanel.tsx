'use client';

import { Button, Panel, PanelState, SignalCard } from '@/design-system';
import { usePolledJson } from '@/hooks/usePolledJson';
import { displayTickSize } from '@/lib/instruments';
import { API_URL, parseSignals } from '@/lib/terminal-api';
import { formatEtTime } from '@/lib/time';

const POLL_MS = 5000;

export default function SignalsPanel() {
  const { state, retry } = usePolledJson(`${API_URL}/api/signals?status=ACTIVE`, parseSignals, POLL_MS);
  const list = state.data;

  let body;
  if (!list) {
    body =
      state.status === 'error' ? (
        <PanelState
          kind="error"
          title="Could not load signals"
          action={
            <Button size="sm" icon="rotate-cw" onClick={retry}>
              Retry
            </Button>
          }
        >
          {state.error}. An empty list would look final, so none is shown.
        </PanelState>
      ) : (
        <PanelState kind="loading" title="Loading signals" />
      );
  } else if (list.signals.length === 0) {
    body = <PanelState kind="empty" title="No active signals" />;
  } else {
    body = (
      <ul className="qe-list">
        {list.signals.map((s) => (
          <li key={s.id}>
            <SignalCard
              symbol={s.symbol}
              side={s.side}
              state={s.status}
              entry={s.entry}
              stop={s.stop}
              targets={s.target !== undefined ? [s.target] : []}
              tickSize={displayTickSize(s.symbol)}
              time={s.createdAt !== undefined ? formatEtTime(s.createdAt) : undefined}
            />
          </li>
        ))}
      </ul>
    );
  }

  return (
    <Panel title="Active signals" scroll>
      {state.status === 'error' && list ? (
        <PanelState kind="stale" title={state.fetchedAt !== undefined ? `Showing signals from ${formatEtTime(state.fetchedAt)}` : 'Showing earlier signals'}>
          Refresh failed: {state.error}. Retrying every {POLL_MS / 1000}s.
        </PanelState>
      ) : null}
      {body}
      {list && list.skipped > 0 ? (
        <p className="qe-body-sm text-ink-muted mt-2">
          {list.skipped} {list.skipped === 1 ? 'signal is' : 'signals are'} hidden: not BUY or SELL, or missing a symbol or entry.
        </p>
      ) : null}
    </Panel>
  );
}
