"""Reusable HTTP cassette (record/replay) helpers for the agents test suite.

A "cassette" here is a JSON file in this directory holding the body of a real
upstream HTTP response (authored to the provider's real response schema). Tests
use `respx` to intercept the outbound HTTP call and replay the recorded body,
so the production code path that builds the request and parses the response runs
for real — deterministically and network-free.

This started for the OpenAI chat-completions endpoint exercised by the content
node, but the helpers are intentionally provider-agnostic so future connectors
(HubSpot / Salesforce, etc.) can drop a cassette JSON in this folder and mount
it the same way.

The sentinel convention
-----------------------
Each cassette embeds a recognisable sentinel string in its payload (see
`CASSETTE_SENTINEL`). A test can assert the sentinel surfaces in the system
under test's output to *prove* the replayed cassette — not an offline fallback —
produced the result.

Re-recording
------------
The committed cassettes are authored-to-shape. To re-record against a live API,
point respx at record mode (or capture a real response) and overwrite the JSON;
the schema is already the real provider schema, so replay behaviour is unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import respx

# Recognisable marker embedded in cassette payloads. A test asserting this string
# appears downstream proves the replayed response (not a template fallback) ran.
CASSETTE_SENTINEL = "CASSETTE_SENTINEL_REACHGTM_OPENAI_REPLAY"

# Real upstream endpoints the cassettes stand in for.
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"

_CASSETTE_DIR = Path(__file__).parent


def load_cassette(name: str) -> dict[str, Any]:
    """Load a cassette JSON body by file name (with or without `.json`)."""
    if not name.endswith(".json"):
        name = f"{name}.json"
    path = _CASSETTE_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Cassette not found: {path}")
    return json.loads(path.read_text())


def mount_openai_chat_cassette(
    router: respx.Router,
    cassette_name: str,
    *,
    status_code: int = 200,
) -> respx.Route:
    """Mount a respx route that replays an OpenAI chat-completions cassette.

    `router` is a respx router/mock (e.g. from `respx.mock(...)` or the
    `respx_mock` fixture). Every POST to the chat-completions endpoint replays
    the recorded cassette body. Returns the route for further assertions
    (e.g. `route.called`).
    """
    body = load_cassette(cassette_name)
    return router.post(OPENAI_CHAT_COMPLETIONS_URL).mock(
        return_value=httpx.Response(status_code, json=body)
    )
