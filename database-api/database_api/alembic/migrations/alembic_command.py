import logging
import subprocess


def upgrade_head():
    """
    Executes Alembic migrations to upgrade the database schema to the latest revision.
    Logs the migration status and raises appropriate errors in case of failure.
    """
    try:
        logging.info("Starting Alembic database migration...")

        result = subprocess.run(
            [
                "alembic",
                "-c",
                "database_api/alembic/alembic.ini",
                "upgrade",
                "head",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,  # Allow capturing errors without raising exceptions
        )

        if result.returncode == 0:
            logging.info("Alembic migrations applied successfully.")
            logging.info(f"Migrations Output:\n{result.stdout.strip()}")
        else:
            raise RuntimeError(
                f"Alembic migration failed. Details:\n"
                f"STDOUT:\n{result.stdout.strip()}\n"
                f"STDERR:\n{result.stderr.strip()}"
            )

    except subprocess.SubprocessError as subprocess_error:
        raise RuntimeError(
            f"Subprocess execution error: {str(subprocess_error)}"
        ) from subprocess_error

    except Exception as unexpected_error:
        raise RuntimeError(
            f"Unexpected error during Alembic migration: {str(unexpected_error)}"
        ) from unexpected_error
