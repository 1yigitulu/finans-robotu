import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="FinansÇözüm V6 - ÇEK SİSTEMİ", layout="wide", page_icon="🏦")

# --- KENAR ÇUBUĞU ---
st.sidebar.title("⚙️ Piyasa Verileri")
st.sidebar.info("Çek vade analizi ve piyasa koşulları için verileri giriniz.")
yillik_faiz = st.sidebar.number_input("Yıllık Mevduat/Kredi Faizi (%)", value=45.0)
kar_marji = st.sidebar.number_input("Brüt Kâr Marjınız (%)", value=15.0)
ideal_vade = st.sidebar.number_input("Şirket Politikası Vade (Gün)", value=45)

gunluk_faiz = yillik_faiz / 360 / 100

# --- ANA BAŞLIK ---
st.title("🏦 FİNANS ROBOTU V6.0 - ÇEK ENTEGRASYONLU")
st.markdown("**Nakit ve Vadeli Çek Ayrıştırmalı Risk Analizi**")
st.markdown("---")

# --- DOSYA YÜKLEME ---
uploaded_file = st.file_uploader("Müşteri Ekstresini Yükleyin (Excel veya CSV)", type=["xlsx", "xls", "csv"])

# --- HESAPLAMA FONKSİYONLARI ---
def agirlikli_tarih_hesapla(df, tarih_col, tutar_col):
    """Tarihlerin tutara göre ağırlıklı ortalamasını bulur."""
    df_temp = df.copy()
    df_temp = df_temp[df_temp[tutar_col] > 0]
    if df_temp.empty: return None
    
    ref_date = df_temp[tarih_col].min()
    df_temp['gun_farki'] = (df_temp[tarih_col] - ref_date).dt.days
    
    toplam_tutar = df_temp[tutar_col].sum()
    agirlikli_gun = (df_temp[tutar_col] * df_temp['gun_farki']).sum() / toplam_tutar
    return ref_date + datetime.timedelta(days=int(agirlikli_gun))

def yorumcu_analizi(net_kar_orani, gerceklesen_vade, ideal_vade, finansal_maliyet, kalan_bakiye, kar_marji):
    """Ekonomist ağzından detaylı yorum."""
    if net_kar_orani < 0:
        return (
            "ACİL DURUM: ÇEKLER KURTARMIYOR, ZARARDASINIZ", "🚨", "error",
            f"**Sayın Yöneticim, durum kritik.** Çeklerin vadeleri dahil edildiğinde ortalama vadeniz **{gerceklesen_vade} güne** çıkmış. Vade farkı ({finansal_maliyet:,.0f} TL) tüm kârınızı yutmuş.",
            "- **Sevkiyatı Durdurun:** Çeklerin vadesi dolup tahsil edilmeden mal vermeyin."
        )
    elif net_kar_orani < (kar_marji / 3):
        return (
            "DİKKAT: VADELİ ÇEKLER KÂRI ERİTTİ", "⚠️", "warning",
            f"**Çek vadeleri çok uzun.** Net kâr oranı **%{net_kar_orani:.2f}**. Paranın zaman maliyeti kârınızı süpürüyor.",
            "- **Vade Kısıtlaması:** Müşteriden daha kısa vadeli çek talep edin."
        )
    elif gerceklesen_vade > ideal_vade:
        return (
            "İDARE EDER: VADE AŞIMI VAR", "⚖️", "info",
            f"Ortalama vade **{gerceklesen_vade} güne** çıkmış. Çekler sayesinde tahsilat garanti gibi dursa da vade farkı maliyeti ({finansal_maliyet:,.0f} TL) oluşmuş.",
            "- **Hatırlatma:** Müşteriyi çek vadelerini öne çekmesi konusunda uyarın."
        )
    else:
        return (
            "MÜKEMMEL: ÇEKLER VE NAKİT DENGELİ", "✅", "success",
            f"**Tebrikler.** Ortalama vade **{gerceklesen_vade} gün**. Çeklerin vadesi makul, nakit akışı sağlıklı.",
            "- **Devam:** Bu çalışma modelini koruyun."
        )

# --- ANA PROGRAM AKIŞI ---
if uploaded_file is not None:
    try:
        # DOSYA OKUMA
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file, header=1) 
        else: df = pd.read_excel(uploaded_file, header=1)

        # TEMİZLİK VE FORMATLAMA
        df.columns = df.columns.str.strip()
        df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
        
        # 'Vade Tarihi' sütunu var mı kontrol et, yoksa normal tarihi kopyala
        if 'Vade Tarihi' not in df.columns:
            st.warning("Excel'de 'Vade Tarihi' sütunu bulunamadı. Çekler için de İşlem Tarihi kullanılacak.")
            df['Efektif_Tarih'] = df['Tarih']
        else:
            df['Vade Tarihi'] = pd.to_datetime(df['Vade Tarihi'], errors='coerce')
            # Eğer Vade Tarihi boşsa (Nakitse), İşlem Tarihini kullan
            df['Efektif_Tarih'] = df['Vade Tarihi'].fillna(df['Tarih'])

        df['Borç'] = pd.to_numeric(df['Borç'], errors='coerce').fillna(0)
        df['Alacak'] = pd.to_numeric(df['Alacak'], errors='coerce').fillna(0)
        
        # ÇEK ALGILAMA MANTIĞI
        # Açıklama veya Fiş Türü içinde "Çek" geçenleri işaretle
        def cek_kontrol(row):
            text = str(row.get('Açıklama', '')) + " " + str(row.get('Fiş Türü', ''))
            if 'Çek' in text or 'ÇEK' in text or 'cek' in text:
                return 'Çek'
            return 'Nakit/Havale'

        df['Odeme_Turu'] = df.apply(cek_kontrol, axis=1)

        # Veri Temizliği Son
        df = df.dropna(subset=['Tarih'])

        # --- HESAPLAMALAR ---
        toplam_satis = df['Borç'].sum()
        toplam_odenen = df['Alacak'].sum()
        kalan_bakiye = toplam_satis - toplam_odenen
        
        # 1. Ortalama Fatura Tarihi
        avg_fatura_tarihi = agirlikli_tarih_hesapla(df, 'Tarih', 'Borç')
        
        # 2. Ortalama Ödeme Tarihi (KRİTİK BÖLÜM: Efektif Tarih Kullanılıyor)
        # Efektif Tarih: Nakitse işlem günü, Çekse vade günü.
        
        df_odeme = df[df['Alacak'] > 0].copy()
        
        # Simülasyon: Kalan bakiye bugün kapanırsa
        bugun = datetime.datetime.now()
        if kalan_bakiye > 0:
            df_odeme = pd.concat([df_odeme, pd.DataFrame([{
                'Efektif_Tarih': bugun, 
                'Alacak': kalan_bakiye, 
                'Borç': 0,
                'Odeme_Turu': 'Kalan Bakiye'
            }])], ignore_index=True)
            
        avg_odeme_tarihi = agirlikli_tarih_hesapla(df_odeme, 'Efektif_Tarih', 'Alacak')
        
        if avg_fatura_tarihi and avg_odeme_tarihi:
            gerceklesen_vade = int((avg_odeme_tarihi - avg_fatura_tarihi).days)
        else:
            gerceklesen_vade = 0

        # Finansal Analiz
        finansal_maliyet = toplam_satis * gerceklesen_vade * gunluk_faiz
        teorik_kar = toplam_satis * (kar_marji / 100)
        net_kar = teorik_kar - finansal_maliyet
        net_kar_orani = (net_kar / toplam_satis) * 100 if toplam_satis > 0 else 0

        # --- GÖRSELLEŞTİRME ---
        
        # Metrikler
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Ciro", f"{toplam_satis:,.0f} TL")
        c2.metric("Tahsilat (Çek Dahil)", f"{toplam_odenen:,.0f} TL")
        c3.metric("KALAN BAKİYE", f"{kalan_bakiye:,.0f} TL", delta_color="inverse")
        c4.metric("Ortalama Vade", f"{gerceklesen_vade} Gün", delta=f"Hedef: {ideal_vade}")
        
        st.divider()

        sol, sag = st.columns([1, 2])
        with sol:
            # Gauge Chart
            st.subheader("⏱️ Gerçek Vade (Çekler Dahil)")
            fig = go.Figure(go.Indicator(
                mode = "gauge+number", value = gerceklesen_vade,
                gauge = {
                    'axis': {'range': [None, max(130, gerceklesen_vade + 20)]},
                    'bar': {'color': "black"},
                    'steps': [
                        {'range': [0, 30], 'color': "#00b894"},
                        {'range': [30, 45], 'color': "#fdcb6e"},
                        {'range': [45, 90], 'color': "#e17055"},
                        {'range': [90, 500], 'color': "#d63031"}
                    ],
                    'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': ideal_vade}
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
            
            # Çek Bilgilendirmesi
            cek_toplam = df[df['Odeme_Turu'] == 'Çek']['Alacak'].sum()
            if cek_toplam > 0:
                st.info(f"ℹ️ **Bilgi:** Toplam tahsilatın **{cek_toplam:,.2f} TL** kadarı ÇEK ile yapılmıştır. Robot, bu ödemeler için işlem tarihini değil, **Vade Tarihini** baz alarak hesap yapmıştır.")

        with sag:
            # Ekonomist Yorumu
            baslik, ikon, renk, yorum, tavsiye = yorumcu_analizi(net_kar_orani, gerceklesen_vade, ideal_vade, finansal_maliyet, kalan_bakiye, kar_marji)
            st.subheader(f"{ikon} Ekonomist Görüşü")
            with st.container():
                st.markdown(f"### {baslik}")
                st.write(yorum)
                st.warning(f"💡 **Finansal Gerçek:** Kağıt üzerinde {teorik_kar:,.0f} TL kâr bekliyordunuz. Çek vade maliyetleriyle birlikte **{finansal_maliyet:,.0f} TL** eridi.")
                st.success(f"💰 **CEBE KALAN NET KÂR: {net_kar:,.0f} TL**")
                st.markdown("#### 🚀 Tavsiyeler")
                st.markdown(tavsiye)

        with st.expander("📂 Detaylı Ekstre ve Vade Tarihleri"):
            # Gösterim için özel tablo
            gosterim_df = df[['Tarih', 'Vade Tarihi', 'Fiş Türü', 'Açıklama', 'Borç', 'Alacak', 'Odeme_Turu']].copy()
            # Tarihleri string yapalım düzgün gözüksün
            gosterim_df['Tarih'] = gosterim_df['Tarih'].dt.strftime('%d.%m.%Y')
            gosterim_df['Vade Tarihi'] = gosterim_df['Vade Tarihi'].dt.strftime('%d.%m.%Y')
            st.dataframe(gosterim_df)

    except Exception as e:
        st.error(f"Hata: {e}")
else:
    st.info("Lütfen dosyayı yükleyin.")