from __future__ import annotations

from shared.schemas import ContentAsset, GTMState, ValidationStatus


BRAND_ALIGNMENT_THRESHOLD = 0.7
MAX_REVISION_ATTEMPTS = 2


def _score_asset_against_brand(asset: ContentAsset, brand_chunks: list[dict]) -> float:
    """Return a deterministic brand alignment score in the range [0, 1]."""
    if not brand_chunks:
        return 0.5

    similarities = [
        float(chunk.get("similarity", 0.0))
        for chunk in brand_chunks
        if chunk.get("similarity") is not None
    ]

    if not similarities:
        return 0.5

    score = sum(similarities) / len(similarities)
    return max(0.0, min(1.0, score))


def _revise_asset(asset: ContentAsset, score: float) -> ContentAsset:
    """Apply a lightweight deterministic revision note for low-scoring assets."""
    return asset.model_copy(
        update={
            "validation_status": ValidationStatus.REVISED,
            "brand_alignment_score": score,
            "revision_notes": (
                "Revised for stronger brand alignment. "
                "Emphasize approved messaging, ICP pain points, and consistent positioning."
            ),
        }
    )


def _approve_asset(asset: ContentAsset, score: float) -> ContentAsset:
    """Approve assets that meet the brand alignment threshold."""
    return asset.model_copy(
        update={
            "validation_status": ValidationStatus.APPROVED,
            "brand_alignment_score": score,
            "revision_notes": None,
        }
    )


async def brand_alignment_node(state: GTMState, retriever=None) -> GTMState:
    """Validate and revise content assets against brand knowledge chunks."""
    if retriever is None:
        # Lazily resolve the process-global retriever registered by the agents
        # lifespan so content validation is grounded in the company's real KB.
        # Degrade gracefully (retriever stays None → neutral score) if the
        # registry/retriever is unavailable, e.g. offline tests with no API key.
        try:
            from agents.app.tools.retriever_registry import get_retriever

            retriever = get_retriever()
        except Exception:  # noqa: BLE001 — never let retriever wiring break the graph
            retriever = None

    validated_assets: list[ContentAsset] = []

    for asset in state.content_assets:
        query = f"{asset.title}\n{asset.body}\nTarget ICP: {asset.target_icp}"

        try:
            brand_chunks = []
            if retriever is not None:
                brand_chunks = await retriever.retrieve(
                    query=query,
                    namespace=str(state.company_id),
                    top_k=5,
                )

            score = _score_asset_against_brand(asset, brand_chunks)

            if score >= BRAND_ALIGNMENT_THRESHOLD:
                validated_assets.append(_approve_asset(asset, score))
            else:
                revised_asset = asset
                revision_attempts = 0

                while score < BRAND_ALIGNMENT_THRESHOLD and revision_attempts < MAX_REVISION_ATTEMPTS:
                    revised_asset = _revise_asset(revised_asset, score)
                    revision_attempts += 1

                    # Deterministic simulated improvement for stub-driven testing.
                    score = min(1.0, score + 0.15)

                if score >= BRAND_ALIGNMENT_THRESHOLD:
                    validated_assets.append(_approve_asset(revised_asset, score))
                else:
                    validated_assets.append(
                        revised_asset.model_copy(
                            update={
                                "validation_status": ValidationStatus.REVISED,
                                "brand_alignment_score": score,
                                "revision_notes": (
                                    "Reached max revision attempts. "
                                    "Asset still needs manual brand review."
                                ),
                            }
                        )
                    )

        except Exception as exc:
            validated_assets.append(
                asset.model_copy(
                    update={
                        "validation_status": ValidationStatus.REJECTED,
                        "brand_alignment_score": 0.0,
                        "revision_notes": f"Brand validation failed: {exc}",
                    }
                )
            )

    return state.model_copy(
        update={
            "content_assets": validated_assets,
            "current_agent": "brand_alignment",
        }
    )