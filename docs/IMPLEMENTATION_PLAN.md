# 供应链管理系统新版实施计划

## 一、总目标

将当前 Tkinter 单文件项目升级为 PySide6 + MySQL 的分层桌面系统。
新版主入口为 `main.py`，旧 `scm_gui.py` 仅作为 legacy 参考。

默认数据库为 MySQL `experiment2026`。系统需支持登录、权限、仪表盘、
订单、库存、客户、供应商、用户管理和审计日志。

## 二、阶段与提交

1. `docs: 新增新版项目规范与实施计划`
   - 新增 `docs/PROJECT_SPEC.md`。
   - 新增 `docs/IMPLEMENTATION_PLAN.md`。

2. `chore: 初始化 PySide6 项目骨架`
   - 新增 `main.py`、`requirements.txt`、`.gitignore`、
     `config.ini.example`。
   - 建立 `core/`、`dao/`、`service/`、`ui/`、`sql/`、`utils/`。
   - 清理 legacy 入口中的真实数据库密码。

3. `feat: 实现配置读取与数据库连接层`
   - 实现 `core/config.py`。
   - 实现 `core/db.py`，提供连接池和事务 helper。

4. `sql: 新增应用辅助表与数据库对象脚本`
   - 新增用户、权限、审计日志表。
   - 新增库存、销售、供应商相关视图。
   - 新增 KPI 存储过程、审计触发器和种子数据。

5. `feat: 实现登录与权限服务`
   - 实现 `auth_dao`、`auth_service`、`LoginDialog`。
   - 演示账号由 SQL seed 创建。
   - 登录后返回用户身份和权限。

6. `feat: 搭建主窗口工业控制台布局`
   - 实现主窗口、侧边栏、顶部工具栏和页面切换。
   - 新增统一 QSS，严格匹配 prompt 色彩系统。

7. `feat: 实现仪表盘与通用表格模型`
   - 实现通用 `QAbstractTableModel`。
   - 实现仪表盘 KPI、趋势图和库存摘要。

8. `feat: 实现订单与库存核心模块`
   - 订单查询、明细、状态更新、模拟下单事务。
   - 库存查询、低库存筛选、补货、ABC 分类。

9. `feat: 实现客户供应商用户与日志模块`
   - 客户 CRUD。
   - 供应商分析。
   - 用户权限管理。
   - 审计日志查看。

10. `chore: 完成验证脚本与收尾`
    - 新增 smoke test。
    - 确认 `python main.py` 可启动。
    - 确认代码中无真实数据库密码和 UI 层 SQL。

## 三、验证要求

每次提交前运行：

```bash
python -m compileall .
```

最终验收还需要完成：

- 数据库对象初始化可重复执行。
- 经理和员工账号均可登录。
- 权限按钮与页面访问符合角色配置。
- 订单事务失败时完整回滚。
- 主窗口所有页面可正常切换。
- 控制台和日志中无静默致命异常。

## 四、默认假设

- GUI 框架采用 PySide6。
- 默认数据库为 `experiment2026`。
- 真实数据库密码由本地 `config.ini` 或环境变量提供。
- 不修改外层 `Plan` 目录下的辅助材料。
