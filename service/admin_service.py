"""用户权限与日志服务。"""

from __future__ import annotations

from core.db import transaction
from dao import auth_dao, log_dao
from service.auth_service import UserSession
from service.order_service import PermissionError


class AdminService:
    """后台管理服务。"""

    def __init__(self, user_session: UserSession) -> None:
        self.user_session = user_session

    def list_users(self) -> list[dict]:
        """查询用户。"""
        self._require_admin()
        return auth_dao.list_users()

    def update_permissions(self, user_id: int, permissions: dict) -> None:
        """更新用户权限。"""
        self._require_admin()
        target = auth_dao.get_user_by_id(user_id)
        if target is None:
            raise PermissionError("目标用户不存在或已停用。")
        if not self.user_session.can_manage_user(target):
            raise PermissionError("只有管理员可以分配用户权限。")

        normalized_permissions = permissions.copy()
        if target.get("role") == "admin":
            normalized_permissions.update(
                {
                    "can_view": True,
                    "can_insert": True,
                    "can_update": True,
                    "can_delete": True,
                }
            )
        if target.get("role") == "staff":
            normalized_permissions["can_update"] = False
            normalized_permissions["can_delete"] = False

        with transaction() as db_cursor:
            auth_dao.update_permissions(
                user_id,
                normalized_permissions["can_view"],
                normalized_permissions["can_insert"],
                normalized_permissions["can_update"],
                normalized_permissions["can_delete"],
                db_cursor=db_cursor,
            )
            auth_dao.log_action(
                self.user_session.username,
                "users",
                "UPDATE",
                f"更新用户 {user_id} 权限",
                db_cursor=db_cursor,
            )

    def list_logs(self) -> list[dict]:
        """查询审计日志。"""
        if not self.user_session.is_manager:
            raise PermissionError("只有经理或管理员可以查看审计日志。")
        return log_dao.list_logs()

    def _require_manager(self) -> None:
        """检查经理权限。"""
        if not self.user_session.is_manager:
            raise PermissionError("只有经理或管理员可以执行该操作。")

    def _require_admin(self) -> None:
        """检查管理员权限。"""
        if not self.user_session.is_admin:
            raise PermissionError("只有管理员可以执行该操作。")
