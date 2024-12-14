from sqlalchemy import Column, Integer, String

from database_api.database import Base


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    gcp_project_id = Column(String, unique=True, index=True)
