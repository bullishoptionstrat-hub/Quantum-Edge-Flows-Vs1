'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  // A ref, not state: nothing renders from the socket, and subscribe() reads it when called.
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001/ws';
    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    websocket.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    wsRef.current = websocket;

    return () => {
      websocket.close();
      if (wsRef.current === websocket) {
        wsRef.current = null;
      }
    };
  }, []);

  const subscribe = useCallback(
    (channel: string, options: any) => {
      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(
          JSON.stringify({
            action: 'subscribe',
            channel,
            ...options,
          })
        );
      }
    },
    []
  );

  return { isConnected, subscribe };
}
