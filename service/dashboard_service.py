"""仪表盘业务服务。"""

from __future__ import annotations

from dataclasses import dataclass

from core.db import DatabaseError
from dao import dashboard_dao


@dataclass(frozen=True)
class KpiItem:
    """仪表盘指标项。"""

    title: str
    value: str
    trend: str
    status: str


class DashboardService:
    """仪表盘服务。"""

    def load_dashboard(self) -> tuple[list[KpiItem], list[dict], list[dict]]:
        """加载仪表盘 KPI、趋势和低库存摘要。"""
        try:
            kpis = dashboard_dao.get_dashboard_kpis()
        except Exception:
            try:
                kpis = dashboard_dao.get_dashboard_kpis_fallback()
            except Exception as exc:
                raise DatabaseError("仪表盘 KPI 查询失败。") from exc

        try:
            sales_history = dashboard_dao.get_sales_history()
            low_stock = dashboard_dao.get_low_stock_snapshot()
        except Exception as exc:
            raise DatabaseError("仪表盘明细查询失败。") from exc

        return self._format_kpis(kpis), sales_history, low_stock

    def _format_kpis(self, kpis: dict) -> list[KpiItem]:
        """格式化 KPI 展示数据。"""
        revenue = float(kpis.get("total_revenue") or 0)
        return [
            KpiItem(
                "总订单数",
                f"{int(kpis.get('total_orders') or 0):,}",
                "来自 Orders",
                "normal",
            ),
            KpiItem(
                "累计销售额",
                f"¥{revenue:,.2f}",
                "来自存储过程",
                "success",
            ),
            KpiItem(
                "客户数量",
                f"{int(kpis.get('total_customers') or 0):,}",
                "覆盖 Customer",
                "normal",
            ),
            KpiItem(
                "缺货预警",
                f"{int(kpis.get('low_stock_count') or 0):,}",
                "库存低于 100",
                "warning",
            ),
        ]
