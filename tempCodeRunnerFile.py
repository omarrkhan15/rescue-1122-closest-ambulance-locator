def clean_location(raw):
    if not isinstance(raw, str):
        return raw
    parts = [p.strip() for p in raw.split(",")]
    # Always keep just Road, City, Province, Country — drop everything after
    cleaned = ", ".join(parts[:4])
    return cleaned