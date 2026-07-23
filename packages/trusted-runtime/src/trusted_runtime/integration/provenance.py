from __future__ import annotations

from pathlib import Path
from typing import Any

from trusted_runtime.shared.enums import AdapterProvenance
from trusted_runtime.shared.receipts import sha256_hex


def process_provenance_record(
    *,
    adapter_name: str,
    adapter_provenance: AdapterProvenance,
    adapter_version: str,
    adapter_path: str | None,
    source_payload: Any,
) -> dict[str, Any]:
    payload = {
        "adapter_name": adapter_name,
        "adapter_provenance": adapter_provenance.value,
        "adapter_version": adapter_version,
        "adapter_path": str(Path(adapter_path).resolve()) if adapter_path else None,
        "source_payload_sha256": sha256_hex(source_payload),
    }
    payload["record_sha256"] = sha256_hex(payload)
    return payload
