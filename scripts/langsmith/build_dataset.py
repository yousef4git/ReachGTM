from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_dataset_records(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []

    for asset in assets:
        if asset.get("status") != "approved":
            continue

        records.append(
            {
                "inputs": {
                    "content_type": asset.get("content_type", ""),
                    "prompt": asset.get("prompt", ""),
                },
                "outputs": {
                    "title": asset.get("title", ""),
                    "body": asset.get("body", ""),
                },
                "metadata": {
                    "asset_id": asset.get("id"),
                    "strategy_id": asset.get("strategy_id"),
                    "source": "approved_content_asset",
                },
            }
        )

    return records


def write_dataset_file(input_path: Path, output_path: Path) -> int:
    assets = json.loads(input_path.read_text(encoding="utf-8"))
    records = build_dataset_records(assets)
    output_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return len(records)