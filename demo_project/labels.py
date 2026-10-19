"""Whitespace normalization; intentionally regressed for the exercise."""


def slug(text):
    """Lowercase words joined by one hyphen; blank input yields empty text."""
    return text.strip().lower().replace(" ", "-")
