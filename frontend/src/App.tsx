import { Routes, Route, Link } from "react-router";
import Home from "./pages/Home.tsx";
import About from "./pages/About.tsx";

function App() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <nav className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-4xl items-center gap-6">
          <Link to="/" className="text-lg font-semibold">
            Decent Visualizer
          </Link>
          <Link to="/about" className="text-sm text-gray-600 hover:text-gray-900">
            About
          </Link>
        </div>
      </nav>
      <main className="mx-auto max-w-4xl px-6 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
