import { BestConfigPanel } from "./components/BestConfigPanel";
import { BudgetOverviewPanel } from "./components/BudgetOverviewPanel";
import { ConfigDiffCard } from "./components/ConfigDiffCard";
import { CurrentConfigPanel } from "./components/CurrentConfigPanel";
import { ExperimentSidebar } from "./components/ExperimentSidebar";
import { HypothesisCard } from "./components/HypothesisCard";
import { MetricsGrid } from "./components/MetricsGrid";
import { PipelineStrip } from "./components/PipelineStrip";
import { RecentEventsCard } from "./components/RecentEventsCard";
import { ReflectionCard } from "./components/ReflectionCard";
import { ScientistThoughtCard } from "./components/ScientistThoughtCard";
import { TopBar } from "./components/TopBar";
import { useLiveSocket } from "./hooks/useLiveSocket";
import "./App.css";

function App() {
  const { event, state, connected } = useLiveSocket();

  return (
    <div className="app">
      <TopBar event={event} state={state} connected={connected} />
      <PipelineStrip state={state} />
      <div className="layout">
        <ExperimentSidebar state={state} />
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
