#!/usr/bin/env python3
"""Live view of one product's board and the loops running against it.

    python3 scripts/loop-dashboard.py [port]     # default 8787

Run it in the product repository. It reads what already exists - the board in
features/INDEX.md, the persisted loop state, loop processes, each feature's
loop.log and git - and renders on every request. The page refreshes itself every
10 seconds. The same process exposes the derived facts as a versioned, read-only
JSON API below /api/v1. It owns no database and accepts no write method.

/status is the other half and stays the other half: it reads the documents and
says what they mean, once, for somebody who was not there. This says what is
happening right now, and interprets nothing.
"""

import html
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

RUNGS = ["Roadmap", "Spec", "Designed", "Ready", "In Progress", "In Review", "Done", "Dropped"]
REFRESH_SECONDS = 10
API_VERSION = 1


def sh(*args, cwd=None):
    """Run a command, return stdout stripped, empty string on any failure."""
    try:
        out = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def board():
    """Rows of features/INDEX.md, as dicts. Column names differ per language, so
    the status is found by value and owner/branch are taken from the last two."""
    index = Path("features/INDEX.md")
    if not index.is_file():
        return []
    rows = []
    for line in index.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\|\s*[A-Z]+-\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        status = next((c for c in cells if c in RUNGS), "")
        if not status:
            continue  # some other table that happens to start with an ID, e.g. an AC list
        rest = cells[2:]
        # Headers are in the project's own language, so each column is recognised by
        # the shape of its values instead of by its name.
        rows.append({
            "id": cells[0],
            "name": cells[1] if len(cells) > 1 else "",
            "status": status,
            "prio": next((c for c in rest if re.fullmatch(r"P\d", c)), ""),
            "effort": next((c for c in rest if re.fullmatch(r"XS|S|M|L|XL", c)), ""),
            "wave": next((c for c in rest if re.fullmatch(r"\d{1,2}", c)), ""),
            "deps": next((c for c in rest if re.fullmatch(r"[A-Z]+-\d+(,\s*[A-Z]+-\d+)*", c)), ""),
            "owner": cells[-2] if len(cells) > 2 else "",
            "branch": cells[-1] if len(cells) > 1 else "",
        })
    return rows


# Most reports write the verdict in English even when the prose is not - the way the
# board's rungs are - but not all of them do, so the words a project actually uses
# are listed and mapped back to one name. Longest first, or "Approved" swallows
# "Approved with notes".
VERDICTS = {
    "review": {
        "Approved with notes": "Approved with notes",
        "Freigegeben mit Anmerkungen": "Approved with notes",
        "Changes required": "Changes required",
        "Änderungen erforderlich": "Changes required",
        "Approved": "Approved",
        "Freigegeben": "Approved",
    },
    "qa": {
        "Not production ready": "Not production ready",
        "Nicht produktionsreif": "Not production ready",
        "Ready with reservations": "Ready with reservations",
        "Produktionsreif mit Vorbehalten": "Ready with reservations",
        "Bedingt produktionsreif": "Ready with reservations",
        "Production ready": "Production ready",
        "Produktionsreif": "Production ready",
    },
}
VERDICT_HUE = {"Approved": "c-green", "Production ready": "c-green",
               "Approved with notes": "c-yellow", "Ready with reservations": "c-yellow",
               "Changes required": "c-red", "Not production ready": "c-red"}
SEVERITIES = ("Critical", "Major", "Minor", "Cosmetic", "Blocking", "Note", "Trivial",
              "Kritisch", "Schwer", "Gering", "Kosmetisch", "Blockierend", "Anmerkung")

# Reports write the severity into the finding's own heading, in their own language,
# often in bold and sometimes with a remark after it.
SEVERITY_WORDS = {"Critical": "Critical", "Kritisch": "Critical",
                  "Major": "Major", "Schwer": "Major",
                  "Minor": "Minor", "Gering": "Minor",
                  "Cosmetic": "Cosmetic", "Kosmetisch": "Cosmetic"}
IN_HEADING = re.compile(r"[·|]\s*\**\s*(" + "|".join(SEVERITY_WORDS) + r")\s*\**")


def doc(fid, name, branch="", worktrees=None):
    """Where a feature document actually is. They travel with the feature branch -
    /build and /review write them inside the worktree - so while a branch is open
    the copy on the default branch is the older one, or missing entirely."""
    d = feature_dir(fid)
    if not d:
        return None
    listing = worktrees if worktrees is not None else sh("git", "worktree", "list")
    for line in listing.splitlines():
        if branch and f"[{branch}]" in line:
            candidate = Path(line.split()[0]) / d / name
            if candidate.is_file():
                return candidate
    path = d / name
    return path if path.is_file() else None


def words(text):
    return {w for w in re.findall(r"[\wäöüß]{5,}", text.lower())}


# F for findings, N and A for notes: a report's other tables use other letters -
# S-12 is a source, and reading it as a finding put a citation on the board.
ROW = re.compile(r"^\|\s*\**([FNA]-\d+)\**([^|]*)\|([^|]*)\|(.*)$")


def outcome_rows(text):
    """Rows of a resolution table: what was done about a finding, and where.

    /build appends one under the report it worked, and a later /qa round opens by
    re-checking the round before it - the same shape either way."""
    rows = []
    for line in text.splitlines():
        row = ROW.match(line)
        if not row:
            continue
        label, did = row.group(2).strip(" *·\u2014"), row.group(3).strip(" *")
        sha = re.search(r"\b[0-9a-f]{7,40}\b", row.group(4))
        rows.append({"id": row.group(1), "label": label,
                     "did": "" if (re.search(r"\b(offen|open)\b", did, re.I) or
                                   not did.strip(" \u2014-*")) else did.split()[0].strip(" *·\u2014"),
                     "detail": did, "commit": sha.group(0) if sha else ""})
    return rows


def rounds(fid, branch="", worktrees=None):
    """How often each delivery stage has been attempted.

    New loops keep the count in persistent state while reports remain current
    snapshots. Fall back to old accumulated-report counting for earlier projects."""
    out = {}
    attempts = loop_state(fid).get("attempts", {})
    for kind in ("review", "qa"):
        path = doc(fid, f"{kind}.md", branch, worktrees)
        if path:
            if kind in attempts:
                found = int(attempts.get(kind, 0)) + 1
            else:
                found = len(
                    ROUND.findall(path.read_text(encoding="utf-8", errors="replace"))
                )
            if found:
                out[kind] = found
    return out


def carried(fid, branch="", worktrees=None):
    """Resolution rows that are not about the current findings - which means they are
    about the round before, and are the only place that says those were settled."""
    out = []
    for kind in ("review", "qa"):
        path = doc(fid, f"{kind}.md", branch, worktrees)
        if not path:
            continue
        text = last_round(path.read_text(encoding="utf-8", errors="replace"))
        current = {f["id"]: f["what"] for f in findings(fid, branch, worktrees)
                   if f["source"] == kind}
        for row in outcome_rows(text):
            mine = current.get(row["id"], "")
            if not (mine and (words(row["label"]) & words(mine))):
                out.append(dict(row, source=kind))
    return out


def findings(fid, branch="", worktrees=None):
    """The findings of review.md and qa.md, by their own numbering. Both write them
    as `### F-1 - what is wrong`, under a heading that says whether they block."""
    # /build appends its own table under a report - one row per finding, what it did
    # about it, and the commit - so a finding can say more than "found". It is the
    # builder's record and not a re-measurement, which is what the next round is for.
    # The table's columns differ between rounds and projects, so only two things are
    # read by position: the id opens the row, and what was done follows it. The
    # commit is found by its shape, wherever the row happens to keep it.
    worked = re.compile(r"^\|\s*\**([A-Z]-\d+)\**([^|]*)\|([^|]*)\|(.*)$")


    def words(text):
        return {w for w in re.findall(r"[\wäöüß]{5,}", text.lower())}

    out = []
    for kind in ("review", "qa"):
        path = doc(fid, f"{kind}.md", branch, worktrees)
        if not path:
            continue
        section, done = "", {}
        text = last_round(path.read_text(encoding="utf-8", errors="replace"))
        lines = text.splitlines()

        # Ids repeat between rounds - a round that re-checks the previous one lists
        # its F-1 next to this round's F-1 - so the id alone is not an identity. The
        # row carries the finding's own words too, and one word of five letters or
        # more in common is enough: "Fokus nach dem Speichern" and "Nach jedem
        # erfolgreichen Speichern verliert die Tastatur ihren Platz" share one and
        # are the same finding; a confidence dot and a sector error share none.
        for line in lines:
            row = worked.match(line)
            if row:
                label, did = row.group(2).strip(" *·\u2014"), row.group(3).strip(" *")
                sha = re.search(r"\b[0-9a-f]{7,40}\b", row.group(4))
                commit = sha.group(0) if sha else ""
                # "Code - how" and "Document - how" mean handled; only the word open,
                # or an empty cell, means it is not. The em dash is a separator here,
                # not a marker, and reading it as one marked everything unfixed.
                still_open = (re.search(r"\b(offen|open)\b", did, re.I) is not None
                              or not did.strip(" \u2014-*"))
                # The first word is the kind of resolution - fixed, resolved, code,
                # document - and the rest is the explanation, which belongs in the file.
                done[row.group(1)] = ("" if still_open else did.split()[0].strip(" *·\u2014"),
                                      commit, words(label))

        for line in lines:
            if line.startswith("## "):
                section = line[3:].lower()
            head = re.match(r"###\s+([A-Z]-\d+)\s*(?:\u2013|\u2014|-)\s*(.+)", line)
            if head:
                what = head.group(2).strip()
                # /qa writes one Findings section and puts the severity at the end of
                # the heading; /review splits blocking findings from notes by section.
                # Read the severity where it is stated and fall back to the section.
                found = list(IN_HEADING.finditer(what))
                severity = SEVERITY_WORDS[found[-1].group(1)] if found else ""
                if found:
                    what = what[:found[-1].start()].strip(" ·|*")
                note = (severity in ("Minor", "Cosmetic")) if severity else \
                    any(w in section for w in ("anmerkung", "note", "hinweis"))
                did, commit, said = done.get(head.group(1), ("", "", set()))
                # The row has to be about this finding, not about the one that held
                # the same id a round ago.
                if said and not (said & words(what)):
                    did, commit = "", ""
                out.append({"id": head.group(1), "what": what, "source": kind,
                            "note": note, "severity": severity,
                            "done": did, "commit": commit})
    return out


# /qa appends a second report under the first when a feature comes back, so a file
# can hold several rounds - each opening with its own verdict heading. Only the last
# one is the current state; the rest is history, and showing it doubles every
# finding under an id that now means something else.
# A round declares its verdict either as a heading or as a bold label on its own
# line - both forms are in use - and that declaration is where a round starts.
ROUND = re.compile(r"(?m)^(?:#{2,3}\s*\**\s*|\*\*)(?:Verdikt|Verdict|Urteil)\b")


def last_round(text):
    starts = [m.start() for m in ROUND.finditer(text)]
    return text[starts[-1]:] if starts else text


def report(fid, kind, branch="", worktrees=None):
    """The verdict and the severity counts of review.md or qa.md - the two facts that
    decide whether a feature ships, and the reason a marker saying only "this file
    exists" is not worth the ink."""
    path = doc(fid, f"{kind}.md", branch, worktrees)
    if not path:
        return {}
    text = last_round(path.read_text(encoding="utf-8", errors="replace"))[:20000]

    # Look where the verdict is declared, not wherever the words appear: a review
    # that says "nothing here meets the bar for Changes required" would otherwise be
    # read as requiring changes. Inside that region the last value wins, because /qa
    # appends its re-check ("Ready with reservations → Production ready") rather than
    # rewriting the first one.
    label = re.search(r"(?:Verdict|Urteil|Verdikt)\**:?\**", text)
    region = text[label.end():label.end() + 240] if label else text
    words = sorted(VERDICTS[kind], key=len, reverse=True)
    hits = [(region.rfind(v), VERDICTS[kind][v]) for v in words if v in region]
    if not hits:  # no label, or a wording we do not know: fall back to the document
        hits = [(-text.find(v), VERDICTS[kind][v]) for v in words if v in text]
    counts = {name: int(n) for name, n in
              # The count is sometimes followed by a remark - "2 (both carried over
              # from round one)" - and dropping the row for that hid a whole severity.
              re.findall(rf"\|\s*({'|'.join(SEVERITIES)})\s*\|\s*(\d+)[^|]*\|", text)}
    return {"verdict": max(hits)[1] if hits else "", "counts": counts,
            "findings": [f for f in findings(fid, branch, worktrees) if f["source"] == kind]}


def evidence_files(fid, branch="", worktrees=None):
    marker = doc(fid, "evidence", branch, worktrees)  # a directory, so doc() misses it
    folder = marker if marker else None
    if folder is None:
        d = feature_dir(fid)
        for line in (worktrees if worktrees is not None else sh("git", "worktree", "list")).splitlines():
            if branch and f"[{branch}]" in line and d:
                candidate = Path(line.split()[0]) / d / "evidence"
                if candidate.is_dir():
                    folder = candidate
        if folder is None and d and (d / "evidence").is_dir():
            folder = d / "evidence"
    return sorted(f.name for f in folder.iterdir()) if folder and folder.is_dir() else []


def spend(fid):
    """What the agents spent on this feature, from the log the loop already writes.
    One session per stage, and a session's last result carries its totals."""
    d = feature_dir(fid)
    log = d / "loop.log" if d else None
    if not log or not log.is_file():
        return {}
    per_session = {}
    for line in sh("grep", '"type":"result"', str(log)).splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        sid, turns = event.get("session_id", ""), event.get("num_turns", 0)
        if turns >= per_session.get(sid, {}).get("num_turns", -1):
            per_session[sid] = event
    if not per_session:
        return {}
    use = [e.get("usage") or {} for e in per_session.values()]
    return {
        "stages": len(per_session),
        "turns": sum(e.get("num_turns", 0) for e in per_session.values()),
        "hours": sum(e.get("duration_ms", 0) for e in per_session.values()) / 3600000,
        "cost": sum(e.get("total_cost_usd", 0) or 0 for e in per_session.values()),
        "out": sum(u.get("output_tokens", 0) for u in use),
        "cache": sum(u.get("cache_read_input_tokens", 0) for u in use),
    }


def last_commit_age(branch):
    """Hours since the branch last moved - the other half of "is anybody on this"."""
    stamp = sh("git", "log", "-1", "--format=%ct", branch)
    if not stamp.isdigit():
        return None
    return (datetime.now().timestamp() - int(stamp)) / 3600


def tasks(fid, branch="", worktrees=None):
    """The task table of one feature, read where it actually lives.

    tasks.md is a feature document and travels with the feature branch - /build
    ticks its rows off as it goes - so while a build is running the truth is in the
    worktree, and the copy on the default branch still says Open for everything."""
    d = feature_dir(fid)
    if not d:
        return []
    path = d / "tasks.md"
    for line in (worktrees if worktrees is not None else sh("git", "worktree", "list")).splitlines():
        if branch and f"[{branch}]" in line:
            candidate = Path(line.split()[0]) / path
            if candidate.is_file():
                path = candidate
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\|\s*[A-Z]+-\d+-T\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        state = next((c for c in reversed(cells) if c in {"Open", "In Progress", "Done"}), "")
        out.append({
            "id": cells[0],
            "what": cells[1] if len(cells) > 1 else "",
            "layer": cells[2] if len(cells) > 2 else "",
            "batch": cells[3] if len(cells) > 3 else "",
            "size": cells[4] if len(cells) > 4 else "",
            "state": state,
            "owner": cells[-1] if cells[-1] not in {"\u2014", "-"} else "",
        })
    return out


BUG_STATES = ["Open", "Reproduced", "In Progress", "Fixed", "Closed",
              "Not reproducible", "Not a bug"]
BUG_SEVERITIES = ["Critical", "Major", "Minor", "Cosmetic"]
BUG_HUE = {"Critical": "c-red", "Major": "c-orange", "Minor": "c-yellow", "Cosmetic": "",
           "Fixed": "c-green", "Closed": "c-green", "Open": "c-red",
           "Reproduced": "c-orange", "In Progress": "c-orange"}


def bugs():
    """Rows of bugs/INDEX.md, if a project has one.

    /fix creates that file without anybody having written down its columns - unlike
    features/INDEX.md, which /plan-product lays out - so nothing here may depend on
    a position. Status and severity are found by their value, the branch by its
    shape, and the title is the longest thing left in the row."""
    index = Path("bugs/INDEX.md")
    if not index.is_file():
        return []
    out = []
    for line in index.read_text(encoding="utf-8", errors="replace").splitlines():
        if not re.match(r"^\|\s*(\*\*)?BUG-\d+", line):
            continue
        cells = [c.strip().strip("*") for c in line.strip().strip("|").split("|")]
        rest = cells[1:]
        known = set(BUG_STATES) | set(BUG_SEVERITIES)
        titles = [c for c in rest if c not in known and not c.startswith("fix/")]
        out.append({
            "id": re.sub(r"[^A-Z0-9-]", "", cells[0]),
            "what": max(titles, key=len) if titles else "",
            "state": next((c for c in rest if c in BUG_STATES), ""),
            "severity": next((c for c in rest if c in BUG_SEVERITIES), ""),
            "branch": next((c for c in rest if c.startswith("fix/")), ""),
        })
    return out


def readiness(rows):
    """Mark what the pick rule of /build would allow: status Ready, no owner, every
    dependency Done. The board holds all three, but a reader would have to look up
    nineteen rows to see it, which is exactly the sum nobody does."""
    done = {r["id"] for r in rows if r["status"] == "Done"}
    for r in rows:
        deps = [d.strip() for d in r["deps"].split(",") if d.strip()]
        r["waiting"] = [d for d in deps if d not in done]
        free = r["owner"] in {"", "\u2014", "-"}
        r["pickable"] = r["status"] == "Ready" and free and not r["waiting"]
    return rows


def running_loops():
    """One entry per loop working on this repository, with its feature and runtime."""
    loops = []
    for process in loop_processes():
        if not process["is_loop"]:
            continue
        # The id is the last one in the line - `loop-feature.sh PROJ-x` puts it there -
        # but it is not always its own word: a loop started through a shell wrapper
        # ends up as `... loop-feature.sh PROJ-5' < /dev/null && ...`, and a token
        # match on that quoted form fails and invents a second, nameless run.
        found = re.findall(r"\b[A-Z]+-\d+\b", process["args"])
        feature = found[-1] if found else "?"
        loops.append({"pid": process["pid"], "elapsed": process["elapsed"], "feature": feature})
    # ps shows the wrapper shells too; one row per feature is what anybody wants
    seen, unique = set(), []
    for loop in sorted(loops, key=lambda x: x["pid"]):
        if loop["feature"] in seen:
            continue
        seen.add(loop["feature"])
        unique.append(loop)
    return unique


# A loop process is `bash …/loop-feature.sh PROJ-x`; the stage it is in is only
# visible on its `claude -p /<ns>:<skill> PROJ-x` child. Both are matched, and both
# are filtered the same way.
INTERESTING = re.compile(r"loop-feature\.sh|[/:][a-z][a-z-]*\s+[A-Z]+-\d+\b")


def loop_processes():
    """The loop processes and their stages, for *this* repository only.

    The process list is machine-wide and a feature id is not unique across
    projects: two products with a PROJ-3 would each show the other's loop. The
    working directory tells them apart, and lsof is what knows it - ps does not.
    Only the few interesting lines are looked up, because lsof per process is not
    free, and when lsof is missing nothing is filtered: a loop from elsewhere is a
    smaller error than no loop at all."""
    here, out = str(Path.cwd().resolve()), []
    for line in sh("ps", "-eo", "pid=,etime=,args=").splitlines():
        if "grep" in line or not INTERESTING.search(line):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        cwd = ""
        for entry in sh("lsof", "-a", "-p", parts[0], "-d", "cwd", "-Fn").splitlines():
            if entry.startswith("n"):
                cwd = entry[1:]
        if cwd and cwd != here:
            continue
        out.append({"pid": parts[0], "elapsed": parts[1], "args": " ".join(parts[2:]),
                    "is_loop": "loop-feature.sh" in line})
    return out


def active_stage(fid):
    """Which skill is executing now, from the live child process."""
    for process in loop_processes():
        match = re.search(rf"[/:]([a-z][a-z-]*)\s+{re.escape(fid)}\b", process["args"])
        if match:
            return match.group(1)
    return ""


def current_stage(fid):
    """Which skill owns the next transition, live first and persisted otherwise."""
    active = active_stage(fid)
    if active:
        return active
    state = loop_state(fid)
    if state.get("stage"):
        return state["stage"]
    return ""


def loop_state(fid):
    """The state persisted by loop-feature.sh in Git's common directory."""
    common = sh("git", "rev-parse", "--git-common-dir")
    if not common:
        return {}
    root = Path(common)
    if not root.is_absolute():
        root = Path.cwd() / root
    path = root / "kaitersberg" / "loops" / f"{fid}.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def feature_dir(fid):
    return next(iter(sorted(Path("features").glob(f"{fid}-*"))), None)


# What exists in the feature folder, in the order the pipeline writes it. These are
# not rungs - /review, /qa and /pr all happen inside In Review and set no status of
# their own - so this says how far the feature got inside its rung without claiming
# a state no skill ever wrote. It also outlives the loop that produced it.
EVIDENCE = ["spec", "design", "tasks", "review", "qa", "pr"]

# A colour has to mean one thing everywhere, so the mapping lives in one place.
HUES = {
    "P0": "c-red", "P1": "c-orange", "P2": "c-yellow",
    "XS": "c-indigo", "S": "c-indigo", "M": "c-indigo", "L": "c-indigo", "XL": "c-indigo",
    "Roadmap": "", "Spec": "c-blue", "Designed": "c-blue", "Ready": "c-blue",
    "In Progress": "c-orange", "In Review": "c-orange", "Done": "c-green", "Dropped": "c-red",
    "spec": "c-blue", "design": "c-blue", "tasks": "c-blue",
    "review": "c-teal", "qa": "c-purple", "pr": "c-green", "proof": "c-green",
}
LAYER_HUES = ["c-teal", "c-indigo", "c-purple", "c-pink", "c-blue", "c-orange"]
SHORT = {"Approved": "ok", "Approved with notes": "notes", "Changes required": "changes",
         "Production ready": "ready", "Ready with reservations": "reservations",
         "Not production ready": "blocked"}


def hue(value, kind=""):
    """The class for one badge. Layers are named in the project's language, so they
    get a stable colour from the name itself rather than from a list we cannot keep."""
    if kind == "layer" and value:
        return LAYER_HUES[sum(map(ord, value)) % len(LAYER_HUES)]
    if kind == "wave":
        return "c-teal"
    return HUES.get(value, "")


def evidence(fid, branch="", worktrees=None):
    d = feature_dir(fid)
    if not d:
        return []
    live = [name for name in EVIDENCE if doc(fid, f"{name}.md", branch, worktrees)]
    if live:
        return live + (["proof"] if doc(fid, "proof.md", branch, worktrees) else [])
    # PROJ-1 has no spec and no test report; proof.md stands in for both
    return [name for name in EVIDENCE if (d / f"{name}.md").is_file()] + \
           (["proof"] if (d / "proof.md").is_file() else [])


def log_tail(fid, lines=400):
    """Last stage, last tool call and last verdict from the feature's loop.log."""
    d = feature_dir(fid)
    log = d / "loop.log" if d else None
    if not log or not log.is_file():
        return {}
    raw = sh("tail", "-n", str(lines), str(log))
    tool = verdict = mode = stage_from_log = ""
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []) or []:
                if block.get("type") == "tool_use":
                    tool = block.get("name", "")
        elif event.get("type") == "result":
            structured = event.get("structured_output") or {}
            verdict = structured.get("outcome") or structured.get("verdict", "")
        elif event.get("type") == "kaitersberg_stage":
            stage_from_log = event.get("stage", "")
        elif event.get("subtype") == "init":
            mode = event.get("permissionMode", "")
    age = int(datetime.now().timestamp() - log.stat().st_mtime)
    # The process knows the stage; dontAsk, the read-only profile, only tells us it
    # is a reviewing one, and is the fallback for the moment between two stages.
    stage = current_stage(fid) or stage_from_log or ("review" if mode == "dontAsk" else "…")
    return {"tool": tool, "verdict": verdict, "stage": stage, "age": age}


def since_report(fid, branch, kind="qa"):
    """The commits that landed after the newest report was written.

    While a build works a findings list there is nothing per finding to show - its
    table is written at the end - so guessing which finding a commit belongs to
    would repeat a mistake this file already made once. The commits themselves are
    facts, and their subjects say plainly enough what is being worked on."""
    path = doc(fid, f"{kind}.md", branch)
    if not path or not branch or branch in {"\u2014", "-"}:
        return []
    worktree = ""
    for line in sh("git", "worktree", "list").splitlines():
        if f"[{branch}]" in line:
            worktree = line.split()[0]
    when = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%S")
    log = sh("git", "log", f"--since={when}", "--format=%h\t%s", branch, cwd=worktree or None)
    return [line.split("\t", 1) for line in log.splitlines() if "\t" in line]


def branch_state(branch):
    """Commits ahead of the default branch, and how much is uncommitted."""
    if not branch or branch in {"\u2014", "-", ""}:
        return {}
    base = sh("git", "symbolic-ref", "--short", "HEAD") or "main"
    worktree = ""
    for line in sh("git", "worktree", "list").splitlines():
        if f"[{branch}]" in line:
            worktree = line.split()[0]
    ahead = sh("git", "rev-list", "--count", f"{base}..{branch}")
    dirty = sh("git", "status", "--short", cwd=worktree) if worktree else ""
    return {"ahead": ahead or "0", "dirty": len(dirty.splitlines()), "worktree": bool(worktree)}


def api_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def api_value(value):
    """Turn the board's visual empty markers into an API null."""
    return None if value in {"", "\u2014", "-"} else value


def task_progress(items):
    counts = {state: sum(1 for item in items if item["state"] == state)
              for state in ("Done", "In Progress", "Open")}
    return {
        "total": len(items),
        "done": counts["Done"],
        "in_progress": counts["In Progress"],
        "open": counts["Open"],
    }


def loop_state_snapshot(state):
    """Expose the transition facts, never arbitrary future state-file fields."""
    if not state:
        return None
    return {
        "stage": state.get("stage"),
        "last_stage": state.get("last_stage"),
        "last_outcome": state.get("last_outcome"),
        "head_sha": state.get("head_sha"),
        "attempts": state.get("attempts", {}),
        "transitions": state.get("transitions", 0),
        "created_at": state.get("created_at"),
        "updated_at": state.get("updated_at"),
    }


def loop_snapshot(row, live_loop=None):
    persisted = loop_state(row["id"])
    if not live_loop and not persisted:
        return None
    activity = log_tail(row["id"]) if live_loop else {}
    age = activity.get("age")
    return {
        "running": bool(live_loop),
        "stage": activity.get("stage") or persisted.get("stage"),
        "elapsed": live_loop.get("elapsed") if live_loop else None,
        "pid": live_loop.get("pid") if live_loop else None,
        "stalled": bool(live_loop and isinstance(age, int) and age > 120),
        "last_activity": {
            "age_seconds": age,
            "tool": activity.get("tool") or None,
            "verdict": activity.get("verdict") or None,
        } if activity else None,
        "state": loop_state_snapshot(persisted),
    }


def feature_snapshot(row, loops=None, worktrees=None, detailed=False):
    """The dashboard's read model for one feature, with API-friendly types."""
    loops = loops or {}
    items = tasks(row["id"], row["branch"], worktrees)
    marks = evidence(row["id"], row["branch"], worktrees)
    attempts = rounds(row["id"], row["branch"], worktrees)
    reports = {}
    for kind in ("review", "qa"):
        if kind not in marks:
            continue
        result = report(row["id"], kind, row["branch"], worktrees)
        current = result.get("findings", [])
        reports[kind] = {
            "verdict": result.get("verdict") or None,
            "severity_counts": result.get("counts", {}),
            "attempts": attempts.get(kind, 1),
            "open_findings": sum(1 for item in current
                                 if not item["note"] and not item.get("done")),
            "notes": sum(1 for item in current if item["note"] and not item.get("done")),
        }

    dependencies = [item.strip() for item in row["deps"].split(",")
                    if api_value(item.strip())]
    result = {
        "id": row["id"],
        "name": row["name"],
        "status": row["status"],
        "priority": api_value(row["prio"]),
        "effort": api_value(row["effort"]),
        "wave": int(row["wave"]) if row["wave"].isdigit() else None,
        "dependencies": dependencies,
        "owner": api_value(row["owner"]),
        "branch": api_value(row["branch"]),
        "pickable": bool(row.get("pickable")),
        "waiting_on": row.get("waiting", []),
        "task_progress": task_progress(items),
        "documents": marks,
        "reports": reports,
        "spend": spend(row["id"]) or None,
        "loop": loop_snapshot(row, loops.get(row["id"])),
    }
    if detailed:
        api_tasks = [{**item, "owner": api_value(item["owner"])} for item in items]
        api_findings = [{**item,
                         "done": api_value(item.get("done")),
                         "commit": api_value(item.get("commit"))}
                        for item in findings(row["id"], row["branch"], worktrees)]
        settled = [{**item, "commit": api_value(item.get("commit"))}
                   for item in carried(row["id"], row["branch"], worktrees)
                   if item["did"]]
        result.update({
            "tasks": api_tasks,
            "findings": api_findings,
            "settled_findings": settled,
            "evidence_files": evidence_files(row["id"], row["branch"], worktrees),
            "branch_state": branch_state(row["branch"]),
            "landed_since_report": [
                {"sha": sha, "subject": subject}
                for sha, subject in since_report(row["id"], row["branch"])
            ],
        })
    return result


def api_context():
    rows = readiness(board())
    loops = {item["feature"]: item for item in running_loops()}
    return rows, loops, sh("git", "worktree", "list")


def api_envelope(**payload):
    return {
        "schema_version": API_VERSION,
        "read_only": True,
        "generated_at": api_timestamp(),
        **payload,
    }


def dashboard_snapshot():
    rows, loops, worktrees = api_context()
    features = [feature_snapshot(row, loops, worktrees, detailed=True) for row in rows]
    return api_envelope(
        project=Path.cwd().name,
        rungs=RUNGS,
        status_counts={rung: sum(1 for row in rows if row["status"] == rung)
                       for rung in RUNGS},
        features=features,
        loops=[{"feature": feature["id"], **feature["loop"]}
               for feature in features if feature["loop"]],
        bugs=bugs(),
    )


def api_route(path):
    """Return an HTTP status and JSON payload for one versioned API route."""
    if path.rstrip("/") == "/api/v1":
        return 200, api_envelope(
            name="Kaitersberg loop dashboard API",
            endpoints={
                "snapshot": "/api/v1/snapshot",
                "features": "/api/v1/features",
                "feature": "/api/v1/features/{feature_id}",
                "loops": "/api/v1/loops",
                "bugs": "/api/v1/bugs",
            },
        )

    if path.rstrip("/") == "/api/v1/snapshot":
        return 200, dashboard_snapshot()

    rows, loops, worktrees = api_context()
    if path.rstrip("/") == "/api/v1/features":
        return 200, api_envelope(
            features=[feature_snapshot(row, loops, worktrees) for row in rows])

    match = re.fullmatch(r"/api/v1/features/([A-Z]+-\d+)/?", path)
    if match:
        row = next((item for item in rows if item["id"] == match.group(1)), None)
        if row:
            return 200, api_envelope(
                feature=feature_snapshot(row, loops, worktrees, detailed=True))
        return 404, api_envelope(error={
            "code": "feature_not_found",
            "message": f"No feature {match.group(1)} exists on the board.",
        })

    if path.rstrip("/") == "/api/v1/loops":
        found = []
        for row in rows:
            value = loop_snapshot(row, loops.get(row["id"]))
            if value:
                found.append({"feature": row["id"], **value})
        return 200, api_envelope(loops=found)

    if path.rstrip("/") == "/api/v1/bugs":
        return 200, api_envelope(bugs=bugs())

    return 404, api_envelope(error={
        "code": "not_found",
        "message": "No such read-only API endpoint.",
    })


# The look is Apple's own vocabulary rather than a theme laid on top of it: the
# system type stack, the system colours, materials instead of borders, one accent
# doing all the work. Everything is a system font, so the page owes nothing to the
# network - which is what a tool you open while offline needs.
CSS = """
*, *::before, *::after { box-sizing: border-box; }

:root {
  color-scheme: light dark;
  --bg: #f2f2f7;
  --wash: radial-gradient(120% 90% at 12% -10%, #ffffff 0%, #f2f2f7 55%, #eaeaef 100%);
  --material: rgba(255, 255, 255, 0.72);
  --material-thick: rgba(255, 255, 255, 0.86);
  --label: #1d1d1f;
  --label-2: rgba(60, 60, 67, 0.62);
  --label-3: rgba(60, 60, 67, 0.32);
  --separator: rgba(60, 60, 67, 0.13);
  --panel: rgba(120, 120, 128, 0.06);
  --card: #ffffff;
  --blue: #0071e3;
  --green: #248a3d;
  --orange: #b25000;
  --dot: #30d158;
  --red: #d70015;
  --yellow: #a05a00;
  --teal: #0071a4;
  --indigo: #3634a3;
  --purple: #8944ab;
  --pink: #d30f45;
  --shadow: 0 1px 2px rgba(0,0,0,.04), 0 8px 24px -12px rgba(0,0,0,.18);
  --radius: 14px;
  --text: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", system-ui, sans-serif;
  --display: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", system-ui, sans-serif;
  --mono: ui-monospace, "SF Mono", SFMono-Regular, Menlo, monospace;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #000000;
    --wash: radial-gradient(120% 90% at 12% -10%, #1c1c1e 0%, #0a0a0b 60%, #000000 100%);
    --material: rgba(28, 28, 30, 0.66);
    --material-thick: rgba(38, 38, 41, 0.82);
    --label: #f5f5f7;
    --label-2: rgba(235, 235, 245, 0.6);
    --label-3: rgba(235, 235, 245, 0.3);
    --separator: rgba(84, 84, 88, 0.45);
    --panel: rgba(120, 120, 128, 0.08);
    --card: #1c1c1e;
    --blue: #0a84ff;
    --green: #30d158;
    --orange: #ff9f0a;
    --red: #ff453a;
    --yellow: #ffd60a;
    --teal: #40c8e0;
    --indigo: #7d7aff;
    --purple: #bf5af2;
    --pink: #ff375f;
    --shadow: 0 1px 2px rgba(0,0,0,.5), 0 12px 32px -16px rgba(0,0,0,.8);
  }
}

html, body { height: 100%; }

body {
  margin: 0;
  height: 100dvh;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  background: var(--bg);
  background-image: var(--wash);
  background-attachment: fixed;
  color: var(--label);
  font-family: var(--text);
  font-size: 15px;
  line-height: 1.45;
  letter-spacing: -0.01em;
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
}

/* chrome */
.chrome {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.5rem 1.25rem;
  padding: 1.4rem clamp(1rem, 3vw, 2.5rem) 1.1rem;
  background: var(--material);
  -webkit-backdrop-filter: saturate(180%) blur(24px);
  backdrop-filter: saturate(180%) blur(24px);
  border-bottom: 1px solid var(--separator);
}

h1 {
  font-family: var(--display);
  font-size: clamp(1.35rem, 2.6vw, 1.9rem);
  font-weight: 600;
  letter-spacing: -0.028em;
  margin: 0;
}

.meta { color: var(--label-2); font-size: 0.82rem; margin: 0; font-variant-numeric: tabular-nums; }
.spacer { flex: 1 1 auto; }

.segments {
  display: flex;
  gap: 1px;
  padding: 2px;
  border-radius: 10px;
  background: var(--separator);
  overflow: hidden;
}
.seg {
  padding: 0.28rem 0.7rem;
  background: var(--material-thick);
  font-size: 0.76rem;
  color: var(--label-2);
  white-space: nowrap;
}
.seg:first-child { border-radius: 8px 0 0 8px; }
.seg:last-child { border-radius: 0 8px 8px 0; }
.seg b { color: var(--label); font-variant-numeric: tabular-nums; font-weight: 600; }

/* running loops */
main {
  /* A column, not fixed rows: the bug strip appears only in some projects, and a
     grid with two rows declared pushes the board to the bottom when there are three. */
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
  padding: 1.1rem clamp(1rem, 3vw, 2.5rem) clamp(1rem, 3vw, 2rem);
}

.activity { display: flex; flex-wrap: wrap; gap: 0.7rem; align-items: flex-start; }
.bugs { align-items: center; }
.strip { margin: 0 0.3rem 0 0; font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
         letter-spacing: 0.07em; color: var(--label-2); display: flex; gap: 0.5rem; align-items: center; }
.strip .count { font-variant-numeric: tabular-nums; color: var(--label-3); letter-spacing: 0; }
.run.bug { display: block; padding: 0.55rem 0.8rem; }
.run.bug .branch { font-family: var(--mono); font-size: 0.68rem; color: var(--label-3); }

.run {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.6rem 0.95rem 0.6rem 0.8rem;
  border-radius: var(--radius);
  background: var(--material-thick);
  -webkit-backdrop-filter: blur(20px);
  backdrop-filter: blur(20px);
  box-shadow: var(--shadow);
}
.run.idle { color: var(--label-2); font-size: 0.85rem; box-shadow: none; background: none; padding-left: 0; }

.dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--dot);
  animation: pulse 2.4s ease-out infinite;
  flex: none;
}
@keyframes pulse {
  0%   { box-shadow: 0 0 0 0 rgba(48, 209, 88, 0.55); }
  70%  { box-shadow: 0 0 0 9px rgba(48, 209, 88, 0); }
  100% { box-shadow: 0 0 0 0 rgba(48, 209, 88, 0); }
}

.run .who { font-weight: 600; letter-spacing: -0.015em; }
.run .stage {
  font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--blue); font-weight: 600; margin-left: 0.35rem;
}
.run .line { font-size: 0.78rem; color: var(--label-2); font-variant-numeric: tabular-nums; }
.run.quiet .line { color: var(--orange); }
.run.quiet .dot { background: var(--orange); animation: none; }

/* board */
.kanban {
  min-height: 0;
  flex: 1 1 auto;
  display: flex;
  align-items: stretch;
  gap: 0.9rem;
  overflow-x: auto;
  overscroll-behavior-x: contain;
  scrollbar-width: thin;
}
.col { flex: 1 1 15rem; max-width: 21rem; }
/* An empty rung keeps its place as a rail, so the ladder stays readable */
.col.rail { flex: 0 0 2.1rem; opacity: 0.55; }
.col.rail h2 { border: 0; justify-content: center; padding: 0.6rem 0; height: 100%; }
.col.rail .turn { writing-mode: vertical-rl; transform: rotate(180deg); font-size: 0.68rem;
                  color: var(--label-2); letter-spacing: 0.04em; }

.col {
  min-height: 0; display: grid; grid-template-rows: auto minmax(0, 1fr);
  background: var(--panel); border: 1px solid var(--separator); border-radius: 10px;
  overflow: hidden;
}

.col h2 {
  margin: 0;
  padding: 0.6rem 0.7rem;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--label);
  display: flex;
  align-items: center;
  gap: 0.45rem;
  border-bottom: 1px solid var(--separator);
}
.col h2 .count {
  font-variant-numeric: tabular-nums; color: var(--label-2); font-size: 0.72rem; font-weight: 500;
  background: color-mix(in srgb, var(--label-3) 22%, transparent);
  border-radius: 999px; padding: 0.02rem 0.42rem; margin-left: auto;
}
.col h2::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: var(--label-3); }
.col.in-progress h2::before, .col.in-review h2::before { background: var(--orange); }
.col.done h2::before { background: var(--green); }
.col.ready h2::before, .col.designed h2::before, .col.spec h2::before { background: var(--blue); }

.cards { min-height: 0; overflow-y: auto; overscroll-behavior-y: contain; padding: 0.5rem; scrollbar-width: thin; }

h3.group {
  margin: 0.55rem 0 0.35rem; font-size: 0.66rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--label-3); position: sticky; top: -0.5rem;
  background: var(--panel); padding: 0.15rem 0;
}
h3.group:first-child { margin-top: 0; }
.card .waiting { color: var(--label-2); }
.card .stalled { color: var(--orange); }
.card {
  background: var(--card);
  border: 1px solid var(--separator);
  border-radius: 8px;
  padding: 0.6rem 0.7rem;
  margin-bottom: 0.5rem;
  transition: border-color 0.15s, background 0.15s;
}
.card:hover { border-color: color-mix(in srgb, var(--blue) 55%, var(--separator)); }
.card:focus-visible, a:focus-visible { outline: 2px solid var(--blue); outline-offset: 2px; border-radius: 8px; }
.card .id { font-size: 0.72rem; font-weight: 600; color: var(--label-2); font-variant-numeric: tabular-nums; }
.card .name { font-family: var(--display); letter-spacing: -0.015em; line-height: 1.3; }
.card .sub { font-size: 0.74rem; color: var(--label-2); margin-top: 0.3rem; }
.card .branch { font-family: var(--mono); font-size: 0.68rem; color: var(--label-3); word-break: break-all; }
.card.live { border-color: var(--orange); box-shadow: inset 0 0 0 1px var(--orange); }
.card.live .id { color: var(--orange); }
.card .stage-line { display: flex; align-items: center; gap: 0.35rem; color: var(--label); font-variant-numeric: tabular-nums; }
.dot.small { width: 6px; height: 6px; }
a.card { display: block; color: inherit; text-decoration: none; }
a.card:hover { transform: translateY(-1px); }
.chips { display: inline-flex; flex-wrap: wrap; gap: 0.25rem; margin-left: 0.4rem; vertical-align: middle; }
.chips.big { gap: 0.3rem; margin: 0; }
.chip {
  font-size: 0.62rem; letter-spacing: 0.03em; padding: 0.06rem 0.4rem; border-radius: 999px;
  font-weight: 600;
  color: var(--hue, var(--label-2));
  background: color-mix(in srgb, var(--hue, var(--label-3)) 16%, transparent);
}
/* One hue per kind of fact, so a colour always means the same thing */
.c-red { --hue: var(--red); }        .c-orange { --hue: var(--orange); }
.c-yellow { --hue: var(--yellow); }  .c-green { --hue: var(--green); }
.c-teal { --hue: var(--teal); }      .c-blue { --hue: var(--blue); }
.c-indigo { --hue: var(--indigo); }  .c-purple { --hue: var(--purple); }
.c-pink { --hue: var(--pink); }
.chips.big .chip { font-size: 0.72rem; padding: 0.16rem 0.6rem; }
.bar { height: 3px; border-radius: 2px; background: color-mix(in srgb, var(--label-3) 28%, transparent); margin: 0.5rem 0 0.25rem; overflow: hidden; }
.bar i { display: block; height: 100%; background: var(--green); border-radius: 2px; }
body[data-offline] { opacity: 0.55; transition: opacity 0.3s; }
body[data-offline] .meta::after { content: " - server not answering"; color: var(--orange); }
.back { color: var(--blue); text-decoration: none; margin-right: 0.2rem; }
.muted { color: var(--label-2); font-weight: 400; }
.detail { display: grid; grid-template-rows: minmax(0, 1fr); }
/* Work on the left, facts on the right; on a narrow screen the facts come first,
   because "what is this and who owns it" is the question a small screen asks. */
.layout { min-height: 0; display: grid; grid-template-columns: minmax(0, 1fr) 17rem; gap: 1.5rem; }
.detail .scroll { min-height: 0; overflow-y: auto; padding-right: 0.4rem; }
.facts { min-height: 0; overflow-y: auto; }
.facts dl { margin: 0; display: grid; grid-template-columns: 1fr; gap: 0.1rem 0; }
.facts dt { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--label-2); margin-top: 0.9rem; }
.facts dd { margin: 0.15rem 0 0; }
.facts .sev { display: flex; flex-wrap: wrap; gap: 0.25rem; margin-top: 0.3rem; }
.facts .evidence-list { font-family: var(--mono); font-size: 0.68rem; line-height: 1.5; color: var(--label-3); margin-top: 0.25rem; }
.facts .branch { font-family: var(--mono); font-size: 0.72rem; color: var(--label-2); word-break: break-all; }

.crumbs { margin: 0 0 0.1rem; font-size: 0.78rem; color: var(--label-2); }
.crumbs a { color: var(--blue); text-decoration: none; }
.crumbs a:hover { text-decoration: underline; }

.progress-block { min-width: 12rem; }
.progress { display: flex; height: 6px; border-radius: 3px; overflow: hidden; background: color-mix(in srgb, var(--label-3) 25%, transparent); }
.progress i { display: block; height: 100%; }
.seg-done { background: var(--green); }
.seg-in-progress { background: var(--orange); }
.seg-open { background: color-mix(in srgb, var(--label-3) 45%, transparent); }
.progress-block .meta { margin-top: 0.3rem; }

.filters { margin: 0 0 0.6rem; }
.filter {
  font-size: 0.74rem; text-decoration: none; color: var(--label-2);
  border: 1px solid var(--separator); border-radius: 999px; padding: 0.16rem 0.7rem;
}
.filter:hover { border-color: var(--blue); color: var(--blue); }
.empty { color: var(--label-2); }
.empty code { font-family: var(--mono); font-size: 0.85em; }

h2.batch { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.07em; color: var(--label-2);
           margin: 1.4rem 0 0.5rem; display: flex; align-items: center; gap: 0.5rem;
           position: sticky; top: 0; background: var(--bg); padding: 0.3rem 0; z-index: 1; }
h2.batch .count { font-variant-numeric: tabular-nums; color: var(--label-3); letter-spacing: 0; }

.task {
  background: var(--card); border: 1px solid var(--separator); border-radius: 8px;
  padding: 0.6rem 0.75rem; margin-bottom: 0.5rem;
  border-left: 3px solid color-mix(in srgb, var(--label-3) 40%, transparent);
}
.task.done { border-left-color: var(--green); }
.task.in-progress { border-left-color: var(--orange); }
.task .tid { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; font-size: 0.72rem; font-weight: 600; color: var(--label-2); }
.task .state-icon { display: inline-flex; }
.task.done .state-icon, .task.done .state { color: var(--green); }
.task.in-progress .state-icon, .task.in-progress .state { color: var(--orange); }
.task .state { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.05em; }
@media (max-width: 900px) {
  .layout { grid-template-columns: minmax(0, 1fr); grid-template-rows: auto minmax(0, 1fr); }
  .facts { order: -1; overflow: visible; }
  .facts dl { grid-template-columns: repeat(auto-fit, minmax(7rem, 1fr)); gap: 0.4rem 1rem; }
  .facts dt { margin-top: 0; }
}
.task .what { margin-top: 0.25rem; line-height: 1.4; }
.count.working { display: inline-flex; align-items: center; gap: 0.35rem; color: var(--orange); }
.landed { font-size: 0.8rem; color: var(--label-2); line-height: 1.7; }
.landed code { font-family: var(--mono); font-size: 0.9em; color: var(--label-3); margin-right: 0.4rem; }
.trail { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-top: 0.4rem; }
.mark {
  font-size: 0.66rem; letter-spacing: 0.02em; padding: 0.08rem 0.42rem;
  border-radius: 999px; font-weight: 600;
  color: var(--hue, var(--label-2));
  background: color-mix(in srgb, var(--hue, var(--label-3)) 16%, transparent);
}

/* one column at a time on a phone, and it snaps */
@media (max-width: 720px) {
  .kanban { grid-auto-columns: 86%; scroll-snap-type: x mandatory; }
  .col { scroll-snap-align: start; }
  .chrome { padding-top: 1rem; }
}

@media (prefers-reduced-motion: reduce) {
  .dot { animation: none; }
  .card { transition: none; }
}
"""



# Instead of a meta refresh, which reloads the document and throws away the scroll
# position and every hover: fetch the same page, compare, and swap only when it
# actually differs. Scripts inserted through innerHTML do not run, so this loop
# survives its own replacement without ever starting a second timer.
SCRIPT = """
addEventListener('load', () => {
  let last = document.body.innerHTML;
  const scrollers = () => [...document.querySelectorAll('.cards, .scroll, .kanban')];
  const tick = async () => {
    try {
      const html = await (await fetch(location.pathname + location.search, {cache: 'no-store'})).text();
      const fresh = new DOMParser().parseFromString(html, 'text/html').body.innerHTML;
      if (fresh !== last) {
        const keep = scrollers().map(el => [el.scrollTop, el.scrollLeft]);
        document.body.innerHTML = last = fresh;
        scrollers().forEach((el, i) => {
          if (keep[i]) { el.scrollTop = keep[i][0]; el.scrollLeft = keep[i][1]; }
        });
      }
      document.body.removeAttribute('data-offline');
    } catch {
      document.body.dataset.offline = '1';   // the server is gone; say so rather than lie
    }
    setTimeout(tick, %d000);
  };
  setTimeout(tick, %d000);
});
""" % (REFRESH_SECONDS, REFRESH_SECONDS)

def project_spend(rows):
    """What the agents have spent on this product, over the features that ran through
    the loop. Features built by hand leave no log and are simply not in it."""
    totals = [spend(r["id"]) for r in rows]
    totals = [t for t in totals if t]
    if not totals:
        return ""
    hours = sum(t["hours"] for t in totals)
    cost = sum(t["cost"] for t in totals)
    stages = sum(t["stages"] for t in totals)
    return (f" · {stages} agent stages · {hours:.1f} h · ≈${cost:.0f} at API list price")


def page():
    rows = board()
    loops = {loop["feature"]: loop for loop in running_loops()}
    counts = {rung: sum(1 for r in rows if r["status"] == rung) for rung in RUNGS}
    now = datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S")
    project = Path.cwd().name

    def esc(text):
        return html.escape(str(text))

    body = ['<header class="chrome">', f"<div><h1>{esc(project)}</h1>",
            f'<p class="meta">{sum(counts.values())} features · read at {now}, '
            f"refreshing every {REFRESH_SECONDS}s{project_spend(rows)}</p></div>",
            '<div class="spacer"></div>',
            '<div class="segments">']
    for rung in RUNGS:
        if counts[rung]:
            body.append(f'<span class="seg"><b>{counts[rung]}</b> {esc(rung)}</span>')
    body.append("</div></header><main>")

    # Read once, shown twice: in the activity strip and on the card the loop owns.
    live = {}
    for fid, loop in loops.items():
        tail = log_tail(fid)
        row = next((r for r in rows if r["id"] == fid), {})
        live[fid] = {"tail": tail, "state": branch_state(row.get("branch", "")),
                     "elapsed": loop["elapsed"], "stalled": tail.get("age", 0) > 120}

    body.append('<section class="activity">')
    if loops:
        for fid, loop in sorted(loops.items()):
            tail, state = live[fid]["tail"], live[fid]["state"]
            # No tool call for two minutes is what a stuck stage looks like from outside
            stalled = live[fid]["stalled"]
            line = " · ".join(filter(None, [
                esc(tail.get("tool") or "starting"),
                f"{state['ahead']} commits" if state.get("ahead") else "",
                f"{state['dirty']} uncommitted" if state.get("dirty") else "",
                esc(loop["elapsed"]),
                "no activity for 2 min" if stalled else "",
            ]))
            body.append(
                f'<article class="run{" quiet" if stalled else ""}"><span class="dot"></span>'
                f'<div><div><span class="who">{esc(fid)}</span>'
                f'<span class="stage">{esc(tail.get("stage", "?"))}</span></div>'
                f'<div class="line">{line}</div></div></article>')
    else:
        body.append('<article class="run idle">No loop is running.</article>')
    body.append("</section>")

    # Only when a project has bugs at all: /fix creates the file, and until then an
    # empty strip would be a heading for nothing.
    reported = bugs()
    if reported:
        shut = {"Fixed", "Closed", "Not a bug", "Not reproducible"}
        open_bugs = [b for b in reported if b["state"] not in shut]
        body.append('<section class="activity bugs"><h2 class="strip">Bugs'
                    f'<span class="count">{len(open_bugs)} open · {len(reported)} total</span></h2>')
        for b in sorted(open_bugs, key=lambda b: BUG_SEVERITIES.index(b["severity"])
                        if b["severity"] in BUG_SEVERITIES else 9):
            chips = "".join(f'<span class="chip {BUG_HUE.get(v, "")}">{esc(v)}</span>'
                            for v in (b["severity"], b["state"]) if v)
            branch = f'<div class="sub branch">{esc(b["branch"])}</div>' if b["branch"] else ""
            body.append(f'<article class="run bug"><div><span class="who">{esc(b["id"])}</span>'
                        f'<span class="chips">{chips}</span></div>'
                        f'<div class="line">{esc(b["what"])}</div>{branch}</article>')
        if not open_bugs:
            body.append('<article class="run idle">Every reported bug is closed.</article>')
        body.append("</section>")

    readiness(rows)
    worktrees = sh("git", "worktree", "list")
    for r in rows:
        r["tasks"] = tasks(r["id"], r["branch"], worktrees)

    body.append('<section class="kanban">')
    def order(r):
        return (int(r["wave"] or 99), r["prio"] or "P9", int(re.sub(r"\D", "", r["id"]) or 0))

    for rung in RUNGS:
        cards = sorted([r for r in rows if r["status"] == rung], key=order)
        slug = rung.lower().replace(" ", "-")
        if not cards:
            # An empty rung stays on the board as a rail: the ladder is the point,
            # and a missing column makes the pipeline look shorter than it is.
            body.append(f'<div class="col rail {slug}"><h2><span class="turn">{esc(rung)}</span></h2></div>')
            continue
        body.append(f'<div class="col {slug}"><h2>{esc(rung)}'
                    f'<span class="count">{len(cards)}</span></h2><div class="cards">')
        wave = None
        many = len({r["wave"] for r in cards}) > 1
        for r in cards:
            if many and r["wave"] != wave:
                wave = r["wave"]
                body.append(f'<h3 class="group">Wave {esc(wave or "-")}</h3>')
            running = live.get(r["id"])
            owner = (f'<div class="sub">{esc(r["owner"])}</div>'
                     if r["owner"] not in {"", "\u2014", "-"} else "")
            branch = (f'<div class="sub branch">{esc(r["branch"])}</div>'
                      if r["branch"] not in {"", "\u2014", "-"} else "")
            marks = evidence(r["id"], r["branch"], worktrees)
            times = rounds(r["id"], r["branch"], worktrees)
            # Only the three the loop produces are worth the ink; spec, design and
            # tasks are implied by any rung past Ready.
            # review and qa carry what they decided, not merely that they ran -
            # the word and the colour, never the colour alone.
            pieces = []
            for kind in ("review", "qa"):
                if kind in marks:
                    told = report(r["id"], kind, r["branch"], worktrees)
                    said = told.get("verdict", "")
                    open_now = sum(1 for f in told.get("findings", [])
                                   if not f["note"] and not f.get("done"))
                    pieces.append(f'<span class="mark {VERDICT_HUE.get(said, hue(kind))}" '
                                  f'title="{esc(said or kind)}">{kind}'
                                  + (f" · {SHORT.get(said, said)}" if said else "")
                                  + (f" ×{times[kind]}" if times.get(kind, 0) > 1 else "")
                                  + (f" · {open_now}" if open_now else "") + "</span>")
            pieces += [f'<span class="mark {hue(m)}">{m}</span>'
                       for m in ("pr", "proof") if m in marks]
            trail = f'<div class="trail">{"".join(pieces)}</div>' if pieces else ""
            stage = ""
            if running:
                stage = (f'<div class="sub stage-line"><span class="dot small"></span>'
                         f'{esc(running["tail"].get("stage", "?"))} · '
                         f'{esc(running["tail"].get("tool") or "starting")} · '
                         f'{esc(running["elapsed"])}</div>')
            chips = "".join(
                f'<span class="chip {k}">{esc(c)}</span>' for c, k in filter(lambda x: x[0], [
                    (r["prio"], hue(r["prio"])),
                    (f"Wave {r['wave']}" if r["wave"] else "", hue("", "wave")),
                    (r["effort"], hue(r["effort"]))]))
            # Only the dependencies that are actually still open are worth naming
            deps = (f'<div class="sub waiting">waiting on {esc(", ".join(r["waiting"]))}</div>'
                    if r["waiting"] else "")
            if r["pickable"]:
                chips += '<span class="chip c-green">pickable</span>'
            elif r["status"] == "Ready" and r["waiting"]:
                chips += '<span class="chip c-yellow">blocked</span>' 
            # An owner with no loop behind it is the state this pipeline produces
            # most easily, and the board alone cannot show it.
            idle = ""
            if not running and r["status"] in ("In Progress", "In Review") \
                    and r["owner"] not in {"", "\u2014", "-"}:
                age = last_commit_age(r["branch"]) if r["branch"] not in {"", "\u2014", "-"} else None
                since = f", last commit {age:.0f} h ago" if age and age >= 1 else ""
                idle = f'<div class="sub stalled">no loop running{since}</div>'
            used = spend(r["id"])
            cost = (f'<div class="sub">{used["hours"]:.1f} h · ≈${used["cost"]:.0f} · '
                    f'{used["stages"]} stages</div>' if used else "")
            done = [t for t in (r.get("tasks") or []) if t["state"] == "Done"]
            bar = ""
            if r.get("tasks"):
                pct = round(100 * len(done) / len(r["tasks"]))
                bar = (f'<div class="bar" title="{len(done)} of {len(r["tasks"])} tasks done">'
                       f'<i style="width:{pct}%"></i></div>'
                       f'<div class="sub">{len(done)}/{len(r["tasks"])} tasks</div>')
            body.append(f'<a class="card{" live" if running else ""}" href="/{esc(r["id"])}">'
                        f'<div class="id">{esc(r["id"])}<span class="chips">{chips}</span></div>'
                        f'<div class="name">{esc(r["name"])}</div>'
                        f'{stage}{idle}{bar}{trail}{deps}{cost}{owner}{branch}</a>')
        body.append("</div></div>")
    body.append("</section></main>")

    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{esc(project)} - board and loops</title>"
            f"<style>{CSS}</style><script>{SCRIPT}</script></head>"
            f"<body>{''.join(body)}</body></html>")


ICONS = {  # state carried by shape as well as colour, never colour alone
    "Done": '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path fill="currentColor" '
            'd="M8 1a7 7 0 100 14A7 7 0 008 1zm3.2 5.1l-3.9 4a.7.7 0 01-1 0L4.8 8.6a.7.7 0 111-1l1 1 3.4-3.5a.7.7 0 111 1z"/></svg>',
    "In Progress": '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><circle cx="8" cy="8" r="6.4" '
                   'fill="none" stroke="currentColor" stroke-width="1.6"/><path fill="currentColor" d="M8 2.6A5.4 5.4 0 018 13.4z"/></svg>',
    "Open": '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><circle cx="8" cy="8" r="6.4" fill="none" '
            'stroke="currentColor" stroke-width="1.6" stroke-dasharray="2.6 2.2"/></svg>',
}


def detail(fid, hide_done=False):
    """One feature: what the board knows, what exists on disk, and every task."""
    rows = board()
    row = next((r for r in rows if r["id"] == fid), None)
    if not row:
        return None
    items = tasks(fid, row["branch"])
    counts = {state: sum(1 for t in items if t["state"] == state)
              for state in ("Done", "In Progress", "Open")}
    running = active_stage(fid)
    persisted = loop_state(fid).get("stage", "")
    used = spend(fid)
    project = Path.cwd().name

    def esc(text):
        return html.escape(str(text))

    # Progress as a bar AND as numbers - a bar alone is a shape somebody has to guess at
    total = max(len(items), 1)
    segments = "".join(
        f'<i class="seg-{state.lower().replace(" ", "-")}" style="width:{100 * counts[state] / total}%"></i>'
        for state in ("Done", "In Progress", "Open") if counts[state])

    facts = [("Status", f'<span class="chip {hue(row["status"])}">{esc(row["status"])}</span>'),
             ("Priority", f'<span class="chip {hue(row["prio"])}">{esc(row["prio"])}</span>' if row["prio"] else ""),
             ("Wave", f'<span class="chip {hue("", "wave")}">{esc(row["wave"])}</span>' if row["wave"] else ""),
             ("Effort", f'<span class="chip {hue(row["effort"])}">{esc(row["effort"])}</span>' if row["effort"] else ""),
             ("Depends on", esc(row["deps"]) if row["deps"] else ""),
             ("Owner", esc(row["owner"]) if row["owner"] not in {"\u2014", "-", ""} else ""),
             ("Branch", f'<span class="branch">{esc(row["branch"])}</span>'
              if row["branch"] not in {"\u2014", "-", ""} else ""),
             ("Documents", "".join(f'<span class="mark {hue(m)}">{m}</span>'
                                   for m in evidence(fid, row["branch"]))),
             ("Running now", f'<span class="dot"></span> {esc(running)}' if running else ""),
             ("Next loop stage", esc(persisted)
              if persisted and persisted not in {"complete", running} else "")]

    times = rounds(fid, row["branch"])
    for kind, title in (("review", "Review"), ("qa", "QA")):
        said = report(fid, kind, row["branch"])
        if not said:
            continue
        title = f"{title} · round {times[kind]}" if times.get(kind, 0) > 1 else title
        verdict = said.get("verdict")
        sev = " ".join(f'<span class="chip {"c-red" if n and name in ("Critical", "Blocking") else ""}">'
                       f"{name} {n}</span>" for name, n in said.get("counts", {}).items())
        facts.append((title, (f'<span class="chip {VERDICT_HUE.get(verdict, "")}">{esc(verdict)}</span>'
                              if verdict else '<span class="muted">no verdict found</span>')
                      + (f'<div class="sev">{sev}</div>' if sev else "")))

    files = evidence_files(fid, row["branch"])
    if files:
        facts.append(("Evidence", f'{len(files)} files<div class="sub evidence-list">'
                      + "<br>".join(esc(f) for f in files[:6])
                      + (f"<br>and {len(files) - 6} more" if len(files) > 6 else "") + "</div>"))

    if used:
        facts.append(("Agent spend", f'{used["stages"]} stages · {used["turns"]} turns · '
                      f'{used["hours"]:.1f} h<div class="sub">{used["out"]:,} tokens out · '
                      f'{used["cache"] / 1e6:.1f} M cache read</div>'
                      f'<div class="sub">≈ ${used["cost"]:.2f} at API list price</div>'))

    shown = [t for t in items if not (hide_done and t["state"] == "Done")]

    body = [f'<header class="chrome"><div>'
            f'<p class="crumbs"><a href="/">{esc(project)}</a> <span aria-hidden="true">/</span> {esc(fid)}</p>'
            f'<h1>{esc(row["name"])}</h1></div>'
            f'<div class="spacer"></div>'
            f'<div class="progress-block">'
            f'<div class="progress" role="img" aria-label="{counts["Done"]} of {len(items)} tasks done">{segments}</div>'
            f'<p class="meta">{counts["Done"]} done · {counts["In Progress"]} in progress · '
            f'{counts["Open"]} open'
            # The same line the card carries, so the two never have to be compared
            + (f' · {used["hours"]:.1f} h · ≈${used["cost"]:.0f} · {used["stages"]} stages'
               if used else "")
            + '</p></div></header>'
            '<main class="detail"><div class="layout">']

    # What has to happen next comes before what already happened.
    found = findings(fid, row["branch"])
    landed = since_report(fid, row["branch"])
    found_html = []
    if found:
        blocking = [f for f in found if not f["note"] and not f.get("done")]
        handled = [f for f in found if f.get("done")]
        # A stage is running and the report predates it, so the open findings are
        # what it is working on - that is exact, where guessing per finding is not.
        working = (f'<span class="count working"><span class="dot"></span>'
                   f'{esc(running)} working on these</span>' if running and blocking else "")
        found_html.append(f'<h2 class="batch">Findings<span class="count">'
                          f'{len(blocking)} blocking · {len(found) - len(blocking) - len(handled)} notes'
                          + (f' · {len(handled)} worked' if handled else "") + "</span>"
                          + working + "</h2>")
        for f in sorted(found, key=lambda f: (bool(f.get("done")), f["note"], f["id"])):
            state = "done" if f.get("done") else "open" if f["note"] else "in-progress"
            word = "worked" if f.get("done") else "note" if f["note"] else "blocking"
            icon = "Done" if f.get("done") else "Open" if f["note"] else "In Progress"
            found_html.append(
                f'<article class="task {state}"><div class="tid">'
                f'<span class="state-icon">{ICONS[icon]}</span>'
                f'<span class="state">{word}</span>'
                f'<span class="muted">{esc(f["id"])}</span>'
                f'<span class="chip {hue(f["source"], "layer")}">{esc(f["source"])}</span>'
                + (f'<span class="chip {BUG_HUE.get(f["severity"], "")}">{esc(f["severity"])}</span>'
                   if f.get("severity") else "")
                # The builder's own record, and labelled as that: the next round measures.
                + (f'<span class="chip c-green" title="recorded by /build, not re-measured">'
                   f'{esc(f["done"].lower())} · {esc(f["commit"][:7])}</span>'
                   if f.get("done") else "")
                + f'</div><div class="what">{esc(f["what"])}</div></article>')

    # tasks, built in one piece - the order of these strings is the page
    task_html = []
    if items:
        task_html.append('<p class="filters">' + (
            '<a class="filter" href="?done=hide">Hide done</a>' if not hide_done
            else '<a class="filter on" href="?">Show done</a>') + "</p>")
    if not items:
        task_html.append('<p class="empty">No <code>tasks.md</code> yet - <code>/tasks</code> has not run '
                         "for this feature.</p>")
    elif not shown:
        task_html.append('<p class="empty">Every task is done. <a href="?">Show them</a>.</p>')

    batch = None
    for t in shown:
        if t["batch"] != batch:
            batch = t["batch"]
            in_batch = [x for x in items if x["batch"] == batch]
            done_here = sum(1 for x in in_batch if x["state"] == "Done")
            task_html.append(f'<h2 class="batch">Batch {esc(batch)}'
                             f'<span class="count">{done_here}/{len(in_batch)}</span></h2>')
        state = t["state"] or "Open"
        slug = state.lower().replace(" ", "-")
        owner = f'<span class="muted">{esc(t["owner"])}</span>' if t["owner"] else ""
        task_html.append(
            f'<article class="task {slug}"><div class="tid">'
            f'<span class="state-icon">{ICONS.get(state, ICONS["Open"])}</span>'
            f'<span class="state">{esc(state)}</span>'
            f'<span class="muted">{esc(t["id"])}</span>'
            f'<span class="chip {hue(t["layer"], "layer")}">{esc(t["layer"])}</span>'
            f'<span class="chip {hue(t["size"])}">{esc(t["size"])}</span>{owner}</div>'
            f'<div class="what">{esc(t["what"])}</div></article>')
    settled = [c for c in carried(fid, row["branch"]) if c["did"]]
    if settled:
        found_html.append('<h2 class="batch">Settled in the round before'
                          f'<span class="count">{len(settled)}</span></h2>')
        for c in settled:
            found_html.append(
                f'<article class="task done"><div class="tid">'
                f'<span class="state-icon">{ICONS["Done"]}</span>'
                f'<span class="state">{esc(c["did"].lower())}</span>'
                f'<span class="muted">{esc(c["id"])}</span>'
                f'<span class="chip {hue(c["source"], "layer")}">{esc(c["source"])}</span>'
                + (f'<span class="chip c-green">{esc(c["commit"][:7])}</span>'
                   if c["commit"] else "")
                + f'</div><div class="what">{esc(c["label"])}</div></article>')

    if landed:
        found_html.append('<h2 class="batch">Landed since the report'
                          f'<span class="count">{len(landed)}</span></h2><div class="landed">'
                          + "".join(f'<div><code>{esc(sha)}</code> {esc(subject)}</div>'
                                    for sha, subject in landed[:10]) + "</div>")

    body.append('<div class="scroll">' + "".join(found_html) + "".join(task_html) + "</div>")

    # the facts, beside the work on a wide screen and above it on a narrow one
    body.append('<aside class="facts"><dl>')
    for label, value in facts:
        if value:
            body.append(f"<dt>{esc(label)}</dt><dd>{value}</dd>")
    body.append("</dl></aside></div></main>")

    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{esc(fid)} {esc(row["name"])} - tasks</title><style>{CSS}</style>'
            f'<script>{SCRIPT}</script></head>'
            f'<body>{"".join(body)}</body></html>')


class Handler(BaseHTTPRequestHandler):
    def send_content(self, content, content_type, status=200, head_only=False, headers=None):
        out = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(out)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if not head_only:
            self.wfile.write(out)

    def send_json(self, payload, status=200, head_only=False, headers=None):
        response_headers = {"Cache-Control": "no-store", **(headers or {})}
        self.send_content(
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            "application/json; charset=utf-8",
            status,
            head_only,
            response_headers,
        )

    def serve(self, head_only=False):
        parsed = urlsplit(self.path)
        path, query = parsed.path, parsed.query
        if path == "/api" or path.startswith("/api/"):
            status, payload = api_route(path)
            self.send_json(payload, status, head_only)
            return
        match = re.fullmatch(r"/([A-Z]+-\d+)/?", path)
        rendered = detail(match.group(1), "done=hide" in query) if match else None
        if match and rendered is None:
            self.send_error(404, "no such feature on the board")
            return
        self.send_content(rendered or page(), "text/html; charset=utf-8", head_only=head_only)

    def do_GET(self):
        self.serve()

    def do_HEAD(self):
        self.serve(head_only=True)

    def method_not_allowed(self):
        self.send_json(
            api_envelope(error={
                "code": "method_not_allowed",
                "message": "The dashboard API is read-only; use GET or HEAD.",
            }),
            405,
            headers={"Allow": "GET, HEAD"},
        )

    do_POST = method_not_allowed
    do_PUT = method_not_allowed
    do_PATCH = method_not_allowed
    do_DELETE = method_not_allowed

    def log_message(self, *args):
        pass  # a refresh every ten seconds would drown the terminal


if __name__ == "__main__":
    if not Path("features/INDEX.md").is_file():
        sys.exit("no features/INDEX.md here - run this in the product repository")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    print(f"http://localhost:{port}  · API /api/v1  (ctrl-c to stop)")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
