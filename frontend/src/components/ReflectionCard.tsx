import type { LiveEvent } from "../types";
import styles from "./ScientistThoughtCard.module.css"; // shared card styling

export function ReflectionCard({ event }: { event: LiveEvent | null }) {
  if (event?.node !== "reflection" || !event.reasoning) return null;
  return (
    <div className={styles.card} data-variant="green">
      <h3>Reflection (After #{event.experiment})</h3>
      <p>{event.reasoning}</p>
    </div>
  );
}
