from backend.app.services.content_service import generate_content_assets
from shared.schemas import ContentGenerateRequest, ContentType


def test_generate_content_assets():
    request = ContentGenerateRequest(
        content_types=[
            ContentType.COLD_EMAIL,
            ContentType.LINKEDIN_POST,
        ],
        count_per_type=2,
    )

    assets = generate_content_assets(request)

    assert len(assets) == 4

    assert assets[0].type == ContentType.COLD_EMAIL
    assert assets[1].type == ContentType.COLD_EMAIL
    assert assets[2].type == ContentType.LINKEDIN_POST
    assert assets[3].type == ContentType.LINKEDIN_POST

    assert assets[0].title
    assert assets[0].body