import { Routes, Route, Link } from "react-router";
import Home from "./pages/Home.tsx";

function App() {
  return (
    <div className="min-h-screen">
      <nav className="fixed top-0 z-10 w-full border-b border-border-default bg-bg-surface">
        <div className="mx-auto flex h-12 max-w-6xl items-center gap-6 px-6">
          <Link to="/" className="text-sm font-semibold text-text-primary">
            Decent Visualizer
          </Link>
        </div>
      </nav>
      <main className="mx-auto max-w-6xl px-6 pt-18 pb-8">
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
