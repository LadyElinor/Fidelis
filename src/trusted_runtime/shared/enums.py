from __future__ import annotations

from enum import Enum


class RuntimeDisposition(str, Enum):
    PROCEED = "PROCEED"
    HALT = "HALT"
    CONFIRM_HUMAN = "CONFIRM_HUMAN"
    SUSPEND = "SUSPEND"


class NormativeSummary(str, Enum):
    LUMINOUS = "LUMINOUS"
    CHARGED = "CHARGED"
    DANGEROUS = "DANGEROUS"
    QUIET_GOOD = "QUIET_GOOD"
    INERT = "INERT"
    CORROSIVE = "CORROSIVE"
    CONTESTED = "CONTESTED"
    UNDETERMINED = "UNDETERMINED"


class RiskState(str, Enum):
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"
    BLACK = "BLACK"


class ReceiptSchemaVersion(str, Enum):
    V1_0_0 = "1.0.0"


class AdapterProvenance(str, Enum):
    REAL = "REAL"
    PARTIAL = "PARTIAL"
    STUB = "STUB"
    UNAVAILABLE = "UNAVAILABLE"


class DecisionIntegrity(str, Enum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    DEMO_ONLY = "DEMO_ONLY"


class TripValidationStatus(str, Enum):
    UNVALIDATED = "UNVALIDATED"
    CALIBRATING = "CALIBRATING"
    VALIDATED = "VALIDATED"
    RETIRED = "RETIRED"
