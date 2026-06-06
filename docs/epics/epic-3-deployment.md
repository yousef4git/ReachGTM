# Epic 3 — Production Deployment

**Goal:** Ship to AWS ECS Fargate. Staging auto-deploys. Production deploys via deploy.yml on merge to main.

---

## PRs in this Epic

| PR | Title | Owner | Branch |
|---|---|---|---|
| #19 | AWS infra — ECR repos, ECS cluster, task definitions | Yousef | `epic-3/pr-19-aws-infra` |
| #20 | GitHub OIDC deploy role + Secrets | Yousef | `epic-3/pr-20-oidc` |
| #21 | RDS + ElastiCache provisioning | Nawaf | `epic-3/pr-21-rds` |
| #22 | S3 storage service (document uploads) | Nawaf | `epic-3/pr-22-s3` |
| #23 | CloudFront CDN for frontend | Bader | `epic-3/pr-23-cdn` |
| #24 | Databar + Fetch MCP server integration | Abdulrahem | `epic-3/pr-24-mcp-extra` |
| #25 | Production smoke test suite | All | `epic-3/pr-25-smoke-tests` |

---

## Acceptance Criteria

- [ ] `git push origin main` triggers deploy.yml and updates ECS services
- [ ] All 3 services reachable at production URLs with valid SSL
- [ ] RDS PostgreSQL with pgvector extension (HNSW index created by init.sql)
- [ ] ElastiCache Redis connected (rate limiter operational)
- [ ] S3 document uploads working via storage_service.py
- [ ] Databar and Fetch MCP tools available to research agent
- [ ] Zero-downtime deploy via ECS rolling update
