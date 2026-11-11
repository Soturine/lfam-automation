"""Gera codesys/exports/LFAM_PROGRAM.xml a partir do gerador (na raiz do repo: python tools/gen_ld_xml.py)."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from codesys.generator import program

out = pathlib.Path(__file__).resolve().parents[1] / "codesys" / "exports" / "LFAM_PROGRAM.xml"
out.write_text(program.xml(), encoding="utf-8")
print("wrote", out, "-", len(program.RUNGS), "rungs")
