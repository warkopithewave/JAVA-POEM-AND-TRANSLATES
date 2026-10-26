"""Pembuat kartu bagikan Waskita Sastra (PNG rasio 4:5 untuk Instagram/WhatsApp)."""
import io
import os
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1350
INK = (20, 17, 15)
GOLD = (212, 168, 87)
GOLD_SOFT = (232, 201, 138)
TEXT = (237, 228, 211)
TEXT_SOFT = (205, 192, 168)
MUTED = (168, 155, 134)

_DIR = os.path.dirname(os.path.abspath(__file__))


def _find_font(name: str) -> str:
    """Cari font di folder fonts/ atau langsung di folder yang sama dengan kartu.py."""
    for cand in (os.path.join(_DIR, "fonts", name), os.path.join(_DIR, name)):
        if os.path.exists(cand):
            return cand
    return os.path.join(_DIR, name)


REG = _find_font("CormorantGaramond.ttf")
ITA = _find_font("CormorantGaramond-Italic.ttf")

# True jika kedua file font ada. Jika tidak, kartu tetap dibuat dengan font cadangan.
FONTS_OK = os.path.exists(REG) and os.path.exists(ITA)


def _font(path, size, weight):
    try:
        f = ImageFont.truetype(path, size)
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass  # font statis: abaikan
        return f
    except Exception:
        return ImageFont.load_default(size)  # cadangan jika file font belum diunggah


# ------------------------------------------------------------------
# MENGAMBIL BAIT & TERJEMAHAN DARI JAWABAN MODEL
# ------------------------------------------------------------------
def _clean(block: str) -> str:
    lines = []
    for ln in block.splitlines():
        ln = re.sub(r"\*\*|__|`", "", ln)
        ln = re.sub(r"^\s*(>|[-*•]|\d+[.)])\s+", "", ln)
        ln = ln.replace("*", "").strip()
        lines.append(ln)
    text = "\n".join(lines).strip()
    return re.sub(r"\n{3,}", "\n\n", text)


def extract_card_parts(text: str):
    """Ambil (bait, terjemahan) dari jawaban bagian '### Gubahan' dan '### Terjemahan Balik'."""
    sections, title, buf = {}, None, []
    for ln in text.splitlines():
        m = re.match(r"^\s*#{1,6}\s*(.+?)\s*#*\s*$", ln)
        if m:
            if title is not None:
                sections[title] = "\n".join(buf)
            title, buf = m.group(1).strip().lower(), []
        elif title is not None:
            buf.append(ln)
    if title is not None:
        sections[title] = "\n".join(buf)

    verse = trans = ""
    for t, body in sections.items():
        if not verse and t.startswith("gubahan"):
            verse = _clean(body)
        elif not trans and t.startswith("terjemahan balik"):
            trans = _clean(body)
    return verse, trans


# ------------------------------------------------------------------
# MENGGAMBAR
# ------------------------------------------------------------------
def _diamond(d, cx, cy, r, fill):
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)


def _spaced_width(d, text, font, spacing):
    return sum(d.textlength(c, font=font) for c in text) + spacing * (len(text) - 1)


def _draw_spaced(d, cx, y, text, font, fill, spacing):
    x = cx - _spaced_width(d, text, font, spacing) / 2
    for c in text:
        d.text((x, y), c, font=font, fill=fill)
        x += d.textlength(c, font=font) + spacing


def _wrap(d, text, font, max_w):
    lines = []
    for para in text.splitlines():
        words, cur = para.split(), ""
        if not words:
            lines.append("")
            continue
        for w in words:
            trial = (cur + " " + w).strip()
            if d.textlength(trial, font=font) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def _divider(d, cy, half=150):
    d.line([(W / 2 - half, cy), (W / 2 - 18, cy)], fill=GOLD + (120,), width=2)
    d.line([(W / 2 + 18, cy), (W / 2 + half, cy)], fill=GOLD + (120,), width=2)
    _diamond(d, W / 2, cy, 7, GOLD)


def _fit(lines, max_lines):
    """Potong daftar baris jika terlalu panjang; tandai dengan elipsis."""
    if len(lines) <= max_lines:
        return lines
    cut = lines[:max_lines]
    cut[-1] = cut[-1].rstrip(" ,;.") + " …"
    return cut


def make_card(verse: str, translation: str, label: str = "", footer: str = "") -> bytes:
    # ---------- latar ----------
    img = Image.new("RGB", (W, H), INK)
    glow = Image.new("RGB", (W, H), INK)
    ImageDraw.Draw(glow).ellipse([W / 2 - 520, -380, W / 2 + 520, 420], fill=(66, 50, 24))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    img = Image.blend(img, glow, 0.9)
    d = ImageDraw.Draw(img, "RGBA")

    # ---------- bingkai ----------
    d.rounded_rectangle([44, 44, W - 44, H - 44], radius=30, outline=GOLD + (150,), width=3)
    d.rounded_rectangle([64, 64, W - 64, H - 64], radius=22, outline=GOLD + (70,), width=1)
    for cx, cy in [(64, 64), (W - 64, 64), (64, H - 64), (W - 64, H - 64)]:
        _diamond(d, cx, cy, 9, GOLD)

    # ---------- kepala ----------
    for dx in (-44, 0, 44):
        _diamond(d, W / 2 + dx, 128, 6, GOLD + (200,))
    _draw_spaced(d, W / 2, 158, "WASKITA SASTRA", _font(REG, 38, 600), GOLD_SOFT, 9)
    if label:
        lab_font = _font(REG, 24, 500)
        label = label.upper()
        while _spaced_width(d, label, lab_font, 5) > W - 200 and len(label) > 8:
            label = label[:-2].rstrip() + "…"
        _draw_spaced(d, W / 2, 214, label, lab_font, MUTED, 5)
    _divider(d, 282)

    # ---------- isi (bait + terjemahan), skala otomatis agar muat ----------
    top, bottom = 330, H - 190
    avail = bottom - top
    max_w = W - 2 * 130
    scale = 1.0
    while True:
        vf = _font(ITA, int(58 * scale), 500)
        tf = _font(REG, int(37 * scale), 500)
        lf = _font(REG, int(23 * scale), 600)
        v_lines = _wrap(d, verse, vf, max_w)
        t_lines = _wrap(d, translation, tf, max_w - 40) if translation else []
        v_lh, t_lh = int(vf.size * 1.28), int(tf.size * 1.42)
        extra = (70 + 56) if t_lines else 0
        total = len(v_lines) * v_lh + extra + len(t_lines) * t_lh
        if total <= avail or scale <= 0.55:
            break
        scale -= 0.04

    # masih terlalu panjang pada skala terkecil: potong dengan elipsis
    if total > avail:
        if t_lines:
            room_t = max(2, int((avail - len(v_lines) * v_lh - extra) / t_lh))
            t_lines = _fit(t_lines, room_t)
        total = len(v_lines) * v_lh + extra + len(t_lines) * t_lh
        if total > avail:
            v_lines = _fit(v_lines, max(1, int((avail - extra - len(t_lines) * t_lh) / v_lh)))
            total = len(v_lines) * v_lh + extra + len(t_lines) * t_lh

    y = top + max(0, (avail - total) / 2)
    for ln in v_lines:
        d.text((W / 2, y), ln, font=vf, fill=TEXT, anchor="ma")
        y += v_lh
    if t_lines:
        y += 28
        _divider(d, y, half=110)
        y += 42
        _draw_spaced(d, W / 2, y, "TERJEMAHAN", lf, MUTED, 5)
        y += 56
        for ln in t_lines:
            d.text((W / 2, y), ln, font=tf, fill=TEXT_SOFT, anchor="ma")
            y += t_lh

    # ---------- kaki ----------
    if footer:
        d.line([(W / 2 - 60, H - 150), (W / 2 + 60, H - 150)], fill=GOLD + (90,), width=1)
        d.text((W / 2, H - 128), footer, font=_font(REG, 28, 500), fill=MUTED, anchor="ma")

    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()
