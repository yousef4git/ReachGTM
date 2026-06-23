from __future__ import annotations

import uuid

import asyncpg

from shared.schemas import ContentAsset, ContentGenerateRequest, ContentType


def _title_for_content_type(content_type: ContentType, index: int) -> str:
    labels = {
        ContentType.COLD_EMAIL: "Cold Email",
        ContentType.LINKEDIN_POST: "LinkedIn Post",
        ContentType.BLOG_OUTLINE: "Blog Outline",
        ContentType.AD_COPY: "Ad Copy",
    }
    return f"{labels[content_type]} #{index}"


def _body_for_content_type(content_type: ContentType, index: int) -> str:
    bodies = {
        ContentType.COLD_EMAIL: (
            "Hi {{first_name}},\n\n"
            "I noticed your team is working on growth. ReachGTM can help turn market research "
            "into clear GTM campaigns faster. Would you be open to a quick conversation this week?"
        ),
        ContentType.LINKEDIN_POST: (
            "Great go-to-market teams do not just create more content. They connect research, "
            "positioning, and customer pain points into one repeatable motion."
        ),
        ContentType.BLOG_OUTLINE: (
            "1. Define the ICP\n"
            "2. Identify the strongest pain points\n"
            "3. Map channels to buying intent\n"
            "4. Turn insights into measurable campaigns"
        ),
        ContentType.AD_COPY: (
            "Build GTM campaigns from research in minutes. Align messaging, channels, and content "
            "with ReachGTM."
        ),
    }
    return f"{bodies[content_type]}\n\nVariant: {index}"


def generate_content_assets(body: ContentGenerateRequest) -> list[ContentAsset]:
    """Generate deterministic content assets for the requested content types."""
    count_per_type = max(1, body.count_per_type)
    assets: list[ContentAsset] = []

    for content_type in body.content_types:
        for index in range(1, count_per_type + 1):
            assets.append(
                ContentAsset(
                    type=content_type,
                    title=_title_for_content_type(content_type, index),
                    body=_body_for_content_type(content_type, index),
                    target_icp="GTM leaders and growth teams",
                )
            )

    return assets


# ── DB persistence ──────────────────────────────────────────────────────────


def _as_uuid(value) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


async def persist_content_assets(
    conn: asyncpg.Connection,
    company_id,
    strategy_id,
    assets: list[dict],
) -> list[str]:
    """Insert content assets (as plain dicts off the agent bundle) and return new ids."""
    company_uuid = _as_uuid(company_id)
    strategy_uuid = _as_uuid(strategy_id) if strategy_id else None
    new_ids: list[str] = []

    for asset in assets:
        score = asset.get("brand_alignment_score")
        new_id = await conn.fetchval(
            """INSERT INTO content_assets
               (company_id, strategy_id, content_type, title, body,
                validation_status, brand_alignment_score)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               RETURNING id""",
            company_uuid,
            strategy_uuid,
            str(asset.get("type") or "cold_email"),
            str(asset.get("title") or "Untitled"),
            str(asset.get("body") or ""),
            str(asset.get("validation_status") or "pending"),
            float(score) if score is not None else None,
        )
        new_ids.append(str(new_id))

    return new_ids


async def list_content(conn: asyncpg.Connection, company_id) -> list[dict]:
    """Return the company's persisted content assets, newest first."""
    rows = await conn.fetch(
        """SELECT id, content_type, title, body, validation_status,
                  brand_alignment_score, strategy_id, created_at
           FROM content_assets
           WHERE company_id = $1
           ORDER BY created_at DESC""",
        _as_uuid(company_id),
    )
    return [
        {
            "id": str(r["id"]),
            "type": r["content_type"],
            "title": r["title"],
            "body": r["body"],
            "target_icp": "",
            "validation_status": r["validation_status"],
            "brand_alignment_score": r["brand_alignment_score"],
            "strategy_id": str(r["strategy_id"]) if r["strategy_id"] else None,
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]
