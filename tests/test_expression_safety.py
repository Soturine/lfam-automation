"""O avaliador de expressoes nao usa eval: so uma lista branca. Expressoes perigosas ou desconhecidas sao recusadas."""
import pytest

from codesys.generator.ld import _ev


@pytest.mark.parametrize("expr", [
    "__import__('os').system('echo x')", "open('x')", "().__class__", "[1,2]", "lambda: 1", "A if B else C",
    "abs(-1)", "SEL(1, 2, 3, key=4)", "A.real", "'texto'", "A[0]",
])
def test_disallowed_expressions_are_rejected(expr):
    with pytest.raises((ValueError, SyntaxError, TypeError)):
        _ev(expr, {})


def test_allowed_expressions_and_iec_keywords():
    assert _ev("NOT A OR B AND TRUE", {"A": True, "B": False}) is False
    assert _ev("LIMIT(17.0, SEL(F, SP, SP * 0.9), 34.0)", {"F": True, "SP": 30.0}) == 27.0
    assert _ev("(N + 1) MOD 20", {"N": 19}) == 0
    assert _ev("X <> 3", {"X": 4}) is True
    assert _ev("DESCONHECIDA + 1", {}) == 1.0, "nome nao inicializado vale 0 (como no CLP apos a carga)"
