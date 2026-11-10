# Komuta Üssü kurulumu (Windows 10/11, PowerShell 5.1 ya da 7).
#   powershell -ExecutionPolicy Bypass -File kur.ps1          kurar
#   powershell -ExecutionPolicy Bypass -File kur.ps1 -Dene    kurar ve ofisi kısa bir denemeyle açıp kapatır
#   -KisayolYok                                              masaüstüne kısayol koymaz
# Hiçbir şeyi oturum açılışına yazmaz, yönetici izni istemez, internete yalnız model sunucusu için
# değil hiç çıkmaz: her şey bu klasörde ve 127.0.0.1 üzerinde kalır. Tekrar çalıştırmak güvenlidir.
param([switch]$Dene, [switch]$KisayolYok)
$ErrorActionPreference = 'Stop'
$kok = $PSScriptRoot
$eksik = New-Object System.Collections.Generic.List[string]
function Tamam($m) { Write-Host "  [tamam] $m" -ForegroundColor Green }
function Uyari($m) { Write-Host "  [dikkat] $m" -ForegroundColor Yellow; $eksik.Add($m) }
function Baslik($m) { Write-Host ""; Write-Host "== $m" -ForegroundColor Cyan }

Write-Host "Komuta Üssü kuruluyor: $kok"

# 1. Python 3.10+
Baslik 'Python'
$py = $null
foreach ($aday in @(@('py', '-3'), @('python'), @('python3'))) {
    try {
        $arg = @($aday | Select-Object -Skip 1) + @('-c', 'import sys;print(sys.executable);print(sys.version_info[0]*100+sys.version_info[1])')
        $cikti = & $aday[0] @arg 2>$null
        if ($LASTEXITCODE -eq 0 -and $cikti.Count -ge 2 -and [int]$cikti[1] -ge 310) { $py = $cikti[0].Trim(); break }
    } catch { }
}
if (-not $py) {
    Write-Host '  Python 3.10 ya da yenisi bulunamadı. Kur: winget install Python.Python.3.12' -ForegroundColor Red
    Write-Host '  (ya da python.org; kurarken "Add python.exe to PATH" işaretli olsun), sonra bu betiği yeniden çalıştır.'
    exit 1
}
$pyw = Join-Path (Split-Path $py) 'pythonw.exe'
if (-not (Test-Path $pyw)) { $pyw = $py }
[IO.File]::WriteAllText((Join-Path $kok 'python-yolu.txt'), $pyw)
Tamam "Python: $py"

# 2. Ayar dosyası (kişisel, repoya girmez)
Baslik 'Ayarlar'
$ayar = Join-Path $kok 'ayar.json'
if (-not (Test-Path $ayar)) { Copy-Item (Join-Path $kok 'ayar.ornek.json') $ayar; Tamam 'ayar.json ayar.ornek.json''dan oluşturuldu' }
else { Tamam 'ayar.json zaten var, dokunulmadı' }
# Değer metin olarak geçer (PowerShell 5.1 tırnakları Python'a aktarmaz); 'true'/'false' mantık değeri olur.
function AyarYaz($anahtar, $deger) {
    & $py -X utf8 -c "import json,sys;p=sys.argv[1];a=json.load(open(p,encoding='utf-8'));d=sys.argv[3];a[sys.argv[2]]={'true':True,'false':False}.get(d,d);open(p,'w',encoding='utf-8',newline='').write(json.dumps(a,ensure_ascii=False,indent=1)+'\n')" $ayar $anahtar $deger
    if ($LASTEXITCODE -ne 0) { throw "ayar.json yazılamadı: $anahtar" }
}

# 3. Yerel model sunucusu: LM Studio (1234) ya da Bionic (1235)
Baslik 'Model sunucusu'
$api = $null; $modeller = @()
foreach ($port in 1234, 1235) {
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:$port/v1/models" -TimeoutSec 3
        $api = "http://127.0.0.1:$port/v1"; $modeller = @($r.data | ForEach-Object { $_.id }); break
    } catch { }
}
if ($api) {
    AyarYaz 'api' $api
    Tamam "Sunucu açık: $api ($($modeller.Count) model)"
    try { Invoke-RestMethod -Uri ($api -replace '/v1$', '/api/v1/models') -TimeoutSec 3 | Out-Null; Tamam 'Model yükleme/boşaltma API''si var' }
    catch { Uyari 'Sunucunun /api/v1/models ucu yok: LM Studio''yu 0.4 ya da yenisine güncelle (ofis modelleri kendisi açıp kapatır).' }
    $gerekli = & $py -X utf8 -c "import json;a=json.load(open(r'$ayar',encoding='utf-8'));print('\n'.join(sorted({m for z in a['zincir'].values() for m in z if not m.startswith('opencode/')})))"
    foreach ($m in $gerekli) {
        if ($modeller -contains $m) { Tamam "Model indirilmiş: $m" }
        else { Uyari "Model eksik: $m  (LM Studio > Discover'da ara ve indir, ya da: lms get $m)" }
    }
} else {
    Uyari 'Yerel model sunucusu bulunamadı.'
    Write-Host '    1. LM Studio''yu kur: https://lmstudio.ai  (ya da: winget install ElementLabs.LMStudio)'
    Write-Host '    2. Discover''dan gemma-4-e4b-it modelini indir (yaklaşık 5 GB; isteğe bağlı qwen3.5-9b).'
    Write-Host '    3. Developer sekmesinde Local Server''ı aç (port 1234), sonra bu betiği yeniden çalıştır.'
}

# 4. Başlatıcı (Komuta Üssü.exe) ve masaüstü kısayolu
Baslik 'Başlatıcı'
$hedef = Join-Path $kok 'ofis.bat'
$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (Test-Path $csc) {
    $exe = Join-Path $kok 'Komuta Üssü.exe'
    $c = & $csc /nologo /target:winexe "/win32icon:$(Join-Path $kok 'us.ico')" "/out:$exe" (Join-Path $kok 'us.cs') 2>&1
    if ($LASTEXITCODE -eq 0) { $hedef = $exe; Tamam 'Komuta Üssü.exe derlendi' }
    else { Uyari "Başlatıcı derlenemedi, ofis.bat kullanılacak: $c" }
} else { Uyari '.NET derleyicisi (csc) yok, ofis.bat kullanılacak.' }
if (-not $KisayolYok) {
    $masa = [Environment]::GetFolderPath('Desktop')
    $k = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $masa 'Komuta Üssü.lnk'))
    $k.TargetPath = $hedef; $k.WorkingDirectory = $kok; $k.IconLocation = (Join-Path $kok 'us.ico'); $k.Description = 'Komuta Üssü: yerel yapay zekâ ofisi'
    $k.Save(); Tamam "Masaüstü kısayolu: $masa\Komuta Üssü.lnk"
}

# 5. İsteğe bağlı deneme: ofis bekleme kipinde açılır, ekran ve iş listesi yanıt veriyor mu bakılır, kapatılır.
if ($Dene) {
    Baslik 'Deneme'
    $acik = $false; try { Invoke-RestMethod http://127.0.0.1:8765/durum -TimeoutSec 2 | Out-Null; $acik = $true } catch { }
    if ($acik) { Uyari 'Port 8765''te zaten bir ofis çalışıyor; deneme atlandı.' }
    else {
        $eski = & $py -X utf8 -c "import json;print('true' if json.load(open(r'$ayar',encoding='utf-8')).get('durdur') else 'false')"
        AyarYaz 'durdur' 'true'
        $p = Start-Process -FilePath $py -ArgumentList '-X', 'utf8', 'ofis.py' -WorkingDirectory $kok -WindowStyle Hidden -PassThru
        $ok = $false
        for ($i = 0; $i -lt 40 -and -not $ok; $i++) { Start-Sleep -Milliseconds 500; try { $d = Invoke-RestMethod http://127.0.0.1:8765/durum -TimeoutSec 2; $ok = $true } catch { } }
        if ($ok) {
            Tamam "Ofis açıldı: $($d.mod)"
            try { $is = Invoke-RestMethod http://127.0.0.1:8765/isler.json -TimeoutSec 5; Tamam "İş Defteri yanıt veriyor ($(@($is).Count) iş)" } catch { Uyari 'İş Defteri yanıt vermedi.' }
        } else { Uyari 'Ofis 20 saniyede açılmadı; ofis.log dosyasına bak.' }
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        AyarYaz 'durdur' $eski
    }
}

Baslik 'Sonuç'
if ($eksik.Count -eq 0) { Write-Host '  Kurulum tamam. Masaüstündeki Komuta Üssü kısayoluna çift tıkla.' -ForegroundColor Green }
else {
    Write-Host "  Kurulum bitti, $($eksik.Count) eksik var:" -ForegroundColor Yellow
    $eksik | ForEach-Object { Write-Host "   - $_" }
    Write-Host '  Eksikleri giderip bu betiği yeniden çalıştırabilirsin.'
}
