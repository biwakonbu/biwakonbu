#!/usr/bin/env python3
"""Update README Popular Note Posts section.

Fetches https://note.com/biwakonbu, extracts articles and like counts,
selects the most liked ones, and replaces the section between
<!-- NOTE_POSTS_START --> and <!-- NOTE_POSTS_END --> in README.md.
"""

import re
import os
import sys
import requests
from bs4 import BeautifulSoup
from pathlib import Path

USERNAME = os.getenv("NOTE_USERNAME", "biwakonbu")
NOTE_URL = f"https://note.com/{USERNAME}"
README_PATH = Path(__file__).resolve().parent.parent / "README.md"
MAX_ITEMS = int(os.getenv("NOTE_MAX_ITEMS", "3"))


def fetch_articles():
    print("Fetching note.com page…", NOTE_URL)
    res = requests.get(NOTE_URL, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    article_links = soup.select("a[href^='https://note.com/{}/n/']".format(USERNAME))
    results = []
    for a in article_links:
        href = a.get("href")
        if not href:
            continue
        title_tag = a.select_one("h3, h2, p")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)

        # Like count may be in a span inside the link or sibling; attempt to find numeric
        like_tag = a.select_one("span")
        likes = 0
        if like_tag:
            m = re.search(r"\d+", like_tag.get_text())
            if m:
                likes = int(m.group())
        results.append({"title": title, "href": href, "likes": likes})

    # Deduplicate by href keeping max likes
    dedup = {}
    for item in results:
        href = item["href"]
        if href not in dedup or item["likes"] > dedup[href]["likes"]:
            dedup[href] = item

    return list(dedup.values())


def format_items(items):
    lines = []
    for it in items:
        title = it["title"]
        href = it["href"]
        likes = it["likes"]
        heart = "\u2665"
        line = f"• <a href=\"{href}\" style=\"color:#81A1C1;\">{title}</a> ({likes}{heart})"
        lines.append(line)
    # HTML line breaks
    return "<br/>\n            ".join(lines)


def update_readme(rendered_html):
    content = README_PATH.read_text(encoding="utf-8")
    start_marker = "<!-- NOTE_POSTS_START -->"
    end_marker = "<!-- NOTE_POSTS_END -->"

    pattern = re.compile(f"{start_marker}.*?{end_marker}", re.S)
    replacement = f"{start_marker}\n            {rendered_html}\n            {end_marker}"

    new_content, count = pattern.subn(replacement, content)
    if count == 0:
        print("Markers not found in README.md, aborting.")
        sys.exit(1)
    if new_content != content:
        README_PATH.write_text(new_content, encoding="utf-8")
        print("README.md updated.")
    else:
        print("No changes to README.md.")


def main():
    articles = fetch_articles()
    if not articles:
        print("No articles found, abort.")
        return
    articles.sort(key=lambda x: x["likes"], reverse=True)
    top_items = articles[:MAX_ITEMS]
    html = format_items(top_items)
    update_readme(html)


if __name__ == "__main__":
    main()
