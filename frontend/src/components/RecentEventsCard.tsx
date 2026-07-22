import { useEffect, useRef, useState } from "react";
import type { LiveEvent } from "../types";
import styles from "./RecentEventsCard.module.css";

const MAX_LINES = 100;

export function RecentEventsCard({ event }: { event: LiveEvent | null }) {
  const [lines, setLines] = useState<string[]>([]);
  const lastEventRef = useRef<LiveEvent | null>(null);

  useEffect(() => {
    if (!event || event === lastEventRef.current) return;
    lastEventRef.current = event;
    const time = new Date(event.timestamp).toLocaleTimeString();
    const suffix = event.failure_reason ? ` — ${event.failure_reason}` : "";
    setLines((prev) => [...prev, `${time} ${event.node} ${event.message}${suffix}`].slice(-MAX_LINES));
  }, [event]);

  return (
    <div className={styles.card}>
      <h3>Recent Events</h3>
      <div className={styles.log}>
        {lines.map((line, i) => (
          <div key={i}>{line}</div>
        ))}
      </div>
    </div>
  );
}
