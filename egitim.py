"""Ofisin eğitimi: taslak puanlama, ajan hafızası, sınav ve kural deneme.

Puanı model vermez, bu kurallar verir: modelin kendi yazısına not vermesine güvenilmez, üstelik
sabit kurallar anlık çalışır ve makineyi yormaz. Yeni kuralı model önerebilir ama hafızaya ancak
sınavda puanı gerçekten yükseltirse girer; öneri güvenlik süzgecinden de geçer. Baş ajanın
yazdığı kurallar (hafiza/<id>.md) kendi kendine silinmez, ajanın öğrendikleri (<id>.oz.md)
sınırı aşınca en eskisinden silinir.
"""
import datetime, json, os, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
# Ajanın her projede geçerli kuralları burada, projeye özgü olanlar projeler/<id>/hafiza içinde.
GENEL = os.path.join(ROOT, 'egitim', 'genel')
HAFIZA = PUANLAR = SINAV = ''
PROJE = {}
OZ_SINIR = 6
os.makedirs(GENEL, exist_ok=True)


def proje(klasor, bilgi):
    """Puanlar, hafıza ve sınav etkin projenin klasöründen gelir."""
    global HAFIZA, PUANLAR, SINAV, PROJE
    HAFIZA = os.path.join(klasor, 'hafiza')
    PUANLAR = os.path.join(klasor, 'puanlar.jsonl')
    SINAV = os.path.join(klasor, 'sinav.json')
    PROJE = bilgi
    os.makedirs(HAFIZA, exist_ok=True)

EMOJI = r'[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B50\uFE0F]'
# ad, desen, ceza, kuralın ajana söylenişi
CEZALAR = [
    ('rol anlatımı', r'(rolümde|uzmanı olarak|analisti olarak|tasarımcısı olarak)', 15, 'Kendinden ve rolünden söz etme.'),
    ('emoji', EMOJI, 10, 'Emoji kullanma.'),
    ('uydurma: söz', r'(en kısa sürede (çöz|düzelt)|hemen düzelt|garanti ediyoruz)', 15, 'Yapılacağı kesin olmayan şeye söz verme.'),
    ('yabancı harf', r'[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]', 25, 'Yazdığın dilde kal, başka alfabeden kelime karıştırma.'),
    ('hitap', r'\bsahibim\b|size yardımcı olabilirim', 10, 'Sahibine sen diye yaz, yardım teklifiyle bitirme.'),
    ('baskı dili', r'(kaçırma|acele et|son şans|sınırlı süre|hurry|don.t miss)', 15, 'Baskı kuran dil kullanma.'),
    ('abartı', r'(en iyi|mükemmel|muhteşem|the best|the ultimate|benzersiz)', 10, 'Abartı sözcükleri kullanma.'),
]
GIRIS = (r'^\W*(harika|tabii|tabi ki|elbette|merhaba|memnuniyetle|sure\b|great\b|işte\b|aşağıda|anladığım kadarıyla|bir [^\n]{0,30} olarak)', 15, 'dolgu giriş', 'Doğrudan işe başla, giriş cümlesi yazma.')
ADET = re.compile(r'\b(\d{1,2}) (?:(?:kısa|farklı|dürüst|küçük|maliyetsiz|sayı|tane|adet|soru|ana|temel)\s+)*(\w+)', re.I)
MADDE = re.compile(r'^\s*(\d+[.)]|[-*•]|\*\*|#{1,4} )', re.M)
INGILIZCE = re.compile(r'\b(the|your|you|and|with|first|every|to)\b', re.I)


# Kalıp cezaları yalnız yüzeyi görürse puan fazla yumuşak olur: bir denemede 292 taslağın 188'i
# 100 aldı. Şimdi içeriğe de bakılır ve otomatik puan en çok 90
# olur: 100 yalnız sahibinin ya da baş ajanın "İyi" oyudur.
TAVAN = 90
GENEL_LAF = re.compile(r'(önemlidir|önem taşı|büyük önem|kritik (öneme|bir)|dikkat edilmeli|göz önünde bulundur|'
                   r'sağlanmalıdır|etkili bir şekilde|önemli bir rol|çeşitli|birçok|oldukça|it is important|various|crucial)', re.I)
SOMUT = re.compile(r'\d|"[^"\n]{2,60}"|«[^»\n]{2,60}»|[\w-]+\.(?:cs|py|md|txt|png|json)\b')
CUMLE = re.compile(r'[^.!?\n]{25,}[.!?]')
ICERIK = [
    ('yüzeysel', 20, 'Görevi yüzeyde bırakma: her maddeye bir neden ve bir örnek yaz.'),
    ('genel laf', 10, '"önemlidir", "kritik", "çeşitli" gibi genel sözler yerine ne yapılacağını yaz.'),
    ('somut değil', 15, 'Somut ol: sayı, örnek metin ya da gerçek dosya adı ver.'),
    ('tekrar', 15, 'Aynı cümleyi ya da fikri iki kez yazma.'),
    ('yarım', 10, 'Taslağı yarım bırakma, son cümleyi tamamla.'),
]


def icerik(gorev, metin):
    """İçeriğin cezaları: kısa, genel, somutsuz, tekrarlı ya da yarım kalan taslak."""
    sade = re.sub(r'\s+', ' ', metin).strip()
    hatalar = []
    if len(sade) < 300:
        hatalar.append('yüzeysel')
    if len(GENEL_LAF.findall(sade)) >= 3:
        hatalar.append('genel laf')
    if not SOMUT.search(metin):
        hatalar.append('somut değil')
    cumleler = [re.sub(r'\W+', ' ', c).strip().lower() for c in CUMLE.findall(metin)]
    if len(cumleler) - len(set(cumleler)) >= 1:
        hatalar.append('tekrar')
    # Ofisin kendi satırları ("PASLA: Yok") cümle değildir.
    son = [l.strip() for l in metin.splitlines() if l.strip() and not re.match(r'[A-ZÇĞİÖŞÜ]{3,}:', l.strip())]
    if son and not MADDE.match(son[-1]) and not re.search(r'[.!?:)"»\]*_`]$', son[-1]):
        hatalar.append('yarım')
    return hatalar


DOSYA = re.compile(r'[\w./\\-]+\.(?:cs|py|tsx?|mjs)\b')
_dosyalar = {}


def kod_dosyalari():
    """Projenin gerçek dosya adları. Bir ajan yedi dosya uydurmuş, otomatik puan 100 vermişti. Repo yoksa denetim atlanır."""
    kok = PROJE.get('kod')
    if not kok:
        return set()
    if kok not in _dosyalar:
        o = subprocess.run(['git', '-C', kok, 'ls-files'], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=30, creationflags=0x08000000).stdout
        _dosyalar[kok] = {os.path.basename(s) for s in o.splitlines()}
    return _dosyalar[kok]


def uydurma_dosya(metin):
    """Var diye anılan ama repoda olmayan dosyalar. "Yeni" denen satır öneridir, sayılmaz."""
    gercek = kod_dosyalari()
    if not gercek:
        return []
    return [a for s in metin.splitlines() if not re.search(r'\byeni\b', s, re.I)
            for a in DOSYA.findall(s) if re.split(r'[/\\]', a)[-1] not in gercek]


def puanla(gorev, metin, tavan=TAVAN):
    """0-100 arası puan ve hata adları. Görev ne istediyse ona göre bakar."""
    temiz = metin
    for izinli in PROJE.get('izinli_eposta', []):
        temiz = temiz.replace(izinli, '')
    hatalar, puan = [], 100
    if re.search(GIRIS[0], temiz.strip()[:80], re.I):
        puan -= GIRIS[1]; hatalar.append(GIRIS[2])
    for ad, desen, ceza, _ in CEZALAR + [tuple(k[:4]) for k in PROJE.get('cezalar', [])]:
        if re.search(desen, temiz, re.I):
            puan -= ceza; hatalar.append(ad)
    if 'yabancı harf' in hatalar and re.search(r'japon|çince|korece|chinese|japanese|korean', gorev, re.I):
        puan += 25; hatalar.remove('yabancı harf')
    for k in PROJE.get('cezalar', []):
        if len(k) > 4 and k[0] in hatalar and k[4] in gorev.lower():
            puan += k[2]; hatalar.remove(k[0])
    if uydurma_dosya(temiz):
        puan -= 30; hatalar.append('uydurma dosya')
    m = ADET.search(gorev)
    if m and len(MADDE.findall(metin)) < int(m.group(1)):
        puan -= 20; hatalar.append('eksik madde')
    if re.search(r'ingilizce', gorev, re.I) and len(INGILIZCE.findall(metin)) < 3 and not re.search(r'english|ingilizce', metin, re.I):
        puan -= 20; hatalar.append('İngilizce yok')
    cezasi = {ad: ceza for ad, ceza, _ in ICERIK}
    for ad in icerik(gorev, temiz):
        puan -= cezasi[ad]; hatalar.append(ad)
    return max(0, min(tavan, puan)), hatalar


def duzeltme(hatalar):
    """Taslağın hatalarını ajana söylenecek kurallara çevirir."""
    sozluk = {k[0]: k[3] for k in CEZALAR + [tuple(k) for k in PROJE.get('cezalar', [])]}
    sozluk.update({GIRIS[2]: GIRIS[3],
                   'uydurma dosya': 'Yalnız sana verilen dosya adlarını yaz. Bilmiyorsan dosya adı yazma, "dosya bulunacak" de.',
                   'eksik madde': 'İstenen sayıda madde yaz, her madde kendi satırında numaralı olsun.',
                   'İngilizce yok': 'İngilizce istenen yerleri gerçekten İngilizce yaz.'})
    sozluk.update({ad: kural for ad, _, kural in ICERIK})
    return [sozluk[h] for h in hatalar if h in sozluk]


def kaydet(kim, kaynak, gorev, puan, hatalar, model=''):
    with open(PUANLAR, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'t': datetime.datetime.now().isoformat(timespec='seconds'), 'kim': kim, 'kaynak': kaynak,
                            'gorev': gorev[:80], 'puan': puan, 'hatalar': hatalar, 'model': model}, ensure_ascii=False) + '\n')


_kayit = {'yol': '', 't': 0, 'veri': []}


def kayitlar():
    if not os.path.exists(PUANLAR):
        return []
    t = os.path.getmtime(PUANLAR)
    if _kayit['yol'] != PUANLAR or _kayit['t'] != t:
        with open(PUANLAR, encoding='utf-8') as f:
            _kayit.update(yol=PUANLAR, t=t, veri=[json.loads(s) for s in f if s.strip()])
    return _kayit['veri']


def ortalamalar(son=10):
    """Her ajanın son işlerdeki ortalaması; yeniden yazım öncesi ilk taslak ayrı sayılmaz."""
    gruplar = {}
    for k in kayitlar():
        if k['kaynak'] == 'iş':
            gruplar.setdefault(k['kim'], []).append(k['puan'])
    return {kim: round(sum(p[-son:]) / len(p[-son:])) for kim, p in gruplar.items()}


SEVIYE = ('Çırak', 'Kalfa', 'Usta', 'Uzman', 'Mükemmel')


def seviye(kim):
    """Otomatik puan tek başına yetmez: üst seviyeler sahibinin ya da baş ajanın İyi oyunu ister."""
    k = [x for x in kayitlar() if x['kim'] == kim]
    isler = [x for x in k if x['kaynak'] == 'iş']
    if len(isler) < 5:
        return SEVIYE[0]
    son = isler[-10:]
    ort = sum(x['puan'] for x in son) / len(son)
    uydurma = any(h.startswith('uydurma') for x in son for h in x['hatalar'])
    iyi = sum(1 for x in k if x['kaynak'] == 'sahibi' and x['puan'] == 100)
    kotu = any(x['kaynak'] == 'sahibi' and x['puan'] == 0 for x in k[-20:])
    if ort >= 96 and len(isler) >= 30 and iyi >= 3 and not uydurma and not kotu:
        return SEVIYE[4]
    if ort >= 92 and len(isler) >= 15 and iyi >= 1 and not uydurma:
        return SEVIYE[3]
    if ort >= 88 and len(isler) >= 10 and not uydurma:
        return SEVIYE[2]
    return SEVIYE[1] if ort >= 80 else SEVIYE[0]


def sik_hatalar(kim, son=12):
    say = {}
    for k in [k for k in kayitlar() if k['kim'] == kim][-son:]:
        for h in k['hatalar']:
            say[h] = say.get(h, 0) + 1
    return sorted(say, key=say.get, reverse=True)


def oy(kim, ad, yol, iyi):
    """Sahibinin oyu en güçlü eğitimdir: iyi taslak ajana örnek olur, kötüsü hata sayılır."""
    kaydet(kim, 'sahibi', ad, 100 if iyi else 0, [] if iyi else ['sahibi beğenmedi'])
    if iyi:
        with open(yol, encoding='utf-8') as f:
            taslak = f.read().split('## Taslak\n', 1)[-1].strip()
        with open(os.path.join(HAFIZA, kim + '.ornek.md'), 'w', encoding='utf-8') as f:
            f.write(taslak[:700])


def beceriler(kim):
    """Baş ajanın aktardığı bilgi. Yerel modelin bağlamı dar, toplam sınırlı tutulur."""
    with open(os.path.join(ROOT, 'ekip.json'), encoding='utf-8') as f:
        uye = next((u for u in json.load(f) if u['id'] == kim), {})
    parca = []
    for ad in uye.get('beceriler', []):
        yol = os.path.join(ROOT, 'egitim', 'beceriler', ad + '.md')
        if os.path.exists(yol):
            with open(yol, encoding='utf-8') as f:
                parca.append(f.read().strip())
    return '\n\nBildiklerin:\n' + '\n'.join(parca)[:3200] if parca else ''


def hafiza(kim):
    metin = []
    for yol in (os.path.join(GENEL, kim + '.md'), os.path.join(HAFIZA, kim + '.md'), os.path.join(HAFIZA, kim + '.oz.md')):
        if os.path.exists(yol):
            with open(yol, encoding='utf-8') as f:
                metin.append(f.read().strip())
    metin = 'Kendi kuralların:\n' + '\n'.join(x for x in metin if x) if metin else ''
    metin += beceriler(kim)
    ornek = os.path.join(HAFIZA, kim + '.ornek.md')
    if os.path.exists(ornek):
        with open(ornek, encoding='utf-8') as f:
            metin += '\n\nSahibinin beğendiği örnek, tarzını buna benzet ama kopyalama:\n' + f.read()
    return metin


def kural_uygun(metin, guvenlik):
    """Modelin önerdiği kural hafızaya girmeden önceki süzgeç."""
    k = metin.strip().strip('"-* ')
    # Aristoteles's rules were thrown out 7 times for length, most opening "Yazarlar, ..." (seen in the
    # logs): the address is dropped and a rule may run to 180 characters.
    k = re.sub(r'^(yazarlar|yazar|ajanlar)\s*[,:]\s*', '', k, flags=re.I)
    k = k[:1].upper() + k[1:]
    if not 12 <= len(k) <= 180 or '\n' in k or guvenlik(k):
        return None
    # Hafızaya girecek söz yalnız yazı üslubu hakkında olabilir: yetki, dosya ya da kural kaldırma değil.
    if re.search(r'(yok say|görmezden|ignore|önceki kural|kuralları kaldır|sistem|komut|dosya|internet|şifre|anahtar|yetki|baş ajan|sahibi)', k, re.I):
        return None
    return k


def kural_ekle(kim, kural):
    yol = os.path.join(HAFIZA, kim + '.oz.md')
    satirlar = []
    if os.path.exists(yol):
        with open(yol, encoding='utf-8') as f:
            satirlar = [s.rstrip('\n') for s in f if s.strip()]
    satirlar = (satirlar + ['- ' + kural])[-OZ_SINIR:]
    with open(yol, 'w', encoding='utf-8') as f:
        f.write('\n'.join(satirlar) + '\n')


def sinav_sirasi():
    """En düşük ortalamalı ve en uzun süredir sınava girmemiş ajan önce gelir. Sınavı olmayan projede boş döner."""
    # Sınavı olmayan projede ortak sınav çalışır: eğitim her projede sürsün.
    kaynak = SINAV if os.path.exists(SINAV) else os.path.join(ROOT, 'egitim', 'genel_sinav.json')
    with open(kaynak, encoding='utf-8') as f:
        sorular = json.load(f)
    son = {}
    for k in kayitlar():
        if k['kaynak'] == 'sınav':
            son[k['kim']] = k['t']
    ort = ortalamalar()
    kim = sorted(sorular, key=lambda a: (son.get(a, ''), ort.get(a, 100)))[0]
    adet = sum(1 for k in kayitlar() if k['kaynak'] == 'sınav' and k['kim'] == kim)
    return kim, sorular[kim][adet % len(sorular[kim])]


def bugunku_sinav():
    gun = datetime.date.today().isoformat()
    return sum(1 for k in kayitlar() if k['kaynak'] == 'sınav' and k['t'].startswith(gun))
