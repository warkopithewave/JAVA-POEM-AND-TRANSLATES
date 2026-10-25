import streamlit as st
from google import genai

# ------------------------------------------------------------------
# KONFIGURASI HALAMAN
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Waskita Sastra - Kajian Klasik & Kawi",
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ------------------------------------------------------------------
# KLIEN GEMINI (API key dari Streamlit Secrets)
# ------------------------------------------------------------------
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("API Key belum dikonfigurasi di Streamlit Secrets. Harap atur terlebih dahulu di pengaturan aplikasi Anda.")
    client = None

MODELS = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash"]

# ------------------------------------------------------------------
# DATA CONTOH NASKAH
# ------------------------------------------------------------------
DEFAULT_TEXT = (
    "Surya candra lan kartika\n"
    "Jurang arga myang jaladri\n"
    "Yekti mawa pasang surut\n"
    "Ywa maneh ta amung sira\n"
    "Yen kalisa owah gingsir"
)

SAMPLES = [
    {
        "label": "🌀 Kalatidha",
        "title": "Serat Kalatidha",
        "author": "R.Ng. Ranggawarsita",
        "meta": "Pupuh Sinom · Jawa Baru, abad ke-19",
        "text": (
            "Amenangi jaman edan,\n"
            "ewuh aya ing pambudi,\n"
            "melu edan nora tahan,\n"
            "yen tan melu anglakoni,\n"
            "boya keduman melik,\n"
            "kaliren wekasanipun,\n"
            "ndilalah kersa Allah,\n"
            "begja-begjane kang lali,\n"
            "luwih begja kang eling lawan waspada."
        ),
    },
    {
        "label": "🪷 Sutasoma",
        "title": "Kakawin Sutasoma",
        "author": "Mpu Tantular",
        "meta": "Kakawin · Jawa Kuno, abad ke-14",
        "text": (
            "Rwāneka dhātu winuwus Buddha Wiśwa,\n"
            "Bhinnêki rakwa ring apan kena parwanosěn,\n"
            "Mangka ng Jinatwa kalawan Śiwatatwa tunggal,\n"
            "Bhinnêka tunggal ika tan hana dharma mangrwa."
        ),
    },
    {
        "label": "🔥 Wedhatama",
        "title": "Serat Wedhatama",
        "author": "K.G.P.A.A. Mangkunegara IV",
        "meta": "Pupuh Pangkur · Jawa Baru, abad ke-19",
        "text": (
            "Mingkar mingkuring angkara,\n"
            "akarana karenan mardi siwi,\n"
            "sinawung resmining kidung,\n"
            "sinuba sinukarta,\n"
            "mrih kretarta pakartining ngelmu luhung,\n"
            "kang tumrap neng tanah Jawa,\n"
            "agama ageming aji."
        ),
    },
]

# ------------------------------------------------------------------
# STATE & CALLBACK
# ------------------------------------------------------------------
if "input_text" not in st.session_state:
    st.session_state.input_text = DEFAULT_TEXT


def set_text(text: str):
    st.session_state.input_text = text


# ------------------------------------------------------------------
# CSS: TEMA "LONTAR EMAS"
# ------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500&family=Inter:wght@400;500;600&family=Noto+Sans+Javanese:wght@400;700&display=swap');

:root {
  --gold: #D4A857;
  --gold-soft: #E8C98A;
  --ink: #14110F;
  --panel: #1E1915;
  --line: #3A3027;
  --text: #EDE4D3;
  --muted: #A89B86;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
  background:
    radial-gradient(900px 500px at 50% -8%, rgba(212,168,87,0.16) 0%, transparent 70%),
    radial-gradient(700px 400px at 100% 100%, rgba(111,165,143,0.08) 0%, transparent 70%),
    var(--ink);
  color: var(--text);
}

#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.2rem; max-width: 760px; }

/* ---------- HERO ---------- */
.hero {
  text-align: center;
  padding: 2rem 1rem 1.4rem;
  margin-bottom: 1.2rem;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: linear-gradient(160deg, rgba(212,168,87,0.12), rgba(212,168,87,0.02) 55%, transparent);
  box-shadow: 0 10px 40px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04);
}
.hero .aksara {
  font-family: 'Noto Sans Javanese', serif;
  font-size: 1.45rem;
  color: var(--gold);
  letter-spacing: 0.08em;
  opacity: 0.95;
}
.hero .title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 3rem;
  font-weight: 700;
  line-height: 1.1;
  margin: 0.15rem 0 0.1rem;
  background: linear-gradient(90deg, #F6E3B4, #D4A857 50%, #F6E3B4);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.hero .subtitle {
  color: var(--muted);
  font-size: 0.92rem;
  max-width: 480px;
  margin: 0.3rem auto 0.9rem;
}
.orn { color: var(--gold); text-align: center; letter-spacing: 0.7em; opacity: 0.7; margin: 0.4rem 0; font-size: 0.8rem; }
.pills span {
  display: inline-block;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 0.22rem 0.8rem;
  margin: 0.15rem;
  font-size: 0.76rem;
  color: var(--gold-soft);
  background: rgba(212,168,87,0.07);
}

/* ---------- TAB ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 0.3rem; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { color: var(--muted); font-weight: 500; padding: 0.6rem 0.9rem; }
.stTabs [aria-selected="true"] { color: var(--gold) !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--gold) !important; }

/* ---------- SECTION LABEL ---------- */
.section-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.55rem;
  font-weight: 600;
  color: var(--gold-soft);
  margin: 0.8rem 0 0.2rem;
}
.hint { color: var(--muted); font-size: 0.82rem; margin-bottom: 0.4rem; }

/* ---------- INPUT ---------- */
.stTextArea label p, .stRadio label p { color: var(--muted) !important; font-size: 0.82rem !important; }
.stTextArea [data-baseweb="textarea"] {
  background: #17130F !important;
  border: 1px solid var(--line) !important;
  border-radius: 14px !important;
}
.stTextArea [data-baseweb="textarea"]:focus-within {
  border-color: var(--gold) !important;
  box-shadow: 0 0 0 3px rgba(212,168,87,0.18) !important;
}
.stTextArea textarea {
  background: transparent !important;
  color: var(--text) !important;
  font-family: 'Cormorant Garamond', serif !important;
  font-size: 1.22rem !important;
  line-height: 1.6 !important;
}

/* ---------- TOMBOL ---------- */
.stButton > button, .stDownloadButton > button {
  width: 100%;
  border-radius: 12px;
  font-weight: 600;
  transition: all .18s ease;
}
/* tombol sekunder (chip contoh) */
.stButton > button[kind="secondary"],
[data-testid="stBaseButton-secondary"] {
  background: rgba(212,168,87,0.07);
  color: var(--gold-soft);
  border: 1px solid var(--line);
  font-size: 0.85rem;
}
.stButton > button[kind="secondary"]:hover,
[data-testid="stBaseButton-secondary"]:hover {
  border-color: var(--gold);
  color: var(--gold);
  background: rgba(212,168,87,0.14);
  transform: translateY(-1px);
}
/* tombol utama (aksi) */
.stButton > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, #E8C98A 0%, #D4A857 45%, #B98A3A 100%);
  color: #1A130A;
  border: none;
  padding: 0.7rem 1rem;
  font-size: 1rem;
  letter-spacing: 0.02em;
  box-shadow: 0 6px 20px rgba(212,168,87,0.28);
}
.stButton > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
  filter: brightness(1.08);
  transform: translateY(-1px);
  box-shadow: 0 10px 26px rgba(212,168,87,0.38);
  color: #1A130A;
}
.stDownloadButton > button {
  background: transparent;
  color: var(--gold-soft);
  border: 1px solid var(--gold);
}
.stDownloadButton > button:hover { background: rgba(212,168,87,0.12); color: var(--gold); }

/* ---------- KARTU HASIL ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: linear-gradient(180deg, #1F1A15, #19150F);
  border: 1px solid var(--line) !important;
  border-left: 4px solid var(--gold) !important;
  border-radius: 14px !important;
  box-shadow: 0 8px 30px rgba(0,0,0,0.35);
}
[data-testid="stVerticalBlockBorderWrapper"] h1,
[data-testid="stVerticalBlockBorderWrapper"] h2,
[data-testid="stVerticalBlockBorderWrapper"] h3,
[data-testid="stVerticalBlockBorderWrapper"] h4 {
  font-family: 'Cormorant Garamond', serif;
  color: var(--gold-soft);
  font-size: 1.45rem;
  font-weight: 700;
  margin-top: 1rem;
  padding-bottom: 0.2rem;
  border-bottom: 1px solid var(--line);
}
[data-testid="stVerticalBlockBorderWrapper"] p,
[data-testid="stVerticalBlockBorderWrapper"] li { color: var(--text); line-height: 1.7; }
[data-testid="stVerticalBlockBorderWrapper"] strong { color: var(--gold-soft); }
[data-testid="stVerticalBlockBorderWrapper"] em { color: #CFE3D8; }

/* ---------- EXPANDER (pustaka) ---------- */
[data-testid="stExpander"] {
  border: 1px solid var(--line) !important;
  border-radius: 14px !important;
  background: rgba(30,25,21,0.7);
}
[data-testid="stExpander"] summary p { font-family: 'Cormorant Garamond', serif; font-size: 1.2rem; color: var(--gold-soft); font-weight: 600; }

.excerpt {
  font-family: 'Cormorant Garamond', serif;
  font-style: italic;
  font-size: 1.15rem;
  line-height: 1.7;
  color: var(--text);
  border-left: 3px solid var(--gold);
  padding: 0.2rem 0 0.2rem 1rem;
  margin: 0.4rem 0 0.8rem;
  white-space: pre-line;
}
.meta { color: var(--muted); font-size: 0.8rem; }
.disclaimer { color: var(--muted); font-size: 0.76rem; text-align: center; margin-top: 1rem; }
hr { border-color: var(--line); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------
# HERO
# ------------------------------------------------------------------
HERO = """
<div class="hero">
<div class="aksara">ꦮꦱ꧀ꦏꦶꦠ ꦱꦱ꧀ꦠꦿ</div>
<div class="title">Waskita Sastra</div>
<div class="subtitle">Menyingkap makna naskah Jawa Kuno, Kawi, dan sastra Nusantara dengan bantuan kecerdasan buatan.</div>
<div class="orn">✦ ✦ ✦</div>
<div class="pills">
<span>📖 Terjemahan Bebas</span>
<span>🔎 Bedah Kosakata</span>
<span>🌌 Filosofi &amp; Kosmologi</span>
</div>
</div>
"""
st.markdown(HERO, unsafe_allow_html=True)

# ------------------------------------------------------------------
# TAB
# ------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🏠 Telaah", "📚 Pustaka", "ℹ️ Tentang"])

# ================= TAB 1: TELAAH =================
with tab1:
    st.markdown('<div class="section-title">Masukkan Teks / Bait Sastra</div>', unsafe_allow_html=True)
    st.markdown('<div class="hint">Ketik, tempel, atau coba salah satu naskah contoh di bawah.</div>', unsafe_allow_html=True)

    chip_cols = st.columns(len(SAMPLES))
    for i, s in enumerate(SAMPLES):
        with chip_cols[i]:
            st.button(s["label"], key=f"chip_{i}", on_click=set_text, args=(s["text"],))

    user_input = st.text_area(
        "Teks Jawa Kuno / Kawi / bait sastra:",
        key="input_text",
        height=190,
        max_chars=3000,
    )

    depth = st.radio(
        "Kedalaman analisis",
        ["Ringkas", "Mendalam"],
        index=1,
        horizontal=True,
    )

    if st.button("✨ Terjemahkan & Bedah Makna", type="primary"):
        if not user_input.strip():
            st.warning("Mohon masukkan teks terlebih dahulu.")
        elif client is None:
            st.error("API Key belum dikonfigurasi.")
        else:
            if depth == "Ringkas":
                format_rule = (
                    "Berikan jawaban RINGKAS (sekitar 150-250 kata) dengan tiga bagian:\n"
                    "### Terjemahan Bebas\n### Kosakata Penting\n### Makna & Filosofi"
                )
            else:
                format_rule = (
                    "Berikan jawaban MENDALAM dengan tiga bagian:\n"
                    "### Terjemahan Bebas (Bahasa Indonesia)\nTerjemahan utuh yang puitis namun akurat.\n"
                    "### Bedah Kosakata & Analisis Per Baris\nUraikan kata penting (kawi/kuna) beserta arti harfiahnya.\n"
                    "### Nilai Filosofi & Kosmologi\nMakna mendalam atau sasmita di balik teks."
                )

            prompt = f"""
Bertindaklah sebagai ahli filologi, sastra Jawa Kuno, dan Kawi Nusantara.
Analisis teks sastra berikut:
\"\"\"
{user_input}
\"\"\"

{format_rule}

Gunakan judul bagian dengan format "###" (jangan "#" atau "##").
Jika ada kata atau bagian yang Anda tidak yakin, katakan terus terang.
"""

            analysis_result, used_model, last_error = None, None, None
            with st.spinner("Membaca lontar... menimbang kata dan makna..."):
                for model_name in MODELS:
                    try:
                        response = client.models.generate_content(
                            model=model_name, contents=prompt
                        )
                        analysis_result = response.text
                        used_model = model_name
                        break
                    except Exception as e:
                        last_error = e  # coba model berikutnya

            if analysis_result:
                st.session_state["result"] = {
                    "text": analysis_result,
                    "model": used_model,
                    "source": user_input,
                }
            else:
                st.session_state.pop("result", None)
                st.error(f"Gagal menghubungi Gemini: {last_error}")

    # ---- Tampilan hasil (tetap muncul setelah tombol unduh ditekan) ----
    res = st.session_state.get("result")
    if res:
        st.markdown('<div class="orn">✦ ✦ ✦</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📖 Hasil Telaah</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(res["text"])
        st.caption(f"Dianalisis dengan {res['model']}")

        export_md = (
            "# Waskita Sastra - Hasil Telaah\n\n"
            "## Teks Asli\n\n"
            + "\n".join("> " + line for line in res["source"].splitlines())
            + "\n\n---\n\n"
            + res["text"]
        )
        st.download_button(
            "⬇ Simpan hasil (.md)",
            data=export_md,
            file_name="waskita-sastra-hasil.md",
            mime="text/markdown",
        )
        st.markdown(
            '<div class="disclaimer">Hasil AI dapat keliru, terutama pada teks Kawi/Jawa Kuno. '
            "Verifikasi dengan kamus (mis. Old Javanese-English Dictionary karya Zoetmulder) atau ahli filologi.</div>",
            unsafe_allow_html=True,
        )

# ================= TAB 2: PUSTAKA =================
with tab2:
    st.markdown('<div class="section-title">Pustaka Naskah Klasik</div>', unsafe_allow_html=True)
    st.markdown('<div class="hint">Pilih naskah, lalu tekan "Muat ke Telaah" dan kembali ke tab Telaah.</div>', unsafe_allow_html=True)

    for i, s in enumerate(SAMPLES):
        with st.expander(f"{s['title']}  ·  {s['author']}"):
            st.markdown(f'<div class="meta">{s["meta"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="excerpt">{s["text"]}</div>', unsafe_allow_html=True)
            if st.button("Muat ke Telaah", key=f"load_{i}", on_click=set_text, args=(s["text"],)):
                st.toast("Teks dimuat. Buka tab Telaah untuk menganalisis.", icon="📜")

# ================= TAB 3: TENTANG =================
with tab3:
    st.markdown('<div class="section-title">Tentang Waskita Sastra</div>', unsafe_allow_html=True)
    st.write(
        "Waskita Sastra membantu peneliti, penggiat budaya, dan masyarakat umum "
        "mengkaji teks sastra Nusantara: menerjemahkan, membedah kosakata, dan menggali "
        "lapisan makna filosofisnya."
    )
    st.markdown('<div class="orn">✦ ✦ ✦</div>', unsafe_allow_html=True)
    st.caption("Dibangun dengan Python, Streamlit, & Gemini AI · Mobile Optimized")
