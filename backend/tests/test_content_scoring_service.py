from uuid import uuid4

from backend.app.services.content_scoring_service import (
    ContentPerformanceMetrics,
    score_content_asset,
)
from shared.schemas import ContentAsset, ContentType


def test_content_effectiveness_score():
    asset = ContentAsset(
        id=uuid4(),
        type=ContentType.COLD_EMAIL,
        title="Test Email",
        body="Hello world",
        target_icp="SaaS",
    )

    metrics = ContentPerformanceMetrics(
        asset_id=asset.id,
        impressions=100,
        opens=50,
        clicks=20,
        replies=10,
        conversions=5,
    )

    result = score_content_asset(asset, metrics)

    assert result.score > 0
    assert result.grade in {"poor", "fair", "good", "excellent"}
    assert result.open_rate == 0.5