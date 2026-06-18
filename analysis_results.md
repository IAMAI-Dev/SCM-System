# 供应链管理系统（新版本迭代分析与 Debug 测试报告）

本报告对新版本 `SCM-System` 进行了全面的静态代码分析和架构审计，对比了其与旧版本 `供应链管理系统` 的改动，列出了所有潜在的问题（包括核心 Bug、架构设计违背、代码冗余等），并针对性地给出了修改建议。

---

## 一、 新版本核心改动内容汇总

相较于旧版本（基准代码），新版本在保留原有功能的基础上，通过非侵入性与功能增强引入了以下改动：

### 1. 业务功能层面的增强
* **🛒 智能补货建议 (Smart Replenishment Suggestion)**
  * **入口**：库存调度页面。
  * **原理**：获取所有库存后，筛选出库存量低于 100 的零件，并计算建议补货量（$100 - \text{avail\_qty}$）。通过 `QMessageBox` 以弹窗列表展示。
* **📦 采购单生成与采购管理 (Purchase Order)**
  * **生成**：在库存调度页面选中零件后，点击“生成采购单”按钮，弹窗输入数量并调用 Service 层存入 `scm_replenishment_orders` 表。
  * **管理**：侧边栏新增“采购管理”导航项，懒加载 `ReplenishmentPage`（显示单号、零件ID、供应商ID、数量、状态和创建时间）。
* **📊 经营分析驾驶舱 (Manager Dashboard)**
  * **入口**：侧边栏新增“经营分析”导航项（经理及以上级别可见）。
  * **图表**：使用 `matplotlib` 动态渲染三个图表：
    1. 月度营收趋势（折线图，单位为万元，已对 `None` 值做防御过滤）。
    2. Top 10 畅销零件（柱状图，基于销售数量）。
    3. 客户价值分布（散点图，横轴为账户余额，纵轴为订单数）。
* **📊 数据库性能监控 (Performance Monitor)**
  * **入口**：侧边栏新增“性能监控”导航项（管理员可见）。
  * **展示**：展示各个表的大小（MB）与行数；同时列表展示非主键索引清单（作为未使用索引的参考）。
* **📤 数据一键导出 Excel**
  * **原理**：封装 `utils/excel_exporter.py` 通用导出模块，在客户管理、订单管理、用户权限、审计日志、供应商分析、仪表盘等主要数据表格页面中，新增了“导出 Excel”按钮。

### 2. 基础架构与规范的改动
* **数据表变更**：新增了 `sql/06.sql`（创建补货订单表 `scm_replenishment_orders`）。
* **辅助文件引入**：新增了 `utils/excel_exporter.py`，引入了 `pandas` 依赖来转换表格数据并导出至本地。
* **页面路由扩展**：在 `ui/main_window.py` 中注册了 `performance`（性能监控）、`manager`（经营分析）以及 `replenishment`（采购管理）三个新页面的懒加载工厂和权限校验。

---

## 二、 潜在问题清单及修改建议

在对新版本进行静态编译和完整逻辑走读后，共发现 **18 个潜在问题**（其中包含 **4 个核心运行时 Bug**、**3 个架构设计缺陷** 以及 **4 个用户反馈的问题**）。以下是详细清单及具体的修改建议：

### 1. 核心运行时 Bug（会导致报错或数据不正确）

#### 🔴 Bug 1：补货订单表 `scm_replenishment_orders` 未进行初始化
* **文件位置**：[db.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/core/db.py#L98-L127)
* **具体表现**：`db.py` 的 `initialize_database_objects()` 中定义了启动时需要执行的 SQL 脚本列表：
  ```python
  script_names = [
      "01_app_tables.sql",
      "02_views.sql",
      "03_procedures.sql",
      "04_triggers.sql",
      "05_seed.sql",
  ]
  ```
  新版本新增的 `06.sql`（创建 `scm_replenishment_orders` 表）被遗漏在列表外。这导致新用户或重新部署的环境在启动时**不会创建补货订单表**，一旦点击“采购管理”或“生成采购单”，程序会报 `ProgrammingError: Table 'scm_replenishment_orders' doesn't exist` 崩溃。
* **修改建议**：在 `script_names` 列表的末尾追加 `"06.sql"`，确保应用启动时自动建表。

#### 🔴 Bug 2：性能监控页面的“行数”列显示为空白
* **文件位置**：[performance_page.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/ui/pages/performance_page.py#L27-L33) & [performance_dao.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/dao/performance_dao.py#L4-L17)
* **具体表现**：
  * 在 DAO 层中，查询行数的别名是 `row_count`：`table_rows AS row_count`。
  * 但在 UI 页面初始化表格模型时，定义的键名是 `"rows"`：
    ```python
    self.table_model = DictTableModel([
        ("name", "表名"),
        ("size_mb", "大小 (MB)"),
        ("rows", "行数"), # 这里的键值与 row_count 不匹配
    ])
    ```
  由于字典模型取值是根据 `key` 获取的，这会导致性能监控表格中的“行数”这一整列数据永远显示为空白。
* **修改建议**：将 `performance_page.py` 中的 `("rows", "行数")` 修改为 `("row_count", "行数")`。

#### 🔴 Bug 3：采购单审计日志未处于同一个数据库事务内（失去原子性）
* **文件位置**：[inventory_service.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/service/inventory_service.py#L200-L215)
* **具体表现**：
  在 `create_replenishment_order` 中，开启了事务上下文 `with transaction() as db_cursor:`，但调用审计日志 `auth_dao.log_action` 时**未传入 `db_cursor` 参数**：
  ```python
  with transaction() as db_cursor:
      order_id = inventory_dao.create_replenishment_order(
          part_key, supplier_key, quantity, db_cursor
      )
      auth_dao.log_action( # 未传入 db_cursor
          self.user_session.username,
          "inventory",
          "INSERT",
          f"创建补货订单 {order_id}..."
      )
  ```
  这会导致 `log_action` 在内部使用全新的数据库连接并开启新事务执行，破坏了原定“写数据与写审计日志在同一个事务中提交/回滚”的设计目标。如果写操作回滚，审计日志仍然会被记录，反之亦然。
* **修改建议**：在 `auth_dao.log_action` 调用中显式传入 `db_cursor=db_cursor`。

#### 🔴 Bug 4：供应商分析导出 Excel 时，“评分”列全部为空白
* **文件位置**：[suppliers_page.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/ui/pages/suppliers_page.py#L555-L567)
* **具体表现**：
  在 `_apply_ranking()` 中，第四列（“评分”）只调用了 `self.rank_table.setCellWidget(row_index, 3, self._score_bar(...))` 插入进度条控件，但**没有通过 `self._set_item()` 写入文本项**。
  由于通用导出工具是通过 `model.data(index)` 读取单元格的 `DisplayRole` 文本的，没有 `QTableWidgetItem` 意味着导出器在这个单元格读到的值为 `None`，最终导出的 Excel 报表中，所有供应商的“评分”都成了空值。
* **修改建议**：在 `setCellWidget` 之前，先调用 `self._set_item(row_index, 3, str(row["score"]))` 写入底层数据模型。

### 3. 代码健壮性、性能及依赖问题

#### 🟢 问题 8：`requirements.txt` 中缺少 `pandas` 和 `openpyxl` 依赖
* **文件位置**：[requirements.txt](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/requirements.txt)
* **具体表现**：
  项目引入了一键导出 Excel 的功能，其核心工具 `utils/excel_exporter.py` 依赖了 `pandas`。此外，`pandas` 在执行 `.to_excel()` 写入 `.xlsx` 时必须使用 `openpyxl` 作为引擎。然而这两项依赖并未记录在 `requirements.txt` 中。新成员拉取代码并安装依赖后，点击导出按钮将因缺少库而报错。
* **修改建议**：在 `requirements.txt` 中添加 `pandas` 和 `openpyxl`。

#### 🟢 问题 9：只读元数据查询错用了 `transaction()` 上下文管理器
* **文件位置**：[performance_dao.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/dao/performance_dao.py)
* **具体表现**：
  `get_table_stats()` 和 `get_unused_indexes()` 仅是读取 `information_schema` 表的元数据，却在内部使用了 `with transaction() as cursor:` 开启了事务。这增加了不必要的数据库开销（发送了 `START TRANSACTION` / `COMMIT` / `ROLLBACK` 命令），并在极高并发时可能导致锁资源竞争。
* **修改建议**：将 `with transaction() as cursor:` 替换为 `with cursor() as db_cursor:`。

#### 🟢 问题 10：订单号模糊搜索时未限制类型转换，可能导致性能降低
* **文件位置**：[order_dao.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/dao/order_dao.py#L23)
* **具体表现**：
  在 `list_orders` 中，当用户输入搜索字符时，SQL 拼接为了 `o.Orderkey = %s OR c.Name LIKE %s`。如果用户搜索的是包含字母的客户姓名，由于 `Orderkey` 为整型，数据库会对 `o.Orderkey = '客户名'` 执行隐式类型转换，这在 MySQL 中会导致索引失效并触发全表扫描。
* **修改建议**：参照 `customer_dao.py` 的做法，先通过 `search_key.isdigit()` 确认是否为数字，如果是数字才加入 `o.Orderkey = %s` 的比较逻辑。

#### 🟢 问题 11：性能监控页面中“未使用索引”查询逻辑不够严谨
* **文件位置**：[performance_dao.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/dao/performance_dao.py#L19-L34)
* **具体表现**：
  `get_unused_indexes()` 的查询仅仅是检索了除主键之外的前 10 个索引，但这并不等于“未使用的索引”。哪怕该索引被系统频繁使用，它也会被列出来。这可能会误导管理员去删除正在使用的关键索引。
* **修改建议**：
  在表格表头或说明文案中明确标注为“非主键索引列表（仅限参考）”，或者在可能的情况下使用 `performance_schema.table_io_waits_summary_by_index_usage` 进行真实未使用索引的排查（考虑到部分简易环境未开启性能图表，维持现状但修改文字表述是最稳妥的）。

#### 🟢 问题 12：经营分析驾驶舱刷新失败时会累积垃圾错误标签
* **文件位置**：[manager_dashboard_page.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/ui/pages/manager_dashboard_page.py#L47-L49)
* **具体表现**：
  在 `refresh()` 捕获到异常时，直接调用了 `self.layout.addWidget(QLabel(f"加载失败：{str(e)}"))`。如果数据库连接断开，用户反复点击“刷新”，每次点击都会产生并追加一个红色的失败 Label，导致 UI 界面堆积大量错乱的错误标签。
* **修改建议**：使用独立的 `self.status_label` 呈现刷新状态，或者刷新失败时使用 `QMessageBox.critical` 弹窗提醒，不应直接在主布局中无限追加 Label。

#### 🟢 问题 13：经营分析驾驶舱图表中文显示可能出现异常（未适配中文字体）
* **文件位置**：[manager_dashboard_page.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/ui/pages/manager_dashboard_page.py#L71-L106)
* **具体表现**：
  在经营分析页面刷新图表时，直接在 matplotlib 的 Axes 上写入了中文文本（如图表标题、坐标轴标签等），但并没有显式地为文本或者坐标轴应用项目中统一的 `CHINESE_FONT` 属性（或通过 `_apply_chinese_font` 配置）。这在没有配置全局默认中文字体的机器上，会导致图表中的所有中文字符渲染为乱码或空白方块（`□`）。
* **修改建议**：在 `manager_dashboard_page.py` 中引入 `ui.analytics_widgets` 模块下的 `_apply_chinese_font` 和 `CHINESE_FONT`，在画图时显式配置坐标轴字体与标题字体。

#### 🟢 问题 14：供应商分析柱状图中的供应商名称未做截断，导致文字重叠
* **文件位置**：[analytics_widgets.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/ui/analytics_widgets.py#L539)
* **具体表现**：
  重构后的 `draw_bar()` 直接使用了从 `prepared_data.keys()` 中获取的完整供应商名字作为 X 轴刻度，没有调用内置的 `_short_name` 进行截断。由于数据库中供应商的名字往往较长（如 `Supplier#000000001` 等），刻度标签之间在窗口缩小或正常宽度下会发生严重文字重叠遮挡。
* **修改建议**：对刻度标签调用截断函数，修改为 `names = [_short_name(name) for name in prepared_data.keys()]`。

#### 🟢 问题 15：订单明细弹窗内容为空
* **文件位置**：[orders_page.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/ui/pages/orders_page.py#L313-L345) & [order_dao.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/dao/order_dao.py#L31-L52)
* **具体表现**：
  在订单管理页面中，点击“查看明细”会弹出一个显示该订单所含零件、供应商及数量金额的表格。然而，当选择列表中任何一个订单时，弹出的“订单明细”窗口里表格内容全部是空的。
  * **原因定位**：
    当前 `exp1` 数据库中，`orders`（订单表）有 0 行数据，而 `lineitem`（订单明细表）有 22025 行数据，但是 `lineitem` 表中的 `Orderkey` 都在 `1` 到 `20001` 之间。
    由于主窗口显示的 100 条订单（订单号如 21100, 21099, 21098 等）是缓存/模拟测试数据（其订单号超出了 `lineitem` 表的 `20001` 上限），点击“查看明细”时程序使用 `Orderkey = 21098` 实时查询 `lineitem` 数据库，数据库中不存在该明细，故返回空结果，导致明细弹窗内没有任何行。
  * **修改建议**：
    1. 在 `list_order_details` 的 SQL 查询或 UI 展现中添加防御保护，如果明细数据为空，在弹窗中显示友好提示“该模拟订单暂无明细数据”。
    2. 在 `05_seed.sql` 或数据导入中，确保 `Orders` 和 `Lineitem` 的 `Orderkey` 能够正确关联。

#### 🟢 问题 16：供应商分析和经营分析页面中的图表大量缺失或空白
* **文件位置**：[manager_dashboard_page.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/ui/pages/manager_dashboard_page.py#L51-L110) & [suppliers_page.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/ui/pages/suppliers_page.py#L430-L457)
* **具体表现**：
  在“经营分析”页面中，“月度营收趋势”折线图完全为空（没有线）；“客户价值分布”散点图只显示中间单个橙色零点；在“供应商分析”页面中，部分图表为空或异常。
  * **原因定位**：
    1. **月度营收趋势**为空：该折线图按 `lineitem` 表中的 `Shipdate` 进行月份统计。但在 `exp1` 数据库的 `lineitem` 表中，所有记录的 `Shipdate` 字段全部为 `NULL`，导致 SQL 分组出的月份均为 `NULL`，在前端绘图过滤后列表为空。
    2. **客户价值分布**单点在零处：该散点图横轴为客户余额 `Acctbal`，纵轴为订单数。但在数据库中，`customer` 表的 `Acctbal` 字段全部为 `NULL`，且 `orders` 表行数为 0，导致所有客户的余额和订单数被转为 `0.0` 和 `0`。
    3. **供应商分析 - 采购额趋势**为空：由于 `lineitem` 表中的 `Receiptdate` 列全部为 `NULL`，导致 SQL 查询出的月份均为 `None`，折线图因没有有效月份坐标而无法渲染。
  * **修改建议**：
    这属于**数据库种子数据完整性缺失**导致的图表异常。
    1. 需在数据库或初始化脚本中，为 `lineitem` 的 `Shipdate`/`Receiptdate` 填充演示时间，为 `customer` 的 `Acctbal` 填充模拟余额。
    2. 优化 `ChartCanvas` 绘图代码，使其在检测到数据字段全部为 `NULL` 或数据为空时，在图表中心清晰渲染“暂无有效数据”文本，避免展示空坐标系误导用户。

#### 🟢 问题 17：性能监控功能含义不清
* **文件位置**：[performance_page.py](file:///d:/Database_Learning/team_exp/供应链管理系统/SCM-System/ui/pages/performance_page.py#L1-L100)
* **说明解释**：
  “性能监控”页面是为数据库管理员（DBA）或系统运维人员提供的工具。其核心用途是展示数据库中各个物理表的磁盘占用大小（MB）和总行数，并列出系统内的所有非主键索引。管理员可以通过它一目了然地识别出占用空间大或行数巨大的表，以便有针对性地对非主键索引进行调优（例如排查冗余索引或为慢查询补充索引）。
  * **修改建议**：
    在性能监控页面的顶部增加一段简单直观的中文辅助说明标签，例如：`"💡 提示：本页面用于监控数据库表空间占用、数据规模以及非主键索引清单，供数据库管理员(DBA)性能调优参考。"`，提升非专业开发用户的体验。

#### 🟢 问题 18：系统界面按钮和标题中大量夹杂了 emoji 表情
* **文件位置**：
  * `ui/pages/manager_dashboard_page.py:24` ("📊 经营分析驾驶舱")
  * `ui/pages/customers_page.py:285` ("📤 导出 Excel")
  * `ui/pages/dashboard_page.py:180` ("📤 导出 Excel")
  * `ui/pages/inventory_page.py:378` ("🛒 智能补货建议")
  * `ui/pages/inventory_page.py:383` ("📦 生成采购单")
  * `ui/pages/logs_page.py:114` ("📤 导出 Excel")
  * `ui/pages/orders_page.py:273` ("📤 导出 Excel")
  * `ui/pages/performance_page.py:62` ("📊 数据库指标")
  * `ui/pages/performance_page.py:70` ("📌 非主键索引清单")
  * `ui/pages/replenishment_page.py:31` ("📦 采购管理")
  * `ui/pages/suppliers_page.py:409` ("📤 导出 Excel")
  * `ui/pages/users_page.py:175` ("📤 导出 Excel")
* **具体表现**：
  各模块页面中的主要交互按钮（如“导出 Excel”、“智能补货建议”、“生成采购单”）以及标题中前缀了各类 emoji 图标。这些图标破坏了工业级后台管理系统的端庄严谨性，需予以清除。
* **修改建议**：
  将上述所有文件中的 `QPushButton` 和 `QLabel` 的文本前缀 emoji 清理，替换为纯文字（如将 `"📤 导出 Excel"` 修改为 `"导出 Excel"`）。

---

## 三、 测试结论与下一步行动计划

### 1. 冒烟测试状态
* **AST语法解析**：**通过**（所有文件均符合 Python 3.10 语法规范标准，无语法错误）。
* **冒烟检查脚本 `smoke_check.py`**：**通过**（未发现残留的本地敏感硬编码路径、旧数据库密码或 UI 层的直写 SQL）。
* **运行时业务闭环**：该版本存在 Bug 1（补货订单表未自动创建）和 Bug 2（性能监控行数列名不匹配），导致在干净环境下**无法正常使用**性能监控和补货建议功能。同时，由于本地 `exp1` 数据库中 `Orders` 表为空且多处日期字段为 `NULL`，导致订单明细弹窗无内容，且经营分析与供应商分析图表出现大面积空白。

### 2. 下一步建议修改方案
在您授权允许修改代码后，我们将为您一次性执行以下优化动作：
1. **数据库初始化与表结构修复**：修改 `core/db.py` 补充 `06.sql` 执行逻辑；同时更新 `05_seed.sql` 脚本以自动为 `customer.Acctbal`、`lineitem.Shipdate` / `Receiptdate` 生成一批合理的模拟数据，解决图表显示空白问题。
2. **状态更新选项中文本地化**：修改 `orders_page.py` 的“更新状态”功能，将选择项从 raw 字符 `["O", "F", "P"]` 优化为 `["进行中 (O)", "已完成 (F)", "挂起 (P)"]`，并在存入数据库时自动提取首字母，帮助用户看懂状态的业务含义。
3. **Emoji 表情全面清洗**：清理全部 10 个 UI 页面按钮和标题中的 emoji 表情符号，恢复企业级风格。
4. **性能监控功能解释**：在 `performance_page.py` 界面添加中文业务说明标签，方便理解其 DBA 调优目的。
5. **页面缺陷治理**：修复性能监控列为空（Bug 2）、一键导出评分缺失（Bug 4）、以及刷新失败页面堆叠（Bug 12） of UI 问题。
6. **数据一致性保全**：修复 `inventory_service` 事务传参（Bug 3）以及 `performance_dao` 读写资源浪费（Bug 9）。
7. **架构治理与代码清洗**：
   * 彻底删除所有 Python 文件中遗留的 `'''` 巨型无用注释段，还代码以清爽。
   * 删除 `service/manager_dashboard_page.py` 错位垃圾文件。
   * 新增 `dao/manager_dao.py` 并迁入 `manager_service.py` 内部直接写的 SQL，恢复规范分层。
8. **依赖补全**：在 `requirements.txt` 中追加 `pandas` 与 `openpyxl`。