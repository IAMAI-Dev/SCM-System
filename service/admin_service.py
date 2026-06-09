"""用户权限与日志服务。"""

from __future__ import annotations

from dao import auth_dao, log_dao
from service.auth_service import UserSession
from service.order_service import PermissionError


class AdminService:
    """后台管理服务。"""

    def __init__(self, user_session: UserSession) -> None:
        self.user_session = user_session

    def list_users(self) -> list[dict]:
        """查询用户。"""
        self._require_manager()
        return auth_dao.list_users()

    def update_permissions(self, user_id: int, permissions: dict) -> None:
        """更新用户权限。"""
        self._require_manager()
        auth_dao.update_permissions(
            user_id,
            permissions["can_view"],
            permissions["can_insert"],
            permissions["can_update"],
            permissions["can_delete"],
        )
        auth_dao.log_action(
            self.user_session.username,
            "users",
            "UPDATE",
            f"更新用户 {user_id} 权限",
        )

    def list_logs(self) -> list[dict]:
        """查询审计日志。"""
        return log_dao.list_logs()

    def _require_manager(self) -> None:
        """检查经理权限。"""
        if not self.user_session.is_manager:
            raise PermissionError("只有经理角色可以执行该操作。")
