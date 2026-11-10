def normalize_page(
    q: str | None, limit: int, offset: int
) -> tuple[str | None, int, int]:
    if not 1 <= limit <= 100 or offset < 0:
        raise ValueError("INVALID_PAGINATION")
    normalized = q.strip() if q is not None else None
    if normalized == "":
        normalized = None
    if normalized is not None and len(normalized) > 100:
        raise ValueError("SEARCH_QUERY_TOO_LONG")
    return normalized, limit, offset


def literal_search_pattern(query: str) -> str:
    escaped = query.replace("\\","\\\\").replace("%","\\%").replace("_","\\_")
    return f"%{escaped}%"
