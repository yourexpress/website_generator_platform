import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  approveDesign,
  approveRequirements,
  buildDownloadUrl,
  chatAssistant,
  generateBuild,
  getImageSuggestions,
  getProject,
  getProviders,
  uploadAssets,
} from "../lib/api";
import { DesignPreview } from "../components/DesignPreview";
import { SectionCard } from "../components/SectionCard";
import { AssistantMessage, ImageSuggestion, ProjectDetail, ProviderCatalogItem, RequirementInput } from "../lib/types";

const INTRO_MESSAGE: AssistantMessage = {
  id: "intro",
  role: "assistant",
  content:
    "Describe the website you want in natural language. After each message, I will refresh the requirement brief and generate a new design preview automatically.",
  created_at: new Date(0).toISOString(),
};

export function WorkspacePage() {
  const { projectId = "" } = useParams();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [providers, setProviders] = useState<ProviderCatalogItem[]>([]);
  const [suggestions, setSuggestions] = useState<ImageSuggestion[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<"openai" | "gemini" | "claude" | "deepseek">("openai");
  const [chatInput, setChatInput] = useState("");
  const [siteType, setSiteType] = useState<RequirementInput["site_type"]>("brochure");
  const [preferredPageCount, setPreferredPageCount] = useState(1);
  const [selectedAssetIds, setSelectedAssetIds] = useState<string[]>([]);
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
    if (!selectedAssetIds.length && project.assets.length) {
      setSelectedAssetIds(project.assets.map((asset) => asset.id));
    }
    const latestRequirement = project.requirement_versions[0];
    if (latestRequirement) {
      setSiteType(latestRequirement.source_input.site_type);
      setPreferredPageCount(latestRequirement.source_input.preferred_page_count);
      if (latestRequirement.source_input.uploaded_asset_ids.length) {
        setSelectedAssetIds(latestRequirement.source_input.uploaded_asset_ids);
      }
    }
  }, [project]);

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

  async function handleChatSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = chatInput.trim();
    if (!message) {
      return;
    }
    await withAction("assistant", async () => {
      await chatAssistant(projectId, selectedProvider, selectedProviderConfig?.default_models.requirements, {
        message,
        site_type: siteType,
        preferred_page_count: preferredPageCount,
        uploaded_asset_ids: selectedAssetIds,
      });
      setChatInput("");
      await refreshProject();
    });
  }

  async function handleApproveRequirement(id: string) {
    await withAction("approve-requirements", async () => {
      await approveRequirements(projectId, id);
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
  const conversation = project.assistant_messages.length ? project.assistant_messages : [INTRO_MESSAGE];

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
          title="AI Briefing"
          description="Talk to the assistant in natural language. Each new prompt refreshes the requirement brief and regenerates the design preview automatically."
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
            <div className="chat-toolbar">
              <label>
                Site type
                <select value={siteType} onChange={(event) => setSiteType(event.target.value as RequirementInput["site_type"])}>
                  <option value="brochure">Brochure</option>
                  <option value="landing">Landing</option>
                  <option value="campaign">Campaign</option>
                  <option value="portfolio">Portfolio</option>
                </select>
              </label>
              <label>
                Page count
                <input
                  type="number"
                  min={1}
                  max={5}
                  value={preferredPageCount}
                  onChange={(event) => setPreferredPageCount(Number(event.target.value) || 1)}
                />
              </label>
            </div>

            <div className="toggle-grid">
              {project.assets.map((asset) => {
                const selected = selectedAssetIds.includes(asset.id);
                return (
                  <button
                    key={asset.id}
                    className={`toggle-chip ${selected ? "is-active" : ""}`}
                    type="button"
                    onClick={() =>
                      setSelectedAssetIds((current) =>
                        selected ? current.filter((value) => value !== asset.id) : [...current, asset.id],
                      )
                    }
                  >
                    {asset.filename}
                  </button>
                );
              })}
            </div>

            <div className="chat-thread">
              {conversation.map((message) => (
                <article key={message.id} className={`chat-bubble ${message.role}`}>
                  <div className="panel-kicker">{message.role === "assistant" ? "AI" : "You"}</div>
                  <p>{message.content}</p>
                </article>
              ))}
            </div>

            <form className="chat-compose" onSubmit={handleChatSubmit}>
              <label className="full-span">
                Message
                <textarea
                  value={chatInput}
                  onChange={(event) => setChatInput(event.target.value)}
                  placeholder="Describe the business, audience, brand feel, structure, and any must-have sections."
                />
              </label>
              <button className="button primary" type="submit" disabled={!chatInput.trim() || busyAction === "assistant"}>
                {busyAction === "assistant" ? "Generating preview..." : "Send prompt"}
              </button>
            </form>
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
              <div className="panel inset-panel">
                <h3>Open questions</h3>
                <ul className="clean-list">
                  {latestRequirement.brief.open_questions.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : null}
        </SectionCard>

        <SectionCard
          step="Step 2"
          title="Design Preview"
          description="The preview refreshes automatically after each prompt. Review the current direction, then approve the design when it is ready for code generation."
        >
          {latestDesign ? (
            <div className="result-grid preview-grid">
              <div className="panel inset-panel">
                <div className="row-between">
                  <h3>Current design direction</h3>
                  <button className="button secondary" onClick={() => handleApproveDesign(latestDesign.id)}>
                    {latestDesign.approved ? "Approved" : "Approve design"}
                  </button>
                </div>
                <p>{latestDesign.design.visual_direction.mood}</p>
                <ul className="clean-list">
                  {latestDesign.design.pages.map((page) => (
                    <li key={page.slug}>
                      <strong>{page.title}</strong>: {page.sections.map((section) => section.name).join(", ")}
                    </li>
                  ))}
                </ul>
                <div className="row-between preview-actions">
                  <button className="button secondary" type="button" disabled={busyAction === "suggestions"} onClick={handleLoadSuggestions}>
                    {busyAction === "suggestions" ? "Loading..." : "Load image suggestions"}
                  </button>
                </div>
              </div>

              <div className="panel inset-panel">
                <DesignPreview design={latestDesign.design} />
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
          ) : (
            <p className="helper-text">Start the AI conversation above to generate the first design preview.</p>
          )}
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
