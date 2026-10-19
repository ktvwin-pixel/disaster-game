"""대화 상황별 배경 11종 · © 2026 KOREA CONTENTS LAB"""
import sys
from kit import *
from scenes import sky, apartment

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'


def F(col, m=None):
    a = np.empty((H, W, 3), np.float32)
    a[:] = C(col)
    return a if m is None else a * m[..., None]


def tex(seed, scale=20, lo=.75, hi=1.15):
    return lo + (hi - lo) * noise(scale, 4, seed)


def water_refl(img, wl, tint_top, tint_bot, amp=10, k=.55, seed=5):
    h = H - wl
    refl = cv2.resize(cv2.flip(img[max(0, wl - 220):wl], 0), (W, h))
    n = noise(40, 3, seed, shape=(h, W), sy=8)
    yy = np.arange(h, dtype=np.float32)[:, None]
    mapx = (np.arange(W, dtype=np.float32)[None, :] + np.sin(yy * .5 + n * 9) * amp).astype(np.float32)
    refl = cv2.remap(refl, mapx, np.repeat(yy, W, 1).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    refl = cv2.GaussianBlur(refl, (0, 0), 2)
    img[wl:] = vgrad([(0, tint_top), (1, tint_bot)], h, W) * (1 - k) + refl * k
    rip = smooth(.62, .8, noise(30, 4, seed + 1, shape=(h, W), sy=5))
    img[wl:] += C('#b9d4ec')[None, None, :] * rip[..., None] * .14


def sign(img, x0, y0, x1, y1, bg, lines_, fg='#ffffff', size=26, border=None, pole=None):
    if pole:
        paint(img, C('#5b6470'), rect((x0 + x1) / 2 - 5, y1, (x0 + x1) / 2 + 5, pole))
    if border:
        paint(img, C(border), rect(x0 - 4, y0 - 4, x1 + 4, y1 + 4))
    paint(img, C(bg), rect(x0, y0, x1, y1))
    n = len(lines_)
    for i, t in enumerate(lines_):
        text(img, t, (x0 + x1) / 2, y0 + (y1 - y0) * (i + .5) / n, size if i == 0 else int(size * .78), fg)


def car(img, x, y, w, col, lights=False, seed=0):
    """y = 바퀴 바닥"""
    h = w * .34
    body = poly([(x, y - h * .25), (x + w * .06, y - h * .6), (x + w * .26, y - h * .66), (x + w * .36, y - h), (x + w * .7, y - h), (x + w * .82, y - h * .64), (x + w * .97, y - h * .55), (x + w, y - h * .25), (x + w, y - h * .1), (x, y - h * .1)])
    paint(img, F(col) * shade_v(y - h, y, 1.15, .7)[..., None], body)
    paint(img, C('#1c2836'), poly([(x + w * .38, y - h * .94), (x + w * .52, y - h * .94), (x + w * .52, y - h * .66), (x + w * .3, y - h * .66)]))
    paint(img, C('#1c2836'), poly([(x + w * .55, y - h * .94), (x + w * .68, y - h * .94), (x + w * .78, y - h * .66), (x + w * .55, y - h * .66)]))
    for cx in (x + w * .2, x + w * .8):
        paint(img, C('#141414'), ellipse(cx, y - h * .12, w * .09, w * .09))
        paint(img, C('#8a9099'), ellipse(cx, y - h * .12, w * .04, w * .04))
    if lights:
        glow(img, x + w, y - h * .38, w * .12, '#fff2c0', .8, w * .05)


def people(img, xs, y, col='#2a2a33', s=1.0, seed=0):
    rng = np.random.default_rng(seed)
    for x in xs:
        hh = (34 + rng.random() * 8) * s
        paint(img, C(col), ellipse(x, y - hh, 7 * s, 7 * s))
        paint(img, F(col) * (.85 + rng.random() * .3), poly([(x - 9 * s, y), (x - 8 * s, y - hh + 8 * s), (x + 8 * s, y - hh + 8 * s), (x + 9 * s, y)]))


# ------------------------------------------------------------------ 지하차도 침수 (f2)
def underpass():
    img = sky([(0, '#070d19'), (.5, '#1a2c46'), (1, '#2b4566')])
    paint(img, C('#0b1322'), smooth(.42, .78, noise(260, 6, 3)) * np.clip(1.2 - YY / 380, 0, 1), .9)
    for i, (x0, t, x1) in enumerate([(0, 230, 200), (180, 280, 340), (860, 260, 1010), (1000, 210, 1200)]):
        building(img, x0, t, x1, '#16233a', k=.2)
        windows(img, x0 + 8, t + 14, x1 - 8, 560, max(3, (x1 - x0) // 34), 9, 12, 14, .3, seed=200 + i, dark='#101a2c', glowk=.25)
    depth(img, 2.0)
    # 지상 도로(위쪽) + 옹벽
    paint(img, C('#232b38'), rect(0, 520, W, 560))
    paint(img, F('#6b7280') * tex(3)[..., None], poly([(0, 560), (440, 560), (470, 700), (0, 900)]))
    paint(img, F('#6b7280') * tex(4)[..., None], poly([(W, 560), (760, 560), (730, 700), (W, 900)]))
    paint(img, F('#565d68') * tex(5)[..., None], rect(380, 400, 820, 560))
    text(img, 'OO지하차도', 600, 440, 34, '#e8edf3')
    paint(img, C('#05070b'), poly([(440, 560), (760, 560), (760, 700), (440, 700)]))
    glow(img, 600, 600, 70, '#ffd27a', .12)
    # 통행 제한 표지
    paint(img, C('#111'), rect(420, 478, 780, 520))
    text(img, '침수 · 통행 제한', 600, 499, 28, '#ff4a3a', glowk=.7)
    # 내려가는 도로 + 물
    paint(img, F('#2f3540') * tex(6)[..., None], poly([(470, 700), (730, 700), (1000, 900), (200, 900)]))
    car(img, 520, 712, 170, '#d9d9de')
    WL = 690
    sub = img[WL:].copy()
    water_refl(img, WL, '#3a5a74', '#132436', amp=8, k=.5)
    img[WL:] = img[WL:] * np.clip((np.arange(H - WL)[:, None] / 30), 0, 1)[..., None] * 0 + img[WL:]
    paint(img, F('#9ab3c9'), lines([(0, WL + 1, W, WL + 1)], 2, 1.4), .4)
    # 차단기
    for x0 in (180, 640):
        for i in range(8):
            col = '#f2f2f2' if i % 2 else '#e02a2a'
            paint(img, C(col), poly([(x0 + i * 46, 760), (x0 + i * 46 + 46, 760), (x0 + i * 46 + 46, 776), (x0 + i * 46, 776)]))
    paint(img, C('#5b6470'), rect(176, 760, 186, 900)); paint(img, C('#5b6470'), rect(1006, 760, 1016, 900))
    glow(img, 181, 752, 22, '#ffb02e', .9); glow(img, 1011, 752, 22, '#ffb02e', .9)
    # 멈춘 차 전조등
    car(img, 40, 900, 300, '#3a6ea5', lights=True)
    rain(img, 1300, -10, 38, .28, 7)
    return finish(img, .3, .014)


# ------------------------------------------------------------------ 계곡 급류 (f3)
def valley():
    img = sky([(0, '#4a5560'), (.6, '#7c8892'), (1, '#9aa5ac')])
    paint(img, C('#5d6870'), smooth(.4, .8, noise(220, 6, 8)) * np.clip(1 - YY / 360, 0, 1), .7)
    # 산 능선 3겹
    for i, (base, amp, col, seed) in enumerate([(330, 90, '#4a5a52', 1), (420, 110, '#3a4c40', 2), (520, 120, '#2c3d31', 3)]):
        n = noise(300, 4, 40 + seed, shape=(1, W))[0]
        top = base - n * amp * 2
        m = (YY >= top[None, :]).astype(np.float32)
        tr = tex(60 + i, 8, .8, 1.15)
        paint(img, F(col) * tr[..., None], cv2.GaussianBlur(m, (0, 0), 1.2))
        paint(img, C('#a9b4b8'), np.clip(1 - np.abs(YY - (base + 60)) / 70, 0, 1) * .5, .5)
    # 왼쪽·오른쪽 가까운 산비탈
    paint(img, F('#243327') * tex(70, 10)[..., None], poly([(0, 380), (180, 430), (380, 640), (300, 900), (0, 900)]))
    paint(img, F('#26362a') * tex(71, 10)[..., None], poly([(W, 360), (1020, 420), (820, 640), (900, 900), (W, 900)]))
    # 흙탕물 급류 (가운데)
    river = poly([(560, 560), (640, 560), (900, 900), (300, 900)])
    flow = noise(18, 5, 90, sy=60)
    paint(img, F('#7a5e3e') * (.8 + .4 * flow)[..., None], river)
    foam = smooth(.62, .82, noise(14, 4, 91, sy=34)) * river
    paint(img, C('#efe8dc'), foam, .85)
    paint(img, C('#f6f1e8'), poly([(560, 560), (640, 560), (660, 600), (540, 600)], 4), .6)
    # 바위
    for (x, y, rx) in [(360, 820, 60), (820, 790, 50), (470, 690, 26), (720, 700, 30)]:
        paint(img, F('#6b6a64') * shade_v(y - rx, y + rx, 1.2, .6)[..., None], ellipse(x, y, rx, rx * .6))
    # 자갈 둔치 + 텐트
    paint(img, F('#a49b8a') * tex(92, 6)[..., None], poly([(830, 660), (1200, 620), (1200, 900), (980, 900), (860, 760)]))
    for (x, col) in [(930, '#e8742a'), (1060, '#2f8ad8')]:
        paint(img, F(col) * shade_v(640, 720, 1.1, .7)[..., None], poly([(x, 720), (x + 50, 650), (x + 100, 720)]))
        paint(img, C('#1a1a1a'), poly([(x + 42, 720), (x + 50, 680), (x + 58, 720)]))
    # 경고 표지
    sign(img, 150, 560, 330, 640, '#ffd400', ['급류 주의', '계곡 야영 금지'], fg='#111111', size=28, border='#111111', pole=760)
    rain(img, 700, -8, 30, .18, 9, '#e6eef4')
    return finish(img, .28, .014)


# ------------------------------------------------------------------ 전통시장 화재 (h2)
def market():
    img = np.zeros((H, W, 3), np.float32)
    img[:] = vgrad([(0, '#2a1a14'), (.5, '#4a2a18'), (1, '#1e1410')])
    # 아케이드 지붕 (반투명 아치)
    roof = poly([(0, 0), (W, 0), (W, 160), (760, 330), (440, 330), (0, 160)])
    paint(img, F('#c8a46a') * .55, roof)
    for i in range(10):
        t = i / 9
        x0 = 0 + t * 440; x1 = W - t * (W - 760); y = 160 + t * 170
        paint(img, C('#5a4030'), polyline([(x0, y), (600, 40 + t * 250), (x1, y)], 4))
    # 양옆 가게
    shops = [('건어물', '#2a6ab8'), ('떡집', '#c8402a'), ('야채', '#2a8a4a'), ('정육점', '#b82a3a'), ('반찬', '#c8902a'), ('수산물', '#2a7ab8')]
    for side in (0, 1):
        for i in range(3):
            t0, t1 = i / 3, (i + 1) / 3
            def P(t, y):  # 원근 보간
                xa = 0 + t * 440 if side == 0 else W - t * (W - 760)
                return xa, y
            xa0, _ = P(t0, 0); xa1, _ = P(t1, 0)
            top0, top1 = 180 + t0 * 160, 180 + t1 * 160
            bot0, bot1 = 900 - t0 * 290, 900 - t1 * 290
            wall = poly([(xa0, top0), (xa1, top1), (xa1, bot1), (xa0, bot0)])
            name, col = shops[side * 3 + i]
            paint(img, F('#5a4a3e') * tex(300 + i + side * 3)[..., None], wall)
            sg = poly([(xa0, top0), (xa1, top1), (xa1, top1 + 50 - t1 * 20), (xa0, top0 + 70 - t0 * 20)])
            paint(img, C(col), sg)
            cx = (xa0 + xa1) / 2
            text(img, name, cx, (top0 + top1) / 2 + 30 - t0 * 10, int(46 - i * 12), '#ffffff')
            # 진열대
            gd = poly([(xa0, bot0 - 160 + t0 * 60), (xa1, bot1 - 130 + t1 * 50), (xa1, bot1 - 60), (xa0, bot0 - 90)])
            paint(img, F('#8a5a2a') * tex(320 + i)[..., None], gd)
            dots = smooth(.55, .7, noise(8, 3, 330 + i + side * 7)) * gd
            paint(img, C(['#e05a2a', '#7ab84a', '#e8c040'][i]), dots, .8)
    # 바닥 통로
    paint(img, F('#3a2e26') * tex(340, 30)[..., None], poly([(440, 610), (760, 610), (W, 900), (0, 900)]))
    # 화재 (왼쪽 두 번째 가게)
    glow(img, 300, 470, 260, '#ff7a1a', .55, 220)
    for i, (fx, fy, fw, fh) in enumerate([(260, 640, 150, 260), (330, 600, 110, 220), (200, 700, 120, 200)]):
        flames(img, fx, fy, fw, fh, 400 + i, 1.0)
    smoke(img, poly([(150, 560), (420, 560), (700, 330), (W, 200), (W, 0), (0, 0), (0, 300)]), 410, dark='#140d0c', lit='#c8501e', lit_from=(0, 600), density=.85, scale=110)
    # 소화기 표지
    sign(img, 900, 520, 1040, 560, '#c8202a', ['소화기'], size=24)
    paint(img, C('#d01f26'), rect(950, 570, 984, 650)); paint(img, C('#222'), rect(958, 560, 976, 572))
    rng = np.random.default_rng(4)
    em = np.zeros((H, W), np.float32)
    for _ in range(120):
        cv2.circle(em, (int(150 + rng.random() * 400), int(250 + rng.random() * 400)), int(1 + rng.random() * 2), 1.0, -1, cv2.LINE_AA)
    add(img, C('#ffcf7a'), em, .9)
    return finish(img, .32, .014)


# ------------------------------------------------------------------ 산불 마을 (h3)
def wildfire():
    img = sky([(0, '#120808'), (.45, '#4a1a10'), (.75, '#a8401a'), (1, '#c86020')])
    smoke(img, poly([(0, 380), (W, 300), (W, -60), (0, -60)]), 501, dark='#1a1212', lit='#d8642a', lit_from=(0, 420), density=.9, scale=170)
    # 능선 + 불띠
    n = noise(260, 4, 502, shape=(1, W))[0]
    ridge = 440 - n * 140
    m = (YY >= ridge[None, :]).astype(np.float32)
    paint(img, F('#1a120e') * tex(503, 10)[..., None], cv2.GaussianBlur(m, (0, 0), 1))
    fire_line = np.exp(-((YY - ridge[None, :] - 6) / 10) ** 2) * (XX > 120) * (XX < 1100)
    add(img, C('#ff8a2a'), fire_line, 1.2)
    add(img, C('#ff6a1a'), cv2.GaussianBlur(fire_line, (0, 0), 18), 1.0)
    for i, x in enumerate(range(160, 1100, 70)):
        r = ridge[x]
        flames(img, x, r + 8, 50, 70 + (i * 37) % 50, 520 + i, .9)
    # 앞쪽 산자락
    paint(img, F('#120c0a') * tex(530, 12)[..., None], poly([(0, 560), (300, 520), (700, 580), (1200, 520), (1200, 900), (0, 900)]))
    # 시골 마을 집들
    for i, (x, w, roof) in enumerate([(120, 200, '#3a4a6a'), (400, 170, '#7a2a2a'), (760, 220, '#3a5a4a'), (1010, 170, '#5a4a6a')]):
        y = 700
        paint(img, F('#c9b89a') * .55, rect(x, y - 110, x + w, y))
        paint(img, F(roof) * .7, poly([(x - 20, y - 105), (x + w / 2, y - 170), (x + w + 20, y - 105)]))
        paint(img, C('#ffcf7a') * .8, rect(x + 24, y - 80, x + 64, y - 44)); glow(img, x + 44, y - 62, 30, '#ffb85a', .3)
    paint(img, F('#3a3028') * tex(540, 20)[..., None], poly([(480, 900), (560, 700), (640, 700), (760, 900)]))
    sign(img, 820, 720, 1060, 790, '#1d8a4c', ['마을회관 대피소 →'], size=28, pole=900)
    rng = np.random.default_rng(5)
    em = np.zeros((H, W), np.float32)
    for _ in range(260):
        cv2.circle(em, (int(rng.random() * W), int(150 + rng.random() * 600)), int(1 + rng.random() * 2), 1.0, -1, cv2.LINE_AA)
    add(img, C('#ffcf7a'), em, .9); add(img, C('#ff8a2a'), cv2.GaussianBlur(em, (0, 0), 4), .7)
    return finish(img, .32, .014)


# ------------------------------------------------------------------ 해변 지진해일 (e2)
def tsunami():
    img = sky([(0, '#3a4652'), (.6, '#6a7a86'), (1, '#9aa6ae')])
    paint(img, C('#2a3440'), smooth(.4, .8, noise(240, 6, 601)) * np.clip(1 - YY / 380, 0, 1), .8)
    # 먼바다 + 해일 벽
    HZ = 420
    img[HZ:] = vgrad([(0, '#2a4a5a'), (1, '#1a3442')], H - HZ, W)
    wave_top = HZ - 170 - noise(200, 3, 602, shape=(1, W))[0] * 90
    wm = ((YY > wave_top[None, :]) & (YY < HZ + 30)).astype(np.float32)
    face = np.clip((YY - wave_top[None, :]) / 200, 0, 1)
    wcol = mix(C('#4a8a96'), C('#12303a'), face[..., None]) * (0.85 + .3 * noise(12, 4, 610, sy=40))[..., None]
    paint(img, wcol, cv2.GaussianBlur(wm, (0, 0), 1.2))
    smoke(img, np.clip(rect(0, 0, W, H) * (np.abs(YY - wave_top[None, :] + 20) < 40), 0, 1), 611, dark='#dfe8ea', density=.55, scale=40)
    crest = np.exp(-((YY - wave_top[None, :] - 4) / 8) ** 2)
    foam = crest * (.6 + .6 * noise(10, 4, 603))
    paint(img, C('#eef4f6'), np.clip(foam, 0, 1), .9)
    add(img, C('#e8f2f6'), cv2.GaussianBlur(crest, (0, 0), 14), .25)
    # 물이 빠진 해저(젖은 모래·바위)
    paint(img, F('#6a6050') * tex(604, 12, .7, 1.1)[..., None], poly([(0, 470), (W, 450), (W, 620), (0, 640)]))
    add(img, C('#b8c8cc'), smooth(.6, .8, noise(16, 4, 605, sy=4)) * rect(0, 470, W, 640), .25)
    for (x, y, r) in [(200, 560, 40), (520, 520, 26), (880, 580, 50), (1060, 520, 30)]:
        paint(img, F('#3a3a36') * shade_v(y - r, y + r, 1.2, .6)[..., None], ellipse(x, y, r, r * .5))
    # 모래사장 + 파라솔
    paint(img, F('#d8c49a') * tex(606, 16)[..., None], poly([(0, 640), (W, 620), (W, 900), (0, 900)]))
    for i, (x, col) in enumerate([(260, '#e04a3a'), (720, '#2a8ad8'), (930, '#f2b705')]):
        paint(img, C('#ddd'), rect(x - 2, 640, x + 3, 760))
        paint(img, C(col), poly([(x - 70, 660), (x, 620), (x + 70, 660)]))
        paint(img, C('#3a2e24'), ellipse(x + 10, 768, 60, 8, 4), .35)
    # 언덕 대피로 + 표지
    paint(img, F('#3a5a34') * tex(607, 12)[..., None], poly([(1000, 900), (1060, 560), (1200, 420), (1200, 900)]))
    sign(img, 70, 640, 400, 720, '#1f5fbf', ['지진해일 긴급대피장소', '→ 높은 곳으로 300m'], size=26, pole=860)
    # 사이렌 기둥
    paint(img, C('#6b7280'), rect(560, 500, 570, 820)); paint(img, C('#c8c8c8'), rect(540, 480, 590, 510))
    return finish(img, .28, .014)


# ------------------------------------------------------------------ 초등학교 (e3)
def school():
    img = sky([(0, '#4a5068'), (.6, '#8a8a9a'), (1, '#b0a89a')])
    # 학교 건물
    building(img, 140, 220, 1060, '#d9cbb0', k=.15, roof='#8a6a4a')
    for f in range(4):
        y = 250 + f * 100
        windows(img, 160, y, 1040, y + 80, 14, 1, 48, 56, .2, lit='#ffe6b0', dark='#6a8aa8', seed=700 + f, glowk=0, frame='#f2ece0')
    paint(img, C('#f2ece0'), ellipse(600, 200, 44, 44)); paint(img, C('#333'), lines([(600, 200, 600, 172), (600, 200, 620, 210)], 3))
    text(img, 'OO초등학교', 600, 158, 34, '#3a2a1a')
    # 균열·깨진 창
    paint(img, C('#2a2018'), polyline([(380, 230), (400, 300), (372, 360), (410, 440), (390, 520)], 4))
    paint(img, C('#2a2018'), polyline([(860, 240), (840, 320), (870, 380), (845, 470)], 4))
    paint(img, C('#1a1a1a'), poly([(460, 360), (500, 356), (480, 390)]))
    # 운동장
    paint(img, F('#c8a87a') * tex(710, 30)[..., None], rect(0, 640, W, 900))
    paint(img, C('#f2f2f2'), lines([(80, 720, 80, 640), (200, 720, 200, 640), (80, 640, 200, 640)], 6))
    # 줄지어 앉은 학생들 (작은 실루엣)
    for row in range(3):
        y = 760 + row * 46
        people(img, [360 + i * 40 + row * 10 for i in range(12)], y, col=['#2a4a7a', '#7a3a3a', '#3a6a4a'][row], s=.8, seed=row)
    smoke(img, rect(0, 560, W, 660), 720, dark='#c8b49a', density=.35, scale=80)
    sign(img, 960, 650, 1140, 700, '#1d8a4c', ['운동장 대피'], size=26, pole=820)
    return finish(img, .26, .013)


# ------------------------------------------------------------------ 주택가 가스 누출 (b1)
def gasleak():
    img = sky([(0, '#0c1220'), (.6, '#1e2a40'), (1, '#2c3a52')])
    for i, (x0, t, x1, col) in enumerate([(0, 240, 360, '#6a5448'), (380, 200, 820, '#7a6a5a'), (840, 260, 1200, '#5e5048')]):
        paint(img, F(col) * .55 * tex(800 + i, 6)[..., None] * shade_v(t, GY, 1, .7)[..., None], rect(x0, t, x1, GY + 20))
        windows(img, x0 + 20, t + 20, x1 - 20, GY - 120, 4, 3, 60, 52, .55, lit='#ffd27a', dark='#141c28', seed=810 + i, frame='#a89e90', glowk=.4)
    # 노란 가스 배관 + 계량기
    pipe = []
    for x in (300, 470, 760, 960):
        pipe += [(x, 230, x, GY - 20)]
    pipe += [(300, 600, 470, 600), (760, 640, 960, 640), (470, 360, 760, 360)]
    paint(img, C('#f2c21b'), lines(pipe, 9))
    add(img, C('#fff2a0'), lines(pipe, 3), .25)
    for (x, y) in [(470, 520), (760, 560)]:
        paint(img, C('#d8dde3'), rect(x - 26, y - 34, x + 26, y + 34)); paint(img, C('#1a1a1a'), rect(x - 16, y - 20, x + 16, y))
    # 골목 바닥
    paint(img, F('#2e333a') * tex(820, 30)[..., None], rect(0, GY, W, H))
    # 옅은 가스 안개
    smoke(img, rect(250, 380, 1000, 820), 830, dark='#9ac8a0', density=.22, scale=90)
    # 경고 테이프 + 표지
    tape = np.zeros((H, W, 3), np.float32); tm = rect(-40, 780, W + 40, 806)
    paint(tape, C('#ffd400'), tm)
    for i in range(8):
        text(tape, '가스 누출 · 화기 엄금', 90 + i * 170, 793, 17, '#111111')
    M = cv2.getRotationMatrix2D((600, 793), -2.5, 1)
    paint(img, cv2.warpAffine(tape, M, (W, H)), cv2.warpAffine(tm, M, (W, H)))
    # 도시가스 안전점검 차량
    paint(img, C('#f2f2f2'), poly([(820, 760), (820, 660), (1000, 660), (1000, 640), (1060, 640), (1090, 680), (1094, 760)]))
    paint(img, C('#2a7ad8'), rect(820, 700, 1094, 714))
    text(img, '가스안전점검', 910, 690, 22, '#2a5aa8')
    paint(img, C('#ff9a1a'), rect(1000, 628, 1040, 640)); glow(img, 1020, 634, 40, '#ff9a1a', .8)
    for cx in (870, 1050):
        paint(img, C('#141414'), ellipse(cx, 762, 22, 22)); paint(img, C('#8a9099'), ellipse(cx, 762, 9, 9))
    glow(img, 600, 300, 300, '#ffd27a', .08)
    return finish(img, .3, .014)


# ------------------------------------------------------------------ 옥탑방 폭염 (w2)
def rooftop():
    img = sky([(0, '#ff8a2a'), (.4, '#ffb84a'), (1, '#ffe7a8')])
    glow(img, 900, 120, 220, '#fff2c0', .9); glow(img, 900, 120, 70, '#ffffff', 1.0)
    # 먼 지붕들
    for i, (x0, t, x1) in enumerate([(0, 330, 240), (220, 360, 420), (980, 340, 1200)]):
        building(img, x0, t, x1, '#d08a5a', k=.15)
        windows(img, x0 + 10, t + 10, x1 - 10, 520, 4, 4, 18, 18, .4, lit='#ffe6b8', dark='#b8743a', seed=900 + i, glowk=0)
    depth(img, 2.0)
    # 초록 방수 옥상 바닥
    paint(img, F('#3a8a5a') * tex(910, 30, .8, 1.1)[..., None], poly([(0, 560), (W, 540), (W, 900), (0, 900)]))
    paint(img, C('#d8d0c0'), rect(0, 548, W, 566))
    # 옥탑방
    paint(img, F('#e8dcc8') * shade_v(300, 640, 1.05, .85)[..., None], rect(380, 330, 820, 640))
    paint(img, F('#2a6ab8') * .8, poly([(360, 340), (600, 260), (840, 340)]))
    paint(img, C('#6a5a4a'), rect(450, 450, 540, 640)); paint(img, C('#9fd0ef') * .8, rect(620, 420, 760, 520))
    paint(img, C('#f2f2f2'), lines([(620, 470, 760, 470), (690, 420, 690, 520)], 3))
    # 물탱크, 고추 화분, 빨랫줄
    paint(img, F('#2f6b8a') * shade_v(380, 520, 1.1, .7)[..., None], rect(900, 400, 1010, 520)); paint(img, C('#3f8aa8'), ellipse(955, 400, 55, 14))
    for x in range(120, 340, 50):
        paint(img, C('#b8603a'), poly([(x, 700), (x + 36, 700), (x + 30, 740), (x + 6, 740)]))
        paint(img, C('#4a8a2a'), ellipse(x + 18, 690, 22, 14)); paint(img, C('#d82a1a'), ellipse(x + 12, 694, 4, 8))
    paint(img, C('#555'), polyline([(840, 420), (1000, 450), (1160, 420)], 2))
    for (x, col) in [(900, '#e8e8e8'), (960, '#5a8ad8'), (1080, '#e86a8a')]:
        paint(img, C(col), poly([(x, 432), (x + 40, 438), (x + 38, 500), (x + 2, 496)]))
    # 선풍기
    paint(img, C('#e8e8e8'), ellipse(580, 600, 30, 30)); paint(img, C('#bbb'), rect(576, 630, 584, 680)); paint(img, C('#ddd'), ellipse(580, 682, 22, 6))
    sign(img, 40, 600, 300, 650, '#1d5fb8', ['경로당 무더위쉼터 ↓'], size=24)
    img[:] = displace_x(img, 1.4, .08, 520, H, 9)
    paint(img, C('#fff2d0'), smooth(.72, .9, noise(30, 3, 920, sy=10)) * np.clip((YY - 540) / 200, 0, 1), .22)
    return finish(img, .22, .012, warm=(1.04, 1.0, .93))


# ------------------------------------------------------------------ 마트 주차장 (w3)
def parking():
    img = sky([(0, '#ff9a3a'), (.4, '#ffc25a'), (1, '#ffe9b0')])
    glow(img, 220, 110, 200, '#fff2c0', .9); glow(img, 220, 110, 60, '#ffffff', 1.0)
    # 마트 건물
    building(img, 140, 220, 1080, '#e6e0d4', k=.12, roof='#b0a898')
    paint(img, C('#d8402a'), rect(140, 240, 1080, 330))
    text(img, 'OO마트', 610, 285, 64, '#ffffff')
    paint(img, F('#7ab0d0') * .85, rect(200, 380, 1020, 560))
    paint(img, C('#e6e0d4'), lines([(400, 380, 400, 560), (610, 380, 610, 560), (820, 380, 820, 560)], 6))
    # 주차장
    paint(img, F('#7a7068') * tex(1010, 30)[..., None], rect(0, 560, W, H))
    for x in range(0, W, 150):
        paint(img, C('#f2ede2'), poly([(x, 600), (x + 6, 600), (x - 60, 900), (x - 70, 900)]), .8)
    cols = ['#3a6ea5', '#e8e8e8', '#2a2a2a', '#b3282d', '#8a8f96', '#e8e8e8', '#2f5a3a']
    for i, x in enumerate(range(30, 1150, 160)):
        car(img, x, 640, 130, cols[i % len(cols)])
    # 앞쪽 차 (햇빛가리개)
    car(img, 380, 890, 460, '#c8c8cc')
    paint(img, C('#c0c4ca'), poly([(380 + 460 * .55, 890 - 156 * .94), (380 + 460 * .68, 890 - 156 * .94), (380 + 460 * .78, 890 - 156 * .66), (380 + 460 * .55, 890 - 156 * .66)]), .8)
    # 온도 표지
    paint(img, C('#5a5f66'), rect(1050, 440, 1060, 700))
    paint(img, C('#111'), rect(980, 360, 1130, 450)); text(img, '35℃', 1055, 405, 46, '#ffd400', glowk=.8)
    # 카트
    paint(img, C('#9aa3ad'), polyline([(150, 760), (160, 700), (250, 700), (240, 760), (150, 760)], 4))
    img[:] = displace_x(img, 1.6, .08, 600, H, 10)
    paint(img, C('#fff2d0'), smooth(.72, .9, noise(30, 3, 1020, sy=10)) * np.clip((YY - 600) / 200, 0, 1), .25)
    return finish(img, .22, .012, warm=(1.04, 1.0, .93))


# ------------------------------------------------------------------ 노후 아파트 균열 (c3)
def oldapt():
    img = sky([(0, '#2e323c'), (.6, '#6a6e78'), (1, '#9a9ca2')])
    paint(img, C('#4a4e58'), smooth(.4, .8, noise(220, 6, 1101)) * np.clip(1 - YY / 380, 0, 1), .6)
    apartment(img, 220, 170, 980, '#a8a296', 7, 6, .35, 1102, lit='#ffd98a', dark='#2a2a30', number='3', numcol='#5a5448', rail='#8a8478', k=.2)
    # 균열 (번지는)
    for pts in [[(420, 200), (440, 300), (410, 380), (450, 470), (430, 560), (470, 680)], [(760, 220), (735, 330), (770, 420), (740, 540)], [(600, 480), (650, 520), (640, 600), (700, 650)]]:
        paint(img, C('#1a1612'), polyline(pts, 5))
        paint(img, C('#d8d0c0'), polyline([(x + 3, y + 2) for x, y in pts], 1), .5)
    # 떨어진 콘크리트 조각
    rng = np.random.default_rng(11)
    for _ in range(18):
        x, y = 360 + rng.random() * 480, 735 + rng.random() * 40
        s = 6 + rng.random() * 14
        paint(img, C('#b0a898'), poly([(x, y), (x + s, y + 2), (x + s - 3, y + s * .6), (x - 2, y + s * .5)]))
    paint(img, F('#4a4844') * tex(1110, 30)[..., None], rect(0, GY, W, H))
    # 안전진단 안내 + 통제선
    sign(img, 40, 560, 300, 640, '#c8202a', ['접근 금지', '안전진단 중'], size=30, pole=820)
    tape = np.zeros((H, W, 3), np.float32); tm = rect(-40, 770, W + 40, 798)
    paint(tape, C('#ffd400'), tm)
    for i in range(8):
        text(tape, '통제선 · 출입금지', 80 + i * 180, 784, 19, '#111111')
    M = cv2.getRotationMatrix2D((600, 784), 2, 1)
    paint(img, cv2.warpAffine(tape, M, (W, H)), cv2.warpAffine(tm, M, (W, H)))
    people(img, [930, 970, 1010, 1060], 860, col='#3a3e48', s=1.3, seed=3)
    return finish(img, .28, .015)


# ------------------------------------------------------------------ 요양원 (v2)
def nursing():
    img = sky([(0, '#5a8a9a'), (.6, '#9ac0c8'), (1, '#c8dcdc')])
    # 가을 나무
    for (x, col) in [(80, '#c8702a'), (1120, '#d89a2a')]:
        paint(img, C('#5a3a2a'), rect(x - 8, 420, x + 8, GY))
        t = tex(1200 + x, 10, .7, 1.2)
        paint(img, F(col) * t[..., None], np.clip(ellipse(x, 380, 110, 90) + ellipse(x - 60, 430, 60, 50) + ellipse(x + 60, 430, 60, 50), 0, 1) * smooth(.3, .5, noise(12, 4, 1210 + x) + .2))
    building(img, 200, 220, 1000, '#efe8dc', k=.12, roof='#a87a5a')
    for f in range(3):
        windows(img, 220, 250 + f * 110, 980, 340 + f * 110, 10, 1, 52, 60, .4, lit='#ffe6b0', dark='#8aa8b8', seed=1220 + f, glowk=0, frame='#ffffff')
    paint(img, C('#2a7a5a'), rect(420, 196, 780, 246)); text(img, 'OO요양원', 600, 221, 34, '#ffffff')
    # 유리 현관 + 안내문
    paint(img, F('#a8d0e0') * .8, rect(500, 580, 700, GY))
    paint(img, C('#ffffff'), rect(560, 610, 640, 700))
    text(img, '면회', 600, 632, 18, '#c8202a'); text(img, '제한', 600, 656, 18, '#c8202a'); text(img, '안내', 600, 680, 18, '#c8202a')
    # 비대면 면회 부스
    paint(img, F('#f2f2f2'), rect(760, 600, 960, GY))
    paint(img, F('#bfe0ec') * .85, rect(776, 620, 944, 700))
    paint(img, C('#2a63b8'), rect(760, 570, 960, 604)); text(img, '비대면 면회실', 860, 587, 22, '#ffffff')
    paint(img, F('#8a8f96') * tex(1230, 30)[..., None], rect(0, GY, W, H))
    # 마스크 착용 안내
    sign(img, 250, 600, 440, 660, '#ffd400', ['마스크 착용 필수'], fg='#111111', size=24, pole=820)
    rng = np.random.default_rng(13)
    for (x, y, r) in [(160, 120, 22), (1000, 90, 16), (700, 120, 12)]:
        paint(img, C('#5fd0b0'), ellipse(x, y, r, r), .45)
        sp = np.zeros((H, W), np.float32)
        for k in range(10):
            t = k / 10 * 2 * np.pi
            cv2.circle(sp, (int(x + np.cos(t) * r * 1.3), int(y + np.sin(t) * r * 1.3)), 3, 1.0, -1, cv2.LINE_AA)
        paint(img, C('#d65a7a'), sp, .45)
    return finish(img, .22, .012)


SCENES = dict(underpass=underpass, valley=valley, market=market, wildfire=wildfire, tsunami=tsunami, school=school,
              gasleak=gasleak, rooftop=rooftop, parking=parking, oldapt=oldapt, nursing=nursing)
if __name__ == '__main__':
    names = sys.argv[2:] or list(SCENES)
    for n in names:
        save(SCENES[n](), f'{OUT}/{n}.webp', q=72)
        print('ok', n)
