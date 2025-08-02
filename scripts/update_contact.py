#!/usr/bin/env python3
"""Populate contact section (X & Gmail) in README from GitHub user profile.

Uses GitHub REST API to fetch `twitter_username` and `email` fields.
If email is private (null), badge is hidden.
"""
import os
import sys
import re
from pathlib import Path
import json
import urllib.request

README_PATH = Path(__file__).resolve().parent.parent / "README.md"
USERNAME = os.getenv("GITHUB_USERNAME", "biwakonbu")
API_URL = f"https://api.github.com/users/{USERNAME}"
TOKEN = os.getenv("GITHUB_TOKEN")  # optional for higher rate limit

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def fetch_profile():
    req = urllib.request.Request(API_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)
    return data


def build_badges(twitter_username: str | None, email: str | None) -> str:
    parts = []
    if twitter_username:
        x_url = f"https://x.com/{twitter_username}"
        badge = (
            f'<a href="{x_url}"><img '
            f'src="https://img.shields.io/badge/X-%40{twitter_username}-2E3440?style=flat-square&logo=x&logoColor=88C0D0&labelColor=3B4252" /></a>'
        )
        parts.append(badge)
    if email:
        badge = (
            f'<a href="mailto:{email}"><img '
            f'src="https://img.shields.io/badge/GMail-{email}-2E3440?style=flat-square&logo=gmail&logoColor=81A1C1&labelColor=3B4252" /></a>'
        )
        parts.append(badge)
    if not parts:
        return ""
    return "\n            ".join(parts)


def update_readme(html: str):
    start_marker = "<!-- CONTACT_START -->"
    end_marker = "<!-- CONTACT_END -->"
    content = README_PATH.read_text(encoding="utf-8")
    pattern = re.compile(f"{start_marker}.*?{end_marker}", re.S)
    replacement = f"{start_marker}\n            {html}\n            {end_marker}"
    new_content, n = pattern.subn(replacement, content)
    if n == 0:
        print("Contact markers not found in README.md")
        sys.exit(1)
    if new_content != content:
        README_PATH.write_text(new_content, encoding="utf-8")
        print("Contact section updated.")
    else:
        print("Contact section unchanged.")


def main():
    try:
        profile = fetch_profile()
    except Exception as e:
        print("Failed to fetch GitHub profile:", e, file=sys.stderr)
        return
    twitter = profile.get("twitter_username")
    email = profile.get("email")
    html = build_badges(twitter, email)
    update_readme(html)


if __name__ == "__main__":
    main()
