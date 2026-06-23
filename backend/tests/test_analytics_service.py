from backend.app.services.analytics_service import calculate_strategy_performance


def test_calculate_strategy_performance():
    result = calculate_strategy_performance(
        sent=100,
        opened=40,
        replied=10,
    )

    assert result["sent"] == 100
    assert result["opened"] == 40
    assert result["replied"] == 10
    assert result["open_rate"] == 0.4
    assert result["reply_rate"] == 0.1