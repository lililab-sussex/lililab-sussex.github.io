#!/usr/bin/env python3
"""
Fetch publications from ORCID for all members with an ORCID ID and write _data/citations.yaml.
This keeps the publications list in sync with lab members.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MEMBERS_DIR = ROOT / "_members"
OUTPUT = ROOT / "_data" / "citations.yaml"

# Theme tagging keywords for the four main areas.
THEME_KEYWORDS = {
    "Medical Image Analysis": [
        "mri",
        "magnetic resonance",
        "imaging",
        "ct",
        "scan",
        "segmentation",
        "reconstruction",
        "registration",
    ],
    "Computer Vision": [
        "vision",
        "image",
        "video",
        "recognition",
        "detection",
        "classification",
        "tracking",
        "object",
        "scene",
    ],
    "Ecological Monitoring": [
        "ecology",
        "environment",
        "species",
        "wildlife",
        "habitat",
        "conservation",
        "monitoring",
        "acoustic",
        "ecoacoustic",
        "ecoacoustics",
        "bioacoustic",
        "bioacoustics",
    ],
    "Machine Learning": [
        "learning",
        "model",
        "bayesian",
        "probabilistic",
        "neural",
        "uncertainty",
        "inference",
    ],
}


def load_members() -> list[dict]:
    members = []
    for path in MEMBERS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        fm, _ = text.split("---", 2)[1:]
        data = yaml.safe_load(fm)
        orcid = data.get("links", {}).get("orcid")
        if orcid:
            members.append({"name": data.get("name", ""), "orcid": orcid})
    return members


def fetch_orcid_works(orcid: str) -> list[dict]:
    url = f"https://pub.orcid.org/v3.0/{orcid}/works"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:  # nosec
        data = json.load(resp)
    groups = data.get("group") or []
    works = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        summaries = group.get("work-summary") or []
        if not summaries:
            continue
        summary = summaries[0] or {}
        title = (
            summary.get("title", {})
            .get("title", {})
            .get("value")
            or "[no title]"
        )
        pub_date = summary.get("publication-date", {}) or {}
        year = (pub_date.get("year") or {}).get("value")
        month = (pub_date.get("month") or {}).get("value")
        day = (pub_date.get("day") or {}).get("value")
        date_parts = [p for p in [year, month, day] if p]
        date_str = "-".join(date_parts) if date_parts else None
        external_ids = summary.get("external-ids", {}).get("external-id", []) or []
        doi = next(
            (
                eid.get("external-id-value")
                for eid in external_ids
                if (eid.get("external-id-type") or "").lower() == "doi"
            ),
            None,
        )
        link = (summary.get("url") or {}).get("value")
        works.append(
            {
                "id": f"doi:{doi}" if doi else summary.get("put-code"),
                "put_code": summary.get("put-code"),
                "title": title,
                "authors": [],  # ORCID summary doesn’t list full authors.
                "publisher": (summary.get("journal-title") or {}).get("value")
                or summary.get("type")
                or "[no publisher info]",
                "date": date_str or "[no date info]",
                "link": f"https://doi.org/{doi}" if doi else link,
                "orcid": orcid,
                "source": "orcid",
            }
        )
    return works


def tag_themes(title: str, keywords: list[str] | None = None, publisher: str = "") -> list[str]:
    """
    Assign themes based on title plus any keyword strings we can extract
    from ORCID metadata. Falls back to Machine Learning if nothing matches.
    """
    tags = []
    blobs = [title or "", publisher or ""] + (keywords or [])
    low = " ".join(blobs).lower()
    for theme, kw_list in THEME_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(kw)}\b", low) for kw in kw_list):
            tags.append(theme)
    if not tags:
        tags.append("Machine Learning")
    return tags


def fetch_work_keywords(orcid: str, put_code: str | None) -> list[str]:
    """
    Fetch keywords/subjects for a specific ORCID work (best effort).
    """
    if not put_code:
        return []
    url = f"https://pub.orcid.org/v3.0/{orcid}/work/{put_code}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # nosec
            data = json.load(resp)
    except Exception:
        return []

    keywords = []
    kw_block = data.get("keywords", {}).get("keyword", []) or []
    for kw in kw_block:
        val = kw.get("content") or kw.get("value")
        if val:
            keywords.append(val)

    # Some records use "subject" or "title" inside a "citation" block.
    subject = data.get("title", {}).get("subtitle", {}).get("value")
    if subject:
        keywords.append(subject)

    return keywords


def main() -> int:
    members = load_members()
    unique_orcids = sorted({m["orcid"] for m in members if m.get("orcid")})
    if not unique_orcids:
        print("No ORCID IDs found in members.")
        return 1

    all_works = []
    for orcid in unique_orcids:
        try:
            works = fetch_orcid_works(orcid)
            for w in works:
                kw = fetch_work_keywords(orcid, w.get("put_code"))
                if kw:
                    w["keywords"] = kw
                w["tags"] = tag_themes(w.get("title", ""), kw, w.get("publisher", ""))
            all_works.extend(works)
        except urllib.error.HTTPError as e:
            print(f"Failed to fetch {orcid}: {e}", file=sys.stderr)
        except Exception as e:  # pragma: no cover - best effort
            import traceback

            print(f"Unexpected error for {orcid}: {e}", file=sys.stderr)
            traceback.print_exc()

    # De-duplicate by id
    seen = set()
    deduped = []
    for w in all_works:
        if w["id"] in seen:
            continue
        seen.add(w["id"])
        w.pop("put_code", None)
        deduped.append(w)

    deduped.sort(key=lambda w: w.get("date", ""), reverse=True)

    OUTPUT.write_text(
        "# DO NOT EDIT, GENERATED AUTOMATICALLY FROM ORCID\n"
        + yaml.safe_dump(deduped, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"Wrote {len(deduped)} entries to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
