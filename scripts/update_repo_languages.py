#!/usr/bin/env python3
"""Update language composition for featured repos in README.

Currently supports reviewtask repo. Insert between markers:
<!-- LANG_REVIEWTASK_START --> ... END
"""
import os
import sys
import re
import json
import urllib.request
from pathlib import Path

OWNER = os.getenv("REPO_OWNER", "biwakonbu")
REPO = os.getenv("FEATURED_REPO", "reviewtask")
TOKEN = os.getenv("GITHUB_TOKEN")
API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/languages"
README_PATH = Path(__file__).resolve().parent.parent / "README.md"
MAX_LANGS = int(os.getenv("MAX_LANGS", "4"))

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

# Some language brand colors (Nord-adjusted tints)
LANG_COLORS = {
    "Go": "88C0D0",
    "TypeScript": "81A1C1",
    "JavaScript": "EBCB8B",
    "Rust": "D08770",
    "HTML": "5E81AC",
    "CSS": "A3BE8C",
    "Shell": "B48EAD",
}


def fetch_languages():
    req = urllib.request.Request(API_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)
    return data  # dict lang -> bytes


def format_languages(data):
    total = sum(data.values())
    if total == 0:
        return ""
    # Convert to list sorted by percentage desc
    items = [
        (lang, bytes_ * 100 / total)
        for lang, bytes_ in data.items()
    ]
    items.sort(key=lambda x: x[1], reverse=True)
    items = items[:MAX_LANGS]

    # Build colored spans with percentage rounded
    parts = []
    for lang, pct in items:
        pct_int = round(pct)
        color = LANG_COLORS.get(lang, "4C566A")  # fallback border color
        span = (
            f'<span style="color:#{color}">{lang} {pct_int}%</span>'
        )
        parts.append(span)
    return " · ".join(parts)


def update_readme(langs_html):
    start_marker = "<!-- LANG_REVIEWTASK_START -->"
    end_marker = "<!-- LANG_REVIEWTASK_END -->"
    content = README_PATH.read_text(encoding="utf-8")
    pattern = re.compile(f"{start_marker}.*?{end_marker}", re.S)
    replacement = f"{start_marker}\n                  {langs_html}\n                  {end_marker}"
    new_content, n = pattern.subn(replacement, content)
    if n == 0:
        print("Language markers not found")
        sys.exit(1)
    if new_content != content:
        README_PATH.write_text(new_content, encoding="utf-8")
        print("README updated with languages.")
    else:
        print("README language section unchanged.")


def main():
    try:
        langs_data = fetch_languages()
    except Exception as e:
        print("Failed to fetch languages:", e, file=sys.stderr)
        return
    html = format_languages(langs_data)
    update_readme(html)


if __name__ == "__main__":
    main()
