import { useState } from "react";
import { BestConfigPanel } from "./components/BestConfigPanel";
import { BudgetOverviewPanel } from "./components/BudgetOverviewPanel";
import { ConfigDiffCard } from "./components/ConfigDiffCard";
import { CurrentConfigPanel } from "./components/CurrentConfigPanel";
import { ExperimentDetailPage } from "./components/ExperimentDetailPage";
import { ExperimentSidebar } from "./components/ExperimentSidebar";
import { HypothesisCard } from "./components/HypothesisCard";
import { MetricsGrid } from "./components/MetricsGrid";
import { PipelineStrip } from "./components/PipelineStrip";
import { RecentEventsCard } from "./components/RecentEventsCard";
import { ReflectionCard } from "./components/ReflectionCard";
import { RunsListPage } from "./components/RunsListPage";
import { ScientistThoughtCard } from "./components/ScientistThoughtCard";
import { TopBar } from "./components/TopBar";
import { useLiveSocket } from "./hooks/useLiveSocket";
import "./App.css";

type View = { name: "live" } | { name: "runs" } | { name: "experiment"; id: number };

function App() {
  const { event, state, connected } = useLiveSocket();
  const [view, setView] = useState<View>({ name: "live" });

  if (view.name === "runs") {
    return (
      <RunsListPage
        onBack={() => setView({ name: "live" })}
        onSelectExperiment={(id) => setView({ name: "experiment", id })}
      />
    );
  }

  if (view.name === "experiment") {
    return (
      <ExperimentDetailPage experimentId={view.id} onBack={() => setView({ name: "runs" })} />
    );
  }

  return (
    <div className="app">
      <TopBar event={event} state={state} connected={connected} />
      <PipelineStrip state={state} />
      <div className="layout">
        <ExperimentSidebar state={state} onViewAll={() => setView({ name: "runs" })} />
        <main className="mainGrid">
          <ScientistThoughtCard event={event} />
          <HypothesisCard event={event} />
          <ConfigDiffCard event={event} state={state} />
          <MetricsGrid event={event} />
          <ReflectionCard event={event} />
          <RecentEventsCard event={event} />
        </main>
        <div className="rightRail">
          <CurrentConfigPanel event={event} />
          <BestConfigPanel state={state} />
          <BudgetOverviewPanel state={state} />
        </div>
      </div>
    </div>
  );
}

export default App;
