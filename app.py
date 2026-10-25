import streamlit as st
from google import genai

# Konfigurasi Halaman & Tema Estetik
st.set_page_config(
    page_title="Waskita Sastra - Kajian Klasik & Kawi",
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Mengambil API key secara aman dari Streamlit Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error("API Key belum dikonfigurasi di Streamlit Secrets. Harap atur terlebih dahulu di pengaturan aplikasi Anda.")
    client = None

# Styling CSS Kustom untuk Tampilan Mobile-Friendly & Estetik Muted Palette
st.markdown(
    """
    <style>
    .main {
        background-color: #F7F5F0;
        color: #383531;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stButton>button {
        background-color: #6A7B68;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1rem;
        font-weight: 600;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #556353;
        color: white;
    }
    .stTextArea textarea {
        background-color: #FFFFFF;
        color: #383531;
        border: 1px solid #D3CEC4;
        border-radius: 8px;
    }
    h1, h2, h3, h4 {
        color: #2C352D;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Header Aplikasi
st.markdown("### 📜 Waskita Sastra")
st.caption(
    "Kajian Klasik, Kawi, & Sastra Nusantara Berbasis Kecerdasan Buatan"
)

# Menu Navigasi Tab Ala Mobile App
tab1, tab2, tab3 = st.tabs(["🏠 Beranda & Terjemah", "📚 Contoh Naskah", "ℹ️ Tentang"])

with tab1:
    st.markdown("#### Masukkan Teks / Bait Sastra")

    # Kotak Input Teks Bebas
    user_input = st.text_area(
        "Ketik atau tempel teks Jawa Kuno / Kawi / bait sastra di sini:",
        value="Surya candra lan kartika\nJurang arga myang jaladri\nYekti mawa pasang surut\nYwa maneh ta amung sira\nYen kalisa owah gingsir",
        height=140,
    )

    if st.button("Terjemahkan & Bedah Makna"):
        if not user_input.strip():
            st.warning("Mohon masukkan teks terlebih dahulu.")
        elif client is None:
            st.error("API Key belum dikonfigurasi.")
        else:
            prompt = f"""
            Bertindaklah sebagai ahli filologi, sastra Jawa Kuno, dan Kawi Nusantara.
            Analisis teks sastra berikut secara mendalam:
            "{user_input}"

            Berikan output dalam format struktur berikut:
            1. **Terjemahan Bebas (Bahasa Indonesia):** Terjemahan utuh yang puitis namun akurat.
            2. **Bedah Kosakata & Analisis Per Baris:** Uraikan kata-kata penting (misal: kawi/kuna) beserta arti harfiahnya.
            3. **Nilai Filosofi & Kosmologi:** Penjelasan makna mendalam atau sasmita di balik teks tersebut.
            """

            MODELS = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash"]
            analysis_result, last_error = None, None

            with st.spinner("Menganalisis struktur bahasa, leksikon, dan filosofi..."):
                for model_name in MODELS:
                    try:
                        response = client.models.generate_content(
                            model=model_name, contents=prompt
                        )
                        analysis_result = response.text
                        break
                    except Exception as e:
                        last_error = e  # coba model berikutnya

            if analysis_result:
                st.markdown("---")
                st.markdown("### 📖 Hasil Analisis & Terjemahan")
                with st.container(border=True):
                    st.markdown(analysis_result)
            else:
                st.error(f"Gagal menghubungi Gemini: {last_error}")

with tab2:
    st.markdown("#### 📚 Pustaka Naskah Klasik Referensi")
    st.markdown(
        """
    Anda bisa menyalin teks berikut untuk diuji di tab Beranda:
    * **Serat Kalatidha (R.Ng. Ranggawarsita):**
      > *Amenangi jaman edan, sewu woro-woro keliru, melu edan nora tahan, yen tan melu kampuh wetu...*
    * **Dewaruci (Sunan Kalijaga):**
      > *Hana ketug nikanang samudra, mangalun-alun tanpa pegat...*
    """
    )

with tab3:
    st.markdown("#### ℹ️ Tentang Sistem Waskita Sastra")
    st.write(
        "Aplikasi ini menggabungkan antarmuka seluler yang ringan dengan mesin pemrosesan bahasa alami untuk membantu peneliti, penggiat budaya, dan masyarakat umum dalam mengkaji teks sastra Nusantara secara mendalam dan interaktif."
    )
    st.caption("Dibangun dengan Python, Streamlit, & Gemini AI • Mobile Optimized")
