import logging
import subprocess


def upgrade_head():
    """
    Executes Alembic migrations to upgrade the database schema to the latest revision.
    Logs the migration status without returning any values.
    """

    try:
        logging.info("Starting Alembic database migration...")

        result = subprocess.run(
            ["alembic", "upgrade", "head"],
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
                f"Alembic migration failed.  Details:\n{result.stderr.strip()}"
            )

    except subprocess.SubprocessError as subprocess_error:
        logging.critical(f"Subprocess execution error: {str(subprocess_error)}")
    except Exception as subprocess_error:
        logging.critical(
            f"Unexpected error during Alembic migration: {str(subprocess_error)}"
        )
        raise subprocess_error
