import os

from core.schemas.database_api import RoutesSchemas
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

app = FastAPI()

# Configure database URL dynamically based on environment
DB_USER = os.getenv("DB_USER")  # Default for local dev
DB_PASSWORD = os.getenv("DB_PASSWORD")  # Default for local dev
DB_NAME = os.getenv("DB_NAME", "local_db")  # Default for local dev
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")

if CLOUD_SQL_CONNECTION_NAME:
    # Cloud SQL connection
    DATABASE_URL = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}"
        f"?host=/cloudsql/{CLOUD_SQL_CONNECTION_NAME}"
    )
else:
    # Local PostgreSQL connection
    LOCAL_HOST = os.getenv("DB_HOST", "127.0.0.1")  # Default localhost
    LOCAL_PORT = os.getenv("DB_PORT", "5432")  # Default port for PostgreSQL
    DATABASE_URL = (
        f"postgresql+psycopg2://"
        f"{DB_USER}:{DB_PASSWORD}@{LOCAL_HOST}:{LOCAL_PORT}/{DB_NAME}"
    )


# Initialize Database
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# SQLAlchemy model
class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    gcp_project_id = Column(String, unique=True, index=True)


# Create tables if they do not exist
Base.metadata.create_all(bind=engine)


# Dependency to get the database session
def get_database():
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


@app.post("/projects/")
def create_project(
    project: RoutesSchemas.ProjectCreate, database: Session = Depends(get_database)
):
    db_project = (
        database.query(Project)
        .filter(Project.gcp_project_id == project.gcp_project_id)
        .first()
    )
    if db_project:
        raise HTTPException(status_code=400, detail="Project already exists")

    new_project = Project(gcp_project_id=project.gcp_project_id)
    database.add(new_project)
    database.commit()
    database.refresh(new_project)

    return {"id": new_project.id, "gcp_project_id": new_project.gcp_project_id}


if __name__ == "__main__":
    # used for debugging purposes only
    import uvicorn  # isort:skip

    uvicorn.run(app, host="0.0.0.0", port=8000)
