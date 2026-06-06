# Team Guides

Each guide covers: local setup, your specific PRs, exact files to implement, code patterns, test instructions, and PR checklist.

| Guide | Owner | Epic 2 PRs | Epic 3 PRs |
|---|---|---|---|
| [yousef.md](yousef.md) | Yousef (Architecture) | #9 Orchestrator, #11 Strategy, #12 Content, #15 pm-skills, #16 ColdIQ | #19 ECS cluster, #20 OIDC |
| [nawaf.md](nawaf.md) | Nawaf (Backend) | #14 SSE endpoint | #21 RDS/ElastiCache, #22 S3 |
| [bader.md](bader.md) | Bader (Frontend) | #17 Strategy UI, #18 Content/Knowledge UI | #23 CloudFront CDN |
| [abdulrahem.md](abdulrahem.md) | Abdulrahem (ML) | #10 Research node, #13 Brand alignment | #24 Databar/Fetch MCP |

## PR Dependency Order (Epic 2)

```
Yousef PR #9 (orchestrator)     ← start here — unblocks Nawaf
Yousef PR #15 (pm-skills)       ← can be parallel with #9
Yousef PR #16 (coldiq)          ← can be parallel with #9
Abdulrahem PR #10 (research)    ← can be parallel with #9
    ↓
Yousef PR #11 (strategy)        ← needs #10 + #15
    ↓
Yousef PR #12 (content)         ← needs #11 + #16
    ↓
Abdulrahem PR #13 (brand)       ← needs #12
Nawaf PR #14 (SSE)              ← needs #9 (and ideally #12)
Bader PR #17 (strategy UI)      ← needs #14
Bader PR #18 (content UI)       ← needs #17
```

## Branch Rules (everyone)

```
main          ← protected — NEVER push directly — prod deploy only
staging       ← default — all PRs target here
epic-N/pr-N-<name>  ← your feature branch
```

1. Always `git checkout staging && git pull` before creating a feature branch
2. PR targets `staging`, not `main`
3. Tag @yousefalshuwayi as reviewer on every PR
4. Run tests locally before opening the PR
