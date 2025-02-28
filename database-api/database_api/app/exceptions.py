class DatabaseStoppedError(Exception):
    """Raised when the database is stopped."""


class DatabaseStoppingError(Exception):
    """Raised when the database is stopping."""


class DatabaseStartingError(Exception):
    """Raised when the database is starting."""

    def __init__(self, instance_name=None):
        if instance_name:
            message = (
                f"Cloud SQL instance '{instance_name}' "
                f"is currently starting. Please wait until it becomes available."
            )
        else:
            message = (
                "The Cloud SQL instance is currently starting. "
                "Please wait until it becomes available."
            )

        super().__init__(message)
