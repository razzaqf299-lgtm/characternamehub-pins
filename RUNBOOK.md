# Daily Pinterest pin run — characternamehub.com

Each daily run makes **5 pins** for 5 different tool pages and publishes them through
**Pinterest RSS auto-publish** (Metricool's free plan stops at 20 pins/month, so it is no longer used). The campaign runs for **30 days / 150 pins** (Nov 17 – Dec 16, 2026, UTC run dates).

Never pin test designs. Never reuse a URL that is already in `state/log.json`.

## 0. Setup
```bash
git clone --depth 1 https://github.com/razzaqf299-lgtm/characternamehub-pins pins && cd pins
npm install --silent            # jsdom for extract.js
pip install pillow --break-system-packages -q 2>/dev/null || true
export CF_ACCOUNT=...  CF_TOKEN=...   # from the scheduled task's instructions
```
Publishing: each Pinterest board has an RSS feed `feeds/<slug>.xml` in this repo (map in `feeds/boards.json`).
Hamza's site serves them at `https://characternamehub.com/pin-feeds/<slug>.xml` (WPCode snippet in
`wordpress/`), and Pinterest Settings > Auto-publish turns every new feed item into a Pin within ~24 hours.

## 1. Check the campaign
Read `state/log.json` (a list of posted pins). Stop and report "campaign finished" if it already has
150 entries or today's UTC date is after 2026-12-16. Skip any URL listed in `state/skip.txt`.

## 2. Pick 5 URLs
**Every pin must link to a URL that has never been pinned before — on any day, by any route.**
Build the "already pinned" set from ALL of these, then take the first 5 URLs from `queue.txt` not in it:
- every `url` in `state/log.json`;
- every URL in `state/skip.txt` (lines starting with `#` are comments) — includes pages Hamza pinned
  by hand before the campaign;
- every `<link>` already in any `feeds/*.xml` file.
Compare URLs normalized (lowercase, no trailing slash, ignore the `/fantasy-character-names/` path
prefix, so the same tool page is never pinned twice under two paths). The 5 picked URLs must also be
distinct from each other. If the queue runs out, stop and report it — never reuse a URL to fill a slot.

## 3. Prepare each tool
```bash
python3 prep.py URL state/data/SLUG.json
```
Gives the H1, `number` (stated number on the page, else the rounded count of unique names the
generator really produces, else 500+), and 12 male / 12 female names when the tool splits by gender.
Numbers never use commas (1800+, not 1,800+).

## 4. Choose ONE layout by the nature of the tool
- **list** — people, races and classes with real male/female names (`has_gender_split` true):
  elves, dwarves, witches, paladins, vampire hunters… Background = a painted scene of that
  creature's world (no people in it).
- **character** — everything else: creatures and monsters (dragon, werewolf, kaiju, hellhound),
  places and groups (kingdom, city, guild, clan, ship, planet), and other generators (titles,
  techniques, usernames), or when names could not be extracted. Painting = the creature/character
  itself, or the place/thing, instantly recognizable at first glance.

## 5. Generate the painting (free tier: FLUX.2 klein 9B)
```bash
python3 gen.py @cf/black-forest-labs/flux-2-klein-9b work/SLUG.jpg "PROMPT" 864 1536
```
If the daily free allocation is used up (HTTP 429), fall back to `@cf/black-forest-labs/flux-2-klein-4b`.
Prompt rules:
- Start with the subject, described so it is **recognizable at first glance** (signature features:
  ears, skin, horns, wings, weapons, outfit), **full body** for characters/creatures, face clearly lit.
- Add the setting, lighting and mood that fit the lore.
- Composition: subject in the middle and lower two-thirds; **top third darker and uncluttered** for the title.
  For list backgrounds: no people, even and darker lighting, no bright center hotspot.
- End with the style block: *Masterful realistic classical oil painting on canvas, fantasy realism like
  the great fantasy oil painters: lifelike anatomy and textures, dramatic chiaroscuro lighting, rich deep
  colors, visible brushstrokes, impasto and canvas texture. Not cartoon, not anime, not 3D render, not
  digital illustration, no text, no letters.*
Look at the image (downscale and Read it). Regenerate once if the subject is not recognizable, is cut
off, has extra limbs/garbled anatomy, or contains text.

**Franchise tools (Pokemon, Star Wars, anime, games…):** never paint copyrighted characters, creatures,
logos or exact costumes. Paint an original scene that evokes the genre instead (a cozy hometown for a
Pokemon town tool, an original robot for a mech tool, a generic hooded figure for a space-knight tool).

## 6. Compose the pin (1080×1920)
Write a spec JSON and run `python3 compose.py spec.json`:
```json
{"layout":"character","image":"work/SLUG.jpg","out":"pins/DATE/SLUG.png","number":"1400+",
 "subject":"Dragon","noun":"Names","accent":"#FFD9A8","glow":"#B3400F"}
{"layout":"list","image":"work/SLUG.jpg","out":"pins/DATE/SLUG.png","number":"2300+",
 "subject":"Dark Elf","accent":"#D9C8FF","male":[12 names],"female":[12 names]}
```
- `subject` = short creature/tool name from the H1 (e.g. "Dark Elf", "Fantasy Kingdom").
  `noun` defaults to "Names"; use "Titles", "Techniques" etc. only when that is what the tool makes.
- Heading colors must suit the painting (`accent` = heading color, `glow` = glow color for character layout).
- Look at the result (downscale and Read it): text readable, heading not covering the face, names fit.

## 7. Upload
Copy the PNG to `pins/DATE/SLUG.png` in this repo, commit and push. The public link is
`https://raw.githubusercontent.com/razzaqf299-lgtm/characternamehub-pins/main/pins/DATE/SLUG.png`
— check it returns HTTP 200 before scheduling.

## 8. Pick the feed (board)
Read `feeds/boards.json` and choose the ONE feed whose `use_for` best fits the tool. Only these 6 feeds
are connected in Pinterest; never invent a new feed slug. Never put an unrelated tool on a topic feed
(e.g. Jedi or titles are NOT dragon names; Dragon Age is a game -> `game-anime-names`).

**Every feed must contain at least one item** (Pinterest will not connect an empty feed). Before picking
the day's URLs, check each feed in `feeds/boards.json`; for every feed with 0 items, pick the first unused
queue URL that fits it and make that pin too, even if the day then has more than 5 pins (max 6).

## 9. Title and description
- **Title:** `NUMBER ADJECTIVE SUBJECT Names With Meanings` — e.g. *2300+ Mysterious Dark Elf Names
  With Meanings*. Adjective fits the lore. Never use the words "name generator".
- **Description:** 1–2 short sentences (~150–220 characters), inspiring, saying what names they will
  get, the key features (filters, meanings, pronunciation…) and what to do (pick options, tap Generate).

## 10. Publish via the feed
```bash
python3 feeds.py add FEED_SLUG --title "TITLE" --desc "DESCRIPTION" --link TOOL_URL --image RAW_IMAGE_URL
```
Then commit and push (the image, the feed file, and the log together). Pinterest picks up new items
within ~24 hours and publishes them on the feed's board, oldest first. Do not use Metricool any more.

## 11. Log and report
Append to `state/log.json`: {date, url, slug, layout, number, title, board, feed, image_url, route: "rss"}.
Commit and push. Check that `https://characternamehub.com/pin-feeds/FEED_SLUG.xml` returns HTTP 200 and
contains the new item (if it returns 404, the WPCode snippet is not active yet — the items are still saved
in the repo and will publish once it is). Then send a short report: the 5 titles, boards, and any problems
(generator failures, fallback model, feed URL not reachable).
