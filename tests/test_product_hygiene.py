import uuid
from pathlib import Path
from types import SimpleNamespace

import backend.api.users as users_api
from backend.models.user import UserRole
from backend.schemas.user_schema import ActiveUpdateSchema, RoleUpdateSchema


class _UserService:
    def __init__(self, db):
        self.db = db

    async def set_role(self, user_id, role):
        return SimpleNamespace(id=user_id, role=role, is_active=True)

    async def set_active(self, user_id, is_active):
        return SimpleNamespace(id=user_id, role=UserRole.USER, is_active=is_active)


class _Socket:
    def __init__(self):
        self.closed_with = None

    async def close(self, code):
        self.closed_with = code


def _run_immediate(coroutine):
    """Drive coroutines whose test doubles complete without yielding to an event loop."""
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    raise AssertionError("test coroutine unexpectedly required an event loop")


def test_role_change_does_not_read_active_update_fields(monkeypatch):
    """Catches role updates accidentally reading fields owned by another schema."""
    monkeypatch.setattr(users_api, "UserService", _UserService)
    target_id = uuid.uuid4()
    admin = SimpleNamespace(id=uuid.uuid4(), role=UserRole.ADMIN)

    result = _run_immediate(
        users_api.change_role(
            target_id,
            RoleUpdateSchema(role=UserRole.ADMIN),
            db=object(),
            current_user=admin,
        )
    )

    assert result.id == target_id
    assert result.role is UserRole.ADMIN


def test_admin_deactivation_closes_existing_user_sockets(monkeypatch):
    """Catches deactivation leaving an authenticated WebSocket usable."""
    monkeypatch.setattr(users_api, "UserService", _UserService)
    target_id = uuid.uuid4()
    admin = SimpleNamespace(id=uuid.uuid4(), role=UserRole.ADMIN)
    socket = _Socket()
    users_api.manager.active_connections[target_id] = {socket}

    try:
        result = _run_immediate(
            users_api.set_active(
                target_id,
                ActiveUpdateSchema(is_active=False),
                db=object(),
                current_user=admin,
            )
        )
    finally:
        users_api.manager.active_connections.pop(target_id, None)

    assert result.is_active is False
    assert socket.closed_with == 4403


def test_ci_targets_python_312_with_one_test_run_and_a_non_placeholder_secret():
    """Catches CI using the wrong runtime, duplicate suites, or a weak JWT key."""
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    test_commands = [
        line.strip()
        for line in workflow.splitlines()
        if line.strip() in {"run: pytest", "run: python -m pytest"}
    ]
    secret_line = next(
        line for line in workflow.splitlines() if line.strip().startswith("SECRET_KEY:")
    )
    secret = secret_line.split(":", 1)[1].strip().strip("'\"")

    assert 'python-version: "3.12"' in workflow
    assert test_commands == ["run: python -m pytest"]
    assert len(secret) >= 32
    assert "change-me" not in secret.lower()


def test_course_response_uses_pydantic_v2_config():
    """Catches restoring the deprecated nested Pydantic Config class."""
    from backend.schemas.course_schema import CourseResponse

    assert CourseResponse.model_config["from_attributes"] is True
    assert not hasattr(CourseResponse, "Config")
