"""Human-readable console formatting."""


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024**2:
        return f"{size / 1024:.1f} KB"
    return f"{size / 1024**2:.1f} MB"


def format_elapsed(milliseconds: float) -> str:
    return f"{milliseconds:.0f} ms"
