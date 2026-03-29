import { ReactNode } from "react";

interface SectionCardProps {
  step: string;
  title: string;
  description: string;
  children: ReactNode;
}

export function SectionCard({ step, title, description, children }: SectionCardProps) {
  return (
    <section className="panel stage-panel">
      <div className="stage-header">
        <div>
          <div className="panel-kicker">{step}</div>
          <h2>{title}</h2>
        </div>
        <p>{description}</p>
      </div>
      {children}
    </section>
  );
}
