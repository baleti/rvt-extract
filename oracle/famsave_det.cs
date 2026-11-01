// famsave.cs - EditFamily + SaveAs of every editable family of a project; per-family facts into index.tsv. placeholders __FILE__ __TAG__ __ONLY__ (comma list of family names, empty = all)
using Autodesk.Revit.DB; using System.Linq; using System.IO; using System.Text; using System.Collections.Generic; using System.Globalization;
var app = UIApp.Application; var file = @"__FILE__"; var outd = @"C:\wl\out\__TAG__"; Directory.CreateDirectory(outd);
var only = "__ONLY__".Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries).ToList();
Document d = null;
try { d = app.OpenDocumentFile(ModelPathUtils.ConvertUserVisiblePathToModelPath(file), new OpenOptions{ DetachFromCentralOption = DetachFromCentralOption.DetachAndPreserveWorksets }); } catch (Exception ex) { Console.WriteLine("OPENFAIL " + ex.Message); return; }
var sb = new StringBuilder(); Func<string, string> Safe = (s) => { foreach (var c in Path.GetInvalidFileNameChars()) s = s.Replace(c, '_'); return s; };
sb.AppendLine("FILE\t" + file + "\t" + app.VersionNumber);
foreach (var fam in new FilteredElementCollector(d).OfClass(typeof(Family)).Cast<Family>().OrderBy(f => f.Name)) {
  if (only.Count > 0 && !only.Contains(fam.Name)) continue;
  string cat = fam.FamilyCategory != null ? fam.FamilyCategory.Name : "None";
  if (!fam.IsEditable || fam.IsInPlace) { sb.AppendLine("SKIP\t" + fam.Id + "\t" + cat + "\t" + fam.Name + "\teditable=" + fam.IsEditable + " inplace=" + fam.IsInPlace); continue; }
  Document fd = null;
  try {
    fd = d.EditFamily(fam);
    var dir = Path.Combine(outd, Safe(cat)); Directory.CreateDirectory(dir); var path = Path.Combine(dir, Safe(fam.Name) + ".rfa");
    var so = new SaveAsOptions(); so.OverwriteExistingFile = true; fd.SaveAs(path, so);
    var fm = fd.FamilyManager; var nforms = new FilteredElementCollector(fd).OfClass(typeof(GenericForm)).GetElementCount();
    var nrp = new FilteredElementCollector(fd).OfClass(typeof(ReferencePlane)).GetElementCount(); var nel = new FilteredElementCollector(fd).WhereElementIsNotElementType().GetElementCount();
    sb.AppendLine("OK\t" + fam.Id + "\t" + cat + "\t" + fam.Name + "\ttypes=" + fm.Types.Size + "\tparams=" + fm.Parameters.Size + "\tforms=" + nforms + "\trefplanes=" + nrp + "\telements=" + nel + "\t" + new FileInfo(path).Length);
  } catch (Exception ex) { sb.AppendLine("FAIL\t" + fam.Id + "\t" + cat + "\t" + fam.Name + "\t" + ex.Message.Split((char)10)[0]); }
  finally { try { if (fd != null) fd.Close(false); } catch { } }
}
File.WriteAllText(Path.Combine(outd, "index.tsv"), sb.ToString(), new UTF8Encoding(false)); Console.WriteLine("DONE"); d.Close(false);
