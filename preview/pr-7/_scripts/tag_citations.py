#!/usr/bin/env python3
"""
Generate theme tags for citations based on keywords in the title/publisher.

This keeps Manubot/ORCID-generated `_data/citations.yaml` untouched and writes
tags to `_data/citation_tags.yaml`, which the site merges at render time.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "_data" / "citations.yaml"
OUTPUT = ROOT / "_data" / "citation_tags.yaml"

# Research themes and associated keywords (case-insensitive).
THEME_KEYWORDS = {
    "Medical Image Analysis": [
        "mri",
        "magnetic resonance",
        "ct",
        "scan",
        "reconstruction",
        "registration",
        "segmentation",
        "radiology",
        "lung",
        "airway",
        "pulmonary",
        "chest",
        "biomedical imaging",
    ],
    "Computer Vision": [
        "computer vision",
        "vision",
        "video",
        "recognition",
        "detection",
        "classification",
        "tracking",
        "scene",
        "camera",
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
        "bioacoustic",
        "ecoacoustic",
        "soundscape",
        "bird",
        "frog",
    ],
    "Machine Learning": [
        "machine learning",
        "probabilistic",
        "bayesian",
        "uncertainty",
        "latent",
        "representation",
        "inference",
        "neural",
        "deep",
        "variational",
    ],
}

PUBLISHER_THEME_MAP = {
    "ecological informatics": "Ecological Monitoring",
    "bioacoustics": "Ecological Monitoring",
    "machine learning for biomedical imaging": "Medical Image Analysis",
    "physics in medicine & biology": "Medical Image Analysis",
    "medical imaging": "Medical Image Analysis",
    "computer vision and pattern recognition": "Computer Vision",
    "cvpr": "Computer Vision",
    "wacv": "Computer Vision",
}


def load_citations() -> list[dict]:
    if not INPUT.exists():
        raise FileNotFoundError(f"Missing citations file: {INPUT}")
    return yaml.safe_load(INPUT.read_text(encoding="utf-8")) or []


def detect_themes(text: str, publisher: str = "") -> list[str]:
    hits = []
    lower = text.lower()

    # publisher cues
    pub = publisher.lower()
    for key, theme in PUBLISHER_THEME_MAP.items():
        if key in pub:
            hits.append(theme)

    # first pass: everything except Machine Learning
    for theme, keywords in THEME_KEYWORDS.items():
        if theme == "Machine Learning":
            continue
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", lower):
                hits.append(theme)
                break

    if hits:
        return list(set(hits))

    # only tag as Machine Learning if explicit ML keywords appear
    for kw in THEME_KEYWORDS["Machine Learning"]:
        if re.search(rf"\b{re.escape(kw)}\b", lower):
            return ["Machine Learning"]
    return []


def build_tags(entry: dict) -> list[str]:
    title = entry.get("title") or ""
    publisher = entry.get("publisher") or ""
    keywords = entry.get("keywords") or []
    blob = " ".join([title, publisher] + keywords)
    tags = detect_themes(blob, publisher)
    return tags  # empty list if no theme hit


def main() -> int:
    citations = load_citations()

    tagged = []
    for entry in citations:
        if not entry.get("id"):
            continue
        cid = entry.get("id")
        tags = build_tags(entry)

        tagged.append(
            {
                "id": cid,
                "tags": tags,
            }
        )

    OUTPUT.write_text(
        "# DO NOT EDIT, GENERATED AUTOMATICALLY FROM citations.yaml\n"
        + yaml.safe_dump(tagged, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"Wrote {len(tagged)} tagged citations to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
