"""Build the printed project pages and the hover images from the screenshots in img/.
usage (from the book folder): python3 render/work_faces.py
- img/pages/workNN.webp: the top of each screenshot, 1536x864, lightly sharpened
- img/<name>.jpg|png: screenshots narrower than 1230px are enlarged to 1230px wide for hover
Best results come from 1440px-wide screenshots taken at 2x (see README)."""
import os, re
from PIL import Image, ImageFilter
src = open('index.html').read()
works = re.findall(r"\{ n:'(\d\d)'.*?img:'(img/[^']+)'", src)
FW, FH = 1536, 864
def face(im):
    ir, pr = im.width / im.height, FW / FH
    if ir > pr: sw = im.height * pr; box = ((im.width - sw) / 2, 0, (im.width + sw) / 2, im.height)
    else: box = (0, 0, im.width, im.width / pr)
    return im.crop(tuple(round(v) for v in box))
for n, path in works:
    im = Image.open(path).convert('RGB')
    f = face(im)
    soft = f.width < FW   # enlarged: sharpen more
    f = f.resize((FW, FH), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.4, 70, 1) if soft else ImageFilter.UnsharpMask(0.8, 40, 1))
    f.save(f'img/pages/work{n}.webp', 'WEBP', quality=90, method=6)
    s = min(1230 / im.width, 4096 / im.height)
    if s > 1.05:
        big = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 60, 1))
        big.save(path, optimize=True) if path.endswith('.png') else big.save(path, quality=86, optimize=True)
    print(n, path)
