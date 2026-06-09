"""项目轻量级冒烟检查。"""

from __future__ import annotations

import compileall
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".git", ".venv", ".idea", "__pycache__"}
SKIP_FILES = {"config.ini", ".env"}
FORBIDDEN_SNIPPETS = {
    "D:" + "\\Database_Learning",
    "team" + "_exp",
    "database = " + "ex" + "p1",
    "SCM_DB_NAME" + '", "' + "ex" + "p1",
    "experiment" + "2024",
}


def _iter_project_files() -> list[Path]:
    """遍历需要检查的项目文件。"""
    result = []
    for path in PROJECT_ROOT.rglob("*"):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.name in SKIP_FILES:
            continue
        if path.is_file():
            result.append(path)
    return result


def check_compile() -> None:
    """检查 Python 语法。"""
    ok = compileall.compile_dir(
        str(PROJECT_ROOT),
        quiet=1,
        rx=re.compile(r"(\.venv|\.git|\.idea|__pycache__)"),
        maxlevels=20,
    )
    if not ok:
        raise RuntimeError("Python 编译检查失败。")


def check_forbidden_snippets() -> None:
    """检查仓库中是否残留旧密码片段。"""
    for path in _iter_project_files():
        if path.suffix.lower() not in {".py", ".txt", ".md", ".ini"}:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for snippet in FORBIDDEN_SNIPPETS:
            if snippet in content:
                raise RuntimeError(f"发现禁止片段：{path}")


def check_ui_sql_boundary() -> None:
    """检查 UI 层没有直接写 SQL 关键语句。"""
    forbidden = {"SELECT ", "INSERT ", "UPDATE ", "DELETE "}
    ui_dir = PROJECT_ROOT / "ui"
    for path in ui_dir.rglob("*.py"):
        content = path.read_text(encoding="utf-8", errors="ignore")
        upper_content = content.upper()
        if any(token in upper_content for token in forbidden):
            raise RuntimeError(f"UI 层疑似存在 SQL：{path}")


def main() -> int:
    """执行冒烟检查。"""
    check_compile()
    check_forbidden_snippets()
    check_ui_sql_boundary()
    print("smoke check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
