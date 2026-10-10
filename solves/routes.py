"""HTTP layer for the solves domain. Rules live in service.py."""
from flask import Blueprint, jsonify, request

import db

from . import service
from .scramble import generate_scramble

bp = Blueprint("solves", __name__, url_prefix="/api")


def _json_body():
    return request.get_json(silent=True) or {}


@bp.get("/scramble")
def new_scramble():
    return jsonify(scramble=generate_scramble())


@bp.get("/sessions")
def list_sessions():
    return jsonify(service.list_sessions(db.get_db()))


@bp.post("/sessions")
def create_session():
    session = service.create_session(db.get_db(), _json_body().get("name"))
    return jsonify(session), 201


@bp.get("/sessions/<int:session_id>/solves")
def list_solves(session_id):
    return jsonify(service.list_solves(db.get_db(), session_id))


@bp.post("/sessions/<int:session_id>/solves")
def add_solve(session_id):
    data = _json_body()
    solve = service.add_solve(
        db.get_db(),
        session_id,
        data.get("time_ms"),
        data.get("scramble"),
        data.get("penalty", "OK"),
    )
    return jsonify(solve), 201


@bp.patch("/solves/<int:solve_id>")
def set_penalty(solve_id):
    solve = service.set_penalty(db.get_db(), solve_id, _json_body().get("penalty"))
    return jsonify(solve)


@bp.delete("/solves/<int:solve_id>")
def delete_solve(solve_id):
    service.delete_solve(db.get_db(), solve_id)
    return "", 204
