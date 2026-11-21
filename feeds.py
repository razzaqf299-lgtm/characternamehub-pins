#!/usr/bin/env python3
"""Maintain the Pinterest RSS feeds in feeds/<slug>.xml.

Usage:
  feeds.py add SLUG --title T --desc D --link URL --image IMG_URL [--guid G]
  feeds.py init            # create empty feed files for every slug in feeds/boards.json

Each feed keeps the newest 40 items. Pinterest creates a Pin for every new item
(oldest first) within ~24 hours of the feed changing.
"""
import argparse, datetime, html, json, os, re
from email.utils import format_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
FEEDS = os.path.join(HERE, "feeds")
SITE = "https://characternamehub.com"
KEEP = 40


def boards():
    return {k: v for k, v in json.load(open(os.path.join(FEEDS, "boards.json"))).items() if not k.startswith("_")}


def load_items(path):
    if not os.path.exists(path):
        return []
    return re.findall(r"<item>.*?</item>", open(path, encoding="utf-8").read(), re.S)


def write(slug, items):
    b = boards()[slug]
    now = format_datetime(datetime.datetime.now(datetime.timezone.utc))
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<title>{html.escape(b['board'])} | Character Name Hub</title>
<link>{SITE}/</link>
<atom:link href="{SITE}/pin-feeds/{slug}.xml" rel="self" type="application/rss+xml"/>
<description>New name generator pins for the {html.escape(b['board'])} board.</description>
<language>en-us</language>
<lastBuildDate>{now}</lastBuildDate>
{chr(10).join(items[:KEEP])}
</channel>
</rss>
"""
    open(os.path.join(FEEDS, slug + ".xml"), "w", encoding="utf-8").write(xml)


def add(a):
    if a.slug not in boards():
        raise SystemExit(f"Unknown feed slug {a.slug}; see feeds/boards.json")
    path = os.path.join(FEEDS, a.slug + ".xml")
    items = load_items(path)
    guid = a.guid or a.image
    if any(f"<guid isPermaLink=\"false\">{html.escape(guid)}</guid>" in it for it in items):
        print("already in feed"); return
    e = html.escape
    pub = format_datetime(datetime.datetime.now(datetime.timezone.utc))
    item = f"""<item>
<title>{e(a.title)}</title>
<link>{e(a.link)}</link>
<description>{e(a.desc)}</description>
<pubDate>{pub}</pubDate>
<guid isPermaLink="false">{e(guid)}</guid>
<enclosure url="{e(a.image)}" type="image/png" length="0"/>
<media:content url="{e(a.image)}" medium="image" type="image/png" width="1080" height="1920"/>
</item>"""
    write(a.slug, [item] + items)
    print("added to", a.slug)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("add"); s.add_argument("slug"); s.add_argument("--title", required=True)
    s.add_argument("--desc", required=True); s.add_argument("--link", required=True)
    s.add_argument("--image", required=True); s.add_argument("--guid")
    sub.add_parser("init")
    a = p.parse_args()
    if a.cmd == "add":
        add(a)
    else:
        for slug in boards():
            if not os.path.exists(os.path.join(FEEDS, slug + ".xml")):
                write(slug, [])
        print("feeds:", ", ".join(boards()))
