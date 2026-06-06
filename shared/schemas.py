from __future__ import annotations
from enum import Enum
from typing import Annotated, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────

class ContentType(str, Enum):
    COLD_EMAIL = "cold_email"
    LINKEDIN_POST = "linkedin_post"
    BLOG_OUTLINE = "blog_outline"
    AD_COPY = "ad_copy"

class GTMMotion(str, Enum):
    PLG = "product_led_growth"
    SLG = "sales_led_growth"
    CLG = "community_led_growth"
    MLG = "marketing_led_growth"

class ValidationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISED = "revised"

class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


# ── Domain Models ──────────────────────────────────────────────────────────

class CompanyProfile(BaseModel):
    name: str
    website: Optional[str] = None
    industry: str
    stage: str  # seed, series_a, series_b, growth
    description: str
    founded_year: Optional[int] = None

class MarketSize(BaseModel):
    tam: str  # e.g. "$4.2B"
    sam: str
    som: str
    source: str
    year: int

class Competitor(BaseModel):
    name: str
    website: Optional[str] = None
    positioning: str
    strengths: list[str]
    weaknesses: list[str]
    pricing_model: Optional[str] = None

class Segment(BaseModel):
    name: str
    description: str
    size_estimate: str
    pain_points: list[str]
    buying_triggers: list[str]

class Signal(BaseModel):
    type: str  # hiring, funding, product_launch, leadership_change
    description: str
    relevance: str

class ICPProfile(BaseModel):
    title: str
    industry: str
    company_size: str  # "50-200 employees"
    budget_range: str
    pain_points: list[str]
    goals: list[str]
    buying_committee: list[str]  # roles involved in purchase decision
    disqualifiers: list[str]

class ResearchReport(BaseModel):
    company_profile: CompanyProfile
    market_size: MarketSize
    competitors: list[Competitor]
    segments: list[Segment]
    icp: ICPProfile
    signals: list[Signal]
    sources: list[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class ValueProp(BaseModel):
    headline: str
    subheadline: str
    proof_points: list[str]
    differentiators: list[str]

class Channel(BaseModel):
    name: str  # cold_email, linkedin, content, paid, partnerships
    priority: int  # 1 = highest
    rationale: str
    kpis: list[str]
    estimated_cac: Optional[str] = None

class CompetitiveBattlecard(BaseModel):
    competitor: str
    our_strengths_vs_them: list[str]
    their_strengths_vs_us: list[str]
    winning_moves: list[str]
    losing_scenarios: list[str]
    talk_track: str

class GrowthLoop(BaseModel):
    name: str
    type: str  # viral, paid, content, sales
    description: str
    input_metric: str
    output_metric: str

class Milestone(BaseModel):
    week: int
    goal: str
    kpis: list[str]
    owner: str

class GTMStrategy(BaseModel):
    motion: GTMMotion
    icp: ICPProfile
    value_proposition: ValueProp
    channels: list[Channel]
    battlecards: list[CompetitiveBattlecard]
    growth_loops: list[GrowthLoop]
    ninety_day_plan: list[Milestone]
    positioning_statement: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class ContentAsset(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type: ContentType
    title: str
    body: str
    target_icp: str
    validation_status: ValidationStatus = ValidationStatus.PENDING
    brand_alignment_score: Optional[float] = None
    revision_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── LangGraph State ────────────────────────────────────────────────────────

class GTMState(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    company_id: UUID
    user_id: UUID
    messages: list[dict[str, Any]] = Field(default_factory=list)
    current_agent: Optional[str] = None
    research_report: Optional[ResearchReport] = None
    gtm_strategy: Optional[GTMStrategy] = None
    content_assets: list[ContentAsset] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── SSE Events ─────────────────────────────────────────────────────────────

class AgentEventType(str, Enum):
    AGENT_START = "agent_start"
    AGENT_PROGRESS = "agent_progress"
    AGENT_OUTPUT = "agent_output"
    AGENT_COMPLETE = "agent_complete"
    ERROR = "error"
    DONE = "done"

class AgentEvent(BaseModel):
    event: AgentEventType
    agent: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── API Request / Response Models ──────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    company_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class ChatRequest(BaseModel):
    session_id: Optional[UUID] = None
    message: str
    company_id: UUID

class StrategyGenerateRequest(BaseModel):
    company_profile: CompanyProfile
    additional_context: Optional[str] = None

class ContentGenerateRequest(BaseModel):
    strategy_id: UUID
    content_types: list[ContentType]
    count_per_type: int = 3
