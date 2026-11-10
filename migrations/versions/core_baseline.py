"""clean core baseline

Revision ID: core_baseline
Revises:
Create Date: 2026-11-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "core_baseline"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = sa.Enum("USER", "ADMIN", name="userrole")
    chat_type = sa.Enum("PRIVATE", "GROUP", name="chattype")
    level_choices = sa.Enum("A1", "A2", "B1", "B2", "C1", "C2", name="levelchoices")
    friend_status = sa.Enum(
        "PENDING", "ACCEPTED", "REJECTED", name="friendrequeststatus"
    )
    exercise_type = sa.Enum(
        "CHOICE", "TRANSLATE", "FILL_GAP", "MATCH", name="exercisetype"
    )
    timestamp = sa.DateTime(timezone=True)

    op.create_table(
        "achievement",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("xp_reward", sa.Integer(), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=True),
    )
    op.create_table(
        "daily_challenge",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("xp_reward", sa.Integer(), nullable=False),
        sa.Column("challenge_date", sa.Date(), nullable=False, unique=True),
    )
    op.create_table(
        "language",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "user",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("username", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", timestamp, nullable=False),
        sa.Column("avatar", sa.String(), nullable=True),
    )
    op.create_table(
        "course",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("language_id", sa.Integer(), sa.ForeignKey("language.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("level", level_choices, nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
    )
    op.create_index("ix_course_language_id", "course", ["language_id"])
    op.create_table(
        "chat",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("creator_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("type", chat_type, nullable=False),
        sa.Column("language_id", sa.Integer(), sa.ForeignKey("language.id"), nullable=True),
        sa.Column("created_at", timestamp, nullable=False),
    )
    op.create_index("ix_chat_creator_id", "chat", ["creator_id"])
    op.create_table(
        "refresh_token",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("users_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("created_date", timestamp, nullable=False),
    )
    op.create_index("ix_refresh_token_users_id", "refresh_token", ["users_id"])
    op.create_table(
        "friend_request",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sender_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("receiver_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("status", friend_status, nullable=False),
        sa.Column("created_at", timestamp, nullable=False),
    )
    op.create_index("ix_friend_request_receiver_id", "friend_request", ["receiver_id"])
    op.create_table(
        "friendship",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("friend_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("created_at", timestamp, nullable=False),
    )
    op.create_index("ix_friendship_user_id", "friendship", ["user_id"])
    op.create_table(
        "leaderboard",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("xp", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("updated_at", timestamp, nullable=False),
    )
    op.create_index("ix_leaderboard_user_id", "leaderboard", ["user_id"], unique=True)
    op.create_table(
        "streak",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("current_streak", sa.Integer(), nullable=False),
        sa.Column("last_activity", sa.Date(), nullable=True),
        sa.UniqueConstraint("user_id", name="uq_streak_user"),
    )
    op.create_table(
        "user_achievement",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("achievement_id", sa.Integer(), sa.ForeignKey("achievement.id"), nullable=False),
        sa.Column("earned_at", timestamp, nullable=False),
        sa.UniqueConstraint(
            "user_id", "achievement_id", name="uq_user_achievement_user_achievement"
        ),
    )
    op.create_table(
        "xp_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("xp", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("created_at", timestamp, nullable=False),
    )
    op.create_index("ix_xp_history_user_created", "xp_history", ["user_id", "created_at"])
    op.create_table(
        "user_language",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("language_id", sa.Integer(), sa.ForeignKey("language.id"), nullable=False),
        sa.Column("level", level_choices, nullable=True),
        sa.Column("placement_completed", sa.Boolean(), nullable=False),
        sa.UniqueConstraint(
            "user_id", "language_id", name="uq_user_language_user_language"
        ),
    )
    op.create_table(
        "hearts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("hearts", sa.Integer(), nullable=False),
        sa.Column("last_heart_lost_at", timestamp, nullable=True),
        sa.UniqueConstraint("user_id", name="uq_hearts_user"),
    )
    op.create_table(
        "lesson",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("course.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("is_locked", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_lesson_course_id", "lesson", ["course_id"])
    op.create_table(
        "chat_member",
        sa.Column("chat_id", sa.UUID(), sa.ForeignKey("chat.id"), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), primary_key=True),
        sa.Column("joined_at", timestamp, nullable=False),
    )
    op.create_index("ix_chat_member_user_id", "chat_member", ["user_id"])
    op.create_table(
        "message",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("chat_id", sa.UUID(), sa.ForeignKey("chat.id"), nullable=False),
        sa.Column("sender_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", timestamp, nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_message_chat_created", "message", ["chat_id", "created_at", "id"])
    op.create_table(
        "level_test",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("language_id", sa.Integer(), sa.ForeignKey("language.id"), nullable=False),
        sa.Column("is_placement", sa.Boolean(), nullable=False),
        sa.Column("target_level", level_choices, nullable=True),
        sa.Column("passing_score", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", timestamp, nullable=False),
    )
    op.create_table(
        "user_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lesson.id"), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("completed_at", timestamp, nullable=True),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_user_progress_user_lesson"),
    )
    op.create_table(
        "exercise",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lesson.id"), nullable=False),
        sa.Column("type", exercise_type, nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("correct_answer", sa.JSON(), nullable=False),
    )
    op.create_index("ix_exercise_lesson_id", "exercise", ["lesson_id"])
    op.create_table(
        "level_test_question",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("test_id", sa.UUID(), sa.ForeignKey("level_test.id"), nullable=False),
        sa.Column("level", level_choices, nullable=False),
        sa.Column("type", exercise_type, nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("correct_answer", sa.JSON(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
    )
    op.create_table(
        "level_test_attempt",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("test_id", sa.UUID(), sa.ForeignKey("level_test.id"), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("language_id", sa.Integer(), sa.ForeignKey("language.id"), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("result_level", level_choices, nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("completed_at", timestamp, nullable=True),
        sa.Column("created_at", timestamp, nullable=False),
    )
    op.create_table(
        "user_exercise_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercise.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.UniqueConstraint(
            "user_id", "exercise_id", name="uq_user_exercise_progress_user_exercise"
        ),
    )
    op.create_table(
        "exercise_submission",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercise.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response", sa.JSON(), nullable=True),
        sa.Column("created_at", timestamp, nullable=False),
        sa.UniqueConstraint(
            "user_id", "idempotency_key", name="uq_exercise_submission_user_key"
        ),
    )
    op.create_index("ix_exercise_submission_user_id", "exercise_submission", ["user_id"])
    op.create_index(
        "ix_exercise_submission_exercise_id", "exercise_submission", ["exercise_id"]
    )


def downgrade() -> None:
    for table_name in (
        "exercise_submission",
        "user_exercise_progress",
        "level_test_attempt",
        "level_test_question",
        "exercise",
        "user_progress",
        "level_test",
        "message",
        "chat_member",
        "lesson",
        "hearts",
        "user_language",
        "xp_history",
        "user_achievement",
        "streak",
        "leaderboard",
        "friendship",
        "friend_request",
        "refresh_token",
        "chat",
        "course",
        "user",
        "language",
        "daily_challenge",
        "achievement",
    ):
        op.drop_table(table_name)

    for enum_name in (
        "exercisetype",
        "friendrequeststatus",
        "levelchoices",
        "chattype",
        "userrole",
    ):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
