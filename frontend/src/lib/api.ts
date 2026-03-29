import {
  ImageSuggestion,
  ProjectDetail,
  ProjectSummary,
  ProviderCatalogResponse,
  RequirementInput,
} from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed with ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function login(username: string, password: string) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function logout() {
  return request("/auth/logout", {
    method: "POST",
  });
}

export async function listProjects() {
  return request<ProjectSummary[]>("/api/projects");
}

export async function createProject(name: string, summary: string) {
  return request<ProjectSummary>("/api/projects", {
    method: "POST",
    body: JSON.stringify({ name, summary }),
  });
}

export async function getProject(projectId: string) {
  return request<ProjectDetail>(`/api/projects/${projectId}`);
}

export async function getProviders() {
  return request<ProviderCatalogResponse>("/api/providers");
}

export async function uploadAssets(projectId: string, files: File[]) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/uploads`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function refineRequirements(
  projectId: string,
  provider: string,
  model: string | undefined,
  input: RequirementInput,
) {
  return request(`/api/projects/${projectId}/requirements/refine`, {
    method: "POST",
    body: JSON.stringify({
      selection: { provider, model },
      input,
    }),
  });
}

export async function approveRequirements(projectId: string, requirementVersionId: string) {
  return request(`/api/projects/${projectId}/requirements/approve?requirement_version_id=${encodeURIComponent(requirementVersionId)}`, {
    method: "POST",
  });
}

export async function generateDesign(projectId: string, provider: string, model: string | undefined, requirementVersionId?: string) {
  return request(`/api/projects/${projectId}/design/generate`, {
    method: "POST",
    body: JSON.stringify({
      selection: { provider, model },
      requirement_version_id: requirementVersionId,
    }),
  });
}

export async function approveDesign(projectId: string, designVersionId: string) {
  return request(`/api/projects/${projectId}/design/approve?design_version_id=${encodeURIComponent(designVersionId)}`, {
    method: "POST",
  });
}

export async function generateBuild(projectId: string, provider: string, model: string | undefined, designVersionId?: string) {
  return request(`/api/projects/${projectId}/build/generate`, {
    method: "POST",
    body: JSON.stringify({
      selection: { provider, model },
      design_version_id: designVersionId,
    }),
  });
}

export async function getImageSuggestions(projectId: string) {
  return request<{ project_id: string; suggestions: ImageSuggestion[] }>(`/api/projects/${projectId}/image-suggestions`);
}

export function buildDownloadUrl(projectId: string, buildId: string) {
  return `${API_BASE_URL}/api/projects/${projectId}/builds/${buildId}/download`;
}
