#!/usr/bin/env python3
"""Routing eval: does an agent pick the correct skill on a confusable prompt?

Arms:
  descriptions   the 17 skill frontmatter descriptions only (what a bare skill list shows)
  router         AGENTS.md router + disambiguation table + the descriptions

Measures whether the architectural work (negative boundaries + router) actually
prevents mis-routing, and reports which wrong skill was chosen when it fails.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

# Repo root, derived from this file's location (evals/<suite>/run_*.py) so the harness
# runs from any checkout. Override with INFISICAL_SKILLS_REPO if run from elsewhere.
REPO = pathlib.Path(
    os.environ.get("INFISICAL_SKILLS_REPO") or pathlib.Path(__file__).resolve().parents[2]
)
if not (REPO / "skills").is_dir():
    sys.exit(
        f"error: {REPO} is not an infisical-ai-skills checkout "
        "(no skills/ directory). Set INFISICAL_SKILLS_REPO."
    )
HERE = pathlib.Path(__file__).parent
SPEC = json.loads((HERE / "routing_spec.json").read_text())
OUT = HERE / "routing_runs"
OUT.mkdir(exist_ok=True)
MODEL = "sonnet"
NO_TOOLS = ["--disallowedTools", "WebSearch", "WebFetch", "Read", "Glob", "Grep",
            "Bash", "Task", "Agent", "NotebookEdit", "Write", "Edit"]
ARMS = ("descriptions", "router")


def skill_descriptions() -> str:
    rows = []
    for p in sorted((REPO / "skills").iterdir()):
        if not p.is_dir():
            continue
        fm = (p / "SKILL.md").read_text().split("---")[1]
        m = re.search(r'description:\s*"?(.*?)"?\s*(?:\ntriggers:|\n[a-z_]+:|\Z)', fm, re.S)
        desc = " ".join(m.group(1).split()) if m else ""
        rows.append(f"- **{p.name}**: {desc}")
    return "\n".join(rows)


DESCS = skill_descriptions()
ROUTER = (REPO / "AGENTS.md").read_text()

PROMPT = """You are choosing which Agent Skill to load in order to answer a user's question about
Infisical. Below are the available skills.

{context}

USER QUESTION:
{q}

Reply with ONLY the name of the single most appropriate skill, exactly as written above.
No explanation."""


def run(prompt: str) -> tuple[str, float]:
    t0 = time.time()
    try:
        p = subprocess.run(["claude", "-p", prompt, "--model", MODEL] + NO_TOOLS,
                           capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return "__TIMEOUT__", round(time.time() - t0, 1)
    return (p.stdout if p.returncode == 0 else f"__ERR__ {p.stderr[:300]}",
            round(time.time() - t0, 1))


def pick(resp: str) -> str:
    found = re.findall(r"infisical-[a-z-]+", resp)
    return found[-1].rstrip("-") if found else "__NONE__"


def do(case: dict, arm: str) -> dict:
    ctx = (f"AVAILABLE SKILLS:\n{DESCS}" if arm == "descriptions"
           else f"{ROUTER}\n\nSKILL DESCRIPTIONS:\n{DESCS}")
    resp, dur = run(PROMPT.format(context=ctx, q=case["prompt"]))
    chosen = pick(resp)
    ok = chosen == case["expect"]
    d = OUT / f"case-{case['id']}-{case['name']}" / arm
    d.mkdir(parents=True, exist_ok=True)
    (d / "response.txt").write_text(resp)
    (d / "result.json").write_text(json.dumps(
        {"expected": case["expect"], "chosen": chosen, "correct": ok,
         "confusable_with": case["confusable_with"], "duration_seconds": dur}, indent=2))
    flag = "OK " if ok else "BAD"
    print(f"  {flag} {arm:13s} case-{case['id']:<2} {case['name']:34s} "
          f"-> {chosen}{'' if ok else '  (want ' + case['expect'] + ')'}", flush=True)
    return {"id": case["id"], "name": case["name"], "arm": arm,
            "expected": case["expect"], "chosen": chosen, "correct": ok,
            "confusable_with": case["confusable_with"]}


def main():
    only = [a for a in sys.argv[1:] if a.isdigit()] or None
    cases = [c for c in SPEC["cases"] if not only or str(c["id"]) in only]
    jobs = [(c, a) for c in cases for a in ARMS]
    print(f"Routing eval: {len(jobs)} jobs ({len(cases)} cases x {len(ARMS)} arms)\n", flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        res = list(pool.map(lambda j: do(*j), jobs))
    (OUT / "raw_results.json").write_text(json.dumps(res, indent=2))
    print("\n=== SUMMARY ===")
    for arm in ARMS:
        rs = [r for r in res if r["arm"] == arm]
        c = sum(r["correct"] for r in rs)
        print(f"{arm:13s} {c}/{len(rs)} = {c/len(rs)*100:5.1f}%")
    print("\nMis-routes:")
    for r in res:
        if not r["correct"]:
            print(f"  [{r['arm']}] {r['name']}: chose {r['chosen']}, wanted {r['expected']}")


if __name__ == "__main__":
    main()
