"""Checker-facing trace serialization and hashing (DRAFT trace schema; checklist item 11).

Protocol L284 and File 30 L87: the checker runs "over an immutable serialized trace".
The pack does not specify the serialization; it is TO FREEZE (L543). This module
implements the DRAFT proposal in docs/fifo-frozen-values-proposal-DRAFT.md, item 11:
- `trace` is the list of rows the harness recorded (A-040, A-042);
- serialization: UTF-8 JSON, sorted keys, no insignificant whitespace;
- the SHA-256 of those bytes is recorded before the checker runs;
- each checker invocation receives a value decoded from the same bytes, so neither
  invocation can affect the stored bytes or the other invocation's input.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

TRACE_SCHEMA_VERSION_DRAFT = "openvef-trace-0.1-draft"
ROW_KEYS = frozenset({"cycle_index", "reset", "inputs_consumed_at_edge_n", "outputs_after_edge_n",
                      "next_inputs_scheduled_for_edge_n_plus_1", "driver_completed"})


@dataclass(frozen=True)
class FrozenTrace:
    data: bytes
    sha256: str

    def decoded(self) -> Any:
        """A fresh value for one checker invocation."""
        return json.loads(self.data.decode("utf-8"))

    def verify(self) -> bool:
        return hashlib.sha256(self.data).hexdigest() == self.sha256


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def freeze(rows: list) -> FrozenTrace:
    """Serialize and hash a completed trace. Rejects rows outside the DRAFT schema."""
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != ROW_KEYS:
            raise ValueError(f"trace row {i} does not have the schema keys")
    data = canonical_bytes(rows)
    return FrozenTrace(data, hashlib.sha256(data).hexdigest())
