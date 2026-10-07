from app.product.contracts import ARCHITECTURE_LAYERS, CANONICAL_PHASES, CANONICAL_WORKFORCES
from app.workforce.registry import registry


def test_phase_contract_is_unique_and_complete():
    keys = [phase["key"] for phase in CANONICAL_PHASES]
    assert keys == [f"E{i}" for i in range(9, 25)]
    assert len(keys) == len(set(keys))
    assert all(phase["owner"] and phase["scope"] for phase in CANONICAL_PHASES)


def test_workforce_registry_matches_canonical_catalog():
    canonical = {item["key"] for item in CANONICAL_WORKFORCES}
    assert set(registry.names()) == canonical
    assert len(canonical) == 13
    assert all(item["owner_phase"].startswith("E") for item in CANONICAL_WORKFORCES)


def test_architecture_authority_chain_is_explicit():
    assert ARCHITECTURE_LAYERS[:5] == (
        "identity",
        "authorization",
        "domain_service",
        "repository",
        "postgresql_rls",
    )
    assert ARCHITECTURE_LAYERS[-3:] == (
        "output_validation",
        "evidence_provenance",
        "audit_telemetry",
    )
