"""재난소통 영웅 배경 일러스트 도구 · © 2026 KOREA CONTENTS LAB"""
import numpy as np, cv2, math
from PIL import Image, ImageDraw, ImageFont

W, H, GY = 1200, 900, 750
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'


def C(h, a=None):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def mix(a, b, t):
    return np.asarray(a) * (1 - t) + np.asarray(b) * t


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def vgrad(stops, h=H, w=W, y0=0):
    """stops: [(pos 0..1, '#hex'), ...] over rows y0..y0+h"""
    y = np.linspace(0, 1, h)
    out = np.zeros((h, 3), np.float32)
    ps = [s[0] for s in stops]
    for c in range(3):
        out[:, c] = np.interp(y, ps, [C(s[1])[c] for s in stops])
    return np.repeat(out[:, None, :], w, axis=1)


def full_vgrad(stops, top, bottom):
    """gradient image size HxW whose ramp runs from row top to row bottom"""
    y = np.clip((np.arange(H) - top) / max(1, bottom - top), 0, 1)
    out = np.zeros((H, 3), np.float32)
    ps = [s[0] for s in stops]
    for c in range(3):
        out[:, c] = np.interp(y, ps, [C(s[1])[c] for s in stops])
    return np.repeat(out[:, None, :], W, axis=1)


def noise(scale, octaves=5, seed=0, shape=(H, W), sy=None, persist=.5):
    rng = np.random.default_rng(seed)
    acc = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gx = max(2, int(shape[1] / scale * 2 ** o))
        gy = max(2, int(shape[0] / (sy or scale) * 2 ** o))
        g = rng.random((gy, gx)).astype(np.float32)
        acc += cv2.resize(g, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC) * amp
        tot += amp
        amp *= persist
    n = acc / tot
    return (n - n.min()) / (n.max() - n.min() + 1e-6)


def poly(pts, blur=0.0):
    m = np.zeros((H, W), np.float32)
    cv2.fillPoly(m, [np.int32(np.round(pts))], 1.0, lineType=cv2.LINE_AA)
    return cv2.GaussianBlur(m, (0, 0), blur) if blur else m


def rect(x0, y0, x1, y1, blur=0.0):
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], blur)


def ellipse(cx, cy, rx, ry, blur=0.0, angle=0):
    m = np.zeros((H, W), np.float32)
    cv2.ellipse(m, (int(cx), int(cy)), (int(rx), int(ry)), angle, 0, 360, 1.0, -1, cv2.LINE_AA)
    return cv2.GaussianBlur(m, (0, 0), blur) if blur else m


def lines(segs, thick=2, blur=0.0):
    m = np.zeros((H, W), np.float32)
    for (x0, y0, x1, y1) in segs:
        cv2.line(m, (int(x0), int(y0)), (int(x1), int(y1)), 1.0, thick, cv2.LINE_AA)
    return cv2.GaussianBlur(m, (0, 0), blur) if blur else m


def polyline(pts, thick=2, blur=0.0):
    m = np.zeros((H, W), np.float32)
    cv2.polylines(m, [np.int32(pts)], False, 1.0, thick, cv2.LINE_AA)
    return cv2.GaussianBlur(m, (0, 0), blur) if blur else m


def paint(img, color, m, a=1.0):
    m = np.clip(m * a, 0, 1)[..., None]
    col = color if (isinstance(color, np.ndarray) and color.ndim == 3) else np.asarray(color, np.float32)
    img[:] = img * (1 - m) + col * m


def add(img, color, m, k=1.0):
    col = color if (isinstance(color, np.ndarray) and color.ndim == 3) else np.asarray(color, np.float32)
    img[:] = img + col * (m * k)[..., None]


def mul(img, m, k=1.0):
    img[:] = img * (1 - (1 - m[..., None]) * k)


def glow(img, x, y, r, color, k=1.0, ry=None):
    ry = ry or r
    g = np.exp(-(((XX - x) / r) ** 2 + ((YY - y) / ry) ** 2) / 2)
    add(img, C(color) if isinstance(color, str) else color, g, k)


def shade_v(top, bottom, a, b):
    """vertical multiplier from a at row top to b at row bottom"""
    t = np.clip((YY - top) / max(1, bottom - top), 0, 1)
    return a + (b - a) * t


def windows(img, x0, y0, x1, y1, cols, rows, ww, wh, p, lit='#ffd27a', dark='#1a2030', seed=1, glowk=.35, frame=None, var=.25):
    rng = np.random.default_rng(seed)
    gl = np.zeros((H, W), np.float32)
    cw, ch = (x1 - x0) / cols, (y1 - y0) / rows
    litc, darkc = C(lit), C(dark)
    for r in range(rows):
        for c in range(cols):
            x = x0 + c * cw + (cw - ww) / 2
            y = y0 + r * ch + (ch - wh) / 2
            m = rect(x, y, x + ww, y + wh)
            if rng.random() < p:
                col = litc * (1 - var + rng.random() * var)
                paint(img, col, m)
                gl += m
            else:
                paint(img, darkc * (.8 + rng.random() * .4), m)
            if frame:
                paint(img, C(frame), rect(x - 1.5, y + wh - 2, x + ww + 1.5, y + wh + 1.5))
    if glowk:
        add(img, litc, cv2.GaussianBlur(gl, (0, 0), 6), glowk)


_TEX = None


def facade_tex():
    global _TEX
    if _TEX is None:
        n = noise(40, 5, 999) * .6 + noise(6, 2, 998, sy=40) * .4
        _TEX = (.9 + .16 * n).astype(np.float32)
    return _TEX


def depth(img, blur=1.8, haze_col=None, haze=0.0):
    img[:] = cv2.GaussianBlur(img, (0, 0), blur)
    if haze_col is not None:
        paint(img, C(haze_col), np.ones((H, W), np.float32), haze)


def building(img, x0, top, x1, base, bottom=GY, light='left', k=.25, roof=None):
    m = rect(x0, top, x1, bottom)
    col = C(base)
    tex = facade_tex()
    g = np.repeat(np.repeat(col[None, None, :], H, 0), W, 1) * (shade_v(top, bottom, 1.08, .78) * tex)[..., None]
    paint(img, g, m)
    side = rect(x1 - (x1 - x0) * .14, top, x1, bottom) if light == 'left' else rect(x0, top, x0 + (x1 - x0) * .14, bottom)
    img[:] = img * (1 - side[..., None] * k)
    if roof:
        paint(img, C(roof), rect(x0 - 4, top - 6, x1 + 4, top + 2))


def text(img, s, x, y, size, color='#ffffff', anchor='mm', stroke=0, stroke_color='#000000', alpha=1.0, glowk=0, angle=0):
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = ImageFont.truetype(FONT, size, index=1)
    rgb = tuple(int(v * 255) for v in C(color))
    d.text((x, y), s, font=f, fill=rgb + (255,), anchor=anchor, stroke_width=stroke, stroke_fill=tuple(int(v * 255) for v in C(stroke_color)) + (255,))
    if angle:
        layer = layer.rotate(angle, center=(x, y), resample=Image.BICUBIC)
    a = np.asarray(layer, np.float32) / 255
    m = a[..., 3] * alpha
    if glowk:
        add(img, a[..., :3], cv2.GaussianBlur(m, (0, 0), 8), glowk)
    paint(img, a[..., :3], m)


def rain(img, n=900, angle=-12, length=34, k=.35, seed=3, color='#cfe0ff'):
    rng = np.random.default_rng(seed)
    m = np.zeros((H, W), np.float32)
    dx = math.sin(math.radians(angle)) * length
    for _ in range(n):
        x, y = rng.random() * (W + 100) - 50, rng.random() * H
        cv2.line(m, (int(x), int(y)), (int(x + dx), int(y + length)), float(.4 + rng.random() * .6), 1, cv2.LINE_AA)
    add(img, C(color), cv2.GaussianBlur(m, (0, 0), .7), k)


def smoke(img, m, seed, dark='#1c1a1c', lit=None, lit_from=None, density=1.0, scale=120):
    n = noise(scale, 6, seed)
    a = np.clip(cv2.GaussianBlur(m, (0, 0), 18) * (0.35 + 1.1 * smooth(.25, .75, n)), 0, 1) * density
    col = np.repeat(np.repeat(C(dark)[None, None, :], H, 0), W, 1)
    col = col * (0.75 + 0.5 * n[..., None])
    if lit is not None:
        t = np.clip((YY - lit_from[0]) / (lit_from[1] - lit_from[0]), 0, 1)[..., None]
        col = col * (1 - t * .7) + C(lit) * t * .7
    paint(img, col, a)


def flames(img, cx, base, w, h, seed, k=1.0):
    n = noise(26, 5, seed, sy=18)
    t = np.clip((base - YY) / h, -0.2, 1.3)
    dx = np.abs(XX - cx) / (w / 2 * (1 - np.clip(t, 0, 1) * .75) + 1e-3)
    inten = (1 - dx ** 2) * (1 - np.clip(t, 0, 1)) ** 0.6 + (n - .5) * 0.9 - np.clip(t - .2, 0, 1) * .6
    inten = np.where((YY < base + 6) & (YY > base - h * 1.3), inten, -1)
    a = smooth(.08, .35, inten)
    pal = np.stack([np.clip(.8 + inten * 1.4, 0, 1), np.clip(.15 + inten * 1.25, 0, 1), np.clip(-.3 + inten * 1.3, 0, 1)], -1).astype(np.float32)
    paint(img, pal, a, k)
    add(img, C('#ff7a1a'), cv2.GaussianBlur(a, (0, 0), 22), .55 * k)


def finish(img, vignette=.35, grain=.012, seed=9, warm=None):
    v = 1 - vignette * (((XX - W / 2) / (W / 2)) ** 2 + ((YY - H * .45) / (H * .7)) ** 2)
    img *= np.clip(v, .45, 1)[..., None]
    if warm is not None:
        img[:] = img * np.asarray(warm, np.float32)
    painterly(img, .45)
    rng = np.random.default_rng(seed)
    img += rng.normal(0, grain, img.shape).astype(np.float32)
    img[:] = np.clip(img, 0, 1)
    return img


def painterly(img, k=.55):
    a = (np.clip(img, 0, 1) * 255 + .5).astype(np.uint8)
    st = cv2.stylization(a[..., ::-1].copy(), sigma_s=40, sigma_r=.35)[..., ::-1].astype(np.float32) / 255
    img[:] = img * (1 - k) + st * k
    return img


def save(img, path, q=74):
    a = (np.clip(img, 0, 1) * 255 + .5).astype(np.uint8)
    Image.fromarray(a).save(path, 'WEBP', quality=q, method=6)


def displace_x(img, amp, freq, y0, y1, seed=0):
    n = noise(60, 3, seed)
    mapx = XX + np.sin(YY * freq + n * 6) * amp * np.clip((YY - y0) / max(1, y1 - y0), 0, 1)
    out = cv2.remap(img, mapx.astype(np.float32), YY.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return out
