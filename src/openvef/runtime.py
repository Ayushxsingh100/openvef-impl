"""Runtime stages through the D-002 sandbox: factory/signature checks and checker calls.

Implements (with sandbox/harness.py):
  File 30 §3 L27, L35-L39 — restricted-runtime import, `create_driver(seed)` return type,
                   runtime `inspect.signature` checks, in the restricted container.
  Protocol §3.4 L166 (7) — "Factory return type and runtime signatures are checked
                   immediately after factory construction."
  Protocol §3.4 L166 (9)-(10) — each checker null invocation in a separate process (here:
                   a separate container); a wall-clock watchdog is
                   `CHECKER_TIMEOUT|phase=null_check`.

A-037 (decided by Claude, owner review pending): the stage map has no row for a driver
import or factory call that exceeds the wall-clock limit (the watchdog row is
`phase=driver_step` only), so that case raises `RuntimeStageError` and the runner records
ERROR, never a verdict. The F18 factory call uses seed 0, because no fixture supplies a
slot seed.
"""
from __future__ import annotations

from typing import Any, Optional

from openvef.envelope import Failure
from openvef.sandbox import DEFAULT_TIMEOUT_S, run_harness
from openvef.stage_map import CHECKER_TIMEOUT, CheckerOutcome

F18_FACTORY_SEED = 0


class RuntimeStageError(RuntimeError):
    """The sandbox produced no adjudicable result (timeout before a defined row, crash)."""


def _failure(record: dict) -> Failure:
    return Failure(record["stage_id"], record["error_class"], record["diagnostic"], record["disposition"])


def factory_checks(driver_source: str, seed: int = F18_FACTORY_SEED,
                   timeout_s: float = DEFAULT_TIMEOUT_S) -> Optional[Failure]:
    """Restricted import of driver.py, construction, return type and signatures."""
    r = run_harness({"task": "factory", "driver_source": driver_source, "seed": seed}, timeout_s)
    if r.timed_out:
        raise RuntimeStageError("A-037: driver import/factory exceeded the wall-clock limit; no stage-map row")
    if r.result is None:
        raise RuntimeStageError(f"sandbox returned no result (exit {r.returncode}): {r.stderr_tail[-300:]}")
    return None if r.result["failure"] is None else _failure(r.result["failure"])


def checker_invocation(checker_source: str, trace: Any, metadata: Any,
                       timeout_s: float = DEFAULT_TIMEOUT_S) -> CheckerOutcome | Failure:
    """One null invocation in its own container. A Failure means the runtime signature
    check of check_trace failed (AST_SIGNATURE)."""
    r = run_harness({"task": "checker", "checker_source": checker_source, "trace": trace, "metadata": metadata},
                    timeout_s)
    if r.timed_out:
        return CHECKER_TIMEOUT
    if r.result is None:
        raise RuntimeStageError(f"sandbox returned no result (exit {r.returncode}): {r.stderr_tail[-300:]}")
    if "failure" in r.result:
        return _failure(r.result["failure"])
    if "error" in r.result:
        return CheckerOutcome(None, tuple(r.result["error"]))
    return CheckerOutcome(r.result["verdict"], None, r.result["malformed_items"])
