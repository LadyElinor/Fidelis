from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from runtime.models import CaseInput


class InputValidationRuntimeError(Exception):
    pass


def load_case(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_and_validate(path: str | Path) -> CaseInput:
    raw = load_case(path)
    try:
        return CaseInput.model_validate(raw)
    except ValidationError as exc:
        raise InputValidationRuntimeError(str(exc)) from exc
