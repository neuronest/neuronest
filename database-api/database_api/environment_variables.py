import os
from urllib.parse import quote

DB_USER = os.getenv("DB_USER")  # Default for local dev
# URL-encode the password to handle special characters like '@', '$', and '#'
# URL encoding ensures that these characters are interpreted
# correctly in the connection string
DB_PASSWORD = quote(os.environ["DB_PASSWORD"])  # Default for local dev
DB_NAME = os.getenv("DB_NAME", "local_db")  # Default for local dev
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")
LOCAL_HOST = os.getenv("DB_HOST", "127.0.0.1")  # Default localhost
LOCAL_PORT = os.getenv("DB_PORT", "5432")  # Default port for PostgreSQL
