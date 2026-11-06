import sys
from PIL import Image
# usage: stitch.py top.jpg bottom.jpg out.jpg   (top = scrollY 0, bottom = scrollY 450; image is 900x900 at page (0,0))
top, bot, out = sys.argv[1:4]
a = Image.open(top).convert("RGB"); b = Image.open(bot).convert("RGB")
assert a.size[0] >= 900 and b.size[0] >= 900, (a.size, b.size)
im = Image.new("RGB", (900, 900))
im.paste(a.crop((0, 0, 900, 450)), (0, 0))
im.paste(b.crop((0, 0, 900, 450)), (0, 450))
im.save(out, quality=95)
print("ok", out, im.size)
