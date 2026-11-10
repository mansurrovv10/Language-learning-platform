"""add product completion tables

Revision ID: product_completion
Revises: core_baseline
Create Date: 2026-11-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "product_completion"
down_revision: Union[str, Sequence[str], None] = "core_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    timestamp = sa.DateTime(timezone=True)

    op.create_table(
        "review_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercise.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("box", sa.Integer(), nullable=False),
        sa.Column("due_at", timestamp, nullable=False),
        sa.Column("last_result", sa.Boolean(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("correct_streak", sa.Integer(), nullable=False),
        sa.Column("created_at", timestamp, nullable=False),
        sa.Column("updated_at", timestamp, nullable=False),
        sa.UniqueConstraint(
            "user_id", "exercise_id", name="uq_review_item_user_exercise"
        ),
        sa.CheckConstraint("box >= 0 AND box <= 5", name="ck_review_item_box"),
        sa.CheckConstraint(
            "attempts >= 0 AND correct_streak >= 0",
            name="ck_review_item_attempts",
        ),
    )
    op.create_index(
        "ix_review_item_user_due", "review_item", ["user_id", "due_at", "id"]
    )

    op.create_table(
        "practice_session",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("created_at", timestamp, nullable=False),
        sa.Column("expires_at", timestamp, nullable=False),
        sa.Column("completed_at", timestamp, nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("heart_awarded", sa.Boolean(), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=True),
        sa.Column("response", sa.JSON(), nullable=True),
        sa.CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 100)",
            name="ck_practice_session_score",
        ),
        sa.CheckConstraint(
            "expires_at > created_at", name="ck_practice_session_expiry"
        ),
        sa.CheckConstraint(
            "completed_at IS NULL OR "
            "(score IS NOT NULL AND passed IS NOT NULL "
            "AND request_hash IS NOT NULL AND response IS NOT NULL)",
            name="ck_practice_session_completion",
        ),
        sa.CheckConstraint(
            "NOT heart_awarded OR (completed_at IS NOT NULL AND passed)",
            name="ck_practice_session_heart_award",
        ),
    )
    op.create_index(
        "ix_practice_session_user_created",
        "practice_session",
        ["user_id", "created_at", "id"],
    )

    op.create_table(
        "practice_session_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id",
            sa.UUID(),
            sa.ForeignKey("practice_session.id"),
            nullable=False,
        ),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercise.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("exercise_type", sa.String(32), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("correct_answer", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "session_id", "position", name="uq_practice_item_session_position"
        ),
        sa.UniqueConstraint(
            "session_id", "exercise_id", name="uq_practice_item_session_exercise"
        ),
        sa.CheckConstraint("position >= 0", name="ck_practice_item_position"),
    )
    op.create_index(
        "ix_practice_session_item_session_id",
        "practice_session_item",
        ["session_id"],
    )

    op.create_table(
        "user_daily_goal",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("target_xp", sa.Integer(), nullable=False),
        sa.Column("updated_at", timestamp, nullable=False),
        sa.UniqueConstraint("user_id", name="uq_user_daily_goal_user"),
        sa.CheckConstraint(
            "target_xp >= 10 AND target_xp <= 200",
            name="ck_user_daily_goal_target",
        ),
    )

    op.create_table(
        "ai_usage",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("request_type", sa.String(32), nullable=False),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("successful", sa.Boolean(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("created_at", timestamp, nullable=False),
        sa.CheckConstraint(
            "input_tokens IS NULL OR input_tokens >= 0",
            name="ck_ai_usage_input_tokens",
        ),
        sa.CheckConstraint(
            "output_tokens IS NULL OR output_tokens >= 0",
            name="ck_ai_usage_output_tokens",
        ),
    )
    op.create_index(
        "ix_ai_usage_user_created", "ai_usage", ["user_id", "created_at", "id"]
    )


def downgrade() -> None:
    op.drop_table("ai_usage")
    op.drop_table("user_daily_goal")
    op.drop_table("practice_session_item")
    op.drop_table("practice_session")
    op.drop_table("review_item")
