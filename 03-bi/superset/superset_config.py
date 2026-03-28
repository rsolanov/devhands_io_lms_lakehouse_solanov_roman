import os

SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "your-secret-key-here")

SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SUPERSET_DATABASE_URI",
    "postgresql+psycopg2://superset:superset@bi-postgres:5432/superset",
)

WTF_CSRF_ENABLED = True

ROW_LIMIT = 5000
SUPERSET_WEBSERVER_PORT = 8088

FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
}