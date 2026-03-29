import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { listProjects } from "./lib/api";
import { LoginPage } from "./pages/LoginPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { WorkspacePage } from "./pages/WorkspacePage";

export default function App() {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    async function bootstrap() {
      try {
        await listProjects();
        setAuthenticated(true);
      } catch {
        setAuthenticated(false);
      }
    }
    void bootstrap();
  }, []);

  if (authenticated === null) {
    return <main className="app-shell">Loading...</main>;
  }

  if (!authenticated) {
    return <LoginPage onAuthenticated={() => setAuthenticated(true)} />;
  }

  return (
    <Routes>
      <Route path="/" element={<ProjectsPage onLoggedOut={() => setAuthenticated(false)} />} />
      <Route path="/projects/:projectId" element={<WorkspacePage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
