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
  PERSISTED = "persisted",
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

export interface ValueProp {
  headline: string;
  subheadline: string;
  proof_points: string[];
  differentiators: string[];
}

export interface Channel {
  name: string;
  priority: number;
  rationale: string;
  kpis: string[];
  estimated_cac?: string | null;
}

export interface GrowthLoop {
  name: string;
  type: string;
  description: string;
  input_metric: string;
  output_metric: string;
}

export interface Milestone {
  week: number;
  goal: string;
  kpis: string[];
  owner: string;
}

export interface CompetitiveBattlecard {
  competitor: string;
  our_strengths_vs_them: string[];
  their_strengths_vs_us: string[];
  winning_moves: string[];
  losing_scenarios: string[];
  talk_track: string;
}

export interface GTMStrategy {
  motion: GTMMotion;
  icp: ICPProfile;
  value_proposition?: ValueProp;
  channels?: Channel[];
  battlecards?: CompetitiveBattlecard[];
  growth_loops?: GrowthLoop[];
  ninety_day_plan?: Milestone[];
  positioning_statement: string;
  generated_at: string;
}

// Lightweight view of the research report (only what the UI surfaces).
export interface ResearchHighlights {
  market_size?: { tam?: string; sam?: string; som?: string } & Record<string, unknown>;
  competitors?: { name: string; positioning?: string }[];
  signals?: { description?: string; source?: string }[];
  sources?: string[];
}

// The full deliverable bundle emitted on the agent_complete frame.
export interface StrategyBundle {
  gtm_strategy: GTMStrategy | null;
  content_assets: ContentAsset[];
  research_report: ResearchHighlights | null;
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

export interface AcceptInviteRequest {
  invite_token: string;
  password: string;
  email: string;
}

export type TeamRole = "owner" | "admin" | "member";

export interface CreateInviteRequest {
  role: TeamRole;
}

export interface CreateInviteResponse {
  invite_token: string;
  invite_url: string;
}

export interface TeamMember {
  id: string;
  email: string;
  role: TeamRole;
  is_active: boolean;
  created_at: string;
}

// Roles assignable via the promote/demote endpoint ("owner" is not settable).
export type AssignableRole = "member" | "admin";

// Billing plans a workspace can be on (issue #31). Mirrors PLAN_SEAT_LIMITS in
// backend/app/api/team.py. Real billing is not wired up — switching is free.
export type WorkspacePlan = "free" | "pro" | "enterprise";

export interface TeamSettings {
  company_id: string;
  name: string;
  plan: WorkspacePlan;
  seat_count: number;
  seat_limit: number;
}

export interface KnowledgeDocument {
  id: string;
  filename: string;
  doc_type: string;
  status: "pending" | "indexed" | "failed";
  chunk_count?: number;
  created_at: string;
}
