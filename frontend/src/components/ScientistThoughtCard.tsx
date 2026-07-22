import type { LiveEvent } from "../types";
import styles from "./ScientistThoughtCard.module.css";

export function ScientistThoughtCard({ event }: { event: LiveEvent | null }) {
  if (!event?.reasoning) return null;
  return (
    <div className={styles.card}>
      <h3>Scientist Thought</h3>
      <p>{event.reasoning}</p>
    </div>
  );
}
