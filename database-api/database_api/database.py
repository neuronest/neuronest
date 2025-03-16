from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from database_api.environment_variables import (
    CLOUD_SQL_CONNECTION_NAME,
    DB_NAME,
    DB_PASSWORD,
    DB_USER,
    LOCAL_HOST,
    LOCAL_PORT,
)

# SQLAlchemy database URL from configuration
if CLOUD_SQL_CONNECTION_NAME:
    # Cloud SQL connection
    DATABASE_URL = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}"
        f"?host=/cloudsql/{CLOUD_SQL_CONNECTION_NAME}"
    )
else:
    # Local PostgreSQL connection
    DATABASE_URL = (
        f"postgresql+psycopg2://"
        f"{DB_USER}:{DB_PASSWORD}@{LOCAL_HOST}:{LOCAL_PORT}/{DB_NAME}"
    )


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
