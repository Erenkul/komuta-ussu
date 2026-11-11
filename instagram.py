"""Instagram from the office: drafts wait on an approval card, and only your press on Paylaş posts one;
the account's and the posts' numbers come back for the statistics tab.

Setup (README, "Instagram"): a Meta app with the Instagram use case and Unified login, your professional
account added as Instagram Tester and given a token. The token goes in kisisel/instagram-token.txt and the
account id in kisisel/instagram/hesap.json as {"ig_id": "..."}; both stay out of git. Nothing here prints,
logs or returns the token: every reply from Meta passes through temizle(), which drops the paging links
(they carry it) and blanks any text that holds it.

A Reel goes up with Meta's resumable upload straight from the local file: a container is opened, the bytes
are sent to rupload.facebook.com, the container is asked until it is FINISHED, and media_publish puts it
on the profile. Nothing is posted until kisisel/instagram/ayar.json says "yayinda": true. Instagram allows
five hashtags a post, so a draft with more is marked. A cover picture is laid as the video's last frame
and thumb_offset points at it; a track from Instagram's own list (GET /ig_audio) can ride along through
audio_configuration. Drafts of type 'elle' (carousels, stories, AI-made clips) are posted by hand.
"""
import datetime, json, os, re, subprocess, threading, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
def _hesap():
    try:
        with open(os.path.join(ROOT, 'kisisel', 'instagram', 'hesap.json'), encoding='utf-8') as f:
            return str(json.load(f).get('ig_id', ''))
    except (OSError, ValueError):
        return ''


IG_ID = _hesap()
GRAPH = 'https://graph.facebook.com/v27.0'
kilit = threading.Lock()


def kisisel(*p):
    os.makedirs(os.path.join(ROOT, 'kisisel', 'instagram'), exist_ok=True)
    return os.path.join(ROOT, 'kisisel', *p)


def anahtar():
    try:
        with open(kisisel('instagram-token.txt'), encoding='utf-8-sig') as f:
            return f.read().strip()
    except OSError:
        return ''


def temizle(v, t=None):
    """Meta's reply without the key in it: paging links go, any string holding the key is blanked."""
    t = t if t is not None else anahtar()
    if isinstance(v, dict):
        return {k: temizle(x, t) for k, x in v.items() if k != 'paging'}
    if isinstance(v, list):
        return [temizle(x, t) for x in v]
    if isinstance(v, str) and (t and t in v or 'access_token=' in v):
        return '[gizlendi]'
    return v


class Hata(Exception):
    pass


def api(yol, yontem='GET', **alan):
    t = anahtar()
    if not t:
        raise Hata('Anahtar dosyası boş: kisisel/instagram-token.txt')
    if not IG_ID:
        raise Hata('Hesap kimliği yok: kisisel/instagram/hesap.json {"ig_id": "..."}')
    alan['access_token'] = t
    veri = urllib.parse.urlencode(alan).encode()
    if yontem == 'GET':
        istek = urllib.request.Request(GRAPH + yol + '?' + veri.decode())
    else:
        istek = urllib.request.Request(GRAPH + yol, data=veri, method=yontem)
    try:
        with urllib.request.urlopen(istek, timeout=60) as r:
            return temizle(json.loads(r.read() or b'{}'), t)
    except urllib.error.HTTPError as e:
        try:
            h = json.loads(e.read() or b'{}').get('error', {})
        except ValueError:
            h = {}
        raise Hata(temizle(h.get('error_user_msg') or h.get('message') or ('HTTP ' + str(e.code)), t))
    except urllib.error.URLError as e:
        raise Hata('Meta\'ya ulaşılamadı: ' + str(e.reason)[:120])


# ---- drafts -------------------------------------------------------------------------------------

def taslaklar():
    try:
        with open(kisisel('instagram', 'taslaklar.json'), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def yaz(L):
    p = kisisel('instagram', 'taslaklar.json')
    with open(p + '.yeni', 'w', encoding='utf-8', newline='') as f:
        json.dump(L, f, ensure_ascii=False, indent=1)
    os.replace(p + '.yeni', p)


def degistir(kimlik, **alan):
    with kilit:
        L = taslaklar()
        for x in L:
            if x['id'] == kimlik:
                x.update(alan)
        yaz(L)


def bilgi(video):
    """Length, size and frame of a video by ffprobe, for the card and for Meta's limits."""
    try:
        r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                            'stream=width,height,codec_name:format=duration', '-of', 'json', video],
                           capture_output=True, text=True, timeout=30, creationflags=0x08000000)
        j = json.loads(r.stdout or '{}')
        s = (j.get('streams') or [{}])[0]
        return {'sure': round(float(j.get('format', {}).get('duration', 0)), 1), 'en': s.get('width'), 'boy': s.get('height'),
                'kodek': s.get('codec_name', '')}
    except Exception:
        return {}


ETIKET_SINIRI = 5


def yayinda():
    try:
        with open(kisisel('instagram', 'ayar.json'), encoding='utf-8') as f:
            return bool(json.load(f).get('yayinda'))
    except (OSError, ValueError):
        return False


def kapakli(video, kapak, hedef):
    """The video with the cover picture as its last frame, the picture fitted into the video's frame
    on its own edge colour. Gives the cover frame's time in ms."""
    b = bilgi(video)
    en, boy = b.get('en') or 1080, b.get('boy') or 1920
    suz = (f'[1:v]scale={en}:{boy}:force_original_aspect_ratio=decrease,pad={en}:{boy}:(ow-iw)/2:(oh-ih)/2:color=0x101820,'
           f'setsar=1,fps=30,format=yuv420p,trim=end_frame=1[k];'
           f'[0:v]fps=30,scale={en}:{boy},setsar=1,format=yuv420p[v];'
           f'[0:a]aresample=48000,aformat=channel_layouts=stereo[a];'
           f'anullsrc=r=48000:cl=stereo,atrim=duration=0.0334[s];'
           f'[v][a][k][s]concat=n=2:v=1:a=1[ov][oa]')
    r = subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', video, '-loop', '1', '-i', kapak, '-filter_complex', suz,
                        '-map', '[ov]', '-map', '[oa]', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-profile:v', 'high',
                        '-g', '60', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', hedef],
                       capture_output=True, text=True, timeout=600, creationflags=0x08000000)
    if r.returncode or not os.path.isfile(hedef):
        raise Hata('Kapaklı video yapılamadı: ' + (r.stderr or '')[-200:])
    return max(0, int(bilgi(hedef).get('sure', 0) * 1000) - 20)


def muzik_ara(soz, kac=8):
    r = api('/ig_audio', audio_type='music', user_id=IG_ID, search_query=soz)
    return [{'id': a.get('audio_id'), 'ad': a.get('title'), 'sanatci': a.get('display_artist'),
             'sn': round((a.get('duration_in_ms') or 0) / 1000), 'dinle': a.get('on_platform_audio_preview_link', '')}
            for a in (r.get('audio') or [])[:kac]]


def taslak_ekle(video, aciklama, baslik='', kapak_ms=0, notu='', tur='reel', dil='', grup='', sira=0, gorseller=(), kapak='', muzik='',
                muzik_id='', muzik_ses=30):
    """Claude's side: a draft goes onto the card list; nothing is posted."""
    video = os.path.abspath(video) if video else ''
    gorseller = [os.path.abspath(g) for g in gorseller]
    kapak = os.path.abspath(kapak) if kapak else ''
    if video and (not os.path.isfile(video) or not video.lower().endswith(('.mp4', '.mov'))):
        raise Hata('Video bulunamadı ya da mp4/mov değil: ' + video)
    for g in gorseller + ([kapak] if kapak else []):
        if not os.path.isfile(g) or not g.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise Hata('Görsel bulunamadı: ' + g)
    if not video and not gorseller:
        raise Hata('Taslakta video ya da görsel yok.')
    kimlik = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    yukle = video
    if video and kapak and tur == 'reel':
        os.makedirs(kisisel('instagram', 'hazir'), exist_ok=True)
        yukle = kisisel('instagram', 'hazir', kimlik + '.mp4')
        kapak_ms = kapakli(video, kapak, yukle)
    b = bilgi(yukle) if yukle else {}
    mb = round(os.path.getsize(yukle) / 1e6, 1) if yukle else 0
    sorun = []
    if mb > 300: sorun.append('300 MB\'tan büyük')
    if b.get('sure') and not 3 <= b['sure'] <= 900: sorun.append('3 sn ile 15 dk arasında değil')
    if b.get('en') and b['en'] > 1920: sorun.append('genişliği 1920\'den büyük')
    if len(aciklama) > 2200: sorun.append('açıklama 2200 karakteri geçiyor')
    if len(re.findall(r'#\w', aciklama)) > ETIKET_SINIRI: sorun.append(str(ETIKET_SINIRI) + '\'ten çok etiket')
    if len(gorseller) > 20: sorun.append('20\'den çok görsel')
    x = {'id': kimlik, 'tarih': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
         'baslik': baslik or os.path.basename(video or gorseller[0]), 'video': video, 'yukle': yukle, 'kapak': kapak,
         'gorseller': gorseller, 'aciklama': aciklama, 'kapak_ms': int(kapak_ms), 'notu': notu, 'muzik': muzik, 'muzik_id': str(muzik_id), 'muzik_ses': int(muzik_ses), 'muzik_ekle': bool(muzik_id),
         'tur': tur if tur in ('reel', 'elle') else 'reel', 'dil': dil, 'grup': grup, 'sira': int(sira), 'mb': mb, **b,
         'sorun': sorun, 'durum': 'bekliyor'}
    with kilit:
        L = taslaklar(); L.insert(0, x); yaz(L[:200])
    return x


# ---- posting ------------------------------------------------------------------------------------

def paylas(kimlik, aciklama):
    """You pressed Paylaş: open a Reels container, upload the file, wait, publish."""
    if not yayinda():
        raise Hata('Paylaşım kilitli: kisisel/instagram/ayar.json içinde "yayinda": true değil.')
    x = next((x for x in taslaklar() if x['id'] == kimlik), None)
    if not x or x['durum'] not in ('bekliyor', 'hata'):
        raise Hata('Bu taslak paylaşılmaya hazır değil.')
    if x.get('tur') == 'elle' or not x.get('video'):
        raise Hata('Bu taslak uygulamadan elle paylaşılacak.')
    dosya = x.get('yukle') or x['video']
    if not os.path.isfile(dosya):
        raise Hata('Video dosyası yerinde yok.')
    aciklama = str(aciklama)[:2200]
    degistir(kimlik, durum='yukleniyor', aciklama=aciklama, hata='')

    def calis():
        try:
            alan = {'media_type': 'REELS', 'upload_type': 'resumable', 'caption': aciklama, 'share_to_feed': 'true'}
            if x.get('kapak_ms'):
                alan['thumb_offset'] = str(x['kapak_ms'])
            if x.get('muzik_id') and x.get('muzik_ekle'):
                alan['audio_configuration'] = json.dumps({'audio_id': x['muzik_id'], 'audio_volume': x.get('muzik_ses', 30), 'video_volume': 100})
            kap = api('/' + IG_ID + '/media', 'POST', **alan)
            boyut = os.path.getsize(dosya)
            with open(dosya, 'rb') as f:
                istek = urllib.request.Request(kap['uri'], data=f.read(), method='POST', headers={
                    'Authorization': 'OAuth ' + anahtar(), 'offset': '0', 'file_size': str(boyut)})
            try:
                with urllib.request.urlopen(istek, timeout=600) as r:
                    r.read()
            except urllib.error.HTTPError as e:
                raise Hata('Yükleme reddedildi (HTTP ' + str(e.code) + ')')
            degistir(kimlik, durum='isleniyor')
            for _ in range(60):
                time.sleep(10)
                d = api('/' + kap['id'], fields='status_code,status')
                if d.get('status_code') == 'FINISHED':
                    break
                if d.get('status_code') in ('ERROR', 'EXPIRED'):
                    raise Hata('Instagram videoyu işleyemedi: ' + str(d.get('status', ''))[:200])
            else:
                raise Hata('Instagram 10 dakikada videoyu işlemeyi bitirmedi.')
            m = api('/' + IG_ID + '/media_publish', 'POST', creation_id=kap['id'])
            p = api('/' + m['id'], fields='permalink')
            degistir(kimlik, durum='paylasildi', medya=m['id'], adres=p.get('permalink', ''),
                     paylasildi=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))
        except Exception as e:
            degistir(kimlik, durum='hata', hata=str(temizle(str(e)))[:300])
    threading.Thread(target=calis, daemon=True).start()


def sil(kimlik):
    with kilit:
        L = []
        for x in taslaklar():
            if x['id'] == kimlik and x['durum'] not in ('yukleniyor', 'isleniyor'):
                # Only the prepared copy goes; your own files stay where they are.
                if x.get('yukle') and x['yukle'] != x.get('video') and x['yukle'].startswith(kisisel('instagram', 'hazir')):
                    try:
                        os.remove(x['yukle'])
                    except OSError:
                        pass
                continue
            L.append(x)
        yaz(L)
    return L


# ---- statistics ---------------------------------------------------------------------------------

REELS = 'views,reach,likes,comments,shares,saved,total_interactions,ig_reels_avg_watch_time'
DIGER = 'reach,likes,comments,shares,saved,total_interactions'
onbellek = {'t': 0, 'veri': None}


def istatistik(taze=False):
    """The account and its last twelve posts with their numbers; asked at most every five minutes."""
    if not taze and onbellek['veri'] and time.time() - onbellek['t'] < 300:
        return onbellek['veri']
    hesap = api('/' + IG_ID, fields='username,name,followers_count,follows_count,media_count,profile_picture_url')
    gun = {}
    try:
        for m in api('/' + IG_ID + '/insights', metric='reach,profile_views,accounts_engaged,total_interactions',
                     period='day', metric_type='total_value').get('data', []):
            gun[m['name']] = m.get('total_value', {}).get('value')
    except Hata as e:
        gun['hata'] = str(e)
    medya = api('/' + IG_ID + '/media', limit='12',
                fields='id,caption,media_type,media_product_type,timestamp,permalink,thumbnail_url,media_url,like_count,comments_count').get('data', [])
    for m in medya:
        m['sayilar'] = {}
        for olcu in ((REELS,) if m.get('media_product_type') == 'REELS' else ()) + (DIGER,):
            try:
                for d in api('/' + m['id'] + '/insights', metric=olcu).get('data', []):
                    m['sayilar'][d['name']] = (d.get('values') or [{}])[0].get('value')
                break
            except Hata as e:
                m['sayilar_hata'] = str(e)
        m['caption'] = (m.get('caption') or '')[:300]
    veri = {'hesap': hesap, 'gun': gun, 'medya': medya, 'saat': datetime.datetime.now().strftime('%H:%M')}
    onbellek.update(t=time.time(), veri=veri)
    return veri


if __name__ == '__main__':
    # Claude adds a draft:  python instagram.py taslak <video> <caption file> [title] [cover ms] [note]
    import sys
    a = sys.argv[1:]
    if a[:1] == ['plan'] and len(a) == 2:
        # Many drafts at once: [{video|gorseller, aciklama, baslik, notu, tur, dil, grup, sira, kapak, muzik}]
        with open(a[1], encoding='utf-8') as f:
            for t in json.load(f):
                x = taslak_ekle(t.get('video', ''), t['aciklama'], t.get('baslik', ''), t.get('kapak_ms', 0), t.get('notu', ''),
                                t.get('tur', 'reel'), t.get('dil', ''), t.get('grup', ''), t.get('sira', 0), t.get('gorseller', ()),
                                t.get('kapak', ''), t.get('muzik', ''), t.get('muzik_id', ''), t.get('muzik_ses', 30))
                print('taslak', x['sira'], x['dil'], x['tur'], x['baslik'], 'kapak ms', x['kapak_ms'], 'sorun:', x['sorun'] or 'yok')
    elif a[:1] == ['taslak'] and len(a) >= 3:
        with open(a[2], encoding='utf-8') as f:
            x = taslak_ekle(a[1], f.read().strip(), *(a[3:4] or ['']), int(a[4]) if len(a) > 4 else 0, a[5] if len(a) > 5 else '')
        print('taslak', x['id'], x['baslik'], x['sure'] if 'sure' in x else '', 'sorun:', x['sorun'] or 'yok')
    elif a[:1] == ['muzik']:
        for m in muzik_ara(' '.join(a[1:])):
            print(m['id'], '|', m['ad'], '|', m['sanatci'], '|', m['sn'], 's')
    elif a[:1] == ['dene']:
        v = istatistik(True)
        print(v['hesap'].get('username'), v['hesap'].get('followers_count'), 'takipçi,', len(v['medya']), 'gönderi; gün:', v['gun'])
    else:
        print(__doc__.split('\n\n')[0])
