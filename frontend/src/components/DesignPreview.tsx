import { CSSProperties, useState } from "react";
import { DesignSpec } from "../lib/types";

interface DesignPreviewProps {
  design: DesignSpec;
}

type DeviceMode = "desktop" | "tablet" | "mobile";

export function DesignPreview({ design }: DesignPreviewProps) {
  const heroPage = design.pages[0];
  const [deviceMode, setDeviceMode] = useState<DeviceMode>("desktop");

  return (
    <div className="design-preview">
      <div className="design-preview-header">
        <div>
          <div className="panel-kicker">Live Preview</div>
          <h3>{design.project_name}</h3>
          <p>Responsive concept preview across desktop, tablet, and mobile.</p>
        </div>
        <div className="preview-device-switcher">
          {(["desktop", "tablet", "mobile"] as DeviceMode[]).map((mode) => (
            <button
              key={mode}
              type="button"
              className={`device-toggle ${deviceMode === mode ? "is-active" : ""}`}
              onClick={() => setDeviceMode(mode)}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      <div
        className={`preview-stage ${deviceMode}`}
        style={
          {
            ["--preview-ink" as string]: design.visual_direction.colors[0],
            ["--preview-accent" as string]: design.visual_direction.colors[3],
            ["--preview-surface" as string]: design.visual_direction.colors[2],
          } as CSSProperties
        }
      >
        <div className={`preview-device-shell ${deviceMode}`}>
          <div className="preview-device-bar">
            <span />
            <span />
            <span />
          </div>

          <div className="preview-frame">
            <div className="preview-nav">
              <span className="preview-brand">{design.project_name}</span>
              <div className="preview-nav-links">
                {design.sitemap.map((page) => (
                  <span key={page}>{page}</span>
                ))}
              </div>
            </div>

            {heroPage ? (
              <section className="preview-hero">
                <div>
                  <p className="preview-eyebrow">{design.visual_direction.typography}</p>
                  <h2>{heroPage.hero_message}</h2>
                  <p>{design.content_strategy[0]}</p>
                  <div className="preview-actions-row">
                    <span className="preview-pill primary">Primary CTA</span>
                    <span className="preview-pill">Secondary CTA</span>
                  </div>
                </div>
                <div className="preview-hero-art">
                  <span>{design.visual_direction.mood}</span>
                </div>
              </section>
            ) : null}

            <div className="preview-sections">
              {heroPage?.sections.slice(0, 4).map((section) => (
                <article key={section.name} className="preview-card">
                  <div className="panel-kicker">{section.layout}</div>
                  <h4>{section.name}</h4>
                  <p>{section.purpose}</p>
                </article>
              ))}
            </div>

            <div className="preview-footer-strip">
              {design.components.slice(0, 4).map((component) => (
                <span key={`${component.page_slug}-${component.name}`}>{component.name}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
