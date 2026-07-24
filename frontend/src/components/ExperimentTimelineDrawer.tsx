import { useEffect, useRef, useState } from "react";
import { fetchExperimentEvents, type NodeEventRecord } from "../api/history";
import styles from "./ExperimentTimelineDrawer.module.css";

interface Props {
  experimentUuid: string | null;
  highlightNode?: string | null;
  onClose: () => void;
}

function parseJson(value: string | null): Record<string, unknown> | null {
  if (!value) return null;
  try {
    const parsed = JSON.parse(value);
    return typeof parsed === "object" && parsed !== null ? parsed : null;
  } catch {
    return null;
  }
}

export function ExperimentTimelineDrawer({ experimentUuid, highlightNode, onClose }: Props) {
  const [events, setEvents] = useState<NodeEventRecord[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "error" | "ready">("idle");
  const highlightRef = useRef<HTMLLIElement | null>(null);

  useEffect(() => {
    if (!experimentUuid) return;
    let cancelled = false;
    setStatus("loading");
    fetchExperimentEvents(experimentUuid)
      .then((rows) => {
        if (cancelled) return;
        setEvents(rows);
        setStatus("ready");
      })
      .catch(() => {
        if (cancelled) return;
        setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [experimentUuid]);

  useEffect(() => {
    if (status === "ready" && highlightRef.current) {
      highlightRef.current.scrollIntoView({ block: "center" });
    }
  }, [status]);

  useEffect(() => {
    if (!experimentUuid) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [experimentUuid, onClose]);

  if (!experimentUuid) return null;

  const hypothesis = events.find((event) => event.hypothesis)?.hypothesis;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <aside
        className={styles.drawer}
        onClick={(e) => e.stopPropagation()}
        aria-label="Experiment timeline"
      >
        <header className={styles.header}>
          <div>
            <h2>Experiment Timeline</h2>
            {hypothesis && <p className={styles.hypothesis}>{hypothesis}</p>}
            <span className={styles.uuid}>{experimentUuid}</span>
          </div>
          <button className={styles.close} onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>

        <div className={styles.body}>
          {status === "loading" && <p className={styles.status}>Loading…</p>}
          {status === "error" && (
            <p className={styles.error}>
              Couldn't load this experiment's history.{" "}
              <button
                className={styles.retry}
                onClick={() => {
                  setStatus("loading");
                  fetchExperimentEvents(experimentUuid)
                    .then((rows) => {
                      setEvents(rows);
                      setStatus("ready");
                    })
                    .catch(() => setStatus("error"));
                }}
              >
                Retry
              </button>
            </p>
          )}
          {status === "ready" && events.length === 0 && (
            <p className={styles.empty}>
              No detailed history recorded for this experiment — it predates event logging.
            </p>
          )}
          {status === "ready" && events.length > 0 && (
            <ol className={styles.timeline}>
              {events.map((event) => {
                const config = parseJson(event.config_json);
                const metrics = parseJson(event.metrics_json);
                const isHighlighted = highlightNode === event.node;
                return (
                  <li
                    key={event.id}
                    ref={isHighlighted ? highlightRef : null}
                    className={styles.entry}
                    data-status={event.status}
                    data-highlighted={isHighlighted}
                  >
                    <div className={styles.entryHeader}>
                      <span className={styles.node}>{event.node.replace(/_/g, " ")}</span>
                      <span className={styles.entryStatus}>{event.status.toLowerCase()}</span>
                      <time className={styles.time}>
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </time>
                    </div>
                    {event.message && <p className={styles.message}>{event.message}</p>}
                    {event.reasoning && <p className={styles.reasoning}>{event.reasoning}</p>}
                    {event.failure_reason && (
                      <p className={styles.failure}>{event.failure_reason}</p>
                    )}
                    {event.progress_current != null && event.progress_total != null && (
                      <p className={styles.progress}>
                        {event.progress_current} / {event.progress_total}
                      </p>
                    )}
                    {config && Object.keys(config).length > 0 && (
                      <dl className={styles.kv}>
                        {Object.entries(config).map(([key, value]) => (
                          <div key={key} className={styles.kvRow}>
                            <dt>{key}</dt>
                            <dd>{String(value)}</dd>
                          </div>
                        ))}
                      </dl>
                    )}
                    {metrics && Object.keys(metrics).length > 0 && (
                      <dl className={styles.kv}>
                        {Object.entries(metrics).map(([key, value]) => (
                          <div key={key} className={styles.kvRow}>
                            <dt>{key}</dt>
                            <dd>{typeof value === "number" ? value.toFixed(3) : String(value)}</dd>
                          </div>
                        ))}
                      </dl>
                    )}
                  </li>
                );
              })}
            </ol>
          )}
        </div>
      </aside>
    </div>
  );
}
