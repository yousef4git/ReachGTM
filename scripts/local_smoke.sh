#!/usr/bin/env bash
# Local end-to-end smoke test for the docker-compose stack.
# Exercises: health -> register -> login -> authed reads -> SSE strategy stream.
set -uo pipefail

API=http://localhost:8000
pass=0; fail=0
chk() { if [ "$1" = "$2" ]; then echo "  PASS  $3 (got $1)"; pass=$((pass+1)); else echo "  FAIL  $3 (want $2, got $1)"; fail=$((fail+1)); fi; }

echo "== health =="
chk "$(curl -s -o /dev/null -w '%{http_code}' $API/health)" 200 "backend /health"
chk "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001/health)" 200 "agents /health"

echo "== register =="
EMAIL="smoke+$(date +%s)@acme.test"
REG=$(curl -s -w '\n%{http_code}' -X POST $API/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"Passw0rd!23\",\"company_name\":\"Acme Smoke\"}")
REG_CODE=$(echo "$REG" | tail -1); REG_BODY=$(echo "$REG" | sed '$d')
chk "$REG_CODE" 201 "POST /auth/register"
TOKEN=$(echo "$REG_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
[ -n "$TOKEN" ] && echo "  token acquired (${#TOKEN} chars)" || echo "  NO TOKEN"

echo "== login =="
LOGIN=$(curl -s -o /dev/null -w '%{http_code}' -X POST $API/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"Passw0rd!23\"}")
chk "$LOGIN" 200 "POST /auth/login"

echo "== authed reads =="
AUTH="Authorization: Bearer $TOKEN"
chk "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" $API/api/v1/team/members)" 200 "GET /team/members"
chk "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" $API/api/v1/team/settings)" 200 "GET /team/settings"
chk "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" $API/api/v1/content/)" 200 "GET /content/"
chk "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" $API/api/v1/knowledge/)" 200 "GET /knowledge/"
chk "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" $API/api/v1/usage/summary)" 200 "GET /usage/summary"
echo "  auth guard: unauth team/members should be 401"
chk "$(curl -s -o /dev/null -w '%{http_code}' $API/api/v1/team/members)" 401 "GET /team/members (no token)"

echo "== SSE strategy stream (self-auth GET, max 60s) =="
SSE_FILE=$(mktemp)
curl -s --max-time 60 -N \
  "$API/api/v1/strategy/generate/stream?token=$TOKEN&goal=Launch%20our%20dev-tools%20SaaS%20to%20mid-market&content_types=linkedin_post&count_per_type=1" \
  > "$SSE_FILE" 2>/dev/null
EVENTS=$(grep -c '^event:' "$SSE_FILE" 2>/dev/null || echo 0)
echo "  SSE frames received: $EVENTS"
echo "  event types seen: $(grep '^event:' "$SSE_FILE" | sort -u | tr '\n' ' ')"
if [ "$EVENTS" -ge 1 ]; then echo "  PASS  SSE produced events"; pass=$((pass+1)); else echo "  FAIL  SSE produced no events"; fail=$((fail+1)); echo "  --- first 20 lines ---"; head -20 "$SSE_FILE"; fi
rm -f "$SSE_FILE"

echo ""
echo "== RESULT: $pass passed, $fail failed =="
[ "$fail" -eq 0 ]
