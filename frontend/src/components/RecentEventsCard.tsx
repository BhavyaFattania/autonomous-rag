import { useEffect, useRef, useState } from "react";
import type { DashboardState, LiveEvent } from "../types";
import { Sparkline } from "./Sparkline";
import styles from "./RecentEventsCard.module.css";

const MAX_LINES = 100;

interface Props {
  event: LiveEvent | null;
  state: DashboardState | null;
}

export function RecentEventsCard({ event, state }: Props) {
  const [lines, setLines] = useState<string[]>([]);
  const lastEventRef = useRef<LiveEvent | null>(null);

  useEffect(() => {
    if (!event || event === lastEventRef.current) return;
    lastEventRef.current = event;
    const time = new Date(event.timestamp).toLocaleTimeString();
    const suffix = event.failure_reason ? ` — ${event.failure_reason}` : "";
    setLines((prev) => [...prev, `${time} ${event.node} ${event.message}${suffix}`].slice(-MAX_LINES));
  }, [event]);

  const scores = (state?.history ?? []).map((row) => row.score);

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h3>Recent Events</h3>
        {scores.length >= 2 && (
          <div className={styles.trend}>
            <span className={styles.trendLabel}>Score Trend</span>
            <Sparkline values={scores} color="var(--signal-violet)" />
          </div>
        )}
      </div>
      <div className={styles.log}>
        {lines.map((line, i) => (
          <div key={i} className={styles.logLine}>
            {line}
          </div>
        ))}
      </div>
    </div>
  );
}
