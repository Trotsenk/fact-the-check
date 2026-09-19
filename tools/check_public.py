"""Детектор утечек перед коммитом в публичный репозиторий.

Проверяет файлы, подготовленные к коммиту (git add), на то, чему не место
в открытом доступе: ключи API, приватные ключи, пути на Mac автора, IP-адреса,
личная почта. Дополнительные запреты (например, адрес сервера) лежат в
private/запреты.txt — сам список тоже частный, поэтому его нет в репозитории.

Запуск:  python tools/check_public.py          — файлы из git add
         python tools/check_public.py --all    — все отслеживаемые файлы
Код возврата 0 — чисто, 1 — найдены нарушения (коммит делать нельзя).
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVATE_LIST = ROOT / "private" / "запреты.txt"

# Общие запреты: безопасно держать в публичном коде, в них нет частных данных.
PATTERNS = {
    "ключ API Anthropic": r"sk-ant-[A-Za-z0-9_\-]{10,}",
    "приватный ключ": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    # Шаблон собран из частей, иначе детектор находит сам себя в этой строке.
    "путь на Mac": "/" + "Users" + r"/[^/\s]+/",
    "IP-адрес": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    # Почта, кроме служебных адресов GitHub и примеров.
    "почта": r"[A-Za-z0-9._%+\-]+@(?!users\.noreply\.github\.com)(?!example\.)[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
}


def files_to_check(check_all: bool) -> list[str]:
    cmd = ["git", "ls-files"] if check_all else ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line]


def private_patterns() -> dict[str, str]:
    # Каждая строка файла — буквальная строка-запрет; # — комментарий.
    if not PRIVATE_LIST.exists():
        return {}
    lines = PRIVATE_LIST.read_text(encoding="utf-8").splitlines()
    return {f"частный запрет «{s[:3]}…»": re.escape(s) for s in (l.strip() for l in lines) if s and not s.startswith("#")}


def main() -> int:
    check_all = "--all" in sys.argv
    rules = {**PATTERNS, **private_patterns()}
    files = files_to_check(check_all)
    hits = []
    for name in files:
        path = ROOT / name
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue  # двоичные и удалённые файлы пропускаем — считаем их ниже
        for label, pattern in rules.items():
            for m in re.finditer(pattern, text):
                line_no = text.count("\n", 0, m.start()) + 1
                hits.append((name, line_no, label))
    # Сводка (правило МОО 44): сколько на входе, сколько нарушений.
    print(f"Проверено файлов: {len(files)} · правил: {len(rules)} · нарушений: {len(hits)}")
    for name, line_no, label in hits:
        print(f"  ✗ {name}:{line_no} — {label}")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
