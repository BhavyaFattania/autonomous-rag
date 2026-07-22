import type { LiveEvent } from "../types";
import styles from "./ScientistThoughtCard.module.css"; // shared card styling

export function HypothesisCard({ event }: { event: LiveEvent | null }) {
  if (!event?.hypothesis) return null;
  return (
    <div className={styles.card}>
      <h3>Current Hypothesis</h3>
      <p>{event.hypothesis}</p>
    </div>
  );
}
