from database_api.database import SessionLocal


def get_database():
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
