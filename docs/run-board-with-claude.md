# Set up the ReachGTM board — for Yousef (run with Claude Code)

The issues, labels, and milestones already exist on `yousef4git/ReachGTM`. The only
thing left is the **Projects v2 board**, which must be created by the repo owner
(@yousef4git) — a collaborator can't create a board under someone else's personal
account. A ready, validated script does the work: [`scripts/setup_github_project.ps1`](../scripts/setup_github_project.ps1).

## Option A — paste this prompt into Claude Code

Open Claude Code in the ReachGTM repo (as Yousef) and paste the prompt below verbatim:

```text
You're setting up the GitHub Projects v2 board for this repo (yousef4git/ReachGTM).
The 37 issues, 16 labels, and 4 milestones already exist — do NOT recreate them.
Your job: create the "ReachGTM Roadmap" board UNDER the yousef4git account, set its
Status columns to To Do / In Progress / In Review / Done, add every open issue, and
set each to "To Do". A finished, idempotent script already exists at
scripts/setup_github_project.ps1 — use it, don't reinvent it.

Do this:
1. Check GitHub CLI is installed: run `gh --version`. If missing, install it
   (`winget install --id GitHub.cli`, or https://cli.github.com).
2. Check I'm logged in AS yousef4git WITH the project scope: run `gh auth status`.
   It must show account `yousef4git` and scopes including `project` and `repo`.
   If it's the wrong account or missing the project scope, run:
   `gh auth login --hostname github.com --git-protocol https --web --scopes "repo,project,read:org"`
   then tell me to open https://github.com/login/device and enter the one-time code
   it prints, and wait for me to authorize before continuing.
3. Run the script: `pwsh ./scripts/setup_github_project.ps1`
   (on Windows PowerShell use: `powershell -ExecutionPolicy Bypass -File ./scripts/setup_github_project.ps1`).
4. The GitHub API can't set a view's layout, so after the script finishes, tell me
   to open the printed board URL and: switch the view to "Board" layout with
   "Group by = Status" (gives To Do / In Progress / In Review / Done columns), and
   optionally add a second "Table" view grouped by "Milestone" (Week 1/2/3 + Backlog).
5. Verify: the board should contain ~37 issues, all under "To Do". Report the board URL.

If a step fails, read the actual error and fix the root cause (almost always: wrong
account or missing `project` scope — re-auth as yousef4git). The script is idempotent,
so it's safe to re-run.
```

## Option B — run it yourself (no Claude)

```powershell
# 1. install gh if needed:  winget install --id GitHub.cli
# 2. log in AS yourself with the project scope:
gh auth login --hostname github.com --git-protocol https --web --scopes "repo,project,read:org"
# 3. run the script:
pwsh ./scripts/setup_github_project.ps1
```

Then open the printed board URL → switch to **Board** layout, **Group by = Status**.

## What you'll get
- Board **ReachGTM Roadmap** under `yousef4git`, linked to the repo's Projects tab
- Columns: **To Do / In Progress / In Review / Done**
- All ~37 open issues added and placed in **To Do**
