"""HTTP layer for the stats domain."""
from flask import Blueprint, jsonify

import db

from . import service

bp = Blueprint("stats", __name__, url_prefix="/api")


@bp.get("/sessions/<int:session_id>/stats")
def session_stats(session_id):
    """Recompute and store personal bests, then return the summary.

    `new_pbs` lists the kinds that improved since the last call.
    """
    conn = db.get_db()
    refreshed = service.refresh_pbs(conn, session_id)
    summary = service.get_summary(conn, session_id)
    summary["new_pbs"] = refreshed["new"]
    return jsonify(summary)
