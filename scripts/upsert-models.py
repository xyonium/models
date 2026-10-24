#!/usr/bin/env python3
"""Upsert local aistudio model overrides into an upstream models.json.

The CLIProxyAPI catalog source is a *whole-file* replacement, so we always start
from the freshly fetched upstream file and only add our own entries on top.
That keeps every other section byte-identical to upstream.

If upstream already carries one of our IDs, the upstream entry wins unless
--force is passed: the maintainers may have better metadata than we do.

Usage:
    python3 upsert-models.py upstream.json models.json [--force]
"""

import argparse
import json
import sys

# Entries we maintain locally. Keep them in sync with
# https://github.com/router-for-me/models/pull/55 and /pull/56.
OVERRIDES = [
    {
        # Insert directly after this upstream model when adding.
        "_anchor": "gemini-3.1-flash-lite-preview",
        "entry": {
            "id": "gemini-3.1-flash-lite-image",
            "object": "model",
            "created": 1782864000,
            "owned_by": "google",
            "type": "gemini",
            "display_name": "Gemini 3.1 Flash Lite Image",
            "name": "models/gemini-3.1-flash-lite-image",
            "version": "3.1",
            "description": "Our smallest and most cost effective image generation and editing model, built for at scale usage.",
            "inputTokenLimit": 65536,
            "outputTokenLimit": 4096,
            "supportedGenerationMethods": [
                "generateContent",
                "countTokens",
                "batchGenerateContent",
            ],
            "supportedInputModalities": ["text", "image"],
            "supportedOutputModalities": ["text", "image"],
        },
    },
    {
        "_anchor": "gemini-3.5-flash-lite",
        "entry": {
            "id": "gemini-3.5-transcribe",
            "object": "model",
            "created": 1787702400,
            "owned_by": "google",
            "type": "gemini",
            "display_name": "Gemini 3.5 Transcribe",
            "name": "models/gemini-3.5-transcribe",
            "version": "3.5",
            "description": "Audio transcription model: up to 1 hour of audio per request, returns text with optional word-level annotations.",
            "inputTokenLimit": 98304,
            "outputTokenLimit": 32768,
            "supportedGenerationMethods": ["generateContent", "countTokens"],
            "supportedInputModalities": ["audio"],
            "supportedOutputModalities": ["text"],
        },
    },
]

SECTION = "aistudio"


def index_of(models, model_id):
    for i, model in enumerate(models):
        if model.get("id") == model_id:
            return i
    return -1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src", help="freshly fetched upstream models.json")
    parser.add_argument("dst", help="output models.json (full replacement)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite entries upstream already provides",
    )
    args = parser.parse_args()

    with open(args.src, encoding="utf-8") as fh:
        catalog = json.load(fh)

    section = catalog.get(SECTION)
    if not isinstance(section, list):
        sys.exit(f"upstream catalog has no '{SECTION}' section; refusing to write")

    for item in OVERRIDES:
        entry = item["entry"]
        pos = index_of(section, entry["id"])
        if pos >= 0:
            if not args.force:
                print(f"skip   {entry['id']}: already upstream")
                continue
            section[pos] = entry
            print(f"update {entry['id']}: replaced upstream entry")
            continue

        anchor = index_of(section, item["_anchor"])
        if anchor >= 0:
            section.insert(anchor + 1, entry)
        else:
            section.append(entry)
        print(f"add    {entry['id']}")

    with open(args.dst, "w", encoding="utf-8") as fh:
        json.dump(catalog, fh, indent=2, ensure_ascii=False)

    # Sanity check: CPA rejects duplicate IDs inside a section at load time.
    ids = [m["id"] for m in section]
    if len(ids) != len(set(ids)):
        sys.exit("duplicate model ids in aistudio section after upsert")
    print(f"ok     {SECTION}: {len(section)} entries")


if __name__ == "__main__":
    main()
