#!/usr/bin/env python3
"""Price-ladder card: 3 items side by side/stacked with photo, title, sub, price.
Usage: python3 -I ladder_gen.py ladder.json photos out   (ladder.json: {"id","hook","items":[{title,sub,price,photo}]})"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creative_gen import font, cover, pill, LOGO, BRAND_GREEN, DARK, WHITE, Image, ImageDraw

def render(cfg, pdir, W, H):
    im = Image.new("RGB", (W, H), DARK); d = ImageDraw.Draw(im)
    s = W / 1080; m = int(56*s)
    y = m
    y = int(pill(d, (m, y), cfg.get("badge", "OPEN 24 HOURS"), font(int(30*s)), BRAND_GREEN, DARK))
    lh = int(50*s); lw = int(LOGO.width*lh/LOGO.height); lg = LOGO.resize((lw, lh), Image.LANCZOS)
    im.paste(lg, (W-m-lw, m), lg)
    hf = font(int((84 if H > W else 72)*s), "Black")
    y += int(24*s)
    for i, line in enumerate(cfg["hook"].split("\n")):
        d.text((m, y), line, font=hf, fill=BRAND_GREEN if i else WHITE); y += int(hf.size*1.08)
    y += int(20*s)
    cta_h = int(90*s); bottom = H - m - cta_h - int(28*s)
    items = cfg["items"]; n = len(items)
    tf = font(int(44*s)); sf = font(int(28*s), "Medium"); pf = font(int(64*s), "Black")
    if H > W:  # stacked rows
        rh = (bottom - y - (n-1)*int(20*s)) // n
        for it in items:
            pw = int(rh*1.0)
            ph = cover(Image.open(os.path.join(pdir, it["photo"])).convert("RGB"), pw, rh, 0.5)
            mask = Image.new("L", (pw, rh), 0); ImageDraw.Draw(mask).rounded_rectangle([0,0,pw,rh], int(28*s), fill=255)
            d.rounded_rectangle([m, y, W-m, y+rh], int(28*s), fill=(28,28,32))
            im.paste(ph, (m, y), mask)
            tx = m + pw + int(32*s); ty = y + int(rh*0.18)
            d.text((tx, ty), it["title"], font=tf, fill=WHITE)
            yy = ty + int(tf.size*1.25)
            for ln in it["sub"].split("\n"):
                d.text((tx, yy), ln, font=sf, fill=(200,200,200)); yy += int(sf.size*1.3)
            d.text((tx, yy + int(10*s)), f"Rs {it['price']}", font=pf, fill=BRAND_GREEN)
            y += rh + int(20*s)
    else:  # 3 columns
        gap = int(20*s); cw = (W - 2*m - (n-1)*gap)//n; chh = bottom - y
        for i, it in enumerate(items):
            x = m + i*(cw+gap); phh = int(chh*0.52)
            d.rounded_rectangle([x, y, x+cw, y+chh], int(24*s), fill=(28,28,32))
            ph = cover(Image.open(os.path.join(pdir, it["photo"])).convert("RGB"), cw, phh, 0.5)
            mask = Image.new("L", (cw, phh), 0); ImageDraw.Draw(mask).rounded_rectangle([0,0,cw,phh+40], int(24*s), fill=255)
            im.paste(ph, (x, y), mask)
            tx = x + int(20*s); ty = y + phh + int(18*s)
            tf2 = font(int(36*s)); sf2 = font(int(23*s), "Medium"); pf2 = font(int(56*s), "Black")
            sz = 36
            while d.textlength(it["title"], font=font(int(sz*s))) > cw - int(40*s) and sz > 22: sz -= 1
            tf2 = font(int(sz*s)); d.text((tx, ty), it["title"], font=tf2, fill=WHITE); yy = ty + int(36*s*1.3)
            for ln in it["sub"].split("\n"):
                d.text((tx, yy), ln, font=sf2, fill=(200,200,200)); yy += int(sf2.size*1.3)
            d.text((tx, y+chh-int(20*s)-pf2.size), f"Rs {it['price']}", font=pf2, fill=BRAND_GREEN)
    yb = H - m
    d.rounded_rectangle([m, yb-cta_h, W-m, yb], int(24*s), fill=BRAND_GREEN)
    cf = font(int(38*s)); d.text((m+int(32*s), yb-cta_h+(cta_h-cf.size)//2-4), "Order now  •  foodrun.store", font=cf, fill=DARK)
    return im

if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1])); os.makedirs(sys.argv[3], exist_ok=True)
    for tag, (W, H) in {"1x1": (1080,1080), "9x16": (1080,1920)}.items():
        p = os.path.join(sys.argv[3], f"{cfg['id']}_{tag}.jpg"); render(cfg, sys.argv[2], W, H).save(p, quality=92); print("wrote", p)
