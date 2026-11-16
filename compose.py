#!/usr/bin/env python3
"""Compose 1080x1920 Pinterest pins for characternamehub.com.

Layouts:
  character  -- painted character + big glowing heading (number / NAMES / WITH MEANINGS)
  list       -- themed background + heading + male names, divider, female names

Usage (JSON spec on stdin or as file arg):
{
  "layout": "character" | "list",
  "image": "path/to/painting.jpg",
  "out": "out/pin.png",
  "number": "1,800+",
  "subject": "Dark Elf",            # heading text -> "DARK ELF NAMES"
  "accent": "#E6DDF5",              # heading color (character) / subline color (list)
  "glow": "#6B2FA3",                # glow color for character heading
  "heading_font": "Cinzel",         # character layout heading font
  "male": [...], "female": [...]    # list layout, up to 10 each
}
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
W, H = 1080, 1920
SITE = "characternamehub.com"


def font(name, size, weight=700):
    f = ImageFont.truetype(os.path.join(FONTS, name + ".ttf"), size)
    try:
        axes = f.get_variation_axes()
        vals = []
        for a in axes:
            n = a.get("name", b"")
            n = n.decode() if isinstance(n, bytes) else str(n)
            if n.lower().startswith(("weight", "wght")):
                vals.append(max(a["minimum"], min(a["maximum"], weight)))
            else:
                vals.append(a.get("default", a["minimum"]))
        f.set_variation_by_axes(vals)
    except Exception:
        pass
    return f


def fit(name, text, max_w, start, weight=700, min_size=40):
    size = start
    while size > min_size:
        f = font(name, size, weight)
        if f.getbbox(text)[2] - f.getbbox(text)[0] <= max_w:
            return f
        size -= 4
    return font(name, min_size, weight)


def cover(img_path):
    im = Image.open(img_path).convert("RGB")
    scale = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    x = (im.width - W) // 2
    y = (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def gradient(base, top_alpha=230, top_h=760, bottom_alpha=170, bottom_h=320):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = ov.load()
    for y in range(H):
        a = 0
        if y < top_h:
            a = int(top_alpha * (1 - y / top_h) ** 1.4)
        elif y > H - bottom_h:
            a = int(bottom_alpha * ((y - (H - bottom_h)) / bottom_h) ** 1.6)
        for x in range(W):
            px[x, y] = (0, 0, 0, a)
    return Image.alpha_composite(base.convert("RGBA"), ov)


def centered(draw, y, text, f, fill, stroke=0, stroke_fill=None):
    b = draw.textbbox((0, 0), text, font=f, stroke_width=stroke)
    x = (W - (b[2] - b[0])) // 2 - b[0]
    draw.text((x, y - b[1]), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return y + (b[3] - b[1])


def glow_text(canvas, lines, glow_rgb, radius=18, strength=2):
    """lines: list of (y, text, font, fill). Draws a soft colored glow then the text."""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for y, text, f, _ in lines:
        centered(d, y, text, f, glow_rgb + (255,), stroke=6, stroke_fill=glow_rgb + (255,))
    g = layer.filter(ImageFilter.GaussianBlur(radius))
    for _ in range(strength):
        canvas = Image.alpha_composite(canvas, g)
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    for y, text, f, _ in lines:
        centered(ds, y + 6, text, f, (0, 0, 0, 200))
    canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(canvas)
    for y, text, f, fill in lines:
        centered(d, y, text, f, fill)
    return canvas


def footer(canvas, f, fill=(255, 255, 255, 235), y=1830, stroke=0):
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    centered(ImageDraw.Draw(sh), y + 3, SITE if stroke == 0 else SITE.upper(), f, (0, 0, 0, 220))
    canvas = Image.alpha_composite(canvas, sh.filter(ImageFilter.GaussianBlur(4)))
    d = ImageDraw.Draw(canvas)
    centered(d, y, SITE if stroke == 0 else SITE.upper(), f, fill, stroke=stroke, stroke_fill=(0, 0, 0, 255))
    return canvas


def character(spec):
    canvas = gradient(cover(spec["image"]))
    accent = hex_rgb(spec.get("accent", "#E6DDF5"))
    glow = hex_rgb(spec.get("glow", "#6B2FA3"))
    hf = spec.get("heading_font", "Cinzel")
    title = f"{spec['subject'].upper()} {spec.get('noun', 'Names').upper()}"
    f_num = font(hf, 210, 900)
    f_title = fit(hf, title, W - 110, 150, 900)
    f_sub = fit(hf, spec.get("subline", "WITH MEANINGS").upper(), W - 300, 78, 700)
    y = 70
    lines = []
    lines.append((y, spec["number"], f_num, accent + (255,)))
    y += (f_num.getbbox(spec["number"])[3] - f_num.getbbox(spec["number"])[1]) + 34
    lines.append((y, title, f_title, accent + (255,)))
    y += (f_title.getbbox(title)[3] - f_title.getbbox(title)[1]) + 30
    lines.append((y, spec.get("subline", "WITH MEANINGS").upper(), f_sub, (255, 255, 255, 240)))
    canvas = glow_text(canvas, lines, glow)
    canvas = footer(canvas, font("Cinzel", 44, 700), y=1838)
    return canvas


def name_list(spec):
    base = cover(spec["image"]).convert("RGBA")
    base = Image.alpha_composite(base, Image.new("RGBA", (W, H), (0, 0, 0, 120)))
    canvas = gradient(base, top_alpha=200, top_h=420, bottom_alpha=200, bottom_h=260)
    d = ImageDraw.Draw(canvas)
    accent = hex_rgb(spec.get("accent", "#D9C8FF"))
    head = f"{spec['number']} {spec['subject']} {spec.get('noun', 'Names')}"
    f_head = fit("Montserrat", head, W - 70, 120, 900)
    f_sub = font("Montserrat", 70, 800)
    f_label = font("Montserrat", 92, 900)
    male, female = spec["male"][:12], spec["female"][:12]
    f_name = fit("Fredoka", max(male + female, key=len), 470, 84, 600)
    white, black = (255, 255, 255, 255), (0, 0, 0, 255)

    y = 80
    y = centered(d, y, head, f_head, white, stroke=7, stroke_fill=black) + 26
    y = centered(d, y, spec.get("subline", "With Meanings"), f_sub, accent + (255,), stroke=5, stroke_fill=black) + 80

    cols = [(W // 4 + 5, "Male", male), (3 * W // 4 - 5, "Female", female)]

    def at(cx, top, text, f, fill, stroke):
        b = d.textbbox((0, 0), text, font=f, stroke_width=stroke)
        d.text((cx - (b[2] - b[0]) // 2 - b[0], top - b[1]), text, font=f, fill=fill,
               stroke_width=stroke, stroke_fill=black)
        return b[3] - b[1]

    label_top = y
    lh = max(at(cx, y, label, f_label, white, 6) for cx, label, _ in cols)
    y += lh + 34
    # horizontal divider under the labels
    d.rounded_rectangle((70, y + 2, W - 70, y + 10), radius=4, fill=(0, 0, 0, 190))
    d.rounded_rectangle((70, y - 2, W - 70, y + 5), radius=4, fill=(255, 255, 255, 240))
    y += 52

    rows = max(len(male), len(female))
    row_h = min(108, (1770 - y) // max(rows, 1))
    for cx, _, names in cols:
        for i, n in enumerate(names):
            at(cx, y + i * row_h, n, f_name, white, 5)

    # vertical divider between the Male and Female columns
    bottom = y + rows * row_h - (row_h - f_name.size) // 2
    d.rounded_rectangle((W // 2 + 1, label_top - 6, W // 2 + 9, bottom), radius=4, fill=(0, 0, 0, 190))
    d.rounded_rectangle((W // 2 - 3, label_top - 10, W // 2 + 4, bottom - 4), radius=4, fill=(255, 255, 255, 240))

    canvas = footer(canvas, font("Oswald", 56, 700), y=1820, stroke=4)
    return canvas


def main():
    spec = json.load(open(sys.argv[1]) if len(sys.argv) > 1 else sys.stdin)
    img = character(spec) if spec["layout"] == "character" else name_list(spec)
    os.makedirs(os.path.dirname(spec["out"]) or ".", exist_ok=True)
    img.convert("RGB").save(spec["out"], "PNG", optimize=True)
    print(spec["out"])


if __name__ == "__main__":
    main()
