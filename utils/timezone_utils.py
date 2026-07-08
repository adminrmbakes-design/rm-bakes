from datetime import timedelta

# =========================================
# IST (Asia/Kolkata) — fixed UTC+5:30, no DST
# =========================================
# Every datetime is stored in UTC throughout the app (datetime.utcnow()).
# This module is the single place that converts a stored UTC value to
# IST for DISPLAY — the database itself never changes.

IST_OFFSET = timedelta(hours=5, minutes=30)


def to_ist(utc_dt):
    """Convert a naive UTC datetime to a naive IST datetime for display.
    Returns None unchanged so callers can still guard with {% if %}."""

    if not utc_dt:
        return None

    return utc_dt + IST_OFFSET


def format_ist(utc_dt, fmt="%d %b %Y, %I:%M %p"):
    """Convert + format in one call — used as the `ist` Jinja filter.
    Returns an empty string for None so it can be dropped straight into
    a template expression without an extra guard."""

    ist_dt = to_ist(utc_dt)

    if not ist_dt:
        return ""

    return ist_dt.strftime(fmt)
