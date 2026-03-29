import { DesignSpec } from "../lib/types";

interface DesignPreviewProps {
  design: DesignSpec;
}

export function DesignPreview({ design }: DesignPreviewProps) {
  const heroPage = design.pages[0];

  return (
    <div className="design-preview">
      <div className="design-preview-header">
        <div>
          <div className="panel-kicker">Live Preview</div>
          <h3>{design.project_name}</h3>
        </div>
        <div className="token-list">
          {design.visual_direction.colors.map((color) => (
            <span key={color} className="color-token">
              <span className="color-dot" style={{ background: color }} />
              {color}
            </span>
          ))}
        </div>
      </div>

      <div className="preview-frame" style={{ ["--preview-ink" as string]: design.visual_direction.colors[0], ["--preview-accent" as string]: design.visual_direction.colors[3] }}>
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
      </div>
    </div>
  );
}
