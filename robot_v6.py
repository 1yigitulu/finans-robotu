import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="FinansÇözüm V6.1 - AKILLI YORUMCU", layout="wide", page_icon="🧠")

# --- KENAR ÇUBUĞU ---
st.sidebar.title("⚙️ Piyasa Verileri")
st.sidebar.info("Verileri güncel piyasa koşullarına göre giriniz.")
yillik_faiz = st.sidebar.number_input("Yıllık Mevduat/Kredi Faizi (%)", value=45.0)
kar_marji = st.sidebar.number_input("Brüt Kâr Marjınız (%)", value=15.0)
ideal_vade = st.sidebar.number_input("Şirket Politikası Vade (Gün)", value=45)

gunluk_faiz = yillik_faiz / 360 / 100

# --- ANA BAŞLIK ---
st.title("🧠 FİNANS ROBOTU V6.1 - AKILLI YORUMCU")
st.markdown("**Nakit ve Çek Ayrıştırmalı Dinamik Analiz**")
st.markdown("---")

# --- DOSYA YÜKLEME ---
uploaded_file = st.file_uploader("Müşteri Ekstresini Yükleyin (Excel veya CSV)", type=["xlsx", "xls", "csv"])

# --- HESAPLAMA FONKSİYONLARI ---
def agirlikli_tarih_hesapla(df, tarih_col, tutar_col):
    df_temp = df.copy()
    df_temp = df_temp[df_temp[tutar_col] > 0]
    if df_temp.empty: return None
    
    ref_date = df_temp[tarih_col].min()
    df_temp['gun_farki'] = (df_temp[tarih_col] - ref_date).dt.days
    
    toplam_tutar = df_temp[tutar_col].sum()
    agirlikli_gun = (df_temp[tutar_col] * df_temp['gun_farki']).sum() / toplam_tutar
    return ref_date + datetime.timedelta(days=int(agirlikli_gun))

def yorumcu_analizi(net_kar_orani, gerceklesen_vade, ideal_vade, finansal_maliyet, kalan_bakiye, kar_marji, cek_var_mi):
    """
    Ekonomist ağzından detaylı yorum.
    cek_var_mi: True ise çek odaklı konuşur, False ise genel vade odaklı konuşur.
    """
    
    # 1. SENARYO: ZARAR
    if net_kar_orani < 0:
        baslik = "ACİL DURUM: SERMAYE ERİMESİ MEVCUT"
        ikon = "🚨"
        renk = "error"
        
        if cek_var_mi:
            yorum = f"**Sayın Yöneticim, durum kritik.** Çeklerin vadeleri dahil edildiğinde ortalama vadeniz **{gerceklesen_vade} güne** çıkmış. Vade farkı ({finansal_maliyet:,.0f} TL) tüm kârınızı yutmuş."
            tavsiye = "- **Sevkiyatı Durdurun:** Çeklerin vadesi dolup tahsil edilmeden mal vermeyin."
        else:
            yorum = f"**Sayın Yöneticim, durum kritik.** Müşterinin ödeme performansı çok düşük. Ortalama vade **{gerceklesen_vade} güne** ulaşmış. {finansal_maliyet:,.0f} TL tutarındaki vade maliyeti kârınızı bitirmiş."
            tavsiye = "- **Sevkiyatı Durdurun:** Eski borç kapanmadan mal çıkışı yapmayın.\n- **Peşin Çalışın:** Vadeli çalışmayı sonlandırın."

        return baslik, ikon, renk, yorum, tavsiye

    # 2. SENARYO: RİSKLİ (Kâr Eridi)
    elif net_kar_orani < (kar_marji / 3):
        baslik = "DİKKAT: KÂR MARJI KRİTİK SEVİYEDE"
        ikon = "⚠️"
        renk = "warning"
        
        if cek_var_mi:
            yorum = f"**Vadeli çekler kârı eritti.** Çek vadeleri çok uzun olduğu için net kâr oranı **%{net_kar_orani:.2f}** seviyesine düştü. Paranın zaman maliyeti kârınızı süpürüyor."
            tavsiye = "- **Vade Kısıtlaması:** Müşteriden daha kısa vadeli çek talep edin."
        else:
            yorum = f"**Ödemeler çok gecikiyor.** Nakit dönüş hızı çok yavaşladığı için net kâr oranı **%{net_kar_orani:.2f}** seviyesinde kaldı. Parayı faize koysanız daha kârlıydı."
            tavsiye = "- **Fiyat Politikası:** Vade farkı faturası kesin veya fiyatları güncelleyin."

        return baslik, ikon, renk, yorum, tavsiye

    # 3. SENARYO: İDARE EDER
    elif gerceklesen_vade > ideal_vade:
        baslik = "İDARE EDER: VADE AŞIMI VAR"
        ikon = "⚖️"
        renk = "info"
        
        if cek_var_mi:
            yorum = f"Ortalama vade **{gerceklesen_vade} güne** çıkmış. Çekler ödeniyor olsa da, vadelerin uzunluğu size {finansal_maliyet:,.0f} TL faiz maliyeti yaratıyor."
            tavsiye = "- **Hatırlatma:** Müşteriyi çek vadelerini öne çekmesi konusunda uyarın."
        else:
            yorum = f"İdeal vade ({ideal_vade} gün) aşılmış ve **{gerceklesen_vade} güne** çıkılmış. Henüz zarar yok ama kârınızdan {finansal_maliyet:,.0f} TL eksildi."
            tavsiye = "- **Sözlü Uyarı:** 'Ödemeleri biraz daha sıklaştıralım' şeklinde hatırlatma yapın."

        return baslik, ikon, renk, yorum, tavsiye

    # 4. SENARYO: MÜKEMMEL
    else:
        baslik = "MÜKEMMEL: TİCARET SAĞLIKLI"
        ikon = "✅"
        renk = "success"
        
        if cek_var_mi:
            yorum = f"**Tebrikler.** Ortalama vade **{gerceklesen_vade} gün**. Çeklerin vadesi makul ve nakit akışınız dengeli."
        else:
            yorum = f"**Tebrikler.** Müşteri ödemelerine sadık. Ortalama vade **{gerceklesen_vade} gün**. Nakit akışınız gayet sağlıklı."
            
        tavsiye = "- **Devam:** Bu çalışma modelini koruyun."

        return baslik, ikon, renk, yorum, tavsiye


# --- ANA PROGRAM AKIŞI ---
if uploaded_file is not None:
    try:
        # DOSYA OKUMA
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file, header=1) 
        else: df = pd.read_excel(uploaded_file, header=1)

        # TEMİZLİK
        df.columns = df.columns.str.strip()
        df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
        
        # Vade Tarihi Kontrolü
        if 'Vade Tarihi' not in df.columns:
            df['Efektif_Tarih'] = df['Tarih']
        else:
            df['Vade Tarihi'] = pd.to_datetime(df['Vade Tarihi'], errors='coerce')
            df['Efektif_Tarih'] = df['Vade Tarihi'].fillna(df['Tarih'])

        df['Borç'] = pd.to_numeric(df['Borç'], errors='coerce').fillna(0)
        df['Alacak'] = pd.to_numeric(df['Alacak'], errors='coerce').fillna(0)
        
        # ÇEK ALGILAMA (Dinamik)
        def cek_kontrol(row):
            text = str(row.get('Açıklama', '')) + " " + str(row.get('Fiş Türü', ''))
            if 'Çek' in text or 'ÇEK' in text or 'cek' in text:
                return 'Çek'
            return 'Nakit/Havale'

        df['Odeme_Turu'] = df.apply(cek_kontrol, axis=1)
        
        # Dosyada HİÇ Çek var mı kontrolü (Yorumcu için)
        cek_var_mi = 'Çek' in df['Odeme_Turu'].values

        df = df.dropna(subset=['Tarih'])

        # HESAPLAMALAR
        toplam_satis = df['Borç'].sum()
        toplam_odenen = df['Alacak'].sum()
        kalan_bakiye = toplam_satis - toplam_odenen
        
        avg_fatura_tarihi = agirlikli_tarih_hesapla(df, 'Tarih', 'Borç')
        
        df_odeme = df[df['Alacak'] > 0].copy()
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

        finansal_maliyet = toplam_satis * gerceklesen_vade * gunluk_faiz
        teorik_kar = toplam_satis * (kar_marji / 100)
        net_kar = teorik_kar - finansal_maliyet
        net_kar_orani = (net_kar / toplam_satis) * 100 if toplam_satis > 0 else 0

        # --- EKRAN ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Ciro", f"{toplam_satis:,.0f} TL")
        c2.metric("Tahsilat", f"{toplam_odenen:,.0f} TL")
        c3.metric("KALAN BAKİYE", f"{kalan_bakiye:,.0f} TL", delta_color="inverse")
        c4.metric("Ortalama Vade", f"{gerceklesen_vade} Gün", delta=f"Hedef: {ideal_vade}")
        
        st.divider()

        sol, sag = st.columns([1, 2])
        with sol:
            st.subheader("⏱️ Gerçek Vade")
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
            
            if cek_var_mi:
                st.info("ℹ️ **Bilgi:** Bu müşteri ödemelerinde ÇEK kullanmıştır. Hesaplamalar Çek Vade Tarihine göre yapılmıştır.")
            else:
                st.info("ℹ️ **Bilgi:** Bu müşteride ÇEK kullanımı tespit edilmemiştir. Hesaplamalar Nakit/Havale işlem tarihine göre yapılmıştır.")

        with sag:
            # Fonksiyona cek_var_mi parametresini gönderiyoruz
            baslik, ikon, renk, yorum, tavsiye = yorumcu_analizi(
                net_kar_orani, gerceklesen_vade, ideal_vade, finansal_maliyet, kalan_bakiye, kar_marji, cek_var_mi
            )
            
            st.subheader(f"{ikon} Ekonomist Görüşü")
            with st.container():
                st.markdown(f"### {baslik}")
                st.write(yorum)
                
                # Dinamik Finansal Gerçek Mesajı
                sebep_text = "Çek vade maliyetleriyle" if cek_var_mi else "Vade/Gecikme maliyetiyle"
                
                st.warning(f"💡 **Finansal Gerçek:** Kağıt üzerinde {teorik_kar:,.0f} TL kâr bekliyordunuz. {sebep_text} birlikte **{finansal_maliyet:,.0f} TL** eridi.")
                st.success(f"💰 **CEBE KALAN NET KÂR: {net_kar:,.0f} TL**")
                
                st.markdown("#### 🚀 Tavsiyeler")
                st.markdown(tavsiye)

        with st.expander("📂 Ekstre Detayı"):
            st.dataframe(df)

    except Exception as e:
        st.error(f"Hata: {e}")
else:
    st.info("Lütfen dosyayı yükleyin.")