"""One-off: turn the kanban CSV into a GitHub Issue hierarchy.

For each workstream (the CSV's "Epic" column) we create one **parent** issue named
for the workstream, then create every card in it as a **sub-issue** linked under
that parent via GitHub's native sub-issues API. Cards keep sprint/priority labels.

Run from the repo root with gh authenticated:  python scripts/upload_kanban_issues.py
Single-use import — re-running would create duplicates.
"""

import csv
import json
import subprocess
import sys
import time
from collections import OrderedDict
from pathlib import Path

CSV = Path("global_ai_conversation_analytics_kanban_cards.csv")
PRIORITY_COLOR = {"High": "b60205", "Medium": "fbca04", "Low": "0e8a16"}
SPRINT_COLOR = "1d76db"
PARENT_COLOR = "0b5394"
PAUSE = 0.3  # be gentle with GitHub's secondary rate limits


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True)


def repo_slug() -> str:
    res = run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
    return res.stdout.strip()


def ensure_label(name: str, color: str) -> None:
    run(["gh", "label", "create", name, "--color", color, "--force"])


def create_issue(repo: str, title: str, body: str, labels: list[str]) -> dict:
    """Create via the API so we get the issue's numeric id (needed to link sub-issues)."""
    args = ["gh", "api", "--method", "POST", f"repos/{repo}/issues",
            "-f", f"title={title}", "-f", f"body={body}"]
    for label in labels:
        args += ["-f", f"labels[]={label}"]
    res = run(args)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip())
    return json.loads(res.stdout)


def link_sub_issue(repo: str, parent_number: int, child_id: int) -> subprocess.CompletedProcess:
    return run(["gh", "api", "--method", "POST",
                f"repos/{repo}/issues/{parent_number}/sub_issues",
                "-F", f"sub_issue_id={child_id}"])


def main() -> None:
    repo = repo_slug()
    if not repo:
        sys.exit("Could not determine repo (is gh authenticated and a remote set?)")
    rows = list(csv.DictReader(CSV.open()))

    # Group cards by workstream, preserving first-seen order.
    groups: "OrderedDict[str, list[dict]]" = OrderedDict()
    for r in rows:
        groups.setdefault(r["Epic"], []).append(r)

    print(f"Repo: {repo} | {len(groups)} parent workstreams | {len(rows)} cards")

    # Labels: sprint + priority (no 'epic' labels — hierarchy handles grouping).
    for s in sorted({r["Sprint"] for r in rows}):
        ensure_label(f"sprint: {s}", SPRINT_COLOR)
    for p, c in PRIORITY_COLOR.items():
        ensure_label(f"priority: {p}", c)
    ensure_label("workstream", PARENT_COLOR)

    created = 0
    linked = 0
    for workstream, cards in groups.items():
        card_list = "\n".join(f"- {c['Card ID']} — {c['Title']}" for c in cards)
        parent_body = (
            f"Parent issue for the **{workstream}** workstream "
            f"({len(cards)} cards). Sub-issues are linked below.\n\n{card_list}"
        )
        parent = create_issue(repo, workstream, parent_body, ["workstream"])
        print(f"\n#{parent['number']}  {workstream}  ({len(cards)} cards)")
        time.sleep(PAUSE)

        for c in cards:
            title = f"{c['Card ID']} — {c['Title']}"
            body = (
                f"**Workstream:** {workstream}  \n"
                f"**Sprint:** {c['Sprint']} · **Category:** {c['Category']} · "
                f"**Priority:** {c['Priority']} · **Story Points:** {c['Story Points']}  \n"
                f"**Owner:** {c['Owner']}\n\n"
                f"**Description:** {c['Description']}\n\n"
                f"**Acceptance Criteria:** {c['Acceptance Criteria']}\n\n"
                f"**Dependencies:** {c['Dependencies']}  \n"
                f"**Deliverable:** {c['Deliverable']}"
            )
            labels = [f"sprint: {c['Sprint']}", f"priority: {c['Priority']}"]
            try:
                child = create_issue(repo, title, body, labels)
                created += 1
            except RuntimeError as e:
                print(f"   FAILED create {c['Card ID']}: {e}", file=sys.stderr)
                continue
            time.sleep(PAUSE)
            res = link_sub_issue(repo, parent["number"], child["id"])
            if res.returncode == 0:
                linked += 1
                print(f"   ↳ #{child['number']}  {c['Card ID']}")
            else:
                print(f"   ↳ #{child['number']}  {c['Card ID']}  (link failed: {res.stderr.strip()})",
                      file=sys.stderr)
            time.sleep(PAUSE)

    print(f"\nDone. Parents: {len(groups)} | Sub-issues created: {created} | linked: {linked}")


if __name__ == "__main__":
    main()
