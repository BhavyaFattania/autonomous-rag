import { useEffect, useState } from "react";
import { fetchRunEvents, fetchRuns, type NodeEventRecord, type RunSummary } from "../api/history";
import styles from "./LogFeedPage.module.css";

const NODES = [
  "scientist",
  "validator",
  "deduplicator",
  "budget_guard",
  "indexer",
  "smoke_test",
  "evaluator",
  "acceptance",
  "recorder",
  "reflection",
  "report_writer",
];

const STATUSES = [
  "RUNNING",
  "PENDING",
  "ACCEPTED",
  "COMPETITIVE",
  "REJECTED",
  "FAILED_SMOKE",
  "FAILED_TIMEOUT",
  "FAILED_DUPLICATE",
  "FAILED_VALIDATION",
  "FAILED_API_ERROR",
  "BUDGET_EXCEEDED",
  "INTERRUPTED",
];

const PAGE_SIZE = 50;

interface Props {
  onOpenExperiment: (experimentUuid: string, node: string) => void;
}

export function LogFeedPage({ onOpenExperiment }: Props) {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [runId, setRunId] = useState<string>("");
  const [node, setNode] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [events, setEvents] = useState<NodeEventRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRuns()
      .then((rows) => {
        setRuns(rows);
        if (rows.length > 0) setRunId(rows[0].run_id);
      })
      .catch(() => setError("Failed to load runs"));
  }, []);

  useEffect(() => {
    if (!runId) return;
    setLoading(true);
    setError(null);
    fetchRunEvents(runId, { node: node || undefined, status: status || undefined, limit: PAGE_SIZE })
      .then((rows) => {
        setEvents(rows);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load events");
        setLoading(false);
      });
  }, [runId, node, status]);

  function loadMore() {
    if (!runId || events.length === 0) return;
    setLoading(true);
    fetchRunEvents(runId, {
      node: node || undefined,
      status: status || undefined,
      limit: PAGE_SIZE,
      beforeId: events[events.length - 1].id,
    })
      .then((rows) => {
        setEvents((prev) => [...prev, ...rows]);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load more events");
        setLoading(false);
      });
  }

  return (
    <div className={styles.page}>
      <div className={styles.filters}>
        <select
          className={styles.select}
          value={runId}
          onChange={(e) => setRunId(e.target.value)}
        >
          {runs.map((run) => (
            <option key={run.run_id} value={run.run_id}>
              {run.run_id} ({new Date(run.started_at).toLocaleString()})
            </option>
          ))}
        </select>
        <select className={styles.select} value={node} onChange={(e) => setNode(e.target.value)}>
          <option value="">All nodes</option>
          {NODES.map((n) => (
            <option key={n} value={n}>
              {n.replace(/_/g, " ")}
            </option>
          ))}
        </select>
        <select
          className={styles.select}
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {error && <p className={styles.error}>{error}</p>}
      {!error && runs.length === 0 && !loading && (
        <p className={styles.empty}>No runs recorded yet.</p>
      )}

      {events.length > 0 && (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Time</th>
              <th>Exp</th>
              <th>Node</th>
              <th>Status</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr
                key={event.id}
                onClick={() => event.experiment_uuid && onOpenExperiment(event.experiment_uuid, event.node)}
              >
                <td className={styles.mono}>{new Date(event.timestamp).toLocaleTimeString()}</td>
                <td className={styles.mono}>#{event.experiment_seq}</td>
                <td>{event.node.replace(/_/g, " ")}</td>
                <td data-status={event.status}>{event.status.toLowerCase()}</td>
                <td className={styles.message}>{event.failure_reason || event.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {!error && runId && events.length === 0 && !loading && (
        <p className={styles.empty}>No events match these filters.</p>
      )}

      {events.length > 0 && events.length % PAGE_SIZE === 0 && (
        <button className={styles.loadMore} onClick={loadMore} disabled={loading}>
          {loading ? "Loading…" : "Load more"}
        </button>
      )}
    </div>
  );
}
