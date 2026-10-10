"""Convert rendered PNG frames into the WebP sizes the web player loads.
usage: python encode.py <png_dir> <out_dir>
"""
import os, sys
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
sizes = {1920: 78, 960: 78}
for w in sizes:
    os.makedirs(os.path.join(out, str(w)), exist_ok=True)
files = sorted(f for f in os.listdir(src) if f.endswith('.png'))
total = 0
for f in files:
    im = Image.open(os.path.join(src, f)).convert('RGB')
    for w, q in sizes.items():
        h = round(w * 9 / 16)
        r = im if im.width == w else im.resize((w, h), Image.LANCZOS)
        p = os.path.join(out, str(w), f.replace('.png', '.webp'))
        r.save(p, 'WEBP', quality=q, method=5)
        total += os.path.getsize(p)
print(len(files), 'frames,', round(total / 1e6, 1), 'MB total across sizes')
