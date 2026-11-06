#!/usr/bin/env python3
"""
Food Run creative generator.
Usage:
  python3 creative_gen.py deals.json photos/ out/
- deals.json: list of {"id","title","sub","price","photo","daypart","badge"}
- photos/: raw food photos (jpg/png). If photo missing -> stylised gradient background.
Outputs per deal: out/<id>_1x1.jpg (1080x1080), out/<id>_9x16.jpg (1080x1920)
All text comes from deals.json — only website-verified prices go in there.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import os as _os
FONT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "fonts") + "/"
if not _os.path.exists(FONT_DIR): FONT_DIR = "/usr/share/fonts/opentype/inter/"
def font(size, weight="Bold"):
    for name in (f"InterDisplay-{weight}.otf", f"Inter-{weight}.otf", f"Inter-{weight}.ttf"):
        p = os.path.join(FONT_DIR, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)

BRAND_GREEN = (151, 234, 22)   # Food Run lime (sampled from logo)
LOGO = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")).convert("RGBA") if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")) else None
BRAND_YELLOW = (151, 234, 22)  # use brand lime for price + badge
DARK = (14, 14, 16)
WHITE = (255, 255, 255)

def cover(img, W, H, ay=0.62):
    r = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * r) + 1, int(img.height * r) + 1), Image.LANCZOS)
    x = (img.width - W) // 2; y = int((img.height - H) * ay)
    return img.crop((x, y, x + W, y + H))

def bg(photo_path, W, H):
    if photo_path and os.path.exists(photo_path):
        im = Image.open(photo_path).convert("RGB")
        if True:  # photo fills top ~60%, dark panel below, soft blend (both formats)
            canvas = Image.new("RGB", (W, H), DARK)
            ph = int(H * (0.68 if H > W * 1.2 else 0.60))
            top = cover(im, W, ph)
            canvas.paste(top, (0, 0))
            # blend band so the photo fades into the dark panel
            band = int(H * 0.12)
            mask = Image.new("L", (W, band))
            for y in range(band):
                mask.putpixel((0, y), int(255 * (y / band) ** 1.2))
            mask = mask.resize((W, band))
            dark = Image.new("RGB", (W, band), DARK)
            region = canvas.crop((0, ph - band, W, ph))
            canvas.paste(Image.composite(dark, region, mask), (0, ph - band))
            return canvas
        return cover(im, W, H)
    # stylised fallback: dark radial gradient
    im = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(im)
    for i in range(60, 0, -1):
        c = int(14 + (60 - i) * 0.6)
        d.ellipse([W//2 - i*W//60, H//2 - i*H//60, W//2 + i*W//60, H//2 + i*H//60], fill=(c, c+8, c))
    return im

def gradient_overlay(im, top_alpha=0, bottom_alpha=220):
    W, H = im.size
    ov = Image.new("L", (1, H))
    for y in range(H):
        t = y / H
        a = int(top_alpha + (bottom_alpha - top_alpha) * (t ** 1.6))
        ov.putpixel((0, y), a)
    ov = ov.resize((W, H))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(black, im, ov)

def pill(d, xy, text, f, fill, color):
    x, y = xy
    tw = d.textlength(text, font=f); th = f.size
    pad = int(f.size * 0.45)
    d.rounded_rectangle([x, y, x + tw + pad*2, y + th + pad*1.3], radius=(th + pad)//2, fill=fill)
    d.text((x + pad, y + pad*0.55), text, font=f, fill=color)
    return y + th + pad*1.3

def render(deal, photo_dir, W, H):
    im = bg(os.path.join(photo_dir, deal.get("photo", "")) if deal.get("photo") else None, W, H)
    im = gradient_overlay(im)
    d = ImageDraw.Draw(im)
    s = (W / 1080) * (0.78 if H <= W * 1.2 else 1.0)  # scale (smaller type on 1:1)
    m = int(64 * s)

    # top-left badge (daypart / 24 hours)
    y = m
    y = pill(d, (m, y), deal.get("badge", "OPEN 24 HOURS"), font(int(34*s), "Bold"), BRAND_YELLOW, DARK)

    # brand top-right
    if LOGO is not None:
        lh = int(56 * s); lw = int(LOGO.width * lh / LOGO.height)
        lg = LOGO.resize((lw, lh), Image.LANCZOS)
        im.paste(lg, (W - m - lw, m + int(4*s)), lg)
    else:
        bf = font(int(40*s), "Bold")
        d.text((W - m - d.textlength("Food Run", font=bf), m + 8), "Food Run", font=bf, fill=WHITE)

    # bottom block
    price_f = font(int(190*s), "Black") if os.path.exists(FONT_DIR+"InterDisplay-Black.otf") else font(int(190*s), "Bold")
    title_f = font(int(78*s), "Bold")
    sub_f = font(int(40*s), "Medium")
    cta_f = font(int(40*s), "Bold")

    yb = H - m
    # CTA bar
    cta = "Order now  •  foodrun.store"
    cta_h = int(96*s)
    d.rounded_rectangle([m, yb - cta_h, W - m, yb], radius=int(24*s), fill=BRAND_GREEN)
    d.text((m + int(32*s), yb - cta_h + (cta_h - cta_f.size)//2 - 4), cta, font=cta_f, fill=DARK)
    yb -= cta_h + int(36*s)

    # sub
    sub = deal.get("sub", "")
    if sub:
        d.text((m, yb - sub_f.size), sub, font=sub_f, fill=(230, 230, 230))
        yb -= sub_f.size + int(18*s)

    # price
    price = f"Rs {deal['price']}"
    d.text((m, yb - price_f.size * 1.05), price, font=price_f, fill=BRAND_YELLOW)
    yb -= int(price_f.size * 1.05) + int(8*s)

    # title
    d.text((m, yb - title_f.size * 1.1), deal["title"], font=title_f, fill=WHITE)
    return im

def main():
    deals_path, photo_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    deals = json.load(open(deals_path))
    for deal in deals:
        for tag, (W, H) in {"1x1": (1080, 1080), "9x16": (1080, 1920)}.items():
            im = render(deal, photo_dir, W, H)
            p = os.path.join(out, f"{deal['id']}_{tag}.jpg")
            im.save(p, quality=92)
            print("wrote", p)

if __name__ == "__main__":
    main()
