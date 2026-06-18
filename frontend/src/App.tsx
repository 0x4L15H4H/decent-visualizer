import { Routes, Route, Link, Navigate, useLocation } from "react-router";
import { AuthProvider, useAuth } from "./contexts/AuthContext.tsx";
import Home from "./pages/Home.tsx";
import Beans from "./pages/Beans.tsx";
import Settings from "./pages/Settings.tsx";
import Login from "./pages/Login.tsx";

function NavTab({ to, label }: { to: string; label: string }) {
  const { pathname } = useLocation();
  const active = pathname === to;
  return (
    <Link
      to={to}
      className={`text-sm ${active ? "text-text-primary" : "text-text-muted hover:text-text-primary"}`}
    >
      {label}
    </Link>
  );
}

function AppRoutes() {
  const { user, loading, logout } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-border-default border-t-accent" />
      </div>
    );
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div className="min-h-screen">
      <nav className="fixed top-0 z-10 w-full border-b border-border-default bg-bg-surface">
        <div className="mx-auto flex h-12 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-6">
            <Link to="/" className="font-vga text-sm text-text-primary">
              DECENT VISUALIZER
            </Link>
            <NavTab to="/" label="Shots" />
            <NavTab to="/beans" label="Beans" />
            <NavTab to="/settings" label="Settings" />
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-text-secondary">{user.display_name ?? user.email}</span>
            <button
              type="button"
              onClick={logout}
              className="text-sm text-text-muted hover:text-text-primary"
            >
              Log out
            </button>
          </div>
        </div>
      </nav>
      <main className="mx-auto max-w-6xl px-6 pt-18 pb-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/beans" element={<Beans />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;
