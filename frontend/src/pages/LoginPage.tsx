import { FormEvent, useState } from "react";
import { login } from "../lib/api";

interface LoginPageProps {
  onAuthenticated: () => void;
}

export function LoginPage({ onAuthenticated }: LoginPageProps) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("change-me");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(username, password);
      onAuthenticated();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to log in");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-shell">
      <div className="orb orb-left" />
      <div className="orb orb-right" />
      <section className="panel login-panel">
        <div className="panel-kicker">Admin Access</div>
        <h1>Website Generator Platform</h1>
        <p className="lede">
          Turn rough prompts and uploaded images into refined requirements, a UX-grade design spec, and a downloadable
          static site bundle.
        </p>
        <form className="stack-form" onSubmit={handleSubmit}>
          <label>
            Username
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
            />
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <button className="button primary" type="submit" disabled={busy}>
            {busy ? "Signing in..." : "Enter workspace"}
          </button>
        </form>
      </section>
    </main>
  );
}
