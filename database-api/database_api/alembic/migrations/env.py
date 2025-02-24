import os
import re
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from database_api.database import DATABASE_URL

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None  # pylint: disable=invalid-name

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


# pylint: disable=redefined-outer-name,unused-argument
def process_revision_directives(context, revision, directives):
    """
    Customize revision filenames to use a numerical index.

    Note: Alembic is responsible for calling this function with the 'revision'
    argument, so the unused 'revision' parameter is part of the required
    function signature and cannot be removed.
    """
    migration_dir = os.path.join(context.script.dir, "versions")
    existing_migrations = os.listdir(migration_dir)

    # Find the highest numerical index in existing migration files
    migration_numbers = (
        [
            int(re.match(r"(\d+)_", f).group(1))
            for f in existing_migrations
            if re.match(r"(\d+)_", f)
        ]
        if existing_migrations
        else [0]
    )

    next_number = max(migration_numbers, default=0) + 1
    directives[0].rev_id = f"{next_number:04d}_{directives[0].rev_id}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(DATABASE_URL)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
