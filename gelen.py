"""Ofis ile baş ajan arasındaki köprü.

    python gelen.py                  okunmamış notları basar, okundu işaretler (Claude Code kancası)
    python gelen.py yanit <ad> <söz> baş ajanın yanıtını ofis ekranına yazar

Yalnız sahibinin yazdığı notları basar: ajanların yazdıkları baş ajana buradan ulaşmaz.
"""
import glob, os, sys

KLASOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mesajlar')


def main():
    if len(sys.argv) >= 4 and sys.argv[1] == 'yanit':
        ad = os.path.basename(sys.argv[2])
        with open(os.path.join(KLASOR, ad + '.bas'), 'w', encoding='utf-8') as f:
            f.write(' '.join(sys.argv[3:]))
        return
    sys.stdout.reconfigure(encoding='utf-8')
    for p in sorted(glob.glob(os.path.join(KLASOR, '*.txt'))):
        isaret = p[:-4] + '.okundu'
        if os.path.exists(isaret):
            continue
        with open(p, encoding='utf-8') as f:
            metin = f.read().strip()
        print(f'Sahibi üsten yazdı ({os.path.basename(p)[:-4]}): {metin}')
        open(isaret, 'w').close()
    # Üssün kendi bildirimleri (ör. plan birleştirme): sahibinin sözü değil, öyle de basılır.
    for p in sorted(glob.glob(os.path.join(KLASOR, '*.sistem'))):
        isaret = p[:-7] + '.okundu'
        if os.path.exists(isaret):
            continue
        with open(p, encoding='utf-8') as f:
            metin = f.read().strip()
        print(f'Üs bildirdi ({os.path.basename(p)[:-7]}): {metin}')
        open(isaret, 'w').close()


if __name__ == '__main__':
    main()
