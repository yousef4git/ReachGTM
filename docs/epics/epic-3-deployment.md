# Epic 3 — Production Deployment (Phase 3: Infra Rotation)

**Goal:** Ship to AWS ECS Fargate. Everyone deploys 1-2 pieces of infrastructure they haven't touched yet.

---

---

## PRs in this Epic

| PR | Title | Owner | Branch | What They Learn |
|----|-------|-------|--------|----------------|
| #19 | AWS infra — ECR repos, ECS cluster, task definitions | **Abdulrahem** | `epic-3/pr-19-aws-infra` | ECS Fargate, container orchestration, Terraform |
| #20 | GitHub OIDC + deploy pipeline | **Bader** | `epic-3/pr-20-oidc` | IAM OIDC, GitHub Actions secrets, secure deploy |
| #21 | RDS + ElastiCache provisioning | **Yousef** | `epic-3/pr-21-rds` | PostgreSQL managed, Redis parameter groups |
| #22 | S3 storage service (document uploads) | **Yousef** | `epic-3/pr-22-s3` | boto3, presigned URLs, bucket policies |
| #23 | CloudFront CDN for frontend | **Nawaf** | `epic-3/pr-23-cdn` | CDN, origin groups, edge caching |
| #24 | Databar + Fetch MCP server integration | **Abdulrahem** | `epic-3/pr-24-mcp-extra` | Deepens MCP knowledge |
| #25 | Production smoke test suite | **All 4 paired** | `epic-3/pr-25-smoke-tests` | Integration testing, CI/CD verification |

## PR Count Per Person

| Person | PRs |
|--------|-----|
| **Nawaf** | #23, #25 (paired) |
| **Bader** | #20, #25 (paired) |
| **Abdulrahem** | #19, #24, #25 (paired) |
| **Yousef** | #21, #22, #25 (paired) |

## Acceptance Criteria

- [ ] `git push origin main` triggers deploy.yml and updates ECS services
- [ ] All 3 services reachable at production URLs with valid SSL
- [ ] RDS PostgreSQL with pgvector extension (HNSW index created by init.sql)
- [ ] ElastiCache Redis connected (rate limiter operational)
- [ ] S3 document uploads working via storage_service.py
- [ ] Databar and Fetch MCP tools available to research agent
- [ ] CloudFront serves frontend with proper caching headers
- [ ] Zero-downtime deploy via ECS rolling update
- [ ] Every team member has deployed at least 1 infra resource
