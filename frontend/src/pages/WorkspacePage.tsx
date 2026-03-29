import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  approveDesign,
  approveRequirements,
  buildDownloadUrl,
  generateBuild,
  generateDesign,
  getImageSuggestions,
  getProject,
  getProviders,
  uploadAssets,
  refineRequirements,
} from "../lib/api";
import { ImageSuggestion, ProjectDetail, ProviderCatalogItem, RequirementInput } from "../lib/types";
import { SectionCard } from "../components/SectionCard";

const DEFAULT_REQUIREMENT_INPUT: RequirementInput = {
  prompt: "",
  business_name: "",
  business_type: "",
  site_type: "brochure",
  target_audience: [],
  brand_direction: "",
  required_sections: [],
  cta_goals: [],
  reference_notes: "",
  preferred_page_count: 1,
  uploaded_asset_ids: [],
};

export function WorkspacePage() {
  const { projectId = "" } = useParams();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [providers, setProviders] = useState<ProviderCatalogItem[]>([]);
  const [suggestions, setSuggestions] = useState<ImageSuggestion[]>([]);
  const [requirementInput, setRequirementInput] = useState<RequirementInput>(DEFAULT_REQUIREMENT_INPUT);
  const [selectedProvider, setSelectedProvider] = useState<"openai" | "gemini" | "claude" | "deepseek">("openai");
  const [busyAction, setBusyAction] = useState("");
  const [error, setError] = useState("");

  const selectedProviderConfig = useMemo(
    () => providers.find((provider) => provider.name === selectedProvider),
    [providers, selectedProvider],
  );

  async function refreshProject() {
    setProject(await getProject(projectId));
  }

  useEffect(() => {
    async function load() {
      try {
        const [projectResult, providerResult] = await Promise.all([getProject(projectId), getProviders()]);
        setProject(projectResult);
        setProviders(providerResult.providers);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Unable to load workspace");
      }
    }
    void load();
  }, [projectId]);

  useEffect(() => {
    if (!project) {
      return;
    }
    setRequirementInput((current) => ({
      ...current,
      business_name: current.business_name || project.name,
    }));
  }, [project?.name]);

  async function withAction<T>(label: string, task: () => Promise<T>) {
    setBusyAction(label);
    setError("");
    try {
      return await task();
    } catch (taskError) {
      setError(taskError instanceof Error ? taskError.message : "Operation failed");
      throw taskError;
    } finally {
      setBusyAction("");
    }
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fileInput = event.currentTarget.elements.namedItem("assets") as HTMLInputElement | null;
    const files = fileInput?.files ? Array.from(fileInput.files) : [];
    if (!files.length) {
      return;
    }
    await withAction("upload", async () => {
      await uploadAssets(projectId, files);
      await refreshProject();
    });
  }

  async function handleRefine() {
    await withAction("requirements", async () => {
      await refineRequirements(projectId, selectedProvider, selectedProviderConfig?.default_models.requirements, requirementInput);
      await refreshProject();
    });
  }

  async function handleApproveRequirement(id: string) {
    await withAction("approve-requirements", async () => {
      await approveRequirements(projectId, id);
      await refreshProject();
    });
  }

  async function handleGenerateDesign() {
    const requirementVersionId = project?.requirement_versions[0]?.id;
    if (!requirementVersionId) {
      return;
    }
    await withAction("design", async () => {
      await generateDesign(projectId, selectedProvider, selectedProviderConfig?.default_models.design, requirementVersionId);
      await refreshProject();
    });
  }

  async function handleApproveDesign(id: string) {
    await withAction("approve-design", async () => {
      await approveDesign(projectId, id);
      await refreshProject();
    });
  }

  async function handleGenerateBuild() {
    const designVersionId = project?.design_versions[0]?.id;
    if (!designVersionId) {
      return;
    }
    await withAction("build", async () => {
      await generateBuild(projectId, selectedProvider, selectedProviderConfig?.default_models.build, designVersionId);
      await refreshProject();
    });
  }

  async function handleLoadSuggestions() {
    await withAction("suggestions", async () => {
      const result = await getImageSuggestions(projectId);
      setSuggestions(result.suggestions);
    });
  }

  if (!project) {
    return (
      <main className="app-shell">
        <p>Loading workspace...</p>
        {error ? <p className="error-text">{error}</p> : null}
      </main>
    );
  }

  const latestRequirement = project.requirement_versions[0];
  const latestDesign = project.design_versions[0];
  const latestBuild = project.build_versions[0];

  return (
    <main className="app-shell workspace-shell">
      <header className="topbar">
        <div>
          <div className="panel-kicker">Project Workspace</div>
          <h1>{project.name}</h1>
          <p className="topbar-subtitle">{project.summary || "No summary yet"}</p>
        </div>
        <div className="toolbar">
          <Link className="button ghost" to="/">
            Back to projects
          </Link>
          <label className="provider-select">
            Active provider
            <select value={selectedProvider} onChange={(event) => setSelectedProvider(event.target.value as typeof selectedProvider)}>
              {providers.map((provider) => (
                <option key={provider.name} value={provider.name}>
                  {provider.name} {provider.configured ? "" : "(offline fallback)"}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="workspace-grid">
        <SectionCard
          step="Step 1"
          title="Input Studio"
          description="Collect project context, uploads, and raw requirements, then polish them into a structured brief."
        >
          <div className="panel inset-panel">
            <form className="stack-form" onSubmit={handleUpload}>
              <label>
                Upload images
                <input type="file" name="assets" accept="image/*" multiple />
              </label>
              <button className="button secondary" type="submit" disabled={busyAction === "upload"}>
                {busyAction === "upload" ? "Uploading..." : "Upload assets"}
              </button>
            </form>
            <div className="token-list">
              {project.assets.map((asset) => (
                <span key={asset.id} className="token">
                  {asset.filename}
                </span>
              ))}
            </div>
          </div>

          <div className="panel inset-panel">
            <div className="form-grid">
              <label>
                Prompt
                <textarea
                  value={requirementInput.prompt}
                  onChange={(event) => setRequirementInput({ ...requirementInput, prompt: event.target.value })}
                  placeholder="Build a polished brochure website for a design studio with a bold editorial hero and clear proof blocks."
                />
              </label>
              <label>
                Business name
                <input
                  value={requirementInput.business_name || ""}
                  onChange={(event) => setRequirementInput({ ...requirementInput, business_name: event.target.value })}
                />
              </label>
              <label>
                Business type
                <input
                  value={requirementInput.business_type || ""}
                  onChange={(event) => setRequirementInput({ ...requirementInput, business_type: event.target.value })}
                />
              </label>
              <label>
                Brand direction
                <input
                  value={requirementInput.brand_direction || ""}
                  onChange={(event) => setRequirementInput({ ...requirementInput, brand_direction: event.target.value })}
                  placeholder="Editorial, bright, premium"
                />
              </label>
              <label>
                Site type
                <select
                  value={requirementInput.site_type}
                  onChange={(event) => setRequirementInput({ ...requirementInput, site_type: event.target.value as RequirementInput["site_type"] })}
                >
                  <option value="brochure">Brochure</option>
                  <option value="landing">Landing</option>
                  <option value="campaign">Campaign</option>
                  <option value="portfolio">Portfolio</option>
                </select>
              </label>
              <label>
                Preferred page count
                <input
                  type="number"
                  min={1}
                  max={5}
                  value={requirementInput.preferred_page_count}
                  onChange={(event) =>
                    setRequirementInput({
                      ...requirementInput,
                      preferred_page_count: Number(event.target.value) || 1,
                    })
                  }
                />
              </label>
              <label>
                Target audience
                <input
                  value={requirementInput.target_audience.join(", ")}
                  onChange={(event) =>
                    setRequirementInput({
                      ...requirementInput,
                      target_audience: event.target.value.split(",").map((value) => value.trim()).filter(Boolean),
                    })
                  }
                  placeholder="startup founders, marketing teams"
                />
              </label>
              <label>
                Required sections
                <input
                  value={requirementInput.required_sections.join(", ")}
                  onChange={(event) =>
                    setRequirementInput({
                      ...requirementInput,
                      required_sections: event.target.value.split(",").map((value) => value.trim()).filter(Boolean),
                    })
                  }
                  placeholder="hero, services, case studies, contact"
                />
              </label>
              <label>
                CTA goals
                <input
                  value={requirementInput.cta_goals.join(", ")}
                  onChange={(event) =>
                    setRequirementInput({
                      ...requirementInput,
                      cta_goals: event.target.value.split(",").map((value) => value.trim()).filter(Boolean),
                    })
                  }
                  placeholder="Book a discovery call"
                />
              </label>
              <label className="full-span">
                Reference notes
                <textarea
                  value={requirementInput.reference_notes || ""}
                  onChange={(event) => setRequirementInput({ ...requirementInput, reference_notes: event.target.value })}
                />
              </label>
            </div>

            <div className="toggle-grid">
              {project.assets.map((asset) => {
                const selected = requirementInput.uploaded_asset_ids.includes(asset.id);
                return (
                  <button
                    key={asset.id}
                    className={`toggle-chip ${selected ? "is-active" : ""}`}
                    type="button"
                    onClick={() =>
                      setRequirementInput((current) => ({
                        ...current,
                        uploaded_asset_ids: selected
                          ? current.uploaded_asset_ids.filter((value) => value !== asset.id)
                          : [...current.uploaded_asset_ids, asset.id],
                      }))
                    }
                  >
                    {asset.filename}
                  </button>
                );
              })}
            </div>

            <button
              className="button primary"
              type="button"
              disabled={!requirementInput.prompt.trim() || busyAction === "requirements"}
              onClick={handleRefine}
            >
              {busyAction === "requirements" ? "Polishing..." : "Polish requirements"}
            </button>
          </div>

          {latestRequirement ? (
            <div className="result-grid">
              <div className="panel inset-panel">
                <div className="row-between">
                  <h3>Latest requirement brief</h3>
                  <button className="button secondary" onClick={() => handleApproveRequirement(latestRequirement.id)}>
                    {latestRequirement.approved ? "Approved" : "Approve brief"}
                  </button>
                </div>
                <p>{latestRequirement.brief.business_context}</p>
                <ul className="clean-list">
                  {latestRequirement.brief.value_propositions.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
                <p className="meta-line">
                  Version {latestRequirement.version_number} via {latestRequirement.provider} / {latestRequirement.model}
                </p>
              </div>
            </div>
          ) : null}
        </SectionCard>

        <SectionCard
          step="Step 2"
          title="Design Studio"
          description="Transform the approved requirement brief into a structured design spec with sitemap, layout guidance, and component inventory."
        >
          <div className="row-between">
            <button className="button primary" type="button" disabled={!latestRequirement || busyAction === "design"} onClick={handleGenerateDesign}>
              {busyAction === "design" ? "Generating design..." : "Generate design"}
            </button>
            <button className="button secondary" type="button" disabled={!latestRequirement || busyAction === "suggestions"} onClick={handleLoadSuggestions}>
              {busyAction === "suggestions" ? "Loading..." : "Load image suggestions"}
            </button>
          </div>

          {latestDesign ? (
            <div className="result-grid">
              <div className="panel inset-panel">
                <div className="row-between">
                  <h3>Latest design spec</h3>
                  <button className="button secondary" onClick={() => handleApproveDesign(latestDesign.id)}>
                    {latestDesign.approved ? "Approved" : "Approve design"}
                  </button>
                </div>
                <p>{latestDesign.design.visual_direction.mood}</p>
                <div className="token-list">
                  {latestDesign.design.visual_direction.colors.map((color) => (
                    <span key={color} className="color-token">
                      <span className="color-dot" style={{ background: color }} />
                      {color}
                    </span>
                  ))}
                </div>
                <ul className="clean-list">
                  {latestDesign.design.pages.map((page) => (
                    <li key={page.slug}>
                      <strong>{page.title}</strong>: {page.sections.map((section) => section.name).join(", ")}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="panel inset-panel">
                <h3>Licensed image recommendations</h3>
                {suggestions.length ? (
                  <ul className="clean-list">
                    {suggestions.map((suggestion) => (
                      <li key={suggestion.url}>
                        <a href={suggestion.url} target="_blank" rel="noreferrer">
                          {suggestion.source_name}
                        </a>
                        <p>{suggestion.intended_use}</p>
                        <small>{suggestion.licensing_note}</small>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No suggestions loaded yet.</p>
                )}
              </div>
            </div>
          ) : null}
        </SectionCard>

        <SectionCard
          step="Step 3"
          title="Build Studio"
          description="Generate the static export bundle, keep version history, and download a ZIP when the build is complete."
        >
          <button className="button primary" type="button" disabled={!latestDesign || busyAction === "build"} onClick={handleGenerateBuild}>
            {busyAction === "build" ? "Generating build..." : "Generate static site"}
          </button>

          {latestBuild ? (
            <div className="result-grid">
              <div className="panel inset-panel">
                <h3>Latest build artifact</h3>
                <p>
                  Version {latestBuild.version_number} via {latestBuild.provider} / {latestBuild.model}
                </p>
                <ul className="clean-list">
                  {latestBuild.manifest.files.map((file) => (
                    <li key={file}>{file}</li>
                  ))}
                </ul>
                <a className="button secondary" href={buildDownloadUrl(project.id, latestBuild.id)}>
                  Download ZIP export
                </a>
              </div>
            </div>
          ) : (
            <p className="helper-text">No build generated yet.</p>
          )}
        </SectionCard>
      </div>
    </main>
  );
}
