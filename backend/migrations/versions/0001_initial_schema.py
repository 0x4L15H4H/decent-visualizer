"""Create the initial SQLite schema."""

from alembic import op

from app.schema import SCHEMA

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    for statement in SCHEMA.split(";"):
        if statement.strip() and not statement.lstrip().upper().startswith("PRAGMA"):
            op.execute(statement)


def downgrade() -> None:
    for table in (
        "shots",
        "beans",
        "entity_aliases",
        "canonical_entities",
        "settings",
        "sessions",
        "users",
    ):
        op.drop_table(table)
