"""Gera codesys/exports/NETWORKS_LOGIC.xml a partir do gerador (rodar na raiz do repo: python tools/gen_ld_xml.py)."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from codesys.generator import networks_logic as N
from codesys.generator.ld import pou_xml

out = pathlib.Path(__file__).resolve().parents[1] / "codesys" / "exports" / "NETWORKS_LOGIC.xml"
out.write_text(pou_xml("PLC_PRG", N.variables(), N.ALL), encoding="utf-8")
print("wrote", out)
