'use client';

import { useEffect, useState } from 'react';
import AlertsPanel from '@/components/panels/AlertsPanel';
import ChartPanel from '@/components/panels/ChartPanel';
import SignalsPanel from '@/components/panels/SignalsPanel';
import { FeedStatus, IconButton, TerminalHeader, ToggleGroup } from '@/design-system';
import { useWebSocket } from '@/hooks/useWebSocket';

const SYMBOLS = ['ES', 'NQ', 'GC', 'SPY', 'QQQ'];
const TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1D'];

export default function Dashboard() {
  const [symbol, setSymbol] = useState('ES');
  const [timeframe, setTimeframe] = useState('1h');
  const { isConnected, subscribe } = useWebSocket();

  useEffect(() => {
    if (isConnected) {
      subscribe('candles', { symbol, timeframe });
    }
  }, [symbol, timeframe, isConnected, subscribe]);

  return (
    <main className="qe-page">
      <TerminalHeader>
        {/* The stream's connection state; each panel reports the age of its own data. */}
        <FeedStatus state={isConnected ? 'live' : 'disconnected'} source="Stream" />
        <IconButton icon="menu" label="Menu" />
        <IconButton icon="settings" label="Settings" />
      </TerminalHeader>

      <div className="qe-stack mb-6">
        <ToggleGroup label="Symbol" options={SYMBOLS} value={symbol} onChange={setSymbol} />
        <ToggleGroup label="Timeframe" tone="alt" size="sm" options={TIMEFRAMES} value={timeframe} onChange={setTimeframe} />
      </div>

      <div className="qe-grid">
        <div className="qe-col-8">
          <ChartPanel symbol={symbol} timeframe={timeframe} />
        </div>
        <div className="qe-col-4 qe-stack">
          <SignalsPanel />
          <AlertsPanel />
        </div>
      </div>
    </main>
  );
}
