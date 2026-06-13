# 供应链管理系统

这是一个基于 PySide6 与 MySQL 的供应链管理桌面系统。系统采用分层
架构，提供登录权限、仪表盘、订单管理、库存调度、客户管理、供应商
分析、用户权限和审计日志等功能。

界面风格采用工业调度控制台设计：石墨色侧边栏、暖白顶部工具栏、
暖灰内容区和铜色主操作按钮，强调真实企业桌面软件的数据密度与稳定感。

## 一、运行环境

- Python 3.10 或更高版本。
- MySQL 8.x。
- 已在自己的 MySQL 中准备课程数据库；库名可以自定义，默认示例名为
  `experiment2026`。
- Windows PowerShell 或 PyCharm 终端。

## 二、安装依赖

进入克隆后的项目根目录，也就是包含 `main.py` 的目录：

```powershell
cd path\to\供应链管理系统
```

安装 Python 依赖：

```powershell
pip install -r requirements.txt
```

依赖包括：

- PySide6
- mysql-connector-python
- matplotlib

## 三、配置数据库

复制配置模板：

```powershell
Copy-Item config.ini.example config.ini
```

打开并修改本地配置：

```powershell
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
theme = industrial
```

其中 `database` 填写你本机实际的数据库名。`account_set` 可省略；省略时
界面顶部显示的账套名会跟随 `database`。

注意：`config.ini` 已加入 `.gitignore`，不要把真实数据库密码提交到
仓库。

也可以通过环境变量覆盖数据库配置：

- `SCM_DB_HOST`
- `SCM_DB_PORT`
- `SCM_DB_USER`
- `SCM_DB_PASSWORD`
- `SCM_DB_NAME`
- `SCM_DB_POOL_NAME`
- `SCM_DB_POOL_SIZE`
- `SCM_ACCOUNT_SET`

## 四、启动程序

运行：

```powershell
python main.py
```

程序启动时会自动初始化应用辅助数据库对象，包括：

- `scm_users` 用户权限表
- `scm_logs` 操作审计日志表
- `scm_order_audit` 订单状态审计表
- 库存、销售、供应商、客户相关视图
- 仪表盘 KPI 存储过程
- 用户与订单审计触发器
- 演示登录账号

## 五、演示账号

默认演示账号密码均为 `123456`。

| 用户名 | 部门 | 角色 | 说明 |
| --- | --- | --- | --- |
| `admin` | 总管理 | admin | 总管理员，拥有全部权限 |
| `David` | 采购部 | manager | 本部门完全控制，其他部门查询 |
| `Tom` | 销售部 | manager | 本部门完全控制，其他部门查询 |
| `Jerry` | 客户管理部 | manager | 本部门完全控制，其他部门查询 |
| `Marry` | 采购部 | staff | 本部门查看和插入 |
| `Jack` | 销售部 | staff | 本部门查看和插入 |
| `Mike` | 客户管理部 | staff | 本部门查看和插入 |

## 六、项目结构

```text
供应链管理系统/
├── main.py                 # PySide6 主入口
├── config.ini.example      # 数据库配置模板
├── requirements.txt        # Python 依赖
├── README.md               # 项目说明
├── core/                   # 配置、数据库连接池、初始化逻辑
├── dao/                    # 数据访问层，只在这里写 SQL
├── service/                # 业务服务层，负责权限和业务规则
├── ui/                     # PySide6 界面层
│   └── pages/              # 各业务页面
├── sql/                    # 数据库辅助对象脚本
├── tools/                  # 检查脚本
├── docs/                   # 新版规范与实施计划
├── scm_gui.py              # 旧 Tkinter 版本，仅作 legacy 参考
└── scm.txt                 # 旧版文本副本，仅作 legacy 参考
```

## 七、本地检查

运行语法编译检查：

```powershell
python -m compileall -q -x "(\.venv|\.git|\.idea|__pycache__)" .
```

运行冒烟检查：

```powershell
python tools\smoke_check.py
```

冒烟检查会确认：

- Python 文件可编译。
- 仓库中没有残留旧数据库密码片段。
- UI 层没有直接编写 SQL。

## 八、常见问题

### 1. 启动时报数据库连接失败

请检查 `config.ini` 中的 `host`、`port`、`user`、`password` 和
`database` 是否正确，并确认 MySQL 服务已启动。

### 2. 登录账号不存在

程序启动时会自动执行 `sql/05_seed.sql`。如果初始化失败，请检查
`config.ini` 中 `database` 指向的数据库是否存在，以及当前 MySQL 用户
是否有创建表、视图、存储过程和触发器的权限。

### 3. 页面数据为空

本系统依赖课程数据库中的核心表，例如 `Customer`、`Orders`、
`Lineitem`、`Part`、`PartSupp`、`Supplier`、`Nation`。请确认这些表
已经导入到 `config.ini` 中 `database` 指向的数据库。

### 4. 触发器或存储过程初始化失败

请确认当前 MySQL 用户具备创建 `TRIGGER` 和 `PROCEDURE` 的权限。
如果权限不足，可先使用管理员账号执行 `sql/` 目录中的脚本。

## 九、开发约束

- UI 层不允许写 SQL。
- SQL 必须使用参数化查询。
- 写操作必须通过 service 层做权限检查。
- 数据库账号密码不得硬编码。
- 每次阶段性开发都应运行检查并单独提交。
