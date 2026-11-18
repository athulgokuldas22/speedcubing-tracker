"""openapi.yaml must list exactly the routes the Flask app has, with the same methods."""
import re
from pathlib import Path

import yaml

from app import main

SPEC = Path(__file__).resolve().parent.parent / "openapi.yaml"


def test_openapi_documents_exactly_the_routes_of_the_app(monkeypatch):
    monkeypatch.setattr(main, "run_migrations", lambda: None)
    app = main.create_app()
    routes = set()
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        path = re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", rule.rule)  # <int:id> -> {id}
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            routes.add((method.lower(), path))

    spec = yaml.safe_load(SPEC.read_text())
    documented = {
        (method, path)
        for path, item in spec["paths"].items()
        for method in item
        if method != "parameters"
    }
    assert documented == routes
