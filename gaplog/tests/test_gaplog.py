import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gaplog import FIELDS, GapLog, read  # noqa: E402
from gaplog.__main__ import main as cli  # noqa: E402


def test_record_roundtrip(tmp_path):
    p = tmp_path / "g.jsonl"
    log = GapLog(p)
    rec = log.record("t1", "completed", "completed", "manual")
    got = list(read(p))
    assert got == [rec]
    assert got[0]["match"] is True
    assert set(got[0]) == set(FIELDS)


def test_mismatch_detected(tmp_path):
    p = tmp_path / "g.jsonl"
    rec = GapLog(p).record("t1", "completed:pushed", "not-on-remote", "manual")
    assert rec["match"] is False


def test_read_rejects_missing_fields(tmp_path):
    p = tmp_path / "g.jsonl"
    p.write_text(json.dumps({"ts": "2026-01-01", "task_id": "x"}) + "\n")
    with pytest.raises(ValueError):
        list(read(p))


def test_prereg_refuses_overwrite(tmp_path, capsys):
    pre = tmp_path / "pre.json"
    cli(["preregister", str(pre), "--min-n", "10", "--rate", "0.01"])
    with pytest.raises(FileExistsError):
        cli(["preregister", str(pre), "--min-n", "1", "--rate", "0.5"])


def test_summarize_verdicts(tmp_path, capsys):
    pre = tmp_path / "pre.json"
    g = tmp_path / "g.jsonl"
    cli(["preregister", str(pre), "--min-n", "2", "--rate", "0.25"])
    capsys.readouterr()

    log = GapLog(g)
    log.record("a", "done", "done", "v")
    cli(["summarize", str(g), "--prereg", str(pre)])
    assert "INSUFFICIENT DATA" in capsys.readouterr().out

    log.record("b", "done", "not-done", "v")
    cli(["summarize", str(g), "--prereg", str(pre)])
    out = capsys.readouterr().out
    assert "rate:          0.5000" in out
    assert "THRESHOLD MET" in out


def _write_prereg(path, declared_at, min_n=2, rate=0.25):
    path.write_text(json.dumps({
        "declared_at": declared_at, "min_n": min_n,
        "adoption_rate": rate, "note": "",
    }))


def _write_rec(path, ts, match=True, mode="a"):
    rec = {"ts": ts, "task_id": "t", "reported": "done",
           "verified": "done" if match else "not-done",
           "match": match, "verifier": "v"}
    with open(path, mode) as f:
        f.write(json.dumps(rec) + "\n")


def test_prereg_equal_timestamp_is_valid(tmp_path, capsys):
    """Same clock tick (coarse-resolution clocks) must not reject the
    happy path — regression for the <= string-comparison bug."""
    ts = "2026-07-04T10:00:00.500000+00:00"
    pre, g = tmp_path / "pre.json", tmp_path / "g.jsonl"
    _write_prereg(pre, ts)
    _write_rec(g, ts)
    code = cli(["summarize", str(g), "--prereg", str(pre)])
    out = capsys.readouterr().out
    assert code == 0
    assert "INVALID" not in out
    assert "INSUFFICIENT DATA" in out


def test_prereg_zero_microsecond_format_is_parsed_not_string_compared(tmp_path, capsys):
    """isoformat() drops zero microseconds; parsed comparison must still
    order correctly where lexicographic comparison would not be trusted."""
    pre, g = tmp_path / "pre.json", tmp_path / "g.jsonl"
    _write_prereg(pre, "2026-07-04T10:00:00+00:00", min_n=1)
    _write_rec(g, "2026-07-04T10:00:00.000001+00:00")
    code = cli(["summarize", str(g), "--prereg", str(pre)])
    out = capsys.readouterr().out
    assert code == 0
    assert "INVALID" not in out


def test_prereg_strictly_postdating_first_record_is_invalid(tmp_path, capsys):
    pre, g = tmp_path / "pre.json", tmp_path / "g.jsonl"
    _write_prereg(pre, "2026-07-04T10:00:01+00:00")
    _write_rec(g, "2026-07-04T10:00:00.999999+00:00")
    code = cli(["summarize", str(g), "--prereg", str(pre)])
    assert code == 2
    assert "INVALID" in capsys.readouterr().out


def test_prereg_postdating_data_is_invalid(tmp_path, capsys):
    g = tmp_path / "g.jsonl"
    pre = tmp_path / "pre.json"
    _write_rec(g, "2026-07-04T10:00:00+00:00")
    _write_prereg(pre, "2026-07-04T10:00:01+00:00", min_n=1, rate=0.01)
    code = cli(["summarize", str(g), "--prereg", str(pre)])
    assert code == 2
    assert "INVALID" in capsys.readouterr().out


def test_demo_end_to_end(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(ROOT / "demo" / "said_done.py")],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    assert "DISCREPANCY" in proc.stdout
    assert "MATCH" in proc.stdout
    recs = list(read(tmp_path / "gaps.jsonl"))
    assert [r["match"] for r in recs] == [False, True]
