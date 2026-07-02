from __future__ import annotations

from trusted_runtime.config import detect_integration_mode, load_integration_paths
from trusted_runtime.integration.status import adapter_status


def test_load_integration_paths_has_workspace_root():
    paths = load_integration_paths()
    assert paths.workspace_root.exists()


def test_detect_integration_mode_returns_auditable_axes():
    report = detect_integration_mode()
    assert report.mode.value in {"stub", "partial", "all-real"}
    assert "ethics_council" in report.components
    assert hasattr(report.components["ethics_council"], "import_real")
    assert hasattr(report.components["ethics_council"], "path_real")
    assert hasattr(report.components["ethics_council"], "behavior_real")


def test_adapter_status_shape():
    status = adapter_status()
    assert status["status_version"]
    assert status["integration_mode"] in {"stub", "partial", "all-real"}
    assert "adapters" in status
    assert "ethics_council" in status["adapters"]
    assert "trustworthy_agent_stack" in status["adapters"]
    assert "meaning_assay" in status["adapters"]
    assert "sophron_cer" in status["adapters"]
    assert "attest_agent_conlang" in status["adapters"]


def test_adapter_status_surfaces_truth_axes_and_required_paths():
    status = adapter_status()
    ethics = status["adapters"]["ethics_council"]
    assert "import_real" in ethics
    assert "path_real" in ethics
    assert "behavior_real" in ethics
    assert "required_paths" in ethics
    assert isinstance(ethics["required_paths"], list)
