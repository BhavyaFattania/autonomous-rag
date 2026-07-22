import { useEffect, useRef, useState } from "react";
import type { DashboardState, LiveEvent, LivePayload } from "../types";

export function useLiveSocket() {
  const [event, setEvent] = useState<LiveEvent | null>(null);
  const [state, setState] = useState<DashboardState | null>(null);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;

    function connect() {
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      const socket = new WebSocket(`${protocol}://${window.location.host}/ws/live`);
      socketRef.current = socket;

      socket.onopen = () => {
        if (!cancelled) setConnected(true);
      };

      socket.onmessage = (raw) => {
        const payload: LivePayload = JSON.parse(raw.data);
        if (cancelled) return;
        setEvent(payload.event);
        setState(payload.state);
      };

      socket.onclose = () => {
        if (cancelled) return;
        setConnected(false);
        // Reconnect after a short delay -- the dashboard should recover
        // automatically if the backend restarts mid-run.
        reconnectTimeoutRef.current = window.setTimeout(connect, 1000);
      };

      socket.onerror = () => {
        socket.close();
      };
    }

    connect();

    return () => {
      cancelled = true;
      window.clearTimeout(reconnectTimeoutRef.current);
      socketRef.current?.close();
    };
  }, []);

  return { event, state, connected };
}
