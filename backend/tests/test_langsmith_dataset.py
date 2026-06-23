from scripts.langsmith.build_dataset import build_dataset_records


def test_build_dataset_records_only_approved_assets():
    assets = [
        {
            "id": "1",
            "strategy_id": "s1",
            "status": "approved",
            "content_type": "linkedin_post",
            "prompt": "Write a post",
            "title": "Title",
            "body": "Body",
        },
        {
            "id": "2",
            "strategy_id": "s2",
            "status": "draft",
            "content_type": "email",
            "prompt": "Write email",
            "title": "Draft",
            "body": "Draft body",
        },
    ]

    records = build_dataset_records(assets)

    assert len(records) == 1
    assert records[0]["metadata"]["asset_id"] == "1"