from dataclasses import dataclass


@dataclass
class _Rule:
    code: str


def test_registry_dedupes_by_code(clean_registry):
    r1 = _Rule(code='abc')
    r2 = _Rule(code='abc')
    r3 = _Rule(code='xyz')

    clean_registry.register(r1)  # type: ignore[arg-type]
    clean_registry.register(r2)  # type: ignore[arg-type]
    clean_registry.register(r3)  # type: ignore[arg-type]

    codes = [r.code for r in clean_registry.all()]
    assert codes.count('abc') == 1
    assert 'xyz' in codes
