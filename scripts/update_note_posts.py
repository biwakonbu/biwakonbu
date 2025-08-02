#!/usr/bin/env python3
"""Update README Popular Note Posts section.

Fetches RSS feed from https://note.com/biwakonbu/rss, extracts articles,
selects the most recent ones, and replaces the section between
<!-- NOTE_POSTS_START --> and <!-- NOTE_POSTS_END --> in README.md.
"""

import re
import os
import sys
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

USERNAME = os.getenv("NOTE_USERNAME", "biwakonbu")
RSS_URL = f"https://note.com/{USERNAME}/rss"
README_PATH = Path(__file__).resolve().parent.parent / "README.md"
MAX_ITEMS = int(os.getenv("NOTE_MAX_ITEMS", "3"))


def fetch_articles():
    print("Fetching RSS feed…", RSS_URL)
    res = requests.get(RSS_URL, timeout=15)
    res.raise_for_status()
    
    # Parse XML
    root = ET.fromstring(res.content)
    
    # Find all items in the RSS feed
    items = root.findall(".//item")
    results = []
    
    for item in items:
        title_elem = item.find("title")
        link_elem = item.find("link")
        pub_date_elem = item.find("pubDate")
        
        if title_elem is None or link_elem is None:
            continue
            
        title = title_elem.text.strip() if title_elem.text else ""
        href = link_elem.text.strip() if link_elem.text else ""
        
        # Parse publication date
        pub_date = None
        if pub_date_elem is not None and pub_date_elem.text:
            try:
                # RSS date format: "Mon, 02 Jan 2006 15:04:05 MST"
                pub_date = datetime.strptime(pub_date_elem.text, "%a, %d %b %Y %H:%M:%S %Z")
            except ValueError:
                try:
                    # Alternative format without timezone
                    pub_date = datetime.strptime(pub_date_elem.text[:25], "%a, %d %b %Y %H:%M:%S")
                except ValueError:
                    pub_date = None
        
        if title and href:
            results.append({
                "title": title, 
                "href": href, 
                "pub_date": pub_date
            })
    
    return results


def format_items(items):
    lines = []
    for it in items:
        title = it["title"]
        href = it["href"]
        pub_date = it["pub_date"]
        
        # Format date
        date_str = ""
        if pub_date:
            date_str = f" ({pub_date.strftime('%Y-%m-%d')})"
        
        line = f"• <a href=\"{href}\" style=\"color:#81A1C1;\">{title}</a>{date_str}"
        lines.append(line)
    # HTML line breaks
    return "<br/>\n".join(lines)


def update_readme(rendered_html):
    content = README_PATH.read_text(encoding="utf-8")
    start_marker = "<!-- NOTE_POSTS_START -->"
    end_marker = "<!-- NOTE_POSTS_END -->"

    pattern = re.compile(f"{start_marker}.*?{end_marker}", re.S)
    replacement = f"{start_marker}\n{rendered_html}\n{end_marker}"

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
    
    # Sort by publication date (newest first)
    articles_with_date = [a for a in articles if a["pub_date"] is not None]
    articles_without_date = [a for a in articles if a["pub_date"] is None]
    
    articles_with_date.sort(key=lambda x: x["pub_date"], reverse=True)
    sorted_articles = articles_with_date + articles_without_date
    
    top_items = sorted_articles[:MAX_ITEMS]
    html = format_items(top_items)
    update_readme(html)


if __name__ == "__main__":
    main()
