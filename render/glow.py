"""Soft glow on the bright parts, like a filmed screen. glow(img) -> img"""
from PIL import Image, ImageFilter, ImageChops, ImageEnhance
def glow(im, threshold=140, radius_frac=0.016, strength=0.8):
    w = im.width
    hi = im.convert('RGB').point(lambda v: max(0, v - threshold) * 255 // max(1, 255 - threshold))
    hi = hi.filter(ImageFilter.GaussianBlur(w * radius_frac))
    hi = ImageEnhance.Brightness(hi).enhance(strength)
    return ImageChops.add(im.convert('RGB'), hi)
