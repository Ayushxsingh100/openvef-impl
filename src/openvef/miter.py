"""Mask-aware miter and bounded check (Protocol §11) — H5; counterexample replay — H6.

Implements:
  L278 — "The same mask and legal-input assumptions are used by the trace comparator and
         bounded-equivalence miter."
  L291 — "Build the miter with the same observation mask as the trace comparator and with
         the same reset sequence and legal-input assumptions from the design specification."
  L293-L297 — bound N no greater than the cycle cap; shortest counterexample length;
         NON_EQUIVALENT_WITHIN_N, BOUNDED_EQUIVALENT_N, UNDECIDED.
  L513 (F4) — replay the counterexample in the simulator; the masked divergence must
         appear at the predicted cycle.
  Owner decision D-007 (3) — Yosys built-in `sat` (no new dependency).

Construction (A-045, decided by Claude under the standing delegation, approved under D-009):
  - gold = null netlist, gate = mutant netlist, both read from the exported netlists;
  - mask: every "always" entry compares the port in every step; a window entry compares
    its port only where the GOLD (null) predicate signal has the stated value (L273);
  - legal-input assumption: generated from the design pack's executable predicate (for
    the FIFO, FIFO-042; FIFO-043 states the same rules are the miter's assumptions) by
    exhaustive enumeration, evaluated on the gold side's outputs at that step, i.e. the
    outputs the driver would have sampled; exact by construction (`compile_predicate`);
  - reset: reset_sequence[i] forces every input at step i+1; afterwards held inputs keep
    their held value and `legal` = 1 for each driver decision;
  - initial state: every register zero (`-set-init-zero`), a stated bounded-equivalence
    assumption (L544, TO FREEZE); the simulator starts memories at X instead.
Step mapping: Yosys `sat -seq` step t holds the state after t-1 active edges and the
inputs consumed at edge t-1, so trace row n (outputs after edge n) is step n+2.
"""
from __future__ import annotations

import itertools
import re
from typing import Any, Callable, Optional

NON_EQUIVALENT = "NON_EQUIVALENT_WITHIN_N"
BOUNDED_EQUIVALENT = "BOUNDED_EQUIVALENT_N"
UNDECIDED = "UNDECIDED"
ENUMERATION_CAP_BITS = 24  # build default: 16.7M predicate evaluations at most


class MiterError(RuntimeError):
    pass


# --- legal-input predicate → Verilog ----------------------------------------------------

def compile_predicate(fn: Callable[[dict, dict], bool], inputs: dict[str, int], outputs: dict[str, int],
                      out_prefix: str = "gold_") -> dict:
    """Exact Verilog expression for predicate `fn(vector, sampled)`.

    Every assignment of every input and output bit is evaluated (cap: ENUMERATION_CAP_BITS).
    A bit is in the support unless the predicate is invariant under flipping it in every
    assignment; the expression is the truth table over the support bits, so it equals the
    predicate on the whole domain."""
    ports = [("i", p, w) for p, w in sorted(inputs.items())] + [("o", p, w) for p, w in sorted(outputs.items())]
    total = sum(w for _, _, w in ports)
    if total > ENUMERATION_CAP_BITS:
        raise MiterError(f"predicate domain has {total} bits, over the enumeration cap {ENUMERATION_CAP_BITS}")
    # bit j of the index: ports in order, LSB first within each port
    bits = [(k, p, b) for k, p, w in ports for b in range(w)]
    values = [[format(v, f"0{w}b") for v in range(2 ** w)] for _, _, w in ports]
    table = bytearray()
    for combo in itertools.product(*reversed(values)):  # last port varies fastest... reversed:
        combo = combo[::-1]                              # first port is least significant
        vec, smp = {}, {}
        for (k, p, _), v in zip(ports, combo):
            (vec if k == "i" else smp)[p] = v
        r = fn(dict(vec), dict(smp))
        if not isinstance(r, bool):
            raise MiterError("legal-input predicate returned a non-bool")
        table.append(1 if r else 0)
    n = len(table)
    support = []
    for j in range(total):
        s = 1 << j
        if s <= n // (2 * s):
            invariant = all(table[r::2 * s] == table[r + s::2 * s] for r in range(s))
        else:
            invariant = all(table[k:k + s] == table[k + s:k + 2 * s] for k in range(0, n, 2 * s))
        if not invariant:
            support.append(j)

    def name(j: int) -> str:
        k, p, b = bits[j]
        return f"{p}[{b}]" if k == "i" else f"{out_prefix}{p}[{b}]"

    rows = []
    for assign in range(2 ** len(support)):
        idx = sum(((assign >> i) & 1) << j for i, j in enumerate(support))
        rows.append((assign, table[idx]))
    trues = [a for a, v in rows if v]
    if not trues:
        expr = "1'b0"
    elif len(trues) == len(rows):
        expr = "1'b1"
    else:
        use_false = len(trues) > len(rows) - len(trues)
        chosen = [a for a, v in rows if (not v) == use_false]
        terms = ["(" + " & ".join((name(j) if (a >> i) & 1 else f"~{name(j)}") for i, j in enumerate(support)) + ")"
                 for a in chosen]
        expr = " | ".join(terms)
        if use_false:
            expr = f"~({expr})"
    return {"expression": expr, "support": [name(j) for j in support], "domain_bits": total,
            "evaluations": n, "true_count": sum(table)}


# --- miter text ----------------------------------------------------------------------

def _decl(width: int) -> str:
    # Always an explicit range, so a bit-select such as `full[0]` is legal on 1-bit nets.
    return f"[{width - 1}:0] "


def wrapper(toplevel: str, input_widths: dict[str, int], output_widths: dict[str, int], mask: list,
            legal_expr: str) -> str:
    """The miter module `openvef_miter` (gold = null, gate = mutant)."""
    ins = ", ".join(f"input {_decl(w)}{p}" for p, w in sorted(input_widths.items()))
    lines = [f"module openvef_miter({ins}, output trigger, output legal);"]
    for side in ("gold", "gate"):
        for p, w in sorted(output_widths.items()):
            lines.append(f"  wire {_decl(w)}{side}_{p};")
        conns = [f".{p}({p})" for p in sorted(input_widths)] + [f".{p}({side}_{p})" for p in sorted(output_widths)]
        lines.append(f"  {toplevel}_{side} {side}_inst({', '.join(conns)});")
    terms = []
    for e in mask:
        p, w = e["signal"], e["when"]
        diff = f"(gold_{p} != gate_{p})"
        if w == "always":
            terms.append(diff)
        else:
            width = output_widths[w["null_signal"]]
            terms.append(f"((gold_{w['null_signal']} == {width}'b{w['equals']}) & {diff})")
    trigger = " | ".join(terms) if terms else "1'b0"
    lines.append(f"  assign trigger = {trigger};")
    lines.append(f"  assign legal = {legal_expr};")
    lines.append("endmodule")
    return "\n".join(lines) + "\n"


def _const(bits: str) -> str:
    return f"{len(bits)}'b{bits}"


def script(toplevel: str, design: dict, seq: int, timeout_s: int, show: list[str]) -> str:
    """One Yosys script: read both netlists, build the miter, prove trigger = 0 over `seq`
    steps (step 1 is the initial state and is skipped)."""
    reset = design["reset_sequence"]
    held = design.get("held_inputs") or {}
    sets = []
    for i, vec in enumerate(reset, start=1):
        if i > seq:
            break
        sets += [f"-set-at {i} {p} {_const(v)}" for p, v in sorted(vec.items())]
    for t in range(len(reset) + 1, seq + 1):
        sets += [f"-set-at {t} {p} {_const(v)}" for p, v in sorted(held.items())]
        sets.append(f"-set-at {t} legal 1")
    return "\n".join([
        "read_verilog -sv gold.v", f"hierarchy -top {toplevel}", f"rename {toplevel} {toplevel}_gold",
        "design -stash gold",
        "read_verilog -sv gate.v", f"hierarchy -top {toplevel}", f"rename {toplevel} {toplevel}_gate",
        "design -stash gate",
        f"design -copy-from gold -as {toplevel}_gold {toplevel}_gold",
        f"design -copy-from gate -as {toplevel}_gate {toplevel}_gate",
        "read_verilog -sv miter.v", "hierarchy -top openvef_miter", "proc", "flatten", "memory", "dffunmap",
        "opt_clean",
        f"sat -seq {seq} {' '.join(sets)} -set-init-zero -prove trigger 0 -prove-skip 1 -show-inputs "
        f"{' '.join('-show ' + s for s in show)} -timeout {timeout_s}",
    ]) + "\n"


_ROW = re.compile(r"^\s+(\d+)\s+\\(\S+)\s+\S+\s+\S+\s+([01xz]+)\s*$")


def parse_log(log: str) -> dict:
    """The sat verdict and, for a failure, the shown signals per step."""
    if "SAT proof finished - no model found: SUCCESS" in log:
        return {"result": "PROVED"}
    if "SAT proof finished - model found: FAIL" in log:
        steps: dict[int, dict[str, str]] = {}
        tail = log[log.index("SAT proof finished - model found: FAIL"):]
        for line in tail.splitlines():
            m = _ROW.match(line)
            if m:
                steps.setdefault(int(m.group(1)), {})[m.group(2)] = m.group(3)
        return {"result": "FAILED", "steps": steps}
    if "timed out" in log.lower() or "Interrupted SAT solver" in log:
        return {"result": "TIMEOUT"}
    return {"result": "UNKNOWN"}


def bounded_check(null_netlist: str, mutant_netlist: str, design: dict, mask: list, legal_expr: str,
                  n_cycles: int, *, run_yosys: Callable[[dict, list, float], dict], solver_timeout_s: int,
                  wall_timeout_s: float) -> dict:
    """L293-L297 for one mutant. `n_cycles` is N: driver cycles after reset release
    (N ≤ cycle cap); rows 0 .. len(reset)-1+N are compared.

    `run_yosys(files, scripts, timeout_s)` is the harness `yosys` task. The full bound is
    checked first; on a failure, ascending bounds find the shortest counterexample."""
    if n_cycles > design["cycle_cap"]:
        raise MiterError("L293: N must be no greater than the design cycle cap")
    toplevel = design["toplevel"]
    outputs = {p: None for p in design["output_ports"]}
    widths = design["output_widths"]  # from the null netlist's interface (harness task `interface`)
    inputs = {**design["input_ports"], **{p: len(v) for p, v in (design.get("held_inputs") or {}).items()}}
    files = {"gold.v": null_netlist, "gate.v": mutant_netlist,
             "miter.v": wrapper(toplevel, inputs, widths, mask, legal_expr)}
    reset_len = len(design["reset_sequence"])
    seq = reset_len + n_cycles + 1
    show = ["trigger", "legal"] + [f"gold_{p}" for p in sorted(outputs)] + [f"gate_{p}" for p in sorted(outputs)]
    record: dict[str, Any] = {"N": n_cycles, "seq_steps": seq, "solver": "yosys sat (minisat), D-007 (3)",
                              "solver_timeout_s": solver_timeout_s, "miter_verilog": files["miter.v"]}
    full = run_yosys(files, [script(toplevel, design, seq, solver_timeout_s, show)], wall_timeout_s)
    record["yosys_version"] = full.get("yosys_version")
    first = _verdict(full)
    if first["result"] == "PROVED":
        return {**record, "label": BOUNDED_EQUIVALENT}
    if first["result"] != "FAILED":
        return {**record, "label": UNDECIDED, "reason": first["result"]}
    trigger_step = min(t for t, s in first["steps"].items() if s.get("trigger") == "1")
    # shortest: the smallest sequence length that fails
    scripts = [script(toplevel, design, k, solver_timeout_s, show) for k in range(2, trigger_step)]
    shortest = first
    if scripts:
        res = run_yosys(files, scripts, wall_timeout_s)
        for run in res["runs"]:
            v = parse_log(run.get("log", "")) if run.get("returncode") == 0 else {"result": "ERROR"}
            if v["result"] == "FAILED":
                shortest = v
                break
            if v["result"] != "PROVED":
                return {**record, "label": UNDECIDED, "reason": f"shortest-counterexample search: {v['result']}"}
    step = min(t for t, s in shortest["steps"].items() if s.get("trigger") == "1")
    in_names = sorted(inputs)
    schedule = [{p: shortest["steps"][t][p] for p in in_names} for t in range(1, step + 1)]
    return {**record, "label": NON_EQUIVALENT, "counterexample": {
        "trigger_step": step, "predicted_masked_divergence_row": step - 2, "length_cycles": step - 2 - (reset_len - 1),
        "inputs_by_step": schedule,
        "gold_outputs_at_trigger": {p: shortest["steps"][step][f"gold_{p}"] for p in sorted(outputs)},
        "gate_outputs_at_trigger": {p: shortest["steps"][step][f"gate_{p}"] for p in sorted(outputs)}}}


def _verdict(res: dict) -> dict:
    if "runs" not in res or not res["runs"]:
        return {"result": "ERROR"}
    run = res["runs"][0]
    if run.get("timed_out"):
        return {"result": "TIMEOUT"}
    if run.get("returncode") != 0:
        return {"result": "ERROR", "detail": run.get("stderr")}
    return parse_log(run["log"])


# --- H6: replay ------------------------------------------------------------------------

def replay_driver(cex: dict, design: dict) -> str:
    """A fixed-schedule driver (harness machinery, not a control artifact) that applies the
    counterexample's post-reset inputs through the production harness, then COMPLETE."""
    reset_len = len(design["reset_sequence"])
    held = set(design.get("held_inputs") or {})
    vectors = [{p: v for p, v in step.items() if p not in held} for step in cex["inputs_by_step"][reset_len:]]
    return ("class Driver:\n"
            f"    SCHEDULE = {tuple(vectors)!r}\n\n"
            "    def step(self, cycle_index, outputs_after_edge):\n"
            "        if cycle_index < len(self.SCHEDULE):\n"
            "            return dict(self.SCHEDULE[cycle_index])\n"
            "        return 'COMPLETE'\n\n\n"
            "def create_driver(seed):\n"
            "    return Driver()\n")


def replay_agrees(cex: dict, pair: dict) -> dict:
    """F4: the simulator's first masked divergence is at the predicted row."""
    predicted = cex["predicted_masked_divergence_row"]
    return {"predicted_row": predicted, "observed_row": pair.get("first_masked_row"),
            "agrees": pair.get("first_masked_row") == predicted}
