"""Your agent said "done." Did the world agree?

This demo runs twice, offline, against a local bare git repository
standing in for a remote:

  run 1: the agent commits locally, reports "completed (pushed)",
         and never pushes.  (This failure mode was observed in the
         wild: a confident completion report describing local state
         that had not left the machine.)
  run 2: the agent actually pushes.

A separate verifier then reads the remote's HEAD directly and compares
it to what the agent claimed. Both outcomes are appended to gaps.jsonl.

Independence statement (inspect it, don't take it on faith): the
verifier below shares no working directory, no in-process state, and no
git objects with the agent — it reads the bare remote by its own path.
In this single-machine demo that separation is by construction of the
harness; in production, put the verifier behind its own read-only
credential on a host the agent cannot reach.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gaplog import GapLog  # noqa: E402


def sh(*args, cwd):
    return subprocess.run(
        args, cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def agent(workdir: Path, task_id: str, actually_push: bool) -> str:
    """A stand-in for any agent: does work, then self-reports."""
    (workdir / "result.txt").write_text(f"work product for {task_id}\n")
    sh("git", "add", "-A", cwd=workdir)
    sh("git", "commit", "-m", f"complete {task_id}", cwd=workdir)
    if actually_push:
        sh("git", "push", "origin", "main", cwd=workdir)
    return "completed:pushed"  # the self-report, sincere either way


def verifier(remote: Path, workdir: Path) -> str:
    """Independent check: does the remote's HEAD match the local claim?"""
    local = sh("git", "rev-parse", "HEAD", cwd=workdir)
    proc = subprocess.run(
        ["git", "rev-parse", "main"], cwd=remote, capture_output=True, text=True
    )
    remote_head = proc.stdout.strip() if proc.returncode == 0 else "(no commits)"
    return "completed:pushed" if remote_head == local else "not-on-remote"


def run(tag: str, actually_push: bool, root: Path, log: GapLog):
    remote = root / f"{tag}-remote.git"
    workdir = root / f"{tag}-work"
    subprocess.run(["git", "init", "--bare", "-b", "main", remote],
                   check=True, capture_output=True)
    subprocess.run(["git", "clone", remote, workdir],
                   check=True, capture_output=True)
    sh("git", "config", "user.email", "agent@example.test", cwd=workdir)
    sh("git", "config", "user.name", "agent", cwd=workdir)

    reported = agent(workdir, tag, actually_push)
    verified = verifier(remote, workdir)
    rec = log.record(tag, reported, verified,
                     verifier="git-remote-head, read via separate path")

    status = "MATCH" if rec["match"] else "DISCREPANCY"
    print(f"[{tag}] agent reported: {reported!r}   remote says: {verified!r}   -> {status}")


def main():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        log = GapLog(Path.cwd() / "gaps.jsonl")
        run("task-001", actually_push=False, root=root, log=log)
        run("task-002", actually_push=True, root=root, log=log)
    print("\nreceipts appended to gaps.jsonl "
          "(summarize with: python -m gaplog summarize gaps.jsonl)")


if __name__ == "__main__":
    main()
