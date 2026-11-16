#!/usr/bin/env python3
"""Prepare pin data for one characternamehub.com tool URL.

Usage: prep.py URL [OUTJSON]
Fetches the page, runs its generator in jsdom (extract.js), and prints JSON:
  url, slug, h1, meta_title, stated_number, sampled_count, number (string for the pin),
  has_gender_split, male (12), female (12), any (12)
"""
import json
import math
import os
import random
import re
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FEM_END = ("a", "ia", "iel", "ella", "ara", "essa", "istra", "thel", "ae", "ira", "ina", "yra", "elle", "ette", "ielle", "lyn", "wyn")
MASC_WORDS = ("blade", "fang", "fall", "maw", "claw", "bane", "fist", "skull", "storm", "fire", "thorn", "glimmer", "dream", "hune")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (pin-builder)"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "ignore")


def clean(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t or "")).strip()


def stated_number(text):
    nums = [int(n.replace(",", "")) for n in re.findall(r"(\d[\d,]{1,6})\s*\+", text)]
    nums = [n for n in nums if n >= 50]
    return max(nums) if nums else None


def round_down(n):
    if n >= 1000:
        return n // 100 * 100
    if n >= 100:
        return n // 50 * 50
    return max(10, n // 10 * 10)


def pick(names, k=12):
    good = [n for n in names if 3 <= len(n) <= 11 and n[0].isupper() and " " not in n.strip()]
    if len(good) < k:
        good = [n for n in names if len(n) <= 14]
    random.shuffle(good)
    # prefer names without apostrophes, but allow a couple
    plain = [n for n in good if "'" not in n]
    out = plain[:k]
    if len(out) < k:
        out += [n for n in good if n not in out][: k - len(out)]
    return sorted(out, key=lambda s: random.random())


def main():
    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    slug = url.rstrip("/").split("/")[-1]
    html = fetch(url)
    os.makedirs(os.path.join(HERE, "pages"), exist_ok=True)
    page = os.path.join(HERE, "pages", slug + ".html")
    open(page, "w").write(html)

    h1 = clean((re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S) or [None, ""])[1])
    title = clean((re.search(r"<title>(.*?)</title>", html, re.S) or [None, ""])[1])
    desc = (re.search(r'<meta name="description" content="([^"]*)"', html) or [None, ""])[1]
    stated = stated_number(" ".join([h1, title, desc]))

    data = {}
    try:
        res = subprocess.run(["timeout", "100", "node", os.path.join(HERE, "extract.js"), page, "150"],
                             capture_output=True, text=True, timeout=120)
        data = json.loads(res.stdout.strip().splitlines()[-1]) if res.stdout.strip() else {"error": "no output"}
    except Exception as e:  # noqa
        data = {"error": str(e)}

    count = data.get("count", 0) if "error" not in data else 0
    if stated:
        number = f"{stated}+"
    elif count >= 50:
        number = f"{round_down(count)}+"
    else:
        number = "500+"

    male, female, anyn = data.get("male", []), data.get("female", []), data.get("any", [])
    split = bool(data.get("hasGender")) and bool(male) and bool(female)
    if split and not data.get("genderEffective"):
        # gender filter does not change output: split the pool by name endings
        pool = sorted(set(male) | set(female))
        female = [n for n in pool if n.lower().endswith(FEM_END) and not any(w in n.lower() for w in MASC_WORDS)]
        male = [n for n in pool if n not in set(female) and not n.lower().endswith(("a", "ia", "ae", "e", "ie", "y"))]
        split = len(male) >= 12 and len(female) >= 12
    result = {
        "url": url,
        "slug": slug,
        "h1": h1,
        "meta_title": title,
        "stated_number": stated,
        "sampled_count": count,
        "number": number,
        "has_gender_split": split,
        "male": pick(male) if split else [],
        "female": pick(female) if split else [],
        "any": pick(anyn or (male + female), 24),
        "extract_error": data.get("error"),
    }
    s = json.dumps(result, indent=1, ensure_ascii=False)
    if out:
        open(out, "w").write(s)
    print(s)


if __name__ == "__main__":
    main()
