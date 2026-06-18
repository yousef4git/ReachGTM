"""A/B variant generation for content assets (Epic 4 — Phase 2).

Expands a content asset into 3 split-test variants (A/B/C), each leading with a
distinct angle (direct value / social proof / curiosity) so they can be tested
against one another. Deterministic — no LLM call — so it works regardless of LLM
availability and is fully testable.

Variants are returned as separate ContentAssets (new ids), with the variant
label in the title (e.g. "[Variant B] ..."). Keeping the label in the title
keeps this schema-light — no change to shared.schemas.ContentAsset (which would
require a four-owner review).
"""
from __future__ import annotations

from shared.schemas import ContentAsset

NUM_VARIANTS = 3

# Distinct split-test angles applied to each base asset, in A -> B -> C order.
VARIANT_STRATEGIES: dict[str, dict[str, str]] = {
    "A": {"angle": "Direct value", "hook": "Straight to it:", "cta": "Worth a quick look?"},
    "B": {
        "angle": "Social proof",
        "hook": "Teams like yours are already seeing results.",
        "cta": "Want to see how?",
    },
    "C": {"angle": "Curiosity", "hook": "Quick question —", "cta": "Curious if this resonates?"},
}


def _variant_body(label: str, base_body: str) -> str:
    strat = VARIANT_STRATEGIES[label]
    return f"{strat['hook']}\n\n{base_body}\n\n{strat['cta']}"


def make_variants(asset: ContentAsset) -> list[ContentAsset]:
    """Return 3 A/B/C split-test variants of `asset` as new ContentAssets."""
    return [
        ContentAsset(
            type=asset.type,
            title=f"[Variant {label}] {asset.title}",
            body=_variant_body(label, asset.body),
            target_icp=asset.target_icp,
        )
        for label in VARIANT_STRATEGIES
    ]


def expand_assets_to_variants(assets: list[ContentAsset]) -> list[ContentAsset]:
    """Flatten each asset into its 3 variants (3 x len(assets) total)."""
    return [variant for asset in assets for variant in make_variants(asset)]
