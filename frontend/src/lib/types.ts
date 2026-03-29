export type ProviderName = "openai" | "gemini" | "claude" | "deepseek";

export interface ProjectSummary {
  id: string;
  name: string;
  summary: string | null;
  created_at: string;
  updated_at: string;
  active_requirement_version_id: string | null;
  active_design_version_id: string | null;
  active_build_version_id: string | null;
}

export interface UploadedAsset {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  storage_path: string;
  created_at: string;
}

export interface PagePlan {
  slug: string;
  title: string;
  goal: string;
  sections: string[];
}

export interface RequirementInput {
  prompt: string;
  business_name?: string | null;
  business_type?: string | null;
  site_type: "landing" | "brochure" | "campaign" | "portfolio";
  target_audience: string[];
  brand_direction?: string | null;
  required_sections: string[];
  cta_goals: string[];
  reference_notes?: string | null;
  preferred_page_count: number;
  uploaded_asset_ids: string[];
}

export interface RequirementBrief {
  project_name: string;
  project_type: string;
  summary: string;
  business_context: string;
  target_audience: string[];
  value_propositions: string[];
  recommended_tone: string[];
  required_pages: PagePlan[];
  content_requirements: string[];
  asset_requirements: string[];
  assumptions: string[];
  open_questions: string[];
}

export interface RequirementVersion {
  id: string;
  version_number: number;
  status: string;
  approved: boolean;
  provider: ProviderName;
  model: string;
  created_at: string;
  approved_at: string | null;
  source_input: RequirementInput;
  brief: RequirementBrief;
}

export interface AssetReference {
  kind: "uploaded" | "placeholder" | "internet-suggestion";
  label: string;
  source_type: "project-upload" | "placeholder" | "recommended-source";
  asset_id?: string | null;
  page_slug?: string | null;
  section?: string | null;
  alt_text?: string | null;
  notes?: string | null;
}

export interface DesignPageSection {
  name: string;
  purpose: string;
  layout: string;
  content_items: string[];
  cta?: string | null;
}

export interface DesignPage {
  slug: string;
  title: string;
  hero_message: string;
  sections: DesignPageSection[];
}

export interface DesignSpec {
  project_name: string;
  sitemap: string[];
  pages: DesignPage[];
  visual_direction: {
    mood: string;
    colors: string[];
    typography: string;
    layout_keywords: string[];
  };
  components: {
    name: string;
    purpose: string;
    page_slug: string;
    notes: string;
  }[];
  image_plan: AssetReference[];
  content_strategy: string[];
  implementation_notes: string[];
}

export interface DesignVersion {
  id: string;
  requirement_version_id: string;
  version_number: number;
  status: string;
  approved: boolean;
  provider: ProviderName;
  model: string;
  created_at: string;
  approved_at: string | null;
  design: DesignSpec;
}

export interface BuildManifest {
  project_name: string;
  build_id: string;
  site_title: string;
  generated_at: string;
  provider: ProviderName;
  model: string;
  pages: string[];
  files: string[];
  assets: AssetReference[];
  notes: string[];
}

export interface BuildVersion {
  id: string;
  design_version_id: string;
  version_number: number;
  status: string;
  provider: ProviderName;
  model: string;
  created_at: string;
  completed_at: string | null;
  manifest: BuildManifest;
  export_root_path: string;
  export_zip_path: string;
}

export interface GenerationRun {
  id: string;
  stage: "requirements" | "design" | "build";
  provider: ProviderName;
  model: string;
  prompt_version: string;
  status: string;
  latency_ms: number;
  token_usage: Record<string, number>;
  error_message: string | null;
  output_ref_id: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface ProjectDetail extends ProjectSummary {
  assets: UploadedAsset[];
  requirement_versions: RequirementVersion[];
  design_versions: DesignVersion[];
  build_versions: BuildVersion[];
  generation_runs: GenerationRun[];
}

export interface ProviderCatalogItem {
  name: ProviderName;
  configured: boolean;
  offline_fallback: boolean;
  default_models: Record<"requirements" | "design" | "build", string>;
}

export interface ProviderCatalogResponse {
  providers: ProviderCatalogItem[];
}

export interface ImageSuggestion {
  source_name: string;
  url: string;
  licensing_note: string;
  intended_use: string;
  query: string;
}
