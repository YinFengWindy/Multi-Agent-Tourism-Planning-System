from app.portal_home import build_portal_home_payload


def test_build_portal_home_payload_returns_gallery_and_modes() -> None:
    payload = build_portal_home_payload()

    assert payload.headline
    assert len(payload.mode_cards) >= 4
    assert len(payload.gallery_cards) >= 4
    assert payload.mode_cards[0].title == '旅行灵感'
