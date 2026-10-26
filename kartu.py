"""Pembuat kartu bagikan Waskita Sastra (PNG rasio 4:5 untuk Instagram/WhatsApp).

Teks panjang dipecah otomatis menjadi beberapa kartu agar huruf tetap besar dan mudah dibaca.
"""
import io
import os
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1350

THEMES = {
    "terang": {  # krem lontar: kontras tinggi, nyaman dibaca
        "base": (238, 227, 203),
        "glow": (255, 251, 238),
        "gold": (160, 114, 34),
        "title": (112, 76, 18),
        "text": (40, 30, 20),
        "soft": (64, 50, 36),
        "muted": (104, 88, 66),
    },
    "gelap": {  # gelap hangat, sudah dicerahkan
        "base": (36, 29, 22),
        "glow": (96, 73, 38),
        "gold": (214, 170, 90),
        "title": (242, 216, 154),
        "text": (250, 243, 228),
        "soft": (230, 218, 194),
        "muted": (194, 180, 156),
    },
}

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

# Ukuran dasar (px) dan batas pengecilan terkecil agar tetap terbaca di ponsel
VERSE_PX, TRANS_PX, LABEL_PX = 60, 40, 24
MIN_SCALE_PACK = 0.80   # saat memecah ke beberapa kartu
MIN_SCALE_ONE = 0.62    # jika satu bagian saja sudah terlalu panjang


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
_HR = re.compile(r"^\s*([-*_=]\s*){3,}$")


def _clean(block: str) -> str:
    lines = []
    for ln in block.splitlines():
        if _HR.match(ln):          # buang garis pemisah markdown (---, ***, ___)
            lines.append("")
            continue
        ln = re.sub(r"\*\*|__|`", "", ln)
        ln = re.sub(r"^\s*(>|[-*•]|\d+[.)])\s+", "", ln)
        ln = ln.replace("*", "").strip()
        lines.append(ln)
    text = "\n".join(lines).strip()
    return re.sub(r"\n{3,}", "\n\n", text)


def extract_card_parts(text: str):
    """Ambil (bait, terjemahan) dari bagian '### Gubahan' dan '### Terjemahan Balik'."""
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
    """Bungkus teks; paragraf dipisah baris kosong ('')."""
    lines = []
    for para in text.splitlines():
        words, cur = para.split(), ""
        if not words:
            if lines and lines[-1] != "":
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
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def _block_height(lines, lh):
    return sum(lh * 0.5 if ln == "" else lh for ln in lines)


def _divider(d, cy, c, half=150):
    d.line([(W / 2 - half, cy), (W / 2 - 18, cy)], fill=c["gold"] + (170,), width=2)
    d.line([(W / 2 + 18, cy), (W / 2 + half, cy)], fill=c["gold"] + (170,), width=2)
    _diamond(d, W / 2, cy, 7, c["gold"])


def _fit_lines(lines, max_h, lh):
    """Potong baris yang melebihi tinggi; tandai dengan elipsis."""
    out, h = [], 0
    for ln in lines:
        step = lh * 0.5 if ln == "" else lh
        if h + step > max_h:
            break
        out.append(ln)
        h += step
    if len(out) < len(lines) and out:
        out[-1] = out[-1].rstrip(" ,;.") + " …"
    return out


_MEASURE = ImageDraw.Draw(Image.new("RGB", (4, 4)))

TOP, BOTTOM = 330, H - 205
AVAIL = BOTTOM - TOP
MAX_W = W - 2 * 120


def _layout(verse, trans, scale):
    vf = _font(ITA, int(VERSE_PX * scale), 500)
    tf = _font(REG, int(TRANS_PX * scale), 500)
    lf = _font(REG, int(LABEL_PX * scale), 600)
    v_lines = _wrap(_MEASURE, verse, vf, MAX_W)
    t_lines = _wrap(_MEASURE, trans, tf, MAX_W - 20) if trans else []
    v_lh, t_lh = vf.size * 1.28, tf.size * 1.42
    extra = (70 + 56) if t_lines else 0
    total = _block_height(v_lines, v_lh) + extra + _block_height(t_lines, t_lh)
    return {"vf": vf, "tf": tf, "lf": lf, "v": v_lines, "t": t_lines,
            "v_lh": v_lh, "t_lh": t_lh, "extra": extra, "total": total}


def _fits(verse, trans, scale=MIN_SCALE_PACK):
    return _layout(verse, trans, scale)["total"] <= AVAIL


def _paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


def _split_pages(verse, trans):
    """Bagi isi menjadi beberapa halaman; paragraf bait dipasangkan dengan paragraf terjemahan."""
    vp, tp = _paragraphs(verse), _paragraphs(trans) if trans else []
    if trans and len(vp) == len(tp) and len(vp) > 1:
        units = list(zip(vp, tp))
    elif not trans and len(vp) > 1:
        units = [(p, "") for p in vp]
    else:
        return [(verse.strip(), trans.strip())]

    pages, cur_v, cur_t = [], [], []
    for v, t in units:
        nv, nt = "\n\n".join(cur_v + [v]), "\n\n".join(cur_t + [t]).strip()
        if not cur_v or _fits(nv, nt):
            cur_v.append(v)
            cur_t.append(t)
        else:
            pages.append(("\n\n".join(cur_v), "\n\n".join(cur_t).strip()))
            cur_v, cur_t = [v], [t]
    if cur_v:
        pages.append(("\n\n".join(cur_v), "\n\n".join(cur_t).strip()))
    return pages


def _render(verse, trans, label, footer, c, page_no=1, page_total=1):
    # ---------- latar ----------
    img = Image.new("RGB", (W, H), c["base"])
    glow = Image.new("RGB", (W, H), c["base"])
    ImageDraw.Draw(glow).ellipse([W / 2 - 560, -360, W / 2 + 560, 520], fill=c["glow"])
    glow = glow.filter(ImageFilter.GaussianBlur(170))
    img = Image.blend(img, glow, 0.95)
    d = ImageDraw.Draw(img, "RGBA")

    # ---------- bingkai ----------
    d.rounded_rectangle([44, 44, W - 44, H - 44], radius=30, outline=c["gold"] + (230,), width=3)
    d.rounded_rectangle([64, 64, W - 64, H - 64], radius=22, outline=c["gold"] + (110,), width=1)
    for cx, cy in [(64, 64), (W - 64, 64), (64, H - 64), (W - 64, H - 64)]:
        _diamond(d, cx, cy, 9, c["gold"])

    # ---------- kepala ----------
    for dx in (-44, 0, 44):
        _diamond(d, W / 2 + dx, 128, 6, c["gold"])
    _draw_spaced(d, W / 2, 158, "WASKITA SASTRA", _font(REG, 40, 650), c["title"], 9)
    if label:
        lab_font = _font(REG, 26, 600)
        label = label.upper()
        while _spaced_width(d, label, lab_font, 5) > W - 200 and len(label) > 8:
            label = label[:-2].rstrip() + "…"
        _draw_spaced(d, W / 2, 214, label, lab_font, c["muted"], 5)
    _divider(d, 284, c)

    # ---------- isi: skala terbesar yang muat ----------
    scale = 1.0
    lay = _layout(verse, trans, scale)
    floor = MIN_SCALE_PACK if page_total > 1 else MIN_SCALE_ONE
    while lay["total"] > AVAIL and scale > floor:
        scale = round(scale - 0.04, 2)
        lay = _layout(verse, trans, scale)
    if lay["total"] > AVAIL:  # masih terlalu panjang: potong dengan elipsis
        scale = MIN_SCALE_ONE
        lay = _layout(verse, trans, scale)
        if lay["t"]:
            room_t = max(AVAIL * 0.25, AVAIL - _block_height(lay["v"], lay["v_lh"]) - lay["extra"])
            lay["t"] = _fit_lines(lay["t"], room_t, lay["t_lh"])
        total = _block_height(lay["v"], lay["v_lh"]) + lay["extra"] + _block_height(lay["t"], lay["t_lh"])
        if total > AVAIL:
            room_v = AVAIL - lay["extra"] - _block_height(lay["t"], lay["t_lh"])
            lay["v"] = _fit_lines(lay["v"], max(room_v, lay["v_lh"]), lay["v_lh"])
        lay["total"] = _block_height(lay["v"], lay["v_lh"]) + lay["extra"] + _block_height(lay["t"], lay["t_lh"])

    y = TOP + max(0, (AVAIL - lay["total"]) / 2)
    for ln in lay["v"]:
        if ln == "":
            y += lay["v_lh"] * 0.5
            continue
        d.text((W / 2, y), ln, font=lay["vf"], fill=c["text"], anchor="ma")
        y += lay["v_lh"]
    if lay["t"]:
        y += 26
        _divider(d, y, c, half=110)
        y += 40
        _draw_spaced(d, W / 2, y, "TERJEMAHAN", lay["lf"], c["muted"], 5)
        y += 58
        for ln in lay["t"]:
            if ln == "":
                y += lay["t_lh"] * 0.5
                continue
            d.text((W / 2, y), ln, font=lay["tf"], fill=c["soft"], anchor="ma")
            y += lay["t_lh"]

    # ---------- kaki ----------
    if page_total > 1:
        d.text((W / 2, H - 196), f"{page_no} / {page_total}", font=_font(REG, 28, 600), fill=c["muted"], anchor="ma")
    if footer:
        d.line([(W / 2 - 60, H - 150), (W / 2 + 60, H - 150)], fill=c["gold"] + (150,), width=1)
        d.text((W / 2, H - 128), footer, font=_font(REG, 30, 600), fill=c["muted"], anchor="ma")

    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def make_cards(verse: str, translation: str = "", label: str = "", footer: str = "", theme: str = "terang"):
    """Kembalikan daftar PNG (bytes). Teks panjang dipecah menjadi beberapa kartu."""
    c = THEMES.get(theme, THEMES["terang"])
    pages = _split_pages(verse, translation)
    return [_render(v, t, label, footer, c, i + 1, len(pages)) for i, (v, t) in enumerate(pages)]


def make_card(verse: str, translation: str = "", label: str = "", footer: str = "", theme: str = "terang") -> bytes:
    """Kartu tunggal (kartu pertama)."""
    return make_cards(verse, translation, label, footer, theme)[0]
