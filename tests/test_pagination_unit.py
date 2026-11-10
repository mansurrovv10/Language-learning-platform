import pytest


def test_pagination_normalizes_query_and_rejects_invalid_bounds():
    """Catches unbounded search input and invalid database offsets/limits."""
    from backend.pagination import normalize_page

    assert normalize_page("  HeLLo  ", 25, 2) == ("HeLLo", 25, 2)
    assert normalize_page("   ", 25, 0) == (None, 25, 0)
    with pytest.raises(ValueError, match="SEARCH_QUERY_TOO_LONG"):
        normalize_page("x" * 101, 25, 0)
    with pytest.raises(ValueError, match="INVALID_PAGINATION"):
        normalize_page(None, 0, 0)
    with pytest.raises(ValueError, match="INVALID_PAGINATION"):
        normalize_page(None, 101, -1)


def test_paged_routes_are_added_without_removing_legacy_lists():
    """Catches route conflicts or a compatibility-breaking list replacement."""
    from main import duolingo

    paths = duolingo.openapi()["paths"]
    for paged in (
        "/languages/paged",
        "/courses/paged",
        "/lessons/paged",
        "/exercises/paged",
        "/users/paged",
        "/chats/{chat_id}/messages/paged",
    ):
        assert "get" in paths[paged]
    for legacy in ("/languages", "/courses", "/lessons", "/exercises", "/users/"):
        assert "get" in paths[legacy]
