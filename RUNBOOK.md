# Daily Pinterest pin run — characternamehub.com

Each daily run makes **5 pins** for 5 different tool pages and schedules them in Metricool
for the US evening. The campaign runs for **30 days / 150 pins** (Nov 17 – Dec 16, 2026, UTC run dates).

Never pin test designs. Never reuse a URL that is already in `state/log.json`.

## 0. Setup
```bash
git clone --depth 1 https://github.com/razzaqf299-lgtm/characternamehub-pins pins && cd pins
npm install --silent            # jsdom for extract.js
pip install pillow --break-system-packages -q 2>/dev/null || true
export CF_ACCOUNT=...  CF_TOKEN=...   # from the scheduled task's instructions
```
Metricool brand (blogId): **8139925**, timezone Asia/Karachi.

## 1. Check the campaign
Read `state/log.json` (a list of posted pins). Stop and report "campaign finished" if it already has
150 entries or today's UTC date is after 2026-12-16. Skip any URL listed in `state/skip.txt`.

## 2. Pick 5 URLs
Take the first 5 URLs from `queue.txt` that are not in the log or skip list.

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

## 8. Pick the board
Get the current board list: call Metricool `createScheduledPost` as a draft with
`pinterestData.boardId` = `"zz-list-boards-check"`; the error lists all boards with numeric ids
(nothing is created). Use the exact topic board when one exists (e.g. "Dark Elf Names"); otherwise
the best broad board (fantasy characters / creatures / places / games / anime…). Avoid "Quick Saves".
If nothing fits, use the broadest fantasy board and mention it in the report.

## 9. Title and description
- **Title:** `NUMBER ADJECTIVE SUBJECT Names With Meanings` — e.g. *2300+ Mysterious Dark Elf Names
  With Meanings*. Adjective fits the lore. Never use the words "name generator".
- **Description:** 1–2 short sentences (~150–220 characters), inspiring, saying what names they will
  get, the key features (filters, meanings, pronunciation…) and what to do (pick options, tap Generate).

## 10. Schedule in Metricool
Slots in **America/New_York** on the US evening that is in progress at run time:
20:00, 20:45, 21:30, 22:15, 23:00. Convert to Asia/Karachi for `publicationDate` and `date`.
Skip any slot less than 15 minutes in the future (shift to the next free 45-minute slot before 23:59 ET).
`info`: autoPublish true, draft false, media [raw URL], text = description, providers [{"network":"pinterest"}],
`pinterestData`: {boardId (numeric), pinTitle, pinLink = tool URL, pinNewFormat false, isAiGenerated true}.

## 11. Log and report
Append to `state/log.json`: {date, url, slug, layout, number, title, board, image_url, publish_time_et,
metricool_planner_url}. Commit and push. Then send a short report: the 5 titles, boards, times, and
any problems (generator failures, fallback model, missing boards).
