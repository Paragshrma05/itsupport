import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'instance', 'itsupport.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB max upload
