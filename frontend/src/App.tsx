import { PipelineStrip } from "./components/PipelineStrip";
import { TopBar } from "./components/TopBar";
import { useLiveSocket } from "./hooks/useLiveSocket";
import "./App.css";

function App() {
  const { event, state, connected } = useLiveSocket();

  return (
    <div className="app">
      <TopBar event={event} state={state} connected={connected} />
      <PipelineStrip state={state} />
    </div>
  );
}

export default App;
