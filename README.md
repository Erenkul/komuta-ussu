# Komuta Üssü

Bilgisayarında çalışan, çizgi film görünümlü bir yapay zekâ ofisi. On bir ajan (Leonardo ofis
müdürü, Turing güvenlik uzmanı, Shakespeare sosyal medya, Picasso reklam, Champollion çeviri,
Einstein veri, Michelangelo ürün tasarımı, Nightingale topluluk, Aristoteles eğitmen, Darwin
araştırma, Ada yazılım) seçtiğin proje için taslak yazar. Sen onları komuta odası gibi bir ekranda
izler, notunu yazar, işlerini İş Defteri'nde okursun.

- **Tamamen yerel.** Modeller LM Studio (ya da Bionic) üzerinden senin bilgisayarında çalışır.
  Model indirmek dışında internet gerekmez, hiçbir metin dışarı gitmez.
- **Ajanlar yalnız yazar.** Komut çalıştıramaz, dosya silemez, Git'e ya da hesaplarına dokunamaz.
  Her taslak güvenlik kurallarından geçer; takılan karantinaya gider.
- **Bilgisayarı yormaz.** Aynı anda tek model çalışır, işler arasında dinlenir. Model boşta
  kalınca bellekten çıkar; ağır bir uygulama açıkken (ör. Unity) ya da pildeyken ekip bekler.

## Gereksinimler

| | |
|---|---|
| İşletim sistemi | Windows 10 ya da 11 |
| Bellek | 16 GB önerilir (model açıkken 6–9 GB tutar) |
| Python | 3.10 ya da yenisi |
| Model sunucusu | [LM Studio](https://lmstudio.ai) 0.4+ (ya da Bionic) |
| Model | `gemma-4-e4b-it` (yaklaşık 5 GB), isteğe bağlı `qwen3.5-9b` |

## Kurulum

### Claude Code ile (en kolayı)

```
git clone https://github.com/Erenkul/komuta-ussu.git
cd komuta-ussu
claude
```

Açılan Claude Code'a **kur** yaz. Claude [AGENTS.md](AGENTS.md)'deki adımları izler: kurulum
betiğini çalıştırır, eksikleri (Python, LM Studio, model) sana sorarak tamamlar ve ofisi bir
denemeyle açıp kapatır.

### Elle

1. Python 3.10+ kur: `winget install Python.Python.3.12`
2. LM Studio'yu kur (`winget install ElementLabs.LMStudio`), **Discover**'dan `gemma-4-e4b-it`'i
   indir, **Developer** sekmesinde **Local Server**'ı başlat (port 1234).
3. Repoyu indir ve kurulum betiğini çalıştır:

   ```
   git clone https://github.com/Erenkul/komuta-ussu.git
   cd komuta-ussu
   powershell -ExecutionPolicy Bypass -File kur.ps1 -Dene
   ```

Betik Python'u ve model sunucusunu bulur, `ayar.json`'u oluşturur, eksik modelleri söyler,
`Komuta Üssü.exe` başlatıcısını derler ve masaüstüne kısayol koyar. Tekrar çalıştırmak
güvenlidir. Hiçbir şeyi oturum açılışına yazmaz, yönetici izni istemez.

## Kullanım

Masaüstündeki **Komuta Üssü** kısayoluna çift tıkla (ya da `ofis.bat`). Ekran
http://127.0.0.1:8765 adresinde açılır; yalnız bu bilgisayardan erişilir.

- **Üst şerit:** proje seçimi, **İş Defteri**, ofisin durumu (yeşil çalışıyor, sarı durduruldu),
  bellek ve **Ofisi durdur / Ofisi çalıştır** düğmesi.
- **Oda:** her ajanın masası. Yazan ajanın ekranı parlar, levhasında seviyesi ve puanı durur;
  masaya tıklayınca işleri, kuralları ve modelleri açılır.
- **Sağ panel:** şu an kimin ne yazdığı, son biten işler, **Ofise yaz** (müdür hemen yanıtlar),
  haberler, ekip içi yazışma, taslaklar, puanlar ve rapor.
- **İş Defteri** (`/isler`): bütün işler kart kart: kim yaptı, ne istendi, ne çıktı, puanı,
  güvenlikten geçti mi, iş arkadaşı baktı mı. Tam metin biçimli okunur; 👍/👎 ile ajanı eğitirsin.

### Proje açmak

Üstten **+ Yeni** ile aç, **Bilgi** ile projeni anlat: ne olduğu, kimin için, ne olmadığı,
kuralları. Ajanlar yalnız buna dayanır. `projeler/ornek/` örnek şablondur.

### Ofise iş vermek

Ekrandan **Ofise yaz** ile not bırakabilirsin. Doğrudan iş için `projeler/<proje>/gorevler/`
klasörüne bir `.txt` dosyası koy: ilk satır ajanın kimliği, altı görev.

```
deniz
Bu hafta için 3 kısa video fikri yaz: kanca cümlesi ve bir satır görüntü.
```

Ajan kimlikleri: `aylin` (Leonardo), `kaan` (Turing), `deniz` (Shakespeare), `ece` (Picasso),
`can` (Einstein), `zeynep` (Champollion), `bora` (Michelangelo), `selin` (Nightingale),
`elif` (Aristoteles), `darwin` (Darwin), `ada` (Ada).

Ofis bunlardan başka kendiliğinden de çalışır: `gunluk.json`'daki günlük işler, `hedefler.json`'dan
Leonardo'nun böldüğü plan parçaları, ajanların kendi alanındaki Ar-Ge'si ve kendini eğittiği
sınavlar. Hepsini `ayar.json`'dan kısabilir ya da kapatabilirsin.

## Ayarlar (`ayar.json`)

Kurulumda `ayar.ornek.json`'dan kopyalanır ve repoya girmez.

| Anahtar | Ne işe yarar | Varsayılan |
|---|---|---|
| `api` | Model sunucusu adresi (kurulum bulur) | `http://127.0.0.1:1234/v1` |
| `zincir` | Her ajanın sırayla denediği modeller | Gemma, sonra Qwen |
| `baglam` | Ofisin model açtığı bağlam uzunluğu | 8192 |
| `durdur` | `true` iken ofis bekler (ekrandaki düğme bunu değiştirir) | `false` |
| `gunluk_sinav`, `gunluk_arge`, `gunluk_plan`, `gunluk_akran` | Günlük sınav, Ar-Ge, plan ve iş arkadaşı görüşü sınırı | 12, 15, 1, 10 |
| `bosta_birak_sn` | Model bu kadar saniye kullanılmazsa bellekten çıkar | 180 |
| `bellek_esik` | Bellek bu yüzdeyi geçince model hemen bırakılır | 90 |
| `bekle_uygulamalar` | Bunlar açıkken ekip bekler | `["Unity.exe"]` |
| `disari_bekle_dk` | Sen başka bir uygulamada modelle konuştuktan sonra ofisin bekleyeceği dakika | 15 |
| `github_yalniz_baglanti` | GitHub eşitlemede yalnız bağlantısı gösterilecek depolar | `[]` |

## Güvenlik

- Sunucu yalnız `127.0.0.1`'e bağlanır, başka cihazdan erişilemez; yabancı sayfaların istekleri
  reddedilir.
- Ajanların komut, dosya silme, Git, internet ya da hesap yetkisi yoktur.
- Her taslak Turing'in kurallarından geçer (gizli anahtar, şifre, kişisel e-posta, telifli
  karakter, sahte iddia, dış bağlantı, komut); takılan karantinaya gider.
- Taslaklar sen onaylamadan hiçbir yerde kullanılmaz.
- Senin projelerin, ayarların, notların ve taslakların bu klasörde kalır ve repoya girmez
  ([.gitignore](.gitignore)).

## İsteğe bağlı: Claude Code köprüsü

Ofisin "baş ajan"ı olarak Claude Code'u kullanabilirsin: ekrandan yazdığın notlar Claude'a, onun
yanıtları ekrana gelir. Claude Code ayarlarına (`~/.claude/settings.json`) şu kancayı ekle
(yolu kendi klasörünle değiştir), ya da Claude'a "köprüyü kur" de:

```json
{
  "hooks": {
    "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "python C:/yol/komuta-ussu/gelen.py" }] }]
  }
}
```

Claude ekrana `python gelen.py yanit <not-adı> <yanıt>` ile yanıt yazar.

## Klasörler

| Yol | İçerik |
|---|---|
| `ofis.py` | Sunucu ve ajanların çalışma döngüsü (yalnız Python standart kitaplığı) |
| `egitim.py`, `egitim/` | Puanlama, sınavlar, ajanların beceri kartları ve genel kuralları |
| `index.html`, `isler.html` | Ofis ekranı ve İş Defteri |
| `ekip.json`, `modeller.json` | Ajanlar ve önerilen modeller |
| `projeler/<id>/` | Projenin bilgisi, görevleri, taslakları, karantinası, raporları (kişisel) |
| `kur.ps1`, `us.cs`, `ofis.bat` | Kurulum, başlatıcı, yedek başlatma |

## Lisans

[MIT](LICENSE)

---

**English, in short:** Komuta Üssü is a local, cartoon-style AI office for Windows. Eleven agents
draft work for your project on local models through LM Studio; nothing leaves your computer, and
agents can only write drafts. Install: clone, then run `powershell -ExecutionPolicy Bypass -File
kur.ps1 -Dene` (or open Claude Code in the folder and type `kur`). The interface is in Turkish.
