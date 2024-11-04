import os

from core.schemas.database_api import RoutesSchemas
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

app = FastAPI()

# Configure database URL from environment variables

# Makes sense to create a user dedicated to the cloud run
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")

DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@/{DB_NAME}"
    f"?host=/cloudsql/{INSTANCE_CONNECTION_NAME}"
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
    # new_project.id might still be None here without refresh if the id
    # is auto-generated
    database.refresh(new_project)  # Ensures new_project.id now has the generated ID

    return {"id": new_project.id, "gcp_project_id": new_project.gcp_project_id}
