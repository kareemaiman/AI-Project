#!/usr/bin/env python3
"""
Automated Function & API Parser Script for Smart Rail Simulator.

Recursively scans all Python packages (core/, algorithms/, generators/, ui/, main.py),
extracts AST docstrings, classes, methods, and functions, and compiles functions.md.
"""

import os
import ast
from pathlib import Path
from datetime import datetime


def extract_type_or_arg(arg):
    """Formats an AST function argument with optional type hint."""
    res = arg.arg
    if arg.annotation:
        try:
            res += f": {ast.unparse(arg.annotation)}"
        except Exception:
            pass
    return res


def parse_python_file(file_path: Path):
    """Parses a single Python file and returns structured API documentation."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=str(file_path))
    except Exception as e:
        return {"error": str(e)}

    module_doc = ast.get_docstring(tree) or "No module docstring provided."
    classes = []
    functions = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_doc = ast.get_docstring(node) or "No class docstring provided."
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_doc = ast.get_docstring(item) or "No docstring provided."
                    args = [extract_type_or_arg(a) for a in item.args.args]
                    returns = ""
                    if item.returns:
                        try:
                            returns = f" -> {ast.unparse(item.returns)}"
                        except Exception:
                            pass
                    methods.append({
                        "name": item.name,
                        "args": args,
                        "returns": returns,
                        "doc": method_doc,
                        "line": item.lineno
                    })
            classes.append({
                "name": node.name,
                "doc": class_doc,
                "methods": methods,
                "line": node.lineno
            })
        elif isinstance(node, ast.FunctionDef):
            func_doc = ast.get_docstring(node) or "No docstring provided."
            args = [extract_type_or_arg(a) for a in node.args.args]
            returns = ""
            if node.returns:
                try:
                    returns = f" -> {ast.unparse(node.returns)}"
                except Exception:
                    pass
            functions.append({
                "name": node.name,
                "args": args,
                "returns": returns,
                "doc": func_doc,
                "line": node.lineno
            })

    return {
        "file": file_path.name,
        "rel_path": file_path.as_posix(),
        "doc": module_doc,
        "classes": classes,
        "functions": functions
    }


def generate_functions_markdown(root_dir: Path, output_file: Path):
    """Generates the functions.md directory scanning all project subpackages."""
    python_files = sorted([
        f for f in root_dir.glob("**/*.py")
        if not f.name.startswith("test_")
        and not f.name.startswith(".")
        and "venv" not in f.parts
        and ".venv" not in f.parts
        and "__pycache__" not in f.parts
        and "scripts" not in f.parts
    ])

    lines = [
        "# Smart Rail: Automated API & Function Directory (`functions.md`)",
        "",
        f"> **Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        "> **Note:** Do not manually edit this file. It is automatically compiled by `scripts/parse_functions.py`.",
        "",
        "---",
        ""
    ]

    for py_file in python_files:
        info = parse_python_file(py_file)
        if "error" in info:
            continue

        rel = py_file.relative_to(root_dir).as_posix()
        lines.append(f"## Module: [`{rel}`](file:///{py_file.resolve().as_posix()})")
        lines.append(f"**Description:** {info['doc']}\n")

        if info["classes"]:
            lines.append("### Classes\n")
            for cls in info["classes"]:
                lines.append(f"#### `class {cls['name']}` (Line {cls['line']})")
                lines.append(f"{cls['doc']}\n")
                if cls["methods"]:
                    lines.append("| Method | Signature | Description |")
                    lines.append("| :--- | :--- | :--- |")
                    for m in cls["methods"]:
                        sig = f"`{m['name']}({', '.join(m['args'])}){m['returns']}`"
                        doc_summary = m['doc'].strip().split("\n")[0]
                        lines.append(f"| `{m['name']}` | {sig} | {doc_summary} |")
                    lines.append("")

        if info["functions"]:
            lines.append("### Standalone Functions\n")
            lines.append("| Function | Signature | Description |")
            lines.append("| :--- | :--- | :--- |")
            for fn in info["functions"]:
                sig = f"`{fn['name']}({', '.join(fn['args'])}){fn['returns']}`"
                doc_summary = fn['doc'].strip().split("\n")[0]
                lines.append(f"| `{fn['name']}` | {sig} | {doc_summary} |")
            lines.append("")

        lines.append("---\n")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Successfully generated {output_file}")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    out_path = project_root / "docs" / "functions.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    generate_functions_markdown(project_root, out_path)
