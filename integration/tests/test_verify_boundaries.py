from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_verify_boundaries_module():
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "verify_boundaries.py"
    spec = importlib.util.spec_from_file_location("verify_boundaries", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_verify_boundaries_rejects_duplicate_policy_entries(tmp_path, monkeypatch, capsys):
    module = _load_verify_boundaries_module()

    root = tmp_path / "repo"
    contracts = root / "contracts"
    contracts.mkdir(parents=True)
    policy_path = contracts / "dependency-policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "components": {
                    "fidelis-contracts": {"may_depend_on": [], "test_may_depend_on": []},
                    "meaning-assay": {
                        "may_depend_on": ["fidelis-contracts", "fidelis-contracts"],
                        "test_may_depend_on": [],
                    },
                    "ethics-council": {"may_depend_on": ["fidelis-contracts"], "test_may_depend_on": []},
                    "trusted-runtime": {
                        "may_depend_on": ["fidelis-contracts", "meaning-assay", "ethics-council"],
                        "test_may_depend_on": [],
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module, "POLICY", policy_path)

    assert module.main() == 1
    err = capsys.readouterr().err
    assert "duplicate may_depend_on entries" in err



def test_verify_boundaries_rejects_unknown_test_dependency_target(tmp_path, monkeypatch, capsys):
    module = _load_verify_boundaries_module()

    root = tmp_path / "repo"
    contracts = root / "contracts"
    contracts.mkdir(parents=True)
    policy_path = contracts / "dependency-policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "components": {
                    "fidelis-contracts": {"may_depend_on": [], "test_may_depend_on": []},
                    "meaning-assay": {"may_depend_on": ["fidelis-contracts"], "test_may_depend_on": ["ghost-test-component"]},
                    "ethics-council": {"may_depend_on": ["fidelis-contracts"], "test_may_depend_on": []},
                    "trusted-runtime": {
                        "may_depend_on": ["fidelis-contracts", "meaning-assay", "ethics-council"],
                        "test_may_depend_on": [],
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module, "POLICY", policy_path)

    assert module.main() == 1
    err = capsys.readouterr().err
    assert "references unknown test_may_depend_on target" in err



def test_verify_boundaries_rejects_unknown_dependency_target(tmp_path, monkeypatch, capsys):
    module = _load_verify_boundaries_module()

    root = tmp_path / "repo"
    contracts = root / "contracts"
    contracts.mkdir(parents=True)
    policy_path = contracts / "dependency-policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "components": {
                    "fidelis-contracts": {"may_depend_on": [], "test_may_depend_on": []},
                    "meaning-assay": {"may_depend_on": ["fidelis-contracts", "ghost-component"], "test_may_depend_on": []},
                    "ethics-council": {"may_depend_on": ["fidelis-contracts"], "test_may_depend_on": []},
                    "trusted-runtime": {
                        "may_depend_on": ["fidelis-contracts", "meaning-assay", "ethics-council"],
                        "test_may_depend_on": [],
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module, "POLICY", policy_path)

    assert module.main() == 1
    err = capsys.readouterr().err
    assert "references unknown may_depend_on target" in err



def test_verify_boundaries_rejects_dependency_cycle(tmp_path, monkeypatch, capsys):
    module = _load_verify_boundaries_module()

    root = tmp_path / "repo"
    contracts = root / "contracts"
    contracts.mkdir(parents=True)
    policy_path = contracts / "dependency-policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "components": {
                    "fidelis-contracts": {"may_depend_on": [], "test_may_depend_on": []},
                    "meaning-assay": {"may_depend_on": ["fidelis-contracts", "ethics-council"], "test_may_depend_on": []},
                    "ethics-council": {"may_depend_on": ["fidelis-contracts", "meaning-assay"], "test_may_depend_on": []},
                    "trusted-runtime": {
                        "may_depend_on": ["fidelis-contracts", "meaning-assay", "ethics-council"],
                        "test_may_depend_on": [],
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module, "POLICY", policy_path)

    assert module.main() == 1
    err = capsys.readouterr().err
    assert "dependency cycle among" in err



def test_verify_boundaries_accepts_minimal_acyclic_policy(tmp_path, monkeypatch, capsys):
    module = _load_verify_boundaries_module()

    root = tmp_path / "repo"
    contracts = root / "contracts"
    contracts.mkdir(parents=True)
    policy_path = contracts / "dependency-policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "components": {
                    "fidelis-contracts": {"may_depend_on": [], "test_may_depend_on": []},
                    "meaning-assay": {"may_depend_on": ["fidelis-contracts"], "test_may_depend_on": []},
                    "ethics-council": {"may_depend_on": ["fidelis-contracts"], "test_may_depend_on": []},
                    "trusted-runtime": {
                        "may_depend_on": ["fidelis-contracts", "meaning-assay", "ethics-council"],
                        "test_may_depend_on": [],
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module, "POLICY", policy_path)

    assert module.main() == 0
    out = capsys.readouterr().out
    assert "Declared dependency policy valid" in out



def test_verify_boundaries_rejects_forbidden_python_cross_import(tmp_path, monkeypatch, capsys):
    module = _load_verify_boundaries_module()

    root = tmp_path / "repo"
    contracts = root / "contracts"
    packages = root / "packages"
    contracts.mkdir(parents=True)
    (packages / "fidelis-contracts" / "src" / "fidelis_contracts").mkdir(parents=True)
    (packages / "meaning-assay" / "src" / "meaning_assay").mkdir(parents=True)
    (packages / "ethics-council" / "src" / "ethics_council").mkdir(parents=True)

    for pkg in [
        packages / "fidelis-contracts" / "src" / "fidelis_contracts" / "__init__.py",
        packages / "meaning-assay" / "src" / "meaning_assay" / "__init__.py",
        packages / "ethics-council" / "src" / "ethics_council" / "__init__.py",
    ]:
        pkg.write_text("", encoding="utf-8")

    (packages / "meaning-assay" / "src" / "meaning_assay" / "bad_import.py").write_text(
        "import ethics_council\n",
        encoding="utf-8",
    )

    policy_path = contracts / "dependency-policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "components": {
                    "fidelis-contracts": {"may_depend_on": [], "test_may_depend_on": []},
                    "meaning-assay": {"may_depend_on": ["fidelis-contracts"], "test_may_depend_on": []},
                    "ethics-council": {"may_depend_on": ["fidelis-contracts"], "test_may_depend_on": []},
                    "trusted-runtime": {
                        "may_depend_on": ["fidelis-contracts", "meaning-assay", "ethics-council"],
                        "test_may_depend_on": [],
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module, "POLICY", policy_path)

    assert module.main() == 1
    err = capsys.readouterr().err
    assert "observed forbidden Python import" in err



def test_verify_boundaries_rejects_forbidden_python_test_import(tmp_path, monkeypatch, capsys):
    module = _load_verify_boundaries_module()

    root = tmp_path / "repo"
    contracts = root / "contracts"
    packages = root / "packages"
    contracts.mkdir(parents=True)
    (packages / "fidelis-contracts" / "src" / "fidelis_contracts").mkdir(parents=True)
    (packages / "meaning-assay" / "tests").mkdir(parents=True)
    (packages / "ethics-council" / "src" / "ethics_council").mkdir(parents=True)

    (packages / "fidelis-contracts" / "src" / "fidelis_contracts" / "__init__.py").write_text("", encoding="utf-8")
    (packages / "ethics-council" / "src" / "ethics_council" / "__init__.py").write_text("", encoding="utf-8")
    (packages / "meaning-assay" / "tests" / "test_bad_import.py").write_text(
        "import ethics_council\n",
        encoding="utf-8",
    )

    policy_path = contracts / "dependency-policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "components": {
                    "fidelis-contracts": {"may_depend_on": [], "test_may_depend_on": []},
                    "meaning-assay": {"may_depend_on": ["fidelis-contracts"], "test_may_depend_on": []},
                    "ethics-council": {"may_depend_on": ["fidelis-contracts"], "test_may_depend_on": []},
                    "trusted-runtime": {
                        "may_depend_on": ["fidelis-contracts", "meaning-assay", "ethics-council"],
                        "test_may_depend_on": [],
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module, "POLICY", policy_path)

    assert module.main() == 1
    err = capsys.readouterr().err
    assert "observed forbidden Python test import" in err



def test_verify_boundaries_rejects_forbidden_node_package_dependency(tmp_path, monkeypatch, capsys):
    module = _load_verify_boundaries_module()

    root = tmp_path / "repo"
    contracts = root / "contracts"
    packages = root / "packages"
    contracts.mkdir(parents=True)
    (packages / "fidelis-contracts").mkdir(parents=True)
    (packages / "meaning-assay").mkdir(parents=True)
    (packages / "ethics-council").mkdir(parents=True)

    (packages / "fidelis-contracts" / "package.json").write_text(
        json.dumps({"name": "@fidelis/contracts"}),
        encoding="utf-8",
    )
    (packages / "meaning-assay" / "package.json").write_text(
        json.dumps({"name": "@fidelis/meaning-assay", "dependencies": {"@fidelis/ethics-council": "1.0.0"}}),
        encoding="utf-8",
    )
    (packages / "ethics-council" / "package.json").write_text(
        json.dumps({"name": "@fidelis/ethics-council"}),
        encoding="utf-8",
    )

    policy_path = contracts / "dependency-policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "components": {
                    "fidelis-contracts": {"may_depend_on": [], "test_may_depend_on": []},
                    "meaning-assay": {"may_depend_on": ["fidelis-contracts"], "test_may_depend_on": []},
                    "ethics-council": {"may_depend_on": ["fidelis-contracts"], "test_may_depend_on": []},
                    "trusted-runtime": {
                        "may_depend_on": ["fidelis-contracts", "meaning-assay", "ethics-council"],
                        "test_may_depend_on": [],
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module, "POLICY", policy_path)

    assert module.main() == 1
    err = capsys.readouterr().err
    assert "observed forbidden package.json dependency" in err
