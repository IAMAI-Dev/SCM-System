# service/performance_service.py
from dao import performance_dao
from service.order_service import PermissionError


class PerformanceService:
    def __init__(self, user_session):
        self.user_session = user_session

    def load_stats(self):
        """加载性能统计数据。"""
        # 仅管理员可以查看
        if not self.user_session.can_operate_module("admin", "view"):
            raise PermissionError("仅管理员可查看性能数据")

        return {
            "tables": performance_dao.get_table_stats(),
            "unused_indexes": performance_dao.get_unused_indexes()
        }