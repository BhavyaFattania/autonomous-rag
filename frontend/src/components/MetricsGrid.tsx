import type { LiveEvent } from "../types";
import styles from "./MetricsGrid.module.css";

const TILES: Array<{ key: string; label: string }> = [
  { key: "median_weighted_score", label: "Weighted Score" },
  { key: "median_recall_at_k", label: "Recall@K" },
  { key: "median_mrr", label: "MRR" },
  { key: "median_context_precision", label: "Context Precision" },
  { key: "median_ndcg_at_k", label: "NDCG@K" },
  { key: "median_faithfulness", label: "Faithfulness" },
  { key: "median_answer_relevancy", label: "Answer Relevancy" },
  { key: "median_context_recall", label: "Context Recall" },
  { key: "std_dev_weighted_score", label: "Std Dev (Weighted)" },
];

export function MetricsGrid({ event }: { event: LiveEvent | null }) {
  if (!event?.metrics || Object.keys(event.metrics).length === 0) return null;

  return (
    <div className={styles.grid}>
      <h3 className={styles.heading}>Metrics (Last Completed: #{event.experiment})</h3>
      <div className={styles.tiles}>
        {TILES.filter((tile) => event.metrics[tile.key] !== undefined).map((tile) => (
          <div key={tile.key} className={styles.tile}>
            <span className={styles.tileLabel}>{tile.label}</span>
            <span className={styles.tileValue}>{event.metrics[tile.key].toFixed(3)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
