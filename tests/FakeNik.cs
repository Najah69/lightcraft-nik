// Faux Nik pour tester l'intégration sans les vraies applis : journalise ses arguments et imite leurs effets.
using System;
using System.IO;
using System.Linq;
using System.Xml.Linq;

static class FakeNik
{
    static int Main(string[] a)
    {
        string dir = AppDomain.CurrentDomain.BaseDirectory;
        File.AppendAllText(Path.Combine(dir, "fakenik.log"), DateTime.Now.ToString("HH:mm:ss ") + string.Join(" | ", a) + Environment.NewLine);
        System.Threading.Thread.Sleep(3000);
        int paste = Array.IndexOf(a, "--paste");
        if (paste >= 0)
        {
            string input = a[Array.IndexOf(a, "--input") + 1], output = a[Array.IndexOf(a, "--output") + 1];
            File.Copy(input, output, true);
            return 0;
        }
        int host = Array.IndexOf(a, "--host-lightroom");
        if (host >= 0)
        {
            XDocument x = XDocument.Load(a[host + 1]);
            var keys = x.Descendants("key").ToList();
            string first = keys.First(k => (string)k.Attribute("name") == "input-images").Elements("string").First().Attribute("value").Value;
            string outDir = (string)keys.First(k => (string)k.Attribute("name") == "output-path").Attribute("value");
            string results = (string)keys.First(k => (string)k.Attribute("name") == "run-results-file").Attribute("value");
            string made = Path.Combine(outDir, Path.GetFileNameWithoutExtension(first) + "-HDR.tif");
            File.Copy(first, made, true);
            File.WriteAllText(results, "result=ok\nfilename=" + made + "\nreimport=true\nstack=true\n");
            return 0;
        }
        // « Modifier dans » : Nik enregistre par-dessus le fichier reçu
        foreach (string f in a.Where(File.Exists))
            File.SetLastWriteTime(f, DateTime.Now);
        return 0;
    }
}
