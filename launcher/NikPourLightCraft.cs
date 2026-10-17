// Lanceur de « Nik Collection pour LightCraft » : LightCraft (Settings ▸ External Editing ▸ Other editor) n'accepte
// qu'un programme, auquel il passe les fichiers. Celui-ci démarre pythonw sur NikPourLightCraft.pyw avec ces fichiers.
// pythonw.exe est lu dans launcher.cfg, à côté de l'exe.
using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Windows.Forms;

static class Launcher
{
    [STAThread]
    static int Main(string[] args)
    {
        string dir = AppDomain.CurrentDomain.BaseDirectory;
        string script = Path.Combine(dir, "NikPourLightCraft.pyw");
        string cfg = Path.Combine(dir, "launcher.cfg");
        string pythonw = File.Exists(cfg) ? File.ReadAllText(cfg).Trim() : "pythonw.exe";
        StringBuilder line = new StringBuilder("-I " + Quote(script));
        foreach (string a in args)
            line.Append(' ').Append(Quote(a));
        try
        {
            Process.Start(new ProcessStartInfo(pythonw, line.ToString()) { UseShellExecute = false, WorkingDirectory = dir });
            return 0;
        }
        catch (Exception e)
        {
            MessageBox.Show("Impossible de lancer " + pythonw + " : " + e.Message, "Nik Collection pour LightCraft");
            return 1;
        }
    }

    // Règles de CommandLineToArgvW : guillemets autour, antislashs doublés devant un guillemet.
    static string Quote(string s)
    {
        StringBuilder b = new StringBuilder("\"");
        int slashes = 0;
        foreach (char c in s)
        {
            if (c == '\\') { slashes++; continue; }
            if (c == '"') b.Append('\\', slashes * 2 + 1).Append('"');
            else b.Append('\\', slashes).Append(c);
            slashes = 0;
        }
        return b.Append('\\', slashes * 2).Append('"').ToString();
    }
}
