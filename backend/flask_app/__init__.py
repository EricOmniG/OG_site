# ============================================================
#  flask_app/__init__.py
#  Flask application factory
#
#  Responsibility split:
#    Flask  → webhooks, auth callbacks, billing, admin, waitlist,
#             user CRUD, sharing, file uploads, health
#    FastAPI → /v1/chat, /v1/search, /v1/reason  (streaming inference)
#
#  Both apps sit behind API Gateway. Routes are split at the path level:
#    /v1/chat*, /v1/search*, /v1/reason*  → FastAPI Lambda
#    everything else                       → Flask Lambda
#
#  Local dev: run flask_app and fastapi app on different ports.
#    Flask:   PORT=5000  python -m flask_app.run
#    FastAPI: PORT=8000  uvicorn app.main:app --reload
# ============================================================

from flask import Flask
from flask_cors import CORS

from flask_app.config import FlaskConfig
from flask_app.extensions import db, migrate, redis_client
from flask_app.middleware.auth import clerk_required
from flask_app.middleware.rate_limit import init_rate_limiter

from flask_app.routes.auth import auth_bp
from flask_app.routes.users import users_bp
from flask_app.routes.conversations import conversations_bp
from flask_app.routes.sharing import sharing_bp
from flask_app.routes.billing import billing_bp
from flask_app.routes.apikeys import apikeys_bp
from flask_app.routes.waitlist import waitlist_bp
from flask_app.routes.uploads import uploads_bp
from flask_app.routes.admin import admin_bp
from flask_app.routes.health import health_bp


def create_app(config: FlaskConfig = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # ── Config ──────────────────────────────────────────────
    if config is None:
        config = FlaskConfig.from_env()
    app.config.from_object(config)

    # ── CORS ────────────────────────────────────────────────
    CORS(
        app,
        origins=config.CORS_ORIGINS,
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-API-Key"],
        methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    )

    # ── Extensions ──────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    redis_client.init_app(app)
    init_rate_limiter(app)

    # ── Blueprints ──────────────────────────────────────────
    app.register_blueprint(health_bp)                        # /health
    app.register_blueprint(auth_bp,          url_prefix="/v1/auth")
    app.register_blueprint(users_bp,         url_prefix="/v1/users")
    app.register_blueprint(conversations_bp, url_prefix="/v1/conversations")
    app.register_blueprint(sharing_bp,       url_prefix="/v1/share")
    app.register_blueprint(billing_bp,       url_prefix="/v1/billing")
    app.register_blueprint(apikeys_bp,       url_prefix="/v1/apikeys")
    app.register_blueprint(waitlist_bp,      url_prefix="/v1/waitlist")
    app.register_blueprint(uploads_bp,       url_prefix="/v1/uploads")
    app.register_blueprint(admin_bp,         url_prefix="/v1/admin")

    # ── Error handlers ──────────────────────────────────────
    register_error_handlers(app)

    return app


def register_error_handlers(app: Flask):
    from flask import jsonify

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"detail": str(e), "status": 400}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"detail": "Authentication required", "status": 401}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"detail": "Insufficient permissions", "status": 403}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"detail": "Not found", "status": 404}), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"detail": "Rate limit exceeded", "status": 429}), 429

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled server error")
        return jsonify({"detail": "Internal server error", "status": 500}), 500
