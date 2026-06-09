"""用户认证与权限业务服务。"""

from __future__ import annotations

from dataclasses import dataclass

from dao import auth_dao


@dataclass(frozen=True)
class UserSession:
    """当前登录用户会话。"""

    user_id: int
    username: str
    display_name: str
    department: str
    role: str
    can_view: bool
    can_insert: bool
    can_update: bool
    can_delete: bool

    @property
    def is_manager(self) -> bool:
        """判断是否为经理角色。"""
        return self.role == "manager"

    def has_permission(self, action: str) -> bool:
        """判断用户是否具备指定动作权限。"""
        permission_map = {
            "view": self.can_view,
            "insert": self.can_insert,
            "update": self.can_update,
            "delete": self.can_delete,
        }
        return permission_map.get(action, False)


class AuthService:
    """认证服务。"""

    def login(self, username: str, password: str) -> UserSession | None:
        """登录并返回用户会话。"""
        username = username.strip()
        if not username or not password:
            return None

        user = auth_dao.find_user_by_credentials(username, password)
        if not user:
            return None

        session = UserSession(
            user_id=user["user_id"],
            username=user["username"],
            display_name=user["display_name"],
            department=user["department"],
            role=user["role"],
            can_view=bool(user["can_view"]),
            can_insert=bool(user["can_insert"]),
            can_update=bool(user["can_update"]),
            can_delete=bool(user["can_delete"]),
        )
        auth_dao.log_action(
            session.username,
            "auth",
            "LOGIN",
            f"用户 {session.display_name} 登录系统",
        )
        return session
