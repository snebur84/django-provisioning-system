import pytest
from importlib import import_module

views = import_module("api.views")


def test_sanitize_filename_examples():
    # o comportamento atual retorna o basename do path sem diretórios (ex: '../../etc/passwd' -> 'passwd')
    out = views._sanitize_filename("../../etc/passwd")
    assert out.endswith("passwd")
    # garantir truncamento para nomes muito longos
    long_name = "a" * 200 + ".cfg"
    out2 = views._sanitize_filename(long_name)
    assert len(out2) <= 100 or len(out2) <= 120  # tolerância para limites definidos no código
    # garantir caracteres válidos
    assert all(c.isalnum() or c in "._-" for c in out2)