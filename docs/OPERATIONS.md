# 部署与运维说明

## 部署前检查

1. 安装 Python 3.10+ 与 MySQL 8.x。
2. 导入课程基础表和数据。
3. 创建应用数据库账号，并授予目标库的表、视图、索引、存储过程和
   触发器权限。
4. 从 `config.ini.example` 创建本地 `config.ini`。
5. 在虚拟环境中安装 `requirements.txt`。

## 启动链路

`main.py` 的启动顺序如下：

1. 创建 `QApplication` 并加载统一样式。
2. 后台预热 Matplotlib 和中文字体缓存。
3. 检查 `scm_schema_migrations` 并执行待处理迁移。
4. 显示登录窗口并认证账号。
5. 显示轻量欢迎页。
6. 用户点击模块后按需创建页面并加载业务数据。

## 迁移管理

迁移记录表为 `scm_schema_migrations`。查看已执行迁移：

```sql
SELECT migration_name, applied_at
FROM scm_schema_migrations
ORDER BY migration_name;
```

新增迁移时：

1. 在 `sql/` 新建下一个编号文件。
2. 脚本应可在目标 MySQL 8.x 环境执行。
3. 将文件名追加到 `core/db.py` 的 `MIGRATION_SCRIPTS`。
4. 在备份数据库验证一次首次执行和一次重复启动。
5. 不手工插入迁移记录来绕过失败脚本。

## 常用诊断

### 检查 MySQL 服务

```powershell
Get-Service *mysql*
```

### 检查 Python 依赖

```powershell
python -m pip check
python -m pip show PySide6 mysql-connector-python matplotlib pandas openpyxl
```

### 检查项目

```powershell
python -m compileall -q -x "(\.venv|\.git|\.idea|__pycache__)" .
python tools\smoke_check.py
```

### 图表不显示

1. 确认页面状态已从 `loading` 进入 `loaded`。
2. 检查 DAO 查询是否返回有效日期和值。
3. 确认 Qt 控件只在主线程创建和绘制。
4. 检查画布是否在切换可见后执行最终 `draw()`。
5. 不要给动态画布的父卡片长期保留 `QGraphicsOpacityEffect`。

Matplotlib 缓存位于项目的 `.matplotlib/`，该目录已被 Git 忽略。缓存
损坏时可在应用关闭后删除，下一次启动会自动重建。

## 数据备份与恢复

迁移和应用启动前应备份目标数据库。示例：

```powershell
mysqldump -u root -p experiment2026 > experiment2026.sql
mysql -u root -p experiment2026 < experiment2026.sql
```

不要把包含业务数据或密码的备份文件提交到仓库。

## 发布检查清单

- 配置模板不包含真实密码。
- 待处理迁移可在备份库成功执行。
- 管理员、经理和员工账号权限符合预期。
- 经营分析与供应商分析首次进入即可显示。
- Excel 导出可生成并打开 `.xlsx` 文件。
- `1320x840` 与 `980x620` 下无控件重叠或横向滚动。
- 编译和冒烟检查通过。
