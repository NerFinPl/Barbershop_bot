"""Быстрая проверка синтаксиса всех модулей бота.

Запускаю руками после правок: py_compile не тянет зависимости, поэтому ловит
опечатки даже там, где aiogram не установлен или конфиг ещё не поднялся.
Смысл простой - не гонять бота целиком ради одной забытой кавычки.
"""
from __future__ import annotations

import py_compile
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
SKIP = {"venv", ".venv", "__pycache__", ".git", "tmp_inspect"}


def main() -> int:
    files = sorted(
        path for path in BASE.rglob("*.py") if not (SKIP & set(path.parts))
    )

    bad = 0
    for path in files:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            bad += 1
            print(f"FAIL {path.relative_to(BASE)}")
            print(f"     {exc.msg.strip()}")
        else:
            print(f"ok   {path.relative_to(BASE)}")

    print(f"\nвсего файлов: {len(files)}, с ошибками: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
