import { FormEvent, useEffect, useState } from "react";
import { createProject, listProjects, logout } from "../lib/api";
import { ProjectSummary } from "../lib/types";
import { ProjectCard } from "../components/ProjectCard";

interface ProjectsPageProps {
  onLoggedOut: () => void;
}

export function ProjectsPage({ onLoggedOut }: ProjectsPageProps) {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [name, setName] = useState("");
  const [summary, setSummary] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function loadProjects() {
    setError("");
    try {
      setProjects(await listProjects());
    } catch (loadError) {
      const message = loadError instanceof Error ? loadError.message : "Unable to load projects";
      if (message.includes("401")) {
        onLoggedOut();
        return;
      }
      setError(message);
    }
  }

  useEffect(() => {
    void loadProjects();
  }, []);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await createProject(name, summary);
      setName("");
      setSummary("");
      await loadProjects();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Unable to create project");
    } finally {
      setBusy(false);
    }
  }

  async function handleLogout() {
    await logout();
    onLoggedOut();
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <div className="panel-kicker">Workspace</div>
          <h1>Projects</h1>
        </div>
        <button className="button ghost" onClick={handleLogout}>
          Log out
        </button>
      </header>

      <section className="dashboard-grid">
        <form className="panel stack-form create-project-panel" onSubmit={handleCreate}>
          <div className="panel-kicker">New Project</div>
          <h2>Start a website generation workflow</h2>
          <label>
            Project name
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Northwind Studio" />
          </label>
          <label>
            Summary
            <textarea
              value={summary}
              onChange={(event) => setSummary(event.target.value)}
              placeholder="Creative agency brochure site with strong proof blocks and bold editorial styling."
            />
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <button className="button primary" disabled={busy || name.trim().length < 2} type="submit">
            {busy ? "Creating..." : "Create project"}
          </button>
        </form>

        <section className="projects-grid">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </section>
      </section>
    </main>
  );
}
