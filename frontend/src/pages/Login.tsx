import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useAuth } from "../contexts/AuthContext";
import { api } from "../api";

const inputClass =
  "rounded-md border border-border-default bg-bg-raised px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-accent";

function LoginForm({
  mode,
  onSubmit,
  submitting,
  error,
}: {
  mode: "login" | "signup";
  onSubmit: (email: string, password: string, displayName?: string) => void;
  submitting: boolean;
  error: string | null;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");

  const handleSubmit = useCallback(
    (e: FormEvent) => {
      e.preventDefault();
      onSubmit(email, password, displayName || undefined);
    },
    [email, password, displayName, onSubmit],
  );

  return (
    <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-3">
      {mode === "signup" && (
        <input
          type="text"
          placeholder="Display name (optional)"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          className={inputClass}
        />
      )}
      <input
        type="email"
        placeholder="Email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className={inputClass}
      />
      <input
        type="password"
        placeholder="Password"
        required
        minLength={mode === "signup" ? 8 : undefined}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        className={inputClass}
      />

      {error && <p className="text-sm text-destructive">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="rounded-md border border-border-default bg-bg-raised px-3 py-1.5 text-sm font-medium text-text-primary hover:bg-white/10 disabled:opacity-50"
      >
        {submitting
          ? "..."
          : mode === "login"
            ? "Log in"
            : "Create account"}
      </button>
    </form>
  );
}

function Login() {
  const { login, signup } = useAuth();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [signupsEnabled, setSignupsEnabled] = useState<boolean | null>(null);

  useEffect(() => {
    api
      .get("/api/auth/signup-enabled")
      .then((res) => res.json())
      .then((data) => setSignupsEnabled(data.enabled))
      .catch(() => setSignupsEnabled(false));
  }, []);

  const handleSubmit = useCallback(
    async (email: string, password: string, displayName?: string) => {
      setError(null);
      setSubmitting(true);
      try {
        if (mode === "login") {
          await login(email, password);
        } else {
          await signup(email, password, displayName);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong");
      } finally {
        setSubmitting(false);
      }
    },
    [mode, login, signup],
  );

  const modePill = signupsEnabled && mode === "login"
    ? (
        <button
          type="button"
          onClick={() => { setMode("signup"); setError(null); }}
          className="rounded-full border border-border-default px-3 py-1 text-xs text-text-secondary hover:bg-bg-raised hover:text-text-primary"
        >
          Create new account
        </button>
      )
    : mode === "signup"
      ? (
          <button
            type="button"
            onClick={() => { setMode("login"); setError(null); }}
            className="rounded-full border border-border-default px-3 py-1 text-xs text-text-secondary hover:bg-bg-raised hover:text-text-primary"
          >
            Log in to existing account
          </button>
        )
      : null;

  return (
    <div className="relative flex min-h-screen flex-col">
      <img
        src="/login-bg.svg"
        alt=""
        className="pointer-events-none absolute inset-0 h-full w-full object-cover"
      />
      <div className="relative flex h-12 items-center justify-end px-6">
        {modePill}
      </div>
      <div className="relative flex flex-1 items-center justify-center">
        <div className="w-full max-w-sm">
          <h1 className="mb-6 text-center font-vga text-2xl tracking-wide text-text-primary">
            DECENT VISUALIZER
          </h1>
          <div className="rounded-lg border border-border-default bg-bg-surface p-6">
            <h2 className="text-lg font-medium">
              {mode === "login" ? "Log in" : "Create account"}
            </h2>

          <LoginForm
            mode={mode}
            onSubmit={handleSubmit}
            submitting={submitting}
            error={error}
          />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
