from backend.app.services.usage_service import calculate_usage_summary


def test_calculate_usage_summary():
    summary = calculate_usage_summary(
        strategies=5,
        content_assets=10,
        knowledge_documents=3,
        api_calls=20,
    )

    assert summary["total_usage"] == 38
    assert len(summary["metrics"]) == 4