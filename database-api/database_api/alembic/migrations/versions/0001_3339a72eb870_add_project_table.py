# pylint: disable=invalid-name
"""Add project table

Revision ID: 0001_3339a72eb870
Revises:
Create Date: 2025-01-16 16:48:59.661448

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_3339a72eb870"  # pylint: disable=invalid-name
down_revision: Union[str, None] = None  # pylint: disable=invalid-name
branch_labels: Union[str, Sequence[str], None] = None  # pylint: disable=invalid-name
depends_on: Union[str, Sequence[str], None] = None  # pylint: disable=invalid-name


def upgrade():
    # Create the `projects` table
    op.execute(
        """
        CREATE TABLE projects (
            id SERIAL PRIMARY KEY,
            gcp_project_id VARCHAR NOT NULL UNIQUE
        );
    """
    )

    # Create btree indexes
    op.execute(
        """
        CREATE INDEX ix_projects_id ON projects USING btree (id);
    """
    )
    op.execute(
        """
        CREATE INDEX ix_projects_gcp_project_id ON projects USING btree (gcp_project_id);
    """
    )


def downgrade():
    # Drop indexes
    op.execute(
        """
        DROP INDEX IF EXISTS ix_projects_gcp_project_id;
    """
    )
    op.execute(
        """
        DROP INDEX IF EXISTS ix_projects_id;
    """
    )

    # Drop the `projects` table
    op.execute(
        """
        DROP TABLE IF EXISTS projects;
    """
    )
