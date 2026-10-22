# Swarm Lab, Copyright (c) 2026 Joe El Khoury. All rights reserved.
# Licensed under the Swarm Lab License (source-available). See LICENSE and NOTICE.md.
# https://github.com/joeaelkhoury/SwarmLab
"""Whitespace normalization; intentionally regressed for the exercise."""


def slug(text):
    """Lowercase words joined by one hyphen; blank input yields empty text."""
    return text.strip().lower().replace(" ", "-")
