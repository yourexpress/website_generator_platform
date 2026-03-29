import { Link } from "react-router-dom";
import { ProjectSummary } from "../lib/types";

interface ProjectCardProps {
  project: ProjectSummary;
}

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <article className="panel project-card">
      <div className="panel-kicker">Project</div>
      <h3>{project.name}</h3>
      <p>{project.summary || "No summary yet. Open the workspace to refine requirements and generate the site."}</p>
      <div className="project-meta">
        <span>Updated {new Date(project.updated_at).toLocaleString()}</span>
        <span>{project.active_build_version_id ? "Has export" : "No export yet"}</span>
      </div>
      <Link className="button primary" to={`/projects/${project.id}`}>
        Open workspace
      </Link>
    </article>
  );
}
