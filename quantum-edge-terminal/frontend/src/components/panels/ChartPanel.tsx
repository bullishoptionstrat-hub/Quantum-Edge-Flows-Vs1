'use client';

import { Button, FeedStatus, Panel, PanelState, PriceChart } from '@/design-system';
import { usePolledJson } from '@/hooks/usePolledJson';
import { displayTickSize } from '@/lib/instruments';
import { API_URL, parseCandles } from '@/lib/terminal-api';
import { formatAge, formatBarLabel, formatEtTime, isStale } from '@/lib/time';

interface ChartPanelProps {
  symbol: string;
  timeframe: string;
}

export default function ChartPanel({ symbol, timeframe }: ChartPanelProps) {
  const url = `${API_URL}/api/market-data/candles/${encodeURIComponent(symbol)}/${encodeURIComponent(timeframe)}?limit=50`;
  const { state, retry } = usePolledJson(url, parseCandles);
  const candles = state.data;
  const last = candles?.[candles.length - 1];
  const age = last && state.fetchedAt !== undefined ? state.fetchedAt - last.time : undefined;
  const retryButton = (
    <Button size="sm" icon="rotate-cw" onClick={retry}>
      Retry
    </Button>
  );

  let meta = null;
  if (last && age !== undefined) {
    meta = isStale(age, timeframe) ? (
      <FeedStatus state="stale" detail={`${timeframe} · last bar ${formatEtTime(last.time)}`} age={formatAge(age)} />
    ) : (
      <span className="qe-data">
        {timeframe} · last bar {formatEtTime(last.time)}
      </span>
    );
  }

  let body;
  if (!candles) {
    body =
      state.status === 'error' ? (
        <PanelState kind="error" title={`Could not load ${symbol} ${timeframe} candles`} action={retryButton}>
          {state.error}
        </PanelState>
      ) : (
        <PanelState kind="loading" title={`Loading ${symbol} ${timeframe} candles`} />
      );
  } else if (candles.length === 0) {
    body = (
      <PanelState kind="empty" title={`No ${symbol} ${timeframe} candles`}>
        The API returned no bars for this symbol and timeframe.
      </PanelState>
    );
  } else {
    body = (
      <>
        {state.status === 'error' ? (
          <PanelState kind="stale" title="Refresh failed" action={retryButton}>
            {state.error}. Showing the candles loaded{state.fetchedAt !== undefined ? ` at ${formatEtTime(state.fetchedAt)}` : ''}.
          </PanelState>
        ) : null}
        <PriceChart
          label={`${symbol} ${timeframe} closes`}
          data={candles.map((c) => ({ t: formatBarLabel(c.time, timeframe), close: c.close }))}
          tickSize={displayTickSize(symbol)}
        />
      </>
    );
  }

  return (
    <Panel title={`${symbol} price`} meta={meta}>
      {body}
    </Panel>
  );
}
