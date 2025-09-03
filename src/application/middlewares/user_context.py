from contextvars import ContextVar
from uuid import UUID

current_user_id_var: ContextVar[UUID | None] = ContextVar("current_user_id")
current_user_var: ContextVar[dict] = ContextVar("current_user")

current_user_perm: ContextVar[set[str]] = ContextVar("current_user_permissions")


def get_current_user_id() -> UUID | None:
    return current_user_id_var.get(None)


def get_current_user() -> dict:
    return current_user_var.get({})


def is_admin() -> bool:
    userinfo = current_user_var.get({})
    if userinfo.get("role") == "Admin":
        return True
    return False
