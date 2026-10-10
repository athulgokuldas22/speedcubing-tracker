from flask import Flask, jsonify, render_template

import config
import db
import solves
import stats
from solves.routes import bp as solves_bp
from solves.service import NotFoundError, ValidationError
from stats.routes import bp as stats_bp


def create_app():
    app = Flask(__name__)
    db.init_db(schemas=[solves.SCHEMA, stats.SCHEMA])
    app.teardown_appcontext(db.close_db)
    app.register_blueprint(solves_bp)
    app.register_blueprint(stats_bp)

    @app.errorhandler(ValidationError)
    def bad_request(err):
        return jsonify(error=str(err)), 400

    @app.errorhandler(NotFoundError)
    def not_found(err):
        return jsonify(error=str(err)), 404

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    create_app().run(host=config.HOST, port=config.PORT)
