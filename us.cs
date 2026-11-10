// Komuta Üssü'nü tek tıkla açar: model sunucusunu (LM Studio ya da Bionic) ve ofisi gerekirse
// başlatır, ekranı kendi penceresinde gösterir.
// Derleme (kur.ps1 yapar): csc /target:winexe /win32icon:us.ico /out:"Komuta Üssü.exe" us.cs
// Sunucu yalnız 127.0.0.1'e bağlanır; bu dosya başka hiçbir şey kurmaz, oturum açılışına yazılmaz.
using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Threading;

static class Us
{
    const string Adres = "http://127.0.0.1:8765";

    static bool Acik(string url)
    {
        try
        {
            var q = (HttpWebRequest)WebRequest.Create(url);
            q.Timeout = 800; q.Proxy = null;
            using (q.GetResponse()) return true;
        }
        catch { return false; }
    }

    static void Baslat(string dosya, string arg, string klasor)
    {
        var p = new ProcessStartInfo(dosya, arg) { UseShellExecute = false, CreateNoWindow = true };
        if (klasor != null) p.WorkingDirectory = klasor;
        Process.Start(p);
    }

    // Kurulu ilk model sunucusunu açar; zaten açıksa dokunmaz.
    static void ModelSunucusu()
    {
        string yerel = Environment.GetEnvironmentVariable("LOCALAPPDATA");
        string[][] adaylar = {
            new[] { Path.Combine(yerel, @"Programs\LM Studio\LM Studio.exe"), "LM Studio" },
            new[] { Path.Combine(yerel, @"Programs\Bionic\Bionic.exe"), "Bionic" },
        };
        foreach (var a in adaylar)
        {
            if (!File.Exists(a[0])) continue;
            if (Process.GetProcessesByName(a[1]).Length == 0)
                Process.Start(new ProcessStartInfo(a[0]) { UseShellExecute = true });
            return;
        }
    }

    [STAThread]
    static void Main()
    {
        string kok = AppDomain.CurrentDomain.BaseDirectory;
        ModelSunucusu();
        if (!Acik(Adres))
        {
            // kur.ps1 bulduğu pythonw yolunu python-yolu.txt'ye yazar; yoksa PATH'teki pythonw denenir.
            string yolDosyasi = Path.Combine(kok, "python-yolu.txt");
            string py = File.Exists(yolDosyasi) ? File.ReadAllText(yolDosyasi).Trim() : "pythonw";
            Baslat(py, "-X utf8 ofis.py", kok);
            for (int i = 0; i < 40 && !Acik(Adres); i++) Thread.Sleep(250);
        }
        string edge = Path.Combine(Environment.GetEnvironmentVariable("ProgramFiles(x86)"), @"Microsoft\Edge\Application\msedge.exe");
        if (File.Exists(edge)) Process.Start(edge, "--app=" + Adres + " --window-size=1600,900");
        else Process.Start(new ProcessStartInfo(Adres) { UseShellExecute = true });
    }
}
