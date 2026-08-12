#!/usr/bin/env python3
"""Three-arm A/B/C eval harness for infisical-ai-skills accuracy audit.

Arms:
  baseline    bare prompt, no skill
  old_skill   the skill as committed on `main` (pre-audit)
  new_skill   the corrected skill on this branch

Tools are disabled so all three arms test model knowledge + provided context only.
A skill that can send the model to look things up would mask whether the skill text
itself is correct.

Grading is deterministic regex. Negative ("must_not_match") assertions are evaluated
against the response with counter-example lines stripped, because a correct answer
legitimately quotes the wrong form in order to warn against it.
"""
import json
import pathlib
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

REPO = pathlib.Path("/Users/jakehulberg/Documents/infisical-ai-skills")
SCRATCH = pathlib.Path(__file__).parent
SPEC = json.loads((SCRATCH / "eval_spec.json").read_text())
OUT = SCRATCH / "runs"
OUT.mkdir(exist_ok=True)
MODEL = "sonnet"
BASE_REF = "main"
NO_TOOLS = ["--disallowedTools", "WebSearch", "WebFetch", "Read", "Glob", "Grep",
            "Bash", "Task", "Agent", "NotebookEdit", "Write", "Edit"]

ARMS = ("baseline", "old_skill", "new_skill")

SKILL_PREAMBLE = (
    "You have the following Agent Skill loaded. Treat it as authoritative reference "
    "material for Infisical and follow it over your own prior assumptions.\n\n"
    "===== BEGIN SKILL =====\n{body}\n===== END SKILL =====\n\n"
)

# Lines that present something as incorrect - excluded before negative matching.
COUNTER = re.compile(
    r"wrong|incorrect|don't|do not|never|avoid|deprecat|legacy|mistake|instead of|"
    r"not\s+(valid|supported|paginated|the)|there is no|rather than|fails|unsupported|"
    r"❌|⚠|no longer|isn't|is not|doesn't|does not|misconfigur|trip",
    re.IGNORECASE,
)


def strip_counter_examples(text: str) -> str:
    return "\n".join(l for l in text.splitlines() if not COUNTER.search(l))


def load_skill(skill: str, files: list[str], ref: str | None) -> str:
    parts = []
    for rel in files:
        rp = f"skills/{skill}/{rel}"
        if ref is None:
            body = (REPO / rp).read_text()
        else:
            body = subprocess.run(["git", "-C", str(REPO), "show", f"{ref}:{rp}"],
                                  capture_output=True, text=True, check=True).stdout
        parts.append(f"--- FILE: {rp} ---\n{body}")
    return "\n\n".join(parts)


def run_claude(prompt: str) -> tuple[str, float]:
    t0 = time.time()
    try:
        proc = subprocess.run(["claude", "-p", prompt, "--model", MODEL] + NO_TOOLS,
                              capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        return "__ERROR__ timeout", round(time.time() - t0, 1)
    dur = round(time.time() - t0, 1)
    if proc.returncode != 0:
        return f"__ERROR__ rc={proc.returncode}\n{proc.stderr[:2000]}", dur
    return proc.stdout, dur


def grade(response: str, assertions: list[dict]) -> dict:
    clean = strip_counter_examples(response)
    results = []
    for a in assertions:
        ev, ok = [], True
        for pat in a.get("must_match", []):
            m = re.search(pat, response, re.MULTILINE)
            if m:
                ev.append(f"OK required /{pat}/ -> {m.group(0)[:100]!r}")
            else:
                ok = False
                ev.append(f"MISSING required /{pat}/")
        for pat in a.get("must_not_match", []):
            m = re.search(pat, clean, re.MULTILINE)
            if m:
                ok = False
                ev.append(f"FOUND forbidden /{pat}/ -> {m.group(0)[:100]!r}")
            else:
                ev.append(f"OK absent /{pat}/")
        results.append({"text": a["text"], "passed": ok, "evidence": " | ".join(ev)})
    passed = sum(r["passed"] for r in results)
    return {
        "expectations": results,
        "summary": {"passed": passed, "failed": len(results) - passed,
                    "total": len(results),
                    "pass_rate": round(passed / len(results), 4) if results else 0.0},
    }


def do_one(ev: dict, arm: str) -> dict:
    prompt = ev["prompt"]
    if arm != "baseline":
        ref = BASE_REF if arm == "old_skill" else None
        prompt = SKILL_PREAMBLE.format(
            body=load_skill(ev["skill"], ev["skill_files"], ref)) + prompt
    resp, dur = run_claude(prompt)
    g = grade(resp, ev["assertions"])
    g["timing"] = {"total_duration_seconds": dur}
    d = OUT / f"eval-{ev['eval_id']}-{ev['eval_name']}" / arm / "run-1"
    (d / "outputs").mkdir(parents=True, exist_ok=True)
    (d / "outputs" / "response.md").write_text(resp)
    (d / "grading.json").write_text(json.dumps(g, indent=2))
    (d / "timing.json").write_text(json.dumps(
        {"total_duration_seconds": dur, "response_chars": len(resp), "model": MODEL},
        indent=2))
    (OUT / f"eval-{ev['eval_id']}-{ev['eval_name']}" / "eval_metadata.json").write_text(
        json.dumps({
            "eval_id": ev["eval_id"], "eval_name": ev["eval_name"], "skill": ev["skill"],
            "skill_files": ev["skill_files"], "prompt": ev["prompt"],
            "assertions": [a["text"] for a in ev["assertions"]],
            "arms": list(ARMS), "model": MODEL, "tools": "disabled",
            "grading": "deterministic regex; negative assertions ignore counter-example lines",
        }, indent=2))
    print(f"  {arm:10s} eval-{ev['eval_id']} {ev['eval_name']:42s} "
          f"{g['summary']['passed']}/{g['summary']['total']} ({dur}s)", flush=True)
    return {"eval_id": ev["eval_id"], "eval_name": ev["eval_name"],
            "skill": ev["skill"], "arm": arm, **g["summary"]}


def regrade() -> None:
    """Re-grade already-saved responses without re-invoking the model."""
    results = []
    for ev in SPEC["evals"]:
        base = OUT / f"eval-{ev['eval_id']}-{ev['eval_name']}"
        for arm in ARMS:
            rp = base / arm / "run-1" / "outputs" / "response.md"
            if not rp.exists():
                continue
            g = grade(rp.read_text(), ev["assertions"])
            old = json.loads((base / arm / "run-1" / "grading.json").read_text())
            g["timing"] = old.get("timing", {})
            (base / arm / "run-1" / "grading.json").write_text(json.dumps(g, indent=2))
            print(f"  {arm:10s} eval-{ev['eval_id']} {ev['eval_name']:42s} "
                  f"{g['summary']['passed']}/{g['summary']['total']}")
            results.append({"eval_id": ev["eval_id"], "eval_name": ev["eval_name"],
                            "skill": ev["skill"], "arm": arm, **g["summary"]})
    (OUT / "raw_results.json").write_text(json.dumps(results, indent=2))
    print("\n=== SUMMARY (regraded) ===")
    for arm in ARMS:
        rs = [r for r in results if r["arm"] == arm]
        if not rs:
            continue
        p, t = sum(r["passed"] for r in rs), sum(r["total"] for r in rs)
        print(f"{arm:10s} {p:3d}/{t:3d} = {p/t*100:5.1f}%")


def main():
    if "--regrade" in sys.argv:
        regrade()
        return
    only = [a for a in sys.argv[1:] if a.isdigit()] or None
    evals = [e for e in SPEC["evals"] if not only or str(e["eval_id"]) in only]
    jobs = [(e, arm) for e in evals for arm in ARMS]
    print(f"Running {len(jobs)} jobs ({len(evals)} evals x {len(ARMS)} arms), "
          f"model={MODEL}, tools disabled\n", flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda j: do_one(*j), jobs))
    (OUT / "raw_results.json").write_text(json.dumps(results, indent=2))
    print("\n=== SUMMARY ===")
    for arm in ARMS:
        rs = [r for r in results if r["arm"] == arm]
        p, t = sum(r["passed"] for r in rs), sum(r["total"] for r in rs)
        print(f"{arm:10s} {p:3d}/{t:3d} = {p/t*100:5.1f}%")


if __name__ == "__main__":
    main()
