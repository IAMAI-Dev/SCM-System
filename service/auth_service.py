"""用户认证与权限业务服务。"""

from __future__ import annotations

from dataclasses import dataclass

from dao import auth_dao


MODULE_DEPARTMENTS = {
    "orders": "sales",
    "inventory": "procurement",
    "replenishment": "procurement",
    "suppliers": "procurement",
    "customers": "customer",
}

DEPARTMENT_LABELS = {
    "admin": "总管理",
    "procurement": "采购部",
    "sales": "销售部",
    "customer": "客户管理部",
}


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
    def is_admin(self) -> bool:
        """判断是否为总管理员。"""
        return self.role == "admin"

    @property
    def is_manager(self) -> bool:
        """判断是否为经理或总管理员。"""
        return self.role in {"admin", "manager"}

    @property
    def department_label(self) -> str:
        """返回部门中文名称。"""
        return DEPARTMENT_LABELS.get(self.department, self.department)

    def has_permission(self, action: str) -> bool:
        """判断用户是否具备全局动作权限。"""
        if self.is_admin:
            return True
        permission_map = {
            "view": self.can_view,
            "insert": self.can_insert,
            "update": self.can_update,
            "delete": self.can_delete,
        }
        return permission_map.get(action, False)

    def can_access_module(self, module_key: str) -> bool:
        """判断用户是否可以进入指定模块。"""
        if module_key in {"dashboard"}:
            return True
        if self.is_admin:
            return True
        if module_key == "manager":
            return self.is_manager
        if module_key == "users":
            return False
        if module_key == "logs":
            return self.role == "manager"

        module_department = MODULE_DEPARTMENTS.get(module_key)
        if module_department is None:
            return False
        if self.role == "manager":
            return True
        return self.department == module_department

    def can_operate_module(self, module_key: str, action: str) -> bool:
        """判断用户是否能在模块内执行指定动作。"""
        if self.is_admin:
            return True
        if action == "view":
            return self.can_access_module(module_key) and self.can_view

        module_department = MODULE_DEPARTMENTS.get(module_key)
        if module_department != self.department:
            return False
        if self.role == "manager":
            return self.has_permission(action)
        if self.role == "staff":
            return action in {"insert"} and self.has_permission(action)
        return False

    def can_manage_user(self, target: dict) -> bool:
        """判断是否可分配目标用户权限。"""
        return self.is_admin


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
