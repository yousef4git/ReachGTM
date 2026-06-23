# ReachGTM — build the "ReachGTM Roadmap" Projects v2 board UNDER yousef4git.
#
# WHO RUNS THIS: Yousef (the repo owner). A collaborator cannot create a project
# under a personal account, which is why this must be run by yousef4git.
#
# PREREQS (one time):
#   1. Install GitHub CLI:  winget install --id GitHub.cli   (or https://cli.github.com)
#   2. Log in AS YOURSELF with the project scope:
#        gh auth login --hostname github.com --git-protocol https --web --scopes "repo,project,read:org"
#      (Authorize the one-time code in the browser.)
#   3. Run this script:   pwsh ./scripts/setup_github_project.ps1
#
# WHAT IT DOES (idempotent):
#   - creates/reuses the "ReachGTM Roadmap" board under yousef4git
#   - links it to the repo's Projects tab
#   - rewrites the Status field columns to: To Do / In Progress / In Review / Done
#   - adds every open issue and sets each to "To Do"
# It does NOT create issues/labels/milestones — those already exist on the repo.
#
# NOTE: GitHub's API cannot configure a view's *layout*. After this runs, open the
# board and do the one click described at the end to switch it to a Board view
# grouped by Status. (Status columns themselves are created by this script.)

$ErrorActionPreference = 'Continue'
$repo  = 'yousef4git/ReachGTM'
$owner = 'yousef4git'
$title = 'ReachGTM Roadmap'

function Die($m) { Write-Error $m; exit 1 }

# --- sanity: correct account + scope ---
$me = (gh api user --jq '.login' 2>$null)
if ($LASTEXITCODE -ne 0) { Die "Not logged in. Run: gh auth login --hostname github.com --web --scopes 'repo,project,read:org'" }
if ($me -ne $owner) { Write-Warning "Logged in as '$me', not '$owner'. Creating a board under '$owner' requires you to BE $owner; this will fail otherwise." }

# --- create or reuse the project ---
$projNum = gh project list --owner $owner --format json --jq ".projects[] | select(.title==`"$title`") | .number" 2>$null | Select-Object -First 1
if ($projNum) {
  Write-Host "Reusing existing project #$projNum"
} else {
  $proj = gh project create --owner $owner --title $title --format json | ConvertFrom-Json
  if ($LASTEXITCODE -ne 0) { Die "Failed to create project (need 'project' scope and you must own '$owner')." }
  $projNum = $proj.number
  Write-Host "Created project #$projNum -> $($proj.url)"
}

# --- resolve project node id + Status field id ---
$projId = gh project view $projNum --owner $owner --format json --jq '.id'
$fields = gh project field-list $projNum --owner $owner --format json | ConvertFrom-Json
$statusField = $fields.fields | Where-Object { $_.name -eq 'Status' } | Select-Object -First 1
if (-not $statusField) { Die "Could not find the Status field." }
$statusFieldId = $statusField.id

# --- link to the repo's Projects tab ---
gh project link $projNum --owner $owner --repo $repo 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { Write-Host "Linked to $repo" } else { Write-Host "(link skipped or already linked)" }

# --- rewrite the Status columns: To Do / In Progress / In Review / Done ---
# (Skip if already customized so re-runs don't recreate option ids.)
$curOpts = (gh project field-list $projNum --owner $owner --format json | ConvertFrom-Json).fields |
           Where-Object { $_.id -eq $statusFieldId } | Select-Object -ExpandProperty options -ErrorAction SilentlyContinue
$haveInReview = $curOpts | Where-Object { $_.name -eq 'In Review' }
if (-not $haveInReview) {
  $mut = @'
mutation($fieldId: ID!) {
  updateProjectV2Field(input:{
    fieldId: $fieldId,
    singleSelectOptions: [
      {name:"To Do",       color:GRAY,   description:"Not started"},
      {name:"In Progress", color:YELLOW, description:"Actively being worked on"},
      {name:"In Review",   color:PURPLE, description:"PR open / under review"},
      {name:"Done",        color:GREEN,  description:"Merged / complete"}
    ]
  }){ projectV2Field { ... on ProjectV2SingleSelectField { options { id name } } } }
}
'@
  $upd = gh api graphql -f query=$mut -f fieldId=$statusFieldId | ConvertFrom-Json
  if ($LASTEXITCODE -ne 0) { Die "Failed to update Status options." }
  Write-Host "Status columns set: To Do / In Progress / In Review / Done"
}

# --- get the 'To Do' option id (fresh, after any update) ---
$opts = (gh api graphql -f query='query($id: ID!){ node(id:$id){ ... on ProjectV2SingleSelectField { options { id name } } } }' -f id=$statusFieldId | ConvertFrom-Json).data.node.options
$todoId = ($opts | Where-Object { $_.name -eq 'To Do' }).id
if (-not $todoId) { Die "Could not resolve the 'To Do' option id." }

# --- add every open issue and set Status = To Do ---
$urls = gh issue list --repo $repo --state open --limit 200 --json url --jq '.[].url'
Write-Host ("Adding {0} open issues and setting them to 'To Do'..." -f $urls.Count)
$setMut = @'
mutation($p: ID!, $i: ID!, $f: ID!, $o: String!) {
  updateProjectV2ItemFieldValue(input:{projectId:$p, itemId:$i, fieldId:$f, value:{singleSelectOptionId:$o}}){ projectV2Item { id } }
}
'@
$ok = 0; $fail = 0
foreach ($u in $urls) {
  if (-not $u) { continue }
  $item = gh project item-add $projNum --owner $owner --url $u --format json | ConvertFrom-Json
  if ($LASTEXITCODE -ne 0 -or -not $item.id) { $fail++; continue }
  gh api graphql -f query=$setMut -f p=$projId -f i=$item.id -f f=$statusFieldId -f o=$todoId 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) { $ok++ } else { $fail++ }
}

Write-Host ""
Write-Host "Done. $ok item(s) added & set to 'To Do', $fail failed."
Write-Host "Board: https://github.com/users/$owner/projects/$projNum"
Write-Host ""
Write-Host "ONE manual click (GitHub API can't set view layout):"
Write-Host "  1. Open the board link above."
Write-Host "  2. The default view is a Table. Click the view tab's drop-down (or the + to add a view)"
Write-Host "     and choose 'Board' layout; set 'Group by' = Status."
Write-Host "  -> You'll get To Do / In Progress / In Review / Done columns with every issue under To Do."
Write-Host "  (Optional) Add a second view: Table layout, Group by = Milestone, to see Week 1/2/3 + Backlog."
