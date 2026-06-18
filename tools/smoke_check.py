"""项目轻量级冒烟检查。"""

from __future__ import annotations

import ast
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".git", ".venv", ".idea", "__pycache__"}
SKIP_FILES = {"config.ini", ".env"}
EXAMPLE_FILES = {
    "README.md",
    "config.ini.example",
    "analysis_results.md",
    "task.md",
}
SQL_LITERAL_RE = re.compile(
    r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)\b\s+",
    re.IGNORECASE,
)
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
    """检查 Python 语法，不写入 pyc 缓存。"""
    for path in _iter_project_files():
        if path.suffix.lower() != ".py":
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        try:
            ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            raise RuntimeError(f"Python 语法检查失败：{path}") from exc


def check_forbidden_snippets() -> None:
    """检查仓库中是否残留旧密码片段。"""
    for path in _iter_project_files():
        if path.name in EXAMPLE_FILES:
            continue
        if path.suffix.lower() not in {".py", ".txt", ".md", ".ini"}:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for snippet in FORBIDDEN_SNIPPETS:
            if snippet in content:
                raise RuntimeError(f"发现禁止片段：{path}")


def check_ui_sql_boundary() -> None:
    """检查 UI 层没有直接写 SQL 关键语句。"""
    ui_dir = PROJECT_ROOT / "ui"
    for path in ui_dir.rglob("*.py"):
        source = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=str(path))
        for text in _iter_string_literals(tree):
            if SQL_LITERAL_RE.search(text):
                raise RuntimeError(f"UI 层疑似存在 SQL：{path}")


def _iter_string_literals(tree: ast.AST) -> list[str]:
    """提取 Python 字符串字面量，避免扫描注释和变量名。"""
    literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.append(node.value)
        elif isinstance(node, ast.JoinedStr):
            parts = []
            for value in node.values:
                if (
                    isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                ):
                    parts.append(value.value)
                else:
                    parts.append("{}")
            literals.append("".join(parts))
    return literals


def main() -> int:
    """执行冒烟检查。"""
    check_compile()
    check_forbidden_snippets()
    check_ui_sql_boundary()
    print("smoke check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
