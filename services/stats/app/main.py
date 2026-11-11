import os

import pymssql
from flask import Flask, jsonify
from flask_cors import CORS

from app import db
from app.routes import bp
from app.schema import SCHEMA
from app.solves_client import NotFoundError, SolvesUnavailable


def create_app():
    app = Flask(__name__)
    db.init_db(SCHEMA)
    app.teardown_appcontext(db.close_db)
    app.register_blueprint(bp)

    # The UI is served from another address, so the browser needs CORS to call this service.
    origins = [o for o in os.environ.get("CORS_ORIGINS", "").split(",") if o]
    if origins:
        CORS(app, origins=origins)

    @app.errorhandler(NotFoundError)
    def not_found(err):
        return jsonify(error=str(err)), 404

    @app.errorhandler(SolvesUnavailable)
    def solves_down(err):
        return jsonify(error=str(err)), 503

    @app.get("/health")
    def health():
        """Reports only this service's own state. A solves outage does not make stats unhealthy."""
        try:
            conn = db.connect()
            conn.cursor().execute("SELECT 1")
            conn.close()
        except pymssql.Error:
            return jsonify(status="unavailable"), 503
        return jsonify(status="ok")

    return app
