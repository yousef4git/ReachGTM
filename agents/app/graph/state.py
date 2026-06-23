"""LangGraph state for the GTM graph.

Subclasses the shared GTMState contract to attach a messages reducer. We use a
dict-preserving reducer (not langgraph's add_messages) so messages stay plain
dicts: add_messages coerces incoming {"role","content"} dicts into LangChain
Message objects, which then fail validation when LangGraph re-coerces the state
into shared.schemas.GTMState (messages: list[dict]) between nodes.

Keeping the reducer dict-based fixes that without changing the shared contract.
Like add_messages, it dedupes by message id (assigning one when absent) so nodes
that re-emit the full state don't duplicate the history.
"""
import uuid
from typing import Annotated, Any

from langchain_core.messages import BaseMessage

from shared.schemas import GTMState as _GTMState

_ROLE_BY_TYPE = {"human": "user", "ai": "assistant", "system": "system", "tool": "tool"}


def _as_message_dict(message: Any) -> dict[str, Any]:
    """Normalise a message (LangChain BaseMessage or dict) to a plain dict with an id."""
    if isinstance(message, BaseMessage):
        out: dict[str, Any] = {
            "role": _ROLE_BY_TYPE.get(message.type, message.type),
            "content": message.content,
        }
        if getattr(message, "id", None):
            out["id"] = message.id
    elif isinstance(message, dict):
        out = dict(message)
    else:
        out = {"role": "user", "content": str(message)}
    out.setdefault("id", str(uuid.uuid4()))
    return out


def merge_messages(left: list, right: Any) -> list[dict[str, Any]]:
    """LangGraph reducer: append messages as plain dicts, deduped by id.

    Mirrors add_messages' append + id-dedupe behaviour but preserves the
    shared.schemas.GTMState contract (messages: list[dict]), so the state stays
    valid when LangGraph re-coerces it between nodes and nodes that re-emit the
    full state don't duplicate history.
    """
    right_list = right if isinstance(right, list) else [right]
    merged = [_as_message_dict(m) for m in left]
    by_id = {m["id"]: i for i, m in enumerate(merged)}
    for raw in right_list:
        item = _as_message_dict(raw)
        if item["id"] in by_id:
            merged[by_id[item["id"]]] = item  # update existing message
        else:
            by_id[item["id"]] = len(merged)
            merged.append(item)
    return merged


class GTMState(_GTMState):
    messages: Annotated[list[dict[str, Any]], merge_messages] = []
