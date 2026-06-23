#!/usr/bin/env bash
# ReachGTM — build the "ReachGTM Roadmap" Projects v2 board UNDER yousef4git.
# (macOS/Linux bash port of setup_github_project.ps1)
#
# WHO RUNS THIS: Yousef (the repo owner). A collaborator cannot create a project
# under a personal account, which is why this must be run by yousef4git.
#
# PREREQS (one time):
#   1. Install GitHub CLI:  brew install gh      (or https://cli.github.com)
#   2. Log in AS YOURSELF and grant the project scope:
#        gh auth login  --hostname github.com --git-protocol https --web --scopes "repo,project,read:org"
#      ...or, if already logged in, just add the scope:
#        gh auth refresh --hostname github.com --scopes project
#      (Authorize the one-time code in the browser.)
#   3. Run this script:   bash ./scripts/setup_github_project.sh
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

set -uo pipefail

repo='yousef4git/ReachGTM'
owner='yousef4git'
title='ReachGTM Roadmap'

die() { echo "ERROR: $*" >&2; exit 1; }

# --- tooling check ---
command -v gh >/dev/null 2>&1 || die "GitHub CLI ('gh') not found. Install: brew install gh"

# --- sanity: logged in + correct account + has project scope ---
me="$(gh api user --jq '.login' 2>/dev/null)" \
  || die "Not logged in. Run: gh auth login --hostname github.com --web --scopes 'repo,project,read:org'"
if [ "$me" != "$owner" ]; then
  echo "WARNING: Logged in as '$me', not '$owner'. Creating a board under '$owner' requires you to BE $owner; this will fail otherwise." >&2
fi

# Verify the 'project' scope is present (Projects v2 needs it).
if ! gh project list --owner "$owner" --limit 1 >/dev/null 2>&1; then
  die "Your token is missing the 'project' scope. Grant it with:
       gh auth refresh --hostname github.com --scopes project"
fi

# --- create or reuse the project ---
projNum="$(gh project list --owner "$owner" --format json \
            --jq ".projects[] | select(.title==\"$title\") | .number" 2>/dev/null | head -n1)"
if [ -n "$projNum" ]; then
  echo "Reusing existing project #$projNum"
else
  projUrl="$(gh project create --owner "$owner" --title "$title" --format json --jq '.url')" \
    || die "Failed to create project (need 'project' scope and you must own '$owner')."
  projNum="$(gh project list --owner "$owner" --format json \
              --jq ".projects[] | select(.title==\"$title\") | .number" | head -n1)"
  echo "Created project #$projNum -> $projUrl"
fi
[ -n "$projNum" ] || die "Could not resolve the project number."

# --- resolve project node id + Status field id ---
projId="$(gh project view "$projNum" --owner "$owner" --format json --jq '.id')" \
  || die "Could not resolve the project node id."
statusFieldId="$(gh project field-list "$projNum" --owner "$owner" --format json \
                  --jq '.fields[] | select(.name=="Status") | .id' | head -n1)"
[ -n "$statusFieldId" ] || die "Could not find the Status field."

# --- link to the repo's Projects tab ---
if gh project link "$projNum" --owner "$owner" --repo "$repo" >/dev/null 2>&1; then
  echo "Linked to $repo"
else
  echo "(link skipped or already linked)"
fi

# --- rewrite the Status columns: To Do / In Progress / In Review / Done ---
# (Skip if already customized so re-runs don't recreate option ids.)
haveInReview="$(gh project field-list "$projNum" --owner "$owner" --format json \
                 --jq '.fields[] | select(.id=="'"$statusFieldId"'") | .options[]? | select(.name=="In Review") | .name' 2>/dev/null)"
if [ -z "$haveInReview" ]; then
  read -r -d '' mut <<'GQL'
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
GQL
  gh api graphql -f query="$mut" -f fieldId="$statusFieldId" >/dev/null \
    || die "Failed to update Status options."
  echo "Status columns set: To Do / In Progress / In Review / Done"
fi

# --- get the 'To Do' option id (fresh, after any update) ---
todoId="$(gh api graphql \
  -f query='query($id: ID!){ node(id:$id){ ... on ProjectV2SingleSelectField { options { id name } } } }' \
  -f id="$statusFieldId" \
  --jq '.data.node.options[] | select(.name=="To Do") | .id' | head -n1)"
[ -n "$todoId" ] || die "Could not resolve the 'To Do' option id."

# --- add every open issue and set Status = To Do ---
read -r -d '' setMut <<'GQL'
mutation($p: ID!, $i: ID!, $f: ID!, $o: String!) {
  updateProjectV2ItemFieldValue(input:{projectId:$p, itemId:$i, fieldId:$f, value:{singleSelectOptionId:$o}}){ projectV2Item { id } }
}
GQL

# Collect issue URLs portably (macOS ships bash 3.2 — no `mapfile`).
urls=()
while IFS= read -r line; do
  [ -n "$line" ] && urls+=("$line")
done < <(gh issue list --repo "$repo" --state open --limit 200 --json url --jq '.[].url')
echo "Adding ${#urls[@]} open issues and setting them to 'To Do'..."

ok=0; fail=0
for u in ${urls[@]+"${urls[@]}"}; do
  [ -n "$u" ] || continue
  itemId="$(gh project item-add "$projNum" --owner "$owner" --url "$u" --format json --jq '.id' 2>/dev/null)"
  if [ -z "$itemId" ]; then fail=$((fail+1)); continue; fi
  if gh api graphql -f query="$setMut" -f p="$projId" -f i="$itemId" -f f="$statusFieldId" -f o="$todoId" >/dev/null 2>&1; then
    ok=$((ok+1))
  else
    fail=$((fail+1))
  fi
done

echo ""
echo "Done. $ok item(s) added & set to 'To Do', $fail failed."
echo "Board: https://github.com/users/$owner/projects/$projNum"
echo ""
echo "ONE manual click (GitHub API can't set view layout):"
echo "  1. Open the board link above."
echo "  2. The default view is a Table. Click the view tab's drop-down (or the + to add a view)"
echo "     and choose 'Board' layout; set 'Group by' = Status."
echo "  -> You'll get To Do / In Progress / In Review / Done columns with every issue under To Do."
echo "  (Optional) Add a second view: Table layout, Group by = Milestone, to see Week 1/2/3 + Backlog."
