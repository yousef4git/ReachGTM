from __future__ import annotations

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
