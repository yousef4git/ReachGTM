import pytest
from uuid import uuid4

from shared.schemas import (
    ContentAsset,
    ContentType,
    GTMState,
    ValidationStatus,
)

from agents.app.graph.nodes.brand_alignment import brand_alignment_node


@pytest.mark.asyncio
async def test_brand_alignment_node_updates_assets():
    asset = ContentAsset(
        type=ContentType.COLD_EMAIL,
        title="Test Email",
        body="Sample content",
        target_icp="SaaS Founders",
    )

    state = GTMState(
        company_id=uuid4(),
        user_id=uuid4(),
        content_assets=[asset],
    )

    updated_state = await brand_alignment_node(state)

    assert updated_state.current_agent == "brand_alignment"
    assert len(updated_state.content_assets) == 1

    validated_asset = updated_state.content_assets[0]

    assert validated_asset.brand_alignment_score is not None
    assert validated_asset.validation_status in (
        ValidationStatus.APPROVED,
        ValidationStatus.REVISED,
        ValidationStatus.REJECTED,
    )


class _ExplodingRetriever:
    """Retriever stub that fails the way a misconfigured DB/embeddings client would."""

    async def retrieve(self, *args, **kwargs):
        raise RuntimeError("connection refused")


@pytest.mark.asyncio
async def test_brand_alignment_failure_does_not_reject_content():
    """A retriever/infra failure must not be surfaced as a rejected, 0%-on-brand asset.

    Regression test: previously any exception in validation marked the asset
    REJECTED with brand_alignment_score=0.0, so every card rendered a red
    "Rejected / 0% on-brand" badge when the retriever was down.
    """
    asset = ContentAsset(
        type=ContentType.COLD_EMAIL,
        title="Test Email",
        body="Sample content",
        target_icp="SaaS Founders",
    )

    state = GTMState(
        company_id=uuid4(),
        user_id=uuid4(),
        content_assets=[asset],
    )

    updated_state = await brand_alignment_node(state, retriever=_ExplodingRetriever())

    validated_asset = updated_state.content_assets[0]

    # Validation could not run → asset stays reviewable, not rejected.
    assert validated_asset.validation_status == ValidationStatus.PENDING
    # Unknown score must be null (hidden in UI), never a misleading 0%.
    assert validated_asset.brand_alignment_score is None
    assert validated_asset.revision_notes is not None