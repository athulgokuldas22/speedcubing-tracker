import os

import pymssql
from flask import Flask, jsonify
from flask_cors import CORS

from app import db
from app.routes import bp
from app.schema import SCHEMA
from app.service import NotFoundError, ValidationError


def create_app():
    app = Flask(__name__)
    db.init_db(SCHEMA)
    app.teardown_appcontext(db.close_db)
    app.register_blueprint(bp)

    # The UI is served from another address, so the browser needs CORS to call this service.
    origins = [o for o in os.environ.get("CORS_ORIGINS", "").split(",") if o]
    if origins:
        CORS(app, origins=origins)

    @app.errorhandler(ValidationError)
    def bad_request(err):
        return jsonify(error=str(err)), 400

    @app.errorhandler(NotFoundError)
    def not_found(err):
        return jsonify(error=str(err)), 404

    @app.get("/health")
    def health():
        """Reports only this service's own state: can it reach its own database?"""
        try:
            conn = db.connect()
            conn.cursor().execute("SELECT 1")
            conn.close()
        except pymssql.Error:
            return jsonify(status="unavailable"), 503
        return jsonify(status="ok")

    return app
