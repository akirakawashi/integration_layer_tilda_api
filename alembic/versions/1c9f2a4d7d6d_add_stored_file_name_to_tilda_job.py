"""add stored_file_name to tilda_job

Revision ID: 1c9f2a4d7d6d
Revises: a10d74bec293
Create Date: 2026-04-23 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1c9f2a4d7d6d"
down_revision: Union[str, None] = "a10d74bec293"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tilda_job",
        sa.Column(
            "stored_file_name",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        ),
        schema="integration_tilda",
    )


def downgrade() -> None:
    op.drop_column(
        "tilda_job",
        "stored_file_name",
        schema="integration_tilda",
    )
