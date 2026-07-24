import { useState } from "react";
import { BestConfigPanel } from "./components/BestConfigPanel";
import { BudgetOverviewPanel } from "./components/BudgetOverviewPanel";
import { ConfigDiffCard } from "./components/ConfigDiffCard";
import { CurrentConfigPanel } from "./components/CurrentConfigPanel";
import { ExperimentDetailPage } from "./components/ExperimentDetailPage";
import { ExperimentSidebar } from "./components/ExperimentSidebar";
import { ExperimentTimelineDrawer } from "./components/ExperimentTimelineDrawer";
import { HypothesisCard } from "./components/HypothesisCard";
import { LogFeedPage } from "./components/LogFeedPage";
import { MetricsGrid } from "./components/MetricsGrid";
import { NavTabs, type NavTab } from "./components/NavTabs";
import { PipelineStrip } from "./components/PipelineStrip";
import { RecentEventsCard } from "./components/RecentEventsCard";
import { ReflectionCard } from "./components/ReflectionCard";
import { RunsListPage } from "./components/RunsListPage";
import { ScientistThoughtCard } from "./components/ScientistThoughtCard";
import { TopBar } from "./components/TopBar";
import { useLiveSocket } from "./hooks/useLiveSocket";
import "./App.css";

type View = { name: "live" } | { name: "runs" } | { name: "log" } | { name: "experiment"; id: number };

interface DrawerTarget {
  experimentUuid: string;
  node?: string;
}

function viewToTab(view: View): NavTab {
  if (view.name === "experiment") return "runs";
  return view.name;
}

function App() {
  const { event, state, connected } = useLiveSocket();
  const [view, setView] = useState<View>({ name: "live" });
  const [drawer, setDrawer] = useState<DrawerTarget | null>(null);

  function openDrawer(experimentUuid: string, node?: string) {
    setDrawer({ experimentUuid, node });
  }

  return (
    <div className="app">
      <NavTabs
        active={viewToTab(view)}
        onSelect={(tab) => {
          if (tab === "live") setView({ name: "live" });
          else if (tab === "runs") setView({ name: "runs" });
          else setView({ name: "log" });
        }}
      />

      {view.name === "runs" && (
        <RunsListPage
          onBack={() => setView({ name: "live" })}
          onSelectExperiment={(id) => setView({ name: "experiment", id })}
        />
      )}

      {view.name === "experiment" && (
        <ExperimentDetailPage experimentId={view.id} onBack={() => setView({ name: "runs" })} />
      )}

      {view.name === "log" && <LogFeedPage onOpenExperiment={openDrawer} />}

      {view.name === "live" && (
        <>
          <TopBar event={event} state={state} connected={connected} />
          <PipelineStrip state={state} onSelectNode={openDrawer} />
          <div className="layout">
            <ExperimentSidebar
              state={state}
              onViewAll={() => setView({ name: "runs" })}
              onSelectExperiment={openDrawer}
            />
            <main className="mainGrid">
              <ScientistThoughtCard event={event} />
              <HypothesisCard event={event} />
              <ConfigDiffCard event={event} state={state} />
              <MetricsGrid event={event} />
              <ReflectionCard event={event} />
              <RecentEventsCard event={event} state={state} />
            </main>
            <div className="rightRail">
              <CurrentConfigPanel event={event} />
              <BestConfigPanel state={state} />
              <BudgetOverviewPanel state={state} />
            </div>
          </div>
        </>
      )}

      <ExperimentTimelineDrawer
        experimentUuid={drawer?.experimentUuid ?? null}
        highlightNode={drawer?.node}
        onClose={() => setDrawer(null)}
      />
    </div>
  );
}

export default App;
