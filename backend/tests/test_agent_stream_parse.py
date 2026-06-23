import json

from backend.app.services.agent_stream import _parse_frame


def test_parse_frame_extracts_event_and_data():
    payload = {"event": "agent_complete", "data": {"content_assets": [1, 2], "gtm_strategy": {}}}
    frame = f"event: agent_complete\ndata: {json.dumps(payload)}"
    event_type, data = _parse_frame(frame)
    assert event_type == "agent_complete"
    assert data == {"content_assets": [1, 2], "gtm_strategy": {}}


def test_parse_frame_done_has_no_inner_data():
    frame = 'event: done\ndata: {"event": "done"}'
    event_type, data = _parse_frame(frame)
    assert event_type == "done"
    assert data is None


def test_parse_frame_tolerates_malformed_data():
    frame = "event: agent_progress\ndata: not-json"
    event_type, data = _parse_frame(frame)
    assert event_type == "agent_progress"
    assert data is None
