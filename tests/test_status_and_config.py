from __future__ import annotations

from trusted_runtime.config import load_integration_paths
from trusted_runtime.integration.status import adapter_status


def test_load_integration_paths_has_workspace_root():
    paths = load_integration_paths()
    assert paths.workspace_root.exists()


def test_adapter_status_shape():
    status = adapter_status()
    assert status["status_version"]
    assert "adapters" in status
    assert "ethics_council" in status["adapters"]
    assert "trustworthy_agent_stack" in status["adapters"]
    assert "meaning_assay" in status["adapters"]
    assert "sophron_cer" in status["adapters"]
