# Yousef — Architecture Lead Guide

**Your role:** LangGraph orchestration, strategy/content nodes, pm-skills, ColdIQ skills, AWS infra, overall architecture decisions.

---

## Your PRs

| Epic | PR | Branch | Title |
|---|---|---|---|
| 2 | #9 | `epic-2/pr-9-orchestrator` | Orchestrator node — real routing logic |
| 2 | #11 | `epic-2/pr-11-strategy` | Strategy node — GTM framework generation |
| 2 | #12 | `epic-2/pr-12-content` | Content node — cold email + LinkedIn generation |
| 2 | #15 | `epic-2/pr-15-pm-skills` | pm-skills LangChain tool wrappers |
| 2 | #16 | `epic-2/pr-16-coldiq` | ColdIQ LangChain tool wrappers |
| 3 | #19 | `epic-3/pr-19-aws-infra` | AWS infra — ECR repos, ECS cluster, task definitions |
| 3 | #20 | `epic-3/pr-20-oidc` | GitHub OIDC deploy role + Secrets |

---

## Local Setup

```bash
git clone https://github.com/yousef4git/ReachGTM.git
cd ReachGTM
cp .env.example .env
# Fill in: OPENAI_API_KEY, JWT_SECRET, LANGSMITH_API_KEY, PERPLEXITY_API_KEY
docker compose -f infra/docker-compose.yml up --build
```

Verify all services:
```bash
curl http://localhost:8000/health  # {"service":"backend","status":"ok"}
curl http://localhost:8001/health  # {"service":"agents","status":"ok"}
curl http://localhost:3000         # HTML (redirects to /dashboard)
```

Check LangSmith traces at https://smith.langchain.com — project `reachgtm`.

---

## Epic 2 Order

Implement in this order — later PRs depend on earlier ones:

```
PR #9 (orchestrator) → unblocks Nawaf's PR #14 (/run endpoint)
PR #11 (strategy)    → depends on research (Abdulrahem's PR #10)
PR #12 (content)     → depends on #11 (strategy must exist in state)
PR #15 (pm-skills)   → used inside #11 strategy node
PR #16 (coldiq)      → used inside #12 content node
```

---

## PR #9 — Orchestrator Node

**Branch:** `epic-2/pr-9-orchestrator`

```bash
git checkout staging && git pull
git checkout -b epic-2/pr-9-orchestrator
```

### What to build

The orchestrator is the entry point. It reads the current state and decides routing — either directly to content (if strategy exists) or to research first. It also parses user intent.

```python
# agents/app/graph/nodes/orchestrator.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from agents.app.graph.state import GTMState
from agents.app.prompts.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
import json

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

async def orchestrator_node(state: GTMState) -> dict:
    """Parse intent, set metadata, return routing hint."""
    last_message = state.messages[-1]["content"] if state.messages else ""
    company_profile = state.metadata.get("company_profile", {})

    context = f"""Current state:
- research_report exists: {state.research_report is not None}
- gtm_strategy exists: {state.gtm_strategy is not None}
- content_assets count: {len(state.content_assets)}
- company: {company_profile.get('name', 'unknown')}
- user message: {last_message}"""

    response = await llm.ainvoke([
        SystemMessage(content=ORCHESTRATOR_SYSTEM_PROMPT),
        HumanMessage(content=context),
    ])

    # The conditional edge function _route_from_orchestrator in graph.py
    # handles actual routing — we just update state here
    return {"current_agent": "orchestrator"}
```

### Also update: wire `/run` in agents/app/main.py

After this PR merges, update the `/run` endpoint so Nawaf can connect the SSE stream:

```python
# agents/app/main.py — replace /run stub
from agents.app.graph.graph import graph
from agents.app.graph.state import GTMState
import uuid as _uuid

@app.post("/run")
async def run(body: dict):
    state = GTMState(
        session_id=_uuid.UUID(body.get("session_id", str(_uuid.uuid4()))),
        company_id=_uuid.UUID(body["company_id"]),
        user_id=_uuid.UUID(body["user_id"]),
        metadata={"company_profile": body.get("company_profile", {})},
    )
    result = await graph.ainvoke(state.model_dump())
    return result
```

For streaming, use `graph.astream_events` — this powers Nawaf's SSE endpoint.

### PR checklist

- [ ] Orchestrator node runs without error
- [ ] `/run` endpoint invokes the full graph
- [ ] LangSmith trace appears in dashboard after a `/run` call
- [ ] `pytest agents/tests/ -v` passes
- [ ] Coordinate with Nawaf — share the `/run` request/response shape

---

## PR #15 — pm-skills LangChain Tool Wrappers

**Branch:** `epic-2/pr-15-pm-skills`

Implement this before PR #11 (strategy node uses these tools).

### What to build

The pm-skills library provides positioning and ICP frameworks as structured tools. Wrap them as LangChain `@tool` functions:

```python
# agents/app/tools/skills/pm_skills.py
from langchain_core.tools import tool
from pydantic import BaseModel

class ICPInput(BaseModel):
    segments: list[dict]
    competitors: list[dict]
    company_stage: str

@tool("synthesize_icp", args_schema=ICPInput)
def synthesize_icp(segments: list[dict], competitors: list[dict], company_stage: str) -> dict:
    """Synthesize customer segments and competitive data into a primary ICP profile."""
    # Scoring logic: weight pain-point overlap, segment size, competitive gap
    # Return the highest-scoring segment as the primary ICP
    primary = max(segments, key=lambda s: len(s.get("pain_points", []))) if segments else {}
    return {
        "title": primary.get("name", "Unknown Buyer"),
        "pain_points": primary.get("pain_points", []),
        "buying_triggers": primary.get("buying_triggers", []),
        "company_stage_fit": company_stage,
    }

class PositioningInput(BaseModel):
    icp: dict
    competitors: list[dict]
    product_description: str

@tool("generate_positioning", args_schema=PositioningInput)
def generate_positioning(icp: dict, competitors: list[dict], product_description: str) -> dict:
    """Generate a positioning statement and value proposition."""
    # Simple template — the LLM fills in the specifics
    return {
        "positioning_template": f"For {icp.get('title', 'decision-makers')} who struggle with {', '.join(icp.get('pain_points', [])[:2])}, "
                                 f"{product_description} unlike {competitors[0]['name'] if competitors else 'alternatives'}.",
    }

PM_SKILLS = [synthesize_icp, generate_positioning]
```

---

## PR #16 — ColdIQ LangChain Tool Wrappers

**Branch:** `epic-2/pr-16-coldiq`

Implement before PR #12 (content node uses these).

### What to build

ColdIQ provides email and LinkedIn copy frameworks. Wrap as LangChain tools:

```python
# agents/app/tools/skills/coldiq_skills.py
from langchain_core.tools import tool
from pydantic import BaseModel

class EmailSequenceInput(BaseModel):
    icp: dict
    value_prop: dict
    signal: str  # hiring, funding, product_launch, leadership_change

@tool("generate_email_sequence", args_schema=EmailSequenceInput)
def generate_email_sequence(icp: dict, value_prop: dict, signal: str) -> dict:
    """Generate a 3-email cold outreach sequence using ColdIQ's signal-based framework."""
    return {
        "emails": [
            {
                "position": 1,
                "subject_line_template": f"[{signal.replace('_',' ').title()}] → {{pattern_interrupt}}",
                "opener_type": "signal_acknowledgment",
                "cta": "soft — reply if relevant",
                "word_count_target": 80,
            },
            {
                "position": 2,
                "subject_line_template": "Re: {{first_name}}",
                "opener_type": "social_proof",
                "cta": "case study reference",
                "word_count_target": 100,
            },
            {
                "position": 3,
                "subject_line_template": "Last note — {{value_prop_headline}}",
                "opener_type": "direct_ask",
                "cta": "15-min call",
                "word_count_target": 60,
            },
        ],
        "icp_title": icp.get("title", ""),
        "signal_used": signal,
    }

class LinkedInPostInput(BaseModel):
    topic: str
    audience: str
    hook_type: str  # contrarian, question, bold_claim, story

@tool("generate_linkedin_post", args_schema=LinkedInPostInput)
def generate_linkedin_post(topic: str, audience: str, hook_type: str) -> dict:
    """Generate a LinkedIn post structure using ColdIQ's scroll-stopper framework."""
    return {
        "hook_instruction": f"Write a {hook_type} hook about {topic} for {audience}. Under 150 chars. No emojis.",
        "body_structure": "3-5 short paragraphs. One idea per paragraph. Plain language.",
        "cta": "End with a question or 'comment below' — never 'link in bio'.",
        "estimated_engagement": "high" if hook_type in ["contrarian", "bold_claim"] else "medium",
    }

COLDIQ_SKILLS = [generate_email_sequence, generate_linkedin_post]
```

---

## PR #11 — Strategy Node

**Branch:** `epic-2/pr-11-strategy`

**Depends on:** PR #10 (Abdulrahem's research node must set `research_report` in state), PR #15 (pm-skills).

```python
# agents/app/graph/nodes/strategy.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from agents.app.graph.state import GTMState
from agents.app.prompts.strategy import STRATEGY_SYSTEM_PROMPT
from agents.app.tools.skills.pm_skills import PM_SKILLS
from shared.schemas import GTMStrategy
import json

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
llm_with_tools = llm.bind_tools(PM_SKILLS)

async def strategy_node(state: GTMState) -> dict:
    if not state.research_report:
        return {"current_agent": "strategy", "errors": state.errors + ["No research report in state"]}

    prompt = f"""Based on this research, build a complete GTM strategy:

{state.research_report.model_dump_json(indent=2)}

Return a GTMStrategy as JSON matching the schema exactly."""

    response = await llm.ainvoke([
        SystemMessage(content=STRATEGY_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    data = json.loads(response.content)
    strategy = GTMStrategy(**data)

    return {
        "gtm_strategy": strategy,
        "current_agent": "strategy",
    }
```

---

## PR #12 — Content Node

**Branch:** `epic-2/pr-12-content`

**Depends on:** PR #11 (strategy must exist in state), PR #16 (coldiq skills).

```python
# agents/app/graph/nodes/content.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from agents.app.graph.state import GTMState
from agents.app.prompts.content import CONTENT_SYSTEM_PROMPT
from agents.app.tools.skills.coldiq_skills import COLDIQ_SKILLS
from shared.schemas import ContentAsset, ContentType, ValidationStatus
import json, uuid

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

async def content_node(state: GTMState) -> dict:
    if not state.gtm_strategy:
        return {"current_agent": "content", "errors": state.errors + ["No GTM strategy in state"]}

    strategy = state.gtm_strategy
    assets = []

    # Generate cold email sequence
    email_prompt = f"""Using this GTM strategy, write a 3-email cold outreach sequence:
Strategy: {strategy.model_dump_json(indent=2)}
Target ICP: {strategy.icp.title} at {strategy.icp.industry} companies

Return a JSON array of ContentAsset objects."""

    response = await llm.ainvoke([
        SystemMessage(content=CONTENT_SYSTEM_PROMPT),
        HumanMessage(content=email_prompt),
    ])

    try:
        email_data = json.loads(response.content)
        for item in email_data:
            assets.append(ContentAsset(
                type=ContentType.COLD_EMAIL,
                title=item.get("title", "Cold Email"),
                body=item.get("body", ""),
                target_icp=strategy.icp.title,
                validation_status=ValidationStatus.PENDING,
            ))
    except Exception as e:
        state.errors.append(f"Content generation error: {e}")

    # Generate LinkedIn post
    linkedin_prompt = f"""Write 2 LinkedIn posts for this GTM strategy:
{strategy.positioning_statement}
Target: {strategy.icp.title}

Return a JSON array of ContentAsset objects."""

    response2 = await llm.ainvoke([
        SystemMessage(content=CONTENT_SYSTEM_PROMPT),
        HumanMessage(content=linkedin_prompt),
    ])
    try:
        linkedin_data = json.loads(response2.content)
        for item in linkedin_data:
            assets.append(ContentAsset(
                type=ContentType.LINKEDIN_POST,
                title=item.get("title", "LinkedIn Post"),
                body=item.get("body", ""),
                target_icp=strategy.icp.title,
                validation_status=ValidationStatus.PENDING,
            ))
    except Exception as e:
        state.errors.append(f"LinkedIn generation error: {e}")

    return {
        "content_assets": assets,
        "current_agent": "content",
    }
```

---

## Epic 3 — AWS Infrastructure

### PR #19 — ECS Cluster + Task Definitions

**Branch:** `epic-3/pr-19-aws-infra`

**Files to create:**
- `infra/terraform/main.tf` — provider, backend (S3 remote state)
- `infra/terraform/ecs.tf` — ECS cluster, task definitions for backend/agents/frontend
- `infra/terraform/ecr.tf` — 3 ECR repos (backend, agents, frontend)
- `infra/terraform/alb.tf` — Application Load Balancer + target groups
- `infra/terraform/networking.tf` — VPC, subnets, security groups (or reference existing)

**Key ECS task definition settings:**
```hcl
resource "aws_ecs_task_definition" "backend" {
  family                   = "reachgtm-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = "backend"
    image = "${aws_ecr_repository.backend.repository_url}:latest"
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]
    environment = [
      { name = "ENVIRONMENT", value = "production" }
    ]
    secrets = [
      { name = "OPENAI_API_KEY", valueFrom = "arn:aws:secretsmanager:..." },
      { name = "JWT_SECRET", valueFrom = "arn:aws:secretsmanager:..." },
      { name = "DATABASE_URL", valueFrom = "arn:aws:secretsmanager:..." },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group  = "/ecs/reachgtm-backend"
        awslogs-region = var.aws_region
        awslogs-stream-prefix = "ecs"
      }
    }
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval    = 30
      timeout     = 10
      retries     = 3
      startPeriod = 60
    }
  }])
}
```

### PR #20 — GitHub OIDC Deploy Role

**Branch:** `epic-3/pr-20-oidc`

```hcl
# infra/terraform/github_oidc.tf
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_deploy" {
  name = "reachgtm-github-deploy"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:yousef4git/ReachGTM:ref:refs/heads/main"
        }
      }
    }]
  })
}
```

Add this ARN as `AWS_DEPLOY_ROLE_ARN` in GitHub repo secrets. Update `.github/workflows/deploy.yml` to use `secrets.AWS_DEPLOY_ROLE_ARN`.

---

## Branch Rules

```
main (protected — prod deploy triggers on merge here)
  ↑ PR from staging only
staging (default — all your PRs go here)
  ↑ PR from your feature branch
epic-2/pr-9-orchestrator  ← your branch
```

**PR order for Epic 2:**
1. Open PR #9 (orchestrator) first — Nawaf needs it to wire `/run`
2. Open PR #15 (pm-skills) and PR #16 (coldiq) — can be done in parallel
3. Open PR #11 (strategy) after #15 and after Abdulrahem's PR #10 merges
4. Open PR #12 (content) after #11 and #16 merge

---

## Architecture Decisions Log

Key decisions made in Epic 1 (see `docs/architecture.md` for full ADRs):

| Decision | Choice | Reason |
|---|---|---|
| Agent framework | LangGraph | Native checkpointing, conditional routing, streaming |
| Vector store | pgvector (HNSW) | Same Postgres instance, SQL joins, RLS enforcement |
| Multi-tenancy | Shared schema + RLS | Simple at MVP scale, upgrade path to per-tenant exists |
| Deployment | AWS ECS Fargate | No cluster management, same ECR/Docker skills as local |
| Frontend streaming | Native SSE (EventSource) | Works through ALB without sticky sessions, no library needed |
| LLM | gpt-4o-mini | Cost-effective, fast enough for streaming UX |

**No Vercel** — the frontend runs on ECS Fargate behind CloudFront (Bader's PR #23). Do not add any Vercel configuration.
