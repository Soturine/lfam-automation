"""Verifica se todos os links relativos dos arquivos Markdown apontam para arquivos que existem.
Uso (na raiz): python tools/check_links.py        -> sai com codigo 1 se houver link quebrado."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"node_modules", ".venv", "references", "work", ".git", "dist"}
LINK = re.compile(r'(?:\]\(|(?:src|href)=")([^)"#\s]+)(#[^)"\s]*)?')


def main() -> int:
    bad = total = 0
    for p in sorted(ROOT.rglob("*.md")):
        rel = p.relative_to(ROOT)
        if SKIP & set(rel.parts):
            continue
        text = re.sub(r"```.*?```", "", p.read_text(encoding="utf-8"), flags=re.S)   # ignora blocos de codigo
        for m in LINK.finditer(text):
            target = m.group(1)
            if re.match(r"^(https?:|mailto:|data:)", target) or target.startswith("<"):
                continue
            resolved = (p.parent / target).resolve()
            if ROOT not in resolved.parents and resolved != ROOT:
                continue          # atalhos do proprio GitHub (ex.: ../../issues/new/choose) so existem no site
            total += 1
            if not resolved.exists():
                bad += 1
                print(f"QUEBRADO: {rel} -> {target}")
    print(f"{total} links verificados, {bad} quebrados")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
