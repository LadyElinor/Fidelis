from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_prints_component_summary(tmp_path: Path) -> None:
    report = tmp_path / "component-tests.json"
    report.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "component": "trusted-runtime",
                        "status": "failed",
                        "returncode": 1,
                        "reason_code": "execution_failed",
                    },
                    {
                        "component": "cer-telemetry",
                        "status": "passed",
                        "returncode": 0,
                        "reason_code": None,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "print_component_summary.py"),
            str(report),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "trusted-runtime" in completed.stdout
    assert "execution_failed" in completed.stdout
    assert "cer-telemetry" in completed.stdout
