# -*- coding: utf-8 -*-
import os
import subprocess
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\Users\neelk\.cursor\projects\c-Users-neelk-Cursor\assets\c__Users_neelk_AppData_Roaming_Cursor_User_workspaceStorage_192335c513fdd2f6f873c8a84d0ff9a8_images_WhatsApp_Image_2026-10-08_at_14.05.55-5a047f7f-0df1-4f58-9eec-0e6894e05363.jpg"
OVERLAY = os.path.join(HERE, "slip-overlay.html")
SHOT = os.path.join(HERE, "slip-text.png")
OUT = os.path.join(HERE, "voter-slip-swati-basu.jpg")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

orig = cv2.imread(SRC)
origf = orig.astype(np.float32)
img = origf.copy()
rng = np.random.default_rng(7)

# Boxes must stay inside table cells so no ruled lines are lost.
boxes = [
    (222, 96, 412, 156),    # handwritten "Rama Roy."
    (667, 345, 701, 363),   # top-right Part No.
    (667, 366, 701, 385),   # top-right Serial No.
    (406, 431, 548, 457),   # AC (Bengali)
    (552, 431, 739, 457),   # AC (English)
    (406, 465, 548, 483),   # Name (Bengali)
    (552, 465, 739, 483),   # Name (English)
    (406, 487, 548, 504),   # Gender (Bengali)
    (552, 487, 739, 504),   # Gender (English)
    (406, 507, 560, 524),   # EPIC
    (200, 528, 270, 548),   # "Fathers Name" label (Bengali)
    (312, 528, 400, 548),   # "Fathers Name" label (English)
    (406, 528, 548, 548),   # Father (Bengali)
    (552, 528, 739, 548),   # Father (English)
    (406, 553, 470, 569),   # Part No.
    (406, 573, 739, 618),   # Part Name
    (406, 625, 470, 642),   # Serial No.
    (406, 645, 742, 691),   # Polling station
    (100, 706, 194, 724),   # Date of Poll value
    (406, 705, 480, 720),   # Last updated value
    (406, 762, 748, 780),   # District election office value
]

# Paper with the ink closed out, then shifted back to the real paper tone.
# Only pixels darker than that paper are replaced, so no rectangle is painted.
closed = cv2.morphologyEx(
    orig, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
).astype(np.float32)
paper = cv2.GaussianBlur(closed, (0, 0), 2)
diff = paper - origf
clean = (diff.mean(2) < 8).astype(np.float32)
num = cv2.GaussianBlur(diff * clean[..., None], (0, 0), 11)
den = cv2.GaussianBlur(np.repeat(clean[..., None], 3, axis=2), (0, 0), 11) + 1e-3
paper = paper - num / den
delta = paper.mean(2) - origf.mean(2)

ink = np.zeros(orig.shape[:2], np.float32)
for x0, y0, x1, y1 in boxes:
    dark = np.clip((delta[y0:y1, x0:x1] - 6) / 8.0, 0, 1)
    dark = cv2.dilate(dark, np.ones((2, 2), np.uint8))
    dark = cv2.GaussianBlur(dark, (0, 0), 0.35)
    ink[y0:y1, x0:x1] = np.maximum(ink[y0:y1, x0:x1], dark)
    sub = origf[y0:y1, x0:x1]
    img[y0:y1, x0:x1] = sub * (1 - dark[..., None]) + paper[y0:y1, x0:x1] * dark[..., None]

# Ink colours (RGB) are picked so the darkest pixels after softening land
# on what the same kind of text measures in the original photo.
INK = {
    "en": "rgb(78,78,82)",
    "en10": "rgb(26,30,36)",
    "big": "rgb(92,96,100)",
    "small": "rgb(92,92,95)",
    "bn": "rgb(38,42,48)",
    "epic": "rgb(26,30,36)",
    "dop": "rgb(62,58,62)",
    "lbl": "rgb(38,28,26)",
    "bnlbl": "rgb(44,34,38)",
    "hand": "rgb(86,88,100)",
}

# (left, top, text, class)
texts = [
    (240, 100, "Swati Basu", "hand"),
    (673, 347, "233", "big"),
    (673, 366, "990", "big"),
    (407, 433, "97 - গাইঘাটা (তফসিলি জাতি)", "bn"),
    (573, 432.5, "97 - Gaighata (SC)", "en"),
    (407, 466, "স্বাতী বসু", "bn"),
    (573, 467.5, "Swati Basu", "en"),
    (407, 487, "মহিলা", "bn"),
    (573, 489.5, "Female", "en"),
    (407, 509, "DKJ3430501", "epic"),
    (202, 530, "আত্মীয়ের নাম", "bnlbl"),
    (314, 531, "Relative's Name", "lbl"),
    (407, 530, "বিভাস বসু", "bn"),
    (573, 530.5, "Bibhas Basu", "en"),
    (407, 555.5, "233", "epic"),
    (407, 576, "Gobaradanga Kalejiyet School (Pashchim O Purb)", "en10"),
    (407, 630.5, "990", "epic"),
    (407, 649, "Gobaradanga Kalejiyet School (Pashchim O Purb), Room-2,", "en10"),
    (407, 662, "Gapur", "en10"),
    (107, 710.5, "29.4.2026", "dop"),
    (408, 765.5, "Office of the District Magistrate &amp; District Election Officer North 24 Pgs", "small"),
]

divs = "\n".join(
    f'<div class="{c}" style="left:{x}px;top:{y}px">{t}</div>' for x, y, t, c in texts
)
html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;width:771px;height:1024px;overflow:hidden;background:#fff}}
div{{position:absolute;white-space:nowrap;line-height:1;color:#000;-webkit-font-smoothing:antialiased}}
.en{{font:10.6px Arial,sans-serif}}
.en10{{font:10.2px Arial,sans-serif}}
.big{{font:15px Arial,sans-serif}}
.small{{font:10.3px Arial,sans-serif}}
.epic{{font:11.4px Arial,sans-serif}}
.dop{{font:bold 11.2px Arial,sans-serif}}
.lbl{{font:10.6px Arial,sans-serif;letter-spacing:-.15px}}
.bn{{font:11.5px Vrinda,'Nirmala UI',sans-serif}}
.bnlbl{{font:11px Vrinda,'Nirmala UI',sans-serif}}
.hand{{font:33px 'Ink Free','Segoe Print',cursive;transform:rotate(1.2deg);transform-origin:0 0}}
</style></head><body>
{divs}
</body></html>"""
with open(OVERLAY, "w", encoding="utf-8") as f:
    f.write(html)

if os.path.exists(SHOT):
    os.remove(SHOT)
subprocess.run([
    EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
    "--force-device-scale-factor=1", "--window-size=771,1024",
    "--default-background-color=FFFFFFFF",
    f"--screenshot={SHOT}", "file:///" + OVERLAY.replace("\\", "/"),
], check=True, timeout=60)

shot = cv2.imread(SHOT)[:1024, :771].astype(np.float32)
# Black text on white: the grey of each pixel is coverage, not a white fringe.
cover = np.clip((255.0 - shot.max(2)) / 255.0, 0, 1)
cover = cv2.GaussianBlur(cover, (0, 0), 0.45)
cover[cover < 0.04] = 0

# Tint each glyph with the ink shade of the line it belongs to.
anchors = []
for x, y, text, cls in texts:
    anchors.append((y + 6, x + max(8, len(text) * 3), cls))
ay = np.array([a[0] for a in anchors])
ax = np.array([a[1] for a in anchors])
ac = [a[2] for a in anchors]
ys, xs = np.nonzero(cover > 0)
dist = ((ys[:, None] - ay[None, :]) / 7.0) ** 2 + ((xs[:, None] - ax[None, :]) / 70.0) ** 2
nearest = dist.argmin(1)
ink_bgr = np.zeros_like(img)
for i, cls in enumerate(ac):
    r, g, b = [int(v) for v in INK[cls][4:-1].split(",")]
    sel = nearest == i
    ink_bgr[ys[sel], xs[sel]] = (b, g, r)

img = img * (1 - cover[..., None]) + ink_bgr * cover[..., None]
grain = rng.normal(0, 1.3, img.shape) * np.clip(cover[..., None] * 2.5, 0, 1)
img += grain

out = np.clip(img, 0, 255).astype(np.uint8)
ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 84])
out = cv2.imdecode(buf, cv2.IMREAD_COLOR)
cv2.imwrite(OUT, out, [cv2.IMWRITE_JPEG_QUALITY, 95])
os.remove(SHOT)
print("saved", OUT)
