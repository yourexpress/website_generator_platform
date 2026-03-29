import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
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
import { AssistantMessage, ImageSuggestion, ProjectDetail, ProviderCatalogItem, RequirementInput } from "../lib/types";

const INTRO_MESSAGE: AssistantMessage = {
  id: "intro",
  role: "assistant",
  content:
    "Describe the site in plain language. I keep the current project session context, polish the brief, and try to satisfy every concrete requirement without dropping points.",
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
  const threadRef = useRef<HTMLDivElement | null>(null);

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

  useEffect(() => {
    if (!threadRef.current) {
      return;
    }
    threadRef.current.scrollTop = threadRef.current.scrollHeight;
  }, [project?.assistant_messages.length]);

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
    <main className="chat-app-shell">
      <header className="workspace-topbar panel">
        <div>
          <div className="panel-kicker">Session Workspace</div>
          <h1>{project.name}</h1>
          <p className="topbar-subtitle">{project.summary || "Interactive AI website generation workspace"}</p>
        </div>
        <div className="workspace-topbar-actions">
          <Link className="button ghost" to="/">
            All projects
          </Link>
          <label className="provider-select compact-control">
            Model provider
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

      {error ? <p className="error-text workspace-error">{error}</p> : null}

      <div className="workspace-chat-layout">
        <aside className="workspace-sidebar panel">
          <div className="sidebar-section">
            <div className="panel-kicker">Session Context</div>
            <p>The assistant keeps the full project conversation context and regenerates the latest brief and preview after each message.</p>
          </div>

          <div className="sidebar-section">
            <label className="compact-control">
              Site type
              <select value={siteType} onChange={(event) => setSiteType(event.target.value as RequirementInput["site_type"])}>
                <option value="brochure">Brochure</option>
                <option value="landing">Landing</option>
                <option value="campaign">Campaign</option>
                <option value="portfolio">Portfolio</option>
              </select>
            </label>
            <label className="compact-control">
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

          <div className="sidebar-section">
            <form className="stack-form" onSubmit={handleUpload}>
              <label className="compact-control">
                Upload reference images
                <input type="file" name="assets" accept="image/*" multiple />
              </label>
              <button className="button secondary" type="submit" disabled={busyAction === "upload"}>
                {busyAction === "upload" ? "Uploading..." : "Upload"}
              </button>
            </form>
            <div className="token-list">
              {project.assets.map((asset) => (
                <button
                  key={asset.id}
                  className={`toggle-chip ${selectedAssetIds.includes(asset.id) ? "is-active" : ""}`}
                  type="button"
                  onClick={() =>
                    setSelectedAssetIds((current) =>
                      current.includes(asset.id) ? current.filter((value) => value !== asset.id) : [...current, asset.id],
                    )
                  }
                >
                  {asset.filename}
                </button>
              ))}
            </div>
          </div>

          {latestRequirement ? (
            <div className="sidebar-section">
              <div className="row-between">
                <h3>Current brief</h3>
                <button className="button secondary small-button" onClick={() => handleApproveRequirement(latestRequirement.id)}>
                  {latestRequirement.approved ? "Approved" : "Approve"}
                </button>
              </div>
              <ul className="clean-list compact-list">
                {latestRequirement.brief.value_propositions.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {latestBuild ? (
            <div className="sidebar-section">
              <div className="panel-kicker">Latest Export</div>
              <p>{latestBuild.manifest.pages.length} page static bundle ready.</p>
              <a className="button secondary" href={buildDownloadUrl(project.id, latestBuild.id)}>
                Download ZIP
              </a>
            </div>
          ) : null}
        </aside>

        <section className="workspace-conversation panel">
          <div className="conversation-header">
            <div>
              <div className="panel-kicker">AI Design Chat</div>
              <h2>Describe. Refine. Iterate.</h2>
            </div>
            <p>The assistant polishes the brief but tries to preserve every concrete requirement from this session.</p>
          </div>

          <div className="chat-thread immersive-thread" ref={threadRef}>
            {conversation.map((message) => (
              <article key={message.id} className={`chat-bubble ${message.role}`}>
                <div className="chat-bubble-meta">{message.role === "assistant" ? "AI strategist" : "You"}</div>
                <p>{message.content}</p>
              </article>
            ))}
          </div>

          <form className="chat-compose docked-compose" onSubmit={handleChatSubmit}>
            <label className="full-span">
              Message
              <textarea
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                placeholder="Example: Make it feel premium but warm, keep testimonials and pricing, use the uploaded product shots, and optimize the design for desktop, iPad, and phone."
              />
            </label>
            <div className="compose-actions">
              <span className="compose-hint">Session-aware. Requirement-preserving. Auto-previewing.</span>
              <button className="button primary" type="submit" disabled={!chatInput.trim() || busyAction === "assistant"}>
                {busyAction === "assistant" ? "Refreshing preview..." : "Send"}
              </button>
            </div>
          </form>
        </section>

        <section className="workspace-preview-column">
          <div className="workspace-preview panel">
            <div className="preview-panel-header">
              <div>
                <div className="panel-kicker">Responsive Preview</div>
                <h2>Live design surface</h2>
              </div>
              {latestDesign ? (
                <button className="button secondary small-button" onClick={() => handleApproveDesign(latestDesign.id)}>
                  {latestDesign.approved ? "Approved" : "Approve design"}
                </button>
              ) : null}
            </div>

            {latestDesign ? <DesignPreview design={latestDesign.design} /> : <p className="helper-text">Send a message to generate the first preview.</p>}
          </div>

          <div className="workspace-insights-grid">
            <div className="panel insight-panel">
              <div className="row-between">
                <h3>Design coverage</h3>
                <button className="button secondary small-button" type="button" disabled={busyAction === "suggestions"} onClick={handleLoadSuggestions}>
                  {busyAction === "suggestions" ? "Loading..." : "Image ideas"}
                </button>
              </div>
              {latestDesign ? (
                <ul className="clean-list compact-list">
                  {latestDesign.design.pages.map((page) => (
                    <li key={page.slug}>
                      <strong>{page.title}</strong>: {page.sections.map((section) => section.name).join(", ")}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="helper-text">No design generated yet.</p>
              )}
            </div>

            <div className="panel insight-panel">
              <h3>Image suggestions</h3>
              {suggestions.length ? (
                <ul className="clean-list compact-list">
                  {suggestions.map((suggestion) => (
                    <li key={suggestion.url}>
                      <a href={suggestion.url} target="_blank" rel="noreferrer">
                        {suggestion.source_name}
                      </a>
                      <p>{suggestion.intended_use}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="helper-text">Load licensed image ideas when you want supporting visuals.</p>
              )}
            </div>

            <div className="panel insight-panel build-panel">
              <div className="row-between">
                <div>
                  <div className="panel-kicker">Export</div>
                  <h3>Generate frontend bundle</h3>
                </div>
              </div>
              <p>Build a responsive static export from the current approved design.</p>
              <button className="button primary" type="button" disabled={!latestDesign || busyAction === "build"} onClick={handleGenerateBuild}>
                {busyAction === "build" ? "Building..." : "Generate static site"}
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
