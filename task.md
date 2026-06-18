# 供应链管理系统修复与优化任务清单

本清单整理自 `analysis_results.md` 中的 18 个潜在问题及用户反馈，用于跟踪后续的开发和调试进度。

## 任务拆解与 TODO

### 1. 数据库初始化与数据完整性修复
- [ ] 修改 `core/db.py`，将新增的补货订单 SQL 脚本 `"06.sql"` 追加到 `initialize_database_objects` 的执行列表中，解决干净环境下启动时崩溃的 Bug (问题 1)
- [ ] 编写或修改数据补全脚本（如更新 `sql/05_seed.sql`），为 `customer.Acctbal`、`lineitem.Shipdate` 以及 `lineitem.Receiptdate` 等关键字段填充合理的演示数据，解决经营分析和供应商分析页面中折线图与散点图因数据为 `NULL` 导致的大面积空白问题 (问题 16)

### 2. 状态更新优化与汉化
- [ ] 修改 `ui/pages/orders_page.py` 中的“更新状态”功能，将原先字符下拉框 `["O", "F", "P"]` 优化为中文对应的 `["进行中 (O)", "已完成 (F)", "挂起 (P)"]`，并在传递给后端前提取其状态码首字母 (问题 1)
- [ ] 优化 `ui/pages/orders_page.py` 的明细查看逻辑，当订单明细查询为空时（如查询超出数据库范围的模拟订单明细），增加友好文字提示“该模拟订单暂无明细数据”，避免展现空的明细表 (问题 15)

### 3. 系统 Emoji 表情全面清洗
- [ ] 清理以下页面中包含的全部 emoji 表情前缀，确保系统交互界面简洁庄严 (问题 18)：
  - [ ] `ui/pages/manager_dashboard_page.py` (标题 label)
  - [ ] `ui/pages/customers_page.py` (导出按钮)
  - [ ] `ui/pages/dashboard_page.py` (导出按钮)
  - [ ] `ui/pages/inventory_page.py` (补货与采购按钮)
  - [ ] `ui/pages/logs_page.py` (导出按钮)
  - [ ] `ui/pages/orders_page.py` (导出按钮)
  - [ ] `ui/pages/performance_page.py` (指标与索引列表标签)
  - [ ] `ui/pages/replenishment_page.py` (标题 label)
  - [ ] `ui/pages/suppliers_page.py` (导出按钮)
  - [ ] `ui/pages/users_page.py` (导出按钮)

### 4. 性能监控模块说明与纠错
- [ ] 将 `ui/pages/performance_page.py` 中的表格列键值由 `"rows"` 修复为 `"row_count"`，解决行数列数据展现空白的运行时 Bug (问题 2)
- [ ] 在 `ui/pages/performance_page.py` 顶部添加中文小字说明，指导非专业技术人员理解该页面的 DBA 运维监控用途 (问题 17)
- [ ] 优化 `dao/performance_dao.py`，将只读统计查询中的 `with transaction()` 事务控制重构为 `with cursor()` 普通只读游标连接，避免性能浪费 (问题 9)

### 5. 其它界面与业务 Bug 修复
- [ ] 修复供应商分析中一键导出 Excel 时评分列为空白的缺陷（在 `suppliers_page.py` 渲染评分进度条前先通过 `_set_item` 写入底层数据模型数据）(问题 4)
- [ ] 修复 `service/inventory_service.py` 事务传参问题，确保采购订单的审计日志记录与订单写入使用同一个数据库游标 `db_cursor`，使其处于同一事务内 (问题 3)
- [ ] 修复 `ui/pages/manager_dashboard_page.py` 在刷新失败时无限追加重复的红色错误文本标签的缺陷，改为合理地更新单一状态文本或 QMessageBox 报错 (问题 12)
- [ ] 修复供应商分析图表（柱状图）中供应商名称因字数过长未截断导致的文字重叠重影，对其调用 `_short_name` 进行截断 (问题 14)

### 6. 代码治理与架构规范重构
- [ ] 彻底清除所有 Python 源文件顶部堆积的大段无用 `''' ... '''` 废弃代码多行注释块，保持代码清爽 (问题 7)
- [ ] 物理删除 `service/` 目录下误放且未处理 `None` 防御的旧版 `manager_dashboard_page.py` 界面代码文件 (问题 6)
- [ ] 遵循项目架构分层约束，新建 `dao/manager_dao.py` 并迁入 `service/manager_service.py` 中直写的 SQL 统计查询逻辑，恢复分层分工 (问题 5)

### 7. 项目依赖项补全
- [ ] 在项目的 `requirements.txt` 中追加 `pandas` 与 `openpyxl` 这两项执行 Excel 导出所必须的依赖 (问题 8)
