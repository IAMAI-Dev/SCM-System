"""供应商业务服务。"""

from __future__ import annotations

from dataclasses import dataclass

from dao import supplier_dao


@dataclass(frozen=True)
class SupplierKpi:
    """供应商分析指标。"""

    label: str
    value: str
    hint: str
    status: str


class SupplierService:
    """供应商服务。"""

    def __init__(self, user_session=None) -> None:
        self.user_session = user_session

    def list_suppliers(self) -> list[dict]:
        """查询供应商表现。"""
        self._require_view()
        return supplier_dao.list_suppliers()

    def load_analysis(self) -> dict:
        """加载供应商分析页面数据。"""
        self._require_view()
        suppliers = supplier_dao.list_suppliers(limit=80)
        summary = supplier_dao.get_supplier_summary()
        countries = supplier_dao.get_country_distribution()
        trend = supplier_dao.get_purchase_trend(limit=12)
        ranked = self._rank_suppliers(suppliers)
        return {
            "kpis": self._build_kpis(summary, ranked, trend),
            "bar_data": ranked[:5],
            "country_data": countries,
            "trend_data": trend,
            "ranking": ranked[:20],
        }

    def _build_kpis(
        self,
        summary: dict,
        ranked: list[dict],
        trend: list[dict],
    ) -> list[SupplierKpi]:
        """构建供应商 KPI。"""
        active_count = int(summary.get("active_supplier_count") or 0)
        premium_count = sum(1 for row in ranked if row["score"] >= 92)
        total_parts = int(summary.get("total_part_count") or 0)
        avg_purchase = self._average_purchase_amount(trend)
        return [
            SupplierKpi(
                "活跃供应商",
                f"{active_count:,}",
                "按供应关系统计",
                "normal",
            ),
            SupplierKpi(
                "优质供应商",
                f"{premium_count:,}",
                "评分不低于 92",
                "success",
            ),
            SupplierKpi(
                "供应零件总数",
                f"{total_parts:,}",
                "来自 PartSupp",
                "normal",
            ),
            SupplierKpi(
                "月均采购额",
                self._format_money(avg_purchase),
                "基于 Lineitem",
                "warning",
            ),
        ]

    def _rank_suppliers(self, suppliers: list[dict]) -> list[dict]:
        """生成供应商排名与评分。"""
        max_parts = max(
            (int(row["part_count"] or 0) for row in suppliers),
            default=1,
        )
        ranked = []
        for row in suppliers:
            part_count = int(row["part_count"] or 0)
            avg_cost = float(row["avg_supply_cost"] or 0)
            score = self._score_supplier(part_count, avg_cost, max_parts)
            ranked.append(
                {
                    **row,
                    "score": score,
                    "trend": self._stable_trend(row["supplier_key"]),
                    "avg_supply_cost": avg_cost,
                    "part_count": part_count,
                }
            )
        return sorted(ranked, key=lambda item: item["score"], reverse=True)

    def _score_supplier(
        self,
        part_count: int,
        avg_cost: float,
        max_parts: int,
    ) -> int:
        """按供应规模和成本稳定性生成展示评分。"""
        scale_score = 70 + round(24 * part_count / max(max_parts, 1))
        cost_penalty = 0
        if avg_cost > 5000:
            cost_penalty = 4
        elif avg_cost > 2500:
            cost_penalty = 2
        return max(78, min(99, scale_score - cost_penalty))

    def _stable_trend(self, supplier_key: int) -> str:
        """生成稳定的趋势展示值。"""
        trend_value = int(supplier_key) % 9 - 2
        if trend_value > 0:
            return f"+{trend_value}%"
        return f"{trend_value}%"

    def _average_purchase_amount(self, trend: list[dict]) -> float:
        """计算月均采购额。"""
        values = [float(row["purchase_amount"] or 0) for row in trend]
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _format_money(self, amount: float) -> str:
        """格式化金额。"""
        if amount >= 1000000:
            return f"¥{amount / 1000000:.1f}M"
        if amount >= 10000:
            return f"¥{amount / 10000:.1f}万"
        return f"¥{amount:,.0f}"

    def _require_view(self) -> None:
        """检查采购模块查询权限。"""
        if self.user_session is None:
            return
        if not self.user_session.can_operate_module("suppliers", "view"):
            from service.order_service import PermissionError

            raise PermissionError("当前用户没有供应商模块查询权限。")
