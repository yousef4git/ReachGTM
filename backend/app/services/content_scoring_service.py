"""Content effectiveness scoring utilities.

Scores generated content assets using lightweight performance metrics such as
opens, clicks, replies, conversions, and impressions. The score is deterministic
and does not require database access, so it is easy to test and reuse from API
or analytics jobs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from shared.schemas import ContentAsset


@dataclass(frozen=True)
class ContentPerformanceMetrics:
    asset_id: UUID
    impressions: int = 0
    opens: int = 0
    clicks: int = 0
    replies: int = 0
    conversions: int = 0


@dataclass(frozen=True)
class ContentEffectivenessScore:
    asset_id: UUID
    title: str
    score: float
    open_rate: float
    click_rate: float
    reply_rate: float
    conversion_rate: float
    grade: str


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _grade(score: float) -> str:
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "poor"


def score_content_asset(
    asset: ContentAsset,
    metrics: ContentPerformanceMetrics,
) -> ContentEffectivenessScore:
    """Calculate a weighted effectiveness score for one content asset."""
    open_rate = _rate(metrics.opens, metrics.impressions)
    click_rate = _rate(metrics.clicks, metrics.impressions)
    reply_rate = _rate(metrics.replies, metrics.impressions)
    conversion_rate = _rate(metrics.conversions, metrics.impressions)

    weighted_score = (
        open_rate * 20
        + click_rate * 25
        + reply_rate * 30
        + conversion_rate * 25
    ) * 100

    score = round(min(weighted_score, 100.0), 2)

    return ContentEffectivenessScore(
        asset_id=asset.id,
        title=asset.title,
        score=score,
        open_rate=open_rate,
        click_rate=click_rate,
        reply_rate=reply_rate,
        conversion_rate=conversion_rate,
        grade=_grade(score),
    )


def score_content_assets(
    assets: Iterable[ContentAsset],
    metrics: Iterable[ContentPerformanceMetrics],
) -> list[ContentEffectivenessScore]:
    """Score many content assets and sort from strongest to weakest."""
    metrics_by_asset_id = {item.asset_id: item for item in metrics}

    scores = [
        score_content_asset(
            asset,
            metrics_by_asset_id.get(asset.id, ContentPerformanceMetrics(asset_id=asset.id)),
        )
        for asset in assets
    ]

    return sorted(scores, key=lambda item: item.score, reverse=True)