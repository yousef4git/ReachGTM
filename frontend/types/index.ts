// Mirrors shared/schemas.py — update both files when schemas change

export enum ContentType {
  COLD_EMAIL = "cold_email",
  LINKEDIN_POST = "linkedin_post",
  BLOG_OUTLINE = "blog_outline",
  AD_COPY = "ad_copy",
}

export enum GTMMotion {
  PLG = "product_led_growth",
  SLG = "sales_led_growth",
  CLG = "community_led_growth",
  MLG = "marketing_led_growth",
}

export enum ValidationStatus {
  PENDING = "pending",
  APPROVED = "approved",
  REJECTED = "rejected",
  REVISED = "revised",
}

export enum AgentEventType {
  AGENT_START = "agent_start",
  AGENT_PROGRESS = "agent_progress",
  AGENT_OUTPUT = "agent_output",
  AGENT_COMPLETE = "agent_complete",
  ERROR = "error",
  DONE = "done",
}

export interface AgentEvent {
  event: AgentEventType;
  agent?: string;
  message?: string;
  data?: unknown;
  timestamp: string;
}

export interface ICPProfile {
  title: string;
  industry: string;
  company_size: string;
  budget_range: string;
  pain_points: string[];
  goals: string[];
  buying_committee: string[];
  disqualifiers: string[];
}

export interface ContentAsset {
  id: string;
  type: ContentType;
  title: string;
  body: string;
  target_icp: string;
  validation_status: ValidationStatus;
  brand_alignment_score?: number;
  revision_notes?: string;
  created_at: string;
}

export interface GTMStrategy {
  motion: GTMMotion;
  icp: ICPProfile;
  positioning_statement: string;
  generated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterRequest {
  email: string;
  password: string;
  company_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}
