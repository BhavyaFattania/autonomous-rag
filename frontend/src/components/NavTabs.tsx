import styles from "./NavTabs.module.css";

export type NavTab = "live" | "runs" | "log";

interface Props {
  active: NavTab;
  onSelect: (tab: NavTab) => void;
}

const TABS: { id: NavTab; label: string }[] = [
  { id: "live", label: "Live" },
  { id: "runs", label: "Runs" },
  { id: "log", label: "Log" },
];

export function NavTabs({ active, onSelect }: Props) {
  return (
    <nav className={styles.nav}>
      {TABS.map((tab) => (
        <button
          key={tab.id}
          className={styles.tab}
          data-active={active === tab.id}
          onClick={() => onSelect(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
