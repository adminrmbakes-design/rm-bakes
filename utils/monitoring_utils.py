"""
MONITORING UTILS — RM Bakes
Lightweight health check endpoint for external uptime monitors
(e.g. Uptimeroot hitting https://rm-bakes.com/health) — this is what
keeps the free-tier service from spinning down when idle.

Intentionally has no dependency on the database/session/business
logic: it only renders a static template, so it keeps responding
200 even if Postgres/DATABASE_URL is down.
"""

from flask import Blueprint, render_template

monitoring_bp = Blueprint("monitoring", __name__)


@monitoring_bp.route("/health")
def health():
    return render_template("health.html"), 200
