"""Add Person and move vaccinations to person

Revision ID: 719b0471f5a9
Revises: 25e07a4398b2
Create Date: 2026-02-25 12:46:40.655795

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '719b0471f5a9'
down_revision = '25e07a4398b2'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Create person table
    op.create_table(
        "person",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("first_name", sa.String(length=80), nullable=False),
        sa.Column("last_name", sa.String(length=80), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("relationship", sa.String(length=20), nullable=False, server_default="child"),
    )

    # 2) Add person_id to vaccination (nullable first)
    with op.batch_alter_table("vaccination") as batch_op:
        batch_op.add_column(sa.Column("person_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_vaccination_person",
            "person",
            ["person_id"],
            ["id"],
        )

    # 3) Backfill: create a default "self" person per user, move vaccinations
    conn = op.get_bind()

    users = conn.execute(sa.text("SELECT id, first_name, last_name FROM user")).fetchall()

    for (user_id, first_name, last_name) in users:
        fn = first_name or "Jag"
        ln = last_name or ""

        conn.execute(
            sa.text(
                """
                INSERT INTO person (user_id, first_name, last_name, relationship)
                VALUES (:user_id, :first_name, :last_name, 'self')
                """
            ),
            {"user_id": user_id, "first_name": fn, "last_name": ln},
        )

        person_id = conn.execute(sa.text("SELECT last_insert_rowid()")).scalar()

        conn.execute(
            sa.text(
                """
                UPDATE vaccination
                SET person_id = :person_id
                WHERE user_id = :user_id
                """
            ),
            {"person_id": person_id, "user_id": user_id},
        )

    # 4) Make person_id non-null and drop user_id (SQLite-safe via batch)
    with op.batch_alter_table("vaccination") as batch_op:
        batch_op.alter_column("person_id", existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column("user_id")


def downgrade():
    # Add user_id back (nullable first)
    with op.batch_alter_table("vaccination") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_vaccination_user", "user", ["user_id"], ["id"])

    conn = op.get_bind()

    # Backfill user_id from person.user_id
    conn.execute(
        sa.text(
            """
            UPDATE vaccination
            SET user_id = (
                SELECT user_id FROM person WHERE person.id = vaccination.person_id
            )
            """
        )
    )

    # Drop person_id FK + column
    with op.batch_alter_table("vaccination") as batch_op:
        batch_op.drop_constraint("fk_vaccination_person", type_="foreignkey")
        batch_op.drop_column("person_id")
        batch_op.alter_column("user_id", existing_type=sa.Integer(), nullable=False)

    op.drop_table("person")
