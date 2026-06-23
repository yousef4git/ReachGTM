from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UsageMetric:
    name: str
    value: int
    limit: int | None = None


def calculate_usage_summary(
    strategies: int = 0,
    content_assets: int = 0,
    knowledge_documents: int = 0,
    api_calls: int = 0,
) -> dict:
    metrics = [
        UsageMetric("strategies", strategies),
        UsageMetric("content_assets", content_assets),
        UsageMetric("knowledge_documents", knowledge_documents),
        UsageMetric("api_calls", api_calls),
    ]

    return {
        "metrics": [
            {
                "name": metric.name,
                "value": metric.value,
                "limit": metric.limit,
            }
            for metric in metrics
        ],
        "total_usage": sum(metric.value for metric in metrics),
    }