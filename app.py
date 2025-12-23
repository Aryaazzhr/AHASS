import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# ==================== CUSTOM CSS - Glassmorphism Premium Dark ====================
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #0f0f0f, #1a1a1a);
        color: #ffffff;
    }
    .card {
        background: rgba(30, 30, 40, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        margin-bottom: 24px;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(100, 50, 200, 0.3), rgba(50, 150, 200, 0.3));
        backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    .metric-label {
        font-size: 1rem;
        color: #aaaaaa;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 2.8rem;
        font-weight: 700;
        color: #ffffff;
    }
    .metric-delta {
        font-size: 1rem;
        color: #4ade80;
        margin-top: 8px;
    }
    .title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #ff4b4b, #ff8a8a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 8px;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #bbbbbb;
        text-align: center;
        margin-bottom: 40px;
    }
    h2, h3 {
        color: #ffffff;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ==================== KONFIGURASI ====================
st.set_page_config(page_title="Bengkel Pro Dashboard", layout="wide")

# ==================== HEADER ====================
st.markdown('<div class="title">🛠️ Monitoring & Insight Pelanggan Bengkel</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Data real-time dari database pelanggan Honda • Update otomatis</div>', unsafe_allow_html=True)

# ==================== KONEKSI DATA ====================
url = "https://docs.google.com/spreadsheets/d/1wGEojxqModICUSxRIgCONuiLRIyrEhMGRDWsmxWXjng/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(spreadsheet=url)
    df.columns = df.columns.str.strip()
    df['Tgl Service Terakhir'] = pd.to_datetime(df['Tgl Service Terakhir'], errors='coerce')
    df['Tahun Rakit'] = pd.to_numeric(df['Tahun Rakit'], errors='coerce')

    hari_ini = datetime.now()
    batas_servis = hari_ini - timedelta(days=60)
    perlu_servis = df[df['Tgl Service Terakhir'] <= batas_servis].copy()
    perlu_servis['Terlambat (Hari)'] = (hari_ini - perlu_servis['Tgl Service Terakhir']).dt.days

    # ==================== METRIC CARDS (Glass Style) ====================
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        total_pelanggan = len(df)
        jumlah_perlu_servis = len(perlu_servis)
        persen_perlu = jumlah_perlu_servis / total_pelanggan * 100 if total_pelanggan > 0 else 0
        avg_delay = int(perlu_servis['Terlambat (Hari)'].mean()) if not perlu_servis.empty else 0
        servis_bulan_ini = len(df[df['Tgl Service Terakhir'].dt.month == hari_ini.month])
        
        with col1:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-label'>📊 Total Pelanggan</div>
                    <div class='metric-value'>{total_pelanggan:,}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class='metric-card' style='background: linear-gradient(135deg, rgba(200, 50, 50, 0.4), rgba(200, 100, 50, 0.3));'>
                    <div class='metric-label'>⚠️ Perlu Servis (>60 Hari)</div>
                    <div class='metric-value'>{jumlah_perlu_servis:,}</div>
                    <div class='metric-delta'>↑ {persen_perlu:.1f}% dari total</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div class='metric-card' style='background: linear-gradient(135deg, rgba(180, 80, 200, 0.3), rgba(100, 50, 200, 0.4));'>
                    <div class='metric-label'>⏱ Rata-rata Keterlambatan</div>
                    <div class='metric-value'>{avg_delay}</div>
                    <div class='metric-label' style='font-size:0.9rem; margin-top:8px;'>Hari</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
                <div class='metric-card' style='background: linear-gradient(135deg, rgba(50, 200, 100, 0.3), rgba(50, 150, 200, 0.4));'>
                    <div class='metric-label'>🔧 Servis Bulan Ini</div>
                    <div class='metric-value'>{servis_bulan_ini:,}</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)  # <--- Ini yang benar, tanpa True ekstra!

    # ==================== VISUALISASI RINGKAS ====================
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📊 Insight Cepat")

        c1, c2, c3 = st.columns(3)

        with c1:
            top_model = df['Market Name'].value_counts().head(1)
            st.markdown(f"""
                <div class='metric-card' style='background: linear-gradient(135deg, rgba(255, 100, 100, 0.3), rgba(255, 150, 50, 0.3)); height:180px;'>
                    <div style='font-size:1.1rem; color:#ddd;'>🏍️ Model Terbanyak</div>
                    <div style='font-size:1.8rem; font-weight:700; margin:16px 0;'>{top_model.index[0]}</div>
                    <div style='color:#aaa;'>{top_model.values[0]:,} unit</div>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            if 'Kecamatan' in df.columns:
                top_kec = df['Kecamatan'].value_counts().head(1)
                st.markdown(f"""
                    <div class='metric-card' style='background: linear-gradient(135deg, rgba(100, 200, 255, 0.3), rgba(50, 100, 200, 0.4)); height:180px;'>
                        <div style='font-size:1.1rem; color:#ddd;'>📍 Kecamatan Dominan</div>
                        <div style='font-size:1.8rem; font-weight:700; margin:16px 0;'>{top_kec.index[0]}</div>
                        <div style='color:#aaa;'>{top_kec.values[0]:,} pelanggan</div>
                    </div>
                """, unsafe_allow_html=True)

        with c3:
            umur_rata = (datetime.now().year - df['Tahun Rakit'].mean()) if not df['Tahun Rakit'].isnull().all() else 0
            st.markdown(f"""
                <div class='metric-card' style='background: linear-gradient(135deg, rgba(150, 200, 50, 0.3), rgba(100, 200, 100, 0.4)); height:180px;'>
                    <div style='font-size:1.1rem; color:#ddd;'>🗓️ Rata-rata Umur Motor</div>
                    <div style='font-size:2.5rem; font-weight:700; margin:16px 0;'>{umur_rata:.1f}</div>
                    <div style='color:#aaa;'>Tahun</div>
                </div>
            """, unsafe_allow_html=True)

        # Tren Bulanan Kecil
        st.markdown("<br>", unsafe_allow_html=True)
        df_trend = df.resample('M', on='Tgl Service Terakhir').size().reset_index(name='Jumlah')
        fig_trend = px.area(df_trend, x='Tgl Service Terakhir', y='Jumlah',
                            color_discrete_sequence=['#ff4b4b'], height=300)
        fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                font_color='#ffffff', margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_trend, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ==================== FOLLOW UP (Opsional bisa ditambah lagi) ====================
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📲 Pelanggan Prioritas Follow Up")
        if not perlu_servis.empty:
            st.info(f"Ada **{len(perlu_servis):,} pelanggan** yang sudah lebih dari 60 hari belum servis. Siap untuk reminder WhatsApp!")
            # Bisa ditambah tabel link WA seperti sebelumnya jika perlu
        else:
            st.success("🎉 Semua pelanggan rutin servis dalam 60 hari terakhir!")
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Pastikan Google Sheet dibagikan dengan 'Anyone with the link' dan kolom sesuai.")


