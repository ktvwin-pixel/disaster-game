"""재난 현장 7종 회화풍 배경 · © 2026 KOREA CONTENTS LAB"""
import sys
from kit import *

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'


def sky(stops):
    return vgrad(stops).copy()


def apartment(img, x0, top, x1, base, floors, units, lit_p, seed, lit='#ffd38a', dark='#1b2233', number=None, numcol='#c9c2b0', rail='#9aa3ad', k=.3):
    building(img, x0, top, x1, base, k=k, roof='#3a3f4a')
    fh = (GY - top - 20) / floors
    rng = np.random.default_rng(seed)
    uw = (x1 - x0) / units
    gl = np.zeros((H, W), np.float32)
    for f in range(floors):
        y = top + 14 + f * fh
        for u in range(units):
            wx0, wx1 = x0 + u * uw + uw * .1, x0 + (u + 1) * uw - uw * .1
            m = rect(wx0, y + fh * .18, wx1, y + fh * .78)
            if rng.random() < lit_p:
                paint(img, C(lit) * (.75 + rng.random() * .3), m)
                gl += m
            else:
                paint(img, C(dark) * (.8 + rng.random() * .5), m)
            # 창살(세로 프레임)
            paint(img, C(base) * .7, rect((wx0 + wx1) / 2 - 1, y + fh * .18, (wx0 + wx1) / 2 + 1, y + fh * .78))
        # 발코니 난간 띠
        paint(img, C(rail) * .9, rect(x0, y + fh * .74, x1, y + fh * .84))
        paint(img, C(base) * 1.15, rect(x0, y + fh * .84, x1, y + fh * .92))
    add(img, C(lit), cv2.GaussianBlur(gl, (0, 0), 7), .3)
    if number:
        text(img, number, (x0 + x1) / 2, top - 2 + 0, int((x1 - x0) * .18), numcol, anchor='mb')


# ------------------------------------------------------------------ 침수
def flood():
    img = sky([(0, '#070d19'), (.35, '#14233a'), (.8, '#263f5e'), (1, '#2f4b6b')])
    cl = noise(260, 6, 11)
    a = smooth(.42, .78, cl) * np.clip(1.2 - YY / 380, 0, 1)
    paint(img, mix(C('#0a1220'), C('#1d2c44'), .3), a, .95)
    # 번개
    bolt = [(905, 0), (880, 70), (900, 74), (860, 160), (878, 162), (846, 236)]
    bm = polyline(bolt, 4)
    glow(img, 880, 90, 140, '#9fb8ff', .35)
    add(img, C('#eef4ff'), bm, 1.0)
    add(img, C('#b8ccff'), cv2.GaussianBlur(bm, (0, 0), 10), 1.2)
    # 원경 도시 (안개)
    for i, (x0, t, x1) in enumerate([(0, 300, 160), (150, 250, 300), (840, 280, 980), (960, 230, 1200)]):
        building(img, x0, t, x1, '#16233a', k=.2)
        windows(img, x0 + 8, t + 14, x1 - 8, GY - 120, max(3, (x1 - x0) // 34), 9, 12, 14, .28, seed=40 + i, dark='#101a2c', glowk=.25)
    depth(img, 2.2)
    haze = np.clip((YY - 200) / 500, 0, 1) * .35
    paint(img, C('#2a4262'), haze)
    # 빌라(벽돌) 3동
    brick = noise(6, 2, 7, sy=3)
    for i, (x0, t, x1, col) in enumerate([(70, 430, 400, '#6a4a3e'), (430, 380, 790, '#7a5a48'), (820, 440, 1150, '#5e4a42')]):
        m = rect(x0, t, x1, GY + 10)
        g = np.repeat(np.repeat(C(col)[None, None, :], H, 0), W, 1) * (shade_v(t, GY, 1.0, .7) * (.9 + .2 * brick))[..., None]
        paint(img, g * .55, m)
        paint(img, C('#8a8f96') * .5, rect(x0 - 8, t - 12, x1 + 8, t + 2))
        windows(img, x0 + 18, t + 20, x1 - 18, GY - 70, 4, 3, 54, 46, .6, lit='#ffcf7a', dark='#141c28', seed=60 + i, frame='#b9b2a6', glowk=.45)
        # 옥상 물탱크
        tx = x0 + (x1 - x0) * .7
        paint(img, C('#2f6b4a') * .6, rect(tx, t - 48, tx + 46, t - 12))
        paint(img, C('#3f8a60') * .6, ellipse(tx + 23, t - 48, 23, 6))
        # 반지하 창 (물에 잠김)
        for k in range(4):
            wx = x0 + 30 + k * (x1 - x0 - 60) / 4
            paint(img, C('#ffcf7a') * .8, rect(wx, GY - 46, wx + 50, GY - 16))
            glow(img, wx + 25, GY - 20, 26, '#ffb85a', .35)
    text(img, '반지하 주택가', 610, 372, 22, '#c9d4e4', alpha=.8)
    # 가로등
    paint(img, C('#3a4250'), rect(948, 330, 958, GY + 10))
    paint(img, C('#3a4250'), polyline([(953, 336), (953, 316), (990, 312), (1010, 312)], 7))
    paint(img, C('#f1f5f9'), rect(996, 306, 1036, 318))
    cone = poly([(1000, 318), (1032, 318), (1130, GY), (900, GY)], 18)
    add(img, C('#ffe9b0'), cone * smooth(330, GY, YY) * 0 + cone * (1 - (YY - 318) / 600), .22)
    glow(img, 1016, 318, 40, '#fff2c8', .7)
    # 침수 표지판
    paint(img, C('#5b6470'), rect(352, 600, 360, GY + 10))
    d = poly([(356, 548), (406, 598), (356, 648), (306, 598)])
    paint(img, C('#ffd400'), d)
    paint(img, C('#111111'), d - poly([(356, 556), (398, 598), (356, 640), (314, 598)]))
    text(img, '침수', 356, 600, 26, '#111111')
    # 잠긴 승용차
    car = poly([(470, 712), (492, 664), (520, 642), (640, 640), (680, 664), (712, 704), (716, 718), (470, 718)])
    gcar = np.repeat(np.repeat(C('#b3282d')[None, None, :], H, 0), W, 1) * shade_v(640, 718, 1.1, .6)[..., None]
    paint(img, gcar, car)
    paint(img, C('#1b2636'), poly([(506, 668), (528, 650), (580, 649), (580, 668)]))
    paint(img, C('#1b2636'), poly([(590, 649), (634, 650), (664, 668), (590, 668)]))
    add(img, C('#9fc0e0'), poly([(530, 652), (560, 651), (520, 666)], 2), .35)
    glow(img, 712, 730, 34, '#fff1b0', .8, 18)
    # 물 (수면 위 반사)
    WL = 700
    refl = cv2.flip(img[WL - 200:WL], 0)
    refl = cv2.resize(refl, (W, H - WL))
    n = noise(40, 3, 5, shape=(H - WL, W), sy=8)
    yy = np.arange(H - WL, dtype=np.float32)[:, None]
    mapx = (np.arange(W, dtype=np.float32)[None, :] + np.sin(yy * .55 + n * 9) * 10).astype(np.float32)
    mapy = np.repeat(yy, W, 1).astype(np.float32)
    refl = cv2.remap(refl, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    refl = cv2.GaussianBlur(refl, (0, 0), 2.2)
    water = vgrad([(0, '#2c5376'), (1, '#0d2036')], H - WL, W)
    wimg = water * .62 + refl * .55
    ripple = smooth(.62, .8, noise(30, 4, 8, shape=(H - WL, W), sy=5))
    wimg += C('#a9c8e6')[None, None, :] * ripple[..., None] * .18
    edge = np.clip(1 - (yy / 8), 0, 1)
    img[WL:] = img[WL:] * edge[..., None] * 0 + wimg * (1 - edge[..., None] * .2) + img[WL:] * edge[..., None] * .2
    paint(img, C('#9fc3e6'), lines([(0, WL + 1, W, WL + 1)], 2, 1.2), .5)
    # 떠다니는 잔해
    paint(img, C('#8a6a44'), poly([(780, 724), (826, 716), (832, 736), (786, 744)]))
    paint(img, C('#1c1c1c'), ellipse(240, 742, 26, 10))
    paint(img, C('#3a4a5a'), ellipse(240, 740, 12, 4))
    rain(img, 1300, -10, 38, .28, 3)
    return finish(img, .3, .014, warm=(.95, 1.0, 1.08))


# ------------------------------------------------------------------ 화재
def fire():
    img = sky([(0, '#08040a'), (.4, '#2a0f10'), (.75, '#6e2412'), (1, '#a1421a')])
    glow(img, 600, 380, 460, '#ff7a24', .6, 360)
    glow(img, 600, 200, 300, '#b0481e', .35, 200)
    # 원경
    for i, (x0, t, x1) in enumerate([(0, 360, 150), (140, 300, 330), (900, 320, 1050), (1040, 280, 1200)]):
        building(img, x0, t, x1, '#1a0f12', k=.15)
        windows(img, x0 + 8, t + 14, x1 - 8, GY - 90, max(3, (x1 - x0) // 34), 10, 12, 14, .2, lit='#ffc670', dark='#140b0e', seed=10 + i, glowk=.2)
    depth(img, 2.0)
    # 연기 기둥
    plume = poly([(470, 300), (760, 300), (980, 0), (1150, -60), (260, -60), (360, 0)])
    smoke(img, plume, 21, dark='#0c0909', lit='#e0662a', lit_from=(0, 330), density=1.0, scale=150)
    # 주 아파트 (103동)
    apartment(img, 420, 140, 800, '#5a4f52', 14, 4, .18, 31, lit='#ffc670', dark='#1b1416', number='103', numcol='#d8cdbf', rail='#8a7f80')
    # 불난 층
    for (fx, fy) in [(470, 438), (565, 438), (660, 438), (565, 396), (660, 396), (755, 396), (470, 480)]:
        paint(img, C('#ffb347'), rect(fx - 30, fy - 22, fx + 30, fy + 10))
        glow(img, fx, fy, 50, '#ff7a1a', .5)
    for i, (fx, fy, fw, fh) in enumerate([(470, 420, 80, 120), (565, 420, 90, 150), (660, 420, 80, 130), (565, 378, 80, 110), (660, 378, 90, 140), (755, 378, 70, 100)]):
        flames(img, fx, fy, fw, fh, 40 + i, .95)
    # 그을음
    soot = poly([(440, 380), (800, 380), (790, 160), (430, 160)])
    mul(img, 1 - cv2.GaussianBlur(soot, (0, 0), 30) * noise(40, 4, 7) * .55)
    # 불씨
    rng = np.random.default_rng(4)
    em = np.zeros((H, W), np.float32)
    for _ in range(160):
        x, y = 420 + rng.random() * 420, 120 + rng.random() * 360
        cv2.circle(em, (int(x), int(y)), int(1 + rng.random() * 2), 1.0, -1, cv2.LINE_AA)
    add(img, C('#ffcf7a'), em, .9)
    add(img, C('#ff8a2a'), cv2.GaussianBlur(em, (0, 0), 4), .8)
    # 도로 (젖은 반사)
    road = vgrad([(0, '#3a1b14'), (1, '#0e0809')], H - GY, W)
    img[GY:] = road
    refl = cv2.GaussianBlur(cv2.flip(img[GY - 150:GY], 0), (0, 0), 6)
    img[GY:] = img[GY:] * .7 + cv2.resize(refl, (W, H - GY)) * .45
    # 소방차 + 사다리
    lad = [(735, 640, 660, 430), (752, 640, 677, 430)]
    paint(img, C('#d0d5dc'), lines(lad, 6))
    for t in np.linspace(.05, .95, 11):
        x0, y0 = 735 - 75 * t, 640 - 210 * t
        paint(img, C('#d0d5dc'), lines([(x0, y0, x0 + 17, y0)], 3))
    mist = polyline([(668, 432), (640, 392), (610, 384), (590, 400)], 10, 6)
    add(img, C('#e8f4ff'), mist, .6)
    body = poly([(600, GY - 2), (600, 646), (840, 646), (840, 616), (910, 616), (944, 640), (952, GY - 2)])
    tg = np.repeat(np.repeat(C('#d01f26')[None, None, :], H, 0), W, 1) * shade_v(616, GY, 1.15, .65)[..., None]
    paint(img, tg, body)
    paint(img, C('#f2f2f2'), rect(600, 690, 952, 702))
    paint(img, C('#a9d4f0') * .8, poly([(852, 626), (906, 626), (934, 652), (852, 652)]))
    text(img, '119', 700, 672, 30, '#ffffff')
    paint(img, C('#ff2a2a'), rect(840, 600, 872, 614)); glow(img, 856, 606, 40, '#ff2a2a', .9)
    paint(img, C('#2a6aff'), rect(876, 600, 908, 614)); glow(img, 892, 606, 40, '#2a6aff', .7)
    for cx in (660, 900):
        paint(img, C('#121212'), ellipse(cx, GY + 2, 30, 30))
        paint(img, C('#8a9099'), ellipse(cx, GY + 2, 12, 12))
    # 소방 호스
    paint(img, C('#e8e2d0') * .7, polyline([(610, GY + 20), (520, GY + 60), (380, GY + 50), (300, GY + 90)], 6))
    return finish(img, .32, .013)


# ------------------------------------------------------------------ 지진
def quake():
    img = sky([(0, '#1b1826'), (.45, '#4a3d5a'), (.8, '#9a7266'), (1, '#c38a62')])
    dust = noise(200, 5, 3)
    # 원경
    for i, (x0, t, x1) in enumerate([(0, 330, 200), (980, 300, 1200)]):
        building(img, x0, t, x1, '#2e2838', k=.2)
        windows(img, x0 + 8, t + 14, x1 - 8, GY - 60, 5, 10, 14, 16, .3, lit='#f3d59a', dark='#221d2a', seed=70 + i)
    depth(img, 2.0)
    # 기울어진 건물 (왼쪽)
    tmp = img.copy()
    building(tmp, 150, 240, 420, '#6a5f6c', k=.3, roof='#3c3644')
    windows(tmp, 166, 262, 404, GY - 20, 6, 11, 26, 26, .35, lit='#f3d59a', dark='#1d1a24', seed=80, frame='#9a8f9a')
    M = cv2.getRotationMatrix2D((285, GY), 4.5, 1)
    tmp = cv2.warpAffine(tmp, M, (W, H), borderMode=cv2.BORDER_TRANSPARENT, dst=img.copy())
    img[:] = tmp
    crack = polyline([(300, 260), (320, 330), (290, 380), (330, 460), (300, 540), (340, 640)], 5)
    paint(img, C('#0d0a10'), crack)
    # 상가 건물 (가운데) + 간판
    building(img, 440, 420, 860, '#7a6f72', k=.25, roof='#4a4248')
    windows(img, 456, 520, 844, GY - 20, 5, 2, 56, 60, .4, lit='#f3d59a', dark='#1d1a24', seed=81, frame='#a89ea0')
    signs = [('약국', '#2a7a3a', 0), ('분식', '#c8402a', 0), ('안경', '#2a58b8', 0)]
    for i, (s, col, _) in enumerate(signs):
        x = 456 + i * 132
        paint(img, C(col), rect(x, 440, x + 120, 494))
        text(img, s, x + 60, 467, 30, '#ffffff')
    # 떨어지는 간판
    lay = np.zeros((H, W, 3), np.float32); mm = rect(560, 500, 720, 548)
    paint(lay, C('#e0a020'), mm); text(lay, '노래방', 640, 524, 28, '#3a1a0a')
    M = cv2.getRotationMatrix2D((640, 524), -24, 1)
    lay = cv2.warpAffine(lay, M, (W, H)); mm = cv2.warpAffine(mm, M, (W, H))
    paint(img, lay, mm)
    paint(img, C('#0d0a10'), polyline([(460, 420), (500, 470), (470, 520), (520, 600)], 4))
    paint(img, C('#0d0a10'), polyline([(840, 430), (800, 500), (830, 560), (790, 650)], 4))
    # 기울어진 전봇대와 전선
    pole = np.zeros((H, W, 3), np.float32); pm = rect(890, 260, 904, GY + 10) + rect(856, 290, 940, 300) + rect(864, 320, 932, 328)
    pm = np.clip(pm, 0, 1); paint(pole, C('#6b5848'), pm)
    paint(pole, C('#8a9097'), rect(906, 336, 930, 380)); pm = np.clip(pm + rect(906, 336, 930, 380), 0, 1)
    M = cv2.getRotationMatrix2D((897, GY), -13, 1)
    pole = cv2.warpAffine(pole, M, (W, H)); pm = cv2.warpAffine(pm, M, (W, H))
    paint(img, pole, pm)
    for (a, b) in [((0, 360), (800, 340)), ((0, 380), (806, 362)), ((830, 330), (1200, 400))]:
        xs = np.linspace(a[0], b[0], 30); ys = np.linspace(a[1], b[1], 30) + np.sin(np.linspace(0, np.pi, 30)) * 60
        paint(img, C('#100c12'), polyline(list(zip(xs, ys)), 2))
    # 먼지
    paint(img, C('#c8b49a'), smooth(.45, .9, dust) * np.clip((YY - 350) / 400, 0, 1), .4)
    # 도로 + 균열
    img[GY:] = vgrad([(0, '#3e3842'), (1, '#18151b')], H - GY, W)
    for x in range(40, 1200, 170):
        paint(img, C('#d8d0c0'), rect(x, 818, x + 80, 826), .5)
    fis = poly([(260, 800), (380, 776), (440, 812), (540, 784), (620, 830), (730, 790), (860, 820), (960, 800), (860, 840), (730, 812), (620, 860), (540, 812), (440, 850), (380, 800)])
    paint(img, C('#060408'), fis)
    paint(img, C('#8c808e'), polyline([(380, 776), (440, 812), (540, 784), (620, 830), (730, 790)], 3))
    rng = np.random.default_rng(5)
    for _ in range(26):
        x, y = 360 + rng.random() * 200, 700 + rng.random() * 60
        paint(img, C('#a0624a') * (.7 + rng.random() * .4), poly([(x, y), (x + 26, y + 4), (x + 22, y + 16), (x - 2, y + 12)]))
    # 대피소 표지판
    paint(img, C('#5b6470'), rect(1012, 560, 1020, GY + 10))
    paint(img, C('#1d8a4c'), rect(940, 500, 1092, 568))
    text(img, '대피소', 1016, 520, 26, '#ffffff'); text(img, '→ 200m', 1016, 552, 22, '#ffffff')
    paint(img, C('#c8b49a'), smooth(.55, .95, noise(90, 5, 12)) * np.clip((YY - 600) / 300, 0, 1), .35)
    return finish(img, .3, .014)


# ------------------------------------------------------------------ 폭발
def blast():
    img = sky([(0, '#5a5048'), (.45, '#8a6e58'), (.8, '#b88a5e'), (1, '#d39a62')])
    # 원경 공장
    for (x0, t, w) in [(60, 300, 36), (120, 360, 28), (1090, 320, 36)]:
        building(img, x0, t, x0 + w, '#2a1e1a', k=.1)
    for (x0, t, x1) in [(0, 520, 260), (930, 500, 1200)]:
        building(img, x0, t, x1, '#2e2420', k=.15)
    depth(img, 2.0)
    # 버섯구름
    stem = poly([(560, 640), (586, 470), (566, 330), (720, 330), (700, 470), (726, 640)])
    cap = ellipse(640, 270, 250, 120) + ellipse(520, 300, 120, 90) + ellipse(760, 300, 130, 95) + ellipse(640, 200, 150, 90)
    smoke(img, np.clip(stem + cap, 0, 1), 52, dark='#1e1714', lit='#d8642a', lit_from=(120, 640), density=1, scale=110)
    # 불덩이
    fb = noise(40, 6, 61)
    r = np.sqrt(((XX - 640) / 210) ** 2 + ((YY - 560) / 150) ** 2)
    inten = 1.0 - r + (fb - .5) * .9
    a = smooth(.05, .3, inten) * (YY < GY + 4)
    pal = np.stack([np.clip(.75 + inten * .6, 0, 1), np.clip(.18 + inten * .9, 0, 1), np.clip(-.35 + inten * 1.1, 0, 1)], -1).astype(np.float32)
    paint(img, pal, a)
    glow(img, 640, 560, 260, '#ff8a2a', .55, 190)
    glow(img, 640, 590, 70, '#fff2b0', .35)
    # 충격파 먼지 고리
    ring = ellipse(640, GY - 6, 520, 46, 6) - ellipse(640, GY - 6, 470, 30, 8)
    smoke(img, np.clip(ring, 0, 1), 70, dark='#8a6a50', density=.8, scale=50)
    # 저장탱크 (구형·원통형)
    for (cx, cy, rr) in [(170, 580, 92)]:
        sph = ellipse(cx, cy, rr, rr)
        shade = np.clip(1.15 - np.sqrt(((XX - cx + 30) / rr) ** 2 + ((YY - cy + 30) / rr) ** 2) * .6, .35, 1.1)
        g = np.repeat(np.repeat(C('#cfc8bc')[None, None, :], H, 0), W, 1) * shade[..., None]
        add(img, C('#ff8a3a'), sph * np.clip((XX - cx) / rr, 0, 1), .25)
        paint(img, g, sph)
        for lx in (-60, -20, 20, 60):
            paint(img, C('#6a625a'), rect(cx + lx - 4, cy + 60, cx + lx + 4, GY - 20))
    cyl = rect(300, 520, 410, GY - 20)
    g = np.repeat(np.repeat(C('#bfb7aa')[None, None, :], H, 0), W, 1) * (0.55 + .6 * np.clip(1 - np.abs((XX - 335) / 70), 0, 1))[..., None]
    paint(img, g, cyl); paint(img, C('#d8d0c4'), ellipse(355, 520, 55, 12))
    for y in (580, 640, 700):
        paint(img, C('#8a8278'), rect(300, y, 410, y + 5))
    # 배관
    for y, col in ((690, '#7a6b60'), (712, '#5e5048')):
        paint(img, C(col), rect(0, y, W, y + 10))
    # 펜스 + 경고판
    img[GY:] = vgrad([(0, '#4a3a2e'), (1, '#1e1612')], H - GY, W)
    fence = np.zeros((H, W), np.float32)
    for x in range(0, W, 26):
        cv2.line(fence, (x, 680), (x, GY + 30), 1.0, 2, cv2.LINE_AA)
    cv2.line(fence, (0, 684), (W, 684), 1.0, 3, cv2.LINE_AA)
    paint(img, C('#8a7d70'), fence, .8)
    paint(img, C('#f4f1ea'), rect(470, 690, 620, 768)); paint(img, C('#c0392b'), rect(470, 690, 620, 768) - rect(476, 696, 614, 762))
    tri = poly([(506, 704), (532, 750), (480, 750)])
    paint(img, C('#ffd400'), tri); text(img, '!', 506, 736, 26, '#111111')
    text(img, '위험', 574, 714, 26, '#c0392b'); text(img, '출입금지', 574, 746, 20, '#c0392b')
    # 파편
    rng = np.random.default_rng(8)
    for _ in range(8):
        x, y = 400 + rng.random() * 480, 400 + rng.random() * 200
        s = 5 + rng.random() * 7
        paint(img, C('#2a1a12'), poly([(x, y), (x + s, y + s * .3), (x + s * .7, y + s), (x - s * .2, y + s * .6)], 2.2), .8)
    for _ in range(30):
        x, y = rng.random() * W, 780 + rng.random() * 110
        add(img, C('#bfe0f0'), poly([(x, y), (x + 8, y + 2), (x + 2, y + 6)]), .4)
    return finish(img, .3, .014)


# ------------------------------------------------------------------ 폭염
def heat():
    img = sky([(0, '#ff7a24'), (.35, '#ffa83a'), (.75, '#ffd77a'), (1, '#ffe9b0')])
    glow(img, 600, 150, 260, '#fff2c0', .8)
    glow(img, 600, 150, 90, '#ffffff', 1.0)
    rays = np.zeros((H, W), np.float32)
    ang = np.arctan2(YY - 150, XX - 600)
    rays = (np.cos(ang * 12) * .5 + .5) * np.exp(-np.sqrt((XX - 600) ** 2 + (YY - 150) ** 2) / 260)
    add(img, C('#fff4cc'), rays, .25)
    # 아지랑이 낀 도시 (원경은 흐리게)
    for i, (x0, t, x1) in enumerate([(0, 300, 180), (170, 360, 330), (870, 340, 1020), (1010, 280, 1200)]):
        building(img, x0, t, x1, '#d08a4a', k=.15)
        windows(img, x0 + 10, t + 14, x1 - 10, GY - 80, max(3, (x1 - x0) // 36), 10, 14, 18, .5, lit='#ffe6b8', dark='#b8743a', seed=90 + i, glowk=0)
    depth(img, 2.4)
    paint(img, C('#ffcf8a'), np.clip(1 - np.abs(YY - 520) / 260, 0, 1), .45)
    # 타워크레인
    cr = []
    for i in range(16):
        y = 160 + i * 30
        cr += [(230, y, 252, y + 30), (252, y, 230, y + 30)]
    cr += [(230, 160, 230, 640), (252, 160, 252, 640), (120, 160, 520, 160), (120, 176, 520, 176), (440, 176, 440, 260)]
    paint(img, C('#8a5a2e'), lines(cr, 3), .65)
    # 전광판
    paint(img, C('#5a5f66'), rect(592, 420, 608, GY + 10))
    paint(img, C('#3a3a3a'), rect(440, 290, 760, 436))
    paint(img, C('#0e0e0e'), rect(450, 300, 750, 426))
    text(img, '폭염경보 발령', 600, 334, 34, '#ff5a3a', glowk=.6)
    text(img, '37℃', 600, 396, 64, '#ffd400', glowk=.8)
    # 무더위쉼터 안내
    paint(img, C('#1d5fb8'), rect(930, 430, 1110, 480)); text(img, '무더위쉼터', 1020, 455, 30, '#ffffff')
    # 시든 가로수
    paint(img, C('#6b4a2a'), rect(326, 560, 340, GY))
    can = ellipse(333, 560, 74, 50) + ellipse(300, 590, 44, 30) + ellipse(370, 590, 44, 30)
    tex = noise(14, 4, 33)
    leaf = np.repeat(np.repeat(C('#8a9440')[None, None, :], H, 0), W, 1) * (.7 + .5 * tex[..., None])
    paint(img, leaf, np.clip(can, 0, 1) * smooth(.25, .5, tex + .2))
    # 그늘막
    paint(img, C('#e8e8e8'), rect(866, 566, 874, GY + 6))
    para = poly([(760, 580), (870, 520), (980, 580), (950, 590), (870, 584), (790, 590)])
    paint(img, mix(C('#2f8a4a'), C('#1f6a36'), .3), para)
    add(img, C('#9fe0b0'), poly([(870, 520), (900, 586), (870, 584)]), .3)
    # 도로 + 횡단보도 + 신기루
    road = vgrad([(0, '#8a7768'), (1, '#4a3c34')], H - GY, W)
    img[GY:] = road
    paint(img, C('#2a1e16'), ellipse(870, GY + 14, 120, 12, 6), .45)
    for i in range(10):
        x = 330 + i * 56
        paint(img, C('#f2ede2'), poly([(x, 790), (x + 30, 790), (x + 40, 890), (x + 4, 890)]), .9)
    mirage = cv2.flip(img[GY - 60:GY], 0)
    img[GY:GY + 60] = img[GY:GY + 60] * .7 + mirage * .3
    img[:] = displace_x(img, 1.6, .08, 560, GY, 3)
    hz = noise(30, 3, 19, sy=10)
    paint(img, C('#fff2d0'), smooth(.7, .9, hz) * np.clip((YY - 560) / 200, 0, 1) * (YY < GY + 120), .25)
    return finish(img, .22, .012, warm=(1.04, 1.0, .93))


# ------------------------------------------------------------------ 건물붕괴
def collapse():
    img = sky([(0, '#262833'), (.5, '#55575f'), (1, '#9a9a9e')])
    cl = noise(220, 6, 41)
    paint(img, C('#3a3c46'), smooth(.4, .8, cl) * np.clip(1 - YY / 420, 0, 1), .7)
    for i, (x0, t, x1) in enumerate([(0, 300, 210), (990, 280, 1200)]):
        building(img, x0, t, x1, '#3a3c46', k=.2)
        windows(img, x0 + 10, t + 14, x1 - 10, GY - 60, 5, 11, 16, 18, .15, lit='#d9d4b8', dark='#2a2c34', seed=100 + i, glowk=.1)
    depth(img, 2.0)
    # 서 있는 잔존부
    building(img, 330, 190, 560, '#8d8780', k=.25, roof='#6a645e')
    for f in range(10):
        y = 200 + f * 48
        paint(img, C('#a9a39b'), rect(330, y, 560, y + 10))
        paint(img, C('#1f1c1b'), rect(344, y + 14, 546, y + 44))
        for x in (420, 486):
            paint(img, C('#8d8780') * .9, rect(x, y + 10, x + 10, y + 48))
    # 철근
    rb = []
    for y in range(220, 640, 48):
        rb += [(560, y, 590, y - 14), (560, y + 4, 584, y + 16), (560, y + 8, 594, y + 2)]
    paint(img, C('#7a3e26'), lines(rb, 2))
    # 무너진 슬래브 (팬케이크)
    for i, (y0, y1, x1, drop) in enumerate([(380, 400, 820, 160), (470, 490, 860, 150), (560, 580, 900, 120), (640, 660, 930, 70)]):
        slab = poly([(560, y0), (x1, y0 + drop), (x1, y1 + drop), (560, y1)])
        g = np.repeat(np.repeat(C('#9b958d')[None, None, :], H, 0), W, 1) * (.75 + .3 * noise(20, 3, 200 + i)[..., None])
        paint(img, g, slab)
        paint(img, C('#5a5550'), lines([(560, y1, x1, y1 + drop)], 3))
    hang = poly([(560, 260), (700, 360), (692, 372), (556, 276)])
    paint(img, C('#a39d95'), hang)
    # 잔해 더미
    pile = poly([(240, GY + 10), (330, 650), (420, 680), (520, 620), (640, 660), (760, 630), (880, 670), (980, GY + 10)])
    tex = noise(18, 5, 77)
    g = np.repeat(np.repeat(C('#7a756f')[None, None, :], H, 0), W, 1) * (.6 + .6 * tex[..., None])
    paint(img, g, pile)
    rng = np.random.default_rng(9)
    for _ in range(60):
        x, y = 280 + rng.random() * 660, 640 + rng.random() * 100
        s = 10 + rng.random() * 26
        paint(img, C('#a8a29a') * (.7 + rng.random() * .5), poly([(x, y), (x + s, y + 4), (x + s - 6, y + s * .7), (x - 4, y + s * .5)]))
    paint(img, C('#7a3e26'), lines([(rng.random() * 600 + 300, 660 + rng.random() * 60, rng.random() * 600 + 300, 620 + rng.random() * 60) for _ in range(14)], 2))
    # 먼지
    smoke(img, ellipse(620, 600, 360, 120), 88, dark='#bdb3a4', density=.55, scale=90)
    # 굴착기
    paint(img, C('#f2b705'), poly([(940, GY - 4), (940, 640), (1040, 640), (1040, 600), (1110, 600), (1120, 640), (1150, 640), (1150, GY - 4)]))
    paint(img, C('#9fd0ef') * .8, rect(1052, 610, 1100, 638))
    paint(img, C('#e0a400'), polyline([(1000, 630), (930, 520), (850, 600)], 16))
    paint(img, C('#444444'), poly([(850, 600), (820, 640), (870, 646)]))
    paint(img, C('#2a2a2a'), rect(930, GY - 4, 1160, GY + 24))
    # 구조 조명
    beam = poly([(176, 470), (190, 470), (640, 660), (520, 720)], 10)
    add(img, C('#fffbe8'), beam * np.clip(1 - (XX - 180) / 520, 0, 1), .35)
    paint(img, C('#e5e7eb'), rect(160, 456, 200, 484)); glow(img, 196, 470, 26, '#ffffff', .8)
    paint(img, C('#6b7280'), lines([(180, 484, 150, 600), (180, 484, 210, 600), (180, 484, 180, 600)], 4))
    img[GY:] = np.maximum(img[GY:] * 0, vgrad([(0, '#5a5650'), (1, '#24221f')], H - GY, W))
    # 통제선
    tape = np.zeros((H, W, 3), np.float32); tm = rect(-40, 704, W + 40, 734)
    paint(tape, C('#ffd400'), tm)
    for i in range(8):
        text(tape, '통제선 · 출입금지', 80 + i * 180, 719, 20, '#111111')
    M = cv2.getRotationMatrix2D((600, 719), 3, 1)
    tape = cv2.warpAffine(tape, M, (W, H)); tm = cv2.warpAffine(tm, M, (W, H))
    paint(img, tape, tm)
    return finish(img, .3, .016)


# ------------------------------------------------------------------ 감염병확산
def virus():
    img = sky([(0, '#173a46'), (.55, '#3c7a80'), (1, '#8fbdb8')])
    paint(img, C('#d8ecea'), smooth(.5, .85, noise(240, 5, 51)) * np.clip(1 - YY / 360, 0, 1), .35)
    for i, (x0, t, x1) in enumerate([(0, 340, 140), (1000, 320, 1200)]):
        building(img, x0, t, x1, '#2c5258', k=.2)
        windows(img, x0 + 10, t + 14, x1 - 10, GY - 60, 4, 10, 14, 16, .3, lit='#d8f0f0', dark='#22444a', seed=110 + i, glowk=0)
    depth(img, 2.0)
    # 병원
    building(img, 150, 200, 600, '#e6eef0', k=.18, roof='#b9c6ca')
    windows(img, 170, 300, 580, GY - 120, 8, 6, 38, 40, .55, lit='#a8d4ec', dark='#6e93a8', seed=120, glowk=0)
    paint(img, C('#ffffff'), rect(260, 220, 490, 280))
    paint(img, C('#d62828'), rect(282, 236, 318, 248) + rect(294, 224, 306, 260))
    text(img, 'OO병원', 400, 250, 38, '#1d3a40')
    paint(img, C('#7fa9bf'), rect(320, GY - 110, 430, GY)); paint(img, C('#e6eef0'), rect(372, GY - 110, 378, GY))
    # 선별진료소 천막
    tent = poly([(620, 560), (790, 470), (960, 560)])
    paint(img, C('#f7fafb'), tent)
    add(img, C('#c8d8de'), poly([(790, 470), (960, 560), (790, 560)]), .25)
    paint(img, C('#eef3f5'), rect(632, 560, 948, GY))
    paint(img, C('#2a63b8'), rect(632, 700, 948, GY))
    paint(img, C('#2c3e45'), rect(720, 590, 860, GY))
    paint(img, C('#c9d3d7'), rect(708, 680, 872, 700))
    paint(img, C('#1f5fbf'), rect(670, 486, 910, 540)); text(img, '선별진료소', 790, 513, 34, '#ffffff')
    # 구급차
    paint(img, C('#f7f7f7'), poly([(420, GY - 4), (420, 650), (560, 650), (560, 632), (610, 632), (636, 664), (640, GY - 4)]))
    paint(img, C('#d62828'), rect(420, 682, 640, 694))
    paint(img, C('#9fd0ef'), poly([(566, 640), (604, 640), (624, 664), (566, 664)]))
    text(img, '119 구급', 490, 668, 22, '#d62828')
    paint(img, C('#ff3b3b'), rect(560, 620, 580, 630)); glow(img, 570, 625, 30, '#ff3b3b', .6)
    paint(img, C('#3b7bff'), rect(584, 620, 604, 630)); glow(img, 594, 625, 30, '#3b7bff', .5)
    for cx in (460, 600):
        paint(img, C('#121212'), ellipse(cx, GY, 20, 20)); paint(img, C('#8a9099'), ellipse(cx, GY, 8, 8))
    img[GY:] = vgrad([(0, '#5a666a'), (1, '#2a3236')], H - GY, W)
    for i in range(6):
        paint(img, C('#ffd400'), rect(660 + i * 50, 790, 690 + i * 50, 800))
    text(img, '거리두기 1m', 790, 830, 20, '#e6edf0', alpha=.85)
    # 바이러스 입자 (입체)
    rng = np.random.default_rng(12)
    for (x, y, r, a) in [(120, 120, 34, .85), (330, 70, 22, .7), (980, 110, 40, .85), (1100, 260, 24, .7), (700, 300, 18, .55), (60, 420, 20, .6), (880, 380, 14, .5)]:
        body = ellipse(x, y, r, r)
        sh = np.clip(1.1 - np.sqrt(((XX - x + r * .35) / r) ** 2 + ((YY - y + r * .35) / r) ** 2) * .7, .3, 1.1)
        g = np.repeat(np.repeat(C('#5fd0b0')[None, None, :], H, 0), W, 1) * sh[..., None]
        sp = np.zeros((H, W), np.float32)
        for k in range(12):
            t = k / 12 * 2 * np.pi
            x1, y1 = x + np.cos(t) * r, y + np.sin(t) * r
            x2, y2 = x + np.cos(t) * (r * 1.35), y + np.sin(t) * (r * 1.35)
            cv2.line(sp, (int(x1), int(y1)), (int(x2), int(y2)), 1.0, max(2, int(r / 9)), cv2.LINE_AA)
            cv2.circle(sp, (int(x2), int(y2)), max(3, int(r / 6)), 1.0, -1, cv2.LINE_AA)
        paint(img, C('#d65a7a'), sp, a)
        paint(img, g, body, a)
        add(img, C('#bff5e6'), ellipse(x - r * .35, y - r * .35, r * .3, r * .22, 3), .5 * a)
    return finish(img, .26, .012)


SCENES = dict(flood=flood, fire=fire, quake=quake, blast=blast, heat=heat, collapse=collapse, virus=virus)
if __name__ == '__main__':
    names = sys.argv[2:] or list(SCENES)
    for n in names:
        save(SCENES[n](), f'{OUT}/{n}.webp')
        print('ok', n)
