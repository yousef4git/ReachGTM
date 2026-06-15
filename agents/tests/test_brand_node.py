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