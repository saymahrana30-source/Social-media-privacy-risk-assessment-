"""app.py - Flask application factory.

Run:  python backend/app.py      (serves API + frontend on http://127.0.0.1:5000)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # lets `python backend/app.py` import `backend.*`

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from backend.config import Config
from backend.models import db as dbm
from backend.routes.api import api
from backend.utils.rate_limit import RateLimiter
from backend.utils.validation import ValidationError

SECURITY_HEADERS = {
    "Content-Security-Policy": ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
                                "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
    "Cache-Control": "no-store",
}


def create_app(overrides=None):
    config = Config()
    app = Flask(__name__, static_folder=config.FRONTEND_DIR, static_url_path="", template_folder="templates")
    app.config.from_object(config)
    if overrides:
        app.config.update(overrides)
    dbm.init_db(app.config["DATABASE_PATH"])
    app.teardown_appcontext(dbm.close_db)
    limiter = RateLimiter()
    app.extensions["limiter"] = limiter
    app.register_blueprint(api)

    @app.before_request
    def rate_limit():
        if not request.path.startswith("/api/"):
            return None
        ip = request.remote_addr or "unknown"
        if not limiter.allow(f"all:{ip}", app.config["RATE_LIMIT_PER_MINUTE"]):
            return jsonify({"error": "Too many requests. Please slow down."}), 429
        if request.method in ("POST", "DELETE") and not limiter.allow(f"write:{ip}", app.config["RATE_LIMIT_POST_PER_MINUTE"]):
            return jsonify({"error": "Too many requests. Please slow down."}), 429
        return None

    @app.after_request
    def add_security_headers(resp):
        for k, v in SECURITY_HEADERS.items():
            resp.headers.setdefault(k, v)
        return resp

    @app.errorhandler(ValidationError)
    def handle_validation(err):
        return jsonify({"error": "Validation failed", "details": err.problems}), 400

    @app.errorhandler(HTTPException)
    def handle_http(err):
        return jsonify({"error": err.name}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):  # never leak stack traces to the client
        app.logger.exception("Unhandled error")
        return jsonify({"error": "Internal server error"}), 500

    @app.get("/")
    def home():
        return send_from_directory(app.static_folder, "index.html")

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
