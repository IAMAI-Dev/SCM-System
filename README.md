# 供应链管理系统

基于 PySide6、MySQL 和 Matplotlib 的供应链管理桌面系统。项目采用
`UI -> Service -> DAO -> MySQL` 分层架构，覆盖业务操作、权限、审计、
分析图表、Excel 导出和数据库版本迁移。

新版入口是 `main.py`。根目录中的 `scm_gui.py` 与 `scm.txt` 是旧版
Tkinter 实现，仅用于对照，不再作为开发入口。

## 功能模块

| 模块 | 主要能力 |
| --- | --- |
| 登录与欢迎页 | 账号认证、角色和部门权限、登录审计、轻量首屏 |
| 总览仪表盘 | 订单、营收、客户、库存预警 KPI 和低库存快照 |
| 订单管理 | 查询、明细、状态更新、模拟下单、Excel 导出 |
| 库存调度 | 库存查询、低库存筛选、ABC 分类、补货建议、采购单生成 |
| 客户管理 | 客户查询、维护和 Excel 导出 |
| 供应商分析 | 供应量、国家分布、采购趋势、供应商评分与排名 |
| 采购管理 | 查看补货采购单及其处理状态 |
| 经营分析 | 月度营收、畅销零件、客户价值分布 |
| 性能监控 | 表容量、估算行数和非主键索引清单 |
| 用户与审计 | 用户权限维护、操作日志和订单状态审计 |

仪表盘和分析页面采用后台查询与局部加载状态。登录后先显示欢迎页，
业务页面在首次点击时按需创建，避免启动阶段阻塞界面。

## 技术栈

- Python 3.10 或更高版本
- PySide6 6.7+
- MySQL 8.x
- mysql-connector-python
- Matplotlib
- pandas 与 openpyxl，用于 Excel 导出

## 快速开始

以下命令在包含 `main.py` 的 `SCM-System` 目录执行。

### 1. 创建虚拟环境

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. 准备数据库

应用依赖已导入的课程基础表：

- `Customer`
- `Orders`
- `Lineitem`
- `Part`
- `PartSupp`
- `Supplier`
- `Nation`

程序会管理自身的用户、日志、补货订单、视图、存储过程、触发器和索引，
但不会自动导入上述课程基础数据。

### 3. 配置连接

```powershell
Copy-Item config.ini.example config.ini
notepad config.ini
```

示例：

```ini
[database]
host = localhost
port = 3306
user = root
password = 你的MySQL密码
database = experiment2026
pool_name = scm_pool
pool_size = 5

[app]
warehouse = 华东总仓
account_set = experiment2026
theme = industrial
```

`account_set` 可以省略；省略后顶部账套名跟随数据库名。真实的
`config.ini` 已被 Git 忽略，不应提交数据库密码。

以下环境变量可覆盖配置文件：

| 环境变量 | 对应配置 |
| --- | --- |
| `SCM_DB_HOST` | 数据库主机 |
| `SCM_DB_PORT` | 数据库端口 |
| `SCM_DB_USER` | 数据库用户 |
| `SCM_DB_PASSWORD` | 数据库密码 |
| `SCM_DB_NAME` | 数据库名 |
| `SCM_DB_POOL_NAME` | 连接池名称 |
| `SCM_DB_POOL_SIZE` | 连接池大小 |
| `SCM_ACCOUNT_SET` | 界面账套名 |

### 4. 启动

```powershell
python main.py
```

## 数据库迁移

启动时 `core/db.py` 会创建并读取 `scm_schema_migrations`。只执行尚未
记录的 SQL 脚本，已经应用的脚本不会在每次启动时重复扫描大表。

当前迁移顺序：

1. `01_app_tables.sql`：用户、日志和订单审计表。
2. `02_views.sql`：库存、销售、供应商和客户视图。
3. `03_procedures.sql`：仪表盘存储过程。
4. `04_triggers.sql`：用户与订单审计触发器。
5. `05_seed.sql`：演示账号和必要的演示字段补全。
6. `06.sql`：补货采购单表。
7. `07_performance_indexes.sql`：经营分析与趋势查询索引。

已有旧版数据库在对象完整时会自动建立迁移基线；全新数据库会按顺序
执行全部迁移。新增迁移时应创建新的编号脚本，并追加到
`MIGRATION_SCRIPTS`，不要修改已经发布迁移的语义。

## 演示账号与权限

默认演示账号密码均为 `123456`。

| 用户名 | 部门 | 角色 | 权限摘要 |
| --- | --- | --- | --- |
| `admin` | 总管理 | admin | 全部模块和全部操作 |
| `David` | 采购部 | manager | 采购业务完全控制，其他业务可查询 |
| `Tom` | 销售部 | manager | 销售业务完全控制，其他业务可查询 |
| `Jerry` | 客户管理部 | manager | 客户业务完全控制，其他业务可查询 |
| `Marry` | 采购部 | staff | 本部门查看和新增 |
| `Jack` | 销售部 | staff | 本部门查看和新增 |
| `Mike` | 客户管理部 | staff | 本部门查看和新增 |

权限不仅控制侧边栏入口，写操作还会在 Service 层再次校验。管理员可管理
用户权限，经理可查看经营分析，日志入口按角色限制。

## 项目结构

```text
SCM-System/
├── main.py                    # 应用入口、迁移、登录和主窗口
├── config.ini.example         # 本地配置模板
├── requirements.txt           # Python 依赖
├── core/                      # 配置、连接池、事务和迁移
├── dao/                       # 参数化 SQL 与数据库访问
├── service/                   # 权限、业务规则和事务编排
├── ui/                        # 主窗口、样式、模型和通用图表
│   └── pages/                 # 各业务页面
├── sql/                       # 有序数据库迁移脚本
├── utils/                     # Excel 导出等通用工具
├── tools/                     # 静态冒烟检查
├── docs/                      # 项目规范、实施状态和运维说明
├── analysis_results.md        # 历史问题分析报告
├── task.md                    # 修复任务与完成状态
└── changelog.md               # 新旧版本及迭代记录
```

## 开发与验证

语法编译：

```powershell
python -m compileall -q -x "(\.venv|\.git|\.idea|__pycache__)" .
```

静态冒烟检查：

```powershell
python tools\smoke_check.py
```

冒烟检查会验证 Python 语法、敏感旧配置片段，以及 UI 层是否直接包含
SQL。涉及界面或数据库的修改还应使用真实 MySQL 进行联调，并至少检查
`1320x840` 与 `980x620` 两种窗口尺寸。

## 常见问题

### 数据库连接失败

确认 MySQL 服务已启动，并检查数据库地址、端口、账号、密码和数据库名。
数据库账号需要创建表、视图、索引、存储过程和触发器的权限。

### 登录账号不存在

检查 `scm_schema_migrations` 中是否存在 `05_seed.sql`。如果迁移失败，先
修复数据库权限或基础表结构，再重新启动应用。

### 页面为空或统计为 0

确认课程基础表已经导入当前数据库。`Orders` 为空时订单类指标会显示 0；
`Lineitem` 缺少日期时趋势图可能没有可用月份。

### 图表首次加载较慢

应用会在登录期间后台预热 Matplotlib，进入分析页后再异步查询。图表卡片
显示加载状态属于正常行为；查询完成后应在当前页面直接出现，无需切页。

### Excel 无法导出

重新执行 `python -m pip install -r requirements.txt`，确认 pandas 和
openpyxl 已安装，并选择当前用户有写权限的目录。

## 文档索引

- [项目规范](docs/PROJECT_SPEC.md)
- [实施状态与维护计划](docs/IMPLEMENTATION_PLAN.md)
- [部署与运维说明](docs/OPERATIONS.md)
- [变更记录](changelog.md)
- [历史分析报告](analysis_results.md)
- [修复任务清单](task.md)
