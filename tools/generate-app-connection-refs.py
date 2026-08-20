#!/usr/bin/env python3
"""Generate the factual App Connection reference files from the Infisical source.

Why this exists
---------------
The 2026-08 accuracy audit found that a skill whose facts have drifted performs *worse*
than no skill at all: stale specifics override correct model knowledge. Enum values,
credential field names, and route definitions are exactly the kind of fact that drifts.

So they are not hand-maintained here. They are derived from the Infisical repo, and
re-verification is `python3 tools/generate-app-connection-refs.py && git diff`.

Hand-written guidance (when to use which connection, permission advice, gotchas) stays in
the non-generated reference files. This script only emits facts.

Usage
-----
    python3 tools/generate-app-connection-refs.py [--infisical-repo PATH] [--check]

    --check   exit 1 if the generated output differs from what is on disk (for CI)

Outputs
-------
    skills/infisical-app-connections/references/credentials-by-connection.md
    skills/infisical-app-connections/references/api-surface.md
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from collections import defaultdict

DEFAULT_INFISICAL = pathlib.Path.home() / "documents" / "infisical"
SKILL_REFS = pathlib.Path("skills/infisical-app-connections/references")

# Endpoints registered for every connection by registerAppConnectionEndpoints().
GENERIC_URLS = {"/", "/available", "/:connectionId", "/connection-name/:connectionName",
                "/:connectionId/rotate-credentials", "/:connectionId/usage", "/options"}

# Deliberately no commit hash: the output must be a pure function of the facts, so an
# upstream commit that changes nothing we document produces no diff. The commit is
# reported on stdout instead, where it is useful without being churn.
BANNER = ("<!-- GENERATED FILE — do not edit by hand.\n"
          "     Source: tools/generate-app-connection-refs.py\n"
          "     Regenerate: python3 tools/generate-app-connection-refs.py -->\n\n")


# ----------------------------------------------------------------------------- parsing

def strip_comments(t: str) -> str:
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    return re.sub(r"^\s*//.*$", "", t, flags=re.M)


def balanced(text: str, start: int, open_ch="{", close_ch="}") -> str:
    """Return the substring from the first open_ch at/after start to its match."""
    i = text.find(open_ch, start)
    if i == -1:
        return ""
    depth = 0
    for j in range(i, len(text)):
        if text[j] == open_ch:
            depth += 1
        elif text[j] == close_ch:
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    return ""


def parse_connection_enum(root: pathlib.Path) -> list[tuple[str, str]]:
    """[(EnumKey, slug)] in declaration order."""
    t = (root / "backend/src/services/app-connection/app-connection-enums.ts").read_text()
    m = re.search(r"export enum AppConnection \{(.*?)\n\}", t, re.S)
    return re.findall(r"(\w+)\s*=\s*\"([^\"]+)\"", m.group(1))


def parse_name_map(root: pathlib.Path) -> dict[str, str]:
    t = (root / "backend/src/services/app-connection/app-connection-maps.ts").read_text()
    m = re.search(r"APP_CONNECTION_NAME_MAP[^=]*=\s*\{(.*?)\n\};", t, re.S)
    return dict(re.findall(r"\[AppConnection\.(\w+)\]:\s*\"([^\"]+)\"", m.group(1)))


def parse_fields(obj_src: str) -> list[tuple[str, bool]]:
    """[(fieldName, required)] from a z.object({...}) body, top level only."""
    body = obj_src[obj_src.find("{") + 1:obj_src.rfind("}")]
    out, depth, cur = [], 0, ""
    for ch in body:
        if ch in "({[":
            depth += 1
        elif ch in ")}]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur); cur = ""
        else:
            cur += ch
    out.append(cur)
    fields = []
    for chunk in out:
        m = re.match(r"\s*([a-zA-Z_][\w]*)\s*:", chunk)
        if not m:
            continue
        name = m.group(1)
        optional = ".optional()" in chunk or ".nullish()" in chunk or ".default(" in chunk
        fields.append((name, not optional))
    return fields


def resolve_schema(text: str, schema_name: str, depth: int = 0) -> list[tuple[str, bool]]:
    """Resolve a credentials schema name to its field list, following .merge()/z.union()."""
    if depth > 3:
        return []
    m = re.search(rf"(?:export\s+)?const\s+{re.escape(schema_name)}\s*=\s*", text)
    if not m:
        return []
    tail = text[m.end():]
    # z.union([...]) / z.discriminatedUnion(...): take the union of all member objects
    if tail.lstrip().startswith("z.union") or tail.lstrip().startswith("z.discriminatedUnion"):
        arr = balanced(tail, 0, "[", "]")
        order: list[str] = []
        states: dict[str, set[bool]] = {}
        n_members = 0
        for om in re.finditer(r"z\.object\(", arr):
            member = parse_fields(balanced(arr, om.end() - 1))
            if not member:
                continue
            n_members += 1
            for f, req in member:
                if f not in states:
                    states[f] = set(); order.append(f)
                states[f].add(req)
        out = []
        for f in order:
            st = states[f]
            if len(st) > 1:
                out.append((f, "conditional"))      # required in some branches only
            elif True in st and n_members > 1 and len(
                    [1 for om in re.finditer(r"z\.object\(", arr)]) > 1:
                # required in every branch it appears in; if it is absent from some
                # branch we cannot tell mechanically, so keep it as required
                out.append((f, True))
            else:
                out.append((f, next(iter(st))))
        return out
    # <Other>.merge(<Another>) or <Other>.pick/omit — follow the base name
    base = re.match(r"\s*([A-Z]\w+)\s*\.\s*(merge|pick|omit|extend)\s*\(", tail)
    if base:
        fields = resolve_schema(text, base.group(1), depth + 1)
        mm = re.search(r"\.merge\((\w+)\)", tail[:400])
        if mm:
            seen = {f for f, _ in fields}
            for f, req in resolve_schema(text, mm.group(1), depth + 1):
                if f not in seen:
                    fields.append((f, req))
        return fields
    if tail.lstrip().startswith("z.object"):
        return parse_fields(balanced(tail, 0))
    # bare alias: `const A = B;`
    alias = re.match(r"\s*([A-Z]\w+)\s*[;\n]", tail)
    if alias:
        return resolve_schema(text, alias.group(1), depth + 1)
    return []


# Connections live under one of these roots. Filenames are inconsistent: some use
# `-connection-schemas.ts`, some `-connection-schema.ts`; likewise enums/enum.
CONNECTION_ROOTS = ("backend/src/services/app-connection",
                    "backend/src/ee/services/app-connections")
# Slugs whose source directory is named differently.
SLUG_DIR_ALIASES = {"hashicorp-vault": "hc-vault"}
# Schemas shared across connections (e.g. the SQL username-and-password base).
SHARED_GLOBS = ("backend/src/services/app-connection/shared/*/*-connection-schemas.ts",)


def connection_dir(root: pathlib.Path, slug: str) -> pathlib.Path | None:
    for name in (slug, SLUG_DIR_ALIASES.get(slug, slug)):
        for base in CONNECTION_ROOTS:
            d = root / base / name
            if d.is_dir():
                return d
    return None


def parse_methods_and_credentials(root: pathlib.Path, slug: str) -> list[tuple[str, list]]:
    """[(methodValue, [(field, required)])] for one connection."""
    d = connection_dir(root, slug)
    if d is None:
        return []
    schema_f = (next(iter(sorted(d.glob("*-connection-schema*.ts"))), None)
                or next(iter(sorted(d.glob("*-schema*.ts"))), None))
    if not schema_f:
        return []
    # Append shared schema sources so cross-file bases (e.g. BaseSqlUsernameAndPassword...) resolve.
    text = strip_comments(schema_f.read_text())
    for g in SHARED_GLOBS:
        for sf in root.glob(g):
            text += "\n" + strip_comments(sf.read_text())

    # methodEnumKey -> value, from the connection's own enums file
    enum_vals: dict[str, str] = {}
    enum_files = sorted(d.glob("*-connection-enum*.ts")) or sorted(d.glob("*-enum*.ts"))
    for ef in enum_files:
        for em in re.finditer(r"export enum (\w*ConnectionMethod) \{(.*?)\n\}", ef.read_text(), re.S):
            enum_vals.update(dict(re.findall(r"(\w+)\s*=\s*\"([^\"]+)\"", em.group(2))))

    results: list[tuple[str, list]] = []
    vm = re.search(r"Validate\w*ConnectionCredentialsSchema\s*=\s*z\.discriminatedUnion\(", text)
    if vm:
        arr = balanced(text, vm.end() - 1, "[", "]")
        for obj in re.finditer(r"z\.object\(", arr):
            blk = balanced(arr, obj.end() - 1)
            meth = re.search(r"method:\s*z\s*\.\s*literal\(\s*\w+\.(\w+)", blk) or \
                   re.search(r"method:\s*z[\s\S]{0,120}?\.literal\(\s*\w+\.(\w+)", blk)
            cred = re.search(r"credentials:\s*(\w+)", blk)
            if not meth:
                continue
            mval = enum_vals.get(meth.group(1), meth.group(1))
            fields = resolve_schema(text, cred.group(1)) if cred else []
            results.append((mval, fields))
    if not results:
        # single-method connection: find any *CredentialsSchema and pair with its methods
        cand = re.findall(r"export const (\w*?Credentials\w*Schema)\s*=", text)
        prefer = [c for c in cand if "Input" in c] or [c for c in cand if "Output" not in c] or cand
        fields = resolve_schema(text, prefer[0]) if prefer else []
        for mval in (enum_vals.values() or ["(see docs)"]):
            results.append((mval, fields))
    return results


def parse_routers(root: pathlib.Path) -> dict[str, list[dict]]:
    """slug -> [ {method,url,operationId,auth,query,response} ] for non-generic endpoints."""
    out: dict[str, list[dict]] = defaultdict(list)
    for base in ("backend/src/server/routes/v1/app-connection-routers",
                 "backend/src/ee/routes/v1/app-connection-routers"):
        d = root / base
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*-connection-router.ts")):
            slug = f.name.replace("-connection-router.ts", "")
            if slug == "app-connection":
                continue
            text = f.read_text()
            for blk in text.split("server.route({")[1:]:
                um = re.search(r"url:\s*[`\"]([^`\"]+)[`\"]", blk)
                if not um or um.group(1) in GENERIC_URLS:
                    continue
                am = re.search(r"verifyAuth\(\[([^\]]+)\]", blk)
                auth = sorted(re.findall(r"AuthMode\.(\w+)", am.group(1))) if am else []
                q = re.search(r"querystring:\s*z\.object\(", blk)
                qf = [f for f, _ in parse_fields(balanced(blk, q.end() - 1))] if q else []
                r200 = re.search(r"200:\s*z\.object\(", blk)
                rf = [f for f, _ in parse_fields(balanced(blk, r200.end() - 1))] if r200 else []
                op = re.search(r"operationId:\s*\"([^\"]+)\"", blk)
                mm = re.search(r"method:\s*\"(\w+)\"", blk)
                out[slug].append({
                    "method": mm.group(1) if mm else "GET",
                    "url": um.group(1).replace(":connectionId", "{connectionId}"),
                    "operationId": op.group(1) if op else "",
                    "auth": auth, "query": qf, "response": rf,
                })
    return out


def parse_consumers(root: pathlib.Path) -> dict[str, list[str]]:
    """slug -> ['Secret Sync: X', 'Rotation: Y', 'PKI Sync: Z'] via the *_CONNECTION_MAPs."""
    key_to_slug = dict(parse_connection_enum(root))
    out: dict[str, list[str]] = defaultdict(list)
    specs = [
        ("Secret Sync", "backend/src/services/secret-sync/secret-sync-maps.ts",
         "SECRET_SYNC_CONNECTION_MAP", r"\[SecretSync\.(\w+)\]:\s*AppConnection\.(\w+)",
         "backend/src/services/secret-sync/secret-sync-maps.ts", "SECRET_SYNC_NAME_MAP",
         r"\[SecretSync\.(\w+)\]:\s*\"([^\"]+)\""),
        ("Rotation", "backend/src/ee/services/secret-rotation-v2/secret-rotation-v2-maps.ts",
         "SECRET_ROTATION_CONNECTION_MAP", r"\[SecretRotation\.(\w+)\]:\s*AppConnection\.(\w+)",
         "backend/src/ee/services/secret-rotation-v2/secret-rotation-v2-maps.ts",
         "SECRET_ROTATION_NAME_MAP", r"\[SecretRotation\.(\w+)\]:\s*\"([^\"]+)\""),
        ("PKI Sync", "backend/src/services/pki-sync/pki-sync-maps.ts",
         "PKI_SYNC_CONNECTION_MAP", r"\[PkiSync\.(\w+)\]:\s*AppConnection\.(\w+)",
         "backend/src/services/pki-sync/pki-sync-maps.ts", "PKI_SYNC_NAME_MAP",
         r"\[PkiSync\.(\w+)\]:\s*\"([^\"]+)\""),
        ("Scanning source", "backend/src/ee/services/secret-scanning-v2/secret-scanning-v2-maps.ts",
         "SECRET_SCANNING_DATA_SOURCE_CONNECTION_MAP",
         r"\[SecretScanningDataSource\.(\w+)\]:\s*AppConnection\.(\w+)", None, None, None),
    ]
    for label, cpath, cvar, cpat, npath, nvar, npat in specs:
        cf = root / cpath
        if not cf.is_file():
            continue
        ct = cf.read_text()
        cm = re.search(rf"{cvar}[^=]*=\s*\{{(.*?)\n\}};", ct, re.S)
        if not cm:
            continue
        names = {}
        if npath and nvar:
            nm = re.search(rf"{nvar}[^=]*=\s*\{{(.*?)\n\}};", (root / npath).read_text(), re.S)
            if nm:
                names = dict(re.findall(npat, nm.group(1)))
        for feat_key, conn_key in re.findall(cpat, cm.group(1)):
            slug = key_to_slug.get(conn_key)
            if slug:
                out[slug].append(f"{label}: {names.get(feat_key, feat_key)}")
    return out


# ---------------------------------------------------------------------------- emitting

def emit_credentials(conns, namemap, creds) -> str:
    L = [BANNER]
    L.append("# Credential Fields by Connection\n\n")
    L.append(f"Every one of the **{len(conns)}** App Connection types, with the exact `method` "
             "values it accepts and the `credentials` fields each method requires.\n\n")
    L.append("`POST /api/v1/app-connections/<slug>` with body "
             "`{ name, method, credentials: { ... } }`. See "
             "[api-surface.md](./api-surface.md) for the full request shape.\n\n")
    L.append("| Notation | Meaning |\n|---|---|\n"
             "| **`bold`** | Required |\n"
             "| `plain` | Optional — has `.optional()`, `.nullish()`, or a default |\n"
             "| `plain`\u00b9 | **Conditional** — required in some variants of the schema only |\n\n"
             "\u00b9 A conditional field is required by one branch of a union and optional in "
             "another. The clearest case is GitHub: `host` is required when "
             "`instanceType` is `server` and optional when it is `cloud`. Read the connection's own "
             "page under `docs/integrations/app-connections/` before assuming which applies.\n\n")
    L.append("Where a method shows *(see per-connection docs)*, the schema could not be resolved "
             "mechanically — check `docs/integrations/app-connections/<slug>` rather than guessing.\n\n")
    L.append("---\n\n")
    for key, slug in conns:
        L.append(f"## {namemap.get(key, key)} — `{slug}`\n\n")
        rows = creds.get(slug) or []
        if not rows:
            L.append("*(see per-connection docs)*\n\n")
            continue
        L.append("| `method` | `credentials` fields |\n|---|---|\n")
        for meth, fields in rows:
            if fields:
                def cell(f, req):
                    if req == "conditional":
                        return f"`{f}`\u00b9"
                    return f"**`{f}`**" if req else f"`{f}`"
                cells = ", ".join(cell(f, req) for f, req in fields)
            else:
                cells = "*(see per-connection docs)*"
            L.append(f"| `{meth}` | {cells} |\n")
        L.append("\n")
    return "".join(L)


def emit_api_surface(conns, namemap, routers, consumers) -> str:
    all_eps = [(s, e) for s, eps in routers.items() for e in eps]
    usable = [(s, e) for s, e in all_eps if "IDENTITY_ACCESS_TOKEN" in e["auth"]]
    ui_only = [(s, e) for s, e in all_eps if "IDENTITY_ACCESS_TOKEN" not in e["auth"]]
    L = [BANNER]
    L.append(f"""# App Connection API Surface

Two distinct groups of endpoints, and the difference decides whether you can automate against them.

| Group | Count | Accepts a machine identity token? |
|---|---|---|
| Per-connection CRUD | 9 per connection | **8 of 9** — `/usage` is JWT-only |
| Resource-discovery endpoints | {len(all_eps)} total | **{len(usable)} yes, {len(ui_only)} no** |

**{len(ui_only)} of the {len(all_eps)} discovery endpoints are `AuthMode.JWT` only.** JWT means a
logged-in user session. A machine identity access token is rejected. Many of their router files
carry the comment *"The below endpoints are not exposed and for Infisical App use"* — they exist to
populate dropdowns in the Infisical UI, not as a public API.

Do not write automation against a JWT-only endpoint. See
[What to do instead](#what-to-do-instead-of-a-jwt-only-endpoint).

---

## Per-connection CRUD

Every connection type gets the same **nine** routes under `/api/v1/app-connections/<slug>`.
Eight accept a machine identity access token; `/usage` does not:

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/` | identity + JWT | List connections of this type |
| `GET` | `/available` | identity + JWT | List connections usable in the caller's context |
| `GET` | `/{{connectionId}}` | identity + JWT | Get one by ID |
| `GET` | `/connection-name/{{connectionName}}` | identity + JWT | Get one **by name** |
| `POST` | `/` | identity + JWT | Create |
| `PATCH` | `/{{connectionId}}` | identity + JWT | Update |
| `DELETE` | `/{{connectionId}}` | identity + JWT | Delete |
| `POST` | `/{{connectionId}}/rotate-credentials` | identity + JWT | Rotate the connection's own stored credential |
| `GET` | `/{{connectionId}}/usage` | **JWT only** | What consumes this connection |

`GET /connection-name/{{connectionName}}` is the one worth knowing: it lets automation resolve a
connection by its stable name instead of storing a UUID.

`/usage` is JWT-only. To find what consumes a connection from automation, list the syncs, rotations,
and PKI syncs and filter by `connectionId`.

### Create

```bash
curl -X POST 'https://us.infisical.com/api/v1/app-connections/<slug>' \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "name": "prod-aws",
    "method": "<one of the connection'"'"'s methods>",
    "credentials": {{ }}
  }}'
```

Per-connection `method` values and `credentials` fields:
[credentials-by-connection.md](./credentials-by-connection.md).

Optional body fields — several are hard errors on connections that do not support them:
`description` (max 256), `projectId`, `gatewayId`, `gatewayPoolId`,
`isPlatformManagedCredentials`, `isAutoRotationEnabled`, `rotation`.

---

## Discovery endpoints you can call programmatically

Only these **{len(usable)}** accept a machine identity access token.

| Connection | Endpoint | Returns | Query params |
|---|---|---|---|
""")
    for s, e in sorted(usable, key=lambda x: (x[0], x[1]["url"])):
        rv = ", ".join(f"`{r}`" for r in e["response"]) or "—"
        qv = ", ".join(f"`{q}`" for q in e["query"]) or "—"
        L.append(f"| `{s}` | `{e['method']} /api/v1/app-connections/{s}{e['url']}` | {rv} | {qv} |\n")
    L.append(f"""
---

## What to do instead of a JWT-only endpoint

You need a resource identifier — a vault ID, a repository slug, a cluster ID — to fill in a sync's
`destinationConfig` or a rotation's `parameters`. The Infisical endpoint that lists them is
UI-only. Three options, in order of preference:

1. **Ask the third-party provider directly.** The AWS SDK lists KMS keys; the Bitbucket API lists
   repositories; the 1Password CLI lists vaults. This is the correct automation path — Infisical is
   not the system of record for another provider's resources.
2. **Read the value out of the Infisical UI once** and commit it to your configuration. Resource
   IDs are stable; a vault ID does not change.
3. **Create the sync in the UI once**, then `GET` it through the API to see the exact
   `destinationConfig` the UI produced, and template your automation on that. This is the fastest
   way to get an unfamiliar destination config right.

Option 3 is usually the best answer when someone is stuck on an unfamiliar destination.

---

## All discovery endpoints

`identity` = callable with a machine identity token. `JWT only` = user session, UI-facing.

Each row also lists which features consume that connection, so you can see why the resource
matters.

""")
    for key, slug in conns:
        eps = routers.get(slug)
        if not eps:
            continue
        L.append(f"### {namemap.get(key, key)} — `{slug}`\n\n")
        cons = consumers.get(slug)
        if cons:
            L.append(f"Consumed by: {', '.join(sorted(cons))}\n\n")
        L.append("| Endpoint | Auth | Returns | Query params |\n|---|---|---|---|\n")
        for e in sorted(eps, key=lambda x: x["url"]):
            tag = "identity" if "IDENTITY_ACCESS_TOKEN" in e["auth"] else "**JWT only**"
            rv = ", ".join(f"`{r}`" for r in e["response"]) or "—"
            qv = ", ".join(f"`{q}`" for q in e["query"]) or "—"
            L.append(f"| `{e['method']} {e['url']}` | {tag} | {rv} | {qv} |\n")
        L.append("\n")
    no_disc = [(k, s) for k, s in conns if not routers.get(s)]
    L.append(f"### Connections with no discovery endpoints ({len(no_disc)})\n\n")
    L.append(", ".join(f"`{s}`" for _, s in no_disc) + "\n\n")
    L.append("For these, every value in a consumer's config comes from you or from the provider.\n")
    return "".join(L)


# -------------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--infisical-repo", type=pathlib.Path, default=DEFAULT_INFISICAL)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    root = a.infisical_repo.expanduser()
    if not (root / "backend/src/services/app-connection").is_dir():
        print(f"error: not an Infisical checkout: {root}", file=sys.stderr)
        return 2

    import subprocess
    commit = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip() or "unknown"

    conns = parse_connection_enum(root)
    namemap = parse_name_map(root)
    routers = parse_routers(root)
    consumers = parse_consumers(root)
    creds = {slug: parse_methods_and_credentials(root, slug) for _, slug in conns}

    outputs = {
        SKILL_REFS / "credentials-by-connection.md": emit_credentials(conns, namemap, creds),
        SKILL_REFS / "api-surface.md": emit_api_surface(conns, namemap, routers, consumers),
    }

    # coverage report — surfaces anything the parser could not resolve
    n_eps = sum(len(v) for v in routers.values())
    unresolved = [s for _, s in conns if not any(f for _, f in (creds.get(s) or []))]
    print(f"ground truth      {commit}")
    print(f"connections       {len(conns)}")
    print(f"discovery eps     {n_eps} "
          f"({sum(1 for v in routers.values() for e in v if 'IDENTITY_ACCESS_TOKEN' in e['auth'])} identity-callable)")
    print(f"credential fields resolved for {len(conns) - len(unresolved)}/{len(conns)} connections")
    if unresolved:
        print(f"  unresolved: {', '.join(unresolved)}")

    if a.check:
        drift = [str(p) for p, c in outputs.items() if not p.is_file() or p.read_text() != c]
        if drift:
            print("\nDRIFT — regenerate:\n  " + "\n  ".join(drift), file=sys.stderr)
            return 1
        print("\nup to date")
        return 0

    for p, c in outputs.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(c)
        print(f"wrote {p} ({len(c.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
