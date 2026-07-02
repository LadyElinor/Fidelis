from __future__ import annotations

from trusted_runtime.integration.engine import CerSophronTelemetryAdapter


def test_extract_sophron_signal_tiers_prefers_native_signal_validation_when_present():
    adapter = CerSophronTelemetryAdapter()
    report = {
        "signal_validation": {
            "signals": {
                "sophron.shift": {
                    "tier": "unvalidated",
                    "tier_source": "sophron-emitted",
                    "source_layer": "sophron-cer",
                }
            }
        },
        "report": {
            "signals": {
                "shift": {"score": 0.4, "evidence": [{"id": "e1"}]}
            }
        },
    }

    emitted = adapter._extract_sophron_signal_tiers(report)

    assert emitted["sophron.shift"]["tier"] == "unvalidated"
    assert emitted["sophron.shift"]["tier_source"] == "sophron-emitted"
    assert emitted["sophron.shift"]["source_layer"] == "sophron-cer"
    assert emitted["sophron.shift"]["signal_id"] == "sophron.shift"
    assert emitted["sophron.shift"]["evidence_refs"] == []
    assert emitted["sophron.shift"]["semantic_checks"]["has_signal_id"] is True
    assert emitted["sophron.shift"]["semantic_checks"]["allowed_tier_source"] is True
    assert emitted["sophron.shift"]["semantic_checks"]["allowed_source_layer"] is True


def test_extract_sophron_signal_tiers_falls_back_to_tr_derived_report_shape():
    adapter = CerSophronTelemetryAdapter()
    report = {
        "report": {
            "signals": {
                "shift": {"score": 0.4, "evidence": [{"id": "e1"}]},
                "game": {"score": 0.2, "evidence": [{"id": "e2"}]},
                "decept": {"score": 0.8, "evidence": [{"id": "e3"}]},
                "corrig": {"score": 0.6, "evidence": [{"id": "e4"}]},
                "human": {"conflict_flags": [], "evidence": [{"id": "e5"}]},
            }
        }
    }

    emitted = adapter._extract_sophron_signal_tiers(report)

    assert set(emitted.keys()) == {
        "sophron.shift",
        "sophron.game",
        "sophron.decept",
        "sophron.corrig",
        "sophron.human",
    }
    assert all(item["tier"] == "validated-sim" for item in emitted.values())
    assert all(item["tier_source"] == "tr-derived" for item in emitted.values())
    assert all(item["source_layer"] == "sophron-cer" for item in emitted.values())
    assert all(item["signal_id"].startswith("sophron.") for item in emitted.values())
    assert emitted["sophron.shift"]["evidence_refs"] == ["e1"]
    assert emitted["sophron.game"]["evidence_refs"] == ["e2"]
    assert emitted["sophron.decept"]["evidence_refs"] == ["e3"]
    assert emitted["sophron.corrig"]["evidence_refs"] == ["e4"]
    assert emitted["sophron.human"]["evidence_refs"] == ["e5"]
    assert all(item["semantic_checks"]["has_signal_id"] is True for item in emitted.values())
    assert all(item["semantic_checks"]["allowed_tier_source"] is True for item in emitted.values())
    assert all(item["semantic_checks"]["allowed_source_layer"] is True for item in emitted.values())
    assert all(item["semantic_checks"]["evidence_refs_typed"] is True for item in emitted.values())
    assert all(item["semantic_checks"]["payload_matches_signal"] is True for item in emitted.values())


def test_extract_sophron_signal_tiers_returns_empty_without_supported_shapes():
    adapter = CerSophronTelemetryAdapter()

    assert adapter._extract_sophron_signal_tiers({}) == {}
    assert adapter._extract_sophron_signal_tiers({"report": {}}) == {}
    assert adapter._extract_sophron_signal_tiers({"report": {"signals": None}}) == {}
    assert adapter._extract_sophron_signal_tiers({"signal_validation": {"signals": None}}) == {}
