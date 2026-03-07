# ============================================================
#  flask_app/extensions.py
#  Shared extension instances — initialised in create_app()
# ============================================================

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_redis import FlaskRedis

db = SQLAlchemy()
migrate = Migrate()
redis_client = FlaskRedis()
