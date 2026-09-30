'use client';

import { AlertItem, Button, Panel, PanelState } from '@/design-system';
import { usePolledJson } from '@/hooks/usePolledJson';
import { API_URL, parseAlerts } from '@/lib/terminal-api';
import { formatEtTime } from '@/lib/time';

const POLL_MS = 3000;

export default function AlertsPanel() {
  const { state, retry } = usePolledJson(`${API_URL}/api/alerts?limit=20`, parseAlerts, POLL_MS);
  const alerts = state.data;

  let body;
  if (!alerts) {
    body =
      state.status === 'error' ? (
        <PanelState
          kind="error"
          title="Could not load alerts"
          action={
            <Button size="sm" icon="rotate-cw" onClick={retry}>
              Retry
            </Button>
          }
        >
          {state.error}. An empty list would look final, so none is shown.
        </PanelState>
      ) : (
        <PanelState kind="loading" title="Loading alerts" />
      );
  } else if (alerts.length === 0) {
    body = <PanelState kind="empty" title="No alerts" />;
  } else {
    body = (
      <ul className="qe-list">
        {alerts.map((a) => (
          <li key={a.id}>
            <AlertItem
              severity={a.severity}
              type={a.type}
              message={a.message}
              time={a.sentAt !== undefined ? formatEtTime(a.sentAt) : undefined}
              unread={a.unread}
            />
          </li>
        ))}
      </ul>
    );
  }

  return (
    <Panel title="Alerts" scroll>
      {state.status === 'error' && alerts ? (
        <PanelState kind="stale" title={state.fetchedAt !== undefined ? `Showing alerts from ${formatEtTime(state.fetchedAt)}` : 'Showing earlier alerts'}>
          Refresh failed: {state.error}. Retrying every {POLL_MS / 1000}s.
        </PanelState>
      ) : null}
      {body}
    </Panel>
  );
}
