"""
MONITORING UTILS — RM Bakes
Lightweight health check endpoint for external uptime monitors
(e.g. Uptimeroot hitting https://rm-bakes.com/health).

Intentionally has ZERO dependencies on the rest of the app:
no database, no models, no sessions, no business logic. This means
it keeps responding 200 even if Postgres/DATABASE_URL is down, so
it only ever reflects whether the web process itself is alive.
"""

from flask import Blueprint, Response

monitoring_bp = Blueprint("monitoring", __name__)


@monitoring_bp.route("/health")
def health():
    return Response("RM BAKES OK", status=200, mimetype="text/plain")
