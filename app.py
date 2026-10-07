from flask import Flask

import config
import db
import solves


def create_app():
    app = Flask(__name__)
    db.init_db(schemas=[solves.SCHEMA])

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    create_app().run(host=config.HOST, port=config.PORT)
