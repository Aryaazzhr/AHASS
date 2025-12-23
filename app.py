import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# ==================== CUSTOM CSS - Gaya Medium.com + Glassmorphism Ringan ====================
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 24px;
    }
    .title {
        font-size: 2.8rem;
        font-weight: 700;
        color: #111111;
        text-align: center;
        margin-bottom: 8px;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #555555;
        text-align: center;
        margin-bottom: 40px;
    }
    h2, h3 {
        color: #111111;
        font-weight: 600;
    }
    .metric-label {
        font-size: 1rem;
        color: #666666;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FF4B4B;
    }
</style>
""", unsafe_allow_html=True)

# ==================== KONFIGURASI HALAMAN ====================
st.set_page_config(page_title="Dashboard Bengkel Pro", layout="wide")

# ==================== HEADER ====================
st.markdown('<div class="title">🛠️ Monitoring & Insight Pelanggan Bengkel</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Data real-time dari database pelanggan Honda • Update otomatis</div>', unsafe_allow_html=True)

# ==================== KONEKSI GOOGLE SHEETS ====================
url = "https://docs.google.com/spreadsheets/d/1wGEojxqModICUSxRIgCONuiLRIyrEhMGRDWsmxWXjng/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(spreadsheet=url)
    df.columns = df.columns.str.strip()

    # Konversi tanggal
    df['Tgl Service Terakhir'] = pd.to_datetime(df['Tgl Service Terakhir'], errors='coerce')
    df['Tahun Rakit'] = pd.to_numeric(df['Tahun Rakit'], errors='coerce')

    # Hitung umur motor (tahun)
    current_year = datetime.now().year
    df['Umur Motor (Tahun)'] = current_year - df['Tahun Rakit']

    # Logika filter servis
    hari_ini = datetime.now()
    batas_servis = hari_ini - timedelta(days=60)
    perlu_servis = df[df['Tgl Service Terakhir'] <= batas_servis].copy()
    perlu_servis['Terlambat (Hari)'] = (hari_ini - perlu_servis['Tgl Service Terakhir']).dt.days

    # ==================== METRIK UTAMA (CARD STYLE) ====================
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Pelanggan", f"{len(df):,}")
        col2.metric("Perlu Servis (>60 Hari)", f"{len(perlu_servis):,}", 
                    delta=f"{len(perlu_servis)/len(df)*100:.1f}%" if len(df)>0 else "0%")
        col3.metric("Rata-rata Keterlambatan", 
                    f"{int(perlu_servis['Terlambat (Hari)'].mean()) if not perlu_servis.empty else 0} Hari")
        col4.metric("Servis Bulan Ini", len(df[df['Tgl Service Terakhir'].dt.month == hari_ini.month]))
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ==================== RINGKASAN STATISTIK DALAM TABEL ====================
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📈 Ringkasan Statistik Database Pelanggan")

        stats_data = {
            "Metrik": [
                "Total Pelanggan Terdaftar",
                "Model Motor Terbanyak",
                "Kecamatan Dominan",
                "Rata-rata Umur Motor",
                "Frekuensi Servis Tertinggi",
                "Tahun Rakit Terbanyak"
            ],
            "Nilai": [
                f"{len(df):,}",
                df['Market Name'].mode()[0] if not df['Market Name'].empty else "-",
                df['Kecamatan'].mode()[0] if 'Kecamatan' in df.columns else "-",
                f"{df['Umur Motor (Tahun)'].mean():.1f} tahun" if not df['Umur Motor (Tahun)'].isnull().all() else "-",
                f"{df['Freq of Visit'].max()} kali" if 'Freq of Visit' in df.columns else "-",
                f"{int(df['Tahun Rakit'].mode()[0])}" if not df['Tahun Rakit'].empty else "-"
            ]
        }
        stats_df = pd.DataFrame(stats_data)
        st.table(stats_df)
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ==================== VISUALISASI INSIGHT ====================
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📊 Visualisasi Insight Pelanggan")

        c1, c2 = st.columns(2)

        with c1:
            # Pie Chart - Model Motor
            top_models = df['Market Name'].value_counts().head(8)
            fig_pie = px.pie(values=top_models.values, names=top_models.index,
                             title="Distribusi Model Motor (Top 8)",
                             color_discrete_sequence=px.colors.sequential.Reds_r)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

            # Bar Chart - Kecamatan
            if 'Kecamatan' in df.columns:
                top_kec = df['Kecamatan'].value_counts().head(10)
                fig_bar_kec = px.bar(x=top_kec.index, y=top_kec.values,
                                     labels={'x': 'Kecamatan', 'y': 'Jumlah Pelanggan'},
                                     title="Top 10 Kecamatan Pelanggan",
                                     color=top_kec.values,
                                     color_continuous_scale='Reds')
                st.plotly_chart(fig_bar_kec, use_container_width=True)

        with c2:
            # Bar Chart - Tren Bulanan
            df_trend = df.resample('M', on='Tgl Service Terakhir').size().reset_index(name='Jumlah Servis')
            fig_trend = px.area(df_trend, x='Tgl Service Terakhir', y='Jumlah Servis',
                                title="Tren Kedatangan Servis (Bulanan)",
                                color_discrete_sequence=['#FF4B4B'])
            st.plotly_chart(fig_trend, use_container_width=True)

            # Histogram Tahun Rakit
            fig_hist = px.histogram(df, x='Tahun Rakit', nbins=15,
                                    title="Distribusi Tahun Rakit Motor",
                                    color_discrete_sequence=['#FF6B6B'])
            fig_hist.update_layout(bargap=0.2)
            st.plotly_chart(fig_hist, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ==================== DAFTAR FOLLOW UP WHATSAPP ====================
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📲 Daftar Pelanggan yang Perlu Dihubungi (Waktunya Servis)")

        if not perlu_servis.empty:
            def create_wa_link(row):
                pesan = f"Halo {row['Nama']}, motor {row.get('Market Name', 'Anda')} ({row['Nopol']}) sudah waktunya servis kembali. Terakhir servis {row['Tgl Service Terakhir'].strftime('%d %b %Y')}. Yuk agendakan ke bengkel secepatnya! 🛵"
                nomor = str(row['No HP1']).replace('.0', '').strip()
                if nomor.startswith('0'):
                    nomor = '62' + nomor[1:]
                elif not nomor.startswith('62'):
                    nomor = '62' + nomor
                return f"https://wa.me/{nomor}?text={pesan.replace(' ', '%20')}"

            perlu_servis['WhatsApp'] = perlu_servis.apply(create_wa_link, axis=1)

            display_df = perlu_servis[['Nama', 'Nopol', 'Market Name', 'Tgl Service Terakhir', 
                                       'Terlambat (Hari)', 'WhatsApp']].sort_values(by="Terlambat (Hari)", ascending=False)

            st.write("Klik tombol **Kirim Pesan 🟢** untuk langsung chat via WhatsApp:")

            st.data_editor(
                display_df,
                column_config={
                    "WhatsApp": st.column_config.LinkColumn(
                        "Hubungi Sekarang",
                        display_text="Kirim Pesan 🟢",
                        width="medium"
                    ),
                    "Tgl Service Terakhir": st.column_config.DateColumn("Terakhir Servis"),
                    "Terlambat (Hari)": st.column_config.NumberColumn("Keterlambatan", format="%d hari")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.success("🎉 **Luar biasa!** Semua pelanggan sudah rutin servis dalam 60 hari terakhir.")
        
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"⚠️ Terjadi kesalahan saat memuat data: {e}")
    st.info("Pastikan Google Sheet dapat diakses publik (share link dengan 'Anyone with the link') dan nama kolom sesuai.")
